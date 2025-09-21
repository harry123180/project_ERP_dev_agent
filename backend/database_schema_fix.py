#!/usr/bin/env python3
"""
Database Schema Fix: Remove enum constraints for SQLite compatibility
"""

from app import create_app, db
from sqlalchemy import text
import sqlite3
import os

def fix_database_schema():
    """Fix the database schema to remove enum constraints"""
    
    app = create_app()
    with app.app_context():
        try:
            print("🔍 Analyzing current database schema...")
            
            # Get the database file path
            db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            if 'sqlite:///' in db_uri:
                db_path = db_uri.replace('sqlite:///', '')
                print(f"Database file: {db_path}")
            else:
                print("Not a SQLite database, exiting...")
                return False
            
            # Connect directly to SQLite to examine schema
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check current table schema
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='request_orders'")
            result = cursor.fetchone()
            if result:
                print("Current request_orders table schema:")
                print(result[0])
                
                # Check if enum constraints exist in the schema
                if 'CHECK' in result[0] and 'usage_type' in result[0]:
                    print("\n🔧 Enum constraints detected in schema")
                    
                    # The safest approach is to recreate the table without constraints
                    print("Creating new table without enum constraints...")
                    
                    # Create backup
                    cursor.execute("""
                        CREATE TABLE request_orders_backup AS 
                        SELECT * FROM request_orders
                    """)
                    
                    # Drop original table
                    cursor.execute("DROP TABLE request_orders")
                    
                    # Create new table without enum constraints
                    cursor.execute("""
                        CREATE TABLE request_orders (
                            request_order_no VARCHAR(50) PRIMARY KEY,
                            requester_id INTEGER NOT NULL,
                            requester_name VARCHAR(100) NOT NULL,
                            usage_type VARCHAR(20) NOT NULL,
                            project_id VARCHAR(50),
                            submit_date DATE,
                            order_status VARCHAR(20) NOT NULL DEFAULT 'draft',
                            created_at DATETIME,
                            updated_at DATETIME,
                            FOREIGN KEY (requester_id) REFERENCES users(user_id),
                            FOREIGN KEY (project_id) REFERENCES projects(project_id)
                        )
                    """)
                    
                    # Restore data
                    cursor.execute("""
                        INSERT INTO request_orders 
                        SELECT * FROM request_orders_backup
                    """)
                    
                    # Drop backup
                    cursor.execute("DROP TABLE request_orders_backup")
                    
                    conn.commit()
                    print("✅ Successfully updated request_orders table schema")
                else:
                    print("✅ No enum constraints found in request_orders table")
            
            # Check request_order_items table
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='request_order_items'")
            result = cursor.fetchone()
            if result:
                print("\nCurrent request_order_items table schema:")
                print(result[0])
                
                if 'CHECK' in result[0] and ('item_status' in result[0] or 'acceptance_status' in result[0]):
                    print("\n🔧 Enum constraints detected in request_order_items")
                    
                    # Similar fix for request_order_items
                    cursor.execute("""
                        CREATE TABLE request_order_items_backup AS 
                        SELECT * FROM request_order_items
                    """)
                    
                    cursor.execute("DROP TABLE request_order_items")
                    
                    cursor.execute("""
                        CREATE TABLE request_order_items (
                            detail_id INTEGER PRIMARY KEY,
                            request_order_no VARCHAR(50) NOT NULL,
                            item_name VARCHAR(200) NOT NULL,
                            item_quantity DECIMAL(10,2) NOT NULL,
                            item_unit VARCHAR(20) NOT NULL,
                            item_specification TEXT,
                            item_description TEXT,
                            item_category VARCHAR(10),
                            item_status VARCHAR(20) NOT NULL DEFAULT 'draft',
                            acceptance_status VARCHAR(20) DEFAULT 'pending_acceptance',
                            supplier_id VARCHAR(50),
                            unit_price DECIMAL(10,2),
                            material_serial_no VARCHAR(50),
                            status_note TEXT,
                            needs_acceptance BOOLEAN DEFAULT 1,
                            created_at DATETIME,
                            updated_at DATETIME,
                            FOREIGN KEY (request_order_no) REFERENCES request_orders(request_order_no),
                            FOREIGN KEY (item_category) REFERENCES item_categories(category_code),
                            FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
                        )
                    """)
                    
                    cursor.execute("""
                        INSERT INTO request_order_items 
                        SELECT * FROM request_order_items_backup
                    """)
                    
                    cursor.execute("DROP TABLE request_order_items_backup")
                    conn.commit()
                    print("✅ Successfully updated request_order_items table schema")
                else:
                    print("✅ No enum constraints found in request_order_items table")
            
            conn.close()
            
            # Now test with SQLAlchemy
            print("\n🧪 Testing with SQLAlchemy...")
            from app.models.request_order import RequestOrder
            orders = RequestOrder.query.all()
            print(f"✅ Successfully loaded {len(orders)} requisitions")
            
            for order in orders[:3]:  # Show first 3 orders
                print(f"   - {order.request_order_no}: {order.usage_type} ({order.order_status})")
            
            return True
            
        except Exception as e:
            print(f"❌ Error during schema fix: {str(e)}")
            return False

if __name__ == "__main__":
    print("🚀 Starting Database Schema Fix")
    success = fix_database_schema()
    if success:
        print("🎉 Database schema fix completed successfully!")
    else:
        print("💥 Database schema fix failed")