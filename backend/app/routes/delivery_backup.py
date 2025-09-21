"""
Delivery Management API Routes
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import logging

from app import db
from app.models import PurchaseOrder, Supplier

# Create blueprint
delivery_bp = Blueprint('delivery', __name__, url_prefix='/api/v1/delivery')
logger = logging.getLogger(__name__)

@delivery_bp.route('/maintenance-list', methods=['GET'])
@jwt_required()
def get_delivery_maintenance_list():
    """Get Delivery Maintenance List"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        status_filter = request.args.get('status', '')
        supplier_region_filter = request.args.get('supplier_region', '')
        po_number_filter = request.args.get('po_number', '')
        
        # Start with base query
        query = db.session.query(PurchaseOrder)\
            .join(Supplier, PurchaseOrder.supplier_id == Supplier.supplier_id)\
            .filter(PurchaseOrder.purchase_status == 'purchased')
        
        # Apply filters
        if supplier_region_filter:
            query = query.filter(Supplier.supplier_region == supplier_region_filter)
        
        if status_filter:
            query = query.filter(PurchaseOrder.delivery_status == status_filter)
            
        if po_number_filter:
            query = query.filter(PurchaseOrder.purchase_order_no.ilike(f'%{po_number_filter}%'))
        
        # Execute query
        pos = query.all()
        
        maintenance_list = []
        for po in pos:
            # Check if PO is in delivery maintenance list
            # (domestic or international not in consolidation)
            supplier = Supplier.query.get(po.supplier_id)
            if supplier and (supplier.supplier_region == 'domestic' or 
                           (supplier.supplier_region == 'international' and not po.consolidation_id)):
                maintenance_list.append({
                    'po_number': po.purchase_order_no,
                    'supplier_id': po.supplier_id,
                    'supplier_name': po.supplier_name,
                    'supplier_region': supplier.supplier_region,
                    'delivery_status': po.delivery_status or 'not_shipped',
                    'expected_delivery_date': po.expected_delivery_date.isoformat() if po.expected_delivery_date else None,
                    'actual_delivery_date': po.actual_delivery_date.isoformat() if po.actual_delivery_date else None,
                    'remarks': po.remarks or '',
                    'status_update_required': po.status_update_required,
                    'consolidation_id': po.consolidation_id,
                    'item_count': po.items.count() if hasattr(po, 'items') else 0,
                    'can_create_consolidation': (
                        supplier.supplier_region == 'international' and 
                        po.delivery_status == 'shipped' and 
                        not po.consolidation_id
                    )
                })
        
        # Calculate summary statistics
        total_pos = len(maintenance_list)
        need_update = sum(1 for po in maintenance_list if po['status_update_required'])
        can_consolidate = sum(1 for po in maintenance_list if po['can_create_consolidation'])
        domestic_count = sum(1 for po in maintenance_list if po['supplier_region'] == 'domestic')
        international_count = sum(1 for po in maintenance_list if po['supplier_region'] == 'international')
        
        return jsonify({
            'success': True,
            'data': maintenance_list,
            'summary': {
                'total_pos': total_pos,
                'need_status_update': need_update,
                'can_create_consolidation': can_consolidate,
                'domestic_count': domestic_count,
                'international_count': international_count
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching delivery maintenance list: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@delivery_bp.route('/orders/<po_number>/status', methods=['PUT'])
@jwt_required()
def update_delivery_status(po_number):
    """Update delivery status (mandatory workflow)"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        remarks = data.get('remarks', '')
        
        # Validate status
        valid_statuses = ['not_shipped', 'shipped', 'foreign_customs', 'taiwan_customs', 'in_transit', 'delivered']
        if new_status not in valid_statuses:
            return jsonify({
                'success': False,
                'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
            }), 400
        
        # Find the PO
        po = PurchaseOrder.query.filter_by(purchase_order_no=po_number).first()
        if not po:
            return jsonify({
                'success': False,
                'error': 'Purchase order not found'
            }), 404
        
        # Update status
        po.delivery_status = new_status
        po.status_update_required = False  # Clear the mandatory update flag
        
        # Update remarks if provided
        if remarks:
            po.remarks = remarks
            # Also update all items with the same remarks
            for item in po.items:
                item.remarks = remarks
                item.delivery_status = new_status
        
        # Set dates based on status
        if new_status == 'shipped':
            po.shipped_at = datetime.now()
        elif new_status == 'delivered':
            po.actual_delivery_date = datetime.now()
        
        po.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Status updated to {new_status}',
            'data': {
                'po_number': po_number,
                'delivery_status': new_status,
                'remarks': remarks,
                'status_update_required': False
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating delivery status for {po_number}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@delivery_bp.route('/orders/<po_number>/remarks', methods=['PUT'])
@jwt_required()
def update_remarks(po_number):
    """Update remarks/tracking number"""
    try:
        data = request.get_json()
        remarks = data.get('remarks', '')
        
        # Find the PO
        po = PurchaseOrder.query.filter_by(purchase_order_no=po_number).first()
        if not po:
            return jsonify({
                'success': False,
                'error': 'Purchase order not found'
            }), 404
        
        # Update remarks
        po.remarks = remarks
        
        # Cascade to items
        for item in po.items:
            item.remarks = remarks
        
        po.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Remarks updated',
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

@delivery_bp.route('/consolidations', methods=['POST'])
@jwt_required()
def create_consolidation():
    """Create a new consolidation order"""
    try:
        data = request.get_json()
        po_numbers = data.get('po_numbers', [])
        consolidation_name = data.get('name', f'CONSOL-{datetime.now().strftime("%Y%m%d%H%M%S")}')
        
        if not po_numbers:
            return jsonify({
                'success': False,
                'error': 'No purchase orders selected'
            }), 400
        
        # Verify all POs are eligible
        pos = PurchaseOrder.query.filter(PurchaseOrder.purchase_order_no.in_(po_numbers)).all()
        
        for po in pos:
            supplier = Supplier.query.get(po.supplier_id)
            if not supplier or supplier.supplier_region != 'international' or po.delivery_status != 'shipped':
                return jsonify({
                    'success': False,
                    'error': f'PO {po.purchase_order_no} is not eligible for consolidation'
                }), 400
        
        # Create consolidation (simplified - full model not implemented)
        consolidation_id = f'CONSOL-{datetime.now().strftime("%Y%m%d%H%M%S")}'
        
        # Update POs with consolidation ID
        for po in pos:
            po.consolidation_id = consolidation_id
            po.updated_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Consolidation created',
            'data': {
                'consolidation_id': consolidation_id,
                'po_count': len(pos)
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating consolidation: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@delivery_bp.route('/consolidation-list', methods=['GET'])
@jwt_required()
def get_consolidation_list():
    """Get Consolidation List"""
    try:
        # Query all POs in consolidations
        pos = db.session.query(PurchaseOrder)\
            .filter(PurchaseOrder.consolidation_id != None)\
            .all()
        
        # Group by consolidation
        consolidations = {}
        for po in pos:
            consol_id = po.consolidation_id
            if consol_id not in consolidations:
                consolidations[consol_id] = {
                    'consolidation_id': consol_id,
                    'pos': [],
                    'total_items': 0,
                    'logistics_status': po.delivery_status,
                    'expected_delivery': po.expected_delivery_date.isoformat() if po.expected_delivery_date else None
                }
            
            consolidations[consol_id]['pos'].append({
                'po_number': po.purchase_order_no,
                'supplier_name': po.supplier_name,
                'item_count': po.items.count() if hasattr(po, 'items') else 0
            })
            consolidations[consol_id]['total_items'] += po.items.count() if hasattr(po, 'items') else 0
        
        return jsonify({
            'success': True,
            'data': list(consolidations.values())
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching consolidation list: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500