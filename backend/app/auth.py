from functools import wraps
from flask import jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.models.user import User

def require_roles(*roles):
    """Decorator to require specific roles for an endpoint"""
    def decorator(f):
        @wraps(f)
        @jwt_required(optional=True)
        def decorated_function(*args, **kwargs):
            # Skip authentication for OPTIONS requests (CORS preflight)
            from flask import request
            if request.method == 'OPTIONS':
                return '', 200

            # For other methods, require JWT
            current_user_id = get_jwt_identity()
            if not current_user_id:
                return jsonify({
                    'error': {
                        'code': 'MISSING_TOKEN',
                        'message': 'Authentication required',
                        'details': {}
                    }
                }), 401

            current_user = User.query.get(current_user_id)
            
            if not current_user or not current_user.is_active:
                return jsonify({
                    'error': {
                        'code': 'INVALID_USER',
                        'message': 'User not found or inactive',
                        'details': {}
                    }
                }), 401
            
            # Admin role can access everything
            if current_user.role == 'Admin':
                return f(current_user=current_user, *args, **kwargs)
            
            # Check if user has required role
            if not current_user.has_role(*roles):
                return jsonify({
                    'error': {
                        'code': 'INSUFFICIENT_PERMISSIONS',
                        'message': f'Required roles: {", ".join(roles)}. Current role: {current_user.role}',
                        'details': {
                            'required_roles': list(roles),
                            'current_role': current_user.role
                        }
                    }
                }), 403
            
            return f(current_user=current_user, *args, **kwargs)
        return decorated_function
    return decorator

def get_current_user():
    """Get current user from JWT token"""
    try:
        current_user_id = get_jwt_identity()
        if current_user_id:
            return User.query.get(current_user_id)
        return None
    except:
        return None

def admin_required(f):
    """Decorator to require admin role"""
    return require_roles('Admin')(f)

def procurement_required(f):
    """Decorator to require procurement role or higher"""
    return require_roles('Admin', 'ProcurementMgr', 'Procurement', 'Manager')(f)

def procurement_manager_required(f):
    """Decorator to require procurement manager role or higher"""
    return require_roles('Admin', 'ProcurementMgr', 'Manager')(f)

def accountant_required(f):
    """Decorator to require accountant role or higher"""
    return require_roles('Admin', 'ProcurementMgr', 'Accountant')(f)

def authenticated_required(f):
    """Decorator that allows any authenticated user (Everyone role)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip authentication for OPTIONS requests (CORS preflight)
        from flask import request
        if request.method == 'OPTIONS':
            return '', 200
        # For other methods, apply the role check
        return require_roles('Admin', 'ProcurementMgr', 'Procurement', 'Accountant', 'Everyone', 'Engineer', 'Manager')(f)(*args, **kwargs)
    return decorated_function

# JWT Token blacklist (in production, use Redis or database)
blacklisted_tokens = set()

def is_token_revoked(jwt_header, jwt_payload):
    """Check if JWT token is revoked"""
    jti = jwt_payload['jti']
    return jti in blacklisted_tokens

def revoke_token(jti):
    """Add token to blacklist"""
    blacklisted_tokens.add(jti)

def create_response(data=None, message=None, status_code=200):
    """Create standardized response"""
    if data is not None:
        return jsonify(data), status_code
    elif message:
        return jsonify({'message': message}), status_code
    else:
        return jsonify({'message': 'Success'}), status_code

def create_error_response(code, message, details=None, status_code=400):
    """Create standardized error response"""
    error = {
        'error': {
            'code': code,
            'message': message,
            'details': details or {}
        }
    }
    return jsonify(error), status_code

def paginate_query(query, page, page_size, max_page_size=100):
    """Paginate a SQLAlchemy query"""
    if page_size > max_page_size:
        page_size = max_page_size
    
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        'items': items,
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total': total,
            'pages': (total + page_size - 1) // page_size
        }
    }