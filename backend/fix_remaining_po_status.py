import sqlite3
import sys

try:
    # Connect to database
    conn = sqlite3.connect('erp_development.db')
    cursor = conn.cursor()
    
    # Check current status values
    cursor.execute("SELECT purchase_order_no, purchase_status FROM purchase_orders")
    all_records = cursor.fetchall()
    
    print("Current PO statuses:")
    for po_no, status in all_records:
        print(f"  {po_no}: {status}")
    
    # Update any remaining 'pending' to 'order_created'
    cursor.execute("""
        UPDATE purchase_orders 
        SET purchase_status = 'order_created' 
        WHERE purchase_status = 'pending'
    """)
    
    pending_updated = cursor.rowcount
    
    # Commit changes
    conn.commit()
    
    print(f"\nUpdated {pending_updated} records from 'pending' to 'order_created'")
    
    # Verify the updates
    cursor.execute("SELECT purchase_order_no, purchase_status FROM purchase_orders")
    updated_records = cursor.fetchall()
    
    print("\nUpdated PO statuses:")
    for po_no, status in updated_records:
        print(f"  {po_no}: {status}")
    
    conn.close()
    print("\nDatabase update completed successfully!")
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)