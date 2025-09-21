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

@bp.route('', methods=['GET'])
@bp.route('/', methods=['GET'])
@authenticated_required
def get_purchase_orders(current_user):
    """Get purchase orders list with filters"""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        supplier = request.args.get('supplier', '')
        status = request.args.get('status', '')

        # Build query
        query = PurchaseOrder.query

        # Apply filters
        if supplier:
            query = query.filter(PurchaseOrder.supplier_id == supplier)
        if status:
            query = query.filter(PurchaseOrder.purchase_status == status)

        # Order by creation date - using PO number for now to avoid datetime issues
        query = query.order_by(PurchaseOrder.purchase_order_no.desc())

        # Get total count for pagination info
        total_count = query.count()

        # Apply limit and offset manually instead of using paginate()
        offset = (page - 1) * page_size
        items = query.limit(page_size).offset(offset).all()

        # Calculate pages
        import math
        total_pages = math.ceil(total_count / page_size) if page_size > 0 else 1

        # Format response
        purchase_orders = []
        for po in items:
            try:
                po_dict = po.to_dict(include_user_details=True)  # Include user details to show 製單人 and 採購人
                # Add supplier info
                if po.supplier:
                    po_dict['supplier'] = po.supplier.to_summary_dict()
                purchase_orders.append(po_dict)
            except Exception as e:
                # If there's an error with a specific PO, skip it but log the error
                print(f"Error processing PO {po.purchase_order_no}: {e}")
                continue

        return create_response(
            data={
                'items': purchase_orders,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total': total_count,
                    'pages': total_pages
                }
            },
            message='Purchase orders fetched successfully'
        )
    except Exception as e:
        import traceback
        traceback.print_exc()  # Print full error to console for debugging
        return create_error_response(
            'PO_LIST_ERROR',
            'Failed to list purchase orders',
            {'error': str(e)},
            status_code=500
        )

@bp.route('', methods=['POST'])
@bp.route('/', methods=['POST'])
@procurement_required
def create_purchase_order(current_user):
    """Create a new purchase order"""
    try:
        data = request.get_json()

        # Generate PO number
        now = datetime.now()
        po_no = f"PO{now.strftime('%Y%m%d')}"

        # Find existing POs for today
        existing = PurchaseOrder.query.filter(
            PurchaseOrder.purchase_order_no.like(f"{po_no}%")
        ).count()

        po_no = f"{po_no}{str(existing + 1).zfill(3)}"

        # Get supplier information
        supplier = Supplier.query.get(data['supplier_id'])
        if not supplier:
            return create_error_response('Supplier not found', 404)

        # Create purchase order
        po = PurchaseOrder(
            purchase_order_no=po_no,
            supplier_id=data['supplier_id'],
            supplier_name=supplier.supplier_name_zh or supplier.supplier_name_en or '',
            supplier_address=data.get('supplier_address', supplier.supplier_address),
            contact_phone=data.get('contact_phone', supplier.supplier_phone),
            contact_person=data.get('contact_person', supplier.supplier_contact_person),
            supplier_tax_id=data.get('supplier_tax_id', supplier.supplier_tax_id),
            order_date=datetime.now(),
            quotation_no=data.get('quotation_no'),
            delivery_address=data.get('delivery_address'),
            creation_date=datetime.now(),
            creator_id=current_user.user_id,
            notes=data.get('notes'),
            purchase_status='order_created',
            shipping_status='none',
            billing_status='none'
        )

        # Calculate totals
        subtotal = 0

        # Handle both 'items' and 'lines' format
        items_data = data.get('items', []) or data.get('lines', [])

        # If lines format is used (from build candidates)
        if 'lines' in data and items_data:
            # Load the requisition items by detail_id
            for line in items_data:
                req_item = RequestOrderItem.query.get(line['detail_id'])
                if not req_item:
                    continue

                item = PurchaseOrderItem(
                    purchase_order_no=po_no,
                    item_name=req_item.item_name,
                    item_quantity=line.get('quantity', req_item.item_quantity),
                    item_unit=req_item.item_unit,
                    unit_price=line.get('unit_price', req_item.unit_price or 0),
                    item_specification=req_item.item_specification,
                    line_status='active',
                    source_request_order_no=req_item.request_order_no,
                    source_detail_id=req_item.detail_id
                )

                item.line_subtotal_int = int(item.item_quantity * item.unit_price)
                subtotal += item.line_subtotal_int

                po.items.append(item)

                # Update the requisition item status to indicate it's in a PO
                req_item.item_status = 'order_created'
        else:
            # Original items format (manual creation)
            for item_data in items_data:
                item = PurchaseOrderItem(
                    purchase_order_no=po_no,
                    item_name=item_data['item_name'],
                    item_quantity=item_data['item_quantity'],
                    item_unit=item_data['item_unit'],
                    unit_price=item_data.get('unit_price', 0),
                    item_specification=item_data.get('item_specification'),
                    item_model=item_data.get('item_model'),
                    line_status='active',
                    source_request_order_no=item_data.get('source_request_order_no'),
                    source_detail_id=item_data.get('source_detail_id')
                )

                item.line_subtotal_int = int(item.item_quantity * item.unit_price)
                subtotal += item.line_subtotal_int

                po.items.append(item)

                # If this item is linked to a requisition item, update its status
                if item_data.get('source_detail_id'):
                    req_item = RequestOrderItem.query.get(item_data['source_detail_id'])
                    if req_item:
                        req_item.item_status = 'order_created'

        # Set totals
        po.subtotal_int = subtotal
        po.tax_decimal1 = subtotal * 0.05  # 5% tax
        po.grand_total_int = subtotal + po.tax_decimal1

        db.session.add(po)
        db.session.commit()

        return create_response(
            data=po.to_dict(),
            message='Purchase order created successfully'
        )
    except Exception as e:
        db.session.rollback()
        return create_error_response(str(e), 500)

@bp.route('/build-candidates', methods=['GET'])
@procurement_required
def get_build_candidates(current_user):
    """Get approved items grouped by supplier for PO creation - 支援加急標記"""
    try:
        supplier_id = request.args.get('supplier_id')

        # 查詢時連接請購單主表以取得加急資訊
        from app.models.request_order import RequestOrder
        query = db.session.query(RequestOrderItem, RequestOrder.is_urgent).join(
            RequestOrder, RequestOrderItem.request_order_no == RequestOrder.request_order_no
        ).filter(RequestOrderItem.item_status == 'approved')

        if supplier_id:
            query = query.filter(RequestOrderItem.supplier_id == supplier_id)

        results = query.all()

        # Group by supplier
        suppliers = {}
        for item, is_urgent in results:
            if item.supplier_id not in suppliers:
                suppliers[item.supplier_id] = {
                    'supplier_id': item.supplier_id,
                    'supplier': item.supplier.to_summary_dict() if item.supplier else None,
                    'has_urgent_items': False,
                    'items': []
                }

            # 標記供應商是否有加急項目
            if is_urgent:
                suppliers[item.supplier_id]['has_urgent_items'] = True

            item_dict = item.to_dict()
            item_dict['is_urgent'] = is_urgent
            suppliers[item.supplier_id]['items'].append(item_dict)

        return create_response(list(suppliers.values()))

    except Exception as e:
        return create_error_response(
            'BUILD_CANDIDATES_ERROR',
            'Failed to get build candidates',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/<po_no>', methods=['GET'])
@authenticated_required
def get_purchase_order(current_user, po_no):
    """Get a single purchase order by PO number"""
    try:
        po = PurchaseOrder.query.filter_by(purchase_order_no=po_no).first()
        if not po:
            return create_error_response(
                'PO_NOT_FOUND',
                'Purchase order not found',
                status_code=404
            )

        po_dict = po.to_dict(include_user_details=True)  # Include user details to show 製單人 and 採購人

        # Add supplier info
        if po.supplier:
            po_dict['supplier'] = po.supplier.to_summary_dict()

        # Add items info
        po_dict['items'] = [item.to_dict() for item in po.items]

        return create_response(
            data={'data': po_dict},
            message='Purchase order fetched successfully'
        )
    except Exception as e:
        return create_error_response(
            'GET_PO_ERROR',
            'Failed to get purchase order',
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
    from datetime import datetime
    print(f"[EXPORT_API] Export request for {po_no} at {datetime.now().strftime('%H:%M:%S')}")
    try:
        po = PurchaseOrder.query.get_or_404(po_no)
        data = request.get_json()
        format_type = data.get('format', 'print').lower()
        print(f"[EXPORT_API] Format type: {format_type}")
        
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
        
        else:  # print format - return HTML for printing
            print(f"[EXPORT_API] Using HTML generator for print format")
            html_generator = POHTMLGenerator()
            html_content = html_generator.generate_html(po)

            db.session.commit()

            # Return HTML response optimized for printing
            return Response(
                html_content,
                mimetype='text/html',
                headers={
                    'Content-Type': 'text/html; charset=utf-8',
                }
            )
        
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
                po_dict['output_date'] = po.updated_at.isoformat() if po.updated_at and hasattr(po.updated_at, 'isoformat') else str(po.updated_at) if po.updated_at else None
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

            # Also update the linked requisition item status
            if item.source_detail_id:
                req_item = RequestOrderItem.query.get(item.source_detail_id)
                if req_item:
                    req_item.item_status = 'purchased'
                    req_item.updated_at = datetime.utcnow()

        db.session.commit()

        po_dict = po.to_dict()
        po_dict['confirmed_by'] = current_user.chinese_name
        po_dict['confirmed_at'] = po.updated_at.isoformat() if po.updated_at and hasattr(po.updated_at, 'isoformat') else str(po.updated_at) if po.updated_at else None
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

@bp.route('/<po_no>', methods=['PUT'])
@procurement_required
def update_purchase_order(current_user, po_no):
    """Update purchase order details"""
    try:
        po = PurchaseOrder.query.get_or_404(po_no)
        data = request.get_json()

        # Update allowed fields
        if 'quotation_no' in data:
            po.quotation_no = data['quotation_no']
        if 'notes' in data:
            po.notes = data['notes']
        if 'delivery_address' in data:
            po.delivery_address = data['delivery_address']

        # Update timestamp
        po.updated_at = datetime.utcnow()

        db.session.commit()

        return create_response(
            data=po.to_dict(),
            message='Purchase order updated successfully'
        )
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'UPDATE_PO_ERROR',
            'Failed to update purchase order',
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