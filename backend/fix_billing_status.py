import sqlite3
import sys

try:
    # Connect to database
    conn = sqlite3.connect('erp_development.db')
    cursor = conn.cursor()
    
    # Check current billing_status values
    cursor.execute("SELECT purchase_order_no, billing_status FROM purchase_orders")
    all_records = cursor.fetchall()
    
    print("Current billing statuses:")
    for po_no, status in all_records:
        print(f"  {po_no}: {status}")
    
    # Update 'pending' to 'none' in billing_status
    cursor.execute("""
        UPDATE purchase_orders 
        SET billing_status = 'none' 
        WHERE billing_status = 'pending'
    """)
    
    updated_count = cursor.rowcount
    
    # Commit changes
    conn.commit()
    
    print(f"\nUpdated {updated_count} records from billing_status='pending' to 'none'")
    
    # Verify the updates
    cursor.execute("SELECT purchase_order_no, billing_status FROM purchase_orders")
    updated_records = cursor.fetchall()
    
    print("\nUpdated billing statuses:")
    for po_no, status in updated_records:
        print(f"  {po_no}: {status}")
    
    conn.close()
    print("\nDatabase update completed successfully!")
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)