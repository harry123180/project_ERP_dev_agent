#!/usr/bin/env python
"""
Add usage_type column to inventory_batches table
"""

import sqlite3
import os

def add_usage_type_column():
    """Add usage_type column to inventory_batches table if it doesn't exist"""
    
    db_path = 'erp_development.db'
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(inventory_batches)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'usage_type' not in column_names:
            # Add the column with default value
            cursor.execute("""
                ALTER TABLE inventory_batches 
                ADD COLUMN usage_type VARCHAR(20) DEFAULT 'general'
            """)
            conn.commit()
            print("✓ Added usage_type column to inventory_batches table")
            
            # Update existing records based on item categories
            # Office supplies
            cursor.execute("""
                UPDATE inventory_batches 
                SET usage_type = 'office' 
                WHERE item_name LIKE '%紙%' 
                   OR item_name LIKE '%筆%' 
                   OR item_name LIKE '%辦公%'
            """)
            
            # IT equipment
            cursor.execute("""
                UPDATE inventory_batches 
                SET usage_type = 'it' 
                WHERE item_name LIKE '%電腦%' 
                   OR item_name LIKE '%滑鼠%' 
                   OR item_name LIKE '%鍵盤%'
                   OR item_name LIKE '%螢幕%'
            """)
            
            conn.commit()
            print("✓ Updated usage_type for existing inventory batches")
            
        else:
            print("usage_type column already exists")
        
        # Show current data
        cursor.execute("""
            SELECT item_name, usage_type, COUNT(*) as batch_count
            FROM inventory_batches
            GROUP BY item_name, usage_type
        """)
        
        results = cursor.fetchall()
        if results:
            print("\nCurrent inventory usage types:")
            print("-" * 60)
            for item_name, usage_type, count in results:
                print(f"{item_name}: {usage_type} ({count} batches)")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    add_usage_type_column()