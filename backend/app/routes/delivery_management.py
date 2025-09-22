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

@delivery_bp.route('/orders/<po_number>/remarks', methods=['PUT', 'OPTIONS'])
@jwt_required()
def update_po_remarks(po_number):
    """Update remarks/tracking number for a purchase order"""

    # Handle OPTIONS request for CORS
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = request.get_json()
        remarks = data.get('remarks', '')

        # Update the purchase order's remarks using raw SQL
        update_query = text("""
            UPDATE purchase_orders
            SET remarks = :remarks,
                updated_at = :updated_at
            WHERE purchase_order_no = :po_number
        """)

        result = db.session.execute(update_query, {
            'remarks': remarks,
            'updated_at': datetime.utcnow(),
            'po_number': po_number
        })

        if result.rowcount == 0:
            return jsonify({
                'success': False,
                'error': 'Purchase order not found'
            }), 404

        # Also update purchase order items
        update_items_query = text("""
            UPDATE purchase_order_items
            SET remarks = :remarks
            WHERE purchase_order_no = :po_number
        """)

        db.session.execute(update_items_query, {
            'remarks': remarks,
            'po_number': po_number
        })

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Remarks updated successfully',
            'data': {
                'po_number': po_number,
                'remarks': remarks
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating remarks for {po_number}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@delivery_bp.route('/orders/<po_number>/status', methods=['PUT', 'OPTIONS'])
@jwt_required()
def update_po_status(po_number):
    """Update delivery status for a specific purchase order"""

    # Handle OPTIONS request for CORS
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = request.get_json()
        new_status = data.get('new_status')  # Changed from 'delivery_status' to match frontend
        remarks = data.get('remarks', '')
        expected_date = data.get('expected_delivery_date')
        actual_date = data.get('actual_delivery_date')

        # Update the purchase order's status using raw SQL
        update_query = text("""
            UPDATE purchase_orders
            SET delivery_status = :new_status,
                remarks = :remarks,
                expected_delivery_date = :expected_date,
                actual_delivery_date = :actual_date,
                status_update_required = false,
                updated_at = :updated_at
            WHERE purchase_order_no = :po_number
        """)

        result = db.session.execute(update_query, {
            'new_status': new_status,
            'remarks': remarks,
            'expected_date': expected_date,
            'actual_date': actual_date,
            'updated_at': datetime.utcnow(),
            'po_number': po_number
        })

        if result.rowcount == 0:
            return jsonify({
                'success': False,
                'error': 'Purchase order not found'
            }), 404

        # Also update purchase order items status if delivered
        if new_status == 'delivered':
            update_items_query = text("""
                UPDATE purchase_order_items
                SET delivery_status = 'delivered'
                WHERE purchase_order_no = :po_number
            """)
            db.session.execute(update_items_query, {'po_number': po_number})

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Delivery status updated successfully',
            'data': {
                'po_number': po_number,
                'delivery_status': new_status,
                'remarks': remarks
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating status for {po_number}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@delivery_bp.route('/status-update', methods=['PUT'])
@jwt_required()
def update_delivery_status():
    """
    Update delivery status for a purchase order with mandatory workflow
    """
    try:
        data = request.get_json()

        # Validate required fields
        if not data.get('purchase_order_no'):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_PO_NUMBER',
                    'message': 'Purchase order number is required'
                }
            }), 400

        po_no = data['purchase_order_no']
        new_status = data.get('delivery_status')
        remarks = data.get('remarks', '')
        expected_date = data.get('expected_delivery_date')
        actual_date = data.get('actual_delivery_date')
        user_id = get_jwt_identity()

        # Use raw SQL to update status
        update_query = text("""
            UPDATE purchase_orders
            SET delivery_status = :new_status,
                remarks = :remarks,
                expected_delivery_date = :expected_date,
                actual_delivery_date = :actual_date,
                status_update_required = false,
                updated_at = :updated_at
            WHERE purchase_order_no = :po_no
        """)

        result = db.session.execute(update_query, {
            'new_status': new_status,
            'remarks': remarks,
            'expected_date': expected_date,
            'actual_date': actual_date,
            'updated_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'po_no': po_no
        })

        if result.rowcount == 0:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'PO_NOT_FOUND',
                    'message': 'Purchase order not found'
                }
            }), 404

        # Log the status change
        log_query = text("""
            INSERT INTO remarks_history (
                reference_type,
                reference_id,
                remarks,
                created_by,
                created_at
            ) VALUES (
                'delivery_status',
                :po_no,
                :remarks,
                :user_id,
                :created_at
            )
        """)

        db.session.execute(log_query, {
            'po_no': po_no,
            'remarks': f"Delivery status updated to {new_status}. {remarks}",
            'user_id': user_id,
            'created_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        })

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Delivery status updated successfully',
            'data': {
                'purchase_order_no': po_no,
                'delivery_status': new_status,
                'updated_at': datetime.utcnow().isoformat()
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating delivery status: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'STATUS_UPDATE_ERROR',
                'message': 'Failed to update delivery status',
                'details': str(e)
            }
        }), 500


@delivery_bp.route('/consolidations', methods=['POST'])
@jwt_required()
def create_consolidation():
    """
    Create a new consolidation order
    """
    try:
        data = request.get_json()

        # Validate required fields
        if not data.get('consolidation_name'):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_NAME',
                    'message': 'Consolidation name is required'
                }
            }), 400

        if not data.get('purchase_order_nos') or not isinstance(data['purchase_order_nos'], list):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_POS',
                    'message': 'At least one purchase order is required'
                }
            }), 400

        user_id = get_jwt_identity()

        # Generate consolidation ID
        count_query = text("SELECT COUNT(*) FROM shipment_consolidations")
        count = db.session.execute(count_query).scalar()
        consolidation_id = f"CONSOL{datetime.now().strftime('%Y%m%d')}{str(count + 1).zfill(3)}"

        # Insert consolidation
        insert_query = text("""
            INSERT INTO shipment_consolidations (
                consolidation_id,
                consolidation_name,
                logistics_status,
                expected_delivery_date,
                total_weight,
                total_volume,
                carrier,
                tracking_number,
                customs_declaration_no,
                logistics_notes,
                remarks,
                created_by,
                created_at,
                updated_at
            ) VALUES (
                :consolidation_id,
                :consolidation_name,
                :logistics_status,
                :expected_delivery_date,
                :total_weight,
                :total_volume,
                :carrier,
                :tracking_number,
                :customs_declaration_no,
                :logistics_notes,
                :remarks,
                :created_by,
                :created_at,
                :updated_at
            )
        """)

        current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

        db.session.execute(insert_query, {
            'consolidation_id': consolidation_id,
            'consolidation_name': data['consolidation_name'],
            'logistics_status': 'in_transit',  # Use 'in_transit' which is likely a valid ENUM value
            'expected_delivery_date': data.get('expected_delivery_date'),
            'total_weight': data.get('total_weight', 0),
            'total_volume': data.get('total_volume', 0),
            'carrier': data.get('carrier'),
            'tracking_number': data.get('tracking_number'),
            'customs_declaration_no': data.get('customs_declaration_no'),
            'logistics_notes': data.get('logistics_notes'),
            'remarks': data.get('remarks'),
            'created_by': user_id,
            'created_at': current_time,
            'updated_at': current_time
        })

        # Link purchase orders to consolidation
        for po_no in data['purchase_order_nos']:
            # Add to consolidation_pos table
            link_query = text("""
                INSERT INTO consolidation_pos (
                    consolidation_id,
                    purchase_order_no
                ) VALUES (
                    :consolidation_id,
                    :purchase_order_no
                )
            """)

            db.session.execute(link_query, {
                'consolidation_id': consolidation_id,
                'purchase_order_no': po_no
            })

            # Update purchase order with consolidation_id
            update_po_query = text("""
                UPDATE purchase_orders
                SET consolidation_id = :consolidation_id,
                    updated_at = :updated_at
                WHERE purchase_order_no = :po_no
            """)

            db.session.execute(update_po_query, {
                'consolidation_id': consolidation_id,
                'updated_at': current_time,
                'po_no': po_no
            })

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Consolidation created successfully',
            'data': {
                'consolidation_id': consolidation_id,
                'consolidation_name': data['consolidation_name'],
                'purchase_orders': data['purchase_order_nos'],
                'created_at': current_time
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating consolidation: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'CONSOLIDATION_CREATE_ERROR',
                'message': 'Failed to create consolidation',
                'details': str(e)
            }
        }), 500


@delivery_bp.route('/consolidation/<consolidation_id>', methods=['GET'])
@jwt_required()
def get_consolidation_details(consolidation_id):
    """
    Get single consolidation details
    """
    try:
        # Get consolidation info
        consol_query = text("""
            SELECT
                sc.*,
                (SELECT COUNT(*) FROM consolidation_pos cp WHERE cp.consolidation_id = sc.consolidation_id) as po_count,
                (SELECT COUNT(*)
                 FROM purchase_order_items poi
                 JOIN consolidation_pos cp ON poi.purchase_order_no = cp.purchase_order_no
                 WHERE cp.consolidation_id = sc.consolidation_id) as total_items
            FROM shipment_consolidations sc
            WHERE sc.consolidation_id = :consolidation_id
        """)

        consol_result = db.session.execute(consol_query, {'consolidation_id': consolidation_id}).fetchone()

        if not consol_result:
            return jsonify({
                'success': False,
                'error': 'Consolidation not found'
            }), 404

        # Get POs in this consolidation
        po_query = text("""
            SELECT
                po.*,
                s.supplier_name,
                s.supplier_region,
                (SELECT COUNT(*) FROM purchase_order_items poi WHERE poi.purchase_order_no = po.purchase_order_no) as item_count
            FROM purchase_orders po
            JOIN consolidation_pos cp ON po.purchase_order_no = cp.purchase_order_no
            LEFT JOIN suppliers s ON po.supplier_id = s.supplier_id
            WHERE cp.consolidation_id = :consolidation_id
            ORDER BY po.purchase_order_no
        """)

        po_results = db.session.execute(po_query, {'consolidation_id': consolidation_id}).fetchall()

        pos_data = []
        for po_row in po_results:
            pos_data.append({
                'purchase_order_no': po_row.purchase_order_no,
                'supplier_name': po_row.supplier_name,
                'delivery_status': po_row.delivery_status,
                'logistics_status': po_row.delivery_status,  # Use delivery_status as logistics_status
                'expected_delivery_date': str(po_row.expected_delivery_date) if po_row.expected_delivery_date else None,
                'actual_delivery_date': str(po_row.actual_delivery_date) if po_row.actual_delivery_date else None,
                'remarks': po_row.remarks,
                'tracking_number': po_row.tracking_number if hasattr(po_row, 'tracking_number') else None,
                'item_count': po_row.item_count
            })

        return jsonify({
            'success': True,
            'data': {
                'consolidation_id': consol_result.consolidation_id,
                'consolidation_name': consol_result.consolidation_name,
                'logistics_status': consol_result.logistics_status,
                'expected_delivery_date': str(consol_result.expected_delivery_date) if consol_result.expected_delivery_date else None,
                'actual_delivery_date': str(consol_result.actual_delivery_date) if consol_result.actual_delivery_date else None,
                'carrier': consol_result.carrier,
                'tracking_number': consol_result.tracking_number,
                'total_weight': float(consol_result.total_weight) if consol_result.total_weight else 0,
                'total_volume': float(consol_result.total_volume) if consol_result.total_volume else 0,
                'remarks': consol_result.remarks,
                'po_count': consol_result.po_count,
                'total_items': consol_result.total_items,
                'purchase_orders': pos_data,
                'created_at': str(consol_result.created_at) if consol_result.created_at else None,
                'updated_at': str(consol_result.updated_at) if consol_result.updated_at else None
            }
        })

    except Exception as e:
        logger.error(f"Error getting consolidation details: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@delivery_bp.route('/consolidation/<consolidation_id>/status', methods=['PUT'])
@jwt_required()
def update_consolidation_status(consolidation_id):
    """
    Update logistics status for a consolidation
    """
    try:
        data = request.get_json()
        new_status = data.get('logistics_status')

        if not new_status:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_STATUS',
                    'message': 'Logistics status is required'
                }
            }), 400

        # Update consolidation status
        update_query = text("""
            UPDATE shipment_consolidations
            SET logistics_status = :new_status,
                actual_delivery_date = :actual_date,
                logistics_notes = :logistics_notes,
                updated_at = :updated_at
            WHERE consolidation_id = :consolidation_id
        """)

        result = db.session.execute(update_query, {
            'new_status': new_status,
            'actual_date': data.get('actual_delivery_date'),
            'logistics_notes': data.get('logistics_notes'),
            'updated_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'consolidation_id': consolidation_id
        })

        if result.rowcount == 0:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'CONSOLIDATION_NOT_FOUND',
                    'message': 'Consolidation not found'
                }
            }), 404

        # If delivered, update all POs in consolidation
        if new_status == 'delivered':
            update_pos_query = text("""
                UPDATE purchase_orders
                SET delivery_status = 'arrived',
                    actual_delivery_date = :actual_date,
                    updated_at = :updated_at
                WHERE consolidation_id = :consolidation_id
            """)

            db.session.execute(update_pos_query, {
                'actual_date': data.get('actual_delivery_date'),
                'updated_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                'consolidation_id': consolidation_id
            })

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Consolidation status updated successfully',
            'data': {
                'consolidation_id': consolidation_id,
                'logistics_status': new_status,
                'updated_at': datetime.utcnow().isoformat()
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating consolidation status: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'STATUS_UPDATE_ERROR',
                'message': 'Failed to update consolidation status',
                'details': str(e)
            }
        }), 500

# Removed duplicate update_po_remarks function