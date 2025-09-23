#!/usr/bin/env python
"""Check consolidations in SQLite database"""
import sqlite3
import os

# SQLite database path
db_path = r'D:\AWORKSPACE\Github\project_ERP_dev_agent\erp_development.db'

if not os.path.exists(db_path):
    print(f"Database not found at: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== CHECKING CONSOLIDATIONS IN SQLITE ===\n")

# Check consolidations table
cursor.execute("""
    SELECT consolidation_id, consolidation_name, logistics_status,
           created_by, created_at
    FROM consolidations
    ORDER BY created_at DESC
""")

consolidations = cursor.fetchall()
print(f"Found {len(consolidations)} consolidations:")

for c in consolidations:
    print(f"\nConsolidation ID: {c[0]}")
    print(f"  Name: {c[1]}")
    print(f"  Status: {c[2]}")
    print(f"  Created by: {c[3]}")
    print(f"  Created at: {c[4]}")

    # Check linked POs
    cursor.execute("""
        SELECT cp.purchase_order_id, po.purchase_order_no, po.supplier_name
        FROM consolidation_pos cp
        LEFT JOIN purchase_orders po ON cp.purchase_order_id = po.purchase_order_id
        WHERE cp.consolidation_id = ?
    """, (c[0],))

    pos = cursor.fetchall()
    print(f"  Linked POs: {len(pos)}")
    for po in pos:
        print(f"    - PO {po[1]}: {po[2]} (ID: {po[0]})")

if not consolidations:
    print("No consolidations found!")

    # Check if there are any POs to consolidate
    print("\n=== CHECKING AVAILABLE PURCHASE ORDERS ===")
    cursor.execute("""
        SELECT purchase_order_id, purchase_order_no, supplier_name, order_status
        FROM purchase_orders
        WHERE order_status IN ('pending', 'approved', 'shipped')
        ORDER BY created_at DESC
        LIMIT 10
    """)

    pos = cursor.fetchall()
    print(f"Found {len(pos)} eligible POs for consolidation:")
    for po in pos:
        print(f"  - PO {po[1]}: {po[2]} (Status: {po[3]}, ID: {po[0]})")

conn.close()