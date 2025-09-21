#!/bin/bash

# ERP System Production Deployment Script
# Architecture Lead: Winston
# Usage: ./deploy.sh [environment] [action]

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
ENVIRONMENT="${1:-staging}"
ACTION="${2:-deploy}"
VERSION="${3:-$(git rev-parse --short HEAD)}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Load environment configuration
load_environment() {
    local env_file="$PROJECT_ROOT/deployment/environments/${ENVIRONMENT}.env"
    
    if [[ ! -f "$env_file" ]]; then
        log_error "Environment file not found: $env_file"
        exit 1
    fi
    
    log_info "Loading environment configuration for: $ENVIRONMENT"
    # shellcheck source=/dev/null
    source "$env_file"
    export BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
    export VCS_REF="$(git rev-parse HEAD)"
    export VERSION="$VERSION"
}

# Pre-deployment checks
pre_deployment_checks() {
    log_info "Running pre-deployment checks..."
    
    # Check if required tools are installed
    local tools=("docker" "docker-compose" "curl" "git")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "Required tool not found: $tool"
            exit 1
        fi
    done
    
    # Check if required environment variables are set
    local required_vars=("DB_PASSWORD" "JWT_SECRET_KEY" "SECRET_KEY")
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            log_error "Required environment variable not set: $var"
            exit 1
        fi
    done
    
    # Check database connectivity
    if ! docker-compose -f "$PROJECT_ROOT/docker-compose.production.yml" exec -T postgres pg_isready -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; then
        log_warning "Database connection check failed (may be expected during initial deployment)"
    fi
    
    log_success "Pre-deployment checks completed"
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."
    
    cd "$PROJECT_ROOT"
    
    # Build backend image
    log_info "Building backend image..."
    docker build \
        --build-arg BUILD_DATE="$BUILD_DATE" \
        --build-arg VCS_REF="$VCS_REF" \
        --build-arg VERSION="$VERSION" \
        -t "erp/backend:$VERSION" \
        -t "erp/backend:latest" \
        ./backend/
    
    # Build frontend image
    log_info "Building frontend image..."
    docker build \
        --build-arg BUILD_DATE="$BUILD_DATE" \
        --build-arg VCS_REF="$VCS_REF" \
        --build-arg VERSION="$VERSION" \
        --build-arg API_URL="$API_URL" \
        -t "erp/frontend:$VERSION" \
        -t "erp/frontend:latest" \
        ./frontend/
    
    log_success "Docker images built successfully"
}

# Database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    cd "$PROJECT_ROOT"
    
    # Run database initialization and optimization scripts
    docker-compose -f docker-compose.production.yml exec -T postgres psql -U "$DB_USER" -d "$DB_NAME" -f /docker-entrypoint-initdb.d/01-init.sql
    docker-compose -f docker-compose.production.yml exec -T postgres psql -U "$DB_USER" -d "$DB_NAME" -f /docker-entrypoint-initdb.d/02-optimization.sql
    
    # Update table statistics
    docker-compose -f docker-compose.production.yml exec -T postgres psql -U "$DB_USER" -d "$DB_NAME" -c "ANALYZE;"
    
    log_success "Database migrations completed"
}

# Cache warming
warm_cache() {
    log_info "Warming application cache..."
    
    # Wait for backend to be ready
    local max_attempts=30
    local attempt=0
    
    while [[ $attempt -lt $max_attempts ]]; do
        if curl -f -s "$API_URL/health" >/dev/null; then
            break
        fi
        log_info "Waiting for backend to be ready... ($((attempt + 1))/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    if [[ $attempt -eq $max_attempts ]]; then
        log_error "Backend failed to become ready within timeout"
        exit 1
    fi
    
    # Trigger cache warming endpoints
    curl -f -s "$API_URL/api/v1/suppliers" >/dev/null || log_warning "Failed to warm suppliers cache"
    curl -f -s "$API_URL/api/v1/storage/tree" >/dev/null || log_warning "Failed to warm storage cache"
    curl -f -s "$API_URL/api/v1/system/settings" >/dev/null || log_warning "Failed to warm settings cache"
    
    log_success "Cache warming completed"
}

# Health checks
health_checks() {
    log_info "Running health checks..."
    
    local services=("postgres" "redis" "backend" "frontend" "nginx")
    local failed_checks=0
    
    for service in "${services[@]}"; do
        if docker-compose -f "$PROJECT_ROOT/docker-compose.production.yml" ps "$service" | grep -q "Up"; then
            log_success "Service $service is running"
        else
            log_error "Service $service is not running"
            ((failed_checks++))
        fi
    done
    
    # Test application endpoints
    if curl -f -s "$API_URL/health" | grep -q '"status":"healthy"'; then
        log_success "Backend health check passed"
    else
        log_error "Backend health check failed"
        ((failed_checks++))
    fi
    
    if curl -f -s "http://localhost:80/health" >/dev/null; then
        log_success "Frontend health check passed"
    else
        log_error "Frontend health check failed"
        ((failed_checks++))
    fi
    
    if [[ $failed_checks -gt 0 ]]; then
        log_error "$failed_checks health checks failed"
        exit 1
    fi
    
    log_success "All health checks passed"
}

# Performance tests
performance_tests() {
    log_info "Running performance tests..."
    
    # Basic load test using curl
    local endpoints=(
        "$API_URL/health"
        "$API_URL/api/v1/suppliers"
        "$API_URL/api/v1/projects"
    )
    
    for endpoint in "${endpoints[@]}"; do
        log_info "Testing endpoint: $endpoint"
        
        # Measure response time
        local response_time
        response_time=$(curl -w "%{time_total}" -o /dev/null -s "$endpoint")
        
        if (( $(echo "$response_time < 2.0" | bc -l) )); then
            log_success "Endpoint $endpoint responded in ${response_time}s"
        else
            log_warning "Endpoint $endpoint responded slowly in ${response_time}s"
        fi
    done
    
    log_success "Performance tests completed"
}

# Backup current deployment
backup_current_deployment() {
    log_info "Creating backup of current deployment..."
    
    local backup_dir="$PROJECT_ROOT/backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Backup database
    docker-compose -f "$PROJECT_ROOT/docker-compose.production.yml" exec -T postgres pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$backup_dir/database.sql.gz"
    
    # Backup configuration
    cp -r "$PROJECT_ROOT/deployment/environments" "$backup_dir/"
    
    # Backup uploaded files
    if [[ -d "$PROJECT_ROOT/uploads" ]]; then
        tar -czf "$backup_dir/uploads.tar.gz" -C "$PROJECT_ROOT" uploads/
    fi
    
    log_success "Backup created at: $backup_dir"
}

# Deploy application
deploy_application() {
    log_info "Deploying ERP application ($ENVIRONMENT)..."
    
    cd "$PROJECT_ROOT"
    
    case $ENVIRONMENT in
        staging)
            docker-compose -f docker-compose.production.yml up -d --remove-orphans
            ;;
        production)
            # Blue-green deployment for production
            log_info "Performing blue-green deployment..."
            
            # Create backup first
            backup_current_deployment
            
            # Deploy new version
            docker-compose -f docker-compose.production.yml up -d --remove-orphans
            
            # Wait for services to be ready
            sleep 30
            
            # Run health checks
            health_checks
            ;;
        *)
            log_error "Unsupported environment: $ENVIRONMENT"
            exit 1
            ;;
    esac
    
    log_success "Application deployed successfully"
}

# Rollback deployment
rollback_deployment() {
    log_info "Rolling back deployment..."
    
    local latest_backup
    latest_backup=$(find "$PROJECT_ROOT/backups" -maxdepth 1 -type d -name "[0-9]*_[0-9]*" | sort -r | head -n1)
    
    if [[ -z "$latest_backup" ]]; then
        log_error "No backup found for rollback"
        exit 1
    fi
    
    log_info "Rolling back to backup: $(basename "$latest_backup")"
    
    # Stop current services
    docker-compose -f "$PROJECT_ROOT/docker-compose.production.yml" down
    
    # Restore database
    if [[ -f "$latest_backup/database.sql.gz" ]]; then
        log_info "Restoring database..."
        zcat "$latest_backup/database.sql.gz" | docker-compose -f "$PROJECT_ROOT/docker-compose.production.yml" exec -T postgres psql -U "$DB_USER" "$DB_NAME"
    fi
    
    # Restore uploaded files
    if [[ -f "$latest_backup/uploads.tar.gz" ]]; then
        log_info "Restoring uploaded files..."
        tar -xzf "$latest_backup/uploads.tar.gz" -C "$PROJECT_ROOT"
    fi
    
    # Start services with previous version
    docker-compose -f "$PROJECT_ROOT/docker-compose.production.yml" up -d
    
    log_success "Rollback completed"
}

# Monitoring setup
setup_monitoring() {
    log_info "Setting up monitoring..."
    
    # Start monitoring services
    docker-compose -f "$PROJECT_ROOT/docker-compose.production.yml" up -d prometheus grafana loki promtail
    
    # Wait for Grafana to be ready
    local max_attempts=30
    local attempt=0
    
    while [[ $attempt -lt $max_attempts ]]; do
        if curl -f -s http://localhost:3000/api/health >/dev/null; then
            break
        fi
        sleep 5
        ((attempt++))
    done
    
    # Import dashboards (if available)
    if [[ -d "$PROJECT_ROOT/monitoring/grafana/dashboards" ]]; then
        log_info "Importing Grafana dashboards..."
        # Dashboard import logic would go here
    fi
    
    log_success "Monitoring setup completed"
}

# Main deployment logic
main() {
    log_info "Starting ERP deployment process..."
    log_info "Environment: $ENVIRONMENT"
    log_info "Action: $ACTION"
    log_info "Version: $VERSION"
    
    # Load environment configuration
    load_environment
    
    case $ACTION in
        deploy)
            pre_deployment_checks
            build_images
            deploy_application
            run_migrations
            warm_cache
            health_checks
            performance_tests
            setup_monitoring
            ;;
        build)
            build_images
            ;;
        migrate)
            run_migrations
            ;;
        rollback)
            rollback_deployment
            ;;
        health)
            health_checks
            ;;
        backup)
            backup_current_deployment
            ;;
        *)
            log_error "Unknown action: $ACTION"
            echo "Available actions: deploy, build, migrate, rollback, health, backup"
            exit 1
            ;;
    esac
    
    log_success "Deployment process completed successfully!"
    
    # Print useful information
    echo ""
    log_info "Deployment Information:"
    echo "  Environment: $ENVIRONMENT"
    echo "  Version: $VERSION"
    echo "  Frontend URL: http://localhost:80"
    echo "  API URL: $API_URL"
    echo "  Grafana: http://localhost:3000"
    echo "  Prometheus: http://localhost:9090"
}

# Trap errors and cleanup
trap 'log_error "Deployment failed at line $LINENO. Exit code: $?"' ERR

# Run main function
main "$@"