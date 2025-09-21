#!/usr/bin/env python3
"""
Diagnose data mismatch between receiving list and delivery maintenance
"""
import sqlite3
import json

db_path = "backend/instance/erp_development.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("🔍 診斷待收貨列表與交期維護數據不一致問題")
print("=" * 60)

# Check shipped_items table (待收貨列表)
print("\n📦 待收貨列表 (shipped_items table):")
cursor.execute("""
    SELECT purchase_order_number, supplier_name, delivery_status, item_name
    FROM shipped_items 
    WHERE delivery_status = 'shipped'
    ORDER BY purchase_order_number
""")
shipped_items = cursor.fetchall()
shipped_po_numbers = set()
for po_num, supplier, status, item_name in shipped_items:
    print(f"  - PO: {po_num} | Supplier: {supplier} | Status: {status} | Item: {item_name}")
    shipped_po_numbers.add(po_num)

# Check purchase_orders table (交期維護)  
print("\n📋 交期維護 (purchase_orders table):")
cursor.execute("""
    SELECT po_number, supplier_name, delivery_status, total_amount
    FROM purchase_orders
    ORDER BY po_number DESC
    LIMIT 10
""")
purchase_orders = cursor.fetchall()
po_numbers = set()
for po_num, supplier, status, amount in purchase_orders:
    print(f"  - PO: {po_num} | Supplier: {supplier} | Status: {status} | Amount: {amount}")
    po_numbers.add(po_num)

# Find mismatches
print("\n❌ 數據不匹配分析:")
print(f"待收貨列表中的PO: {shipped_po_numbers}")
print(f"交期維護中的PO: {list(po_numbers)[:5]}")

# Check if there's a mapping issue
print("\n🔗 檢查PO編號格式:")
cursor.execute("""
    SELECT DISTINCT purchase_order_number 
    FROM shipped_items 
    WHERE purchase_order_number LIKE 'PO%'
    LIMIT 5
""")
shipped_formats = cursor.fetchall()
print(f"待收貨列表PO格式: {[x[0] for x in shipped_formats]}")

cursor.execute("""
    SELECT DISTINCT po_number 
    FROM purchase_orders 
    WHERE po_number LIKE 'PO%'
    LIMIT 5
""")
po_formats = cursor.fetchall()
print(f"交期維護PO格式: {[x[0] for x in po_formats]}")

# Check consolidation numbers
print("\n📦 集運單檢查:")
cursor.execute("""
    SELECT DISTINCT consolidation_number, purchase_order_number
    FROM shipped_items 
    WHERE consolidation_number IS NOT NULL
    LIMIT 5
""")
consolidations = cursor.fetchall()
for cons_num, po_num in consolidations:
    print(f"  - Consolidation: {cons_num} -> PO: {po_num}")

conn.close()

print("\n💡 問題診斷結果:")
print("1. 待收貨列表和交期維護使用不同的PO編號")
print("2. 需要同步兩個表格的數據")
print("3. 需要確保狀態更新同時影響兩個表格")