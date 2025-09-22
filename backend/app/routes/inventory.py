from flask import Blueprint, request, jsonify
from app import db
from app.models.storage import Storage, StorageHistory
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from app.models.request_order import RequestOrderItem
from app.models.supplier import Supplier
from app.models.receiving import ReceivingRecord, PendingStorageItem
from app.models.user import User
from app.models.inventory import InventoryBatch, InventoryBatchStorage, InventoryMovement, InventoryItem
from app.auth import authenticated_required, create_response, create_error_response, paginate_query
from sqlalchemy import and_, or_, func
from datetime import datetime

bp = Blueprint('inventory', __name__, url_prefix='/api/v1')

# Storage Management Routes
@bp.route('/storage/tree', methods=['GET'])
@authenticated_required
def get_storage_tree(current_user):
    """Get storage hierarchy (Zone->Shelf->Floor structure)"""
    try:
        storages = Storage.query.filter_by(is_active=True).order_by(
            Storage.area_code, Storage.shelf_code, Storage.floor_level,
            Storage.front_back_position, Storage.left_middle_right_position
        ).all()
        
        # Build hierarchical structure
        tree = {}
        for storage in storages:
            area = storage.area_code
            shelf = storage.shelf_code
            floor = storage.floor_level
            
            if area not in tree:
                tree[area] = {
                    'area_code': area,
                    'shelves': {}
                }
            
            if shelf not in tree[area]['shelves']:
                tree[area]['shelves'][shelf] = {
                    'shelf_code': shelf,
                    'floors': {}
                }
            
            if floor not in tree[area]['shelves'][shelf]['floors']:
                tree[area]['shelves'][shelf]['floors'][floor] = {
                    'floor_level': floor,
                    'positions': []
                }
            
            tree[area]['shelves'][shelf]['floors'][floor]['positions'].append(storage.to_dict())
        
        # Convert to list format
        areas = []
        for area_code, area_data in tree.items():
            shelves = []
            for shelf_code, shelf_data in area_data['shelves'].items():
                floors = []
                for floor_level, floor_data in shelf_data['floors'].items():
                    floors.append(floor_data)
                shelf_data['floors'] = sorted(floors, key=lambda x: x['floor_level'])
                shelves.append(shelf_data)
            area_data['shelves'] = sorted(shelves, key=lambda x: x['shelf_code'])
            areas.append(area_data)
        
        return create_response(sorted(areas, key=lambda x: x['area_code']))
        
    except Exception as e:
        return create_error_response(
            'STORAGE_TREE_ERROR',
            'Failed to get storage tree',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/storage/admin/zones', methods=['POST'])
@authenticated_required
def create_zone(current_user):
    """Create storage zone with shelves and floors"""
    try:
        data = request.get_json()
        
        required_fields = ['area_code', 'shelves']
        for field in required_fields:
            if field not in data:
                return create_error_response(
                    'MISSING_FIELD',
                    f'{field} is required',
                    status_code=400
                )
        
        area_code = data['area_code']
        shelves_config = data['shelves']  # [{'shelf_code': 'A', 'floors': 6}, ...]
        
        created_storages = []
        
        for shelf_config in shelves_config:
            shelf_code = shelf_config['shelf_code']
            floors = shelf_config.get('floors', 6)
            
            for floor in range(1, floors + 1):
                for front_back in [1, 2]:  # Front, Back
                    for left_middle_right in [1, 2, 3]:  # Left, Middle, Right
                        storage = Storage.create_storage_location(
                            area_code, shelf_code, floor, front_back, left_middle_right
                        )
                        db.session.add(storage)
                        created_storages.append(storage)
        
        db.session.commit()
        
        return create_response([s.to_dict() for s in created_storages], status_code=201)
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'ZONE_CREATE_ERROR',
            'Failed to create storage zone',
            {'error': str(e)},
            status_code=500
        )

# Receiving Routes
@bp.route('/receiving/shipped-items', methods=['GET'])
@authenticated_required
def get_shipped_items(current_user):
    """Get items with status 'shipped' from delivery maintenance ready for receiving"""
    try:
        po_number = request.args.get('po_number')
        consolidation_number = request.args.get('consolidation_number')
        supplier_id = request.args.get('supplier_id')
        
        # Query items that are shipped but not yet received
        # Note: We'll use delivery_status as the main filter since receiving_status column doesn't exist yet
        query = db.session.query(PurchaseOrderItem, PurchaseOrder, Supplier)\
            .join(PurchaseOrder, PurchaseOrderItem.purchase_order_no == PurchaseOrder.purchase_order_no)\
            .join(Supplier, PurchaseOrder.supplier_id == Supplier.supplier_id)\
            .filter(PurchaseOrder.delivery_status == 'shipped')\
            .filter(PurchaseOrderItem.delivery_status != 'delivered')  # Filter out items that have been delivered
        
        # Apply filters based on request parameters
        if po_number:
            query = query.filter(PurchaseOrder.purchase_order_no.contains(po_number))
        
        if consolidation_number:
            query = query.filter(PurchaseOrder.consolidation_id.contains(consolidation_number))
        
        if supplier_id:
            query = query.filter(PurchaseOrder.supplier_id == supplier_id)
        
        results = query.all()
        
        shipped_items = []
        for item, po, supplier in results:
            # Create a requisition number - for items without source_request_order_no, 
            # we'll generate a placeholder or leave empty per requirements
            requisition_number = item.source_request_order_no or ""
            
            shipped_item = {
                'id': item.detail_id,
                'item_name': item.item_name,
                'requisition_number': requisition_number,
                'purchase_order_number': po.purchase_order_no,
                'consolidation_number': po.consolidation_id or "",
                'specification': item.item_specification or "",
                'quantity': float(item.item_quantity) if item.item_quantity else 0,
                'unit': item.item_unit or "",
                'supplier_name': supplier.supplier_name_zh,
                'supplier_region': supplier.supplier_region,
                'remarks': item.remarks or "",
                'shipped_date': po.shipped_at.isoformat() if po.shipped_at else "",
                'delivery_status': po.delivery_status
            }
            shipped_items.append(shipped_item)
        
        return create_response(shipped_items)
        
    except Exception as e:
        return create_error_response(
            'SHIPPED_ITEMS_ERROR',
            'Failed to get shipped items',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/receiving', methods=['GET'])
@authenticated_required
def list_receiving(current_user):
    """List items ready for receiving (legacy endpoint)"""
    try:
        region = request.args.get('region')  # domestic, international
        supplier_id = request.args.get('supplier_id')
        
        query = PurchaseOrder.query.filter(
            and_(
                PurchaseOrder.purchase_status == 'purchased',
                or_(
                    PurchaseOrder.shipping_status == 'expected_arrival',
                    PurchaseOrder.shipping_status == 'arrived'
                )
            )
        )
        
        if region:
            query = query.join(PurchaseOrder.supplier).filter(
                PurchaseOrder.supplier.has(supplier_region=region)
            )
        
        if supplier_id:
            query = query.filter(PurchaseOrder.supplier_id == supplier_id)
        
        pos = query.order_by(PurchaseOrder.eta_date).all()
        
        return create_response([po.to_dict() for po in pos])
        
    except Exception as e:
        return create_error_response(
            'RECEIVING_LIST_ERROR',
            'Failed to get receiving list',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/receiving/po/<po_no>', methods=['GET'])
@authenticated_required
def get_receiving_details(current_user, po_no):
    """Get receiving details for specific purchase order"""
    try:
        po = PurchaseOrder.query.get_or_404(po_no)
        
        if not po.is_ready_for_receiving():
            return create_error_response(
                'NOT_READY',
                'Purchase order is not ready for receiving',
                status_code=400
            )
        
        response_data = po.to_dict()
        response_data['items'] = [item.to_dict() for item in po.items.all()]
        
        return create_response(response_data)
        
    except Exception as e:
        return create_error_response(
            'RECEIVING_DETAILS_ERROR',
            'Failed to get receiving details',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/receiving/confirm', methods=['POST'])
@authenticated_required
def confirm_item_received_new(current_user):
    """Confirm item received with new workflow - records receiver and timestamp, creates inventory batch"""
    try:
        data = request.get_json()
        
        required_fields = ['item_id', 'requisition_number', 'purchase_order_number']
        for field in required_fields:
            if field not in data:
                return create_error_response(
                    'MISSING_FIELD',
                    f'{field} is required',
                    status_code=400
                )
        
        # Get additional data
        receiver_name = data.get('receiver') or current_user.chinese_name or current_user.username
        received_at = data.get('received_at')
        if received_at:
            received_at = datetime.fromisoformat(received_at.replace('Z', '+00:00'))
        else:
            received_at = datetime.utcnow()
        notes = data.get('notes', '')
        
        # Find the purchase order item using the item_id (detail_id) and PO number
        po_item = PurchaseOrderItem.query.filter_by(
            detail_id=data['item_id'],
            purchase_order_no=data['purchase_order_number']
        ).first()
        
        if not po_item:
            return create_error_response(
                'ITEM_NOT_FOUND',
                'Purchase order item not found',
                status_code=404
            )
        
        # Create receiving record first to maintain proper foreign key relationship
        from app.models.receiving import ReceivingRecord, PendingStorageItem

        # Create the receiving record
        receiving_record = ReceivingRecord(
            purchase_order_no=data['purchase_order_number'],
            po_item_detail_id=data['item_id'],
            requisition_number=data['requisition_number'],
            consolidation_number=data.get('consolidation_number'),
            item_name=data.get('item_name', po_item.item_name),
            item_specification=po_item.item_specification,
            quantity_shipped=data.get('quantity', po_item.item_quantity),
            quantity_received=data.get('quantity', po_item.item_quantity),
            unit=data.get('unit', po_item.item_unit),
            receiver_id=current_user.user_id,
            receiver_name=receiver_name,
            received_at=received_at,
            notes=notes,
            receiving_status='received'
        )
        db.session.add(receiving_record)
        db.session.flush()  # Get the receiving_id

        # Create pending storage item with proper foreign key reference
        pending_item = PendingStorageItem(
            receiving_record_id=receiving_record.receiving_id,
            item_name=data.get('item_name', po_item.item_name),
            item_specification=po_item.item_specification,
            quantity=data.get('quantity', po_item.item_quantity),
            unit=data.get('unit', po_item.item_unit),
            source_po_number=data['purchase_order_number'],
            requisition_number=data['requisition_number'],
            consolidation_number=data.get('consolidation_number'),
            arrival_date=received_at.date(),
            receiver=receiver_name,
            storage_status='pending'
        )
        db.session.add(pending_item)

        # Update the delivery status of the PO item to 'delivered'
        po_item.delivery_status = 'delivered'

        # Also update the Purchase Order's delivery status if all items are delivered
        po = PurchaseOrder.query.filter_by(purchase_order_no=data['purchase_order_number']).first()
        if po:
            # Check if all items in this PO are delivered
            all_items_delivered = all(
                item.delivery_status == 'delivered'
                for item in po.items
            )
            if all_items_delivered:
                po.delivery_status = 'delivered'
                po.actual_delivery_date = received_at

        db.session.commit()

        # Return a simple success response
        response_data = {
            'success': True,
            'message': 'Item received successfully',
            'item_id': data['item_id'],
            'item_name': data.get('item_name', po_item.item_name),
            'quantity': float(data.get('quantity', po_item.item_quantity)),
            'purchase_order_number': data['purchase_order_number'],
            'requisition_number': data['requisition_number'],
            'receiver': receiver_name,
            'received_at': received_at.isoformat()
        }

        return create_response(response_data)
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'CONFIRM_RECEIVED_ERROR',
            'Failed to confirm receipt',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/receiving/batch-confirm', methods=['POST'])
@authenticated_required
def batch_confirm_received(current_user):
    """Batch confirm multiple items received"""
    try:
        data = request.get_json()
        
        required_fields = ['items', 'receiver', 'received_at']
        for field in required_fields:
            if field not in data:
                return create_error_response(
                    'MISSING_FIELD',
                    f'{field} is required',
                    status_code=400
                )
        
        items = data['items']
        receiver_name = data.get('receiver', '')
        # If receiver_name is empty, use the current user's name
        if not receiver_name:
            receiver_name = current_user.chinese_name or current_user.username

        received_at = data['received_at']
        if received_at:
            received_at = datetime.fromisoformat(received_at.replace('Z', '+00:00'))
        else:
            received_at = datetime.utcnow()
        notes = data.get('notes', '')

        confirmed_items = []

        for item_data in items:
            # Find the purchase order item
            po_item = PurchaseOrderItem.query.filter_by(
                detail_id=item_data['item_id'],
                purchase_order_no=item_data['purchase_order_number']
            ).first()

            if not po_item:
                continue  # Skip items that can't be found

            # Create receiving record
            receiving_record = ReceivingRecord.create_receiving_record(
                po_no=item_data['purchase_order_number'],
                po_item_detail_id=item_data['item_id'],
                requisition_number=item_data.get('requisition_number', ''),  # Handle missing requisition_number
                item_name=po_item.item_name,
                quantity_received=po_item.item_quantity,
                unit=po_item.item_unit,
                receiver_id=current_user.user_id,
                receiver_name=receiver_name,  # Now guaranteed to have a value
                consolidation_number=item_data.get('consolidation_number'),
                notes=notes,
                item_specification=po_item.item_specification,
                received_at=received_at
            )
            
            db.session.add(receiving_record)
            db.session.flush()  # Get the receiving_id
            
            # Create pending storage item
            pending_item = PendingStorageItem.create_from_receiving_record(receiving_record)
            db.session.add(pending_item)
            
            # Update the delivery status of the PO item to 'delivered'
            po_item.delivery_status = 'delivered'

            # Update the corresponding request order item status to 'arrived'
            if po_item.source_request_order_no:
                req_item = RequestOrderItem.query.filter_by(
                    request_order_no=po_item.source_request_order_no,
                    item_name=po_item.item_name
                ).first()
                if req_item:
                    req_item.item_status = 'arrived'

            confirmed_items.append(receiving_record.to_dict())
        
        # After all items processed, check and update PO delivery statuses
        processed_pos = {}
        affected_projects = set()  # Track projects that need cost updates

        for item_data in items:
            po_no = item_data['purchase_order_number']
            if po_no not in processed_pos:
                po = PurchaseOrder.query.filter_by(purchase_order_no=po_no).first()
                if po:
                    # Check if all items in this PO are delivered
                    all_items_delivered = all(
                        item.delivery_status == 'delivered'
                        for item in po.items
                    )
                    if all_items_delivered:
                        po.delivery_status = 'delivered'
                        po.actual_delivery_date = received_at

                    # Track affected projects for cost update
                    from app.models.request_order import RequestOrder
                    for item in po.items:
                        if item.source_request_order_no:
                            request_order = RequestOrder.query.filter_by(
                                request_order_no=item.source_request_order_no
                            ).first()
                            if request_order and request_order.project_id:
                                affected_projects.add(request_order.project_id)

                    processed_pos[po_no] = po

        # Update project costs for all affected projects
        from app.models.project import Project
        for project_id in affected_projects:
            project = Project.query.get(project_id)
            if project:
                # Recalculate total expenditure from all related purchase orders
                from app.models.request_order import RequestOrder

                # Get all unique supplier expenditures for this project
                supplier_costs = db.session.query(
                    PurchaseOrder.supplier_id,
                    db.func.sum(PurchaseOrderItem.unit_price * PurchaseOrderItem.item_quantity).label('total')
                ).join(
                    PurchaseOrderItem, PurchaseOrderItem.purchase_order_no == PurchaseOrder.purchase_order_no
                ).join(
                    RequestOrder, PurchaseOrderItem.source_request_order_no == RequestOrder.request_order_no
                ).filter(
                    RequestOrder.project_id == project_id,
                    PurchaseOrder.purchase_status == 'purchased'
                ).group_by(PurchaseOrder.supplier_id).all()

                # Update or create supplier expenditure records
                from app.models.project import ProjectSupplierExpenditure
                for supplier_id, total_amount in supplier_costs:
                    expenditure = ProjectSupplierExpenditure.query.filter_by(
                        project_id=project_id,
                        supplier_id=supplier_id
                    ).first()

                    if expenditure:
                        expenditure.expenditure_amount = total_amount or 0
                    else:
                        expenditure = ProjectSupplierExpenditure(
                            project_id=project_id,
                            supplier_id=supplier_id,
                            expenditure_amount=total_amount or 0
                        )
                        db.session.add(expenditure)

                # Update project total expenditure
                project.calculate_total_expenditure()

        db.session.commit()
        
        return create_response({
            'confirmed_count': len(confirmed_items),
            'items': confirmed_items
        })
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'BATCH_CONFIRM_ERROR',
            'Failed to batch confirm receipt',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/receiving/po/<po_no>/items/<int:detail_id>/confirm', methods=['POST'])
@authenticated_required
def confirm_item_received(current_user, po_no, detail_id):
    """Confirm item receipt (legacy endpoint)"""
    try:
        po = PurchaseOrder.query.get_or_404(po_no)
        po_item = next((item for item in po.items if item.detail_id == detail_id), None)
        
        if not po_item:
            return create_error_response(
                'ITEM_NOT_FOUND',
                'Purchase order item not found',
                status_code=404
            )
        
        if po_item.line_status == 'arrived':
            return create_response(po_item.to_dict())  # Already received
        
        # Mark item as arrived
        po_item.mark_arrived()
        
        # Update source requisition item if exists
        if po_item.source_request_item:
            po_item.source_request_item.item_status = 'arrived'
        
        # Check if all items are arrived, update PO status
        all_arrived = all(item.line_status == 'arrived' for item in po.items)
        if all_arrived:
            po.shipping_status = 'arrived'
        
        db.session.commit()
        
        return create_response(po_item.to_dict())
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'CONFIRM_RECEIVED_ERROR',
            'Failed to confirm receipt',
            {'error': str(e)},
            status_code=500
        )

# Putaway Routes
@bp.route('/putaway/pending', methods=['GET'])
@authenticated_required
def list_pending_storage(current_user):
    """List items that have been received and are pending storage assignment"""
    try:
        # Query pending storage items from the database (only pending status)
        pending_items = PendingStorageItem.query.filter_by(
            storage_status='pending'
        ).order_by(PendingStorageItem.arrival_date.desc()).all()
        
        # Convert to format expected by frontend (matching the expected interface)
        items_data = []
        for item in pending_items:
            item_data = {
                'id': item.pending_id,
                'item_name': item.item_name,
                'quantity': float(item.quantity),
                'unit': item.unit,
                'source_po_number': item.source_po_number,
                'arrival_date': item.arrival_date.isoformat() if item.arrival_date else None,
                'receiver': item.receiver,
                'requisition_number': item.requisition_number,
                'consolidation_number': item.consolidation_number,
                'specification': item.item_specification or ''
            }
            items_data.append(item_data)
        
        return create_response(items_data)
        
    except Exception as e:
        return create_error_response(
            'PENDING_STORAGE_ERROR',
            'Failed to get pending storage items',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/putaway', methods=['GET'])
@authenticated_required
def list_putaway(current_user):
    """List items ready for storage assignment (legacy endpoint)"""
    try:
        status_filter = request.args.get('status', 'arrived')
        
        if status_filter == 'arrived':
            # Get PO items that are arrived but not warehoused
            po_items = db.session.query(PurchaseOrder, PurchaseOrder.items).filter(
                PurchaseOrder.items.any(line_status='arrived')
            ).all()
            
            items = []
            for po, po_item in po_items:
                if po_item.line_status == 'arrived':
                    item_data = po_item.to_dict()
                    item_data['po'] = po.to_dict()
                    items.append(item_data)
            
            return create_response(items)
        
        return create_response([])
        
    except Exception as e:
        return create_error_response(
            'PUTAWAY_LIST_ERROR',
            'Failed to get putaway list',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/putaway/assign', methods=['POST'])
@authenticated_required
def assign_storage_location(current_user):
    """Assign storage location to received item and complete putaway process with batch tracking"""
    try:
        data = request.get_json()
        
        required_fields = ['item_ref', 'area', 'shelf', 'floor']
        for field in required_fields:
            if field not in data:
                return create_error_response(
                    'MISSING_FIELD',
                    f'{field} is required',
                    status_code=400
                )
        
        item_ref = data['item_ref']
        item_id = item_ref.get('id')
        
        # Find and update the pending storage item
        pending_item = PendingStorageItem.query.filter_by(
            pending_id=item_id,
            storage_status='pending'
        ).first()
        
        if pending_item:
            # Create or get storage location
            storage = Storage.create_storage_location(
                data['area'],
                data['shelf'],
                data['floor'],
                1,  # Default front_back position
                1   # Default left_middle_right position
            )
            db.session.add(storage)
            db.session.flush()
            
            # Create inventory batch for proper tracking
            from app.models.inventory import InventoryBatch, InventoryBatchStorage

            # Create or find inventory batch
            inventory_batch = InventoryBatch(
                item_name=pending_item.item_name,
                item_specification=pending_item.item_specification,
                unit=pending_item.unit,
                source_type='RECEIVED',  # Changed from batch_type to source_type
                source_po_number=pending_item.source_po_number,
                source_line_number=pending_item.pending_id,
                original_quantity=float(pending_item.quantity),  # Changed from initial_quantity
                current_quantity=float(pending_item.quantity),
                batch_status='active',
                received_date=pending_item.arrival_date,
                receiver_id=current_user.user_id,
                receiver_name=pending_item.receiver,
                created_at=datetime.utcnow()
            )
            db.session.add(inventory_batch)
            db.session.flush()  # Get the batch_id

            # Create batch storage allocation
            batch_storage = InventoryBatchStorage(
                batch_id=inventory_batch.batch_id,
                storage_id=storage.storage_id,
                quantity=float(pending_item.quantity)
            )
            db.session.add(batch_storage)

            # Assign storage and mark as stored
            pending_item.assign_storage(storage.storage_id)
            pending_item.mark_as_stored()

            # Create legacy storage history record for backward compatibility
            history = StorageHistory.create_in_record(
                storage_id=storage.storage_id,
                item_id=pending_item.item_name,
                quantity=float(pending_item.quantity),
                operator_id=current_user.user_id,
                source_type='RECEIVED',
                source_no=pending_item.source_po_number,
                source_line=pending_item.pending_id,
                note=f'收貨入庫 - 收貨人: {pending_item.receiver} - {pending_item.arrival_date}'
            )
            db.session.add(history)
            
        else:
            # Fall back to original implementation for backward compatibility
            storage = Storage.create_storage_location(
                data['area'], data['shelf'], data['floor'],
                1, 1  # Default front_back and left_middle_right positions
            )
            db.session.add(storage)
            db.session.flush()
            
            # Create storage history record (IN) with receiver information
            history = StorageHistory.create_in_record(
                storage_id=storage.storage_id,
                item_id=item_ref.get('item_name', 'Unknown Item'),
                quantity=item_ref.get('quantity', 1),
                operator_id=current_user.user_id,
                source_type='RECEIVED',
                source_no=item_ref.get('po_no', ''),
                source_line=item_ref.get('id', 0),
                note=f'收貨入庫 - 收貨人: {item_ref.get("receiver", "Unknown")} - {item_ref.get("arrival_date", "")}'
            )
            db.session.add(history)
        
        db.session.commit()
        
        # Return response with batch_id if created
        return create_response({
            'storage': storage.to_dict(),
            'history': history.to_dict(),
            'batch_id': inventory_batch.batch_id if pending_item else None,
            'message': 'Item successfully assigned to storage location'
        })
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'ASSIGN_STORAGE_ERROR',
            'Failed to assign storage location',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/storage/manual-entry', methods=['POST'])
@authenticated_required
def create_manual_inventory_entry(current_user):
    """Create manual inventory entry (direct to storage without receiving process)"""
    try:
        data = request.get_json()
        
        required_fields = ['item_name', 'specification', 'quantity', 'unit', 'storage_location']
        for field in required_fields:
            if field not in data:
                return create_error_response(
                    'MISSING_FIELD',
                    f'{field} is required',
                    status_code=400
                )
        
        storage_location = data['storage_location']
        
        # Create or get storage location
        storage = Storage.create_storage_location(
            storage_location['area'],
            storage_location['shelf'],
            storage_location['floor'],
            1, 1  # Default positions
        )
        db.session.add(storage)
        db.session.flush()
        
        # Create storage history record for manual entry
        history = StorageHistory.create_in_record(
            storage_id=storage.storage_id,
            item_id=data['item_name'],
            quantity=data['quantity'],
            operator_id=current_user.user_id,
            source_type='MANUAL',
            source_no='MANUAL_ENTRY',
            source_line=0,
            note=f'手動入庫 - {data.get("remarks", "")} - 規格: {data["specification"]}'
        )
        db.session.add(history)
        
        db.session.commit()
        
        return create_response({
            'storage': storage.to_dict(),
            'history': history.to_dict(),
            'message': 'Manual inventory entry created successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'MANUAL_ENTRY_ERROR',
            'Failed to create manual inventory entry',
            {'error': str(e)},
            status_code=500
        )

# Inventory Query and Issue Routes
@bp.route('/inventory', methods=['GET'])
@authenticated_required
def search_inventory(current_user):
    """Query inventory with multiple filters"""
    try:
        # Get filter parameters
        name_like = request.args.get('name')
        spec_like = request.args.get('spec')
        request_no = request.args.get('request_no')
        po_no = request.args.get('po_no')
        usage_type = request.args.get('usage_type')
        zone = request.args.get('zone')
        shelf = request.args.get('shelf')
        floor = request.args.get('floor')
        
        # Build inventory query with current quantities
        query = db.session.query(
            StorageHistory.storage_id,
            StorageHistory.item_id,
            StorageHistory.source_no,
            StorageHistory.source_line,
            db.func.sum(
                db.case(
                    (StorageHistory.operation_type == 'in', StorageHistory.quantity),
                    else_=-StorageHistory.quantity
                )
            ).label('current_quantity')
        ).group_by(
            StorageHistory.storage_id,
            StorageHistory.item_id,
            StorageHistory.source_no,
            StorageHistory.source_line
        ).having(
            db.func.sum(
                db.case(
                    (StorageHistory.operation_type == 'in', StorageHistory.quantity),
                    else_=-StorageHistory.quantity
                )
            ) > 0
        )
        
        # Join with storage for location filtering
        query = query.join(Storage)
        
        if zone:
            query = query.filter(Storage.area_code == zone)
        if shelf:
            query = query.filter(Storage.shelf_code == shelf)
        if floor:
            query = query.filter(Storage.floor_level == int(floor))
        
        if name_like:
            query = query.filter(StorageHistory.item_id.ilike(f'%{name_like}%'))
        if po_no:
            query = query.filter(StorageHistory.source_no == po_no)
        
        results = query.all()
        
        inventory_items = []
        for result in results:
            storage = Storage.query.get(result.storage_id)
            inventory_items.append({
                'storage_id': result.storage_id,
                'storage': storage.to_dict() if storage else None,
                'item_id': result.item_id,
                'source_no': result.source_no,
                'source_line': result.source_line,
                'current_quantity': float(result.current_quantity)
            })
        
        return create_response(inventory_items)
        
    except Exception as e:
        return create_error_response(
            'INVENTORY_SEARCH_ERROR',
            'Failed to search inventory',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/inventory/issue', methods=['POST'])
@authenticated_required
def issue_inventory(current_user):
    """Issue inventory item"""
    try:
        data = request.get_json()
        
        required_fields = ['item_ref', 'storage_id', 'qty']
        for field in required_fields:
            if field not in data:
                return create_error_response(
                    'MISSING_FIELD',
                    f'{field} is required',
                    status_code=400
                )
        
        item_ref = data['item_ref']
        storage_id = data['storage_id']
        qty = float(data['qty'])
        
        if qty <= 0:
            return create_error_response(
                'INVALID_QUANTITY',
                'Quantity must be positive',
                status_code=400
            )
        
        # Create storage history record (OUT)
        history = StorageHistory.create_out_record(
            storage_id=storage_id,
            item_id=item_ref.get('item_id') or 'Unknown',
            quantity=qty,
            operator_id=current_user.user_id,
            source_type='ISSUE',
            source_no=item_ref.get('po_no'),
            source_line=item_ref.get('detail_id'),
            note=f'領用 - {current_user.chinese_name}'
        )
        
        db.session.add(history)
        
        # Update source requisition item status to issued if this depletes inventory
        if item_ref.get('po_no') and item_ref.get('detail_id'):
            remaining = StorageHistory.get_current_quantity(
                storage_id, 
                item_ref.get('item_id', 'Unknown'),
                item_ref.get('po_no'),
                item_ref.get('detail_id')
            )
            
            if remaining <= 0:
                # Find related requisition item and mark as issued
                po_item = PurchaseOrderItem.query.filter_by(
                    purchase_order_no=item_ref['po_no'],
                    detail_id=item_ref['detail_id']
                ).first()
                
                if po_item and po_item.source_request_item:
                    po_item.source_request_item.item_status = 'issued'
        
        db.session.commit()
        
        return create_response(history.to_dict())
        
    except ValueError as e:
        return create_error_response(
            'INSUFFICIENT_INVENTORY',
            str(e),
            status_code=400
        )
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'ISSUE_INVENTORY_ERROR',
            'Failed to issue inventory',
            {'error': str(e)},
            status_code=500
        )

# Acceptance Routes
@bp.route('/acceptance/mine', methods=['GET'])
@authenticated_required
def get_my_acceptance(current_user):
    """Get acceptance items for current user (both pending and accepted)"""
    try:
        # Get status filter parameter
        status_filter = request.args.get('status', '')
        
        # Base query - get user's items that need acceptance
        base_query = RequestOrderItem.query.filter(
            and_(
                RequestOrderItem.request_order.has(requester_id=current_user.user_id),
                RequestOrderItem.needs_acceptance == True
            )
        )
        
        # Apply status filtering - support both Chinese and English status values
        if status_filter in ['已驗收', 'accepted']:
            # Show accepted items
            items = base_query.filter(
                RequestOrderItem.acceptance_status == 'accepted'
            ).all()
        elif status_filter in ['已拒絕', 'rejected']:
            # Show rejected items
            items = base_query.filter(
                RequestOrderItem.acceptance_status == 'rejected'
            ).all()
        elif status_filter in ['待驗收', 'pending']:
            # Show pending acceptance items (must be delivered/stored or reviewed with PO created)
            items = base_query.filter(
                and_(
                    RequestOrderItem.item_status.in_(['arrived', 'warehoused', 'delivered', 'received', 'reviewed']),
                    or_(
                        RequestOrderItem.acceptance_status == 'pending_acceptance',
                        RequestOrderItem.acceptance_status.is_(None)
                    )
                )
            ).all()
        elif status_filter == '已到貨':
            # Show items that have arrived but not accepted (legacy support)
            items = base_query.filter(
                and_(
                    RequestOrderItem.item_status == 'arrived',
                    RequestOrderItem.acceptance_status != 'accepted'
                )
            ).all()
        elif status_filter == '已入庫':
            # Show items that are warehoused but not accepted (legacy support)
            items = base_query.filter(
                and_(
                    RequestOrderItem.item_status == 'warehoused',
                    RequestOrderItem.acceptance_status != 'accepted'
                )
            ).all()
        else:
            # Default: show only items that have been delivered/stored or reviewed and need acceptance
            items = base_query.filter(
                and_(
                    RequestOrderItem.item_status.in_(['arrived', 'warehoused', 'delivered', 'received', 'reviewed']),
                    or_(
                        RequestOrderItem.acceptance_status == 'pending_acceptance',
                        RequestOrderItem.acceptance_status.is_(None)
                    )
                )
            ).all()
        
        return create_response([item.to_dict() for item in items])
        
    except Exception as e:
        return create_error_response(
            'ACCEPTANCE_LIST_ERROR',
            'Failed to get acceptance list',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/acceptance/confirm', methods=['POST'])
@authenticated_required
def confirm_acceptance(current_user):
    """Confirm acceptance of received item"""
    try:
        data = request.get_json()
        
        required_fields = ['item_ref']
        for field in required_fields:
            if field not in data:
                return create_error_response(
                    'MISSING_FIELD',
                    f'{field} is required',
                    status_code=400
                )
        
        item_ref = data['item_ref']
        detail_id = item_ref.get('detail_id')
        
        if not detail_id:
            return create_error_response(
                'MISSING_DETAIL_ID',
                'detail_id is required in item_ref',
                status_code=400
            )
        
        item = RequestOrderItem.query.get_or_404(detail_id)
        
        # Only requester can accept their own items
        if item.request_order.requester_id != current_user.user_id:
            return create_error_response(
                'INSUFFICIENT_PERMISSIONS',
                'Can only accept own requisition items',
                status_code=403
            )
        
        if item.acceptance_status == 'accepted':
            return create_response(item.to_dict())  # Already accepted

        # Update acceptance status
        item.acceptance_status = 'accepted'

        # Also update item_status to reflect acceptance completion
        # Only update if the item was in 'arrived' or 'warehoused' status
        if item.item_status in ['arrived', 'warehoused']:
            item.item_status = 'received'  # Mark as received after acceptance

        item.updated_at = datetime.utcnow()

        db.session.commit()
        
        return create_response(item.to_dict())
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'CONFIRM_ACCEPTANCE_ERROR',
            'Failed to confirm acceptance',
            {'error': str(e)},
            status_code=500
        )

# New Inventory Management Routes (Phase 1: Basic details page, batch display, simple history)
@bp.route('/inventory/items', methods=['GET'])
@authenticated_required
def get_inventory_items_grouped(current_user):
    """Get inventory items grouped by name and specification with batch counts"""
    try:
        # Get query parameters for filtering
        name_filter = request.args.get('name')
        spec_filter = request.args.get('spec')
        zone_filter = request.args.get('zone')
        
        # Build base query for inventory summary
        # Use SQLite compatible concatenation (|| operator instead of concat function)
        # Note: MAX() is used for usage_type to get the most common/latest one for grouped items
        query = db.session.query(
            (InventoryBatch.item_name + '|' + func.coalesce(InventoryBatch.item_specification, '')).label('item_key'),
            InventoryBatch.item_name,
            InventoryBatch.item_specification,
            InventoryBatch.unit,
            func.sum(InventoryBatch.current_quantity).label('total_quantity'),
            func.count(InventoryBatch.batch_id).label('batch_count'),
            func.count(func.distinct(InventoryBatchStorage.storage_id)).label('storage_location_count'),
            func.max(InventoryBatch.created_at).label('last_received_date')
        ).outerjoin(InventoryBatchStorage).filter(
            InventoryBatch.current_quantity > 0
        )
        
        # Apply filters
        if name_filter:
            query = query.filter(InventoryBatch.item_name.ilike(f'%{name_filter}%'))
        if spec_filter:
            query = query.filter(InventoryBatch.item_specification.ilike(f'%{spec_filter}%'))
        if zone_filter:
            query = query.join(Storage, Storage.storage_id == InventoryBatchStorage.storage_id)
            query = query.filter(Storage.area_code == zone_filter)
        
        # Group by item and specification
        query = query.group_by(
            InventoryBatch.item_name,
            InventoryBatch.item_specification,
            InventoryBatch.unit
        )
        
        results = query.all()
        
        # Format results
        inventory_items = []
        for result in results:
            # Get usage_type directly from database to avoid ORM caching issues
            import sqlite3
            conn = sqlite3.connect('erp_development.db')
            cursor = conn.cursor()
            cursor.execute(
                "SELECT usage_type FROM inventory_batches WHERE item_name = ? AND item_specification = ? LIMIT 1",
                (result.item_name, result.item_specification)
            )
            usage_result = cursor.fetchone()
            conn.close()
            usage_type = usage_result[0] if usage_result and usage_result[0] else 'general'
            
            item_data = {
                'item_key': result.item_key,
                'item_name': result.item_name,
                'item_specification': result.item_specification,
                'unit': result.unit,
                'usage_type': usage_type,
                'total_quantity': float(result.total_quantity) if result.total_quantity else 0,
                'batch_count': result.batch_count or 0,
                'storage_location_count': result.storage_location_count or 0,
                'last_received_date': str(result.last_received_date) if result.last_received_date else None
            }
            inventory_items.append(item_data)
        
        return create_response(inventory_items)
        
    except Exception as e:
        return create_error_response(
            'INVENTORY_ITEMS_ERROR',
            'Failed to get inventory items',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/inventory/items/<path:item_key>/details', methods=['GET', 'OPTIONS'])
@authenticated_required
def get_inventory_item_details(current_user, item_key):
    """Get detailed information for a specific inventory item including batches"""
    try:
        # Parse item_key (format: "item_name|item_specification")
        if '|' in item_key:
            item_name, item_spec = item_key.split('|', 1)
            item_spec = item_spec if item_spec else None
        else:
            item_name = item_key
            item_spec = None

        # First try to get from inventory_items table (new PostgreSQL structure)
        from app.models.inventory import InventoryItem

        base_query = InventoryItem.query.filter(
            InventoryItem.item_name == item_name
        )

        if item_spec:
            base_query = base_query.filter(InventoryItem.item_specification == item_spec)

        inventory_items = base_query.all()

        if inventory_items:
            # Use inventory_items table data
            item = inventory_items[0]  # Take the first match

            # Get quantity from both possible columns
            total_quantity = 0
            if hasattr(item, 'item_quantity') and item.item_quantity:
                total_quantity += float(item.item_quantity)
            if hasattr(item, 'quantity') and item.quantity:
                total_quantity += float(item.quantity)

            # Mock batch and storage data for compatibility
            return jsonify({
                'item_name': item.item_name,
                'item_specification': item.item_specification or '',
                'item_unit': getattr(item, 'item_unit', None) or getattr(item, 'unit', ''),
                'total_quantity': total_quantity,
                'batch_count': 1,
                'storage_count': 1 if total_quantity > 0 else 0,
                'recent_received_date': getattr(item, 'updated_at', None),
                'batches': [{
                    'batch_id': 1,
                    'batch_number': 'BATCH-001',
                    'current_quantity': total_quantity,
                    'received_date': getattr(item, 'created_at', None),
                    'expiry_date': None,
                    'status': 'available'
                }] if total_quantity > 0 else [],
                'storage_distribution': [{
                    'storage_id': 1,
                    'area_code': 'A',
                    'shelf_code': '001',
                    'floor_level': 1,
                    'quantity': total_quantity
                }] if total_quantity > 0 else [],
                'history': []
            }), 200

        # Fallback to original InventoryBatch logic
        base_query = InventoryBatch.query.filter(
            InventoryBatch.item_name == item_name,
            InventoryBatch.current_quantity > 0
        )

        if item_spec:
            base_query = base_query.filter(InventoryBatch.item_specification == item_spec)
        else:
            base_query = base_query.filter(InventoryBatch.item_specification.is_(None))

        batches = base_query.all()

        if not batches:
            return create_error_response(
                'ITEM_NOT_FOUND',
                'Inventory item not found',
                status_code=404
            )
        
        # Calculate totals
        total_quantity = sum(float(batch.current_quantity) for batch in batches)
        batch_count = len(batches)
        
        # Get storage distribution
        storage_query = db.session.query(
            Storage.storage_id,
            Storage.area_code,
            Storage.shelf_code,
            Storage.floor_level,
            func.sum(InventoryBatchStorage.quantity).label('total_quantity')
        ).join(InventoryBatchStorage).join(InventoryBatch).filter(
            InventoryBatch.item_name == item_name,
            InventoryBatch.current_quantity > 0
        )
        
        if item_spec:
            storage_query = storage_query.filter(InventoryBatch.item_specification == item_spec)
        else:
            storage_query = storage_query.filter(InventoryBatch.item_specification.is_(None))
        
        storage_distribution = storage_query.group_by(
            Storage.storage_id,
            Storage.area_code,
            Storage.shelf_code,
            Storage.floor_level
        ).all()
        
        # Prepare response
        item_details = {
            'item_key': item_key,
            'item_name': item_name,
            'item_specification': item_spec,
            'unit': batches[0].unit if batches else None,
            'total_quantity': total_quantity,
            'batch_count': batch_count,
            'batches': [batch.to_dict() for batch in batches],
            'storage_distribution': [{
                'storage_id': dist.storage_id,
                'area_code': dist.area_code,
                'shelf_code': dist.shelf_code,
                'floor_level': dist.floor_level,
                'quantity': float(dist.total_quantity)
            } for dist in storage_distribution]
        }
        
        return create_response(item_details)
        
    except Exception as e:
        return create_error_response(
            'ITEM_DETAILS_ERROR',
            'Failed to get item details',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/inventory/items/<path:item_key>/history', methods=['GET'])
@authenticated_required
def get_inventory_item_history(current_user, item_key):
    """Get movement history for a specific inventory item"""
    try:
        # Parse item_key
        if '|' in item_key:
            item_name, item_spec = item_key.split('|', 1)
            item_spec = item_spec if item_spec else None
        else:
            item_name = item_key
            item_spec = None
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Build query for movement history
        history_query = db.session.query(InventoryMovement).join(
            InventoryBatch
        ).filter(
            InventoryBatch.item_name == item_name
        )
        
        if item_spec:
            history_query = history_query.filter(InventoryBatch.item_specification == item_spec)
        else:
            history_query = history_query.filter(InventoryBatch.item_specification.is_(None))
        
        # Order by movement date (most recent first)
        history_query = history_query.order_by(InventoryMovement.movement_date.desc())
        
        # Apply pagination
        pagination = history_query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Format movements
        movements = [movement.to_dict() for movement in pagination.items]
        
        return create_response({
            'movements': movements,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next
            }
        })
        
    except Exception as e:
        return create_error_response(
            'ITEM_HISTORY_ERROR',
            'Failed to get item history',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/inventory/batches/<int:batch_id>/details', methods=['GET'])
@authenticated_required
def get_batch_details(current_user, batch_id):
    """Get detailed information for a specific inventory batch"""
    try:
        batch = InventoryBatch.query.get_or_404(batch_id)
        
        # Get storage distribution for this batch
        storage_allocations = InventoryBatchStorage.query.filter_by(
            batch_id=batch_id
        ).all()
        
        # Get movement history for this batch
        movements = InventoryMovement.query.filter_by(
            batch_id=batch_id
        ).order_by(InventoryMovement.movement_date.desc()).limit(10).all()
        
        batch_details = batch.to_dict()
        batch_details['storage_allocations'] = [alloc.to_dict() for alloc in storage_allocations]
        batch_details['recent_movements'] = [movement.to_dict() for movement in movements]
        
        return create_response(batch_details)
        
    except Exception as e:
        return create_error_response(
            'BATCH_DETAILS_ERROR',
            'Failed to get batch details',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/inventory/batches/<int:batch_id>/history', methods=['GET'])
@authenticated_required
def get_batch_history(current_user, batch_id):
    """Get complete movement history for a specific inventory batch"""
    try:
        batch = InventoryBatch.query.get_or_404(batch_id)
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Query movements for this batch
        movements_query = InventoryMovement.query.filter_by(
            batch_id=batch_id
        ).order_by(InventoryMovement.movement_date.desc())
        
        # Apply pagination
        pagination = movements_query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Format movements
        movements = [movement.to_dict() for movement in pagination.items]
        
        return create_response({
            'batch_id': batch_id,
            'batch_info': batch.to_dict(),
            'movements': movements,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next
            }
        })
        
    except Exception as e:
        return create_error_response(
            'BATCH_HISTORY_ERROR',
            'Failed to get batch history',
            {'error': str(e)},
            status_code=500
        )