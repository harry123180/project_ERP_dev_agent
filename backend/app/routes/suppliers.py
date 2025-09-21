from flask import Blueprint, request, jsonify
from app import db
from app.models.supplier import Supplier
from app.auth import authenticated_required, procurement_required, create_response, create_error_response, paginate_query

bp = Blueprint('suppliers', __name__, url_prefix='/api/v1/suppliers')

@bp.route('', methods=['GET'])
@authenticated_required
def list_suppliers(current_user):
    """List suppliers with filtering"""
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        region = request.args.get('region')  # domestic, international
        active_only = request.args.get('active', 'true').lower() == 'true'
        search = request.args.get('q', '').strip()
        
        query = Supplier.query
        
        if region:
            query = query.filter(Supplier.supplier_region == region)
        if active_only:
            query = query.filter(Supplier.is_active == True)
        if search:
            query = query.filter(
                db.or_(
                    Supplier.supplier_name_zh.ilike(f'%{search}%'),
                    Supplier.supplier_name_en.ilike(f'%{search}%'),
                    Supplier.supplier_id.ilike(f'%{search}%')
                )
            )
        
        query = query.order_by(Supplier.supplier_name_zh)
        result = paginate_query(query, page, page_size)
        
        return jsonify({
            'items': [supplier.to_dict() for supplier in result['items']],
            'pagination': result['pagination']
        }), 200
        
    except Exception as e:
        return create_error_response(
            'SUPPLIER_LIST_ERROR',
            'Failed to fetch suppliers',
            {'error': str(e)},
            status_code=500
        )

@bp.route('', methods=['POST'])
@procurement_required
def create_supplier(current_user):
    """Create new supplier"""
    try:
        data = request.get_json()
        
        required_fields = ['supplier_id', 'supplier_name_zh', 'supplier_region']
        for field in required_fields:
            if not data.get(field):
                return create_error_response(
                    'MISSING_FIELD',
                    f'{field} is required',
                    status_code=400
                )
        
        # Check if supplier ID already exists
        if Supplier.query.get(data['supplier_id']):
            return create_error_response(
                'SUPPLIER_EXISTS',
                'Supplier ID already exists',
                status_code=400
            )
        
        # Validate region
        if data['supplier_region'] not in ['domestic', 'international']:
            return create_error_response(
                'INVALID_REGION',
                'Region must be domestic or international',
                status_code=400
            )
        
        supplier = Supplier(
            supplier_id=data['supplier_id'],
            supplier_name_zh=data['supplier_name_zh'],
            supplier_name_en=data.get('supplier_name_en'),
            supplier_address=data.get('supplier_address'),
            supplier_phone=data.get('supplier_phone'),
            supplier_email=data.get('supplier_email'),
            supplier_contact_person=data.get('supplier_contact_person'),
            supplier_tax_id=data.get('supplier_tax_id'),
            supplier_region=data['supplier_region'],
            supplier_remark=data.get('supplier_remark'),
            payment_terms=data.get('payment_terms'),
            bank_account=data.get('bank_account')
        )
        
        db.session.add(supplier)
        db.session.commit()
        
        return create_response(supplier.to_dict(), status_code=201)
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'SUPPLIER_CREATE_ERROR',
            'Failed to create supplier',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/<supplier_id>', methods=['GET'])
@authenticated_required
def get_supplier(current_user, supplier_id):
    """Get supplier details"""
    try:
        supplier = Supplier.query.get_or_404(supplier_id)
        return create_response(supplier.to_dict())
        
    except Exception as e:
        return create_error_response(
            'SUPPLIER_GET_ERROR',
            'Failed to get supplier',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/<supplier_id>', methods=['PUT'])
@procurement_required
def update_supplier(current_user, supplier_id):
    """Update supplier information"""
    try:
        supplier = Supplier.query.get_or_404(supplier_id)
        data = request.get_json()
        
        # Update allowed fields
        updateable_fields = [
            'supplier_name_zh', 'supplier_name_en', 'supplier_address',
            'supplier_phone', 'supplier_email', 'supplier_contact_person',
            'supplier_tax_id', 'supplier_region', 'supplier_remark',
            'payment_terms', 'bank_account', 'is_active'
        ]
        
        for field in updateable_fields:
            if field in data:
                if field == 'supplier_region' and data[field] not in ['domestic', 'international']:
                    return create_error_response(
                        'INVALID_REGION',
                        'Region must be domestic or international',
                        status_code=400
                    )
                setattr(supplier, field, data[field])
        
        db.session.commit()
        
        return create_response(supplier.to_dict())
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(
            'SUPPLIER_UPDATE_ERROR',
            'Failed to update supplier',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/summary', methods=['GET'])
@authenticated_required
def get_suppliers_summary(current_user):
    """Get lightweight suppliers summary for dropdowns"""
    try:
        region = request.args.get('region')
        active_only = request.args.get('active', 'true').lower() == 'true'
        
        query = Supplier.query
        
        if region:
            query = query.filter(Supplier.supplier_region == region)
        if active_only:
            query = query.filter(Supplier.is_active == True)
        
        suppliers = query.order_by(Supplier.supplier_name_zh).all()
        
        return create_response([supplier.to_summary_dict() for supplier in suppliers])
        
    except Exception as e:
        return create_error_response(
            'SUPPLIER_SUMMARY_ERROR',
            'Failed to get suppliers summary',
            {'error': str(e)},
            status_code=500
        )

@bp.route('/<supplier_id>/purchase-orders', methods=['GET'])
@authenticated_required
def get_supplier_purchase_orders(current_user, supplier_id):
    """Get all purchase orders for a specific supplier"""
    try:
        from app.models.purchase_order import PurchaseOrder
        
        # Verify supplier exists
        supplier = Supplier.query.get_or_404(supplier_id)
        
        # Get query parameters
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        status = request.args.get('status')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query
        query = PurchaseOrder.query.filter(PurchaseOrder.supplier_id == supplier_id)
        
        if status:
            query = query.filter(PurchaseOrder.purchase_status == status)
        
        if start_date:
            from datetime import datetime
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(PurchaseOrder.order_date >= start.date())
        
        if end_date:
            from datetime import datetime
            end = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(PurchaseOrder.order_date <= end.date())
        
        # Order by date descending
        query = query.order_by(PurchaseOrder.order_date.desc())
        
        # Paginate
        result = paginate_query(query, page, page_size)
        
        # Calculate summary statistics
        from sqlalchemy import func
        total_orders = PurchaseOrder.query.filter(PurchaseOrder.supplier_id == supplier_id).count()
        total_amount = db.session.query(func.sum(PurchaseOrder.grand_total_int)).filter(
            PurchaseOrder.supplier_id == supplier_id
        ).scalar() or 0
        
        pending_orders = PurchaseOrder.query.filter(
            PurchaseOrder.supplier_id == supplier_id,
            PurchaseOrder.purchase_status.in_(['created', 'confirmed'])
        ).count()
        
        completed_orders = PurchaseOrder.query.filter(
            PurchaseOrder.supplier_id == supplier_id,
            PurchaseOrder.purchase_status == 'completed'
        ).count()
        
        return jsonify({
            'supplier': supplier.to_dict(),
            'purchase_orders': [po.to_dict() for po in result['items']],
            'pagination': result['pagination'],
            'summary': {
                'total_orders': total_orders,
                'total_amount': total_amount,
                'pending_orders': pending_orders,
                'completed_orders': completed_orders
            }
        }), 200
        
    except Exception as e:
        return create_error_response(
            'SUPPLIER_PO_ERROR',
            'Failed to get supplier purchase orders',
            {'error': str(e)},
            status_code=500
        )