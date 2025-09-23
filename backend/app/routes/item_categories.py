"""
Item Categories Management API Routes
物品種類管理 API 路由
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import text
from app import db
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

item_categories_bp = Blueprint('item_categories', __name__, url_prefix='/api/v1/item-categories')

@item_categories_bp.route('', methods=['GET'])
@jwt_required()
def get_item_categories():
    """獲取所有物品種類"""
    try:
        query = text("""
            SELECT
                category_code,
                category_name,
                is_active,
                created_at,
                updated_at
            FROM item_categories
            ORDER BY category_code
        """)

        result = db.session.execute(query)
        categories = []

        for row in result:
            categories.append({
                'category_code': row.category_code,
                'category_name': row.category_name,
                'is_active': row.is_active,
                'created_at': str(row.created_at) if row.created_at else None,
                'updated_at': str(row.updated_at) if row.updated_at else None
            })

        return jsonify({
            'success': True,
            'data': categories,
            'total': len(categories)
        }), 200

    except Exception as e:
        logger.error(f"Error fetching item categories: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@item_categories_bp.route('', methods=['POST'])
@jwt_required()
def create_item_category():
    """新增物品種類"""
    try:
        data = request.get_json()

        # 驗證必要欄位
        if not data.get('category_code') or not data.get('category_name'):
            return jsonify({
                'success': False,
                'error': '種類代碼和名稱為必填欄位'
            }), 400

        # 檢查代碼是否已存在
        check_query = text("""
            SELECT 1 FROM item_categories
            WHERE category_code = :code
        """)

        existing = db.session.execute(
            check_query,
            {'code': data['category_code']}
        ).fetchone()

        if existing:
            return jsonify({
                'success': False,
                'error': f"種類代碼 {data['category_code']} 已存在"
            }), 400

        # 新增種類
        insert_query = text("""
            INSERT INTO item_categories (
                category_code,
                category_name,
                is_active,
                created_at,
                updated_at
            ) VALUES (
                :code,
                :name,
                :is_active,
                :created_at,
                :updated_at
            )
        """)

        current_time = datetime.utcnow()
        db.session.execute(insert_query, {
            'code': data['category_code'],
            'name': data['category_name'],
            'is_active': data.get('is_active', True),
            'created_at': current_time,
            'updated_at': current_time
        })

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '物品種類新增成功',
            'data': {
                'category_code': data['category_code'],
                'category_name': data['category_name']
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating item category: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@item_categories_bp.route('/<category_code>', methods=['PUT'])
@jwt_required()
def update_item_category(category_code):
    """更新物品種類"""
    try:
        data = request.get_json()

        # 檢查種類是否存在
        check_query = text("""
            SELECT 1 FROM item_categories
            WHERE category_code = :code
        """)

        existing = db.session.execute(
            check_query,
            {'code': category_code}
        ).fetchone()

        if not existing:
            return jsonify({
                'success': False,
                'error': f"找不到種類代碼: {category_code}"
            }), 404

        # 更新種類
        update_query = text("""
            UPDATE item_categories
            SET category_name = :name,
                is_active = :is_active,
                updated_at = :updated_at
            WHERE category_code = :code
        """)

        db.session.execute(update_query, {
            'code': category_code,
            'name': data.get('category_name'),
            'is_active': data.get('is_active', True),
            'updated_at': datetime.utcnow()
        })

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '物品種類更新成功'
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating item category: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@item_categories_bp.route('/<category_code>', methods=['DELETE'])
@jwt_required()
def delete_item_category(category_code):
    """刪除物品種類"""
    try:
        # 檢查是否有物品使用此種類
        check_usage_query = text("""
            SELECT COUNT(*) as count
            FROM request_order_items
            WHERE item_category = :code
        """)

        usage_result = db.session.execute(
            check_usage_query,
            {'code': category_code}
        ).fetchone()

        if usage_result and usage_result.count > 0:
            return jsonify({
                'success': False,
                'error': f"無法刪除：有 {usage_result.count} 個物品使用此種類"
            }), 400

        # 刪除種類
        delete_query = text("""
            DELETE FROM item_categories
            WHERE category_code = :code
        """)

        result = db.session.execute(delete_query, {'code': category_code})

        if result.rowcount == 0:
            return jsonify({
                'success': False,
                'error': f"找不到種類代碼: {category_code}"
            }), 404

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '物品種類刪除成功'
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting item category: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@item_categories_bp.route('/<category_code>/toggle-active', methods=['PATCH'])
@jwt_required()
def toggle_category_status(category_code):
    """切換物品種類啟用狀態"""
    try:
        # 切換狀態
        toggle_query = text("""
            UPDATE item_categories
            SET is_active = NOT is_active,
                updated_at = :updated_at
            WHERE category_code = :code
            RETURNING is_active
        """)

        result = db.session.execute(toggle_query, {
            'code': category_code,
            'updated_at': datetime.utcnow()
        }).fetchone()

        if not result:
            return jsonify({
                'success': False,
                'error': f"找不到種類代碼: {category_code}"
            }), 404

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f"物品種類狀態已{'啟用' if result.is_active else '停用'}",
            'is_active': result.is_active
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling category status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500