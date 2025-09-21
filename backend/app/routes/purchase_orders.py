from flask import Blueprint, request, jsonify, send_file, Response
from app import db
from sqlalchemy import text
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
import math
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('purchase_orders', __name__, url_prefix='/api/v1/po')

@bp.before_request
def log_request():
    """Log all incoming requests for debugging"""
    logger.info(f"[PO_API] {request.method} {request.path} - Headers: {dict(request.headers)} - Data: {request.get_data(as_text=True)[:1000]}")

@bp.route('', methods=['GET'])
@bp.route('/', methods=['GET'])
@authenticated_required
def get_purchase_orders(current_user):
    """Get purchase orders list with filters using raw SQL"""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        supplier = request.args.get('supplier', '')
        status = request.args.get('status', '')

        # Build WHERE clause
        where_conditions = []
        params = {}

        if supplier:
            where_conditions.append("po.supplier_id = :supplier")
            params['supplier'] = supplier
        if status:
            where_conditions.append("po.purchase_status = :status")
            params['status'] = status

        where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""

        # Get total count
        count_query = text(f"""
            SELECT COUNT(*) as total
            FROM purchase_orders po
            {where_clause}
        """)

        total_count = db.session.execute(count_query, params).scalar()

        # Calculate offset and pages
        offset = (page - 1) * page_size
        total_pages = math.ceil(total_count / page_size) if page_size > 0 else 1

        # Get purchase orders with raw SQL
        query = text(f"""
            SELECT
                po.purchase_order_no,
                po.supplier_id,
                po.supplier_name,
                po.supplier_address,
                po.contact_phone,
                po.contact_person,
                po.supplier_tax_id,
                po.order_date,
                po.quotation_no,
                po.delivery_address,
                po.creation_date,
                po.creator_id,
                po.output_person_id,
                po.notes,
                po.confirm_purchaser_id,
                po.purchase_status,
                po.shipping_status,
                po.shipped_at,
                po.eta_date,
                po.arrival_date,
                po.carrier,
                po.tracking_no,
                po.logistics_note,
                po.delivery_status,
                po.expected_delivery_date,
                po.actual_delivery_date,
                po.consolidation_id,
                po.remarks,
                po.status_update_required,
                po.subtotal_int,
                po.tax_decimal1,
                po.grand_total_int,
                po.billing_status,
                po.payment_method,
                po.due_date,
                po.billed_month,
                po.payment_date,
                po.payment_note,
                po.created_at,
                po.updated_at,
                u1.chinese_name as creator_name,
                u1.username as creator_username,
                u2.chinese_name as output_person_name,
                u2.username as output_person_username,
                u3.chinese_name as confirm_purchaser_name,
                u3.username as confirm_purchaser_username,
                s.supplier_name_zh,
                s.supplier_name_en,
                s.supplier_email,
                s.supplier_region,
                s.payment_terms
            FROM purchase_orders po
            LEFT JOIN users u1 ON po.creator_id = u1.user_id
            LEFT JOIN users u2 ON po.output_person_id = u2.user_id
            LEFT JOIN users u3 ON po.confirm_purchaser_id = u3.user_id
            LEFT JOIN suppliers s ON po.supplier_id = s.supplier_id
            {where_clause}
            ORDER BY po.purchase_order_no DESC
            LIMIT :limit OFFSET :offset
        """)

        params['limit'] = page_size
        params['offset'] = offset

        results = db.session.execute(query, params).fetchall()

        # Convert results to dictionaries
        purchase_orders = []
        for row in results:
            po_dict = {
                'purchase_order_no': row.purchase_order_no,
                'supplier_id': row.supplier_id,
                'supplier_name': row.supplier_name,
                'supplier_address': row.supplier_address,
                'contact_phone': row.contact_phone,
                'contact_person': row.contact_person,
                'supplier_tax_id': row.supplier_tax_id,
                'order_date': str(row.order_date) if row.order_date else None,
                'quotation_no': row.quotation_no,
                'delivery_address': row.delivery_address,
                'creation_date': str(row.creation_date) if row.creation_date else None,
                'creator_id': row.creator_id,
                'output_person_id': row.output_person_id,
                'notes': row.notes,
                'confirm_purchaser_id': row.confirm_purchaser_id,
                'purchase_status': row.purchase_status,
                'shipping_status': row.shipping_status,
                'shipped_at': str(row.shipped_at) if row.shipped_at else None,
                'eta_date': str(row.eta_date) if row.eta_date else None,
                'arrival_date': str(row.arrival_date) if row.arrival_date else None,
                'carrier': row.carrier,
                'tracking_no': row.tracking_no,
                'logistics_note': row.logistics_note,
                'delivery_status': row.delivery_status,
                'expected_delivery_date': str(row.expected_delivery_date) if row.expected_delivery_date else None,
                'actual_delivery_date': str(row.actual_delivery_date) if row.actual_delivery_date else None,
                'consolidation_id': row.consolidation_id,
                'remarks': row.remarks,
                'status_update_required': row.status_update_required,
                'subtotal_int': row.subtotal_int,
                'tax_decimal1': float(row.tax_decimal1) if row.tax_decimal1 else 0.0,
                'grand_total_int': row.grand_total_int,
                'billing_status': row.billing_status,
                'payment_method': row.payment_method,
                'due_date': str(row.due_date) if row.due_date else None,
                'billed_month': row.billed_month,
                'payment_date': str(row.payment_date) if row.payment_date else None,
                'payment_note': row.payment_note,
                'created_at': str(row.created_at) if row.created_at else None,
                'updated_at': str(row.updated_at) if row.updated_at else None,
                'creator_name': row.creator_name,
                'creator_username': row.creator_username,
                'output_person_name': row.output_person_name,
                'output_person_username': row.output_person_username,
                'confirm_purchaser_name': row.confirm_purchaser_name,
                'confirm_purchaser_username': row.confirm_purchaser_username,
            }

            # Add supplier info if available
            if row.supplier_name_zh:
                po_dict['supplier'] = {
                    'supplier_id': row.supplier_id,
                    'supplier_name_zh': row.supplier_name_zh,
                    'supplier_name_en': row.supplier_name_en,
                    'supplier_email': row.supplier_email,
                    'supplier_region': row.supplier_region,
                    'payment_terms': row.payment_terms
                }

            purchase_orders.append(po_dict)

        return create_response({
            'items': purchase_orders,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total_count,
                'pages': total_pages
            }
        }, message='Purchase orders fetched successfully')
    except Exception as e:
        import traceback
        traceback.print_exc()
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

        # Log the incoming request for debugging
        logger.info(f"[CREATE_PO] Request data: {data}")

        # Validate required fields
        if not data:
            return create_error_response(
                'INVALID_REQUEST',
                'No data provided',
                status_code=400
            )

        if 'supplier_id' not in data:
            return create_error_response(
                'MISSING_SUPPLIER',
                'supplier_id is required',
                status_code=400
            )

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
            logger.error(f"[CREATE_PO] Supplier not found: {data['supplier_id']}")
            return create_error_response(
                'SUPPLIER_NOT_FOUND',
                f"Supplier with ID '{data['supplier_id']}' not found",
                status_code=400
            )

        # Create purchase order
        po = PurchaseOrder(
            purchase_order_no=po_no,
            supplier_id=data['supplier_id'],
            supplier_name=supplier.supplier_name_zh or supplier.supplier_name_en or '',
            supplier_address=data.get('supplier_address', supplier.supplier_address),
            contact_phone=data.get('contact_phone', supplier.supplier_phone),
            contact_person=data.get('contact_person', supplier.supplier_contact_person),
            supplier_tax_id=data.get('supplier_tax_id', supplier.supplier_tax_id),
            order_date=datetime.now().date(),
            quotation_no=data.get('quotation_no'),
            delivery_address=data.get('delivery_address'),
            creation_date=datetime.now().date(),
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

        # Validate that we have items/lines
        if not items_data:
            logger.error("[CREATE_PO] No items or lines provided in request")
            return create_error_response(
                'NO_ITEMS',
                'At least one item or line is required to create a purchase order',
                status_code=400
            )

        # Track items added
        items_added = 0

        # If lines format is used (from build candidates)
        if 'lines' in data and items_data:
            # Load the requisition items by detail_id
            for line in items_data:
                req_item = RequestOrderItem.query.get(line['detail_id'])
                if not req_item:
                    logger.warning(f"[CREATE_PO] Requisition item not found: detail_id={line['detail_id']}")
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
                items_added += 1

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
                items_added += 1

                # If this item is linked to a requisition item, update its status
                if item_data.get('source_detail_id'):
                    req_item = RequestOrderItem.query.get(item_data['source_detail_id'])
                    if req_item:
                        req_item.item_status = 'order_created'

        # Check if we have any items added
        if not po.items:
            logger.error("[CREATE_PO] No valid items were added to the purchase order")
            return create_error_response(
                'NO_VALID_ITEMS',
                'No valid items could be added to the purchase order. Items may not exist or are in invalid status.',
                status_code=400
            )

        # Set totals
        po.subtotal_int = subtotal
        po.tax_decimal1 = subtotal * 0.05  # 5% tax
        po.grand_total_int = subtotal + po.tax_decimal1

        logger.info(f"[CREATE_PO] Successfully created PO {po_no} with {items_added} items")

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