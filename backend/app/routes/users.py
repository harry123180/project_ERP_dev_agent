from flask import Blueprint, request, jsonify
from werkzeug.exceptions import NotFound
from app import db
from app.models.user import User
from app.auth import admin_required, authenticated_required, create_response, create_error_response, paginate_query
import re
from datetime import datetime

bp = Blueprint('users', __name__, url_prefix='/api/v1/users')

@bp.route('', methods=['GET'])
@admin_required
def list_users(current_user):
    """List users (admin only)"""
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        role = request.args.get('role')
        department = request.args.get('department')
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        query = User.query
        
        if role:
            query = query.filter(User.role == role)
        if department:
            query = query.filter(User.department.ilike(f'%{department}%'))
        if active_only:
            query = query.filter(User.is_active == True)
        
        query = query.order_by(User.chinese_name)
        result = paginate_query(query, page, page_size)
        
        return jsonify({
            'items': [user.to_dict() for user in result['items']],
            'pagination': result['pagination']
        }), 200
        
    except Exception as e:
        return create_error_response(
            'USER_LIST_ERROR',
            'Failed to fetch users',
            {'error': str(e)},
            status_code=500
        )

@bp.route('', methods=['POST'])
@admin_required
def create_user(current_user):
    """Create new user (admin only)"""
    try:
        data = request.get_json()
        
        required_fields = ['username', 'chinese_name', 'password', 'role']
        for field in required_fields:
            if not data.get(field):
                return create_error_response(
                    'MISSING_FIELD',
                    f'{field} is required',
                    status_code=400
                )
        
        # Check if username already exists
        if User.query.filter_by(username=data['username']).first():
            return create_error_response(
                'USERNAME_EXISTS',
                'Username already exists',
                status_code=400
            )

        # Validate password strength
        is_valid, message = validate_password_strength(data['password'])
        if not is_valid:
            return create_error_response(
                'WEAK_PASSWORD',
                message,
                status_code=400
            )

        user = User(
            chinese_name=data['chinese_name'],
            username=data['username'],
            department=data.get('department'),
            job_title=data.get('job_title'),
            role=data['role']
        )
        user.set_password(data['password'])

        db.session.add(user)
        db.session.commit()

        # Log admin action
        log_admin_action(current_user, 'USER_CREATED', user.user_id, {
            'username': user.username,
            'chinese_name': user.chinese_name,
            'role': user.role
        })

        return create_response(user.to_dict(), status_code=201)
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'USER_CREATE_ERROR',
            'Failed to create user',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/<int:user_id>', methods=['GET'])
@authenticated_required
def get_user(current_user, user_id):
    """Get user profile"""
    try:
        # Users can only view their own profile unless they're admin
        if current_user.role != 'Admin' and current_user.user_id != user_id:
            return create_error_response(
                'INSUFFICIENT_PERMISSIONS',
                'Can only view own profile',
                status_code=403
            )
        
        user = User.query.get_or_404(user_id)
        return create_response(user.to_dict())
        
    except NotFound:
        return create_error_response(
            'USER_NOT_FOUND',
            f'User with ID {user_id} not found',
            status_code=404
        )
    except Exception as e:
        return create_error_response(
            'USER_GET_ERROR',
            'Failed to get user',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/<int:user_id>', methods=['PUT'])
@authenticated_required
def update_user(current_user, user_id):
    """Update user profile"""
    try:
        # Users can only update their own profile unless they're admin
        if current_user.role != 'Admin' and current_user.user_id != user_id:
            return create_error_response(
                'INSUFFICIENT_PERMISSIONS',
                'Can only update own profile',
                status_code=403
            )
        
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        # Non-admin users cannot change role
        if current_user.role != 'Admin' and 'role' in data:
            return create_error_response(
                'INSUFFICIENT_PERMISSIONS',
                'Cannot change role',
                status_code=403
            )
        
        # Track changes for logging
        changes = {}

        # Update allowed fields
        if 'chinese_name' in data and data['chinese_name'] != user.chinese_name:
            changes['chinese_name'] = {'old': user.chinese_name, 'new': data['chinese_name']}
            user.chinese_name = data['chinese_name']
        if 'department' in data and data['department'] != user.department:
            changes['department'] = {'old': user.department, 'new': data['department']}
            user.department = data['department']
        if 'job_title' in data and data['job_title'] != user.job_title:
            changes['job_title'] = {'old': user.job_title, 'new': data['job_title']}
            user.job_title = data['job_title']
        if 'role' in data and current_user.role == 'Admin' and data['role'] != user.role:
            changes['role'] = {'old': user.role, 'new': data['role']}
            user.role = data['role']
        if 'is_active' in data and current_user.role == 'Admin' and data['is_active'] != user.is_active:
            changes['is_active'] = {'old': user.is_active, 'new': data['is_active']}
            user.is_active = data['is_active']

        db.session.commit()

        # Log admin action if there were changes
        if changes and current_user.role == 'Admin':
            log_admin_action(current_user, 'USER_UPDATED', user.user_id, {
                'username': user.username,
                'chinese_name': user.chinese_name,
                'changes': changes
            })

        return create_response(user.to_dict())
        
    except NotFound:
        return create_error_response(
            'USER_NOT_FOUND',
            f'User with ID {user_id} not found',
            status_code=404
        )
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'USER_UPDATE_ERROR',
            'Failed to update user',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/roles', methods=['GET'])
@authenticated_required
def get_roles(current_user):
    """Get available user roles"""
    roles = ['Admin', 'ProcurementMgr', 'Procurement', 'Accountant', 'Everyone']
    return create_response({
        'roles': [{'value': role, 'label': role} for role in roles]
    })

def validate_password_strength(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"

    return True, "Password is strong"

def log_admin_action(admin_user, action, target_user_id=None, details=None):
    """Log admin actions for audit trail"""
    # For now, we'll log to a simple structure
    # In production, this could be stored in a dedicated audit table
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'admin_user_id': admin_user.user_id,
        'admin_username': admin_user.username,
        'action': action,
        'target_user_id': target_user_id,
        'details': details or {}
    }

    # TODO: Store in database audit table
    print(f"[AUDIT] {log_entry}")
    return log_entry

@bp.route('/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(current_user, user_id):
    """Soft delete user (admin only)"""
    try:
        user = User.query.get_or_404(user_id)

        # Prevent admin from deleting themselves
        if user.user_id == current_user.user_id:
            return create_error_response(
                'CANNOT_DELETE_SELF',
                'Cannot delete your own account',
                status_code=400
            )

        # Soft delete by setting is_active to False
        user.is_active = False
        user.updated_at = datetime.utcnow()

        db.session.commit()

        # Log admin action
        log_admin_action(current_user, 'USER_DELETED', user_id, {
            'username': user.username,
            'chinese_name': user.chinese_name
        })

        return create_response(message=f'User {user.username} has been deactivated')

    except NotFound:
        return create_error_response(
            'USER_NOT_FOUND',
            f'User with ID {user_id} not found',
            status_code=404
        )
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'USER_DELETE_ERROR',
            'Failed to delete user',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/<int:user_id>/reset-password', methods=['POST'])
@admin_required
def reset_user_password(current_user, user_id):
    """Reset user password (admin only)"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()

        if not data or not data.get('new_password'):
            return create_error_response(
                'MISSING_PASSWORD',
                'New password is required',
                status_code=400
            )

        new_password = data.get('new_password')

        # Validate password strength
        is_valid, message = validate_password_strength(new_password)
        if not is_valid:
            return create_error_response(
                'WEAK_PASSWORD',
                message,
                status_code=400
            )

        # Update password
        user.set_password(new_password)
        user.updated_at = datetime.utcnow()
        db.session.commit()

        # Log admin action
        log_admin_action(current_user, 'PASSWORD_RESET', user_id, {
            'username': user.username,
            'chinese_name': user.chinese_name
        })

        return create_response(message=f'Password reset successfully for user {user.username}')

    except NotFound:
        return create_error_response(
            'USER_NOT_FOUND',
            f'User with ID {user_id} not found',
            status_code=404
        )
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'PASSWORD_RESET_ERROR',
            'Failed to reset password',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/<int:user_id>/activate', methods=['POST'])
@admin_required
def activate_user(current_user, user_id):
    """Activate/reactivate user (admin only)"""
    try:
        user = User.query.get_or_404(user_id)
        user.is_active = True
        user.updated_at = datetime.utcnow()

        db.session.commit()

        # Log admin action
        log_admin_action(current_user, 'USER_ACTIVATED', user_id, {
            'username': user.username,
            'chinese_name': user.chinese_name
        })

        return create_response(message=f'User {user.username} has been activated')

    except NotFound:
        return create_error_response(
            'USER_NOT_FOUND',
            f'User with ID {user_id} not found',
            status_code=404
        )
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'USER_ACTIVATE_ERROR',
            'Failed to activate user',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/search', methods=['GET'])
@admin_required
def search_users(current_user):
    """Search users with advanced filtering"""
    try:
        query_text = request.args.get('q', '').strip()
        role = request.args.get('role')
        department = request.args.get('department')
        is_active = request.args.get('is_active')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))

        query = User.query

        # Text search across multiple fields
        if query_text:
            search_filter = db.or_(
                User.username.ilike(f'%{query_text}%'),
                User.chinese_name.ilike(f'%{query_text}%'),
                User.department.ilike(f'%{query_text}%'),
                User.job_title.ilike(f'%{query_text}%')
            )
            query = query.filter(search_filter)

        # Role filter
        if role:
            query = query.filter(User.role == role)

        # Department filter
        if department:
            query = query.filter(User.department.ilike(f'%{department}%'))

        # Active status filter
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            query = query.filter(User.is_active == is_active_bool)

        query = query.order_by(User.chinese_name)
        result = paginate_query(query, page, page_size)

        return jsonify({
            'items': [user.to_dict() for user in result['items']],
            'pagination': result['pagination']
        }), 200

    except Exception as e:
        return create_error_response(
            'USER_SEARCH_ERROR',
            'Failed to search users',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/statistics', methods=['GET'])
@admin_required
def get_user_statistics(current_user):
    """Get user statistics (admin only)"""
    try:
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        inactive_users = total_users - active_users

        # Count by roles
        role_stats = {}
        roles = ['Admin', 'ProcurementMgr', 'Procurement', 'Accountant', 'Everyone']
        for role in roles:
            role_stats[role] = User.query.filter_by(role=role, is_active=True).count()

        # Count by departments
        department_stats = db.session.query(
            User.department,
            db.func.count(User.user_id).label('count')
        ).filter(
            User.is_active == True,
            User.department.isnot(None)
        ).group_by(User.department).all()

        return create_response({
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'role_distribution': role_stats,
            'department_distribution': [
                {'department': dept, 'count': count}
                for dept, count in department_stats
            ]
        })

    except Exception as e:
        return create_error_response(
            'USER_STATISTICS_ERROR',
            'Failed to get user statistics',
            {'error': str(e)},
            status_code=500
        )