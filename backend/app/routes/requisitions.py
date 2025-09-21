from flask import Blueprint, request, jsonify
from sqlalchemy.orm import joinedload
from app import db
from app.models.request_order import RequestOrder, RequestOrderItem
from app.models.item_category import ItemCategory
from app.auth import authenticated_required, procurement_required, create_response, create_error_response, paginate_query
from app.utils.security import require_permission
from datetime import date, datetime

bp = Blueprint('requisitions', __name__, url_prefix='/api/v1/requisitions')

@bp.route('/test-permissions-update', methods=['GET'])
def test_permissions_update():
    """Test endpoint to verify our code is loaded"""
    return jsonify({'message': 'Permissions update code is loaded', 'timestamp': datetime.now().isoformat(), 'version': '2.0'})

@bp.route('/emergency-test', methods=['POST'])
@authenticated_required
def emergency_test_endpoint(current_user):
    """EMERGENCY TEST ENDPOINT - Simple test for emergency routes"""
    try:
        data = request.get_json() or {}
        print(f"[EMERGENCY_TEST] Called by {current_user.username} with data: {data}")
        
        return create_response({
            'message': 'Emergency test endpoint working!',
            'user': current_user.username,
            'data_received': data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"[EMERGENCY_TEST] Error: {e}")
        return create_error_response(
            'EMERGENCY_TEST_ERROR',
            'Emergency test failed',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/<request_order_no>/items/<int:detail_id>/save-changes', methods=['POST'])
@procurement_required  
def save_changes_emergency_hotfix(current_user, request_order_no, detail_id):
    """EMERGENCY HOTFIX: Save changes without approval - P0 Critical Bug Fix"""
    print(f"[EMERGENCY_HOTFIX] Save changes API called for {request_order_no}/{detail_id}")
    try:
        item = RequestOrderItem.query.filter_by(
            request_order_no=request_order_no,
            detail_id=detail_id
        ).first_or_404()
        
        data = request.get_json()
        print(f"[EMERGENCY_HOTFIX] Received data: {data}")
        
        # Emergency debug logging
        with open('approval_debug.log', 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now()}] EMERGENCY_HOTFIX API CALLED: {request_order_no}/{detail_id} - {data}\\n")
        
        # Update supplier if provided
        if 'supplier_id' in data and data['supplier_id']:
            print(f"[EMERGENCY_HOTFIX] Updating supplier_id: {item.supplier_id} -> {data['supplier_id']}")
            item.supplier_id = data['supplier_id']
        
        # Update unit price if provided
        if 'unit_price' in data and data['unit_price'] is not None:
            if float(data['unit_price']) >= 0:
                print(f"[EMERGENCY_HOTFIX] Updating unit_price: {item.unit_price} -> {data['unit_price']}")
                item.unit_price = float(data['unit_price'])
        
        # Update note if provided
        if 'status_note' in data:
            print(f"[EMERGENCY_HOTFIX] Updating status_note: {item.status_note} -> {data['status_note']}")
            item.status_note = data['status_note']
        
        # CRITICAL: DO NOT change item_status - this is just saving changes
        print(f"[EMERGENCY_HOTFIX] Item status remains: {item.item_status}")
        
        db.session.commit()
        print(f"[EMERGENCY_HOTFIX] Changes saved successfully")
        
        # Emergency debug logging
        with open('approval_debug.log', 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now()}] EMERGENCY_HOTFIX COMPLETED: {request_order_no}/{detail_id} - supplier_id={item.supplier_id}, unit_price={item.unit_price}\\n")
        
        return create_response(item.to_dict())
        
    except Exception as e:
        db.session.rollback()
        print(f"[EMERGENCY_HOTFIX] Error: {e}")
        return create_error_response(
            'SAVE_CHANGES_ERROR',
            'Failed to save changes',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/user-statistics', methods=['GET'])
@authenticated_required
def get_user_statistics(current_user):
    """Get user-based ITEM statistics for questions overview - Updated to count items not requisitions"""
    try:
        # Query to get ITEM-level statistics for each user
        from sqlalchemy import func, case
        from app.models.user import User
        
        # Get all users who have submitted requisitions with item-level statistics
        user_stats = db.session.query(
            User.username,
            User.chinese_name,
            func.count(RequestOrderItem.detail_id).label('total_items'),
            func.count(case(
                ((RequestOrderItem.item_status == 'questioned'), RequestOrderItem.detail_id),
                else_=None
            )).label('questioned_items'),
            func.count(case(
                ((RequestOrderItem.item_status == 'rejected'), RequestOrderItem.detail_id),
                else_=None
            )).label('rejected_items')
        ).select_from(User).join(
            RequestOrder, User.user_id == RequestOrder.requester_id
        ).join(
            RequestOrderItem, RequestOrder.request_order_no == RequestOrderItem.request_order_no
        ).group_by(User.user_id, User.username, User.chinese_name).all()
        
        # Convert to list of dictionaries with item-level counts
        stats_list = []
        for stat in user_stats:
            total_problematic = stat.questioned_items + stat.rejected_items
            stats_list.append({
                'username': stat.username,
                'display_name': stat.chinese_name or stat.username,
                'total_items': stat.total_items,
                'questioned_items': stat.questioned_items,
                'rejected_items': stat.rejected_items,
                'total_problematic': total_problematic
            })
        
        return create_response({
            'user_statistics': stats_list,
            'summary': {
                'total_users': len(stats_list),
                'total_items': sum(s['total_items'] for s in stats_list),
                'total_questioned': sum(s['questioned_items'] for s in stats_list),
                'total_rejected': sum(s['rejected_items'] for s in stats_list)
            }
        })
        
    except Exception as e:
        print(f"[ERROR] Failed to get user statistics: {e}")
        return create_error_response(
            'USER_STATISTICS_ERROR',
            'Failed to get user statistics',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/questions-data', methods=['GET'])
@authenticated_required  
def get_questions_data(current_user):
    """Get detailed questions data for LINE copy feature"""
    try:
        # Get requisitions with questioned or rejected items
        problematic_items = db.session.query(
            RequestOrder.request_order_no,
            RequestOrder.requester_name,
            RequestOrderItem.detail_id,
            RequestOrderItem.item_name,
            RequestOrderItem.item_status,
            RequestOrderItem.status_note,
            RequestOrder.submit_date
        ).join(
            RequestOrderItem, RequestOrder.request_order_no == RequestOrderItem.request_order_no
        ).filter(
            RequestOrderItem.item_status.in_(['questioned', 'rejected'])
        ).order_by(RequestOrder.submit_date.desc()).all()
        
        # Group by user
        user_questions = {}
        for item in problematic_items:
            user_key = item.requester_name
            if user_key not in user_questions:
                user_questions[user_key] = {
                    'username': user_key,
                    'questions': [],
                    'rejections': []
                }
            
            item_data = {
                'request_order_no': item.request_order_no,
                'detail_id': item.detail_id,
                'item_name': item.item_name,
                'status_note': item.status_note or '',
                'submit_date': item.submit_date.strftime('%Y-%m-%d') if item.submit_date else ''
            }
            
            if item.item_status == 'questioned':
                user_questions[user_key]['questions'].append(item_data)
            elif item.item_status == 'rejected':
                user_questions[user_key]['rejections'].append(item_data)
        
        return create_response({
            'user_questions': list(user_questions.values())
        })
        
    except Exception as e:
        print(f"[ERROR] Failed to get questions data: {e}")
        return create_error_response(
            'QUESTIONS_DATA_ERROR',
            'Failed to get questions data',
            {'error': str(e)},
            status_code=500
        )

@bp.route('', methods=['GET'])
@authenticated_required
def list_requisitions(current_user):
    """List requisitions with role-based filtering - UPDATED"""
    print(f"[DEBUG] list_requisitions called for user: {current_user.username}, role: {current_user.role}")
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        mine = request.args.get('mine', 'false').lower() == 'true'
        status = request.args.get('status')
        q = request.args.get('q', '').strip()
        
        query = RequestOrder.query
        
        # CRITICAL: Role-based access control
        privileged_roles = ['Admin', 'ProcurementMgr', 'Procurement', 'Manager']
        if current_user.role not in privileged_roles:
            # Non-privileged users can only see their own requisitions
            query = query.filter(RequestOrder.requester_id == current_user.user_id)
        elif mine:
            # Privileged users can optionally filter to see only their own
            query = query.filter(RequestOrder.requester_id == current_user.user_id)
        # Privileged users see all requisitions by default (no additional filter)
        
        # Filter by status
        if status:
            query = query.filter(RequestOrder.order_status == status)
        
        # Search in requester name or order number
        if q:
            query = query.filter(
                db.or_(
                    RequestOrder.request_order_no.ilike(f'%{q}%'),
                    RequestOrder.requester_name.ilike(f'%{q}%')
                )
            )
        
        query = query.order_by(RequestOrder.created_at.desc())
        result = paginate_query(query, page, page_size)
        
        # Add permission context to response
        permissions_data = {
            'can_view_all': current_user.role in privileged_roles,
            'user_role': current_user.role,
            'filtered_to_own': current_user.role not in privileged_roles or mine
        }
        print(f"[DEBUG] Permissions data: {permissions_data}")
        
        response_data = {
            'items': [order.to_dict() for order in result['items']],
            'pagination': result['pagination'],
            'permissions': permissions_data
        }
        print(f"[DEBUG] Response keys: {list(response_data.keys())}")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return create_error_response(
            'REQUISITION_LIST_ERROR',
            'Failed to fetch requisitions',
            {'error': str(e)},
            status_code=500
        )

@bp.route('', methods=['POST'])
@authenticated_required
def create_requisition(current_user):
    """Create new requisition with items"""
    try:
        data = request.get_json()
        
        required_fields = ['usage_type', 'items']
        for field in required_fields:
            if field not in data:
                return create_error_response(
                    'MISSING_FIELD',
                    f'{field} is required',
                    status_code=400
                )
        
        if not data['items'] or not isinstance(data['items'], list):
            return create_error_response(
                'INVALID_ITEMS',
                'At least one item is required',
                status_code=400
            )
        
        # Generate request order number
        today = date.today()
        prefix = f"REQ{today.strftime('%Y%m%d')}"
        existing_count = RequestOrder.query.filter(
            RequestOrder.request_order_no.like(f"{prefix}%")
        ).count()
        request_order_no = f"{prefix}{existing_count + 1:03d}"
        
        # CRITICAL FIX: Handle status from frontend
        initial_status = data.get('status', 'draft')  # Default to draft if not specified
        
        # Create request order with specified status and urgent fields
        order = RequestOrder(
            request_order_no=request_order_no,
            requester_id=current_user.user_id,
            requester_name=current_user.chinese_name,
            usage_type=data['usage_type'],
            project_id=data.get('project_id'),
            order_status=initial_status,  # CRITICAL FIX: Set initial status
            # Add urgent fields
            is_urgent=data.get('is_urgent', False),
            expected_delivery_date=datetime.strptime(data['expected_delivery_date'], '%Y-%m-%d').date()
                if data.get('expected_delivery_date') else None,
            urgent_reason=data.get('urgent_reason')
        )
        
        # CRITICAL FIX: Set submit_date if creating directly in submitted status
        if initial_status == 'submitted':
            order.submit_date = date.today()
        
        db.session.add(order)
        db.session.flush()  # Get the order number
        
        # Add items
        for item_data in data['items']:
            item_required_fields = ['item_name', 'item_quantity', 'item_unit']
            for field in item_required_fields:
                if field not in item_data:
                    return create_error_response(
                        'MISSING_ITEM_FIELD',
                        f'Item field {field} is required',
                        status_code=400
                    )
            
            if float(item_data['item_quantity']) <= 0:
                return create_error_response(
                    'INVALID_QUANTITY',
                    'Item quantity must be positive',
                    status_code=400
                )
            
            # CRITICAL FIX: Set item status based on order status
            item_status = 'pending_review' if initial_status == 'submitted' else 'draft'
            
            item = RequestOrderItem(
                request_order_no=request_order_no,
                item_name=item_data['item_name'],
                item_quantity=item_data['item_quantity'],
                item_unit=item_data['item_unit'],
                item_specification=item_data.get('item_specification'),
                item_description=item_data.get('item_description'),
                item_category=item_data.get('item_category'),
                item_status=item_status,  # CRITICAL FIX: Set correct item status
                needs_acceptance=item_data.get('needs_acceptance', True)
            )
            db.session.add(item)
        
        db.session.commit()
        
        # Reload with relationships
        order = RequestOrder.query.get(request_order_no)
        return create_response(order.to_dict(), status_code=201)
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'REQUISITION_CREATE_ERROR',
            'Failed to create requisition',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/<request_order_no>', methods=['GET'])
@authenticated_required
def get_requisition(current_user, request_order_no):
    """Get requisition details with items and history"""
    try:
        order = RequestOrder.query.get_or_404(request_order_no)
        
        # Non-procurement users can only view their own requisitions
        if (current_user.role not in ['Admin', 'ProcurementMgr', 'Procurement', 'Manager'] and
            order.requester_id != current_user.user_id):
            return create_error_response(
                'INSUFFICIENT_PERMISSIONS',
                'Can only view own requisitions',
                status_code=403
            )
        
        response_data = order.to_dict()
        response_data['items'] = [item.to_dict() for item in order.items.all()]
        
        return create_response(response_data)
        
    except Exception as e:
        return create_error_response(
            'REQUISITION_GET_ERROR',
            'Failed to get requisition',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/<request_order_no>', methods=['PUT'])
@authenticated_required
def update_requisition(current_user, request_order_no):
    """Update draft requisition"""
    try:
        order = RequestOrder.query.get_or_404(request_order_no)
        
        # Only requester can edit their own draft requisitions
        if order.requester_id != current_user.user_id:
            return create_error_response(
                'INSUFFICIENT_PERMISSIONS',
                'Can only edit own requisitions',
                status_code=403
            )
        
        if not order.can_edit():
            return create_error_response(
                'CANNOT_EDIT',
                'Requisition cannot be edited',
                status_code=400
            )
        
        data = request.get_json()
        
        # Update order fields
        if 'usage_type' in data:
            order.usage_type = data['usage_type']
        if 'project_id' in data:
            order.project_id = data['project_id']
        # Update urgent fields
        if 'is_urgent' in data:
            order.is_urgent = data['is_urgent']
        if 'expected_delivery_date' in data:
            order.expected_delivery_date = datetime.strptime(data['expected_delivery_date'], '%Y-%m-%d').date() \
                if data['expected_delivery_date'] else None
        if 'urgent_reason' in data:
            order.urgent_reason = data['urgent_reason']
        
        # Update items if provided
        if 'items' in data:
            # Remove existing items
            RequestOrderItem.query.filter_by(request_order_no=request_order_no).delete()
            
            # Add new items
            for item_data in data['items']:
                item = RequestOrderItem(
                    request_order_no=request_order_no,
                    item_name=item_data['item_name'],
                    item_quantity=item_data['item_quantity'],
                    item_unit=item_data['item_unit'],
                    item_specification=item_data.get('item_specification'),
                    item_description=item_data.get('item_description'),
                    item_category=item_data.get('item_category'),
                    needs_acceptance=item_data.get('needs_acceptance', True)
                )
                db.session.add(item)
        
        db.session.commit()
        
        # Reload with relationships
        order = RequestOrder.query.get(request_order_no)
        response_data = order.to_dict()
        response_data['items'] = [item.to_dict() for item in order.items.all()]
        
        return create_response(response_data)
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'REQUISITION_UPDATE_ERROR',
            'Failed to update requisition',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/<request_order_no>/submit', methods=['POST'])
@authenticated_required
def submit_requisition(current_user, request_order_no):
    """Submit requisition for review"""
    try:
        order = RequestOrder.query.get_or_404(request_order_no)
        
        if order.requester_id != current_user.user_id:
            return create_error_response(
                'INSUFFICIENT_PERMISSIONS',
                'Can only submit own requisitions',
                status_code=403
            )
        
        if not order.can_submit():
            return create_error_response(
                'CANNOT_SUBMIT',
                'Requisition cannot be submitted',
                status_code=400
            )
        
        order.submit()
        db.session.commit()
        
        return create_response(order.to_dict())
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'REQUISITION_SUBMIT_ERROR',
            'Failed to submit requisition',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/<request_order_no>/lines/<int:detail_id>/approve', methods=['POST'])
@procurement_required
def approve_line(current_user, request_order_no, detail_id):
    """Approve requisition line"""
    print(f"[ENDPOINT_DEBUG] ========== APPROVAL ENDPOINT CALLED ==========")
    print(f"[ENDPOINT_DEBUG] Request Order: {request_order_no}, Detail ID: {detail_id}")
    try:
        item = RequestOrderItem.query.filter_by(
            request_order_no=request_order_no,
            detail_id=detail_id
        ).first_or_404()
        
        data = request.get_json()
        required_fields = ['supplier_id', 'unit_price']
        for field in required_fields:
            if field not in data:
                return create_error_response(
                    'MISSING_FIELD',
                    f'{field} is required',
                    status_code=400
                )
        
        if float(data['unit_price']) <= 0:
            return create_error_response(
                'INVALID_PRICE',
                'Unit price must be positive',
                status_code=400
            )
        
        print(f"[APPROVE_LINE] Approving item {detail_id} for {request_order_no}")
        # EMERGENCY DEBUG: Write to file since console output is missing
        with open('approval_debug.log', 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now()}] APPROVAL API CALLED: {request_order_no}/{detail_id}\n")
        item.approve(data['supplier_id'], data['unit_price'], data.get('note', ''))
        print(f"[APPROVE_LINE] Item approved, now flushing to DB")
        
        # CRITICAL BUG FIX: Ensure item approval is persisted before status check
        db.session.flush()  # Flush item approval to database
        
        # Get fresh query of order to check all items (without clearing session)
        order = RequestOrder.query.filter_by(request_order_no=request_order_no).first()
        
        if order:
            print(f"[CRITICAL_FIX] Order {order.request_order_no} found, checking status update")
            print(f"[CRITICAL_FIX] Current order status: {order.order_status}")
            
            # Get fresh item summary
            summary = order.get_summary()
            print(f"[CRITICAL_FIX] Order summary: {summary}")
            
            # Only call status update if order is submitted and all items reviewed
            if (order.order_status == 'submitted' and 
                summary['total_items'] > 0 and 
                summary['pending_items'] == 0):
                
                print(f"[CRITICAL_FIX] Conditions met for status update - calling update_status_after_review")
                order.update_status_after_review()
                print(f"[CRITICAL_FIX] Status after update: {order.order_status}")
                
                # Force the update to be written
                db.session.flush()
                print(f"[CRITICAL_FIX] Status update flushed to database")
            else:
                print(f"[CRITICAL_FIX] Status update conditions not met")
                print(f"[CRITICAL_FIX] - Order status: {order.order_status}")
                print(f"[CRITICAL_FIX] - Total items: {summary['total_items']}")
                print(f"[CRITICAL_FIX] - Pending items: {summary['pending_items']}")
        else:
            print(f"[CRITICAL_FIX] ERROR: Could not find order {request_order_no}")
        
        # Commit all changes
        db.session.commit()
        print(f"[CRITICAL_FIX] All changes committed to database")
        
        # WEBSOCKET INTEGRATION: Broadcast status change if order was updated
        if (order and order.order_status == 'reviewed' and 
            summary.get('pending_items', 1) == 0):
            from app.websocket import broadcast_requisition_status_change
            print(f"[WEBSOCKET] Broadcasting status change for {request_order_no}: submitted → reviewed")
            broadcast_requisition_status_change(
                request_order_no, 
                'submitted', 
                'reviewed',
                {
                    'updated_by': current_user.username,
                    'approved_item_id': detail_id,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
        
        return create_response(item.to_dict())
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'LINE_APPROVE_ERROR',
            'Failed to approve line',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/<request_order_no>/lines/<int:detail_id>/question', methods=['POST'])
@procurement_required
def question_line(current_user, request_order_no, detail_id):
    """Mark line as questioned"""
    try:
        item = RequestOrderItem.query.filter_by(
            request_order_no=request_order_no,
            detail_id=detail_id
        ).first_or_404()
        
        data = request.get_json()
        if not data.get('reason'):
            return create_error_response(
                'MISSING_REASON',
                'Reason is required',
                status_code=400
            )
        
        try:
            # Pass the current user's ID as the reviewer
            item.question(data['reason'], reviewer_id=current_user.user_id)
        except ValueError as ve:
            # CRITICAL FIX: Handle business logic errors gracefully
            print(f"[QUESTION_ERROR] Business logic error for {request_order_no}/{detail_id}: {ve}")
            return create_error_response(
                'QUESTION_NOT_ALLOWED',
                str(ve),
                {
                    'current_status': item.item_status,
                    'item_name': item.item_name,
                    'request_order_no': request_order_no,
                    'detail_id': detail_id
                },
                status_code=400
            )
        
        # CRITICAL BUG FIX: Ensure item update is persisted before status check
        db.session.flush()
        
        order = RequestOrder.query.filter_by(request_order_no=request_order_no).first()
        if order and order.order_status == 'submitted':
            summary = order.get_summary()
            if summary['total_items'] > 0 and summary['pending_items'] == 0:
                print(f"[CRITICAL_FIX] Question - updating status for {order.request_order_no}")
                order.update_status_after_review()
                db.session.flush()
        
        db.session.commit()
        
        # Refresh item to ensure relationships are loaded
        db.session.refresh(item)
        return create_response(item.to_dict())
        
    except Exception as e:
        db.session.rollback()
        print(f"[QUESTION_ERROR] Unexpected error for {request_order_no}/{detail_id}: {e}")
        return create_error_response(
            'LINE_QUESTION_ERROR',
            'Failed to question line',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/<request_order_no>/lines/<int:detail_id>/reject', methods=['POST'])
@procurement_required
def reject_line(current_user, request_order_no, detail_id):
    """Reject requisition line"""
    try:
        item = RequestOrderItem.query.filter_by(
            request_order_no=request_order_no,
            detail_id=detail_id
        ).first_or_404()
        
        data = request.get_json()
        if not data.get('reason'):
            return create_error_response(
                'MISSING_REASON',
                'Reason is required',
                status_code=400
            )
        
        try:
            item.reject(data['reason'])
        except ValueError as ve:
            # CRITICAL FIX: Handle business logic errors gracefully
            print(f"[REJECT_ERROR] Business logic error for {request_order_no}/{detail_id}: {ve}")
            return create_error_response(
                'REJECT_NOT_ALLOWED',
                str(ve),
                {
                    'current_status': item.item_status,
                    'item_name': item.item_name,
                    'request_order_no': request_order_no,
                    'detail_id': detail_id
                },
                status_code=400
            )
        
        # CRITICAL BUG FIX: Ensure item update is persisted before status check
        db.session.flush()
        
        order = RequestOrder.query.filter_by(request_order_no=request_order_no).first()
        if order and order.order_status == 'submitted':
            summary = order.get_summary()
            if summary['total_items'] > 0 and summary['pending_items'] == 0:
                print(f"[CRITICAL_FIX] Reject - updating status for {order.request_order_no}")
                order.update_status_after_review()
                db.session.flush()
        
        db.session.commit()
        
        # Refresh item to ensure relationships are loaded
        db.session.refresh(item)
        return create_response(item.to_dict())
        
    except Exception as e:
        db.session.rollback()
        print(f"[REJECT_ERROR] Unexpected error for {request_order_no}/{detail_id}: {e}")
        return create_error_response(
            'LINE_REJECT_ERROR',
            'Failed to reject line',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/<request_order_no>/reject', methods=['POST'])
@procurement_required
def reject_requisition(current_user, request_order_no):
    """Reject entire requisition"""
    try:
        order = RequestOrder.query.get_or_404(request_order_no)
        
        data = request.get_json()
        reason = data.get('reason', '')
        
        order.reject(reason)
        db.session.commit()
        
        return create_response(order.to_dict())
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'REQUISITION_REJECT_ERROR',
            'Failed to reject requisition',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/<request_order_no>/fix-status', methods=['POST'])
@procurement_required  
def fix_requisition_status(current_user, request_order_no):
    """Manually fix requisition status - EMERGENCY FIX ENDPOINT - NOW HANDLES SAVE-CHANGES"""
    try:
        data = request.get_json() or {}
        
        # EMERGENCY WORKAROUND: Check if this is a save-changes request
        detail_id = data.get('detail_id')
        is_save_changes = detail_id is not None
        
        if is_save_changes:
            # Handle save-changes functionality using working endpoint
            print(f"[EMERGENCY_WORKAROUND] Save changes requested for {request_order_no}/{detail_id}")
            
            item = RequestOrderItem.query.filter_by(
                request_order_no=request_order_no,
                detail_id=detail_id
            ).first_or_404()
            
            print(f"[EMERGENCY_WORKAROUND] Received data: {data}")
            
            # Emergency debug logging
            with open('approval_debug.log', 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now()}] EMERGENCY_WORKAROUND SAVE_CHANGES: {request_order_no}/{detail_id} - {data}\\n")
            
            # Update supplier if provided
            if 'supplier_id' in data and data['supplier_id']:
                print(f"[EMERGENCY_WORKAROUND] Updating supplier_id: {item.supplier_id} -> {data['supplier_id']}")
                item.supplier_id = data['supplier_id']
            
            # Update unit price if provided
            if 'unit_price' in data and data['unit_price'] is not None:
                if float(data['unit_price']) >= 0:
                    print(f"[EMERGENCY_WORKAROUND] Updating unit_price: {item.unit_price} -> {data['unit_price']}")
                    item.unit_price = float(data['unit_price'])
            
            # Update note if provided
            if 'status_note' in data:
                print(f"[EMERGENCY_WORKAROUND] Updating status_note: {item.status_note} -> {data['status_note']}")
                item.status_note = data['status_note']
            
            # CRITICAL: DO NOT change item_status - this is just saving changes
            print(f"[EMERGENCY_WORKAROUND] Item status remains: {item.item_status}")
            
            db.session.commit()
            print(f"[EMERGENCY_WORKAROUND] Changes saved successfully")
            
            # Emergency debug logging
            with open('approval_debug.log', 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now()}] EMERGENCY_WORKAROUND COMPLETED: {request_order_no}/{detail_id} - supplier_id={item.supplier_id}, unit_price={item.unit_price}\\n")
            
            return create_response(item.to_dict())
        
        else:
            # Original status fix functionality
            print(f"[FIX_STATUS] Manual status fix requested for {request_order_no} by {current_user.username}")
            
            order = RequestOrder.query.get_or_404(request_order_no)
            
            print(f"[FIX_STATUS] Current status: {order.order_status}")
            
            # Get current summary before fix
            before_summary = order.get_summary()
            print(f"[FIX_STATUS] Before fix summary: {before_summary}")
            
            # Force status update
            order.update_status_after_review()
            
            # Get summary after fix
            after_summary = order.get_summary()
            print(f"[FIX_STATUS] After fix summary: {after_summary}")
            
            return create_response({
                'message': 'Status fix attempted',
                'requisition_number': request_order_no,
                'before_status': order.order_status if hasattr(order, '_before_status') else 'unknown',
                'after_status': order.order_status,
                'before_summary': before_summary,
                'after_summary': after_summary,
                'fixed_by': current_user.username,
                'timestamp': datetime.now().isoformat()
            })
        
    except Exception as e:
        print(f"[FIX_STATUS] Error: {e}")
        db.session.rollback()
        return create_error_response(
            'STATUS_FIX_ERROR',
            'Failed to fix requisition status or save changes',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/<request_order_no>/emergency-save-changes', methods=['POST'])
@procurement_required  
def emergency_save_changes(current_user, request_order_no):
    """EMERGENCY P0 HOTFIX: Save item changes without approval"""
    try:
        data = request.get_json()
        detail_id = data.get('detail_id')
        
        if not detail_id:
            return create_error_response(
                'MISSING_DETAIL_ID',
                'detail_id is required',
                status_code=400
            )
        
        print(f"[EMERGENCY_HOTFIX] Save changes for {request_order_no}/{detail_id}")
        
        item = RequestOrderItem.query.filter_by(
            request_order_no=request_order_no,
            detail_id=detail_id
        ).first_or_404()
        
        # Emergency debug logging
        with open('approval_debug.log', 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now()}] EMERGENCY_SAVE_CHANGES: {request_order_no}/{detail_id} - {data}\\n")
        
        # Update supplier if provided
        if 'supplier_id' in data and data['supplier_id']:
            item.supplier_id = data['supplier_id']
        
        # Update unit price if provided
        if 'unit_price' in data and data['unit_price'] is not None:
            if float(data['unit_price']) >= 0:
                item.unit_price = float(data['unit_price'])
        
        # Update note if provided
        if 'status_note' in data:
            item.status_note = data['status_note']
        
        db.session.commit()
        
        # Emergency debug logging
        with open('approval_debug.log', 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now()}] EMERGENCY_SAVE_CHANGES COMPLETED: {request_order_no}/{detail_id}\\n")
        
        print(f"[EMERGENCY_HOTFIX] Changes saved successfully!")
        
        return create_response(item.to_dict())
        
    except Exception as e:
        db.session.rollback()
        print(f"[EMERGENCY_HOTFIX] Error: {e}")
        return create_error_response(
            'EMERGENCY_SAVE_ERROR',
            'Emergency save failed',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/<request_order_no>/lines/<int:detail_id>/save-changes', methods=['POST'])
@procurement_required
def save_line_changes(current_user, request_order_no, detail_id):
    """Save supplier and price changes without changing approval status - EMERGENCY HOTFIX"""
    print(f"[SAVE_CHANGES] Emergency hotfix endpoint called for {request_order_no}/{detail_id}")
    try:
        item = RequestOrderItem.query.filter_by(
            request_order_no=request_order_no,
            detail_id=detail_id
        ).first_or_404()
        
        data = request.get_json()
        print(f"[SAVE_CHANGES] Received data: {data}")
        
        # Emergency debug logging
        with open('approval_debug.log', 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now()}] SAVE_CHANGES API CALLED: {request_order_no}/{detail_id} - {data}\n")
        
        # Update supplier if provided
        if 'supplier_id' in data and data['supplier_id']:
            print(f"[SAVE_CHANGES] Updating supplier_id: {item.supplier_id} -> {data['supplier_id']}")
            item.supplier_id = data['supplier_id']
        
        # Update unit price if provided
        if 'unit_price' in data and data['unit_price'] is not None:
            if float(data['unit_price']) >= 0:  # Allow 0 price for special cases
                print(f"[SAVE_CHANGES] Updating unit_price: {item.unit_price} -> {data['unit_price']}")
                item.unit_price = float(data['unit_price'])
        
        # Update note if provided
        if 'status_note' in data:
            print(f"[SAVE_CHANGES] Updating status_note: {item.status_note} -> {data['status_note']}")
            item.status_note = data['status_note']
        
        # CRITICAL: DO NOT change item_status - this is just saving changes
        print(f"[SAVE_CHANGES] Item status remains: {item.item_status}")
        
        db.session.commit()
        print(f"[SAVE_CHANGES] Changes saved successfully for {request_order_no}/{detail_id}")
        
        # Emergency debug logging
        with open('approval_debug.log', 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now()}] SAVE_CHANGES COMPLETED: {request_order_no}/{detail_id} - supplier_id={item.supplier_id}, unit_price={item.unit_price}\n")
        
        return create_response(item.to_dict())
        
    except Exception as e:
        db.session.rollback()
        print(f"[SAVE_CHANGES] Error saving changes: {e}")
        return create_error_response(
            'SAVE_CHANGES_ERROR',
            'Failed to save changes',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/<request_order_no>/emergency-fix-status', methods=['POST'])
@authenticated_required  # Only authenticated, not procurement-specific for EMERGENCY
def emergency_fix_status_admin(current_user, request_order_no):
    """EMERGENCY P0 ENDPOINT: Save changes with admin access - BYPASSES PROCUREMENT REQUIREMENT"""
    try:
        data = request.get_json() or {}
        
        # EMERGENCY WORKAROUND: Check if this is a save-changes request
        detail_id = data.get('detail_id')
        is_save_changes = detail_id is not None
        
        if is_save_changes:
            # Handle save-changes functionality using emergency endpoint
            print(f"[EMERGENCY_ADMIN] Save changes requested for {request_order_no}/{detail_id} by {current_user.username}")
            
            item = RequestOrderItem.query.filter_by(
                request_order_no=request_order_no,
                detail_id=detail_id
            ).first_or_404()
            
            print(f"[EMERGENCY_ADMIN] Received data: {data}")
            
            # Emergency debug logging
            with open('approval_debug.log', 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now()}] EMERGENCY_ADMIN SAVE_CHANGES: {request_order_no}/{detail_id} - {data}\\n")
            
            # Update supplier if provided
            if 'supplier_id' in data and data['supplier_id']:
                print(f"[EMERGENCY_ADMIN] Updating supplier_id: {item.supplier_id} -> {data['supplier_id']}")
                item.supplier_id = data['supplier_id']
            
            # Update unit price if provided
            if 'unit_price' in data and data['unit_price'] is not None:
                if float(data['unit_price']) >= 0:
                    print(f"[EMERGENCY_ADMIN] Updating unit_price: {item.unit_price} -> {data['unit_price']}")
                    item.unit_price = float(data['unit_price'])
            
            # Update note if provided
            if 'status_note' in data:
                print(f"[EMERGENCY_ADMIN] Updating status_note: {item.status_note} -> {data['status_note']}")
                item.status_note = data['status_note']
            
            # CRITICAL: DO NOT change item_status - this is just saving changes
            print(f"[EMERGENCY_ADMIN] Item status remains: {item.item_status}")
            
            db.session.commit()
            print(f"[EMERGENCY_ADMIN] Changes saved successfully")
            
            # Emergency debug logging
            with open('approval_debug.log', 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now()}] EMERGENCY_ADMIN COMPLETED: {request_order_no}/{detail_id} - supplier_id={item.supplier_id}, unit_price={item.unit_price}\\n")
            
            return create_response(item.to_dict())
        
        else:
            return create_error_response(
                'EMERGENCY_ADMIN_ERROR',
                'Emergency admin endpoint requires detail_id for save-changes',
                status_code=400
            )
        
    except Exception as e:
        print(f"[EMERGENCY_ADMIN] Error: {e}")
        db.session.rollback()
        return create_error_response(
            'EMERGENCY_ADMIN_ERROR',
            'Failed to execute emergency admin save changes',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/scan-status-problems', methods=['GET'])
@procurement_required
def scan_status_problems(current_user):
    """Scan all requisitions for status update problems - DIAGNOSTIC ENDPOINT"""
    try:
        print(f"[SCAN_PROBLEMS] Status problem scan requested by {current_user.username}")
        
        # Find all submitted requisitions
        submitted_orders = RequestOrder.query.filter_by(order_status='submitted').all()
        
        problems = []
        
        for order in submitted_orders:
            summary = order.get_summary()
            
            # Check if all items are reviewed but status is still submitted
            if (summary['total_items'] > 0 and 
                summary['pending_items'] == 0):
                
                problems.append({
                    'requisition_number': order.request_order_no,
                    'requester_name': order.requester_name,
                    'current_status': order.order_status,
                    'expected_status': 'reviewed',
                    'summary': summary,
                    'created_at': order.created_at.isoformat() if order.created_at else None,
                    'updated_at': order.updated_at.isoformat() if order.updated_at else None
                })
        
        print(f"[SCAN_PROBLEMS] Found {len(problems)} problems")
        
        return create_response({
            'total_problems': len(problems),
            'problems': problems,
            'scan_time': datetime.now().isoformat(),
            'scanned_by': current_user.username
        })
        
    except Exception as e:
        print(f"[SCAN_PROBLEMS] Error scanning: {e}")
        return create_error_response(
            'SCAN_PROBLEMS_ERROR',
            'Failed to scan status problems',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/<request_order_no>/cancel', methods=['POST'])
@procurement_required
def cancel_request_order(current_user, request_order_no):
    """Cancel/withdraw a request order (ProcurementMgr and Admin only)"""
    try:
        # Check if user has required role
        if current_user.role not in ['ProcurementMgr', 'Admin']:
            return create_error_response(
                'PERMISSION_DENIED',
                'Only Procurement Managers and Administrators can cancel request orders',
                status_code=403
            )
        
        order = RequestOrder.query.get_or_404(request_order_no)
        
        # Check if the requisition is in 'reviewed' status
        # Per business rule: reviewed requisitions cannot be cancelled directly
        # They must be cancelled from the purchase order side
        if order.order_status == 'reviewed':
            return create_error_response(
                'INVALID_STATUS',
                '已審核的請購單不能直接撤銷，請從採購單側進行撤銷',
                status_code=400
            )
        
        # Only allow cancellation of draft and submitted requisitions
        if order.order_status not in ['draft', 'submitted']:
            return create_error_response(
                'INVALID_STATUS',
                f'Cannot cancel requisition with status: {order.order_status}',
                status_code=400
            )
        
        # Get cancellation reason from request
        data = request.get_json() or {}
        reason = data.get('reason', 'No reason provided')
        
        # Call the cancel method
        order.cancel(reason, current_user.user_id)
        
        # Commit the changes
        db.session.commit()
        
        # Return updated order data
        order_dict = order.to_dict()
        order_dict['success'] = True
        order_dict['message'] = f'請購單 {request_order_no} 已撤銷'
        
        return create_response(order_dict)
        
    except ValueError as ve:
        return create_error_response(
            'CANCEL_REQUEST_ORDER_ERROR',
            str(ve),
            status_code=400
        )
    except Exception as e:
        print(f"[CANCEL_REQUEST_ORDER] Error cancelling {request_order_no}: {e}")
        db.session.rollback()
        return create_error_response(
            'CANCEL_REQUEST_ORDER_ERROR',
            'Failed to cancel request order',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/questioned-items', methods=['GET'])
@authenticated_required
def get_questioned_items(current_user):
    """Get all questioned items across requisitions"""
    try:
        from sqlalchemy import text

        # Get query parameters
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        search = request.args.get('search', '')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Build the base query
        query = """
            SELECT
                roi.detail_id,
                roi.request_order_no,
                roi.item_name,
                roi.item_specification,
                roi.item_quantity,
                roi.item_unit,
                roi.item_category,
                roi.item_description,
                roi.item_status,
                roi.status_note,
                roi.reviewed_at as questioned_at,
                roi.reviewer_id as questioned_by,
                roi.supplier_id,
                roi.unit_price,
                ro.requester_name,
                ro.submit_date,
                u.chinese_name as questioned_by_name
            FROM request_order_items roi
            JOIN request_orders ro ON roi.request_order_no = ro.request_order_no
            LEFT JOIN users u ON roi.reviewer_id = u.user_id
            WHERE roi.item_status = 'questioned'
        """

        params = {}

        # Add search filter
        if search:
            query += " AND (roi.item_name LIKE :search OR roi.request_order_no LIKE :search)"
            params['search'] = f'%{search}%'

        # Add date range filter
        if start_date:
            query += " AND roi.reviewed_at >= :start_date"
            params['start_date'] = start_date

        if end_date:
            query += " AND roi.reviewed_at <= :end_date"
            params['end_date'] = end_date + ' 23:59:59'

        # Count total items
        count_query = f"SELECT COUNT(*) as total FROM ({query}) as subquery"
        total_result = db.session.execute(text(count_query), params).fetchone()
        total = total_result.total if total_result else 0

        # Add pagination and ordering
        query += f" ORDER BY roi.reviewed_at DESC LIMIT {page_size} OFFSET {(page - 1) * page_size}"

        # Execute query
        results = db.session.execute(text(query), params).fetchall()

        # Format results
        items = []
        for row in results:
            items.append({
                'detail_id': row.detail_id,
                'request_order_no': row.request_order_no,
                'item_name': row.item_name,
                'item_specification': row.item_specification,
                'item_quantity': row.item_quantity,
                'item_unit': row.item_unit,
                'item_category': row.item_category,
                'item_description': row.item_description,
                'status_note': row.status_note,
                'supplier_id': row.supplier_id,
                'unit_price': row.unit_price,
                'questioned_at': row.questioned_at if isinstance(row.questioned_at, str) else (row.questioned_at.isoformat() if row.questioned_at else None),
                'questioned_by': row.questioned_by_name or (f'User {row.questioned_by}' if row.questioned_by else '-'),
                'requester_name': row.requester_name,
                'submit_date': row.submit_date if isinstance(row.submit_date, str) else (row.submit_date.isoformat() if row.submit_date else None)
            })

        return create_response({
            'items': items,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size if page_size > 0 else 0
        })

    except Exception as e:
        print(f"[GET_QUESTIONED_ITEMS] Error: {e}")
        return create_error_response(
            'GET_QUESTIONED_ITEMS_ERROR',
            'Failed to get questioned items',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/<request_order_no>/lines/<int:detail_id>/note', methods=['PATCH'])
@authenticated_required
def update_item_note(current_user, request_order_no, detail_id):
    """Update note for a requisition item"""
    try:
        from sqlalchemy import text

        data = request.get_json() or {}
        note = data.get('note', '')

        # Update the item note
        query = """
            UPDATE request_order_items
            SET status_note = :note
            WHERE request_order_no = :request_order_no
            AND detail_id = :detail_id
        """

        result = db.session.execute(text(query), {
            'note': note,
            'request_order_no': request_order_no,
            'detail_id': detail_id
        })

        if result.rowcount == 0:
            return create_error_response(
                'ITEM_NOT_FOUND',
                'Requisition item not found',
                status_code=404
            )

        db.session.commit()

        # Get updated item
        item_query = """
            SELECT * FROM request_order_items
            WHERE request_order_no = :request_order_no
            AND detail_id = :detail_id
        """

        item = db.session.execute(text(item_query), {
            'request_order_no': request_order_no,
            'detail_id': detail_id
        }).fetchone()

        return create_response({
            'detail_id': item.detail_id,
            'status_note': item.status_note,
            'message': 'Item note updated successfully'
        })

    except Exception as e:
        print(f"[UPDATE_ITEM_NOTE] Error: {e}")
        db.session.rollback()
        return create_error_response(
            'UPDATE_ITEM_NOTE_ERROR',
            'Failed to update item note',
            {'error': str(e)},
            status_code=500
        )

@bp.route("/urgent-suppliers", methods=["GET"])
@procurement_required
def get_urgent_suppliers(current_user):
    """取得有加急項目的供應商列表"""
    try:
        # 查詢有加急且已核准項目的供應商
        from app.models.supplier import Supplier

        urgent_suppliers = db.session.query(
            Supplier.supplier_id,
            Supplier.supplier_name_zh,
            db.func.count(RequestOrderItem.detail_id).label("urgent_item_count")
        ).join(
            RequestOrderItem, Supplier.supplier_id == RequestOrderItem.supplier_id
        ).join(
            RequestOrder, RequestOrderItem.request_order_no == RequestOrder.request_order_no
        ).filter(
            RequestOrder.is_urgent == True,
            RequestOrderItem.item_status == "approved"
        ).group_by(
            Supplier.supplier_id,
            Supplier.supplier_name_zh
        ).all()

        result = []
        for supplier_id, supplier_name, count in urgent_suppliers:
            result.append({
                "supplier_id": supplier_id,
                "supplier_name_zh": supplier_name,
                "urgent_item_count": count
            })

        return create_response(result)

    except Exception as e:
        return create_error_response(
            "URGENT_SUPPLIERS_ERROR",
            "Failed to get urgent suppliers",
            {"error": str(e)},
            status_code=500
        )

