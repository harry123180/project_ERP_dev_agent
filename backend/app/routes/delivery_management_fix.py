"""
Fixed Delivery Management API Routes - Using raw SQL to avoid datetime parsing issues
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import text
from datetime import datetime
import logging
import math

from app import db

# Create blueprint
delivery_bp = Blueprint('delivery_management', __name__, url_prefix='/api/v1/delivery')
logger = logging.getLogger(__name__)

@delivery_bp.route('/maintenance-list', methods=['GET'])
@jwt_required()
def get_delivery_maintenance_list():
    """
    Get Delivery Maintenance List (交期維護清單) - Fixed with raw SQL
    Contains: Domestic POs + International POs not in consolidation
    """
    try:
        # Get query parameters
        status = request.args.get('status', '')
        supplier_region = request.args.get('supplier_region', '')
        po_number = request.args.get('po_number', '').strip()
        page = request.args.get('page', 1, type=int)
        page_size = min(request.args.get('page_size', 50, type=int), 100)

        # Build WHERE conditions
        where_conditions = ["po.purchase_status = 'purchased'"]
        params = {}

        # Maintenance list filter (domestic + international not in consolidation)
        maintenance_filter = """(
            s.supplier_region = 'domestic'
            OR (s.supplier_region = 'international' AND po.consolidation_id IS NULL)
        )"""
        where_conditions.append(maintenance_filter)

        # Apply additional filters
        if po_number:
            where_conditions.append("po.purchase_order_no LIKE :po_number")
            params['po_number'] = f'%{po_number}%'

        if status:
            where_conditions.append("po.delivery_status = :status")
            params['status'] = status

        if supplier_region:
            where_conditions.append("s.supplier_region = :supplier_region")
            params['supplier_region'] = supplier_region

        where_clause = " WHERE " + " AND ".join(where_conditions)

        # Get total count
        count_query = text(f"""
            SELECT COUNT(*) as total
            FROM purchase_orders po
            JOIN suppliers s ON po.supplier_id = s.supplier_id
            {where_clause}
        """)

        total_count = db.session.execute(count_query, params).scalar()

        # Calculate pagination
        offset = (page - 1) * page_size
        total_pages = math.ceil(total_count / page_size) if page_size > 0 else 1
        has_more = page < total_pages

        # Get maintenance list data with raw SQL
        query = text(f"""
            SELECT
                po.purchase_order_no,
                po.supplier_id,
                po.supplier_name,
                po.purchase_status,
                po.delivery_status,
                po.expected_delivery_date,
                po.actual_delivery_date,
                po.remarks,
                po.status_update_required,
                po.consolidation_id,
                po.subtotal_int,
                po.created_at,
                po.updated_at,
                s.supplier_region,
                (SELECT COUNT(*) FROM purchase_order_items poi WHERE poi.purchase_order_no = po.purchase_order_no) as item_count
            FROM purchase_orders po
            JOIN suppliers s ON po.supplier_id = s.supplier_id
            {where_clause}
            ORDER BY po.status_update_required DESC, po.created_at DESC
            LIMIT :limit OFFSET :offset
        """)

        params['limit'] = page_size
        params['offset'] = offset

        results = db.session.execute(query, params).fetchall()

        # Format maintenance list data
        maintenance_data = []
        for row in results:
            # Check if can be consolidated (international, delivered status, not already in consolidation)
            can_be_consolidated = (
                row.supplier_region == 'international'
                and row.delivery_status == 'shipped'
                and row.consolidation_id is None
            )

            po_data = {
                'po_number': row.purchase_order_no,
                'purchase_order_no': row.purchase_order_no,
                'supplier_id': row.supplier_id,
                'supplier_name': row.supplier_name,
                'supplier_region': row.supplier_region or 'unknown',
                'purchase_status': row.purchase_status,
                'delivery_status': row.delivery_status,
                'expected_delivery_date': str(row.expected_delivery_date) if row.expected_delivery_date else None,
                'actual_delivery_date': str(row.actual_delivery_date) if row.actual_delivery_date else None,
                'remarks': row.remarks,
                'status_update_required': bool(row.status_update_required),
                'can_be_consolidated': can_be_consolidated,
                'item_count': row.item_count,
                'items_count': row.item_count,
                'subtotal': row.subtotal_int,
                'created_at': str(row.created_at) if row.created_at else None,
                'updated_at': str(row.updated_at) if row.updated_at else None
            }
            maintenance_data.append(po_data)

        return jsonify({
            'success': True,
            'data': maintenance_data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total_count,
                'has_more': has_more
            },
            'summary': {
                'total_pos': total_count,
                'pending_status_update': len([po for po in maintenance_data if po['status_update_required']]),
                'ready_for_consolidation': len([po for po in maintenance_data if po['can_be_consolidated']]),
                'domestic_pos': len([po for po in maintenance_data if po['supplier_region'] == 'domestic']),
                'international_pos': len([po for po in maintenance_data if po['supplier_region'] == 'international'])
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error getting delivery maintenance list: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': {
                'code': 'MAINTENANCE_LIST_ERROR',
                'message': 'Failed to retrieve delivery maintenance list',
                'details': str(e)
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@delivery_bp.route('/consolidation-list', methods=['GET'])
@jwt_required()
def get_consolidation_list():
    """
    Get Consolidation List (集運列表) - Fixed with raw SQL
    Contains: Only international POs in consolidation orders
    """
    try:
        # Get query parameters
        consolidation_id = request.args.get('consolidation_id')
        logistics_status = request.args.get('logistics_status')
        page = request.args.get('page', 1, type=int)
        page_size = min(request.args.get('page_size', 50, type=int), 100)

        # Build WHERE conditions
        where_conditions = []
        params = {}

        if consolidation_id:
            where_conditions.append("sc.consolidation_id = :consolidation_id")
            params['consolidation_id'] = consolidation_id

        if logistics_status:
            where_conditions.append("sc.logistics_status = :logistics_status")
            params['logistics_status'] = logistics_status

        where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""

        # Get total count
        count_query = text(f"""
            SELECT COUNT(DISTINCT sc.consolidation_id) as total
            FROM shipment_consolidations sc
            {where_clause}
        """)

        total_count = db.session.execute(count_query, params).scalar()

        # Calculate pagination
        offset = (page - 1) * page_size
        total_pages = math.ceil(total_count / page_size) if page_size > 0 else 1
        has_more = page < total_pages

        # Get consolidations with raw SQL
        query = text(f"""
            SELECT
                sc.consolidation_id,
                sc.consolidation_name,
                sc.logistics_status,
                sc.expected_delivery_date,
                sc.actual_delivery_date,
                sc.total_weight,
                sc.total_volume,
                sc.carrier,
                sc.tracking_number,
                sc.customs_declaration_no,
                sc.logistics_notes,
                sc.remarks,
                sc.created_by,
                sc.created_at,
                sc.updated_at,
                (SELECT COUNT(*) FROM consolidation_pos cp WHERE cp.consolidation_id = sc.consolidation_id) as po_count,
                (SELECT SUM(po.grand_total_int)
                 FROM purchase_orders po
                 JOIN consolidation_pos cp ON po.purchase_order_no = cp.purchase_order_no
                 WHERE cp.consolidation_id = sc.consolidation_id) as total_value
            FROM shipment_consolidations sc
            {where_clause}
            ORDER BY sc.created_at DESC
            LIMIT :limit OFFSET :offset
        """)

        params['limit'] = page_size
        params['offset'] = offset

        results = db.session.execute(query, params).fetchall()

        # Format consolidation data
        consolidations_data = []
        for row in results:
            # Get POs in this consolidation
            po_query = text("""
                SELECT
                    po.purchase_order_no,
                    po.supplier_name,
                    po.delivery_status,
                    po.subtotal_int
                FROM purchase_orders po
                JOIN consolidation_pos cp ON po.purchase_order_no = cp.purchase_order_no
                WHERE cp.consolidation_id = :consolidation_id
                ORDER BY po.purchase_order_no
            """)

            po_results = db.session.execute(po_query, {'consolidation_id': row.consolidation_id}).fetchall()

            pos_data = []
            for po_row in po_results:
                pos_data.append({
                    'purchase_order_no': po_row.purchase_order_no,
                    'supplier_name': po_row.supplier_name,
                    'delivery_status': po_row.delivery_status,
                    'subtotal': po_row.subtotal_int
                })

            consolidation_data = {
                'consolidation_id': row.consolidation_id,
                'consolidation_name': row.consolidation_name,
                'logistics_status': row.logistics_status,
                'expected_delivery_date': str(row.expected_delivery_date) if row.expected_delivery_date else None,
                'actual_delivery_date': str(row.actual_delivery_date) if row.actual_delivery_date else None,
                'total_weight': float(row.total_weight) if row.total_weight else 0,
                'total_volume': float(row.total_volume) if row.total_volume else 0,
                'carrier': row.carrier,
                'tracking_number': row.tracking_number,
                'customs_declaration_no': row.customs_declaration_no,
                'logistics_notes': row.logistics_notes,
                'remarks': row.remarks,
                'po_count': row.po_count,
                'total_value': row.total_value or 0,
                'purchase_orders': pos_data,
                'created_at': str(row.created_at) if row.created_at else None,
                'updated_at': str(row.updated_at) if row.updated_at else None
            }
            consolidations_data.append(consolidation_data)

        return jsonify({
            'success': True,
            'data': consolidations_data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total_count,
                'has_more': has_more
            },
            'summary': {
                'total_consolidations': total_count,
                'pending_delivery': len([c for c in consolidations_data if c['logistics_status'] != 'delivered']),
                'delivered': len([c for c in consolidations_data if c['logistics_status'] == 'delivered'])
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error getting consolidation list: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': {
                'code': 'CONSOLIDATION_LIST_ERROR',
                'message': 'Failed to retrieve consolidation list',
                'details': str(e)
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 500