#!/usr/bin/env python3
"""
Script to update requisitions API with urgent functionality
"""

import re

def update_requisitions_api():
    """Update requisitions.py to support urgent functionality"""
    file_path = '/d/AWORKSPACE/Github/project_ERP_dev_agent/backend/app/routes/requisitions.py'

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 1. Update the POST endpoint (create_requisition) to support urgent fields
        post_pattern = r'(# Create request order with specified status\s+order = RequestOrder\(\s+request_order_no=request_order_no,\s+requester_id=current_user\.user_id,\s+requester_name=current_user\.chinese_name,\s+usage_type=data\[\'usage_type\'\],\s+project_id=data\.get\(\'project_id\'\),\s+order_status=initial_status\s+\))'

        post_replacement = r'''# Create request order with specified status
        order = RequestOrder(
            request_order_no=request_order_no,
            requester_id=current_user.user_id,
            requester_name=current_user.chinese_name,
            usage_type=data['usage_type'],
            project_id=data.get('project_id'),
            order_status=initial_status,
            # 加急相關欄位
            is_urgent=data.get('is_urgent', False),
            expected_delivery_date=datetime.strptime(data['expected_delivery_date'], '%Y-%m-%d').date()
                if data.get('expected_delivery_date') else None,
            urgent_reason=data.get('urgent_reason')
        )

        # 驗證加急相關欄位
        try:
            order.validate_urgent_fields()
        except ValueError as e:
            return create_error_response(
                'VALIDATION_ERROR',
                str(e),
                status_code=400
            )'''

        content = re.sub(post_pattern, post_replacement, content, flags=re.MULTILINE | re.DOTALL)

        # 2. Update the PUT endpoint (update_requisition) to support urgent fields
        put_pattern = r'(# Update order fields\s+if \'usage_type\' in data:\s+order\.usage_type = data\[\'usage_type\'\]\s+if \'project_id\' in data:\s+order\.project_id = data\[\'project_id\'\])'

        put_replacement = r'''# Update order fields
        if 'usage_type' in data:
            order.usage_type = data['usage_type']
        if 'project_id' in data:
            order.project_id = data['project_id']

        # 更新加急相關欄位
        if 'is_urgent' in data:
            order.is_urgent = data['is_urgent']
        if 'expected_delivery_date' in data:
            order.expected_delivery_date = datetime.strptime(data['expected_delivery_date'], '%Y-%m-%d').date() \
                if data['expected_delivery_date'] else None
        if 'urgent_reason' in data:
            order.urgent_reason = data['urgent_reason']

        # 驗證加急相關欄位
        try:
            order.validate_urgent_fields()
        except ValueError as e:
            return create_error_response(
                'VALIDATION_ERROR',
                str(e),
                status_code=400
            )'''

        content = re.sub(put_pattern, put_replacement, content, flags=re.MULTILINE | re.DOTALL)

        # 3. Add urgent suppliers endpoint at the end of the file, before the last line
        urgent_endpoint = '''
@bp.route('/urgent-suppliers', methods=['GET'])
@procurement_required
def get_urgent_suppliers(current_user):
    """取得有加急項目的供應商列表"""
    try:
        # 查詢有加急且已核准項目的供應商
        from app.models.supplier import Supplier

        urgent_suppliers = db.session.query(
            Supplier.supplier_id,
            Supplier.supplier_name_zh,
            db.func.count(RequestOrderItem.detail_id).label('urgent_item_count')
        ).join(
            RequestOrderItem, Supplier.supplier_id == RequestOrderItem.supplier_id
        ).join(
            RequestOrder, RequestOrderItem.request_order_no == RequestOrder.request_order_no
        ).filter(
            RequestOrder.is_urgent == True,
            RequestOrderItem.item_status == 'approved'
        ).group_by(
            Supplier.supplier_id,
            Supplier.supplier_name_zh
        ).all()

        result = []
        for supplier_id, supplier_name, count in urgent_suppliers:
            result.append({
                'supplier_id': supplier_id,
                'supplier_name_zh': supplier_name,
                'urgent_item_count': count
            })

        return create_response(result)

    except Exception as e:
        return create_error_response(
            'URGENT_SUPPLIERS_ERROR',
            'Failed to get urgent suppliers',
            {'error': str(e)},
            status_code=500
        )

'''

        # Insert the urgent endpoint before the last line (assuming the file doesn't end with empty lines)
        lines = content.split('\n')
        # Find a good place to insert - typically before any closing comments or at the end
        insert_index = len(lines)
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() and not lines[i].startswith('#'):
                insert_index = i + 1
                break

        lines.insert(insert_index, urgent_endpoint)
        content = '\n'.join(lines)

        # Write the updated content back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✓ Successfully updated requisitions API with urgent functionality")
        return True

    except Exception as e:
        print(f"Error updating requisitions API: {e}")
        return False

if __name__ == "__main__":
    print("Updating requisitions API...")
    success = update_requisitions_api()
    if success:
        print("API update completed successfully!")
    else:
        print("API update failed!")