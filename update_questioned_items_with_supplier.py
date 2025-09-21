#!/usr/bin/env python3
"""
Update questioned items with supplier and unit price data for testing
"""

import sqlite3
import json
from datetime import datetime

def update_questioned_items():
    # Connect to database
    conn = sqlite3.connect('erp_development.db')
    cursor = conn.cursor()

    try:
        # Update the first questioned item with TSMC supplier and price
        cursor.execute("""
            UPDATE request_order_items
            SET supplier_id = 'TSMC001',
                unit_price = 1500.00
            WHERE detail_id = 13
        """)

        # Update the second questioned item with Intel supplier and price
        cursor.execute("""
            UPDATE request_order_items
            SET supplier_id = 'INTEL001',
                unit_price = 2800.00
            WHERE detail_id = 15
        """)

        conn.commit()
        print("✅ Successfully updated questioned items with supplier and price data")

        # Verify the updates
        cursor.execute("""
            SELECT detail_id, item_name, supplier_id, unit_price, item_status
            FROM request_order_items
            WHERE item_status = 'questioned'
        """)

        items = cursor.fetchall()
        print("\n📋 Updated questioned items:")
        for item in items:
            print(f"  - ID: {item[0]}, Name: {item[1]}, Supplier: {item[2]}, Price: {item[3]}")

    except Exception as e:
        print(f"❌ Error updating questioned items: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    update_questioned_items()