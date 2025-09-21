"""
Enhanced Security Architecture
Advanced JWT authentication and Role-Based Access Control (RBAC)
Architecture Lead: Winston
"""

import jwt
import logging
import hashlib
import secrets
import bcrypt
from functools import wraps
from typing import Dict, List, Optional, Set, Any, Tuple
from datetime import datetime, timedelta
from flask import current_app, request, jsonify, g
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, get_jwt, 
    create_access_token, create_refresh_token
)
import redis
from enum import Enum
import re

logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    """Security levels for different operations"""
    PUBLIC = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class RoleHierarchy(Enum):
    """Role hierarchy levels for RBAC"""
    EVERYONE = 1
    ENGINEER = 2
    ACCOUNTANT = 3
    PROCUREMENT = 4
    PROCUREMENT_MGR = 5
    ADMIN = 6

# Comprehensive permission definitions
PERMISSIONS = {
    # Requisition permissions
    'requisitions.create': {'roles': ['Everyone', 'Engineer'], 'level': SecurityLevel.LOW},
    'requisitions.view_own': {'roles': ['Everyone', 'Engineer'], 'level': SecurityLevel.LOW},
    'requisitions.view_all': {'roles': ['Procurement', 'ProcurementMgr', 'Admin'], 'level': SecurityLevel.MEDIUM},
    'requisitions.update_own': {'roles': ['Everyone', 'Engineer'], 'level': SecurityLevel.LOW},
    'requisitions.approve': {'roles': ['ProcurementMgr', 'Admin'], 'level': SecurityLevel.HIGH},
    'requisitions.reject': {'roles': ['Procurement', 'ProcurementMgr', 'Admin'], 'level': SecurityLevel.MEDIUM},
    'requisitions.delete': {'roles': ['Admin'], 'level': SecurityLevel.HIGH},
    
    # Purchase Order permissions
    'purchase_orders.create': {'roles': ['Procurement', 'ProcurementMgr', 'Admin'], 'level': SecurityLevel.MEDIUM},
    'purchase_orders.view': {'roles': ['Procurement', 'ProcurementMgr', 'Admin'], 'level': SecurityLevel.MEDIUM},
    'purchase_orders.confirm': {'roles': ['ProcurementMgr', 'Admin'], 'level': SecurityLevel.HIGH},
    'purchase_orders.cancel': {'roles': ['ProcurementMgr', 'Admin'], 'level': SecurityLevel.HIGH},
    'purchase_orders.modify': {'roles': ['Procurement', 'ProcurementMgr', 'Admin'], 'level': SecurityLevel.MEDIUM},
    
    # Project permissions
    'projects.create': {'roles': ['ProcurementMgr', 'Admin'], 'level': SecurityLevel.MEDIUM},
    'projects.view': {'roles': ['Everyone', 'Engineer'], 'level': SecurityLevel.LOW},
    'projects.update': {'roles': ['ProcurementMgr', 'Admin'], 'level': SecurityLevel.MEDIUM},
    'projects.delete': {'roles': ['Admin'], 'level': SecurityLevel.HIGH},
    'projects.view_expenditure': {'roles': ['ProcurementMgr', 'Accountant', 'Admin'], 'level': SecurityLevel.MEDIUM},
    
    # Storage permissions
    'storage.view': {'roles': ['Everyone', 'Engineer'], 'level': SecurityLevel.LOW},
    'storage.assign': {'roles': ['Everyone', 'Engineer'], 'level': SecurityLevel.LOW},
    'storage.manage_zones': {'roles': ['ProcurementMgr', 'Admin'], 'level': SecurityLevel.MEDIUM},
    'storage.manage_shelves': {'roles': ['ProcurementMgr', 'Admin'], 'level': SecurityLevel.MEDIUM},
    
    # Inventory permissions
    'inventory.view': {'roles': ['Everyone', 'Engineer'], 'level': SecurityLevel.LOW},
    'inventory.issue': {'roles': ['Everyone', 'Engineer'], 'level': SecurityLevel.LOW},
    'inventory.adjust': {'roles': ['ProcurementMgr', 'Admin'], 'level': SecurityLevel.HIGH},
    
    # Accounting permissions
    'accounting.view_billing': {'roles': ['Accountant', 'ProcurementMgr', 'Admin'], 'level': SecurityLevel.MEDIUM},
    'accounting.generate_billing': {'roles': ['Accountant', 'ProcurementMgr', 'Admin'], 'level': SecurityLevel.HIGH},
    'accounting.mark_paid': {'roles': ['Accountant', 'ProcurementMgr', 'Admin'], 'level': SecurityLevel.HIGH},
    'accounting.view_reports': {'roles': ['Accountant', 'ProcurementMgr', 'Admin'], 'level': SecurityLevel.MEDIUM},
    
    # User management permissions
    'users.create': {'roles': ['Admin'], 'level': SecurityLevel.HIGH},
    'users.view': {'roles': ['Admin'], 'level': SecurityLevel.MEDIUM},
    'users.update': {'roles': ['Admin'], 'level': SecurityLevel.HIGH},
    'users.delete': {'roles': ['Admin'], 'level': SecurityLevel.CRITICAL},
    'users.view_own_profile': {'roles': ['Everyone', 'Engineer'], 'level': SecurityLevel.LOW},
    'users.update_own_profile': {'roles': ['Everyone', 'Engineer'], 'level': SecurityLevel.LOW},
    
    # System permissions
    'system.settings_view': {'roles': ['Admin'], 'level': SecurityLevel.MEDIUM},
    'system.settings_update': {'roles': ['Admin'], 'level': SecurityLevel.CRITICAL},
    'system.logs_view': {'roles': ['Admin'], 'level': SecurityLevel.HIGH},
    'system.maintenance': {'roles': ['Admin'], 'level': SecurityLevel.CRITICAL},
}

class SecurityManager:
    """Advanced security management system"""
    
    def __init__(self):
        self.redis_client = None
        self.failed_login_attempts = {}
        self.blocked_ips = set()
        self.session_store = {}
        self.security_events = []
        self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connection for security features"""
        try:
            redis_url = current_app.config.get('REDIS_URL', 'redis://localhost:6379/1')
            self.redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
        except Exception as e:
            logger.warning(f"Redis not available for security features: {e}")
            self.redis_client = None
    
    def hash_password(self, password: str) -> str:
        """Securely hash password using bcrypt"""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate cryptographically secure random token"""
        return secrets.token_urlsafe(length)
    
    def validate_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password strength"""
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if len(password) > 128:
            errors.append("Password must be less than 128 characters long")
        
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'[0-9]', password):
            errors.append("Password must contain at least one number")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        # Check against common passwords
        common_passwords = ['password', '123456', 'admin', 'password123', 'qwerty']
        if password.lower() in common_passwords:
            errors.append("Password is too common")
        
        return len(errors) == 0, errors
    
    def check_rate_limit(self, identifier: str, limit: int = 5, window: int = 300) -> bool:
        """Check if rate limit is exceeded"""
        if not self.redis_client:
            return True  # Allow if Redis unavailable
        
        try:
            key = f"rate_limit:{identifier}"
            current_count = self.redis_client.get(key)
            
            if current_count is None:
                # First request in window
                self.redis_client.setex(key, window, 1)
                return True
            
            if int(current_count) >= limit:
                return False
            
            # Increment counter
            self.redis_client.incr(key)
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return True  # Allow on error to avoid blocking legitimate users
    
    def record_failed_login(self, username: str, ip_address: str):
        """Record failed login attempt"""
        key = f"{username}:{ip_address}"
        current_time = datetime.utcnow()
        
        if key not in self.failed_login_attempts:
            self.failed_login_attempts[key] = []
        
        # Clean old attempts (older than 1 hour)
        self.failed_login_attempts[key] = [
            attempt for attempt in self.failed_login_attempts[key]
            if (current_time - attempt).seconds < 3600
        ]
        
        # Add new attempt
        self.failed_login_attempts[key].append(current_time)
        
        # Block if too many attempts
        if len(self.failed_login_attempts[key]) >= 5:
            self.block_ip(ip_address, duration=1800)  # Block for 30 minutes
            self.log_security_event('ACCOUNT_LOCKED', {
                'username': username,
                'ip_address': ip_address,
                'attempts': len(self.failed_login_attempts[key])
            })
    
    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP address is blocked"""
        if not self.redis_client:
            return ip_address in self.blocked_ips
        
        try:
            return self.redis_client.exists(f"blocked_ip:{ip_address}")
        except:
            return ip_address in self.blocked_ips
    
    def block_ip(self, ip_address: str, duration: int = 3600):
        """Block IP address for specified duration"""
        if self.redis_client:
            self.redis_client.setex(f"blocked_ip:{ip_address}", duration, 1)
        else:
            self.blocked_ips.add(ip_address)
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security events for auditing"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': event_type,
            'details': details,
            'ip_address': request.remote_addr if request else None,
            'user_agent': request.headers.get('User-Agent') if request else None
        }
        
        if self.redis_client:
            try:
                key = f"security_event:{datetime.utcnow().strftime('%Y%m%d')}"
                self.redis_client.lpush(key, json.dumps(event))
                self.redis_client.expire(key, 2592000)  # Keep for 30 days
            except Exception as e:
                logger.error(f"Failed to log security event: {e}")
        
        self.security_events.append(event)
        logger.warning(f"Security Event: {event_type} - {details}")
    
    def validate_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate and decode JWT token"""
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            
            # Check if token is blacklisted
            if self.is_token_blacklisted(token):
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            self.log_security_event('TOKEN_EXPIRED', {'token': token[:20] + '...'})
            return None
        except jwt.InvalidTokenError:
            self.log_security_event('INVALID_TOKEN', {'token': token[:20] + '...'})
            return None
    
    def blacklist_token(self, token: str):
        """Add token to blacklist"""
        if self.redis_client:
            try:
                # Decode to get expiration
                payload = jwt.decode(
                    token, 
                    current_app.config['JWT_SECRET_KEY'],
                    algorithms=['HS256'],
                    options={'verify_exp': False}
                )
                
                exp_timestamp = payload.get('exp')
                if exp_timestamp:
                    ttl = exp_timestamp - int(datetime.utcnow().timestamp())
                    if ttl > 0:
                        self.redis_client.setex(f"blacklist:{token}", ttl, 1)
            except:
                # If decode fails, blacklist for 24 hours
                self.redis_client.setex(f"blacklist:{token}", 86400, 1)
    
    def is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        if not self.redis_client:
            return False
        
        try:
            return self.redis_client.exists(f"blacklist:{token}")
        except:
            return False

class RBACManager:
    """Role-Based Access Control manager"""
    
    def __init__(self):
        self.role_hierarchy = {
            'Everyone': 1,
            'Engineer': 2,
            'Accountant': 3,
            'Procurement': 4,
            'ProcurementMgr': 5,
            'Admin': 6
        }
    
    def has_permission(self, user_roles: List[str], required_permission: str) -> bool:
        """Check if user has required permission"""
        if required_permission not in PERMISSIONS:
            return False
        
        permission_config = PERMISSIONS[required_permission]
        allowed_roles = permission_config['roles']
        
        # Admin always has access
        if 'Admin' in user_roles:
            return True
        
        # Check if user has any of the required roles
        for user_role in user_roles:
            if user_role in allowed_roles:
                return True
        
        # Check role hierarchy (higher roles can access lower role permissions)
        user_max_level = max(self.role_hierarchy.get(role, 0) for role in user_roles)
        required_min_level = min(self.role_hierarchy.get(role, 99) for role in allowed_roles)
        
        return user_max_level >= required_min_level
    
    def get_user_permissions(self, user_roles: List[str]) -> Set[str]:
        """Get all permissions for user roles"""
        permissions = set()
        
        for permission, config in PERMISSIONS.items():
            if self.has_permission(user_roles, permission):
                permissions.add(permission)
        
        return permissions
    
    def filter_data_by_permissions(self, data: List[Dict], user_roles: List[str], user_id: int) -> List[Dict]:
        """Filter data based on user permissions"""
        filtered_data = []
        
        for item in data:
            # Check if user can view this item
            if self._can_user_access_item(item, user_roles, user_id):
                # Remove sensitive fields based on permissions
                filtered_item = self._filter_sensitive_fields(item, user_roles)
                filtered_data.append(filtered_item)
        
        return filtered_data
    
    def _can_user_access_item(self, item: Dict, user_roles: List[str], user_id: int) -> bool:
        """Check if user can access specific item"""
        # Admin can access everything
        if 'Admin' in user_roles:
            return True
        
        # Owner can always access their own items
        if item.get('created_by') == user_id or item.get('user_id') == user_id:
            return True
        
        # Role-based access rules
        item_type = item.get('type', 'unknown')
        
        if item_type == 'requisition':
            return self.has_permission(user_roles, 'requisitions.view_all')
        elif item_type == 'purchase_order':
            return self.has_permission(user_roles, 'purchase_orders.view')
        elif item_type == 'project':
            return self.has_permission(user_roles, 'projects.view')
        
        return False
    
    def _filter_sensitive_fields(self, item: Dict, user_roles: List[str]) -> Dict:
        """Remove sensitive fields based on user roles"""
        filtered_item = item.copy()
        
        # Remove financial data for non-authorized users
        if not any(role in ['Accountant', 'ProcurementMgr', 'Admin'] for role in user_roles):
            sensitive_fields = ['unit_price', 'total_amount', 'budget', 'expenditure']
            for field in sensitive_fields:
                filtered_item.pop(field, None)
        
        # Remove personal data for non-admin users
        if 'Admin' not in user_roles:
            filtered_item.pop('password_hash', None)
            filtered_item.pop('internal_notes', None)
        
        return filtered_item

# Global security instances
security_manager = SecurityManager()
rbac_manager = RBACManager()

def require_permission(permission: str, allow_self: bool = False):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            try:
                # Get user information from JWT
                current_user_id = get_jwt_identity()
                claims = get_jwt()
                user_roles = claims.get('roles', [])
                
                # Check permission
                if not rbac_manager.has_permission(user_roles, permission):
                    # Check if accessing own resources is allowed
                    if allow_self:
                        resource_id = kwargs.get('id') or kwargs.get('user_id')
                        if resource_id == current_user_id:
                            return f(*args, **kwargs)
                    
                    security_manager.log_security_event('PERMISSION_DENIED', {
                        'user_id': current_user_id,
                        'required_permission': permission,
                        'user_roles': user_roles,
                        'endpoint': request.endpoint
                    })
                    
                    return jsonify({
                        'success': False,
                        'error': {
                            'code': 'INSUFFICIENT_PERMISSIONS',
                            'message': 'You do not have permission to access this resource',
                            'required_permission': permission
                        }
                    }), 403
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Permission check error: {e}")
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'SECURITY_ERROR',
                        'message': 'Security validation failed'
                    }
                }), 500
                
        return decorated_function
    return decorator

def security_check(level: SecurityLevel = SecurityLevel.MEDIUM):
    """Decorator for additional security checks"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ip_address = request.remote_addr
            
            # Check if IP is blocked
            if security_manager.is_ip_blocked(ip_address):
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'IP_BLOCKED',
                        'message': 'Access denied from this IP address'
                    }
                }), 403
            
            # Rate limiting based on security level
            if level.value >= SecurityLevel.HIGH.value:
                if not security_manager.check_rate_limit(ip_address, limit=10, window=300):
                    return jsonify({
                        'success': False,
                        'error': {
                            'code': 'RATE_LIMIT_EXCEEDED',
                            'message': 'Too many requests. Please try again later.'
                        }
                    }), 429
            
            return f(*args, **kwargs)
            
        return decorated_function
    return decorator

def audit_trail(action: str, resource_type: str):
    """Decorator to create audit trail"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = datetime.utcnow()
            
            try:
                # Get user context
                user_id = None
                try:
                    user_id = get_jwt_identity()
                except:
                    pass
                
                # Execute function
                result = f(*args, **kwargs)
                
                # Log successful action
                security_manager.log_security_event('AUDIT_TRAIL', {
                    'action': action,
                    'resource_type': resource_type,
                    'user_id': user_id,
                    'success': True,
                    'duration_ms': (datetime.utcnow() - start_time).total_seconds() * 1000,
                    'endpoint': request.endpoint
                })
                
                return result
                
            except Exception as e:
                # Log failed action
                security_manager.log_security_event('AUDIT_TRAIL', {
                    'action': action,
                    'resource_type': resource_type,
                    'user_id': user_id,
                    'success': False,
                    'error': str(e),
                    'duration_ms': (datetime.utcnow() - start_time).total_seconds() * 1000,
                    'endpoint': request.endpoint
                })
                raise
                
        return decorated_function
    return decorator

def get_security_headers() -> Dict[str, str]:
    """Generate security headers for responses"""
    return {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
    }

def validate_input_security(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate input data for security issues"""
    errors = []
    
    for key, value in data.items():
        if isinstance(value, str):
            # Check for potential XSS
            if re.search(r'<script|javascript:|data:text/html', value, re.IGNORECASE):
                errors.append(f"Potentially malicious content detected in {key}")
            
            # Check for SQL injection patterns
            sql_patterns = ['union', 'select', 'drop', 'delete', 'insert', 'update']
            if any(pattern in value.lower() for pattern in sql_patterns):
                if re.search(r'\b(union|select|drop|delete|insert|update)\b', value, re.IGNORECASE):
                    errors.append(f"Potentially malicious SQL content detected in {key}")
    
    return len(errors) == 0, errors