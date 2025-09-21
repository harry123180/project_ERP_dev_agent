#!/usr/bin/env python3
"""
Create receiving tables migration
"""

import sqlite3
import os
from datetime import datetime

def run_migration():
    db_path = "erp_development.db"
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create receiving_records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS receiving_records (
                receiving_id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_order_no VARCHAR(50) NOT NULL,
                po_item_detail_id INTEGER NOT NULL,
                requisition_number VARCHAR(50) NOT NULL,
                consolidation_number VARCHAR(50),
                item_name VARCHAR(200) NOT NULL,
                item_specification TEXT,
                quantity_shipped DECIMAL(10, 2) NOT NULL,
                quantity_received DECIMAL(10, 2) NOT NULL,
                unit VARCHAR(20) NOT NULL,
                receiver_id INTEGER NOT NULL,
                receiver_name VARCHAR(50) NOT NULL,
                received_at DATETIME NOT NULL,
                notes TEXT,
                receiving_status VARCHAR(20) DEFAULT 'received_pending_storage',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (purchase_order_no) REFERENCES purchase_orders(purchase_order_no),
                FOREIGN KEY (po_item_detail_id) REFERENCES purchase_order_items(detail_id),
                FOREIGN KEY (receiver_id) REFERENCES users(user_id)
            )
        """)
        
        # Create pending_storage_items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pending_storage_items (
                pending_id INTEGER PRIMARY KEY AUTOINCREMENT,
                receiving_record_id INTEGER NOT NULL,
                item_name VARCHAR(200) NOT NULL,
                item_specification TEXT,
                quantity DECIMAL(10, 2) NOT NULL,
                unit VARCHAR(20) NOT NULL,
                source_po_number VARCHAR(50) NOT NULL,
                requisition_number VARCHAR(50) NOT NULL,
                consolidation_number VARCHAR(50),
                suggested_storage_id VARCHAR(20),
                assigned_storage_id VARCHAR(20),
                storage_status VARCHAR(20) DEFAULT 'pending',
                arrival_date DATE NOT NULL,
                receiver VARCHAR(50) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                assigned_at DATETIME,
                stored_at DATETIME,
                FOREIGN KEY (receiving_record_id) REFERENCES receiving_records(receiving_id),
                FOREIGN KEY (suggested_storage_id) REFERENCES storages(storage_id),
                FOREIGN KEY (assigned_storage_id) REFERENCES storages(storage_id)
            )
        """)
        
        # Create storages table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS storages (
                storage_id VARCHAR(20) PRIMARY KEY,
                area_code VARCHAR(10) NOT NULL,
                shelf_code VARCHAR(1) NOT NULL,
                floor_level INTEGER NOT NULL,
                front_back_position INTEGER NOT NULL,
                left_middle_right_position INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create storage_history table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS storage_history (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                storage_id VARCHAR(20) NOT NULL,
                item_id VARCHAR(50) NOT NULL,
                operation_type VARCHAR(10) NOT NULL CHECK(operation_type IN ('in', 'out')),
                operation_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                operator_id INTEGER NOT NULL,
                quantity DECIMAL(10, 2) NOT NULL,
                source_type VARCHAR(30),
                source_no VARCHAR(50),
                source_line INTEGER,
                note TEXT,
                request_item_id INTEGER,
                FOREIGN KEY (storage_id) REFERENCES storages(storage_id),
                FOREIGN KEY (operator_id) REFERENCES users(user_id),
                FOREIGN KEY (request_item_id) REFERENCES request_order_items(detail_id)
            )
        """)
        
        # Create some sample storage locations
        sample_storages = [
            ('Z1-A-1-F-Left', 'Z1', 'A', 1, 1, 1),
            ('Z1-A-1-F-Middle', 'Z1', 'A', 1, 1, 2),
            ('Z1-A-1-F-Right', 'Z1', 'A', 1, 1, 3),
            ('Z1-A-2-F-Left', 'Z1', 'A', 2, 1, 1),
            ('Z1-A-2-F-Middle', 'Z1', 'A', 2, 1, 2),
            ('Z1-B-1-F-Left', 'Z1', 'B', 1, 1, 1),
            ('Z1-B-1-F-Middle', 'Z1', 'B', 1, 1, 2),
            ('Z2-A-1-F-Left', 'Z2', 'A', 1, 1, 1),
            ('Z2-A-1-F-Middle', 'Z2', 'A', 1, 1, 2),
            ('Z2-B-1-F-Left', 'Z2', 'B', 1, 1, 1)
        ]
        
        for storage in sample_storages:
            cursor.execute("""
                INSERT OR IGNORE INTO storages 
                (storage_id, area_code, shelf_code, floor_level, front_back_position, left_middle_right_position)
                VALUES (?, ?, ?, ?, ?, ?)
            """, storage)
        
        conn.commit()
        print("✅ Successfully created receiving tables and sample storage locations!")
        
        # Show created tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%receiving%' OR name LIKE '%storage%' OR name LIKE '%pending%'")
        tables = cursor.fetchall()
        print(f"Created/verified tables: {[t[0] for t in tables]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("Running receiving tables migration...")
    success = run_migration()
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")