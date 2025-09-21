#!/bin/bash
set -e

# ERP System Deployment Script
# Production-ready deployment automation with health checks and rollback capability

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEPLOYMENT_ENV=${DEPLOYMENT_ENV:-production}
BACKUP_BEFORE_DEPLOY=${BACKUP_BEFORE_DEPLOY:-true}
HEALTH_CHECK_RETRIES=${HEALTH_CHECK_RETRIES:-10}
HEALTH_CHECK_DELAY=${HEALTH_CHECK_DELAY:-30}
ROLLBACK_ON_FAILURE=${ROLLBACK_ON_FAILURE:-true}

# Docker Compose profiles
COMPOSE_PROFILES="default"
if [ "${ENABLE_MONITORING}" = "true" ]; then
    COMPOSE_PROFILES="${COMPOSE_PROFILES},monitoring"
fi

# Functions
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

check_prerequisites() {
    log_info "Checking deployment prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check .env file
    if [ ! -f ".env" ]; then
        log_error ".env file not found. Copy .env.example to .env and configure it."
        exit 1
    fi
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

backup_database() {
    if [ "$BACKUP_BEFORE_DEPLOY" = "true" ]; then
        log_info "Creating database backup before deployment..."
        
        # Create backup directory
        mkdir -p database/backups
        
        # Generate backup filename
        BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
        
        # Check if database container exists and is running
        if docker-compose ps database | grep -q "Up"; then
            # Create backup
            docker-compose exec -T database pg_dump \
                -U "${POSTGRES_USER:-erp_user}" \
                -d "${POSTGRES_DB:-erp_system}" \
                --no-owner --no-acl > "database/backups/$BACKUP_FILE"
            
            # Compress backup
            gzip "database/backups/$BACKUP_FILE"
            
            log_success "Database backup created: database/backups/${BACKUP_FILE}.gz"
            echo "${BACKUP_FILE}.gz" > .last_backup
        else
            log_warning "Database container not running, skipping backup"
        fi
    fi
}

validate_configuration() {
    log_info "Validating configuration..."
    
    # Source environment variables
    set -a
    source .env
    set +a
    
    # Check critical variables
    REQUIRED_VARS=(
        "SECRET_KEY"
        "JWT_SECRET_KEY"
        "POSTGRES_PASSWORD"
        "ADMIN_PASSWORD"
    )
    
    for var in "${REQUIRED_VARS[@]}"; do
        if [ -z "${!var}" ]; then
            log_error "Required environment variable $var is not set"
            exit 1
        fi
        
        # Check if it's still using example values
        if [[ "${!var}" == *"change"* ]] || [[ "${!var}" == *"example"* ]]; then
            log_error "Environment variable $var appears to use example value. Please set a secure value."
            exit 1
        fi
    done
    
    log_success "Configuration validation passed"
}

build_images() {
    log_info "Building Docker images..."
    
    # Build with build args
    docker-compose build \
        --parallel \
        --pull \
        --build-arg BUILD_ENV="${DEPLOYMENT_ENV}" \
        --build-arg BUILDKIT_PROGRESS=plain
    
    log_success "Docker images built successfully"
}

deploy_services() {
    log_info "Deploying services..."
    
    # Deploy with specific profiles
    COMPOSE_PROFILES="$COMPOSE_PROFILES" docker-compose up -d \
        --remove-orphans \
        --force-recreate
    
    log_success "Services deployed successfully"
}

wait_for_services() {
    log_info "Waiting for services to be healthy..."
    
    # Wait for database
    log_info "Checking database health..."
    for i in $(seq 1 $HEALTH_CHECK_RETRIES); do
        if docker-compose exec -T database pg_isready -U "${POSTGRES_USER:-erp_user}" -d "${POSTGRES_DB:-erp_system}" &> /dev/null; then
            log_success "Database is healthy"
            break
        fi
        
        if [ $i -eq $HEALTH_CHECK_RETRIES ]; then
            log_error "Database health check failed after $HEALTH_CHECK_RETRIES attempts"
            return 1
        fi
        
        log_info "Database not ready, waiting... (attempt $i/$HEALTH_CHECK_RETRIES)"
        sleep $HEALTH_CHECK_DELAY
    done
    
    # Wait for Redis
    log_info "Checking Redis health..."
    for i in $(seq 1 $HEALTH_CHECK_RETRIES); do
        if docker-compose exec -T redis redis-cli ping | grep -q "PONG"; then
            log_success "Redis is healthy"
            break
        fi
        
        if [ $i -eq $HEALTH_CHECK_RETRIES ]; then
            log_error "Redis health check failed after $HEALTH_CHECK_RETRIES attempts"
            return 1
        fi
        
        log_info "Redis not ready, waiting... (attempt $i/$HEALTH_CHECK_RETRIES)"
        sleep 10
    done
    
    # Wait for backend
    log_info "Checking backend health..."
    for i in $(seq 1 $HEALTH_CHECK_RETRIES); do
        if curl -f -s http://localhost:5000/api/v1/health &> /dev/null; then
            log_success "Backend is healthy"
            break
        fi
        
        if [ $i -eq $HEALTH_CHECK_RETRIES ]; then
            log_error "Backend health check failed after $HEALTH_CHECK_RETRIES attempts"
            return 1
        fi
        
        log_info "Backend not ready, waiting... (attempt $i/$HEALTH_CHECK_RETRIES)"
        sleep $HEALTH_CHECK_DELAY
    done
    
    # Wait for frontend
    log_info "Checking frontend health..."
    for i in $(seq 1 $HEALTH_CHECK_RETRIES); do
        if curl -f -s http://localhost/health &> /dev/null; then
            log_success "Frontend is healthy"
            break
        fi
        
        if [ $i -eq $HEALTH_CHECK_RETRIES ]; then
            log_error "Frontend health check failed after $HEALTH_CHECK_RETRIES attempts"
            return 1
        fi
        
        log_info "Frontend not ready, waiting... (attempt $i/$HEALTH_CHECK_RETRIES)"
        sleep 15
    done
    
    log_success "All services are healthy"
}

run_database_migrations() {
    log_info "Running database migrations..."
    
    # Run migrations through backend container
    docker-compose exec -T backend flask db upgrade
    
    log_success "Database migrations completed"
}

validate_deployment() {
    log_info "Validating deployment..."
    
    # Test basic API endpoint
    if ! curl -f -s http://localhost:5000/api/v1/health | grep -q "healthy"; then
        log_error "Backend health check failed"
        return 1
    fi
    
    # Test frontend
    if ! curl -f -s http://localhost/health | grep -q "healthy"; then
        log_error "Frontend health check failed"
        return 1
    fi
    
    # Test database connection through API
    if ! curl -f -s http://localhost:5000/api/v1/auth/login &> /dev/null; then
        log_error "Database connection test failed"
        return 1
    fi
    
    log_success "Deployment validation passed"
}

rollback_deployment() {
    log_error "Deployment failed, initiating rollback..."
    
    if [ -f ".last_backup" ]; then
        BACKUP_FILE=$(cat .last_backup)
        log_info "Restoring database from backup: $BACKUP_FILE"
        
        # Stop services
        docker-compose down
        
        # Restore database
        if [ -f "database/backups/$BACKUP_FILE" ]; then
            # Start only database for restore
            docker-compose up -d database
            
            # Wait for database
            sleep 30
            
            # Restore backup
            zcat "database/backups/$BACKUP_FILE" | \
                docker-compose exec -T database psql \
                -U "${POSTGRES_USER:-erp_user}" \
                -d "${POSTGRES_DB:-erp_system}"
            
            log_success "Database restored from backup"
        else
            log_warning "Backup file not found: database/backups/$BACKUP_FILE"
        fi
    else
        log_warning "No backup file recorded for rollback"
    fi
    
    # Stop all services
    docker-compose down
    
    log_error "Rollback completed. Please check the logs and fix issues before redeploying."
    exit 1
}

cleanup_old_resources() {
    log_info "Cleaning up old Docker resources..."
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes (be careful with this in production)
    if [ "${CLEANUP_VOLUMES}" = "true" ]; then
        docker volume prune -f
    fi
    
    # Remove unused networks
    docker network prune -f
    
    log_success "Cleanup completed"
}

show_deployment_status() {
    log_info "Deployment Status:"
    echo "=================================="
    docker-compose ps
    echo "=================================="
    
    log_info "Service URLs:"
    echo "Frontend: http://localhost"
    echo "Backend API: http://localhost:5000"
    echo "API Documentation: http://localhost:5000/api/docs"
    
    if echo "$COMPOSE_PROFILES" | grep -q "monitoring"; then
        echo "Grafana: http://localhost:3000"
        echo "Prometheus: http://localhost:9090"
    fi
    
    log_info "Check logs with: docker-compose logs -f [service_name]"
}

# Main deployment process
main() {
    log_info "Starting ERP System deployment..."
    log_info "Environment: $DEPLOYMENT_ENV"
    log_info "Profiles: $COMPOSE_PROFILES"
    
    # Create deployment timestamp
    DEPLOYMENT_START=$(date +%s)
    echo "Deployment started at: $(date)" > .deployment_log
    
    # Run deployment steps
    check_prerequisites
    validate_configuration
    backup_database
    build_images
    deploy_services
    
    # Health checks and validation
    if ! wait_for_services; then
        if [ "$ROLLBACK_ON_FAILURE" = "true" ]; then
            rollback_deployment
        else
            log_error "Service health checks failed. Manual intervention required."
            exit 1
        fi
    fi
    
    if ! run_database_migrations; then
        if [ "$ROLLBACK_ON_FAILURE" = "true" ]; then
            rollback_deployment
        else
            log_error "Database migrations failed. Manual intervention required."
            exit 1
        fi
    fi
    
    if ! validate_deployment; then
        if [ "$ROLLBACK_ON_FAILURE" = "true" ]; then
            rollback_deployment
        else
            log_error "Deployment validation failed. Manual intervention required."
            exit 1
        fi
    fi
    
    # Post-deployment tasks
    cleanup_old_resources
    
    # Calculate deployment time
    DEPLOYMENT_END=$(date +%s)
    DEPLOYMENT_TIME=$((DEPLOYMENT_END - DEPLOYMENT_START))
    
    # Success
    echo "Deployment completed at: $(date)" >> .deployment_log
    echo "Deployment time: ${DEPLOYMENT_TIME}s" >> .deployment_log
    
    log_success "ERP System deployed successfully!"
    log_success "Deployment completed in ${DEPLOYMENT_TIME} seconds"
    
    show_deployment_status
}

# Handle command line arguments
case "${1:-deploy}" in
    deploy)
        main
        ;;
    rollback)
        rollback_deployment
        ;;
    status)
        show_deployment_status
        ;;
    logs)
        docker-compose logs -f "${2:-}"
        ;;
    stop)
        log_info "Stopping ERP System..."
        docker-compose down
        log_success "ERP System stopped"
        ;;
    restart)
        log_info "Restarting ERP System..."
        docker-compose restart
        log_success "ERP System restarted"
        ;;
    backup)
        backup_database
        ;;
    *)
        echo "Usage: $0 {deploy|rollback|status|logs|stop|restart|backup}"
        echo ""
        echo "Commands:"
        echo "  deploy   - Deploy the ERP system (default)"
        echo "  rollback - Rollback to previous backup"
        echo "  status   - Show deployment status"
        echo "  logs     - Show service logs"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  backup   - Create database backup"
        exit 1
        ;;
esac