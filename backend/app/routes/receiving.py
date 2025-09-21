from flask import Blueprint, request, jsonify
from datetime import datetime
from app import db
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from app.models.request_order import RequestOrderItem
from app.auth import authenticated_required, create_response, create_error_response

bp = Blueprint('receiving', __name__, url_prefix='/api/v1/receiving')

@bp.route('/shipped-items', methods=['GET'])
@authenticated_required
def get_shipped_items(current_user):
    """Get list of shipped items ready for receiving"""
    try:
        po_number = request.args.get('po_number', '')
        consolidation_number = request.args.get('consolidation_number', '')
        supplier_id = request.args.get('supplier_id', '')

        # Query purchase orders that have been shipped
        query = PurchaseOrder.query.filter(
            PurchaseOrder.delivery_status == 'shipped'
        )

        if po_number:
            query = query.filter(PurchaseOrder.purchase_order_no.like(f'%{po_number}%'))
        if supplier_id:
            query = query.filter(PurchaseOrder.supplier_id == supplier_id)

        orders = query.all()

        # Build response with items in the format expected by frontend
        result = []
        for order in orders:
            # Get supplier info
            from app.models.supplier import Supplier
            supplier = Supplier.query.get(order.supplier_id)

            # Get associated requisition items
            from app.models.request_order import RequestOrder, RequestOrderItem

            for item in order.items:
                if item.line_status == 'active':  # Only include non-received items
                    # Get requisition number if available
                    req_number = ''
                    if item.source_request_order_no:
                        req_number = item.source_request_order_no

                    result.append({
                        'id': item.detail_id,  # Frontend expects 'id' field
                        'item_name': item.item_name,
                        'specification': item.item_specification or '',
                        'quantity': float(item.item_quantity),
                        'unit': item.item_unit,
                        'purchase_order_number': order.purchase_order_no,
                        'requisition_number': req_number,
                        'consolidation_number': consolidation_number or '',
                        'supplier_name': order.supplier_name,
                        'supplier_region': supplier.supplier_region if supplier else 'domestic',
                        'delivery_status': order.delivery_status,
                        'shipped_date': order.shipped_at.isoformat() if order.shipped_at else '',
                        'remarks': item.remarks or ''
                    })

        return result, 200  # Return as list directly, frontend expects array

    except Exception as e:
        return create_error_response(
            'SHIPPED_ITEMS_ERROR',
            'Failed to fetch shipped items',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/confirm', methods=['POST'])
@authenticated_required
def confirm_receiving(current_user):
    """Confirm receipt of a single item"""
    try:
        data = request.get_json()

        if not data:
            return create_error_response(
                'MISSING_DATA',
                'Request data is required',
                status_code=400
            )

        # Check if it's a batch request (items array) or single item
        if 'items' in data:
            # Batch receiving
            received_items = []
            for item_data in data['items']:
                item_id = item_data.get('item_id')
                received_quantity = item_data.get('received_quantity', item_data.get('quantity', 0))

                if not item_id:
                    continue

                # Get the purchase order item
                po_item = PurchaseOrderItem.query.get(item_id)
                if not po_item:
                    continue

                # Mark item as completed when received
                po_item.line_status = 'completed'
                po_item.updated_at = datetime.utcnow()

                # Update the linked requisition item status to 'arrived'
                if po_item.source_detail_id:
                    req_item = RequestOrderItem.query.get(po_item.source_detail_id)
                    if req_item:
                        req_item.item_status = 'arrived'
                        req_item.updated_at = datetime.utcnow()

                received_items.append({
                    'item_id': item_id,
                    'item_name': po_item.item_name,
                    'received_quantity': received_quantity,
                    'total_received': received_quantity
                })

                # Check if all items in the PO are received
                po = PurchaseOrder.query.get(po_item.purchase_order_no)
                if po:
                    all_received = all(
                        item.line_status == 'completed'
                        for item in po.items
                    )

                    if all_received:
                        po.shipping_status = 'received'
                        po.delivery_status = 'delivered'
                        po.actual_delivery_date = datetime.utcnow()
                    else:
                        po.shipping_status = 'partial_received'

        else:
            # Single item receiving
            item_id = data.get('item_id')
            if not item_id:
                return create_error_response(
                    'MISSING_FIELD',
                    'item_id is required',
                    status_code=400
                )

            purchase_order_number = data.get('purchase_order_number')
            quantity = data.get('quantity', 0)

            # For single item, just update the PO status
            # The actual receiving_records table has a different structure
            # So we'll skip creating a receiving record for now

            # Update PO item status if we have the PO number
            if purchase_order_number:
                po = PurchaseOrder.query.get(purchase_order_number)
                if po:
                    # Mark the PO as received
                    po.delivery_status = 'delivered'
                    po.actual_delivery_date = datetime.utcnow()

                    # Update all PO items and their linked requisition items
                    for po_item in po.items.all():
                        po_item.line_status = 'completed'
                        po_item.updated_at = datetime.utcnow()

                        # Update the linked requisition item status to 'arrived'
                        if po_item.source_detail_id:
                            req_item = RequestOrderItem.query.get(po_item.source_detail_id)
                            if req_item:
                                req_item.item_status = 'arrived'
                                req_item.updated_at = datetime.utcnow()

            received_items = [{
                'item_id': item_id,
                'item_name': data.get('item_name', ''),
                'received_quantity': quantity,
                'purchase_order_number': purchase_order_number
            }]

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Successfully received {len(received_items)} item(s)',
            'data': {
                'received_items': received_items,
                'timestamp': datetime.utcnow().isoformat()
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'RECEIVING_CONFIRM_ERROR',
            'Failed to confirm receiving',
            {'error': str(e)},
            status_code=500
        )