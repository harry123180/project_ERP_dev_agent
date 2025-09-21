from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
from app import db
from app.models.user import User
from app.auth import revoke_token, create_response, create_error_response
from datetime import timedelta
from functools import wraps

def add_cors_headers(f):
    """Decorator to add CORS headers to responses"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"[CORS DECORATOR] Function {f.__name__} called")
        # Handle preflight
        if request.method == 'OPTIONS':
            origin = request.headers.get('Origin')
            print(f"[CORS DECORATOR] OPTIONS preflight for origin: {origin}")
            if origin and origin in current_app.config['CORS_ORIGINS']:
                print(f"[CORS DECORATOR] Creating preflight response for {origin}")
                response = jsonify({})
                response.headers['Access-Control-Allow-Origin'] = origin
                response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
                response.headers['Access-Control-Allow-Credentials'] = 'true'
                return response
        
        # Execute the actual function
        result = f(*args, **kwargs)
        
        # Add CORS headers to the response
        origin = request.headers.get('Origin')
        print(f"[CORS DECORATOR] Adding CORS headers to response for origin: {origin}")
        if origin and origin in current_app.config['CORS_ORIGINS']:
            if isinstance(result, tuple):
                response, status_code = result
                if hasattr(response, 'headers'):
                    response.headers['Access-Control-Allow-Origin'] = origin
                    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
                    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
                    response.headers['Access-Control-Allow-Credentials'] = 'true'
                    print(f"[CORS DECORATOR] Added headers to tuple response")
                return result
            else:
                # Single response object
                if hasattr(result, 'headers'):
                    result.headers['Access-Control-Allow-Origin'] = origin
                    result.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
                    result.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
                    result.headers['Access-Control-Allow-Credentials'] = 'true'
                    print(f"[CORS DECORATOR] Added headers to single response")
        
        return result
    return decorated_function

bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

@bp.route('/login', methods=['POST'])
def login():
    """User authentication with JWT token"""
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return create_error_response(
                'MISSING_CREDENTIALS',
                'Username and password are required',
                status_code=400
            )
        
        username = data.get('username')
        password = data.get('password')
        
        # Find user by username
        user = User.query.filter_by(username=username, is_active=True).first()
        
        if not user or not user.check_password(password):
            return create_error_response(
                'INVALID_CREDENTIALS',
                'Invalid username or password',
                status_code=401
            )
        
        # Create JWT tokens
        access_token = create_access_token(
            identity=user.user_id,
            additional_claims={'role': user.role, 'username': user.username}
        )
        refresh_token = create_refresh_token(identity=user.user_id)
        
        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict(),
            'expires_in': int(timedelta(hours=1).total_seconds())
        }), 200
        
    except Exception as e:
        return create_error_response(
            'LOGIN_ERROR',
            'Login failed',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh JWT token"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_active:
            return create_error_response(
                'INVALID_USER',
                'User not found or inactive',
                status_code=401
            )
        
        # Create new access token
        access_token = create_access_token(
            identity=user.user_id,
            additional_claims={'role': user.role, 'username': user.username}
        )
        
        return jsonify({
            'access_token': access_token,
            'user': user.to_dict(),
            'expires_in': int(timedelta(hours=1).total_seconds())
        }), 200
        
    except Exception as e:
        return create_error_response(
            'REFRESH_ERROR',
            'Token refresh failed',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """User logout and token invalidation"""
    try:
        jti = get_jwt()['jti']
        revoke_token(jti)
        
        return create_response(message='Successfully logged out')
        
    except Exception as e:
        return create_error_response(
            'LOGOUT_ERROR',
            'Logout failed',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_active:
            return create_error_response(
                'INVALID_USER',
                'User not found or inactive',
                status_code=401
            )
        
        return create_response(user.to_dict())
        
    except Exception as e:
        return create_error_response(
            'USER_PROFILE_ERROR',
            'Failed to get user profile',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_active:
            return create_error_response(
                'INVALID_USER',
                'User not found or inactive',
                status_code=401
            )
        
        data = request.get_json()
        if not data or not data.get('current_password') or not data.get('new_password'):
            return create_error_response(
                'MISSING_FIELDS',
                'Current password and new password are required',
                status_code=400
            )
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        # Verify current password
        if not user.check_password(current_password):
            return create_error_response(
                'INVALID_PASSWORD',
                'Current password is incorrect',
                status_code=400
            )
        
        # Update password
        user.set_password(new_password)
        db.session.commit()
        
        return create_response(message='Password changed successfully')
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'PASSWORD_CHANGE_ERROR',
            'Failed to change password',
            {'error': str(e)},
            status_code=500
        )