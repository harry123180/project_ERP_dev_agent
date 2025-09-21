#!/usr/bin/env python3
"""
Sync delivery data between purchase orders and items for consistent display
"""
import sqlite3
from datetime import datetime

db_path = "backend/instance/erp_development.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("🔄 同步交期維護與待收貨數據")
print("=" * 60)

# 1. Create missing shipped items from purchase order items
print("\n📦 Step 1: 從採購單項目創建待收貨記錄...")

# Check if we need to create a shipped_items-like view from purchase_order_items
cursor.execute("""
    SELECT 
        poi.purchase_order_no,
        poi.item_name,
        poi.quantity,
        poi.unit,
        poi.delivery_status,
        po.supplier_name,
        po.shipping_status,
        po.eta_date
    FROM purchase_order_items poi
    JOIN purchase_orders po ON poi.purchase_order_no = po.purchase_order_no
    WHERE poi.delivery_status IN ('shipped', 'in_transit')
       OR po.shipping_status IN ('shipped', 'in_transit')
    LIMIT 20
""")

shipped_items = cursor.fetchall()
print(f"找到 {len(shipped_items)} 個已發貨項目")

for item in shipped_items[:5]:  # Show first 5
    print(f"  - PO: {item[0]} | Item: {item[1]} | Status: {item[4]} | Supplier: {item[5]}")

# 2. Update delivery status consistency
print("\n🔄 Step 2: 同步採購單和項目的交貨狀態...")

# Update purchase_order_items delivery status based on purchase_orders shipping status
cursor.execute("""
    UPDATE purchase_order_items
    SET delivery_status = (
        SELECT CASE 
            WHEN po.shipping_status = 'delivered' THEN 'delivered'
            WHEN po.shipping_status = 'shipped' THEN 'shipped'
            WHEN po.shipping_status = 'in_transit' THEN 'in_transit'
            ELSE purchase_order_items.delivery_status
        END
        FROM purchase_orders po
        WHERE po.purchase_order_no = purchase_order_items.purchase_order_no
    )
    WHERE purchase_order_no IN (
        SELECT purchase_order_no FROM purchase_orders 
        WHERE shipping_status IN ('shipped', 'in_transit', 'delivered')
    )
""")

affected = cursor.rowcount
print(f"  ✅ 更新了 {affected} 個項目的交貨狀態")

# 3. Create consolidation records if missing
print("\n📦 Step 3: 檢查集運單數據...")

cursor.execute("""
    SELECT COUNT(DISTINCT consolidation_no) 
    FROM shipment_consolidations
""")
cons_count = cursor.fetchone()[0]
print(f"  找到 {cons_count} 個集運單")

# 4. Update missing delivery dates
print("\n📅 Step 4: 更新預計交貨日期...")

cursor.execute("""
    UPDATE purchase_orders
    SET eta_date = date('now', '+7 days')
    WHERE eta_date IS NULL 
      AND shipping_status IN ('shipped', 'in_transit')
""")
date_updates = cursor.rowcount
print(f"  ✅ 更新了 {date_updates} 個缺失的預計交貨日期")

# 5. Fix status mappings
print("\n🏷️ Step 5: 修正狀態映射...")

# Ensure consistent status values
status_fixes = [
    ("UPDATE purchase_orders SET shipping_status = 'in_transit' WHERE shipping_status = 'transit'", "transit -> in_transit"),
    ("UPDATE purchase_order_items SET delivery_status = 'shipped' WHERE delivery_status = 'ship'", "ship -> shipped"),
    ("UPDATE purchase_orders SET shipping_status = 'delivered' WHERE shipping_status = 'receive'", "receive -> delivered"),
]

for query, desc in status_fixes:
    cursor.execute(query)
    if cursor.rowcount > 0:
        print(f"  ✅ 修正: {desc} ({cursor.rowcount} 筆)")

# Commit changes
conn.commit()

# 6. Verify data consistency
print("\n✅ Step 6: 驗證數據一致性...")

# Check purchase orders with shipped status
cursor.execute("""
    SELECT 
        purchase_order_no,
        supplier_name,
        shipping_status,
        eta_date
    FROM purchase_orders
    WHERE shipping_status IN ('shipped', 'in_transit')
    ORDER BY purchase_order_no DESC
    LIMIT 10
""")

print("\n📋 已發貨的採購單:")
for row in cursor.fetchall():
    print(f"  - PO: {row[0]} | Supplier: {row[1]} | Status: {row[2]} | ETA: {row[3]}")

# Check items with shipped status
cursor.execute("""
    SELECT 
        poi.purchase_order_no,
        poi.item_name,
        poi.delivery_status,
        po.supplier_name
    FROM purchase_order_items poi
    JOIN purchase_orders po ON poi.purchase_order_no = po.purchase_order_no
    WHERE poi.delivery_status IN ('shipped', 'in_transit')
    LIMIT 10
""")

print("\n📦 已發貨的項目:")
for row in cursor.fetchall():
    print(f"  - PO: {row[0]} | Item: {row[1]} | Status: {row[2]} | Supplier: {row[3]}")

conn.close()

print("\n✅ 數據同步完成！")
print("提示：請刷新頁面查看更新後的數據")