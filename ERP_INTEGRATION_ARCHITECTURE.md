# ERP System Integration Architecture
## Comprehensive Brownfield Modernization Strategy

**Architecture Lead:** Winston  
**Project:** ERP System Integration & Modernization  
**Timeline:** 12 weeks  
**Budget:** $262K  

---

## 1. System Architecture Overview

### Current State Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Vue.js 3      │    │   Flask API     │    │   SQLite/PG     │
│   Element Plus  │◄──►│   SQLAlchemy    │◄──►│   Config Mismatch│
│   Pinia Store   │    │   JWT Auth      │    │   Multiple DBs   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
      Frontend              Backend              Database
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │ 58% API     │    │ 2000ms+     │    │ No Pool     │
   │ Failures    │    │ Response    │    │ No Migration│
   │ CORS Issues │    │ Times       │    │ Strategy    │
   └─────────────┘    └─────────────┘    └─────────────┘
```

### Target State Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       Load Balancer + API Gateway              │
│                     (NGINX + Kong/Ambassador)                  │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                        Service Mesh                            │
│                      (Istio/Linkerd)                          │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────▼────────┐    ┌────────▼────────┐    ┌────────▼────────┐
│   Frontend      │    │   Backend API    │    │   Event Mesh    │
│   Vue.js 3      │    │   Flask + Redis  │    │   Redis Streams │
│   + PWA Cache   │    │   + Celery       │    │   + RabbitMQ    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                    Data Layer                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ PostgreSQL  │  │   Redis     │  │ File Store  │             │
│  │ Primary DB  │  │ Cache/Queue │  │ MinIO/S3    │             │
│  │ + Replica   │  │ + Sessions  │  │ Documents   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Data Layer Architecture

### Database Consolidation Strategy

**Phase 1: Immediate Stabilization (Week 1-2)**

```python
# Enhanced Database Configuration
# File: backend/config.py

class ProductionConfig(Config):
    # Primary Database with Connection Pooling
    SQLALCHEMY_DATABASE_URI = 'postgresql://erp_user:secure_password@postgres-primary:5432/erp_system'
    
    # Advanced Connection Pool Configuration
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,              # Base connections
        'max_overflow': 30,           # Additional connections
        'pool_pre_ping': True,        # Validate connections
        'pool_recycle': 3600,         # Recycle every hour
        'connect_args': {
            'connect_timeout': 10,
            'application_name': 'ERP_Backend',
            'options': '-c default_transaction_isolation=read_committed'
        }
    }
    
    # Read Replica Configuration
    SQLALCHEMY_BINDS = {
        'read_replica': 'postgresql://erp_readonly:password@postgres-replica:5432/erp_system'
    }
    
    # Redis Configuration
    REDIS_URL = 'redis://redis-cluster:6379/0'
    CELERY_BROKER_URL = 'redis://redis-cluster:6379/1'
    CELERY_RESULT_BACKEND = 'redis://redis-cluster:6379/2'
```

**Database Migration Strategy**

```python
# File: backend/database/migration_manager.py

class DatabaseMigrationManager:
    """Manages safe database migrations with zero downtime"""
    
    def __init__(self):
        self.primary_db = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        self.sqlite_dbs = self._discover_sqlite_files()
        
    def consolidate_sqlite_data(self):
        """Migrate all SQLite data to PostgreSQL"""
        migration_plan = {
            'users': self._migrate_users,
            'suppliers': self._migrate_suppliers,
            'requisitions': self._migrate_requisitions,
            'purchase_orders': self._migrate_purchase_orders
        }
        
        for table, migration_func in migration_plan.items():
            try:
                migration_func()
                self._validate_migration(table)
                logging.info(f"Successfully migrated {table}")
            except Exception as e:
                logging.error(f"Migration failed for {table}: {e}")
                self._rollback_migration(table)
    
    def _migrate_with_validation(self, source_query, target_table):
        """Migration with data validation"""
        # Extract from SQLite
        source_data = pd.read_sql(source_query, self.sqlite_db)
        
        # Validate data integrity
        validated_data = self._validate_data_quality(source_data)
        
        # Insert to PostgreSQL with batch processing
        validated_data.to_sql(target_table, self.primary_db, 
                            if_exists='append', index=False, 
                            method='multi', chunksize=1000)
```

### Caching Architecture

**Multi-Level Caching Strategy**

```python
# File: backend/cache/cache_manager.py

class CacheManager:
    """Multi-layer caching with Redis"""
    
    def __init__(self):
        self.redis_client = redis.Redis.from_url(Config.REDIS_URL)
        self.local_cache = {}  # Application-level cache
        
    def get_cached_data(self, key, fetch_func, ttl=3600):
        """Get data with fallback strategy"""
        # L1: Application cache
        if key in self.local_cache:
            return self.local_cache[key]
            
        # L2: Redis cache
        cached = self.redis_client.get(key)
        if cached:
            data = json.loads(cached)
            self.local_cache[key] = data
            return data
            
        # L3: Database fetch
        data = fetch_func()
        self._cache_data(key, data, ttl)
        return data
    
    def _cache_data(self, key, data, ttl):
        """Cache data at multiple levels"""
        # Redis cache
        self.redis_client.setex(key, ttl, json.dumps(data))
        # Local cache (with memory limit)
        if len(self.local_cache) < 1000:
            self.local_cache[key] = data

# Cache Configuration
CACHE_STRATEGIES = {
    'user_sessions': {'ttl': 3600, 'strategy': 'write_through'},
    'supplier_data': {'ttl': 7200, 'strategy': 'cache_aside'},
    'requisition_lists': {'ttl': 300, 'strategy': 'write_behind'},
    'system_settings': {'ttl': 86400, 'strategy': 'refresh_ahead'}
}
```

---

## 3. API Layer Design

### RESTful API Standardization

**Enhanced API Structure**

```python
# File: backend/api/base.py

class BaseAPIResource:
    """Standardized API base with performance optimization"""
    
    def __init__(self):
        self.cache_manager = CacheManager()
        self.rate_limiter = RateLimiter()
        
    def get(self, resource_id=None):
        """GET with caching and pagination"""
        # Rate limiting
        if not self.rate_limiter.allow_request(request.remote_addr):
            return {'error': 'Rate limit exceeded'}, 429
            
        # Caching for single resource
        if resource_id:
            cache_key = f"{self.__class__.__name__}:{resource_id}"
            return self.cache_manager.get_cached_data(
                cache_key, 
                lambda: self._fetch_single(resource_id)
            )
        
        # Pagination for lists
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        return self._fetch_paginated(page, per_page)
    
    def post(self, data):
        """POST with validation and async processing"""
        # Input validation
        if not self._validate_input(data):
            return {'error': 'Invalid input data'}, 400
            
        # Async processing for heavy operations
        if self._is_heavy_operation(data):
            task = process_async.delay(data)
            return {'task_id': task.id, 'status': 'processing'}, 202
            
        # Synchronous processing
        return self._process_sync(data)

# API Performance Middleware
class PerformanceMiddleware:
    def __init__(self, app):
        self.app = app
        
    def __call__(self, environ, start_response):
        start_time = time.time()
        
        def new_start_response(status, response_headers):
            duration = time.time() - start_time
            response_headers.append(('X-Response-Time', str(duration)))
            return start_response(status, response_headers)
            
        return self.app(environ, new_start_response)
```

### API Gateway Pattern

```yaml
# File: deployment/api-gateway.yaml

apiVersion: v1
kind: ConfigMap
metadata:
  name: kong-config
  namespace: erp-system
data:
  kong.yml: |
    _format_version: "2.1"
    
    services:
    - name: erp-backend
      url: http://backend-service:5000
      plugins:
      - name: rate-limiting
        config:
          minute: 100
          hour: 1000
      - name: response-caching
        config:
          cache_ttl: 300
          strategy: memory
      - name: prometheus
        config:
          per_consumer: true
    
    routes:
    - name: api-routes
      service: erp-backend
      paths:
      - /api
      plugins:
      - name: cors
        config:
          origins: ["*"]
          methods: ["GET", "POST", "PUT", "DELETE"]
          headers: ["Accept", "Content-Type", "Authorization"]
      - name: request-transformer
        config:
          add:
            headers:
            - "X-API-Version:v1"
            - "X-Request-ID:$(uuid)"
```

---

## 4. Integration Patterns

### Event-Driven Architecture

**Event Sourcing Implementation**

```python
# File: backend/events/event_manager.py

class EventManager:
    """Central event management with Redis Streams"""
    
    def __init__(self):
        self.redis_client = redis.Redis.from_url(Config.REDIS_URL)
        self.event_handlers = {}
        
    def publish_event(self, event_type, data, correlation_id=None):
        """Publish event to Redis Streams"""
        event = {
            'event_type': event_type,
            'data': json.dumps(data),
            'timestamp': datetime.utcnow().isoformat(),
            'correlation_id': correlation_id or str(uuid4())
        }
        
        # Publish to stream
        stream_name = f"events:{event_type}"
        message_id = self.redis_client.xadd(stream_name, event)
        
        # Update event log
        self._log_event(event, message_id)
        
        return message_id
    
    def subscribe_to_events(self, event_types, handler):
        """Subscribe to specific event types"""
        for event_type in event_types:
            if event_type not in self.event_handlers:
                self.event_handlers[event_type] = []
            self.event_handlers[event_type].append(handler)
    
    def process_events(self):
        """Process events from streams"""
        for event_type, handlers in self.event_handlers.items():
            stream_name = f"events:{event_type}"
            messages = self.redis_client.xread({stream_name: '$'}, block=1000)
            
            for stream, stream_messages in messages:
                for message_id, fields in stream_messages:
                    event_data = json.loads(fields[b'data'])
                    
                    for handler in handlers:
                        try:
                            handler(event_data)
                        except Exception as e:
                            self._handle_event_error(e, event_data, handler)

# Event Definitions
PROCUREMENT_EVENTS = {
    'requisition.created': 'When engineer creates requisition',
    'requisition.approved': 'When requisition is approved',
    'purchase_order.created': 'When PO is created',
    'supplier.delivery': 'When supplier delivers goods',
    'goods.accepted': 'When goods are accepted',
    'invoice.payment': 'When accounting processes payment'
}
```

### WebSocket Integration

```python
# File: backend/websocket/realtime_manager.py

class RealtimeManager:
    """Real-time updates with WebSocket"""
    
    def __init__(self, socketio):
        self.socketio = socketio
        self.user_sessions = {}
        
    def connect_user(self, user_id, session_id):
        """Track user connections"""
        self.user_sessions[user_id] = session_id
        
        # Join user-specific room
        join_room(f"user_{user_id}")
        
        # Join department room
        user = User.query.get(user_id)
        if user:
            join_room(f"dept_{user.department}")
    
    def notify_requisition_update(self, requisition_id, update_type):
        """Notify relevant users of requisition updates"""
        requisition = RequestOrder.query.get(requisition_id)
        
        # Notify creator
        self.socketio.emit('requisition_update', {
            'requisition_id': requisition_id,
            'update_type': update_type,
            'timestamp': datetime.utcnow().isoformat()
        }, room=f"user_{requisition.user_id}")
        
        # Notify procurement team
        self.socketio.emit('procurement_notification', {
            'requisition_id': requisition_id,
            'update_type': update_type,
            'priority': self._calculate_priority(requisition)
        }, room="dept_採購部")
    
    def broadcast_system_notification(self, message, level='info'):
        """Broadcast system-wide notifications"""
        self.socketio.emit('system_notification', {
            'message': message,
            'level': level,
            'timestamp': datetime.utcnow().isoformat()
        }, broadcast=True)

# Real-time Event Handlers
@socketio.on('connect')
def handle_connect():
    user_id = get_current_user_id()
    session_id = request.sid
    realtime_manager.connect_user(user_id, session_id)

@socketio.on('subscribe_to_updates')
def handle_subscription(data):
    subscription_type = data.get('type')
    if subscription_type == 'requisitions':
        join_room('requisition_updates')
    elif subscription_type == 'purchase_orders':
        join_room('po_updates')
```

---

## 5. Performance Architecture

### Caching Strategy Implementation

```python
# File: backend/performance/cache_layers.py

class MultiLevelCache:
    """Comprehensive caching strategy"""
    
    def __init__(self):
        # L1: In-memory cache (fastest)
        self.memory_cache = TTLCache(maxsize=1000, ttl=300)
        
        # L2: Redis cache (distributed)
        self.redis_client = redis.Redis.from_url(Config.REDIS_URL)
        
        # L3: Database query cache
        self.query_cache = {}
        
    @lru_cache(maxsize=100)
    def get_user_permissions(self, user_id):
        """Cache user permissions with LRU"""
        return self._fetch_user_permissions(user_id)
    
    def cache_supplier_data(self):
        """Preload frequently accessed supplier data"""
        suppliers = Supplier.query.filter_by(status='active').all()
        supplier_data = {
            s.supplier_id: {
                'name_zh': s.supplier_name_zh,
                'name_en': s.supplier_name_en,
                'region': s.supplier_region,
                'payment_terms': s.payment_terms
            } for s in suppliers
        }
        
        # Cache for 2 hours
        self.redis_client.setex(
            'suppliers:active', 
            7200, 
            json.dumps(supplier_data)
        )
        
    def invalidate_cache(self, pattern):
        """Intelligent cache invalidation"""
        # Invalidate Redis keys matching pattern
        keys = self.redis_client.keys(pattern)
        if keys:
            self.redis_client.delete(*keys)
            
        # Clear related memory cache
        if 'suppliers' in pattern:
            self.memory_cache.clear()

# Database Query Optimization
class QueryOptimizer:
    """Optimize database queries for performance"""
    
    @staticmethod
    def optimize_requisition_queries():
        """Optimize frequent requisition queries"""
        # Create indexes for common queries
        indexes = [
            'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_requisitions_user_status 
             ON request_orders(user_id, status) WHERE status IN (\'draft\', \'submitted\');',
            
            'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_requisitions_created_date 
             ON request_orders(created_at DESC) WHERE created_at > NOW() - INTERVAL \'30 days\';',
            
            'CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_suppliers_region_status 
             ON suppliers(supplier_region, status) WHERE status = \'active\';'
        ]
        
        for index_sql in indexes:
            db.session.execute(text(index_sql))
        db.session.commit()
    
    @staticmethod
    def create_materialized_views():
        """Create materialized views for complex queries"""
        views = {
            'procurement_dashboard': '''
                CREATE MATERIALIZED VIEW IF NOT EXISTS procurement_dashboard AS
                SELECT 
                    DATE_TRUNC('day', created_at) as date,
                    COUNT(*) as total_requisitions,
                    COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_count,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_count,
                    AVG(CASE WHEN approved_at IS NOT NULL 
                        THEN EXTRACT(epoch FROM approved_at - created_at)/3600 END) as avg_approval_hours
                FROM request_orders 
                WHERE created_at > NOW() - INTERVAL '90 days'
                GROUP BY DATE_TRUNC('day', created_at)
                ORDER BY date DESC;
            ''',
            
            'supplier_performance': '''
                CREATE MATERIALIZED VIEW IF NOT EXISTS supplier_performance AS
                SELECT 
                    s.supplier_id,
                    s.supplier_name_zh,
                    COUNT(po.id) as total_orders,
                    AVG(EXTRACT(epoch FROM po.delivery_date - po.created_at)/86400) as avg_delivery_days,
                    COUNT(CASE WHEN po.status = 'completed' THEN 1 END)::float / COUNT(po.id) as completion_rate
                FROM suppliers s
                LEFT JOIN purchase_orders po ON s.supplier_id = po.supplier_id
                WHERE po.created_at > NOW() - INTERVAL '180 days'
                GROUP BY s.supplier_id, s.supplier_name_zh;
            '''
        }
        
        for view_name, view_sql in views.items():
            db.session.execute(text(view_sql))
        db.session.commit()
```

### Async Processing with Celery

```python
# File: backend/tasks/async_tasks.py

from celery import Celery

celery_app = Celery('erp_tasks')
celery_app.config_from_object('celeryconfig')

@celery_app.task(bind=True, max_retries=3)
def process_purchase_order(self, po_data):
    """Async purchase order processing"""
    try:
        # Create purchase order
        po = PurchaseOrder(**po_data)
        db.session.add(po)
        db.session.commit()
        
        # Send to supplier (email/API)
        send_po_to_supplier.delay(po.id)
        
        # Update inventory reservations
        update_inventory_reservations.delay(po.id)
        
        # Log for audit
        log_audit_event.delay('po_created', po.id)
        
        return {'status': 'success', 'po_id': po.id}
        
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@celery_app.task
def generate_procurement_report(report_type, date_range):
    """Generate reports asynchronously"""
    if report_type == 'monthly_summary':
        return generate_monthly_summary(date_range)
    elif report_type == 'supplier_performance':
        return generate_supplier_performance_report(date_range)
    
@celery_app.task(rate_limit='10/m')
def send_email_notification(email_type, recipient, data):
    """Rate-limited email notifications"""
    templates = {
        'requisition_approved': 'emails/requisition_approved.html',
        'po_created': 'emails/po_created.html',
        'delivery_reminder': 'emails/delivery_reminder.html'
    }
    
    send_email(
        recipient=recipient,
        template=templates[email_type],
        data=data
    )
```

---

## 6. Security Architecture

### Zero-Trust Security Implementation

```python
# File: backend/security/zero_trust.py

class ZeroTrustSecurity:
    """Implement zero-trust security principles"""
    
    def __init__(self):
        self.vault_client = hvac.Client(url=Config.VAULT_URL)
        self.security_logger = SecurityLogger()
        
    def authenticate_request(self, request):
        """Multi-factor authentication check"""
        # Extract token
        token = self._extract_token(request)
        if not token:
            raise SecurityException("Missing authentication token")
            
        # Validate JWT
        payload = self._validate_jwt(token)
        
        # Check token freshness
        if self._is_token_stale(payload):
            raise SecurityException("Token requires refresh")
            
        # Verify user status
        user = User.query.get(payload['sub'])
        if not user or user.status != 'active':
            raise SecurityException("Invalid user status")
            
        # Check IP whitelist for sensitive operations
        if self._is_sensitive_endpoint(request.endpoint):
            self._verify_ip_whitelist(request.remote_addr, user)
            
        return user
    
    def authorize_action(self, user, resource, action):
        """Fine-grained authorization"""
        # Role-based permissions
        role_permissions = self._get_role_permissions(user.role)
        
        # Resource-specific permissions
        resource_permissions = self._get_resource_permissions(user, resource)
        
        # Department-based access
        dept_permissions = self._get_department_permissions(user.department)
        
        # Combine and check
        allowed = (
            action in role_permissions and
            action in resource_permissions and
            action in dept_permissions
        )
        
        # Log authorization attempt
        self.security_logger.log_authorization(
            user.id, resource, action, allowed
        )
        
        return allowed
    
    def encrypt_sensitive_data(self, data, context):
        """Field-level encryption with Vault"""
        encrypted_fields = {}
        
        for field, value in data.items():
            if field in Config.SENSITIVE_FIELDS:
                # Use Vault transit engine
                encrypted_value = self.vault_client.secrets.transit.encrypt_data(
                    name='erp-encryption',
                    plaintext=base64.b64encode(value.encode()).decode(),
                    context=base64.b64encode(context.encode()).decode()
                )
                encrypted_fields[field] = encrypted_value['data']['ciphertext']
            else:
                encrypted_fields[field] = value
                
        return encrypted_fields

# API Security Middleware
class SecurityMiddleware:
    def __init__(self, app):
        self.app = app
        self.security = ZeroTrustSecurity()
        
    def __call__(self, environ, start_response):
        # Rate limiting by IP
        if not self._check_rate_limit(environ['REMOTE_ADDR']):
            return self._rate_limit_response(start_response)
            
        # Security headers
        def secure_start_response(status, headers):
            security_headers = [
                ('X-Content-Type-Options', 'nosniff'),
                ('X-Frame-Options', 'DENY'),
                ('X-XSS-Protection', '1; mode=block'),
                ('Strict-Transport-Security', 'max-age=31536000; includeSubDomains'),
                ('Content-Security-Policy', "default-src 'self'"),
                ('Referrer-Policy', 'strict-origin-when-cross-origin')
            ]
            headers.extend(security_headers)
            return start_response(status, headers)
            
        return self.app(environ, secure_start_response)
```

### Secrets Management with HashiCorp Vault

```python
# File: backend/security/vault_manager.py

class VaultManager:
    """Centralized secrets management"""
    
    def __init__(self):
        self.client = hvac.Client(url=Config.VAULT_URL)
        self._authenticate()
        
    def _authenticate(self):
        """Authenticate with Vault using Kubernetes auth"""
        if Config.ENVIRONMENT == 'kubernetes':
            # Use Kubernetes service account
            jwt_token = open('/var/run/secrets/kubernetes.io/serviceaccount/token').read()
            self.client.auth.kubernetes.login(
                role='erp-backend',
                jwt=jwt_token
            )
        else:
            # Use AppRole for other environments
            self.client.auth.approle.login(
                role_id=Config.VAULT_ROLE_ID,
                secret_id=Config.VAULT_SECRET_ID
            )
    
    def get_database_credentials(self):
        """Get dynamic database credentials"""
        response = self.client.secrets.database.generate_credentials(
            name='erp-database-role'
        )
        return {
            'username': response['data']['username'],
            'password': response['data']['password']
        }
    
    def get_encryption_key(self, key_name):
        """Get encryption key from Vault"""
        response = self.client.secrets.kv.v2.read_secret_version(
            path=f'encryption-keys/{key_name}'
        )
        return response['data']['data']['key']
    
    def rotate_secrets(self):
        """Automated secret rotation"""
        secrets_to_rotate = ['jwt-secret', 'database-password', 'api-keys']
        
        for secret in secrets_to_rotate:
            new_value = self._generate_secure_secret()
            self.client.secrets.kv.v2.create_or_update_secret(
                path=f'erp/{secret}',
                secret={'value': new_value, 'rotated_at': datetime.utcnow().isoformat()}
            )
```

---

## 7. Deployment Architecture

### Container Orchestration Strategy

```dockerfile
# File: deployment/dockerfiles/Dockerfile.backend

FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r erp && useradd -r -g erp erp

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=erp:erp . .

# Production stage
FROM base as production

# Install additional production dependencies
RUN pip install gunicorn gevent

# Set production environment
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Switch to non-root user
USER erp

# Expose port
EXPOSE 5000

# Start application with Gunicorn
CMD ["gunicorn", "--config", "gunicorn.conf.py", "wsgi:application"]
```

### Blue-Green Deployment

```yaml
# File: deployment/blue-green/deployment-script.yaml

apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  name: blue-green-deployment
  namespace: erp-system
spec:
  entrypoint: blue-green-deploy
  
  templates:
  - name: blue-green-deploy
    steps:
    - - name: deploy-green
        template: deploy-version
        arguments:
          parameters:
          - name: version
            value: "{{workflow.parameters.new-version}}"
          - name: environment
            value: "green"
    
    - - name: run-tests
        template: integration-tests
        arguments:
          parameters:
          - name: environment
            value: "green"
    
    - - name: traffic-switch
        template: switch-traffic
        when: "{{steps.run-tests.outputs.result}} == Success"
    
    - - name: cleanup-blue
        template: cleanup-environment
        arguments:
          parameters:
          - name: environment
            value: "blue"

  - name: deploy-version
    inputs:
      parameters:
      - name: version
      - name: environment
    container:
      image: kubectl:latest
      command: [sh, -c]
      args:
      - |
        # Update deployment with new image
        kubectl set image deployment/backend-{{inputs.parameters.environment}} \
          backend=erp/backend:{{inputs.parameters.version}} \
          -n erp-system
        
        # Wait for rollout
        kubectl rollout status deployment/backend-{{inputs.parameters.environment}} \
          -n erp-system --timeout=300s

  - name: integration-tests
    inputs:
      parameters:
      - name: environment
    container:
      image: erp/test-runner:latest
      command: [python, -m, pytest]
      args:
      - tests/integration/
      - --environment={{inputs.parameters.environment}}
      - --verbose
```

### Feature Flag Architecture

```python
# File: backend/features/feature_flags.py

class FeatureFlags:
    """Feature flag management for gradual rollouts"""
    
    def __init__(self):
        self.redis_client = redis.Redis.from_url(Config.REDIS_URL)
        self.default_flags = {
            'new_requisition_ui': False,
            'async_po_processing': False,
            'advanced_reporting': False,
            'real_time_notifications': True
        }
    
    def is_enabled(self, flag_name, user_id=None, percentage=None):
        """Check if feature flag is enabled"""
        # Get flag configuration
        flag_config = self._get_flag_config(flag_name)
        
        if not flag_config:
            return self.default_flags.get(flag_name, False)
        
        # Global enable/disable
        if flag_config.get('global_enabled') is False:
            return False
        if flag_config.get('global_enabled') is True:
            return True
        
        # User-specific flags
        if user_id and str(user_id) in flag_config.get('user_whitelist', []):
            return True
        
        # Percentage rollout
        if percentage and flag_config.get('percentage', 0) >= percentage:
            # Use consistent hashing for user
            if user_id:
                hash_value = hash(f"{flag_name}:{user_id}") % 100
                return hash_value < flag_config['percentage']
        
        return False
    
    def set_flag(self, flag_name, config):
        """Set feature flag configuration"""
        self.redis_client.setex(
            f"feature_flag:{flag_name}",
            86400,  # 24 hours
            json.dumps(config)
        )
    
    def gradual_rollout(self, flag_name, target_percentage, step_size=10):
        """Gradually increase feature flag percentage"""
        current_config = self._get_flag_config(flag_name)
        current_percentage = current_config.get('percentage', 0)
        
        if current_percentage < target_percentage:
            new_percentage = min(
                current_percentage + step_size,
                target_percentage
            )
            
            current_config['percentage'] = new_percentage
            self.set_flag(flag_name, current_config)
            
            return new_percentage
        
        return current_percentage

# Usage in views
@app.route('/api/requisitions')
@jwt_required()
def get_requisitions():
    user_id = get_jwt_identity()
    
    # Check feature flag for new UI
    if feature_flags.is_enabled('new_requisition_ui', user_id):
        return get_requisitions_v2()
    else:
        return get_requisitions_v1()
```

---

## 8. Monitoring & Observability

### Distributed Tracing with OpenTelemetry

```python
# File: backend/monitoring/tracing.py

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

class TracingManager:
    """Distributed tracing setup"""
    
    def __init__(self, app):
        self.app = app
        self.setup_tracing()
        
    def setup_tracing(self):
        """Configure OpenTelemetry tracing"""
        # Set up tracer provider
        trace.set_tracer_provider(TracerProvider())
        tracer = trace.get_tracer(__name__)
        
        # Configure Jaeger exporter
        jaeger_exporter = JaegerExporter(
            agent_host_name=Config.JAEGER_HOST,
            agent_port=Config.JAEGER_PORT
        )
        
        # Add span processor
        span_processor = BatchSpanProcessor(jaeger_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)
        
        # Auto-instrument Flask
        FlaskInstrumentor().instrument_app(self.app)
        
        # Auto-instrument SQLAlchemy
        SQLAlchemyInstrumentor().instrument()
    
    @staticmethod
    def trace_business_operation(operation_name):
        """Decorator for tracing business operations"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                tracer = trace.get_tracer(__name__)
                with tracer.start_as_current_span(operation_name) as span:
                    # Add custom attributes
                    span.set_attribute("operation.name", operation_name)
                    span.set_attribute("user.id", getattr(g, 'user_id', 'anonymous'))
                    
                    try:
                        result = func(*args, **kwargs)
                        span.set_attribute("operation.status", "success")
                        return result
                    except Exception as e:
                        span.set_attribute("operation.status", "error")
                        span.record_exception(e)
                        raise
            return wrapper
        return decorator

# Usage in business logic
@trace_business_operation("create_purchase_order")
def create_purchase_order(requisition_id, supplier_id):
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("validate_requisition") as span:
        requisition = RequestOrder.query.get(requisition_id)
        span.set_attribute("requisition.id", requisition_id)
        span.set_attribute("requisition.status", requisition.status)
    
    with tracer.start_as_current_span("create_po_record"):
        po = PurchaseOrder(
            requisition_id=requisition_id,
            supplier_id=supplier_id,
            status='pending'
        )
        db.session.add(po)
        db.session.commit()
    
    return po
```

### Metrics Collection with Prometheus

```python
# File: backend/monitoring/metrics.py

from prometheus_client import Counter, Histogram, Gauge, start_http_server

class MetricsCollector:
    """Prometheus metrics collection"""
    
    def __init__(self):
        # Request metrics
        self.request_count = Counter(
            'erp_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status']
        )
        
        self.request_duration = Histogram(
            'erp_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint']
        )
        
        # Business metrics
        self.requisitions_created = Counter(
            'erp_requisitions_created_total',
            'Total requisitions created',
            ['department', 'user_role']
        )
        
        self.purchase_orders_processed = Counter(
            'erp_purchase_orders_processed_total',
            'Total purchase orders processed',
            ['supplier_region', 'status']
        )
        
        # System metrics
        self.active_sessions = Gauge(
            'erp_active_sessions',
            'Number of active user sessions'
        )
        
        self.database_connections = Gauge(
            'erp_database_connections',
            'Number of active database connections'
        )
    
    def record_request(self, method, endpoint, status, duration):
        """Record HTTP request metrics"""
        self.request_count.labels(
            method=method,
            endpoint=endpoint,
            status=status
        ).inc()
        
        self.request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_business_event(self, event_type, **labels):
        """Record business event metrics"""
        if event_type == 'requisition_created':
            self.requisitions_created.labels(**labels).inc()
        elif event_type == 'po_processed':
            self.purchase_orders_processed.labels(**labels).inc()
    
    def update_system_metrics(self):
        """Update system-level metrics"""
        # Count active sessions
        active_count = self._count_active_sessions()
        self.active_sessions.set(active_count)
        
        # Count database connections
        db_connections = self._count_db_connections()
        self.database_connections.set(db_connections)

# Metrics middleware
class MetricsMiddleware:
    def __init__(self, app, metrics_collector):
        self.app = app
        self.metrics = metrics_collector
        
    def __call__(self, environ, start_response):
        start_time = time.time()
        method = environ['REQUEST_METHOD']
        endpoint = environ.get('PATH_INFO', '')
        
        def metrics_start_response(status, headers):
            duration = time.time() - start_time
            status_code = status.split()[0]
            
            self.metrics.record_request(method, endpoint, status_code, duration)
            return start_response(status, headers)
            
        return self.app(environ, metrics_start_response)
```

### Log Aggregation Strategy

```python
# File: backend/logging/log_manager.py

import structlog
from pythonjsonlogger import jsonlogger

class LogManager:
    """Structured logging with ELK stack integration"""
    
    def __init__(self):
        self.setup_structured_logging()
        
    def setup_structured_logging(self):
        """Configure structured logging"""
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        # Configure standard logging
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s'
        )
        
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)
    
    @staticmethod
    def get_logger(name):
        """Get a structured logger"""
        return structlog.get_logger(name)
    
    @staticmethod
    def log_business_event(event_type, **context):
        """Log business events with context"""
        logger = structlog.get_logger("business_events")
        logger.info(
            "Business event occurred",
            event_type=event_type,
            **context
        )
    
    @staticmethod
    def log_security_event(event_type, user_id=None, ip_address=None, **context):
        """Log security events"""
        logger = structlog.get_logger("security")
        logger.warning(
            "Security event",
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            **context
        )

# Usage in application
logger = LogManager.get_logger("erp.procurement")

@app.route('/api/requisitions', methods=['POST'])
@jwt_required()
def create_requisition():
    user_id = get_jwt_identity()
    
    try:
        # Log business event
        LogManager.log_business_event(
            "requisition_creation_started",
            user_id=user_id,
            department=g.current_user.department
        )
        
        # Create requisition
        requisition = create_requisition_logic(request.json)
        
        # Log success
        logger.info(
            "Requisition created successfully",
            requisition_id=requisition.id,
            user_id=user_id,
            total_amount=requisition.total_amount
        )
        
        return jsonify(requisition.to_dict()), 201
        
    except ValidationError as e:
        logger.warning(
            "Requisition creation failed - validation error",
            user_id=user_id,
            error=str(e),
            input_data=request.json
        )
        return jsonify({'error': str(e)}), 400
        
    except Exception as e:
        logger.error(
            "Requisition creation failed - system error",
            user_id=user_id,
            error=str(e),
            exc_info=True
        )
        return jsonify({'error': 'Internal server error'}), 500
```

---

## 9. Scalability Design

### Horizontal Scaling Strategy

```python
# File: backend/scaling/load_balancer.py

class LoadBalancingStrategy:
    """Intelligent load balancing for ERP components"""
    
    def __init__(self):
        self.service_registry = ServiceRegistry()
        self.health_checker = HealthChecker()
        
    def route_request(self, request_type, payload):
        """Route requests based on type and load"""
        if request_type == 'read_heavy':
            return self._route_to_read_replica(payload)
        elif request_type == 'write_heavy':
            return self._route_to_write_primary(payload)
        elif request_type == 'compute_intensive':
            return self._route_to_compute_nodes(payload)
        else:
            return self._route_round_robin(payload)
    
    def _route_to_read_replica(self, payload):
        """Route read operations to read replicas"""
        read_replicas = self.service_registry.get_healthy_services('read_replica')
        
        if not read_replicas:
            # Fallback to primary
            return self._route_to_write_primary(payload)
        
        # Choose replica with lowest load
        selected_replica = min(read_replicas, key=lambda x: x.current_load)
        return self._execute_request(selected_replica, payload)
    
    def _auto_scale_decision(self):
        """Automated scaling decisions based on metrics"""
        metrics = self._collect_metrics()
        
        scaling_decisions = []
        
        # CPU-based scaling
        if metrics['avg_cpu_usage'] > 80:
            scaling_decisions.append({
                'action': 'scale_up',
                'service': 'backend',
                'replicas': self._calculate_replica_increase(metrics['avg_cpu_usage'])
            })
        elif metrics['avg_cpu_usage'] < 30:
            scaling_decisions.append({
                'action': 'scale_down',
                'service': 'backend',
                'replicas': 1
            })
        
        # Memory-based scaling
        if metrics['avg_memory_usage'] > 85:
            scaling_decisions.append({
                'action': 'scale_up',
                'service': 'backend',
                'reason': 'memory_pressure'
            })
        
        # Queue length based scaling
        if metrics['queue_length'] > 1000:
            scaling_decisions.append({
                'action': 'scale_up',
                'service': 'worker',
                'replicas': math.ceil(metrics['queue_length'] / 500)
            })
        
        return scaling_decisions

# Database Sharding Strategy
class DatabaseSharding:
    """Implement database sharding for scalability"""
    
    def __init__(self):
        self.shard_configs = {
            'shard_1': 'postgresql://user:pass@db-shard-1:5432/erp_shard_1',
            'shard_2': 'postgresql://user:pass@db-shard-2:5432/erp_shard_2',
            'shard_3': 'postgresql://user:pass@db-shard-3:5432/erp_shard_3'
        }
        
    def get_shard_for_tenant(self, tenant_id):
        """Determine shard based on tenant ID"""
        # Use consistent hashing
        shard_number = hash(tenant_id) % len(self.shard_configs)
        return f'shard_{shard_number + 1}'
    
    def get_shard_for_data(self, table, data):
        """Determine shard based on data characteristics"""
        if table == 'request_orders':
            # Shard by user department
            department_hash = hash(data.get('department', '')) % len(self.shard_configs)
            return f'shard_{department_hash + 1}'
        elif table == 'suppliers':
            # Shard by supplier region
            region = data.get('supplier_region', 'domestic')
            if region == 'domestic':
                return 'shard_1'
            elif region == 'international':
                return 'shard_2'
            else:
                return 'shard_3'
        else:
            # Default sharding by primary key
            pk_hash = hash(str(data.get('id', 0))) % len(self.shard_configs)
            return f'shard_{pk_hash + 1}'
    
    def execute_cross_shard_query(self, query, params):
        """Execute queries across multiple shards"""
        results = []
        
        for shard_name, shard_url in self.shard_configs.items():
            try:
                engine = create_engine(shard_url)
                result = engine.execute(query, params)
                results.extend(result.fetchall())
            except Exception as e:
                logger.error(f"Query failed on {shard_name}: {e}")
        
        return results
```

### Microservices Migration Path

```python
# File: backend/microservices/service_decomposition.py

class ServiceDecomposition:
    """Plan for gradual microservices migration"""
    
    def __init__(self):
        self.migration_phases = {
            'phase_1': ['user_service', 'auth_service'],
            'phase_2': ['supplier_service', 'inventory_service'],
            'phase_3': ['procurement_service', 'approval_service'],
            'phase_4': ['reporting_service', 'notification_service']
        }
    
    def extract_service(self, service_name):
        """Extract service from monolith"""
        if service_name == 'user_service':
            return self._extract_user_service()
        elif service_name == 'supplier_service':
            return self._extract_supplier_service()
        # ... other services
    
    def _extract_user_service(self):
        """Extract user management into separate service"""
        service_definition = {
            'name': 'user_service',
            'database': 'postgresql://user_service_db:5432/users',
            'api_endpoints': [
                '/users',
                '/users/{id}',
                '/users/{id}/permissions',
                '/departments',
                '/roles'
            ],
            'events_published': [
                'user.created',
                'user.updated',
                'user.deactivated'
            ],
            'events_consumed': [
                'auth.login_attempt',
                'auth.password_changed'
            ]
        }
        
        return service_definition
    
    def create_service_contracts(self):
        """Define service contracts for API compatibility"""
        contracts = {
            'user_service': {
                'version': 'v1',
                'endpoints': {
                    'GET /users/{id}': {
                        'response_schema': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'username': {'type': 'string'},
                                'chinese_name': {'type': 'string'},
                                'department': {'type': 'string'},
                                'role': {'type': 'string'},
                                'status': {'type': 'string'}
                            }
                        }
                    }
                }
            }
        }
        
        return contracts
```

---

## 10. Integration Testing Strategy

### Contract Testing Implementation

```python
# File: tests/integration/contract_tests.py

import pact
from pact import Consumer, Provider

class ContractTesting:
    """Implement contract testing between services"""
    
    def __init__(self):
        self.pact = Consumer('frontend').has_pact_with(Provider('backend'))
    
    def test_get_user_contract(self):
        """Test user API contract"""
        # Define expected interaction
        (self.pact
         .given('user exists')
         .upon_receiving('a request for user details')
         .with_request('GET', '/api/users/1')
         .will_respond_with(200, body={
             'id': 1,
             'username': 'test_user',
             'chinese_name': '測試用戶',
             'department': '工程部',
             'role': 'Everyone'
         }))
        
        # Execute test
        with self.pact:
            response = requests.get('http://localhost:5000/api/users/1')
            assert response.status_code == 200
            assert response.json()['username'] == 'test_user'
    
    def test_create_requisition_contract(self):
        """Test requisition creation contract"""
        requisition_data = {
            'requisition_number': 'REQ001',
            'department': '工程部',
            'items': [
                {
                    'item_name': '電阻器',
                    'quantity': 100,
                    'unit_price': 0.5,
                    'supplier_id': 'S001'
                }
            ]
        }
        
        (self.pact
         .given('user is authenticated')
         .upon_receiving('a request to create requisition')
         .with_request('POST', '/api/requisitions', body=requisition_data)
         .will_respond_with(201, body={
             'id': 1,
             'requisition_number': 'REQ001',
             'status': 'draft',
             'created_at': '2024-01-01T00:00:00Z'
         }))
        
        with self.pact:
            response = requests.post(
                'http://localhost:5000/api/requisitions',
                json=requisition_data,
                headers={'Authorization': 'Bearer token'}
            )
            assert response.status_code == 201

# Performance Testing Framework
class PerformanceTests:
    """Comprehensive performance testing"""
    
    def __init__(self):
        self.locust_client = HttpUser()
        
    def test_api_response_times(self):
        """Test API response time requirements"""
        endpoints = [
            {'url': '/api/users', 'max_time': 200},
            {'url': '/api/suppliers', 'max_time': 300},
            {'url': '/api/requisitions', 'max_time': 500},
            {'url': '/api/purchase-orders', 'max_time': 800}
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = self.locust_client.client.get(endpoint['url'])
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            
            assert response.status_code == 200
            assert response_time < endpoint['max_time'], \
                f"Response time {response_time}ms exceeds limit {endpoint['max_time']}ms"
    
    def test_concurrent_user_load(self):
        """Test system under concurrent load"""
        # Simulate 500 concurrent users
        user_scenarios = [
            self._simulate_engineer_workflow,
            self._simulate_procurement_workflow,
            self._simulate_admin_workflow
        ]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=500) as executor:
            futures = []
            
            for i in range(500):
                scenario = random.choice(user_scenarios)
                future = executor.submit(scenario, user_id=i)
                futures.append(future)
            
            # Wait for all scenarios to complete
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                assert result['success'] == True, f"Scenario failed: {result['error']}"

# Chaos Engineering Tests
class ChaosTests:
    """Test system resilience under failure conditions"""
    
    def test_database_failover(self):
        """Test database failover behavior"""
        # Simulate primary database failure
        self._simulate_database_failure('primary')
        
        # Verify system switches to replica
        response = requests.get('/api/users')
        assert response.status_code == 200
        
        # Verify data consistency
        user_data = response.json()
        assert len(user_data) > 0
    
    def test_redis_cache_failure(self):
        """Test behavior when Redis cache fails"""
        # Simulate Redis failure
        self._simulate_redis_failure()
        
        # Verify system degrades gracefully
        response = requests.get('/api/suppliers')
        assert response.status_code == 200
        
        # Response time should be higher but still acceptable
        assert response.elapsed.total_seconds() < 2.0
    
    def test_network_partition(self):
        """Test behavior during network partitions"""
        # Simulate network partition between services
        self._simulate_network_partition('frontend', 'backend')
        
        # Verify frontend shows appropriate error
        # Verify retries and circuit breaker behavior
        # Verify system recovers when partition heals
```

---

## Implementation Timeline & Priorities

### Phase 1: Critical Infrastructure (Weeks 1-3)
**Budget: $65K**

1. **Database Consolidation**
   - Migrate SQLite data to PostgreSQL
   - Implement connection pooling
   - Set up read replicas

2. **Performance Optimization**
   - Implement Redis caching
   - Optimize database queries
   - Add API response time monitoring

3. **Security Hardening**
   - Implement proper JWT handling
   - Add rate limiting
   - Security headers implementation

### Phase 2: Integration Platform (Weeks 4-6)
**Budget: $78K**

1. **Event-Driven Architecture**
   - Implement Redis Streams
   - Add WebSocket for real-time updates
   - Create event publishing/subscribing

2. **API Gateway**
   - Deploy Kong/Ambassador
   - Implement rate limiting
   - Add API versioning

3. **Monitoring Setup**
   - Deploy Prometheus/Grafana
   - Implement distributed tracing
   - Set up log aggregation

### Phase 3: Scalability & Deployment (Weeks 7-9)
**Budget: $65K**

1. **Container Orchestration**
   - Dockerize applications
   - Deploy to Kubernetes
   - Implement auto-scaling

2. **Blue-Green Deployment**
   - Set up deployment pipeline
   - Implement feature flags
   - Create rollback mechanisms

3. **Load Testing**
   - Performance benchmarking
   - Stress testing
   - Capacity planning

### Phase 4: Advanced Features (Weeks 10-12)
**Budget: $54K**

1. **Microservices Preparation**
   - Service boundary definition
   - Contract testing setup
   - Service mesh evaluation

2. **Advanced Security**
   - Vault integration
   - Zero-trust implementation
   - Security monitoring

3. **Production Readiness**
   - Disaster recovery setup
   - Backup strategies
   - Documentation completion

---

## Success Metrics & KPIs

### Technical Metrics
- **API Response Time**: < 500ms (95th percentile)
- **API Success Rate**: > 99.5%
- **Database Query Time**: < 100ms average
- **Cache Hit Rate**: > 80%
- **System Uptime**: > 99.9%

### Business Metrics
- **User Satisfaction**: > 4.5/5
- **Procurement Cycle Time**: 50% reduction
- **System Adoption**: > 95% user adoption
- **Error Reduction**: 90% fewer user-reported issues
- **Processing Efficiency**: 3x faster requisition processing

This comprehensive integration architecture provides a clear path from your current brownfield state to a modern, scalable, and maintainable ERP system while addressing all critical issues identified in your requirements.