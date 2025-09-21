# ERP System Complete Architecture Design
**Architecture Lead: Winston**  
**Date: September 7, 2025**  
**System: Requisition-Procurement-Inventory-Accounting ERP**

---

## 🎯 Architecture Overview

This comprehensive architecture addresses your current ERP system's critical issues and provides a roadmap for a production-ready solution supporting the complete workflow: **工程師請購 → 採購審核 → 採購單生成 → 供應商確認 → 交期維護 → 收貨確認 → 儲位分配 → 請購人驗收 → 庫存查詢領用 → 會計請款付款**

### Current System Assessment
- **Quality Score**: 85/100 (Production Ready)
- **Critical Issues**: HTTP 500 errors, performance problems, missing APIs
- **Strengths**: Strong security (95/100), solid foundation architecture
- **Weaknesses**: Performance optimization needed, missing workflow endpoints

---

## 🏗️ System Architecture Layers

### 1. **Database Architecture Layer**
```
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL 17 Database                   │
├─────────────────────────────────────────────────────────────┤
│  Master Data     │  Transaction Data  │  Operational Data    │
│  ├─ Users        │  ├─ Requisitions   │  ├─ Storage          │
│  ├─ Suppliers    │  ├─ Purchase Orders│  ├─ Inventory        │
│  ├─ Projects     │  ├─ Consolidations │  ├─ Logistics        │
│  └─ Categories   │  └─ Billing        │  └─ Audit Logs      │
└─────────────────────────────────────────────────────────────┘
```

### 2. **Backend Service Architecture**
```
┌─────────────────────────────────────────────────────────────┐
│                    Flask 3.0 Application                    │
├─────────────────────────────────────────────────────────────┤
│  API Layer       │  Service Layer     │  Data Access Layer  │
│  ├─ REST APIs    │  ├─ Business Logic │  ├─ SQLAlchemy ORM  │
│  ├─ JWT Auth     │  ├─ Workflow Mgmt  │  ├─ Query Optimizer │
│  ├─ Validation   │  ├─ State Machine  │  ├─ Connection Pool │
│  └─ Error Handling│  └─ Audit Service  │  └─ Migration Mgmt │
└─────────────────────────────────────────────────────────────┘
```

### 3. **Frontend Architecture Layer**
```
┌─────────────────────────────────────────────────────────────┐
│                Vue.js 3 + TypeScript Frontend               │
├─────────────────────────────────────────────────────────────┤
│  UI Components   │  State Management  │  Service Layer      │
│  ├─ Element Plus │  ├─ Pinia Stores   │  ├─ Axios HTTP     │
│  ├─ Custom Comps │  ├─ Route Guards   │  ├─ API Services   │
│  ├─ Form Validation│ ├─ State Sync     │  ├─ Error Handler  │
│  └─ Charts/Tables │  └─ Local Storage  │  └─ Cache Manager  │
└─────────────────────────────────────────────────────────────┘
```

### 4. **Performance & Caching Layer**
```
┌─────────────────────────────────────────────────────────────┐
│                   Redis Caching Layer                       │
├─────────────────────────────────────────────────────────────┤
│  Session Cache   │  Query Cache       │  Application Cache  │
│  ├─ JWT Tokens   │  ├─ Frequent Queries│ ├─ Master Data     │
│  ├─ User Sessions│  ├─ Search Results │  ├─ Settings        │
│  └─ Role Perms   │  └─ Dashboard Stats│  └─ Static Content  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Database Schema Optimization

### Core Entity Relationship Design
```sql
-- Master Data Entities
Users (1) ←→ (M) RequestOrders ←→ (M) RequestOrderItems
Suppliers (1) ←→ (M) PurchaseOrders ←→ (M) PurchaseOrderItems  
Projects (1) ←→ (M) ProjectExpenditure
Storage (Tree) ←→ (M) StorageHistory

-- Transaction Flow
RequestOrderItems → PurchaseOrderItems → LogisticsEvents → StorageHistory
```

### Performance Indexing Strategy
```sql
-- Critical Performance Indexes
CREATE INDEX CONCURRENTLY idx_request_order_user_status 
    ON request_orders(user_id, status) WHERE status != 'draft';

CREATE INDEX CONCURRENTLY idx_purchase_order_supplier_status
    ON purchase_orders(supplier_id, status, created_at DESC);

CREATE INDEX CONCURRENTLY idx_storage_history_item_location
    ON storage_history(item_reference, storage_id, movement_type);

CREATE INDEX CONCURRENTLY idx_logistics_milestone_po
    ON logistics_events(po_no, milestone_type, event_date DESC);

-- Full-text search optimization
CREATE INDEX CONCURRENTLY idx_request_items_search
    ON request_order_items USING gin(to_tsvector('english', item_name || ' ' || item_spec));
```

### Database Connection Pool Configuration
```python
# High-performance connection pooling
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 15,           # Base connection pool
    'max_overflow': 30,        # Additional connections during peaks
    'pool_recycle': 300,       # Recycle connections every 5 minutes
    'pool_pre_ping': True,     # Validate connections before use
    'connect_args': {
        'connect_timeout': 30,
        'application_name': 'erp_backend'
    }
}
```

---

## 🔧 Complete API Architecture

### Missing Endpoints Implementation
```python
# Projects Management APIs (Currently Missing)
GET    /api/v1/projects                     # List all projects
POST   /api/v1/projects                     # Create new project
GET    /api/v1/projects/{id}               # Get project details
PUT    /api/v1/projects/{id}               # Update project
GET    /api/v1/projects/{id}/expenditure   # Get project spending

# Storage Management APIs (Currently Missing)  
GET    /api/v1/storage/zones               # List storage zones
POST   /api/v1/storage/zones               # Create storage zone
GET    /api/v1/storage/zones/{id}/shelves  # Get zone shelves
POST   /api/v1/storage/shelves             # Create shelf
GET    /api/v1/storage/locations/search    # Search available locations

# Enhanced Requisition APIs (Fix HTTP 500 errors)
GET    /api/v1/requisitions/summary        # Dashboard statistics
POST   /api/v1/requisitions/bulk-action    # Bulk approve/reject
GET    /api/v1/requisitions/export         # Excel export
```

### API Design Patterns
```python
# Standardized Response Format
{
    "success": true,
    "data": {...},
    "pagination": {
        "page": 1,
        "page_size": 20,
        "total": 100,
        "has_more": true
    },
    "timestamp": "2025-09-07T21:00:00Z"
}

# Error Response Format  
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input parameters",
        "details": {
            "field": "quantity",
            "issue": "must_be_positive"
        }
    },
    "timestamp": "2025-09-07T21:00:00Z"
}
```

### State Machine Validation
```python
# Requisition State Transitions
REQUISITION_STATES = {
    'draft': ['submitted', 'cancelled'],
    'submitted': ['in_review', 'rejected'],
    'in_review': ['approved', 'questioned', 'rejected'],
    'approved': ['po_created'],
    'questioned': ['in_review', 'rejected'],
    'rejected': ['draft'],  # Allow resubmission
    'po_created': []  # Terminal state
}
```

---

## 🎨 Frontend State Management Architecture

### Pinia Store Design
```typescript
// stores/workflow.ts - Master workflow orchestration
export const useWorkflowStore = defineStore('workflow', () => {
  // Centralized workflow state
  const currentStep = ref<WorkflowStep>('requisition')
  const workflowData = ref<WorkflowData>({})
  
  // Workflow progression
  const progressToNext = async (data: any) => {
    const nextStep = WORKFLOW_TRANSITIONS[currentStep.value]
    await validateTransition(currentStep.value, nextStep)
    workflowData.value = { ...workflowData.value, ...data }
    currentStep.value = nextStep
  }
  
  return { currentStep, workflowData, progressToNext }
})

// stores/requisition.ts - Enhanced requisition management  
export const useRequisitionStore = defineStore('requisition', () => {
  const requisitions = ref<Requisition[]>([])
  const currentRequisition = ref<Requisition | null>(null)
  const loading = ref(false)
  const filters = ref<RequisitionFilters>({})
  
  // Advanced filtering and pagination
  const filteredRequisitions = computed(() => {
    return requisitions.value.filter(req => {
      if (filters.value.status && req.status !== filters.value.status) return false
      if (filters.value.dateRange && !isInDateRange(req.created_at, filters.value.dateRange)) return false
      return true
    })
  })
  
  return { requisitions, currentRequisition, loading, filters, filteredRequisitions }
})
```

### Component Architecture Patterns
```vue
<!-- Enhanced component composition -->
<template>
  <div class="workflow-container">
    <WorkflowProgress :current-step="currentStep" :steps="WORKFLOW_STEPS" />
    <component :is="currentComponent" v-bind="componentProps" @next="handleNext" />
    <WorkflowActions :step="currentStep" @action="handleAction" />
  </div>
</template>

<script setup lang="ts">
// Composition API with workflow management
const workflowStore = useWorkflowStore()
const { currentStep } = storeToRefs(workflowStore)

const componentMap = {
  requisition: RequisitionForm,
  approval: ApprovalReview,
  procurement: ProcurementOrder,
  shipping: ShippingTracking,
  receiving: ReceivingConfirmation,
  storage: StorageAssignment,
  acceptance: AcceptanceConfirmation,
  inventory: InventoryManagement,
  accounting: BillingPayment
}

const currentComponent = computed(() => componentMap[currentStep.value])
</script>
```

---

## ⚡ Performance Optimization Architecture

### Redis Caching Strategy
```python
# Multi-layer caching implementation
import redis
from functools import wraps

# Cache configuration
CACHE_CONFIG = {
    'default': {
        'timeout': 300,  # 5 minutes
        'key_prefix': 'erp:default:'
    },
    'master_data': {
        'timeout': 3600,  # 1 hour
        'key_prefix': 'erp:master:'
    },
    'user_session': {
        'timeout': 1800,  # 30 minutes  
        'key_prefix': 'erp:session:'
    }
}

# Smart cache decorator
def cache_result(cache_type='default', key_func=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = key_func(*args, **kwargs) if key_func else f"{func.__name__}:{hash(str(args))}"
            
            # Try cache first
            cached = redis_client.get(f"{CACHE_CONFIG[cache_type]['key_prefix']}{cache_key}")
            if cached:
                return json.loads(cached)
            
            # Compute and cache
            result = func(*args, **kwargs)
            redis_client.setex(
                f"{CACHE_CONFIG[cache_type]['key_prefix']}{cache_key}",
                CACHE_CONFIG[cache_type]['timeout'],
                json.dumps(result)
            )
            return result
        return wrapper
    return decorator
```

### Database Query Optimization
```python
# Optimized query patterns
class OptimizedQueries:
    @staticmethod
    @cache_result('master_data', lambda: 'suppliers:all')
    def get_suppliers_with_stats():
        """Get suppliers with cached purchase statistics"""
        return db.session.query(
            Supplier,
            func.count(PurchaseOrder.id).label('total_pos'),
            func.sum(PurchaseOrder.total_amount).label('total_spent')
        ).outerjoin(PurchaseOrder)\
         .group_by(Supplier.id)\
         .all()
    
    @staticmethod  
    def get_requisitions_paginated(page, page_size, filters):
        """Optimized requisition queries with proper indexing"""
        query = db.session.query(RequestOrder)\
                 .options(selectinload(RequestOrder.items))\
                 .options(selectinload(RequestOrder.user))
        
        # Apply filters with index-friendly conditions
        if filters.get('status'):
            query = query.filter(RequestOrder.status == filters['status'])
        if filters.get('user_id'):
            query = query.filter(RequestOrder.user_id == filters['user_id'])
            
        return query.order_by(RequestOrder.created_at.desc())\
                   .paginate(page=page, per_page=page_size)
```

---

## 🔒 Security Architecture

### JWT Enhanced Implementation
```python
# Comprehensive JWT security
class JWTSecurityManager:
    def __init__(self):
        self.blacklisted_tokens = set()
        
    def generate_tokens(self, user):
        """Generate secure access and refresh tokens"""
        access_payload = {
            'user_id': user.id,
            'username': user.username,
            'roles': user.roles,
            'permissions': self.get_user_permissions(user),
            'exp': datetime.utcnow() + timedelta(hours=1)
        }
        
        refresh_payload = {
            'user_id': user.id,
            'type': 'refresh',
            'exp': datetime.utcnow() + timedelta(days=30)
        }
        
        return {
            'access_token': jwt.encode(access_payload, current_app.config['JWT_SECRET_KEY']),
            'refresh_token': jwt.encode(refresh_payload, current_app.config['JWT_SECRET_KEY']),
            'expires_in': 3600
        }
    
    def validate_token(self, token):
        """Comprehensive token validation"""
        if token in self.blacklisted_tokens:
            raise InvalidTokenError('Token has been revoked')
            
        try:
            payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            raise InvalidTokenError('Token has expired')
        except jwt.InvalidTokenError:
            raise InvalidTokenError('Invalid token')
```

### Role-Based Access Control (RBAC)
```python
# Advanced RBAC implementation
ROLE_PERMISSIONS = {
    'Admin': ['*'],  # All permissions
    'ProcurementMgr': [
        'requisitions:approve',
        'purchase_orders:confirm',
        'billing:generate',
        'payments:mark_paid'
    ],
    'Procurement': [
        'requisitions:review',
        'purchase_orders:create',
        'logistics:update'
    ],
    'Accountant': [
        'billing:generate',
        'payments:mark_paid',
        'reports:financial'
    ],
    'Everyone': [
        'requisitions:create',
        'receiving:confirm',
        'storage:assign',
        'inventory:issue'
    ]
}

def require_permission(permission):
    """Permission-based access control decorator"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            current_user_permissions = get_jwt_claims()['permissions']
            if '*' in current_user_permissions or permission in current_user_permissions:
                return f(*args, **kwargs)
            else:
                return jsonify({'error': 'Insufficient permissions'}), 403
        return decorated
    return decorator
```

---

## 🚀 Deployment Architecture

### Production Infrastructure
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  # PostgreSQL with performance tuning
  postgres:
    image: postgres:17
    environment:
      POSTGRES_DB: erp_system
      POSTGRES_USER: erp_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
    command: |
      postgres 
        -c shared_preload_libraries=pg_stat_statements
        -c max_connections=200
        -c shared_buffers=256MB
        -c effective_cache_size=1GB
        -c work_mem=4MB
    
  # Redis for caching
  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
      
  # Backend service
  backend:
    build: ./backend
    environment:
      FLASK_ENV: production
      DATABASE_URL: postgresql://erp_user:${DB_PASSWORD}@postgres:5432/erp_system
      REDIS_URL: redis://redis:6379/0
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
    depends_on:
      - postgres
      - redis
    deploy:
      replicas: 2
      
  # Frontend service  
  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
      
  # Load balancer
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
```

### Environment Configuration
```python
# Production configuration enhancements
class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    
    # Database optimizations
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'max_overflow': 40, 
        'pool_recycle': 300,
        'pool_pre_ping': True
    }
    
    # Security enhancements
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # Performance monitoring
    SQLALCHEMY_RECORD_QUERIES = True
    DATABASE_QUERY_TIMEOUT = 0.5
    
    # Logging configuration
    LOGGING_LEVEL = 'INFO'
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
```

---

## 📈 Monitoring & Health Checks

### Application Monitoring
```python
# Health check endpoints
@app.route('/health')
def health_check():
    """Comprehensive health check"""
    checks = {
        'database': check_database_connection(),
        'redis': check_redis_connection(), 
        'disk_space': check_disk_space(),
        'memory_usage': check_memory_usage(),
        'api_endpoints': check_critical_endpoints()
    }
    
    overall_health = all(check['status'] == 'healthy' for check in checks.values())
    status_code = 200 if overall_health else 503
    
    return jsonify({
        'status': 'healthy' if overall_health else 'unhealthy',
        'checks': checks,
        'timestamp': datetime.utcnow().isoformat()
    }), status_code

# Performance metrics
@app.route('/metrics')
def application_metrics():
    """Application performance metrics"""
    return jsonify({
        'database_connections': get_db_connection_count(),
        'cache_hit_rate': get_cache_hit_rate(),
        'average_response_time': get_avg_response_time(),
        'active_users': get_active_user_count(),
        'api_call_frequency': get_api_call_stats()
    })
```

---

## 🔄 Data Migration & Backup Strategy

### Database Migration Management
```python
# Automated migration scripts
class DatabaseMigration:
    def __init__(self):
        self.migrations = []
    
    def add_migration(self, version, description, up_script, down_script):
        """Add versioned migration"""
        self.migrations.append({
            'version': version,
            'description': description,
            'up': up_script,
            'down': down_script,
            'timestamp': datetime.utcnow()
        })
    
    def migrate_up(self, target_version=None):
        """Execute forward migrations"""
        current_version = self.get_current_version()
        
        for migration in self.migrations:
            if migration['version'] > current_version:
                if target_version and migration['version'] > target_version:
                    break
                    
                print(f"Applying migration {migration['version']}: {migration['description']}")
                db.session.execute(text(migration['up']))
                self.update_version(migration['version'])
                db.session.commit()
```

---

## 📋 Implementation Roadmap

### Phase 1: Foundation Fixes (Week 1-2)
1. **Fix HTTP 500 errors** in requisition endpoints
2. **Implement missing API endpoints** (Projects, Storage)  
3. **Database performance optimization** with indexes
4. **Enhanced error handling** and logging

### Phase 2: Performance & Caching (Week 3-4)
1. **Redis caching integration**
2. **Query optimization** and connection pooling
3. **Frontend state management** improvements
4. **Database connection monitoring**

### Phase 3: Security & Production Ready (Week 5-6)
1. **Enhanced JWT security** implementation
2. **RBAC permission system** completion
3. **Production deployment** configuration
4. **Monitoring and health checks**

### Phase 4: Advanced Features (Week 7-8)
1. **Workflow automation** enhancements
2. **Advanced reporting** and analytics
3. **Integration testing** and QA
4. **Performance benchmarking**

---

## 🎯 Success Metrics

### Performance Targets
- **API Response Time**: < 200ms (95th percentile)
- **Database Query Time**: < 100ms average
- **Frontend Load Time**: < 3 seconds
- **System Uptime**: > 99.9%

### Quality Targets  
- **Test Coverage**: > 90%
- **Code Quality**: A-grade static analysis
- **Security Score**: > 95/100
- **User Satisfaction**: > 4.5/5

This comprehensive architecture provides a clear roadmap for transforming your current ERP system into a production-ready, high-performance solution that fully supports your complete business workflow from requisition to accounting.