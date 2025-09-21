import sqlite3
from datetime import datetime

# Connect to database
conn = sqlite3.connect('erp_development.db')
cursor = conn.cursor()

# 為 REQ20250914001 添加採購、入庫和驗收狀態
# 這些狀態應該來自相關的採購單、入庫單和驗收單

# 1. 查找相關的採購單
cursor.execute("""
    SELECT po_number, status
    FROM purchase_orders
    WHERE request_order_no = 'REQ20250914001'
""")
po_result = cursor.fetchone()

if po_result:
    po_number, po_status = po_result
    print(f"Found PO: {po_number} with status: {po_status}")

    # 根據採購單狀態映射到採購狀態
    purchase_status_map = {
        'draft': 'created',
        'approved': 'purchasing',
        'ordered': 'purchased',
        'partial_received': 'shipped',
        'received': 'arrived',
        'completed': 'arrived'
    }
    purchase_status = purchase_status_map.get(po_status, 'created')
else:
    purchase_status = 'created'  # 假設已製單
    print("No PO found, using default status")

# 2. 查找相關的入庫記錄
cursor.execute("""
    SELECT COUNT(*)
    FROM storage_history
    WHERE po_number IN (
        SELECT po_number FROM purchase_orders WHERE request_order_no = 'REQ20250914001'
    )
""")
storage_count = cursor.fetchone()[0]

if storage_count > 0:
    storage_status = 'completed'
else:
    storage_status = 'pending'

# 3. 查找相關的驗收記錄
cursor.execute("""
    SELECT COUNT(*)
    FROM request_order_items
    WHERE request_order_no = 'REQ20250914001'
    AND acceptance_status = 'accepted'
""")
accepted_count = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(*)
    FROM request_order_items
    WHERE request_order_no = 'REQ20250914001'
""")
total_count = cursor.fetchone()[0]

if accepted_count == total_count and total_count > 0:
    acceptance_status = 'passed'
elif accepted_count > 0:
    acceptance_status = 'partial'
else:
    acceptance_status = 'pending'

print(f"""
Status Summary for REQ20250914001:
- Purchase Status: {purchase_status}
- Storage Status: {storage_status}
- Acceptance Status: {acceptance_status}
""")

# 更新請購單項目的狀態
cursor.execute("""
    UPDATE request_order_items
    SET item_status = 'approved'
    WHERE request_order_no = 'REQ20250914001'
""")

# 創建一個採購單（如果不存在）
cursor.execute("""
    SELECT COUNT(*) FROM purchase_orders WHERE request_order_no = 'REQ20250914001'
""")
if cursor.fetchone()[0] == 0:
    cursor.execute("""
        INSERT INTO purchase_orders (
            po_number, request_order_no, supplier_id, order_date,
            expected_delivery, status, total_amount, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'PO20250914001',
        'REQ20250914001',
        'S001',
        datetime.now().isoformat(),
        datetime.now().isoformat(),
        'approved',
        1234.0,
        datetime.now().isoformat(),
        datetime.now().isoformat()
    ))
    print("Created purchase order PO20250914001")

conn.commit()
conn.close()

print("Database updated successfully!")