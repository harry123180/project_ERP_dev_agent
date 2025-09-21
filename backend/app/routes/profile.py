from flask import Blueprint, request, jsonify
from app import db
from app.models.user import User
from app.auth import authenticated_required, create_response, create_error_response
from datetime import datetime

bp = Blueprint('profile', __name__, url_prefix='/api/v1/profile')

@bp.route('', methods=['GET'])
@authenticated_required
def get_profile(current_user):
    """獲取當前用戶的個人資料"""
    try:
        return create_response({
            'user_id': current_user.user_id,
            'username': current_user.username,
            'chinese_name': current_user.chinese_name,
            'department': current_user.department,
            'job_title': current_user.job_title,
            'role': current_user.role,
            'is_active': current_user.is_active,
            'created_at': current_user.created_at.isoformat() if current_user.created_at else None,
            'updated_at': current_user.updated_at.isoformat() if current_user.updated_at else None
        })
    except Exception as e:
        return create_error_response(
            'PROFILE_ERROR',
            '獲取個人資料失敗',
            {'error': str(e)},
            status_code=500
        )

@bp.route('', methods=['PUT'])
@authenticated_required
def update_profile(current_user):
    """更新當前用戶的個人資料"""
    try:
        data = request.get_json()
        
        # 只允許更新特定欄位
        allowed_fields = ['chinese_name', 'department', 'job_title']
        
        for field in allowed_fields:
            if field in data:
                setattr(current_user, field, data[field])
        
        current_user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return create_response({
            'message': '個人資料更新成功',
            'user': {
                'user_id': current_user.user_id,
                'username': current_user.username,
                'chinese_name': current_user.chinese_name,
                'department': current_user.department,
                'job_title': current_user.job_title,
                'role': current_user.role,
                'updated_at': current_user.updated_at.isoformat() if current_user.updated_at else None
            }
        })
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'UPDATE_ERROR',
            '更新個人資料失敗',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/password', methods=['PUT'])
@authenticated_required
def change_password(current_user):
    """更改密碼"""
    try:
        data = request.get_json()
        
        # 驗證必要欄位
        if 'current_password' not in data or 'new_password' not in data:
            return create_error_response(
                'MISSING_FIELDS',
                '請提供當前密碼和新密碼',
                status_code=400
            )
        
        # 驗證當前密碼
        if not current_user.check_password(data['current_password']):
            return create_error_response(
                'INVALID_PASSWORD',
                '當前密碼不正確',
                status_code=400
            )
        
        # 驗證新密碼強度
        new_password = data['new_password']
        if len(new_password) < 6:
            return create_error_response(
                'WEAK_PASSWORD',
                '新密碼長度至少需要6個字符',
                status_code=400
            )
        
        # 更新密碼
        current_user.set_password(new_password)
        current_user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return create_response({
            'message': '密碼更新成功'
        })
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'PASSWORD_UPDATE_ERROR',
            '更新密碼失敗',
            {'error': str(e)},
            status_code=500
        )