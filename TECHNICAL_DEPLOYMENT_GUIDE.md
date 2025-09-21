# ERP System Technical Deployment Guide

**Version:** 1.0  
**Last Updated:** September 7, 2025  
**Target Audience:** DevOps Engineers, System Administrators, Technical Teams

---

## 🏗️ System Architecture Overview

### **High-Level Architecture**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│  Frontend       │    │  Backend API    │    │  Database       │
│  Vue.js 3       │◄──►│  Flask 3.0      │◄──►│  PostgreSQL 17  │
│  TypeScript     │    │  SQLAlchemy     │    │  Production DB  │
│  Element Plus   │    │  JWT Auth       │    │  Backup System  │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
      Port 5177              Port 5000              Port 5432
```

### **Technology Stack**

#### **Backend Components**
- **Web Framework**: Flask 3.0 with Werkzeug 2.0
- **Database ORM**: SQLAlchemy 2.0 with async support
- **Authentication**: JWT tokens with 1-hour expiration
- **API Design**: RESTful APIs with OpenAPI 3.0 documentation
- **Database**: PostgreSQL 17 with connection pooling
- **Security**: bcrypt password hashing, CORS protection

#### **Frontend Components**
- **Framework**: Vue.js 3 with Composition API
- **Language**: TypeScript 4.9+ for type safety
- **UI Framework**: Element Plus 2.4+ with theme customization
- **State Management**: Pinia 2.0 for reactive state
- **Build Tool**: Vite 4.0 with optimized production builds
- **HTTP Client**: Axios with interceptors for authentication

#### **Database Schema Design**
```sql
-- Core Tables Structure
Users (id, username, password_hash, email, role_id, created_at)
Roles (id, name, permissions)
Suppliers (id, name, contact_info, payment_terms)
Requisitions (id, project_id, requester_id, status, created_at)
RequisitionItems (id, requisition_id, item_description, quantity, unit_cost)
PurchaseOrders (id, supplier_id, status, total_amount, created_at)
PurchaseOrderItems (id, purchase_order_id, requisition_item_id, quantity)
Inventory (id, item_id, quantity_on_hand, location, last_updated)
InventoryTransactions (id, item_id, transaction_type, quantity, timestamp)
```

---

## 🚀 Production Deployment Instructions

### **1. Infrastructure Requirements**

#### **Server Specifications**
```yaml
# Minimum Production Requirements
CPU: 4 cores (2.5GHz+)
RAM: 8GB minimum, 16GB recommended
Storage: 100GB SSD with backup capabilities
Network: 1Gbps connection
OS: Ubuntu 20.04 LTS or CentOS 8+

# Recommended Production Setup
CPU: 8 cores (3.0GHz+)
RAM: 32GB for optimal performance
Storage: 500GB SSD with RAID 1 backup
Network: Load balanced with redundancy
```

#### **Network Architecture**
```
Internet
    │
┌───▼────┐     ┌─────────────┐     ┌─────────────┐
│ nginx  │────►│ App Server  │────►│ Database    │
│ (SSL)  │     │ (Gunicorn)  │     │ (PostgreSQL)│
└────────┘     └─────────────┘     └─────────────┘
Port 443/80         Port 5000          Port 5432
```

### **2. Database Setup**

#### **PostgreSQL Installation & Configuration**
```bash
# Install PostgreSQL 17
sudo apt update
sudo apt install postgresql-17 postgresql-contrib

# Create production database
sudo -u postgres createdb erp_production

# Create database user
sudo -u postgres psql
CREATE USER erp_user WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE erp_production TO erp_user;
ALTER USER erp_user CREATEDB;
\q
```

#### **Database Performance Tuning**
```sql
-- postgresql.conf optimizations
shared_buffers = 256MB                # 25% of RAM
effective_cache_size = 1GB           # 75% of RAM
work_mem = 8MB                       # Per-query memory
maintenance_work_mem = 64MB          # Maintenance operations
checkpoint_completion_target = 0.9   # Checkpoint performance
wal_buffers = 16MB                   # Write-ahead log buffers
```

#### **Database Backup Strategy**
```bash
#!/bin/bash
# Daily backup script
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/postgresql"
pg_dump -U erp_user -h localhost erp_production > $BACKUP_DIR/erp_backup_$DATE.sql
gzip $BACKUP_DIR/erp_backup_$DATE.sql
find $BACKUP_DIR -name "erp_backup_*.sql.gz" -mtime +30 -delete
```

### **3. Backend Deployment**

#### **Python Environment Setup**
```bash
# Create production virtual environment
python3.9 -m venv /opt/erp/venv
source /opt/erp/venv/bin/activate

# Install production dependencies
cd /opt/erp/backend
pip install -r requirements.txt
pip install gunicorn
```

#### **Environment Configuration**
```bash
# /opt/erp/backend/.env
FLASK_ENV=production
SECRET_KEY=your-cryptographically-secure-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
DATABASE_URL=postgresql://erp_user:secure_password@localhost:5432/erp_production
CORS_ORIGINS=https://your-domain.com
LOG_LEVEL=INFO
BACKUP_ENABLED=true
```

#### **Gunicorn Production Configuration**
```python
# gunicorn_config.py
bind = "127.0.0.1:5000"
workers = 4  # 2 x CPU cores
worker_class = "gthread"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True
```

#### **Systemd Service Setup**
```ini
# /etc/systemd/system/erp-backend.service
[Unit]
Description=ERP Backend Application
After=network.target postgresql.service

[Service]
Type=notify
User=erp
Group=erp
WorkingDirectory=/opt/erp/backend
Environment=PATH=/opt/erp/venv/bin
ExecStart=/opt/erp/venv/bin/gunicorn -c gunicorn_config.py app:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### **4. Frontend Deployment**

#### **Node.js Production Setup**
```bash
# Install Node.js 18 LTS
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Build production frontend
cd /opt/erp/frontend
npm ci --production
npm run build
```

#### **Nginx Configuration**
```nginx
# /etc/nginx/sites-available/erp-system
server {
    listen 80;
    listen [::]:80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # Frontend static files
    location / {
        root /opt/erp/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
        
        # Caching for static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
}
```

---

## 🔐 Security Configuration

### **SSL/TLS Setup**
```bash
# Install Certbot for Let's Encrypt
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal setup
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### **Firewall Configuration**
```bash
# Configure UFW firewall
sudo ufw enable
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw deny 5000/tcp   # Block direct backend access
sudo ufw deny 5432/tcp   # Block direct database access
```

### **Application Security Settings**
```python
# Backend security configuration
SECURITY_HEADERS = {
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'Content-Security-Policy': "default-src 'self'",
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block'
}

JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
```

---

## 📊 Monitoring & Logging

### **Application Logging**
```python
# Logging configuration
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/erp/application.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'detailed'
        }
    },
    'formatters': {
        'detailed': {
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        }
    },
    'loggers': {
        'app': {
            'level': 'INFO',
            'handlers': ['file'],
            'propagate': False
        }
    }
}
```

### **System Monitoring Scripts**
```bash
#!/bin/bash
# Health check script
check_backend() {
    curl -f http://localhost:5000/api/health > /dev/null 2>&1
    return $?
}

check_database() {
    PGPASSWORD=$DB_PASSWORD psql -h localhost -U erp_user -d erp_production -c "SELECT 1;" > /dev/null 2>&1
    return $?
}

check_frontend() {
    curl -f https://your-domain.com > /dev/null 2>&1
    return $?
}

# Alert functions
send_alert() {
    echo "$1" | mail -s "ERP System Alert" admin@your-domain.com
}

# Main monitoring loop
if ! check_backend; then
    send_alert "Backend service is down"
fi

if ! check_database; then
    send_alert "Database connection failed"
fi

if ! check_frontend; then
    send_alert "Frontend is not accessible"
fi
```

### **Performance Monitoring**
```bash
# System metrics collection
echo "$(date): CPU $(top -bn1 | grep "Cpu(s)" | awk '{print $2}'), Memory $(free | grep Mem | awk '{printf "%.2f%%", $3/$2 * 100.0}'), Disk $(df -h / | awk 'NR==2{printf "%s", $5}')" >> /var/log/erp/metrics.log
```

---

## 🔄 Backup & Recovery

### **Automated Backup System**
```bash
#!/bin/bash
# Complete system backup script
BACKUP_DATE=$(date +%Y%m%d)
BACKUP_ROOT="/backup/erp"

# Database backup
pg_dump -U erp_user erp_production | gzip > $BACKUP_ROOT/db/erp_db_$BACKUP_DATE.sql.gz

# Application files backup
tar -czf $BACKUP_ROOT/app/erp_app_$BACKUP_DATE.tar.gz /opt/erp/

# Configuration backup
tar -czf $BACKUP_ROOT/config/erp_config_$BACKUP_DATE.tar.gz /etc/nginx/sites-available/erp-system /opt/erp/backend/.env

# Upload to cloud storage (optional)
# aws s3 cp $BACKUP_ROOT/db/erp_db_$BACKUP_DATE.sql.gz s3://your-backup-bucket/
```

### **Disaster Recovery Procedures**
```bash
# Database recovery
gunzip -c erp_db_backup.sql.gz | psql -U erp_user erp_production

# Application recovery
cd /opt/erp
tar -xzf erp_app_backup.tar.gz

# Restart services
sudo systemctl restart erp-backend
sudo systemctl restart nginx
```

---

## 🧪 Testing & Validation

### **Deployment Validation Checklist**
```bash
# Backend API testing
curl http://localhost:5000/api/health
curl -X POST http://localhost:5000/api/auth/login -H "Content-Type: application/json" -d '{"username":"admin","password":"admin123"}'

# Database connectivity
PGPASSWORD=$DB_PASSWORD psql -h localhost -U erp_user -d erp_production -c "SELECT count(*) FROM users;"

# Frontend accessibility
curl https://your-domain.com
curl https://your-domain.com/login

# SSL certificate validation
openssl s_client -connect your-domain.com:443 -servername your-domain.com
```

### **Load Testing**
```bash
# Install Artillery for load testing
npm install -g artillery

# Load test configuration
cat > load-test.yml << EOF
config:
  target: 'https://your-domain.com'
  phases:
    - duration: 60
      arrivalRate: 10
scenarios:
  - name: "Login and navigate"
    steps:
      - post:
          url: "/api/auth/login"
          json:
            username: "admin"
            password: "admin123"
      - get:
          url: "/api/v1/users"
EOF

# Run load test
artillery run load-test.yml
```

---

## 📋 Maintenance Procedures

### **Regular Maintenance Tasks**

#### **Daily Tasks (Automated)**
```bash
# Log rotation and cleanup
logrotate /etc/logrotate.d/erp-system

# Database maintenance
psql -U erp_user -d erp_production -c "VACUUM ANALYZE;"

# Certificate renewal check
certbot renew --dry-run
```

#### **Weekly Tasks**
```bash
# Security updates
sudo apt update && sudo apt upgrade -y

# Database backup verification
gunzip -t /backup/postgresql/erp_backup_*.sql.gz

# Performance metrics review
tail -100 /var/log/erp/metrics.log
```

#### **Monthly Tasks**
```bash
# Database optimization
psql -U erp_user -d erp_production -c "REINDEX DATABASE erp_production;"

# Log archive and cleanup
find /var/log/erp -name "*.log.*" -mtime +90 -delete

# Security audit
sudo lynis audit system
```

### **Emergency Procedures**

#### **Service Recovery**
```bash
# Backend service restart
sudo systemctl restart erp-backend
sudo systemctl status erp-backend

# Database recovery
sudo systemctl restart postgresql
sudo -u postgres pg_isready

# Frontend recovery
sudo systemctl restart nginx
sudo nginx -t
```

#### **Emergency Contacts**
- **Primary Developer**: Available 24/7 for critical issues
- **Database Administrator**: On-call rotation schedule
- **Infrastructure Team**: Escalation for hardware/network issues
- **Security Team**: Immediate notification for security incidents

---

## 📊 Performance Tuning

### **Database Optimization**
```sql
-- Create essential indexes
CREATE INDEX CONCURRENTLY idx_requisitions_status ON requisitions(status);
CREATE INDEX CONCURRENTLY idx_requisitions_created_at ON requisitions(created_at);
CREATE INDEX CONCURRENTLY idx_purchase_orders_supplier ON purchase_orders(supplier_id);
CREATE INDEX CONCURRENTLY idx_inventory_item_location ON inventory(item_id, location);

-- Update table statistics
ANALYZE requisitions;
ANALYZE purchase_orders;
ANALYZE inventory;
```

### **Application Performance**
```python
# Connection pooling configuration
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 20,
    'max_overflow': 0,
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

# Redis caching (optional)
CACHE_TYPE = "redis"
CACHE_REDIS_URL = "redis://localhost:6379/0"
```

### **Nginx Optimization**
```nginx
# Performance optimizations
worker_processes auto;
worker_connections 1024;

gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

# Connection optimization
keepalive_timeout 65;
client_max_body_size 100M;
```

---

## 🔍 Troubleshooting Guide

### **Common Issues & Solutions**

#### **Backend Connection Issues**
```bash
# Check service status
sudo systemctl status erp-backend

# Check logs
tail -f /var/log/erp/application.log

# Database connection test
PGPASSWORD=$DB_PASSWORD psql -h localhost -U erp_user -d erp_production -c "SELECT current_timestamp;"
```

#### **Frontend Loading Issues**
```bash
# Check nginx configuration
sudo nginx -t

# Check static file permissions
ls -la /opt/erp/frontend/dist/

# Clear browser cache and test
curl -I https://your-domain.com
```

#### **Performance Issues**
```sql
-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Check database connections
SELECT count(*) FROM pg_stat_activity;
```

---

## 📈 Scaling Considerations

### **Horizontal Scaling Options**
```yaml
# Load balancer configuration
Backend Servers:
  - server1.internal:5000
  - server2.internal:5000
  - server3.internal:5000

Database:
  - Primary: db-primary.internal:5432
  - Replica: db-replica.internal:5432 (read-only)
```

### **Vertical Scaling Thresholds**
- **CPU Usage** > 70% sustained: Add CPU cores
- **Memory Usage** > 80%: Increase RAM
- **Disk I/O** > 80%: Upgrade to faster storage
- **Database Connections** > 80% of max: Scale database server

---

This technical deployment guide provides comprehensive instructions for production deployment of the ERP system. Follow these procedures for a secure, performant, and maintainable production environment.

**Document Version**: 1.0  
**Next Review**: After first production deployment  
**Contact**: Technical Architecture Team