#!/usr/bin/env python
"""Create test data for consolidation testing"""
import sqlite3
from datetime import datetime

# SQLite database path
db_path = r'D:\AWORKSPACE\Github\project_ERP_dev_agent\erp_development.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== CREATING TEST DATA FOR CONSOLIDATION ===\n")

# First check if we have international suppliers
cursor.execute("""
    SELECT supplier_id, supplier_name_en, supplier_region
    FROM suppliers
    WHERE supplier_region = 'international'
    LIMIT 2
""")
int_suppliers = cursor.fetchall()

if not int_suppliers:
    print("Creating international suppliers...")
    # Create international suppliers with proper ID generation
    import uuid
    for supplier_data in [
        ('Samsung Electronics', 'Kim Lee', '82-2-1234-5678', 'kim@samsung.com'),
        ('Apple Inc', 'John Smith', '1-408-555-1234', 'john@apple.com')
    ]:
        supplier_id = f"SUP-{uuid.uuid4().hex[:8].upper()}"
        cursor.execute("""
            INSERT INTO suppliers (
                supplier_id, supplier_name_zh, supplier_name_en, supplier_region,
                supplier_contact_person, supplier_phone, supplier_email, is_active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (supplier_id, supplier_data[0], supplier_data[0], 'international',
              supplier_data[1], supplier_data[2], supplier_data[3], 1))
    conn.commit()

    cursor.execute("""
        SELECT supplier_id, supplier_name_en, supplier_region
        FROM suppliers
        WHERE supplier_region = 'international'
        LIMIT 2
    """)
    int_suppliers = cursor.fetchall()

print(f"Found {len(int_suppliers)} international suppliers")

# Create test POs with shipped status
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

for i, supplier in enumerate(int_suppliers):
    po_no = f"PO{datetime.now().strftime('%Y%m%d')}TEST{str(i+1).zfill(3)}"

    print(f"\nCreating PO {po_no} for {supplier[1]}...")

    # Check if PO already exists
    cursor.execute("SELECT purchase_order_no FROM purchase_orders WHERE purchase_order_no = ?", (po_no,))
    if cursor.fetchone():
        print(f"  PO {po_no} already exists, skipping...")
        continue

    # Create the PO (need to get a user ID first)
    cursor.execute("SELECT user_id FROM users LIMIT 1")
    user_result = cursor.fetchone()
    if not user_result:
        print("No users found, creating test user...")
        cursor.execute("""
            INSERT INTO users (username, password_hash, email, full_name, is_active)
            VALUES ('test_user', 'hash', 'test@test.com', 'Test User', 1)
        """)
        conn.commit()
        cursor.execute("SELECT user_id FROM users WHERE username='test_user'")
        user_result = cursor.fetchone()

    user_id = user_result[0]

    cursor.execute("""
        INSERT INTO purchase_orders (
            purchase_order_no,
            supplier_id,
            supplier_name,
            order_date,
            purchase_status,
            shipping_status,
            delivery_status,
            expected_delivery_date,
            subtotal_int,
            tax_decimal1,
            grand_total_int,
            remarks,
            creator_id,
            created_at,
            updated_at,
            consolidation_id,
            status_update_required
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?)
    """, (
        po_no,
        supplier[0],
        supplier[1],
        current_time,
        'purchased',
        'shipped',
        'shipped',  # Important: shipped status makes it eligible for consolidation
        '2025-10-15',
        50000,
        5000.0,
        55000,
        f'Test PO for consolidation - {supplier[1]}',
        user_id,
        current_time,
        current_time,
        0  # status_update_required = false
    ))

    # Create some items for the PO
    for j in range(2):
        quantity = 10 + j * 5
        unit_price = 1000.0
        subtotal = int(quantity * unit_price)

        cursor.execute("""
            INSERT INTO purchase_order_items (
                purchase_order_no,
                item_name,
                item_specification,
                item_model,
                item_quantity,
                item_unit,
                unit_price,
                line_subtotal_int,
                delivery_status,
                remarks,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            po_no,
            f'Test Item {j+1}',
            f'Test specification {j+1}',
            f'MODEL-{j+1}',
            quantity,
            'pcs',
            unit_price,
            subtotal,
            'not_shipped',
            'Test item for consolidation',
            current_time
        ))

    print(f"  ✓ Created PO {po_no} with 2 items")

conn.commit()

# Verify the data
print("\n=== VERIFYING TEST DATA ===")
cursor.execute("""
    SELECT po.purchase_order_no, po.supplier_name, po.delivery_status, s.supplier_region
    FROM purchase_orders po
    JOIN suppliers s ON po.supplier_id = s.supplier_id
    WHERE s.supplier_region = 'international'
    AND po.delivery_status = 'shipped'
    AND po.consolidation_id IS NULL
""")

eligible = cursor.fetchall()
print(f"\nFound {len(eligible)} eligible POs for consolidation:")
for po in eligible:
    print(f"  - {po[0]}: {po[1]} (Status: {po[2]}, Region: {po[3]})")

# Also show existing consolidations
cursor.execute("""
    SELECT consolidation_id, consolidation_name, logistics_status
    FROM shipment_consolidations
    ORDER BY created_at DESC
    LIMIT 5
""")
existing = cursor.fetchall()
if existing:
    print(f"\nExisting consolidations:")
    for c in existing:
        print(f"  - {c[0]}: {c[1]} (Status: {c[2]})")

conn.close()
print("\n✓ Test data created successfully")