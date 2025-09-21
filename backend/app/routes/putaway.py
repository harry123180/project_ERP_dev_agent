"""
Putaway (儲位入庫) management routes
Handles pending storage items and warehouse assignment
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app import db
from app.models.request_order import RequestOrderItem
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('putaway', __name__, url_prefix='/api/v1/putaway')

@bp.route('/pending', methods=['GET'])
@jwt_required()
def get_pending_items():
    """Get all items pending storage assignment (待入庫項目)"""
    try:
        # Query pending storage items
        query = text("""
            SELECT
                psi.id,
                psi.detail_id,
                psi.item_name,
                psi.quantity,
                psi.source_po_number,
                psi.received_date,
                psi.receiver_id,
                psi.status,
                u.chinese_name as receiver_name
            FROM pending_storage_items psi
            LEFT JOIN users u ON u.id = psi.receiver_id
            WHERE psi.status = 'pending'
            ORDER BY psi.received_date DESC
        """)

        result = db.session.execute(query)
        items = []

        for row in result:
            items.append({
                'id': row.id,
                'detail_id': row.detail_id,
                'item_name': row.item_name,
                'quantity': float(row.quantity) if row.quantity else 0,
                'source_po_number': row.source_po_number,
                'received_date': row.received_date,
                'receiver': row.receiver_name or 'System',
                'status': row.status
            })

        return jsonify({
            'success': True,
            'data': items,
            'total': len(items)
        }), 200

    except Exception as e:
        logger.error(f"Error getting pending storage items: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'GET_PENDING_ERROR',
                'message': 'Failed to retrieve pending storage items',
                'details': str(e)
            }
        }), 500

@bp.route('/assign', methods=['POST'])
@jwt_required()
def assign_storage():
    """Assign storage location to an item and update status (指定儲位)"""
    try:
        data = request.get_json()
        detail_id = data.get('detail_id')
        storage_id = data.get('storage_id')

        if not detail_id or not storage_id:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_FIELDS',
                    'message': 'detail_id and storage_id are required'
                }
            }), 400

        # Update pending storage item status
        update_pending = text("""
            UPDATE pending_storage_items
            SET status = 'stored',
                updated_at = :updated_at
            WHERE detail_id = :detail_id
        """)

        db.session.execute(update_pending, {
            'detail_id': detail_id,
            'updated_at': datetime.now().isoformat()
        })

        # Update request order item status to 'warehoused' (已入庫)
        req_item = RequestOrderItem.query.get(detail_id)
        if req_item:
            req_item.item_status = 'warehoused'
            req_item.updated_at = datetime.now()

            # Also update related purchase order item if exists
            update_po_item = text("""
                UPDATE purchase_order_items
                SET line_status = 'completed',
                    delivery_status = 'delivered',
                    updated_at = :updated_at
                WHERE source_detail_id = :detail_id
            """)

            db.session.execute(update_po_item, {
                'detail_id': detail_id,
                'updated_at': datetime.now().isoformat()
            })

        # Create storage history record
        insert_history = text("""
            INSERT INTO storage_history (
                storage_id,
                detail_id,
                operation_type,
                quantity,
                operation_date,
                operator_id,
                created_at
            ) VALUES (
                :storage_id,
                :detail_id,
                'in',
                :quantity,
                :operation_date,
                :operator_id,
                :created_at
            )
        """)

        # Get quantity from pending item
        get_quantity = text("""
            SELECT quantity FROM pending_storage_items
            WHERE detail_id = :detail_id
        """)

        quantity_result = db.session.execute(get_quantity, {'detail_id': detail_id}).fetchone()
        quantity = quantity_result.quantity if quantity_result else 1

        current_user_id = get_jwt_identity()

        db.session.execute(insert_history, {
            'storage_id': storage_id,
            'detail_id': detail_id,
            'quantity': quantity,
            'operation_date': datetime.now().isoformat(),
            'operator_id': current_user_id,
            'created_at': datetime.now().isoformat()
        })

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Storage location assigned successfully',
            'data': {
                'detail_id': detail_id,
                'storage_id': storage_id,
                'status': 'warehoused'
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error assigning storage: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'ASSIGN_ERROR',
                'message': 'Failed to assign storage location',
                'details': str(e)
            }
        }), 500

@bp.route('/batch-assign', methods=['POST'])
@jwt_required()
def batch_assign_storage():
    """Batch assign storage locations to multiple items"""
    try:
        data = request.get_json()
        assignments = data.get('assignments', [])

        if not assignments:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'NO_ASSIGNMENTS',
                    'message': 'No assignments provided'
                }
            }), 400

        success_count = 0
        failed_items = []

        for assignment in assignments:
            try:
                detail_id = assignment.get('detail_id')
                storage_id = assignment.get('storage_id')

                if not detail_id or not storage_id:
                    failed_items.append({
                        'detail_id': detail_id,
                        'error': 'Missing required fields'
                    })
                    continue

                # Process each assignment
                # Similar logic as single assign but in a loop

                # Update pending storage item
                update_pending = text("""
                    UPDATE pending_storage_items
                    SET status = 'stored',
                        updated_at = :updated_at
                    WHERE detail_id = :detail_id
                """)

                db.session.execute(update_pending, {
                    'detail_id': detail_id,
                    'updated_at': datetime.now().isoformat()
                })

                # Update request order item
                req_item = RequestOrderItem.query.get(detail_id)
                if req_item:
                    req_item.item_status = 'warehoused'
                    req_item.updated_at = datetime.now()

                success_count += 1

            except Exception as e:
                failed_items.append({
                    'detail_id': detail_id,
                    'error': str(e)
                })

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Batch assignment completed',
            'data': {
                'success_count': success_count,
                'failed_count': len(failed_items),
                'failed_items': failed_items
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in batch assignment: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'BATCH_ASSIGN_ERROR',
                'message': 'Failed to complete batch assignment',
                'details': str(e)
            }
        }), 500