"""
Test delivery route with proper filtering
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import logging

from app import db
from app.models import PurchaseOrder, Supplier

# Create blueprint
test_delivery_bp = Blueprint('test_delivery', __name__, url_prefix='/api/v1/test-delivery')
logger = logging.getLogger(__name__)

@test_delivery_bp.route('/search', methods=['GET'])
@jwt_required()
def test_search():
    """Test search endpoint with debugging"""
    try:
        po_number_filter = request.args.get('po_number', '')

        # Start with base query
        query = db.session.query(PurchaseOrder)\
            .join(Supplier, PurchaseOrder.supplier_id == Supplier.supplier_id)\
            .filter(PurchaseOrder.purchase_status == 'purchased')

        # Count before filter
        count_before = query.count()

        # Apply PO number filter if present
        if po_number_filter:
            query = query.filter(PurchaseOrder.purchase_order_no.contains(po_number_filter))

        # Execute query
        pos = query.all()
        count_after = len(pos)

        # Build results
        results = []
        for po in pos:
            supplier = Supplier.query.get(po.supplier_id)
            if supplier and (supplier.supplier_region == 'domestic' or
                           (supplier.supplier_region == 'international' and not po.consolidation_id)):
                results.append({
                    'po_number': po.purchase_order_no,
                    'supplier_name': po.supplier_name,
                    'supplier_region': supplier.supplier_region
                })

        return jsonify({
            'success': True,
            'debug': {
                'filter_applied': po_number_filter,
                'count_before_filter': count_before,
                'count_after_filter': count_after,
                'final_result_count': len(results)
            },
            'data': results
        }), 200

    except Exception as e:
        logger.error(f"Test search error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500