#!/usr/bin/env python3
"""
Script to update purchase orders API build-candidates endpoint with urgent functionality
"""

def update_build_candidates_endpoint():
    """Update build-candidates endpoint to support urgent marking"""
    file_path = '/d/AWORKSPACE/Github/project_ERP_dev_agent/backend/app/routes/purchase_orders.py'

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find and replace the build-candidates endpoint
        old_endpoint = """@bp.route('/build-candidates', methods=['GET'])
@procurement_required
def get_build_candidates(current_user):
    \"\"\"Get approved items grouped by supplier for PO creation\"\"\"
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

        return create_response(list(suppliers.values()))"""

        new_endpoint = """@bp.route('/build-candidates', methods=['GET'])
@procurement_required
def get_build_candidates(current_user):
    \"\"\"Get approved items grouped by supplier for PO creation - 支援加急標記\"\"\"
    try:
        supplier_id = request.args.get('supplier_id')

        # 查詢時連接請購單主表以取得加急資訊
        from sqlalchemy import and_
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

        return create_response(list(suppliers.values()))"""

        # Replace the endpoint
        content = content.replace(old_endpoint, new_endpoint)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✓ Updated build-candidates endpoint with urgent functionality")
        return True

    except Exception as e:
        print(f"Error updating build-candidates endpoint: {e}")
        return False

if __name__ == "__main__":
    print("Updating purchase orders API...")
    success = update_build_candidates_endpoint()
    if success:
        print("Purchase orders API update completed successfully!")
    else:
        print("Purchase orders API update failed!")