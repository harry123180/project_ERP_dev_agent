#!/usr/bin/env python3
"""
Script to manually update specific lines in requisitions.py
"""

def update_create_requisition():
    """Update create_requisition POST endpoint"""
    file_path = '/d/AWORKSPACE/Github/project_ERP_dev_agent/backend/app/routes/requisitions.py'

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Find the line with "order_status=initial_status  # CRITICAL FIX: Set initial status"
        # and insert urgent fields after it
        for i, line in enumerate(lines):
            if "order_status=initial_status" in line and "# CRITICAL FIX: Set initial status" in line:
                # Insert urgent fields after this line
                indent = "            "  # Match existing indentation
                new_lines = [
                    line,  # Keep existing line
                    f"{indent}# 加急相關欄位\n",
                    f"{indent}is_urgent=data.get('is_urgent', False),\n",
                    f"{indent}expected_delivery_date=datetime.strptime(data['expected_delivery_date'], '%Y-%m-%d').date()\n",
                    f"{indent}    if data.get('expected_delivery_date') else None,\n",
                    f"{indent}urgent_reason=data.get('urgent_reason')\n"
                ]
                lines[i:i+1] = new_lines
                break

        # Find and add validation after the order creation
        for i, line in enumerate(lines):
            if "# CRITICAL FIX: Set submit_date if creating directly in submitted status" in line:
                # Insert validation before this line
                indent = "        "
                validation_lines = [
                    f"{indent}# 驗證加急相關欄位\n",
                    f"{indent}try:\n",
                    f"{indent}    order.validate_urgent_fields()\n",
                    f"{indent}except ValueError as e:\n",
                    f"{indent}    return create_error_response(\n",
                    f"{indent}        'VALIDATION_ERROR',\n",
                    f"{indent}        str(e),\n",
                    f"{indent}        status_code=400\n",
                    f"{indent}    )\n",
                    f"{indent}\n",
                    line  # Keep the original line
                ]
                lines[i:i+1] = validation_lines
                break

        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print("✓ Updated create_requisition POST endpoint")
        return True

    except Exception as e:
        print(f"Error updating create_requisition: {e}")
        return False

def update_update_requisition():
    """Update update_requisition PUT endpoint"""
    file_path = '/d/AWORKSPACE/Github/project_ERP_dev_agent/backend/app/routes/requisitions.py'

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Find the section where order fields are updated
        for i, line in enumerate(lines):
            if "if 'project_id' in data:" in line:
                # Insert urgent field updates after project_id update
                indent = "        "
                new_lines = [
                    line,  # Keep existing line
                    f"{indent}    order.project_id = data['project_id']\n",
                    f"{indent}\n",
                    f"{indent}# 更新加急相關欄位\n",
                    f"{indent}if 'is_urgent' in data:\n",
                    f"{indent}    order.is_urgent = data['is_urgent']\n",
                    f"{indent}if 'expected_delivery_date' in data:\n",
                    f"{indent}    order.expected_delivery_date = datetime.strptime(data['expected_delivery_date'], '%Y-%m-%d').date() \\\n",
                    f"{indent}        if data['expected_delivery_date'] else None\n",
                    f"{indent}if 'urgent_reason' in data:\n",
                    f"{indent}    order.urgent_reason = data['urgent_reason']\n",
                    f"{indent}\n",
                    f"{indent}# 驗證加急相關欄位\n",
                    f"{indent}try:\n",
                    f"{indent}    order.validate_urgent_fields()\n",
                    f"{indent}except ValueError as e:\n",
                    f"{indent}    return create_error_response(\n",
                    f"{indent}        'VALIDATION_ERROR',\n",
                    f"{indent}        str(e),\n",
                    f"{indent}        status_code=400\n",
                    f"{indent}    )\n"
                ]

                # Find the next line and replace project_id assignment
                if i + 1 < len(lines) and "order.project_id = data['project_id']" in lines[i + 1]:
                    lines[i:i+2] = new_lines
                else:
                    lines[i:i+1] = new_lines
                break

        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print("✓ Updated update_requisition PUT endpoint")
        return True

    except Exception as e:
        print(f"Error updating update_requisition: {e}")
        return False

if __name__ == "__main__":
    print("Updating requisition endpoints...")
    success1 = update_create_requisition()
    success2 = update_update_requisition()

    if success1 and success2:
        print("All endpoint updates completed successfully!")
    else:
        print("Some endpoint updates failed!")