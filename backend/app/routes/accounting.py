from flask import Blueprint, request, jsonify
from app import db
from app.models.purchase_order import PurchaseOrder
from app.models.supplier import Supplier
from app.auth import accountant_required, authenticated_required, create_response, create_error_response, paginate_query
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
import re

bp = Blueprint('accounting', __name__, url_prefix='/api/v1/accounting')

# Helper functions for invoice management
def calculate_invoice_date_range(supplier, month_date):
    """Calculate date range for invoice based on supplier payment terms"""
    payment_days = extract_payment_days(supplier.payment_terms)

    if payment_days == 30:
        # 30天條件：當月26日到次月25日
        if month_date.day <= 25:
            # 如果是7月請款，搜尋6/26~7/25的採購單
            prev_month = month_date - relativedelta(months=1)
            start_date = prev_month.replace(day=26)
            end_date = month_date.replace(day=25)
        else:
            # 如果是7月26日後請款，搜尋7/26~8/25的採購單
            start_date = month_date.replace(day=26)
            next_month = month_date + relativedelta(months=1)
            end_date = next_month.replace(day=25)
    elif payment_days == 60:
        # 60天條件：前月1日到當月25日
        prev_month = month_date - relativedelta(months=1)
        start_date = prev_month.replace(day=1)
        end_date = month_date.replace(day=25)
    else:
        # 其他條件：當月1日到當月底
        start_date = month_date.replace(day=1)
        end_date = (month_date + relativedelta(months=1) - relativedelta(days=1))

    # Calculate due date
    due_date = end_date + relativedelta(days=payment_days)

    return start_date, end_date, due_date

def extract_payment_days(payment_terms):
    """Extract payment days from payment terms string"""
    if not payment_terms:
        return 30  # Default to 30 days

    # Try to extract number from payment terms
    match = re.search(r'(\d+)', str(payment_terms))
    if match:
        return int(match.group(1))

    return 30  # Default to 30 days

@bp.route('/invoice-management/search', methods=['GET', 'OPTIONS'])
def search_purchase_orders_for_invoice():
    """Search purchase orders for invoice management"""
    # Handle OPTIONS preflight request (no authentication needed)
    if request.method == 'OPTIONS':
        return '', 200

    # For GET requests, manually handle authentication
    from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
    from app.models.user import User

    try:
        # This will validate the JWT token
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if not current_user or not current_user.is_active:
            return create_error_response(
                'INVALID_USER',
                'User not found or inactive',
                status_code=401
            )
    except Exception as e:
        return create_error_response(
            'AUTHENTICATION_ERROR',
            'Authentication failed',
            {'error': str(e)},
            status_code=401
        )

    # Call the main processing function
    return authenticate_and_process()

def authenticate_and_process():
    """Process the actual request after authentication"""
    # Authentication is already verified above
    from flask_jwt_extended import get_jwt_identity
    from app.models.user import User

    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    try:
        # Support both supplier_id and supplier_name for backward compatibility
        supplier_id = request.args.get('supplier_id')
        supplier_name = request.args.get('supplier_name')
        invoice_month = request.args.get('invoice_month')  # YYYY-MM format

        if not (supplier_id or supplier_name) or not invoice_month:
            return create_error_response(
                'MISSING_PARAMETERS',
                'Either supplier_id or supplier_name is required, along with invoice_month',
                status_code=400
            )

        # Parse month
        try:
            month_date = datetime.strptime(invoice_month, '%Y-%m').date()
        except ValueError:
            return create_error_response(
                'INVALID_MONTH',
                'invoice_month must be in YYYY-MM format',
                status_code=400
            )

        # Get supplier - support both ID and name lookup
        supplier = None
        if supplier_id:
            # Direct ID lookup (existing behavior)
            supplier = Supplier.query.get(supplier_id)
        elif supplier_name:
            # Name lookup with partial matching
            supplier = Supplier.query.filter(
                db.or_(
                    Supplier.supplier_name_zh.ilike(f'%{supplier_name}%'),
                    Supplier.supplier_name_en.ilike(f'%{supplier_name}%')
                )
            ).first()

        if not supplier:
            search_param = supplier_id if supplier_id else supplier_name
            return create_error_response(
                'SUPPLIER_NOT_FOUND',
                f'Supplier "{search_param}" not found',
                status_code=404
            )

        # Use the found supplier's ID for the query
        actual_supplier_id = supplier.supplier_id

        # Calculate date range based on payment terms
        start_date, end_date, due_date = calculate_invoice_date_range(supplier, month_date)

        # Query purchase orders using the actual supplier ID
        # IMPORTANT: Exclude paid orders from invoice management
        query = PurchaseOrder.query.filter(
            PurchaseOrder.supplier_id == actual_supplier_id,
            PurchaseOrder.created_at >= start_date,
            PurchaseOrder.created_at <= end_date,
            PurchaseOrder.purchase_status.in_(['purchase_confirmed', 'partial_received', 'received', 'closed', 'purchased']),
            PurchaseOrder.billing_status != 'paid'  # Exclude paid orders
        ).order_by(PurchaseOrder.created_at.desc())

        # Get all purchase orders
        purchase_orders = query.all()

        # Prepare response with items included
        po_list_with_items = []
        for po in purchase_orders:
            po_dict = po.to_dict()
            # Add items to each purchase order
            po_dict['items'] = [item.to_dict() for item in po.items]
            po_dict['item_count'] = po.items.count()
            po_list_with_items.append(po_dict)

        result = {
            'supplier': supplier.to_dict(),
            'date_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'due_date': due_date.isoformat(),
                'payment_days': extract_payment_days(supplier.payment_terms)
            },
            'purchase_orders': po_list_with_items,
            'summary': {
                'total_orders': len(purchase_orders),
                'total_amount': sum(po.grand_total_int for po in purchase_orders)
            }
        }

        return create_response(result)

    except Exception as e:
        return create_error_response(
            'SEARCH_ERROR',
            'Failed to search purchase orders',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/invoice-management/export', methods=['POST'])
@authenticated_required
def export_invoice_data(current_user):
    """Export invoice data to Excel format"""
    try:
        data = request.get_json()

        # Get the purchase order IDs to export
        po_ids = data.get('purchase_order_ids', [])

        if not po_ids:
            return create_error_response(
                'NO_DATA',
                'No purchase orders to export',
                status_code=400
            )

        # Query purchase orders
        purchase_orders = PurchaseOrder.query.filter(
            PurchaseOrder.purchase_order_no.in_(po_ids)
        ).all()

        # Prepare export data
        export_data = []
        for po in purchase_orders:
            for item in po.items:
                export_data.append({
                    '採購單號': po.purchase_order_no,
                    '供應商': po.supplier.supplier_name_zh if po.supplier else '',
                    '項目名稱': item.item_name,
                    '規格': item.item_specification,
                    '數量': item.item_quantity,
                    '單位': item.item_unit,
                    '單價': item.unit_price,
                    '小計': item.line_subtotal,
                    '狀態': po.purchase_status,
                    '建立日期': po.created_at.strftime('%Y-%m-%d'),
                    '確認日期': po.confirm_purchase_date.strftime('%Y-%m-%d') if po.confirm_purchase_date else ''
                })

        return create_response({'export_data': export_data})

    except Exception as e:
        return create_error_response(
            'EXPORT_ERROR',
            'Failed to export invoice data',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/billing/candidates', methods=['GET'])
@accountant_required
def get_billing_candidates(current_user):
    """Get unbilled purchase orders for supplier billing"""
    try:
        supplier_id = request.args.get('supplier_id')
        month_str = request.args.get('month')  # YYYY-MM format
        
        if not supplier_id or not month_str:
            return create_error_response(
                'MISSING_PARAMETERS',
                'supplier_id and month are required',
                status_code=400
            )
        
        try:
            month_date = datetime.strptime(month_str, '%Y-%m').date()
        except ValueError:
            return create_error_response(
                'INVALID_MONTH',
                'Month must be in YYYY-MM format',
                status_code=400
            )
        
        # Get supplier to check payment terms
        supplier = Supplier.query.get_or_404(supplier_id)
        
        # Determine billing period based on payment terms
        # 30天: current month only
        # 60天: current month + previous month
        start_date = month_date.replace(day=1)
        if '60' in str(supplier.payment_terms):
            start_date = start_date - relativedelta(months=1)
        
        end_date = month_date.replace(day=25)  # 25th cutoff
        if month_date.day > 25:
            # If after 25th, include next month's purchases up to 25th
            end_date = (month_date + relativedelta(months=1)).replace(day=25)
        
        # Query unbilled POs
        query = PurchaseOrder.query.filter(
            PurchaseOrder.supplier_id == supplier_id,
            PurchaseOrder.purchase_status == 'purchased',
            PurchaseOrder.billing_status == 'none',
            PurchaseOrder.order_date >= start_date,
            PurchaseOrder.order_date <= end_date
        ).order_by(PurchaseOrder.order_date)
        
        pos = query.all()
        
        # Calculate totals
        total_subtotal = sum(po.subtotal_int for po in pos)
        total_tax = sum(float(po.tax_decimal1) for po in pos)
        total_grand = sum(po.grand_total_int for po in pos)
        
        return create_response({
            'supplier': supplier.to_summary_dict(),
            'month': month_str,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'purchase_orders': [po.to_dict() for po in pos],
            'summary': {
                'total_subtotal': total_subtotal,
                'total_tax': round(total_tax, 1),
                'total_grand': total_grand,
                'count': len(pos)
            }
        })
        
    except Exception as e:
        return create_error_response(
            'BILLING_CANDIDATES_ERROR',
            'Failed to get billing candidates',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/billing', methods=['POST'])
@accountant_required
def generate_billing(current_user):
    """Generate billing batch for supplier with payment terms"""
    try:
        data = request.get_json()
        
        required_fields = ['supplier_id', 'month', 'term', 'po_list']
        for field in required_fields:
            if field not in data:
                return create_error_response(
                    'MISSING_FIELD',
                    f'{field} is required',
                    status_code=400
                )
        
        supplier_id = data['supplier_id']
        month_str = data['month']
        term = data['term']  # Payment term in days
        po_numbers = data['po_list']
        
        # Optional adjustments
        discount = Decimal(str(data.get('discount', 0)))
        other_deduction = Decimal(str(data.get('other_deduction', 0)))
        invoice_or_receipt = data.get('invoice_or_receipt', '')
        
        # Validate and get POs
        pos = []
        for po_no in po_numbers:
            po = PurchaseOrder.query.filter_by(
                purchase_order_no=po_no,
                supplier_id=supplier_id,
                billing_status='none'
            ).first()
            
            if not po:
                return create_error_response(
                    'INVALID_PO',
                    f'PO {po_no} not found or already billed',
                    status_code=400
                )
            pos.append(po)
        
        # Calculate billing amounts
        total_subtotal = sum(po.subtotal_int for po in pos)
        total_tax = sum(po.tax_decimal1 for po in pos)
        total_grand = sum(po.grand_total_int for po in pos)
        
        # Apply adjustments
        billed_amount = Decimal(total_grand) - discount - other_deduction
        
        # Calculate due date (end of month + payment term)
        month_date = datetime.strptime(month_str, '%Y-%m').date()
        month_end = (month_date + relativedelta(months=1) - relativedelta(days=1))
        due_date = month_end + relativedelta(days=term)
        
        # Update POs
        for po in pos:
            po.billing_status = 'billed'
            po.billed_month = month_str
            po.due_date = due_date
        
        db.session.commit()
        
        # Return billing summary
        billing_summary = {
            'supplier_id': supplier_id,
            'month': month_str,
            'term': term,
            'due_date': due_date.isoformat(),
            'po_count': len(pos),
            'po_numbers': po_numbers,
            'amounts': {
                'subtotal': total_subtotal,
                'tax': float(total_tax),
                'grand_total': total_grand,
                'discount': float(discount),
                'other_deduction': float(other_deduction),
                'billed_amount': float(billed_amount)
            },
            'invoice_or_receipt': invoice_or_receipt,
            'created_by': current_user.chinese_name,
            'created_at': datetime.utcnow().isoformat()
        }
        
        return create_response(billing_summary, status_code=201)
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'BILLING_GENERATE_ERROR',
            'Failed to generate billing',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/billing/<billing_id>/mark-paid', methods=['POST'])
@accountant_required
def mark_batch_paid(current_user, billing_id):
    """Mark billing batch as paid (idempotent)"""
    try:
        data = request.get_json()
        
        required_fields = ['method', 'pay_date']
        for field in required_fields:
            if field not in data:
                return create_error_response(
                    'MISSING_FIELD',
                    f'{field} is required',
                    status_code=400
                )
        
        method = data['method']
        pay_date_str = data['pay_date']
        
        # Validate payment method
        valid_methods = ['remittance', 'check', 'cash']
        if method not in valid_methods:
            return create_error_response(
                'INVALID_METHOD',
                f'Payment method must be one of: {", ".join(valid_methods)}',
                status_code=400
            )
        
        try:
            pay_date = datetime.strptime(pay_date_str, '%Y-%m-%d').date()
        except ValueError:
            return create_error_response(
                'INVALID_DATE',
                'pay_date must be in YYYY-MM-DD format',
                status_code=400
            )
        
        # For this implementation, billing_id is treated as supplier_id-month
        # In a real system, you'd have a separate billing batches table
        try:
            supplier_id, month = billing_id.split('-', 1)
        except ValueError:
            return create_error_response(
                'INVALID_BILLING_ID',
                'Invalid billing ID format',
                status_code=400
            )
        
        # Find all billed POs for this supplier and month
        pos = PurchaseOrder.query.filter(
            PurchaseOrder.supplier_id == supplier_id,
            PurchaseOrder.billed_month == month,
            PurchaseOrder.billing_status == 'billed'
        ).all()
        
        if not pos:
            return create_error_response(
                'BILLING_NOT_FOUND',
                'Billing batch not found',
                status_code=404
            )
        
        # Check idempotency - if already paid, return success
        already_paid = all(po.billing_status == 'paid' for po in pos)
        if already_paid:
            return create_response({
                'message': 'Billing batch already marked as paid',
                'po_count': len(pos)
            })
        
        # Mark all POs as paid
        for po in pos:
            po.billing_status = 'paid'
            po.payment_method = method
        
        db.session.commit()
        
        return create_response({
            'message': 'Billing batch marked as paid',
            'supplier_id': supplier_id,
            'month': month,
            'po_count': len(pos),
            'payment_method': method,
            'pay_date': pay_date.isoformat()
        })
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'MARK_PAID_ERROR',
            'Failed to mark batch as paid',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/po/<po_no>/mark-paid', methods=['POST'])
@accountant_required
def mark_po_paid(current_user, po_no):
    """Mark individual PO as paid"""
    try:
        po = PurchaseOrder.query.get_or_404(po_no)
        
        if po.billing_status == 'paid':
            return create_response({
                'message': 'PO already marked as paid',
                'po_no': po_no
            })
        
        data = request.get_json()
        
        required_fields = ['method', 'pay_date']
        for field in required_fields:
            if field not in data:
                return create_error_response(
                    'MISSING_FIELD',
                    f'{field} is required',
                    status_code=400
                )
        
        method = data['method']
        pay_date_str = data['pay_date']
        
        # Validate payment method
        valid_methods = ['remittance', 'check', 'cash']
        if method not in valid_methods:
            return create_error_response(
                'INVALID_METHOD',
                f'Payment method must be one of: {", ".join(valid_methods)}',
                status_code=400
            )
        
        try:
            pay_date = datetime.strptime(pay_date_str, '%Y-%m-%d').date()
        except ValueError:
            return create_error_response(
                'INVALID_DATE',
                'pay_date must be in YYYY-MM-DD format',
                status_code=400
            )
        
        # Mark PO as paid
        po.billing_status = 'paid'
        po.payment_method = method
        
        db.session.commit()
        
        return create_response({
            'message': 'PO marked as paid',
            'po_no': po_no,
            'payment_method': method,
            'pay_date': pay_date.isoformat(),
            'amount': po.grand_total_int
        })
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'MARK_PO_PAID_ERROR',
            'Failed to mark PO as paid',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/history', methods=['GET'])
@accountant_required
def get_payment_history(current_user):
    """Get payment history with filtering"""
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        supplier_id = request.args.get('supplier_id')
        month = request.args.get('month')
        paid = request.args.get('paid')
        
        query = PurchaseOrder.query.filter(
            PurchaseOrder.billing_status.in_(['billed', 'paid'])
        )
        
        if supplier_id:
            query = query.filter(PurchaseOrder.supplier_id == supplier_id)
        if month:
            query = query.filter(PurchaseOrder.billed_month == month)
        if paid is not None:
            status = 'paid' if paid.lower() == 'true' else 'billed'
            query = query.filter(PurchaseOrder.billing_status == status)
        
        query = query.order_by(PurchaseOrder.due_date.desc(), PurchaseOrder.created_at.desc())
        result = paginate_query(query, page, page_size)
        
        return jsonify({
            'items': [po.to_dict() for po in result['items']],
            'pagination': result['pagination']
        }), 200
        
    except Exception as e:
        return create_error_response(
            'PAYMENT_HISTORY_ERROR',
            'Failed to get payment history',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/reports/summary', methods=['GET'])
@accountant_required
def get_accounting_summary(current_user):
    """Get accounting summary for dashboard"""
    try:
        # Get counts and amounts
        unpaid_count = PurchaseOrder.query.filter_by(billing_status='none', purchase_status='purchased').count()
        billed_count = PurchaseOrder.query.filter_by(billing_status='billed').count()
        paid_count = PurchaseOrder.query.filter_by(billing_status='paid').count()

        # Get amounts
        unpaid_amount = db.session.query(
            db.func.sum(PurchaseOrder.grand_total_int)
        ).filter_by(billing_status='none', purchase_status='purchased').scalar() or 0

        billed_amount = db.session.query(
            db.func.sum(PurchaseOrder.grand_total_int)
        ).filter_by(billing_status='billed').scalar() or 0

        paid_amount = db.session.query(
            db.func.sum(PurchaseOrder.grand_total_int)
        ).filter_by(billing_status='paid').scalar() or 0

        return create_response({
            'unpaid': {
                'count': unpaid_count,
                'amount': unpaid_amount
            },
            'billed': {
                'count': billed_count,
                'amount': billed_amount
            },
            'paid': {
                'count': paid_count,
                'amount': paid_amount
            },
            'total': {
                'count': unpaid_count + billed_count + paid_count,
                'amount': unpaid_amount + billed_amount + paid_amount
            }
        })

    except Exception as e:
        return create_error_response(
            'SUMMARY_ERROR',
            'Failed to get accounting summary',
            {'error': str(e)},
            status_code=500
        )

# Invoice Management Routes
@bp.route('/invoice-management/search2', methods=['GET'])
@accountant_required
def search_purchase_orders_for_invoice_old(current_user):
    """
    Search purchase orders for invoice verification
    根據供應商和月份搜尋採購單，用於請款單查核對照
    """
    try:
        supplier_id = request.args.get('supplier_id')
        month_str = request.args.get('month')  # YYYY-MM format

        # Validate required parameters
        if not supplier_id or not month_str:
            return create_error_response(
                'MISSING_PARAMETERS',
                'supplier_id and month are required',
                status_code=400
            )

        try:
            month_date = datetime.strptime(month_str, '%Y-%m').date()
        except ValueError:
            return create_error_response(
                'INVALID_MONTH',
                'Month must be in YYYY-MM format',
                status_code=400
            )

        # Get supplier to extract payment terms
        supplier = Supplier.query.get_or_404(supplier_id)

        # Calculate smart date range based on payment terms
        start_date, end_date, due_date = calculate_invoice_date_range(supplier, month_date)

        # Query purchase orders in the calculated range
        query = PurchaseOrder.query.filter(
            PurchaseOrder.supplier_id == supplier_id,
            PurchaseOrder.purchase_status.in_(['purchased', 'shipped', 'outputted']),
            PurchaseOrder.order_date >= start_date,
            PurchaseOrder.order_date <= end_date
        ).order_by(PurchaseOrder.order_date.asc())

        pos = query.all()

        # Calculate totals
        total_amount = sum(po.grand_total_int for po in pos)
        total_tax = sum(float(po.tax_decimal1 or 0) for po in pos)

        return create_response({
            'supplier': supplier.to_summary_dict(),
            'month': month_str,
            'search_period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'due_date': due_date.isoformat(),
                'payment_terms': supplier.payment_terms
            },
            'purchase_orders': [po.to_dict() for po in pos],
            'summary': {
                'total_amount': total_amount,
                'total_tax': round(total_tax, 1),
                'count': len(pos),
                'avg_amount': round(total_amount / len(pos) if pos else 0, 2)
            }
        })

    except Exception as e:
        return create_error_response(
            'INVOICE_SEARCH_ERROR',
            'Failed to search purchase orders for invoice',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/invoice-management/export2', methods=['POST'])
@accountant_required
def export_invoice_excel_old(current_user):
    """
    Export invoice verification data to Excel
    匯出請款單查核資料為Excel格式
    """
    try:
        data = request.get_json()

        required_fields = ['supplier_id', 'month', 'po_numbers']
        for field in required_fields:
            if field not in data:
                return create_error_response(
                    'MISSING_FIELD',
                    f'{field} is required',
                    status_code=400
                )

        supplier_id = data['supplier_id']
        month_str = data['month']
        po_numbers = data['po_numbers']

        # Get supplier and POs
        supplier = Supplier.query.get_or_404(supplier_id)

        pos = []
        for po_no in po_numbers:
            po = PurchaseOrder.query.get(po_no)
            if po and po.supplier_id == supplier_id:
                pos.append(po)

        if not pos:
            return create_error_response(
                'NO_POS_FOUND',
                'No valid purchase orders found',
                status_code=400
            )

        # Calculate date range
        month_date = datetime.strptime(month_str, '%Y-%m').date()
        start_date, end_date, due_date = calculate_invoice_date_range(supplier, month_date)

        # Prepare Excel data
        excel_data = {
            'export_info': {
                'supplier': supplier.to_dict(),
                'month': month_str,
                'search_period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'due_date': due_date.isoformat()
                },
                'exported_by': current_user.chinese_name,
                'export_date': datetime.now().isoformat()
            },
            'purchase_orders': [po.to_dict() for po in pos],
            'summary': {
                'total_amount': sum(po.grand_total_int for po in pos),
                'total_tax': sum(float(po.tax_decimal1 or 0) for po in pos),
                'count': len(pos)
            }
        }

        return create_response({
            'message': 'Excel data prepared successfully',
            'filename': f'invoice_verification_{supplier_id}_{month_str}.xlsx',
            'data': excel_data
        })

    except Exception as e:
        return create_error_response(
            'EXCEL_EXPORT_ERROR',
            'Failed to export invoice data to Excel',
            {'error': str(e)},
            status_code=500
        )

def calculate_invoice_date_range(supplier, month_date):
    """
    Calculate smart date range for invoice search based on payment terms
    根據付款條件計算智能搜尋日期範圍
    """
    # Extract payment days from payment terms
    payment_days = extract_payment_days(supplier.payment_terms)

    # Calculate search range
    # For 30-day terms: search from (month-start - payment_days + month_days) to month-25
    # For 60-day terms: search from (month-start - payment_days + month_days) to month-25

    month_start = month_date.replace(day=1)

    # Calculate start date: month start - (payment_days - days in previous month)
    if payment_days == 30:
        # 30天條件：7月請款 → 搜尋6/26~7/25
        start_date = month_start - relativedelta(days=(payment_days - 25))
    elif payment_days == 60:
        # 60天條件：7月請款 → 搜尋6/1~7/25
        start_date = month_start - relativedelta(days=(payment_days - 30))
    else:
        # Default: 30 days
        start_date = month_start - relativedelta(days=(30 - 25))

    # End date: 25th of the month (cutoff point)
    end_date = month_date.replace(day=25)

    # Due date: end of month + payment terms
    month_end = (month_start + relativedelta(months=1) - relativedelta(days=1))
    due_date = month_end + relativedelta(days=payment_days)

    return start_date, end_date, due_date

def extract_payment_days(payment_terms):
    """
    Extract payment days from payment terms string
    從付款條件字串中提取付款天數
    """
    if not payment_terms:
        return 30  # Default

    payment_terms_str = str(payment_terms).lower()

    if '60' in payment_terms_str or 'sixty' in payment_terms_str:
        return 60
    elif '30' in payment_terms_str or 'thirty' in payment_terms_str:
        return 30
    elif '90' in payment_terms_str or 'ninety' in payment_terms_str:
        return 90
    else:
        # Try to extract number from string
        import re
        numbers = re.findall(r'\d+', payment_terms_str)
        if numbers:
            return int(numbers[0])
        else:
            return 30  # Default fallback

# Payment Management Routes
@bp.route('/payment-management/list', methods=['GET', 'OPTIONS'])
def list_purchase_orders_for_payment():
    """List purchase orders available for payment management"""
    # Handle OPTIONS preflight request (no authentication needed)
    if request.method == 'OPTIONS':
        return '', 200

    # For GET requests, manually handle authentication
    from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
    from app.models.user import User

    try:
        # This will validate the JWT token
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if not current_user or not current_user.is_active:
            return create_error_response(
                'INVALID_USER',
                'User not found or inactive',
                status_code=401
            )
    except Exception as e:
        return create_error_response(
            'AUTHENTICATION_ERROR',
            'Authentication failed',
            {'error': str(e)},
            status_code=401
        )

    try:
        # Get filter parameters
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        supplier_id = request.args.get('supplier_id')
        status_filter = request.args.get('status', 'unpaid')  # 'unpaid', 'paid', 'all'

        # Build query
        query = PurchaseOrder.query.filter(
            PurchaseOrder.purchase_status == 'purchased'
        )

        # Filter by payment status
        if status_filter == 'unpaid':
            query = query.filter(
                db.or_(
                    PurchaseOrder.billing_status == 'none',
                    PurchaseOrder.billing_status == 'pending',
                    PurchaseOrder.billing_status == 'billed'
                )
            )
        elif status_filter == 'paid':
            query = query.filter(PurchaseOrder.billing_status == 'paid')
        # else 'all' - no additional filter

        # Filter by supplier if provided
        if supplier_id:
            query = query.filter(PurchaseOrder.supplier_id == supplier_id)

        # Order by created date
        query = query.order_by(PurchaseOrder.created_at.desc())

        # Paginate
        result = paginate_query(query, page, page_size)

        # Add supplier info to each PO
        pos_with_supplier = []
        for po in result['items']:
            po_dict = po.to_dict()
            if po.supplier:
                po_dict['supplier_info'] = {
                    'supplier_id': po.supplier.supplier_id,
                    'supplier_name_zh': po.supplier.supplier_name_zh,
                    'supplier_name_en': po.supplier.supplier_name_en,
                    'payment_terms': po.supplier.payment_terms
                }
            pos_with_supplier.append(po_dict)

        return create_response({
            'items': pos_with_supplier,
            'pagination': result['pagination']
        })

    except Exception as e:
        return create_error_response(
            'LIST_ERROR',
            'Failed to list purchase orders for payment',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/payment-management/update-payment', methods=['POST', 'OPTIONS'])
def update_payment_status():
    """Update payment status for purchase orders"""
    # Handle OPTIONS preflight request
    if request.method == 'OPTIONS':
        return '', 200

    # Authentication
    from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
    from app.models.user import User

    try:
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if not current_user or not current_user.is_active:
            return create_error_response(
                'INVALID_USER',
                'User not found or inactive',
                status_code=401
            )
    except Exception as e:
        return create_error_response(
            'AUTHENTICATION_ERROR',
            'Authentication failed',
            {'error': str(e)},
            status_code=401
        )

    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['purchase_order_nos', 'payment_method']
        for field in required_fields:
            if field not in data:
                return create_error_response(
                    'MISSING_FIELD',
                    f'{field} is required',
                    status_code=400
                )

        po_nos = data['purchase_order_nos']
        payment_method = data['payment_method']
        payment_note = data.get('payment_note', '')

        # Map Chinese payment methods to English for database
        method_mapping = {
            '電匯': 'remittance',
            '支票': 'check',
            'remittance': 'remittance',
            'check': 'check'
        }

        if payment_method not in method_mapping:
            return create_error_response(
                'INVALID_METHOD',
                f'Invalid payment method: {payment_method}',
                status_code=400
            )

        mapped_method = method_mapping[payment_method]

        # Update each purchase order
        updated_pos = []
        for po_no in po_nos:
            po = PurchaseOrder.query.get(po_no)
            if not po:
                continue

            # Check if already paid
            if po.billing_status == 'paid':
                continue

            # Update payment status
            po.billing_status = 'paid'
            po.payment_method = mapped_method
            po.payment_date = date.today()
            po.payment_note = payment_note

            updated_pos.append(po_no)

        db.session.commit()

        return create_response({
            'message': 'Payment status updated successfully',
            'updated_count': len(updated_pos),
            'updated_pos': updated_pos,
            'payment_method': payment_method,
            'payment_date': date.today().isoformat()
        })

    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'UPDATE_ERROR',
            'Failed to update payment status',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/payment-management/summary', methods=['GET', 'OPTIONS'])
def get_payment_summary():
    """Get payment summary statistics"""
    if request.method == 'OPTIONS':
        return '', 200

    # Authentication
    from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
    from app.models.user import User

    try:
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)

        if not current_user or not current_user.is_active:
            return create_error_response(
                'INVALID_USER',
                'User not found or inactive',
                status_code=401
            )
    except Exception as e:
        return create_error_response(
            'AUTHENTICATION_ERROR',
            'Authentication failed',
            {'error': str(e)},
            status_code=401
        )

    try:
        # Get counts and amounts for different statuses
        unpaid_query = PurchaseOrder.query.filter(
            PurchaseOrder.purchase_status == 'purchased',
            PurchaseOrder.billing_status != 'paid'
        )
        unpaid_count = unpaid_query.count()
        unpaid_amount = db.session.query(
            db.func.sum(PurchaseOrder.grand_total_int)
        ).filter(
            PurchaseOrder.purchase_status == 'purchased',
            PurchaseOrder.billing_status != 'paid'
        ).scalar() or 0

        paid_query = PurchaseOrder.query.filter(
            PurchaseOrder.billing_status == 'paid'
        )
        paid_count = paid_query.count()
        paid_amount = db.session.query(
            db.func.sum(PurchaseOrder.grand_total_int)
        ).filter(
            PurchaseOrder.billing_status == 'paid'
        ).scalar() or 0

        # Get payment method breakdown
        remittance_amount = db.session.query(
            db.func.sum(PurchaseOrder.grand_total_int)
        ).filter(
            PurchaseOrder.billing_status == 'paid',
            PurchaseOrder.payment_method == 'remittance'
        ).scalar() or 0

        check_amount = db.session.query(
            db.func.sum(PurchaseOrder.grand_total_int)
        ).filter(
            PurchaseOrder.billing_status == 'paid',
            PurchaseOrder.payment_method == 'check'
        ).scalar() or 0

        return create_response({
            'unpaid': {
                'count': unpaid_count,
                'amount': unpaid_amount
            },
            'paid': {
                'count': paid_count,
                'amount': paid_amount,
                'by_method': {
                    'remittance': remittance_amount,
                    'check': check_amount
                }
            },
            'total': {
                'count': unpaid_count + paid_count,
                'amount': unpaid_amount + paid_amount
            }
        })

    except Exception as e:
        return create_error_response(
            'SUMMARY_ERROR',
            'Failed to get payment summary',
            {'error': str(e)},
            status_code=500
        )