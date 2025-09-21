#!/usr/bin/env python3
"""
Simple update for test items to make them ready for acceptance
"""
import sqlite3

# Connect to database
db_path = "backend/instance/erp_development.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("🔄 Updating test items status for acceptance...")

# List of request order numbers that need to be updated
test_request_orders = [
    'REQ20250911003',  # FF
    'REQ20250911004',  # QQQQ  
    'REQ20250911005',  # 有疑問, OK
    'REQ202509131628'  # test
]

try:
    # Update the item_status to 'arrived' for all these request order items
    for req_no in test_request_orders:
        # Update item status to arrived so they can be accepted
        cursor.execute("""
            UPDATE request_order_items 
            SET item_status = 'arrived', 
                updated_at = datetime('now')
            WHERE request_order_no = ?
        """, (req_no,))
        
        affected_rows = cursor.rowcount
        print(f"✅ Updated {affected_rows} items for {req_no}")
    
    # Commit changes
    conn.commit()
    print("✅ All test items updated successfully!")
    
    # Verify the changes
    print("\n📋 Verification:")
    for req_no in test_request_orders:
        cursor.execute("""
            SELECT item_name, item_status, acceptance_status
            FROM request_order_items 
            WHERE request_order_no = ?
        """, (req_no,))
        
        items = cursor.fetchall()
        for item_name, item_status, acceptance_status in items:
            print(f"  - {item_name}: status={item_status}, acceptance={acceptance_status}")
            
except Exception as e:
    print(f"❌ Error updating items: {e}")
    conn.rollback()
finally:
    conn.close()