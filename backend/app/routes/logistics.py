"""
Logistics Management API Routes
Handles shipping, receiving, and delivery tracking operations
Architecture Lead: Winston
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import and_, func, desc, or_
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
import logging

from app import db
from app.models import (
    LogisticsEvent, PurchaseOrder, PurchaseOrderItem, 
    Supplier, User
)
from app.auth import require_roles
from app.utils.validation import validate_date_string
from app.utils.pagination import paginate_query
from app.utils.cache import cache_result, invalidate_cache

# Create blueprint
logistics_bp = Blueprint('logistics', __name__, url_prefix='/api/v1/logistics')
logger = logging.getLogger(__name__)

@logistics_bp.route('/shipping', methods=['GET'])
@jwt_required()
def list_shipping():
    """
    List all shipping records and events
    Query Parameters:
    - status: filter by shipping status
    - po_no: filter by purchase order number
    - date_from: filter from date (YYYY-MM-DD)
    - date_to: filter to date (YYYY-MM-DD)
    - page: int (default: 1)
    - page_size: int (default: 50)
    """
    try:
        # Get query parameters
        status = request.args.get('status')
        po_no = request.args.get('po_no')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        page = request.args.get('page', 1, type=int)
        page_size = min(request.args.get('page_size', 50, type=int), 100)
        
        # Build query for purchase orders with shipping information
        query = db.session.query(PurchaseOrder)\
                .join(Supplier, PurchaseOrder.supplier_id == Supplier.id)\
                .filter(PurchaseOrder.shipping_status.isnot(None))
        
        # Apply filters
        if status:
            query = query.filter(PurchaseOrder.shipping_status == status)
        if po_no:
            query = query.filter(PurchaseOrder.po_no.ilike(f'%{po_no}%'))
        if date_from:
            try:
                from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
                query = query.filter(PurchaseOrder.po_date >= from_date)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_DATE_FORMAT',
                        'message': 'Invalid date format. Use YYYY-MM-DD',
                        'details': {'date_from': date_from}
                    },
                    'timestamp': datetime.utcnow().isoformat()
                }), 422
        if date_to:
            try:
                to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
                query = query.filter(PurchaseOrder.po_date <= to_date)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_DATE_FORMAT',
                        'message': 'Invalid date format. Use YYYY-MM-DD',
                        'details': {'date_to': date_to}
                    },
                    'timestamp': datetime.utcnow().isoformat()
                }), 422
        
        # Order by most recent
        query = query.order_by(desc(PurchaseOrder.po_date))
        
        # Paginate
        paginated_result = paginate_query(query, page, page_size)
        
        # Format shipping data
        shipping_data = []
        for po in paginated_result['items']:
            # Get logistics events for this PO
            logistics_events = LogisticsEvent.query\
                             .filter(LogisticsEvent.purchase_order_no == po.po_no)\
                             .order_by(desc(LogisticsEvent.happened_at))\
                             .all()
            
            events_data = [
                {
                    'event_id': event.event_id,
                    'status': event.status,
                    'happened_at': event.happened_at.isoformat(),
                    'note': event.note,
                    'created_at': event.created_at.isoformat()
                }
                for event in logistics_events
            ]
            
            po_data = {
                'id': po.id,
                'po_no': po.po_no,
                'po_date': po.po_date.isoformat(),
                'supplier': {
                    'id': po.supplier.id,
                    'name': po.supplier.supplier_name_zh,
                    'contact': po.supplier.contact_name
                },
                'total_amount': float(po.total_amount) if po.total_amount else 0,
                'shipping_status': po.shipping_status,
                'expected_delivery_date': po.expected_delivery_date.isoformat() if po.expected_delivery_date else None,
                'logistics_events': events_data,
                'items_count': len(po.items),
                'created_at': po.created_at.isoformat()
            }
            shipping_data.append(po_data)
        
        return jsonify({
            'success': True,
            'data': shipping_data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': paginated_result['total'],
                'has_more': paginated_result['has_more']
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing shipping records: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'SHIPPING_LIST_ERROR',
                'message': 'Failed to retrieve shipping records',
                'details': str(e)
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@logistics_bp.route('/receiving', methods=['GET'])
@jwt_required()
def list_receiving():
    """
    List items ready for receiving
    Query Parameters:
    - status: filter by receiving status
    - supplier_id: filter by supplier
    - urgent_only: boolean (show only urgent items)
    - page: int (default: 1)
    - page_size: int (default: 50)
    """
    try:
        # Get query parameters
        status = request.args.get('status', 'expected_arrival')
        supplier_id = request.args.get('supplier_id', type=int)
        urgent_only = request.args.get('urgent_only', 'false').lower() == 'true'
        page = request.args.get('page', 1, type=int)
        page_size = min(request.args.get('page_size', 50, type=int), 100)
        
        # Query purchase orders ready for receiving
        query = db.session.query(PurchaseOrder)\
                .join(Supplier, PurchaseOrder.supplier_id == Supplier.id)\
                .filter(PurchaseOrder.shipping_status.in_(['expected_arrival', 'arrived']))
        
        # Apply filters
        if status != 'all':
            query = query.filter(PurchaseOrder.shipping_status == status)
        if supplier_id:
            query = query.filter(PurchaseOrder.supplier_id == supplier_id)
        if urgent_only:
            # Items that are overdue for receiving
            overdue_date = datetime.utcnow().date() - timedelta(days=2)
            query = query.filter(PurchaseOrder.expected_delivery_date < overdue_date)
        
        # Order by expected delivery date (most urgent first)
        query = query.order_by(PurchaseOrder.expected_delivery_date.asc())
        
        # Paginate
        paginated_result = paginate_query(query, page, page_size)
        
        # Format receiving data
        receiving_data = []
        for po in paginated_result['items']:
            # Calculate urgency
            is_overdue = False
            days_until_due = None
            if po.expected_delivery_date:
                days_until_due = (po.expected_delivery_date - datetime.utcnow().date()).days
                is_overdue = days_until_due < 0
            
            # Get items that still need receiving
            pending_items = [
                {
                    'id': item.id,
                    'item_reference': item.item_reference,
                    'item_name': item.item_name,
                    'item_spec': item.item_spec,
                    'quantity': item.quantity,
                    'received_quantity': item.received_quantity or 0,
                    'remaining_quantity': item.quantity - (item.received_quantity or 0),
                    'unit': item.unit,
                    'receiving_status': item.receiving_status
                }
                for item in po.items
                if item.receiving_status in [None, 'pending', 'partial']
            ]
            
            po_data = {
                'id': po.id,
                'po_no': po.po_no,
                'po_date': po.po_date.isoformat(),
                'supplier': {
                    'id': po.supplier.id,
                    'name': po.supplier.supplier_name_zh,
                    'contact': po.supplier.contact_name
                },
                'total_amount': float(po.total_amount) if po.total_amount else 0,
                'shipping_status': po.shipping_status,
                'expected_delivery_date': po.expected_delivery_date.isoformat() if po.expected_delivery_date else None,
                'is_overdue': is_overdue,
                'days_until_due': days_until_due,
                'pending_items': pending_items,
                'pending_items_count': len(pending_items),
                'total_items_count': len(po.items),
                'priority': 'high' if is_overdue else 'medium' if days_until_due and days_until_due <= 1 else 'normal'
            }
            receiving_data.append(po_data)
        
        return jsonify({
            'success': True,
            'data': receiving_data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': paginated_result['total'],
                'has_more': paginated_result['has_more']
            },
            'summary': {
                'overdue_count': len([po for po in receiving_data if po['is_overdue']]),
                'urgent_count': len([po for po in receiving_data if po['priority'] == 'high']),
                'total_pending_items': sum([po['pending_items_count'] for po in receiving_data])
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing receiving items: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'RECEIVING_LIST_ERROR',
                'message': 'Failed to retrieve receiving items',
                'details': str(e)
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@logistics_bp.route('/delivery-tracking', methods=['GET'])
@jwt_required()
def track_deliveries():
    """
    Track delivery status for purchase orders
    Query Parameters:
    - po_no: specific purchase order number
    - status: filter by status
    - active_only: boolean (show only active shipments)
    - page: int (default: 1)
    - page_size: int (default: 50)
    """
    try:
        # Get query parameters
        po_no = request.args.get('po_no')
        status = request.args.get('status')
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        page = request.args.get('page', 1, type=int)
        page_size = min(request.args.get('page_size', 50, type=int), 100)
        
        # Query logistics events
        query = db.session.query(LogisticsEvent)\
                .join(PurchaseOrder, LogisticsEvent.purchase_order_no == PurchaseOrder.po_no)\
                .join(Supplier, PurchaseOrder.supplier_id == Supplier.id)
        
        # Apply filters
        if po_no:
            query = query.filter(LogisticsEvent.purchase_order_no == po_no)
        if status:
            query = query.filter(LogisticsEvent.status == status)
        if active_only:
            # Only show shipments that haven't arrived yet
            query = query.filter(LogisticsEvent.status.notin_(['arrived', 'delivered']))
        
        # Order by most recent events
        query = query.order_by(desc(LogisticsEvent.happened_at))
        
        # Paginate
        paginated_result = paginate_query(query, page, page_size)
        
        # Format tracking data
        tracking_data = []
        for event in paginated_result['items']:
            po = event.purchase_order if hasattr(event, 'purchase_order') else PurchaseOrder.query.filter_by(po_no=event.purchase_order_no).first()
            
            if po:
                # Get all events for this PO for timeline
                all_events = LogisticsEvent.query\
                           .filter(LogisticsEvent.purchase_order_no == event.purchase_order_no)\
                           .order_by(LogisticsEvent.happened_at)\
                           .all()
                
                timeline = [
                    {
                        'status': e.status,
                        'happened_at': e.happened_at.isoformat(),
                        'note': e.note,
                        'is_current': e.event_id == event.event_id
                    }
                    for e in all_events
                ]
                
                # Estimate delivery progress
                status_order = ['shipped', 'in_transit', 'customs_clearance', 'expected_arrival', 'arrived']
                current_index = status_order.index(event.status) if event.status in status_order else 0
                progress_percent = ((current_index + 1) / len(status_order)) * 100
                
                event_data = {
                    'event_id': event.event_id,
                    'po_no': event.purchase_order_no,
                    'current_status': event.status,
                    'happened_at': event.happened_at.isoformat(),
                    'note': event.note,
                    'supplier': {
                        'id': po.supplier.id,
                        'name': po.supplier.supplier_name_zh,
                        'contact': po.supplier.contact_name
                    },
                    'expected_delivery_date': po.expected_delivery_date.isoformat() if po.expected_delivery_date else None,
                    'total_amount': float(po.total_amount) if po.total_amount else 0,
                    'progress_percent': round(progress_percent, 1),
                    'is_active': event.status not in ['arrived', 'delivered'],
                    'timeline': timeline,
                    'items_count': len(po.items) if po.items else 0
                }
                tracking_data.append(event_data)
        
        return jsonify({
            'success': True,
            'data': tracking_data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': paginated_result['total'],
                'has_more': paginated_result['has_more']
            },
            'summary': {
                'active_shipments': len([t for t in tracking_data if t['is_active']]),
                'completed_shipments': len([t for t in tracking_data if not t['is_active']]),
                'total_tracked': len(tracking_data)
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error tracking deliveries: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'DELIVERY_TRACKING_ERROR',
                'message': 'Failed to track deliveries',
                'details': str(e)
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@logistics_bp.route('/shipping/update-status', methods=['POST'])
@jwt_required()
@require_roles(['Admin', 'ProcurementMgr', 'LogisticsCoord'])
def update_shipping_status():
    """
    Update shipping status and create logistics event
    Required fields: po_no, status, happened_at
    Optional fields: note
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['po_no', 'status', 'happened_at']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'MISSING_REQUIRED_FIELD',
                        'message': f'Required field missing: {field}',
                        'details': {'field': field}
                    },
                    'timestamp': datetime.utcnow().isoformat()
                }), 422
        
        # Get purchase order
        po = PurchaseOrder.query.filter_by(po_no=data['po_no']).first()
        if not po:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'PO_NOT_FOUND',
                    'message': 'Purchase order not found',
                    'details': {'po_no': data['po_no']}
                },
                'timestamp': datetime.utcnow().isoformat()
            }), 404
        
        # Validate status
        valid_statuses = ['shipped', 'in_transit', 'customs_clearance', 'expected_arrival', 'arrived']
        if data['status'] not in valid_statuses:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_STATUS',
                    'message': 'Invalid shipping status',
                    'details': {'valid_statuses': valid_statuses}
                },
                'timestamp': datetime.utcnow().isoformat()
            }), 422
        
        # Parse happened_at date
        try:
            happened_at = datetime.fromisoformat(data['happened_at'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_DATE_FORMAT',
                    'message': 'Invalid date format for happened_at',
                    'details': {'expected_format': 'ISO 8601 (e.g., 2023-12-01T10:30:00Z)'}
                },
                'timestamp': datetime.utcnow().isoformat()
            }), 422
        
        # Create logistics event
        logistics_event = LogisticsEvent.create_po_event(
            purchase_order_no=data['po_no'],
            status=data['status'],
            happened_at=happened_at,
            note=data.get('note', ''),
            created_by=get_jwt_identity()
        )
        
        db.session.add(logistics_event)
        
        # Update PO shipping status
        po.shipping_status = data['status']
        po.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Invalidate cache
        invalidate_cache('logistics:*')
        
        logger.info(f"Shipping status updated: PO {data['po_no']} to {data['status']} by user {get_jwt_identity()}")
        
        return jsonify({
            'success': True,
            'data': {
                'event_id': logistics_event.event_id,
                'po_no': po.po_no,
                'new_status': data['status'],
                'happened_at': happened_at.isoformat(),
                'note': data.get('note', ''),
                'created_at': logistics_event.created_at.isoformat()
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating shipping status: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'SHIPPING_UPDATE_ERROR',
                'message': 'Failed to update shipping status',
                'details': str(e)
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@logistics_bp.route('/receiving/confirm-item', methods=['POST'])
@jwt_required()
@require_roles(['Admin', 'ProcurementMgr', 'WarehouseMgr'])
def confirm_item_received():
    """
    Confirm receipt of specific item
    Required fields: po_item_id, received_quantity
    Optional fields: notes, condition
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['po_item_id', 'received_quantity']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'MISSING_REQUIRED_FIELD',
                        'message': f'Required field missing: {field}',
                        'details': {'field': field}
                    },
                    'timestamp': datetime.utcnow().isoformat()
                }), 422
        
        # Get PO item
        po_item = PurchaseOrderItem.query.get(data['po_item_id'])
        if not po_item:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'PO_ITEM_NOT_FOUND',
                    'message': 'Purchase order item not found',
                    'details': {'po_item_id': data['po_item_id']}
                },
                'timestamp': datetime.utcnow().isoformat()
            }), 404
        
        received_quantity = data['received_quantity']
        
        # Validate quantity
        if received_quantity <= 0:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_QUANTITY',
                    'message': 'Received quantity must be greater than zero',
                    'details': {'received_quantity': received_quantity}
                },
                'timestamp': datetime.utcnow().isoformat()
            }), 422
        
        # Update item receiving status
        current_received = po_item.received_quantity or 0
        new_total_received = current_received + received_quantity
        
        if new_total_received > po_item.quantity:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'QUANTITY_EXCEEDS_ORDERED',
                    'message': 'Total received quantity cannot exceed ordered quantity',
                    'details': {
                        'ordered_quantity': po_item.quantity,
                        'already_received': current_received,
                        'attempted_to_receive': received_quantity
                    }
                },
                'timestamp': datetime.utcnow().isoformat()
            }), 422
        
        po_item.received_quantity = new_total_received
        po_item.received_date = datetime.utcnow()
        
        # Set receiving status
        if new_total_received >= po_item.quantity:
            po_item.receiving_status = 'received'
        else:
            po_item.receiving_status = 'partial'
        
        # Add notes if provided
        if data.get('notes'):
            po_item.notes = (po_item.notes or '') + f"\n[{datetime.utcnow().strftime('%Y-%m-%d %H:%M')}] {data['notes']}"
        
        po_item.updated_at = datetime.utcnow()
        
        # Check if all items in PO are received
        po = po_item.purchase_order
        all_items_received = all(
            item.receiving_status in ['received'] 
            for item in po.items
        )
        
        if all_items_received:
            po.shipping_status = 'arrived'
            
            # Create logistics event for full PO arrival
            logistics_event = LogisticsEvent.create_po_event(
                purchase_order_no=po.po_no,
                status='arrived',
                happened_at=datetime.utcnow(),
                note=f'All items received - PO complete',
                created_by=get_jwt_identity()
            )
            db.session.add(logistics_event)
        
        db.session.commit()
        
        # Invalidate cache
        invalidate_cache('logistics:*')
        
        logger.info(f"Item received: {po_item.item_reference} qty {received_quantity} by user {get_jwt_identity()}")
        
        return jsonify({
            'success': True,
            'data': {
                'po_item_id': po_item.id,
                'item_reference': po_item.item_reference,
                'received_quantity': received_quantity,
                'total_received': new_total_received,
                'ordered_quantity': po_item.quantity,
                'receiving_status': po_item.receiving_status,
                'po_fully_received': all_items_received,
                'received_date': po_item.received_date.isoformat()
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error confirming item receipt: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'ITEM_RECEIPT_ERROR',
                'message': 'Failed to confirm item receipt',
                'details': str(e)
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 500