"""
Storage Management API Routes
Handles storage locations, put-away operations, and inventory movements
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
    Storage, StorageHistory, PurchaseOrderItem, RequestOrderItem,
    PurchaseOrder, Supplier, User
)
from app.auth import require_roles
from app.utils.validation import validate_storage_data, validate_movement_data
from app.utils.pagination import paginate_query
from app.utils.cache import cache_result, invalidate_cache

# Create blueprint
storage_bp = Blueprint('storage', __name__, url_prefix='/api/v1/storage')
logger = logging.getLogger(__name__)

@storage_bp.route('/tree', methods=['GET'])
@jwt_required()
@cache_result('storage', lambda: 'tree:hierarchy')
def get_storage_tree():
    """
    Get storage location hierarchy in tree format
    Returns: Zone -> Shelf -> Floor -> Position structure
    """
    try:
        # Query all storage locations ordered by hierarchy
        storage_locations = db.session.query(Storage)\
                           .order_by(Storage.zone, Storage.shelf, Storage.floor, Storage.position)\
                           .all()
        
        # Build hierarchical tree structure
        storage_tree = {}
        
        for storage in storage_locations:
            zone_key = storage.zone or 'Unassigned'
            shelf_key = storage.shelf or 'No Shelf'
            floor_key = storage.floor or 'No Floor'
            
            # Initialize zone if not exists
            if zone_key not in storage_tree:
                storage_tree[zone_key] = {
                    'zone_name': zone_key,
                    'zone_id': storage.zone,
                    'shelves': {},
                    'total_locations': 0,
                    'available_locations': 0
                }
            
            # Initialize shelf if not exists
            if shelf_key not in storage_tree[zone_key]['shelves']:
                storage_tree[zone_key]['shelves'][shelf_key] = {
                    'shelf_name': shelf_key,
                    'shelf_id': storage.shelf,
                    'floors': {},
                    'total_locations': 0,
                    'available_locations': 0
                }
            
            # Initialize floor if not exists
            if floor_key not in storage_tree[zone_key]['shelves'][shelf_key]['floors']:
                storage_tree[zone_key]['shelves'][shelf_key]['floors'][floor_key] = {
                    'floor_name': floor_key,
                    'floor_id': storage.floor,
                    'positions': [],
                    'total_locations': 0,
                    'available_locations': 0
                }
            
            # Add position to floor
            position_data = {
                'id': storage.id,
                'position': storage.position,
                'storage_type': storage.storage_type,
                'is_available': storage.is_available,
                'max_capacity': storage.max_capacity,
                'current_capacity': storage.current_capacity,
                'description': storage.description,
                'created_at': storage.created_at.isoformat()
            }
            
            storage_tree[zone_key]['shelves'][shelf_key]['floors'][floor_key]['positions'].append(position_data)
            
            # Update counters
            storage_tree[zone_key]['shelves'][shelf_key]['floors'][floor_key]['total_locations'] += 1
            storage_tree[zone_key]['shelves'][shelf_key]['total_locations'] += 1
            storage_tree[zone_key]['total_locations'] += 1
            
            if storage.is_available:
                storage_tree[zone_key]['shelves'][shelf_key]['floors'][floor_key]['available_locations'] += 1
                storage_tree[zone_key]['shelves'][shelf_key]['available_locations'] += 1
                storage_tree[zone_key]['available_locations'] += 1
        
        # Convert to list format for frontend consumption
        zones_list = []
        for zone_name, zone_data in storage_tree.items():
            shelves_list = []
            for shelf_name, shelf_data in zone_data['shelves'].items():
                floors_list = []
                for floor_name, floor_data in shelf_data['floors'].items():
                    floors_list.append({
                        'floor_name': floor_name,
                        'floor_id': floor_data['floor_id'],
                        'positions': floor_data['positions'],
                        'total_locations': floor_data['total_locations'],
                        'available_locations': floor_data['available_locations']
                    })
                
                shelves_list.append({
                    'shelf_name': shelf_name,
                    'shelf_id': shelf_data['shelf_id'],
                    'floors': floors_list,
                    'total_locations': shelf_data['total_locations'],
                    'available_locations': shelf_data['available_locations']
                })
            
            zones_list.append({
                'zone_name': zone_name,
                'zone_id': zone_data['zone_id'],
                'shelves': shelves_list,
                'total_locations': zone_data['total_locations'],
                'available_locations': zone_data['available_locations']
            })
        
        return jsonify({
            'success': True,
            'data': {
                'storage_tree': zones_list,
                'summary': {
                    'total_zones': len(zones_list),
                    'total_locations': sum(zone['total_locations'] for zone in zones_list),
                    'available_locations': sum(zone['available_locations'] for zone in zones_list)
                }
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving storage tree: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'GET_STORAGE_TREE_ERROR',
                'message': 'Failed to retrieve storage hierarchy',
                'details': str(e)
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@storage_bp.route('/locations', methods=['GET'])
@jwt_required()
def list_storage_locations():
    """
    List storage locations with filtering
    Query Parameters:
    - zone: string (filter by zone)
    - shelf: string (filter by shelf)
    - floor: string (filter by floor)
    - available_only: boolean (show only available locations)
    - storage_type: string (filter by storage type)
    - page: int (default: 1)
    - page_size: int (default: 50)
    """
    try:
        # Get query parameters
        zone = request.args.get('zone')
        shelf = request.args.get('shelf')
        floor = request.args.get('floor')
        available_only = request.args.get('available_only', 'false').lower() == 'true'
        storage_type = request.args.get('storage_type')
        page = request.args.get('page', 1, type=int)
        page_size = min(request.args.get('page_size', 50, type=int), 100)
        
        # Build query
        query = db.session.query(Storage)
        
        # Apply filters
        if zone:
            query = query.filter(Storage.zone == zone)
        if shelf:
            query = query.filter(Storage.shelf == shelf)
        if floor:
            query = query.filter(Storage.floor == floor)
        if available_only:
            query = query.filter(Storage.is_available == True)
        if storage_type:
            query = query.filter(Storage.storage_type == storage_type)
        
        # Order by zone, shelf, floor, position
        query = query.order_by(Storage.zone, Storage.shelf, Storage.floor, Storage.position)
        
        # Paginate
        paginated_result = paginate_query(query, page, page_size)
        
        # Get current inventory for each location
        locations_data = []
        for storage in paginated_result['items']:
            # Get current items at this location
            current_items = db.session.query(StorageHistory)\
                           .filter(and_(
                               StorageHistory.storage_id == storage.id,
                               StorageHistory.movement_type == 'in'
                           ))\
                           .order_by(desc(StorageHistory.movement_date))\
                           .limit(5)\
                           .all()
            
            current_items_data = [
                {
                    'item_reference': item.item_reference,
                    'quantity': item.quantity,
                    'movement_date': item.movement_date.isoformat(),
                    'po_reference': item.po_reference
                }
                for item in current_items
            ]
            
            location_data = {
                'id': storage.id,
                'zone': storage.zone,
                'shelf': storage.shelf,
                'floor': storage.floor,
                'position': storage.position,
                'storage_type': storage.storage_type,
                'is_available': storage.is_available,
                'max_capacity': storage.max_capacity,
                'current_capacity': storage.current_capacity,
                'utilization_percent': round((storage.current_capacity / storage.max_capacity) * 100, 2) if storage.max_capacity > 0 else 0,
                'description': storage.description,
                'current_items': current_items_data,
                'created_at': storage.created_at.isoformat(),
                'updated_at': storage.updated_at.isoformat() if storage.updated_at else None
            }
            locations_data.append(location_data)
        
        return jsonify({
            'success': True,
            'data': locations_data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': paginated_result['total'],
                'has_more': paginated_result['has_more']
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing storage locations: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'LIST_STORAGE_ERROR',
                'message': 'Failed to retrieve storage locations',
                'details': str(e)
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@storage_bp.route('/putaway', methods=['GET'])
@jwt_required()
def get_putaway_candidates():
    """
    Get items that are ready for put-away (storage assignment)
    These are items that have been received but not yet assigned to storage
    """
    try:
        # Query items that are received but not stored
        putaway_candidates = db.session.query(PurchaseOrderItem)\
                           .join(PurchaseOrder, PurchaseOrderItem.po_id == PurchaseOrder.id)\
                           .join(Supplier, PurchaseOrder.supplier_id == Supplier.id)\
                           .filter(PurchaseOrderItem.receiving_status == 'received')\
                           .filter(PurchaseOrderItem.storage_status.in_(['pending', None]))\
                           .order_by(desc(PurchaseOrderItem.received_date))\
                           .all()
        
        candidates_data = []
        for item in putaway_candidates:
            # Check if item has storage history
            has_storage = db.session.query(StorageHistory)\
                         .filter(StorageHistory.item_reference == item.item_reference)\
                         .filter(StorageHistory.movement_type == 'in')\
                         .first()
            
            if not has_storage:  # Only include items not yet stored
                item_data = {
                    'id': item.id,
                    'po_id': item.po_id,
                    'po_no': item.purchase_order.po_no,
                    'item_reference': item.item_reference,
                    'item_name': item.item_name,
                    'item_spec': item.item_spec,
                    'quantity': item.quantity,
                    'received_quantity': item.received_quantity,
                    'unit': item.unit,
                    'supplier': {
                        'id': item.purchase_order.supplier.id,
                        'name': item.purchase_order.supplier.supplier_name_zh
                    },
                    'received_date': item.received_date.isoformat() if item.received_date else None,
                    'receiving_status': item.receiving_status,
                    'storage_status': item.storage_status,
                    'estimated_size': _estimate_storage_requirements(item),
                    'priority': _calculate_putaway_priority(item)
                }
                candidates_data.append(item_data)
        
        # Sort by priority (high to low)
        candidates_data.sort(key=lambda x: x['priority'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': {
                'items': candidates_data,
                'summary': {
                    'total_items': len(candidates_data),
                    'high_priority': len([item for item in candidates_data if item['priority'] >= 8]),
                    'medium_priority': len([item for item in candidates_data if 5 <= item['priority'] < 8]),
                    'low_priority': len([item for item in candidates_data if item['priority'] < 5])
                }
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving putaway candidates: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'GET_PUTAWAY_ERROR',
                'message': 'Failed to retrieve putaway candidates',
                'details': str(e)
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@storage_bp.route('/putaway/assign', methods=['POST'])
@jwt_required()
def assign_storage_location():
    """
    Assign a storage location to a received item
    Required fields: po_item_id, storage_id, quantity
    Optional fields: notes
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['po_item_id', 'storage_id', 'quantity']
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
        
        # Verify item is received
        if po_item.receiving_status != 'received':
            return jsonify({
                'success': False,
                'error': {
                    'code': 'ITEM_NOT_RECEIVED',
                    'message': 'Item must be received before storage assignment',
                    'details': {'receiving_status': po_item.receiving_status}
                },
                'timestamp': datetime.utcnow().isoformat()
            }), 422
        
        # Get storage location
        storage_location = Storage.query.get(data['storage_id'])
        if not storage_location:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'STORAGE_NOT_FOUND',
                    'message': 'Storage location not found',
                    'details': {'storage_id': data['storage_id']}
                },
                'timestamp': datetime.utcnow().isoformat()
            }), 404
        
        # Check storage availability and capacity
        if not storage_location.is_available:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'STORAGE_NOT_AVAILABLE',
                    'message': 'Storage location is not available',
                    'details': {'storage_id': data['storage_id']}
                },
                'timestamp': datetime.utcnow().isoformat()
            }), 422
        
        quantity = data['quantity']
        if storage_location.current_capacity + quantity > storage_location.max_capacity:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INSUFFICIENT_CAPACITY',
                    'message': 'Insufficient storage capacity',
                    'details': {
                        'available_capacity': storage_location.max_capacity - storage_location.current_capacity,
                        'requested_quantity': quantity
                    }
                },
                'timestamp': datetime.utcnow().isoformat()
            }), 422
        
        # Validate quantity doesn't exceed received quantity
        if quantity > po_item.received_quantity:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'QUANTITY_EXCEEDS_RECEIVED',
                    'message': 'Storage quantity cannot exceed received quantity',
                    'details': {
                        'received_quantity': po_item.received_quantity,
                        'requested_quantity': quantity
                    }
                },
                'timestamp': datetime.utcnow().isoformat()
            }), 422
        
        # Create storage history record
        storage_history = StorageHistory(
            item_reference=po_item.item_reference,
            storage_id=data['storage_id'],
            movement_type='in',
            quantity=quantity,
            movement_date=datetime.utcnow(),
            po_reference=po_item.purchase_order.po_no,
            user_id=get_jwt_identity(),
            notes=data.get('notes', ''),
            created_at=datetime.utcnow()
        )
        
        db.session.add(storage_history)
        
        # Update storage location capacity
        storage_location.current_capacity += quantity
        storage_location.updated_at = datetime.utcnow()
        
        # If capacity is full, mark as unavailable
        if storage_location.current_capacity >= storage_location.max_capacity:
            storage_location.is_available = False
        
        # Update PO item storage status
        po_item.storage_status = 'stored'
        po_item.storage_location_id = data['storage_id']
        po_item.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Invalidate cache
        invalidate_cache('storage:*')
        
        # Log the assignment
        logger.info(f"Storage assigned: Item {po_item.item_reference} to location {storage_location.id} by user {get_jwt_identity()}")
        
        return jsonify({
            'success': True,
            'data': {
                'storage_history_id': storage_history.id,
                'item_reference': po_item.item_reference,
                'storage_location': {
                    'id': storage_location.id,
                    'zone': storage_location.zone,
                    'shelf': storage_location.shelf,
                    'floor': storage_location.floor,
                    'position': storage_location.position
                },
                'quantity_stored': quantity,
                'movement_date': storage_history.movement_date.isoformat(),
                'remaining_capacity': storage_location.max_capacity - storage_location.current_capacity
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error assigning storage location: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'STORAGE_ASSIGNMENT_ERROR',
                'message': 'Failed to assign storage location',
                'details': str(e)
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@storage_bp.route('/admin/zones', methods=['POST'])
@jwt_required()
@require_roles(['Admin', 'ProcurementMgr'])
def create_storage_zone():
    """
    Create a new storage zone (Admin only)
    Required fields: zone_name, zone_type
    Optional fields: description, max_capacity
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('zone_name') or not data.get('zone_type'):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_REQUIRED_FIELDS',
                    'message': 'Zone name and type are required',
                    'details': {'required_fields': ['zone_name', 'zone_type']}
                },
                'timestamp': datetime.utcnow().isoformat()
            }), 422
        
        # Check for duplicate zone
        existing_zone = Storage.query.filter_by(
            zone=data['zone_name'],
            storage_type='zone'
        ).first()
        
        if existing_zone:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'DUPLICATE_ZONE',
                    'message': 'Zone already exists',
                    'details': {'zone_name': data['zone_name']}
                },
                'timestamp': datetime.utcnow().isoformat()
            }), 409
        
        # Create zone
        zone = Storage(
            zone=data['zone_name'],
            storage_type='zone',
            description=data.get('description', ''),
            max_capacity=data.get('max_capacity', 1000),
            current_capacity=0,
            is_available=True,
            created_at=datetime.utcnow()
        )
        
        db.session.add(zone)
        db.session.commit()
        
        # Invalidate cache
        invalidate_cache('storage:*')
        
        logger.info(f"Storage zone created: {data['zone_name']} by user {get_jwt_identity()}")
        
        return jsonify({
            'success': True,
            'data': {
                'id': zone.id,
                'zone_name': zone.zone,
                'zone_type': zone.storage_type,
                'description': zone.description,
                'max_capacity': zone.max_capacity,
                'created_at': zone.created_at.isoformat()
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating storage zone: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'CREATE_ZONE_ERROR',
                'message': 'Failed to create storage zone',
                'details': str(e)
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@storage_bp.route('/admin/shelves', methods=['POST'])
@jwt_required()
@require_roles(['Admin', 'ProcurementMgr'])
def create_storage_shelf():
    """
    Create a new storage shelf within a zone (Admin only)
    Required fields: zone, shelf_name, shelf_type
    Optional fields: description, max_capacity
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['zone', 'shelf_name', 'shelf_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'MISSING_REQUIRED_FIELD',
                        'message': f'Required field missing: {field}',
                        'details': {'field': field}
                    },
                    'timestamp': datetime.utcnow().isoformat()
                }), 422
        
        # Verify zone exists
        zone_exists = Storage.query.filter_by(
            zone=data['zone'],
            storage_type='zone'
        ).first()
        
        if not zone_exists:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'ZONE_NOT_FOUND',
                    'message': 'Specified zone does not exist',
                    'details': {'zone': data['zone']}
                },
                'timestamp': datetime.utcnow().isoformat()
            }), 404
        
        # Check for duplicate shelf in zone
        existing_shelf = Storage.query.filter_by(
            zone=data['zone'],
            shelf=data['shelf_name'],
            storage_type='shelf'
        ).first()
        
        if existing_shelf:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'DUPLICATE_SHELF',
                    'message': 'Shelf already exists in this zone',
                    'details': {'zone': data['zone'], 'shelf': data['shelf_name']}
                },
                'timestamp': datetime.utcnow().isoformat()
            }), 409
        
        # Create shelf
        shelf = Storage(
            zone=data['zone'],
            shelf=data['shelf_name'],
            storage_type='shelf',
            description=data.get('description', ''),
            max_capacity=data.get('max_capacity', 100),
            current_capacity=0,
            is_available=True,
            created_at=datetime.utcnow()
        )
        
        db.session.add(shelf)
        db.session.commit()
        
        # Invalidate cache
        invalidate_cache('storage:*')
        
        logger.info(f"Storage shelf created: {data['zone']}-{data['shelf_name']} by user {get_jwt_identity()}")
        
        return jsonify({
            'success': True,
            'data': {
                'id': shelf.id,
                'zone': shelf.zone,
                'shelf_name': shelf.shelf,
                'shelf_type': shelf.storage_type,
                'description': shelf.description,
                'max_capacity': shelf.max_capacity,
                'created_at': shelf.created_at.isoformat()
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating storage shelf: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'CREATE_SHELF_ERROR',
                'message': 'Failed to create storage shelf',
                'details': str(e)
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# Helper functions
def _estimate_storage_requirements(po_item):
    """Estimate storage space requirements based on item characteristics"""
    # Simple estimation logic - can be enhanced based on business rules
    base_size = po_item.quantity
    
    # Adjust based on item type/category
    if 'large' in po_item.item_name.lower() or 'big' in po_item.item_name.lower():
        return base_size * 2
    elif 'small' in po_item.item_name.lower() or 'mini' in po_item.item_name.lower():
        return base_size * 0.5
    
    return base_size

def _calculate_putaway_priority(po_item):
    """Calculate putaway priority based on various factors"""
    priority = 5  # Base priority
    
    # Higher priority for older items
    if po_item.received_date:
        days_since_received = (datetime.utcnow().date() - po_item.received_date.date()).days
        if days_since_received > 7:
            priority += 3
        elif days_since_received > 3:
            priority += 2
        elif days_since_received > 1:
            priority += 1
    
    # Higher priority for urgent items (based on item name keywords)
    urgent_keywords = ['urgent', 'critical', 'emergency', 'asap']
    if any(keyword in po_item.item_name.lower() for keyword in urgent_keywords):
        priority += 3
    
    # Higher priority for high-value items
    if hasattr(po_item, 'unit_price') and po_item.unit_price and po_item.unit_price > 1000:
        priority += 2
    
    return min(priority, 10)  # Cap at 10