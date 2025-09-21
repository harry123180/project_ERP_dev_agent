from flask import Blueprint, request, jsonify, send_file, Response
from app import db
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from app.models.request_order import RequestOrderItem
from app.models.supplier import Supplier
from app.models.system_settings import SystemSettings
from app.auth import procurement_required, authenticated_required, create_response, create_error_response, paginate_query
from app.utils.security import require_permission
from app.services.po_generator import POGenerator
from app.services.po_generator_enhanced import EnhancedPOGenerator
from app.services.po_html_generator import POHTMLGenerator
from app.services.po_pdf_generator import POPDFGenerator
from app.services.po_excel_generator import POExcelGenerator
from datetime import datetime
import io

bp = Blueprint('purchase_orders', __name__, url_prefix='/api/v1/po')

@bp.route('/build-candidates', methods=['GET'])
@procurement_required
def get_build_candidates(current_user):
    """Get approved items grouped by supplier for PO creation"""
    try:
        supplier_id = request.args.get('supplier_id')
        
        query = RequestOrderItem.query.filter_by(item_status='approved')
        
        if supplier_id:
            query = query.filter_by(supplier_id=supplier_id)
        
        items = query.all()
        
        # Group by supplier
        suppliers = {}
        for item in items:
            if item.supplier_id not in suppliers:
                suppliers[item.supplier_id] = {
                    'supplier_id': item.supplier_id,
                    'supplier': item.supplier.to_summary_dict() if item.supplier else None,
                    'items': []
                }
            suppliers[item.supplier_id]['items'].append(item.to_dict())
        
        return create_response(list(suppliers.values()))
        
    except Exception as e:
        return create_error_response(
            'BUILD_CANDIDATES_ERROR',
            'Failed to get build candidates',
            {'error': str(e)},
            status_code=500
        )

@bp.route('', methods=['POST'])
@procurement_required
def create_purchase_order(current_user):
    """Create purchase order from requisition lines"""
    try:
        data = request.get_json()
        
        required_fields = ['supplier_id', 'lines']
        for field in required_fields:
            if field not in data:
                return create_error_response(
                    'MISSING_FIELD',
                    f'{field} is required',
                    status_code=400
                )
        
        supplier = Supplier.query.get(data['supplier_id'])
        if not supplier:
            return create_error_response(
                'SUPPLIER_NOT_FOUND',
                f'Supplier {data["supplier_id"]} not found',
                status_code=400
            )
        
        # Generate PO number
        po_number = PurchaseOrder.generate_po_number()
        
        # Create PO header
        po = PurchaseOrder(
            purchase_order_no=po_number,
            supplier_id=supplier.supplier_id,
            supplier_name=supplier.supplier_name_zh,
            supplier_address=supplier.supplier_address,
            contact_phone=supplier.supplier_phone,
            contact_person=supplier.supplier_contact_person,
            supplier_tax_id=supplier.supplier_tax_id,
            creator_id=current_user.user_id,
            delivery_address=data.get('delivery_address'),
            notes=data.get('notes'),
            quotation_no=data.get('quotation_no')
        )
        
        db.session.add(po)
        db.session.flush()
        
        # Add line items
        for line_data in data['lines']:
            if 'detail_id' in line_data:
                # From requisition item
                req_item = RequestOrderItem.query.get(line_data['detail_id'])
                if not req_item or req_item.item_status != 'approved':
                    return create_error_response(
                        'INVALID_REQUISITION_ITEM',
                        f'Requisition item {line_data["detail_id"]} not found or not approved',
                        status_code=400
                    )
                
                po_item = PurchaseOrderItem(
                    purchase_order_no=po_number,
                    item_name=req_item.item_name,
                    item_quantity=req_item.item_quantity,
                    item_unit=req_item.item_unit,
                    unit_price=req_item.unit_price,
                    item_specification=req_item.item_specification,
                    source_request_order_no=req_item.request_order_no,
                    source_detail_id=req_item.detail_id
                )
                
                # Keep requisition item status as approved (it's still approved, just linked to a PO now)
                # The item_status should remain 'approved' - we track PO linkage via source_detail_id
                
            else:
                # Manual line item
                po_item = PurchaseOrderItem(
                    purchase_order_no=po_number,
                    item_name=line_data['item_name'],
                    item_quantity=line_data['item_quantity'],
                    item_unit=line_data['item_unit'],
                    unit_price=line_data['unit_price'],
                    item_specification=line_data.get('item_specification'),
                    item_model=line_data.get('item_model')
                )
            
            po_item.update_line_subtotal()
            db.session.add(po_item)
        
        # Recalculate totals
        db.session.flush()
        tax_rate = SystemSettings.get_tax_rate()
        po.recalculate_totals(tax_rate)
        
        db.session.commit()
        
        # Reload with relationships
        po = PurchaseOrder.query.get(po_number)
        response_data = po.to_dict()
        response_data['items'] = [item.to_dict() for item in po.items.all()]
        
        return create_response(response_data, status_code=201)
        
    except Exception as e:
        db.session.rollback()
        import traceback
        error_details = {
            'error': str(e),
            'type': type(e).__name__,
            'traceback': traceback.format_exc()
        }
        print(f"[PO_CREATE_ERROR] {type(e).__name__}: {str(e)}")
        print(f"[PO_CREATE_ERROR] Traceback: {traceback.format_exc()}")
        return create_error_response(
            'PO_CREATE_ERROR',
            'Failed to create purchase order',
            error_details,
            status_code=500
        )

@bp.route('', methods=['GET'])
@procurement_required
def list_purchase_orders(current_user):
    """List purchase orders with filtering"""
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        status = request.args.get('status')
        supplier_id = request.args.get('supplier_id')
        
        query = PurchaseOrder.query
        
        if status:
            query = query.filter(PurchaseOrder.purchase_status == status)
        if supplier_id:
            query = query.filter(PurchaseOrder.supplier_id == supplier_id)
        
        query = query.order_by(PurchaseOrder.created_at.desc())
        result = paginate_query(query, page, page_size)
        
        return jsonify({
            'items': [po.to_dict(include_user_details=True) for po in result['items']],
            'pagination': result['pagination']
        }), 200
        
    except Exception as e:
        return create_error_response(
            'PO_LIST_ERROR',
            'Failed to fetch purchase orders',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/<po_no>', methods=['GET'])
@authenticated_required
def get_purchase_order(current_user, po_no):
    """Get purchase order details with line items"""
    try:
        po = PurchaseOrder.query.get_or_404(po_no)
        
        response_data = po.to_dict(include_user_details=True)
        response_data['items'] = [item.to_dict() for item in po.items.all()]
        
        return create_response(response_data)
        
    except Exception as e:
        return create_error_response(
            'PO_GET_ERROR',
            'Failed to get purchase order',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/<po_no>', methods=['PUT'])
@procurement_required
def update_purchase_order(current_user, po_no):
    """Update purchase order details and recalculate totals"""
    try:
        po = PurchaseOrder.query.get_or_404(po_no)
        
        if not po.can_edit():
            return create_error_response(
                'CANNOT_EDIT',
                'Purchase order cannot be edited',
                status_code=400
            )
        
        data = request.get_json()
        
        # Update allowed fields
        updateable_fields = [
            'delivery_address', 'notes', 'quotation_no'
        ]
        
        for field in updateable_fields:
            if field in data:
                setattr(po, field, data[field])
        
        # Update items if provided
        if 'items' in data:
            # Remove existing items
            PurchaseOrderItem.query.filter_by(purchase_order_no=po_no).delete()
            
            # Add new items
            for item_data in data['items']:
                po_item = PurchaseOrderItem(
                    purchase_order_no=po_no,
                    item_name=item_data['item_name'],
                    item_quantity=item_data['item_quantity'],
                    item_unit=item_data['item_unit'],
                    unit_price=item_data['unit_price'],
                    item_specification=item_data.get('item_specification'),
                    item_model=item_data.get('item_model'),
                    source_request_order_no=item_data.get('source_request_order_no'),
                    source_detail_id=item_data.get('source_detail_id')
                )
                po_item.update_line_subtotal()
                db.session.add(po_item)
        
        # Recalculate totals
        db.session.flush()
        tax_rate = SystemSettings.get_tax_rate()
        po.recalculate_totals(tax_rate)
        
        db.session.commit()
        
        # Reload with relationships
        po = PurchaseOrder.query.get(po_no)
        response_data = po.to_dict()
        response_data['items'] = [item.to_dict() for item in po.items.all()]
        
        return create_response(response_data)
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'PO_UPDATE_ERROR',
            'Failed to update purchase order',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/<po_no>/confirm', methods=['POST'])
@procurement_required
def confirm_purchase(current_user, po_no):
    """Confirm purchase order (idempotent)"""
    try:
        po = PurchaseOrder.query.get_or_404(po_no)
        
        # Check idempotency key
        idempotency_key = request.headers.get('Idempotency-Key')
        
        if not po.can_confirm():
            # If already confirmed, check if this is idempotent request
            if po.purchase_status == 'purchased' and idempotency_key:
                return create_response(po.to_dict())
            else:
                return create_error_response(
                    'CANNOT_CONFIRM',
                    'Purchase order cannot be confirmed',
                    status_code=400
                )
        
        po.confirm_purchase(current_user.user_id, idempotency_key)
        
        # Keep source requisition items as approved (purchase confirmation is tracked via PO status)
        # The requisition items remain 'approved' - we track purchase via the PO relationship
        
        db.session.commit()
        
        return create_response(po.to_dict())
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'PO_CONFIRM_ERROR',
            'Failed to confirm purchase order',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/<po_no>/withdraw', methods=['POST'])
@procurement_required
def withdraw_purchase_order(current_user, po_no):
    """Withdraw purchase order with reason"""
    try:
        po = PurchaseOrder.query.get_or_404(po_no)
        
        data = request.get_json()
        reason = data.get('reason', '')
        
        po.withdraw(reason)
        db.session.commit()
        
        return create_response(po.to_dict())
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'PO_WITHDRAW_ERROR',
            'Failed to withdraw purchase order',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/<po_no>/milestone', methods=['POST'])
@procurement_required
def update_milestone(current_user, po_no):
    """Update shipping milestone for purchase order"""
    try:
        po = PurchaseOrder.query.get_or_404(po_no)
        
        data = request.get_json()
        if not data.get('status'):
            return create_error_response(
                'MISSING_STATUS',
                'Status is required',
                status_code=400
            )
        
        milestone_data = {}
        for field in ['shipped_at', 'eta_date', 'arrival_date', 'carrier', 'tracking_no', 'note']:
            if field in data:
                if field in ['shipped_at'] and data[field]:
                    milestone_data[field] = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
                elif field in ['eta_date', 'arrival_date'] and data[field]:
                    from datetime import datetime as dt
                    milestone_data[field] = dt.fromisoformat(data[field]).date()
                else:
                    milestone_data[field] = data[field]
        
        po.update_milestone(data['status'], **milestone_data)
        db.session.commit()
        
        return create_response(po.to_dict())
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'MILESTONE_UPDATE_ERROR',
            'Failed to update milestone',
            {'error': str(e)},
            status_code=500
        )

# New endpoints for PO output functionality
@bp.route('/<po_no>/preview', methods=['GET'])
@authenticated_required
def preview_purchase_order(current_user, po_no):
    """Get purchase order data for preview"""
    try:
        po = PurchaseOrder.query.get_or_404(po_no)
        generator = POGenerator()
        preview_data = generator.get_preview_data(po)
        return create_response(preview_data)
    except Exception as e:
        return create_error_response(
            'PO_PREVIEW_ERROR',
            'Failed to generate preview',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/<po_no>/export', methods=['POST'])
@procurement_required
def export_purchase_order(current_user, po_no):
    """Export purchase order to Excel or PDF with proper status transitions"""
    try:
        po = PurchaseOrder.query.get_or_404(po_no)
        data = request.get_json()
        format_type = data.get('format', 'print').lower()
        
        # Check if PO can be exported
        if not po.can_export():
            return create_error_response(
                'EXPORT_NOT_ALLOWED',
                f'Purchase order with status "{po.purchase_status}" cannot be exported',
                {'current_status': po.purchase_status, 'allowed_statuses': ['order_created', 'outputted']},
                status_code=400
            )
        
        # Record export operation and handle status transitions
        export_info = po.record_export(current_user.user_id)
        
        # Handle different export formats
        if format_type == 'html':
            html_generator = POHTMLGenerator()
            html_content = html_generator.generate_html(po)
            
            db.session.commit()
            
            # Return HTML response
            return Response(
                html_content,
                mimetype='text/html',
                headers={
                    'Content-Type': 'text/html; charset=utf-8',
                }
            )
            
        elif format_type == 'pdf':
            # For now, return HTML that can be printed to PDF
            pdf_generator = POPDFGenerator()
            html_content = pdf_generator.generate_pdf(po)
            
            db.session.commit()
            
            # Return HTML response with print-friendly format
            return Response(
                html_content,
                mimetype='text/html',
                headers={
                    'Content-Type': 'text/html; charset=utf-8',
                }
            )
            
        elif format_type == 'excel':
            excel_generator = POExcelGenerator()
            file_data = excel_generator.generate_excel(po)
            filename = f"PO_{po_no}.xlsx"
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            
            db.session.commit()
            
            # Send file
            return send_file(
                io.BytesIO(file_data),
                mimetype=mimetype,
                as_attachment=True,
                download_name=filename
            )
        
        else:  # print format - just return status information
            db.session.commit()
            
            return create_response({
                'success': True,
                'purchase_order_no': po_no,
                'export_info': export_info,
                'message': 'Purchase order prepared for printing'
            })
        
    except ValueError as e:
        db.session.rollback()
        return create_error_response(
            'EXPORT_VALIDATION_ERROR',
            str(e),
            {'purchase_order_no': po_no},
            status_code=400
        )
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'PO_EXPORT_ERROR',
            'Failed to export purchase order',
            {'error': str(e), 'purchase_order_no': po_no},
            status_code=500
        )

@bp.route('/pending-confirmation', methods=['GET'])
@authenticated_required
def get_pending_confirmation(current_user):
    """Get purchase orders with status 'order_created' for confirmation"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        
        query = PurchaseOrder.query.filter_by(purchase_status='order_created')
        
        # Apply pagination
        paginated = paginate_query(query, page, page_size)
        
        items = []
        for po in paginated['items']:
            po_dict = po.to_dict()
            # Add output person info
            if po.output_person:
                po_dict['output_by'] = po.output_person.chinese_name
                po_dict['output_date'] = po.updated_at.isoformat() if po.updated_at else None
            items.append(po_dict)
        
        return create_response({
            'items': items,
            'pagination': paginated['pagination']
        })
        
    except Exception as e:
        return create_error_response(
            'GET_PENDING_ERROR',
            'Failed to get pending confirmation list',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/<po_no>/confirm-purchase', methods=['POST'])
@procurement_required
def confirm_purchase_status(current_user, po_no):
    """Confirm purchase status (mark as purchased)"""
    try:
        po = PurchaseOrder.query.get_or_404(po_no)
        
        # Check if status is valid for confirmation (order_created or outputted)
        if po.purchase_status not in ['order_created', 'outputted']:
            return create_error_response(
                'INVALID_STATUS',
                'Purchase order must be in order_created or outputted status',
                {'current_status': po.purchase_status},
                status_code=400
            )
        
        # Update PO status to purchased
        po.purchase_status = 'purchased'
        po.confirm_purchaser_id = current_user.user_id

        # Update timestamp
        from datetime import datetime
        po.updated_at = datetime.utcnow()

        # Update all associated item statuses to completed
        for item in po.items:
            item.line_status = 'completed'
            item.updated_at = datetime.utcnow()

        db.session.commit()

        po_dict = po.to_dict()
        po_dict['confirmed_by'] = current_user.chinese_name
        po_dict['confirmed_at'] = po.updated_at.isoformat() if po.updated_at else None
        po_dict['success'] = True
        po_dict['message'] = f'採購單 {po_no} 已確認採購'
        
        return create_response(po_dict)
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'CONFIRM_PURCHASE_ERROR',
            'Failed to confirm purchase status',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/<po_no>/cancel', methods=['POST'])
@procurement_required
def cancel_purchase_order(current_user, po_no):
    """Cancel/withdraw a purchase order (ProcurementMgr and Admin only)"""
    try:
        # Check if user has required role
        if current_user.role not in ['ProcurementMgr', 'Admin']:
            return create_error_response(
                'PERMISSION_DENIED',
                'Only Procurement Managers and Administrators can cancel purchase orders',
                status_code=403
            )
        
        po = PurchaseOrder.query.get_or_404(po_no)
        
        # Get cancellation reason from request
        data = request.get_json() or {}
        reason = data.get('reason', 'No reason provided')
        
        # Call the withdraw method
        po.withdraw(reason, current_user.user_id)
        
        # Commit the changes
        db.session.commit()
        
        # Return updated PO data
        po_dict = po.to_dict(include_user_details=True)
        po_dict['success'] = True
        po_dict['message'] = f'採購單 {po_no} 已撤銷'
        
        return create_response(po_dict)
        
    except ValueError as e:
        return create_error_response(
            'INVALID_OPERATION',
            str(e),
            status_code=400
        )
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'CANCEL_PURCHASE_ERROR',
            'Failed to cancel purchase order',
            {'error': str(e)},
            status_code=500
        )