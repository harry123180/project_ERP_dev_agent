#!/usr/bin/env python3
"""
Database migration script to create inventory batch tracking tables.
This supports the PM's requirement for batch management by source PO number.
"""

import sqlite3
from datetime import datetime
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_inventory_tables():
    """Create inventory batch tracking tables"""
    
    # Connect to database
    db_path = 'instance/erp_development.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"Creating inventory batch tracking tables in {db_path}...")
    
    try:
        # Create inventory_batches table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory_batches (
                batch_id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name VARCHAR(200) NOT NULL,
                item_specification TEXT,
                unit VARCHAR(20) NOT NULL,
                source_type VARCHAR(20) NOT NULL,
                source_po_number VARCHAR(50) NOT NULL,
                source_line_number INTEGER,
                original_quantity DECIMAL(10, 2) NOT NULL,
                current_quantity DECIMAL(10, 2) NOT NULL,
                batch_status VARCHAR(20) DEFAULT 'active',
                received_date DATE NOT NULL,
                receiver_id INTEGER,
                receiver_name VARCHAR(50),
                primary_storage_id VARCHAR(20),
                lot_number VARCHAR(50),
                expiry_date DATE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (receiver_id) REFERENCES users (user_id),
                FOREIGN KEY (primary_storage_id) REFERENCES storages (storage_id)
            )
        ''')
        
        # Create indexes for inventory_batches
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_inventory_batches_item_name ON inventory_batches (item_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_inventory_batches_source_po ON inventory_batches (source_po_number)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_inventory_batches_received_date ON inventory_batches (received_date)')
        
        # Create inventory_batch_storage table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory_batch_storage (
                allocation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id INTEGER NOT NULL,
                storage_id VARCHAR(20) NOT NULL,
                quantity DECIMAL(10, 2) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (batch_id) REFERENCES inventory_batches (batch_id),
                FOREIGN KEY (storage_id) REFERENCES storages (storage_id)
            )
        ''')
        
        # Create inventory_movements table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory_movements (
                movement_id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id INTEGER NOT NULL,
                movement_type VARCHAR(20) NOT NULL,
                movement_subtype VARCHAR(30),
                quantity DECIMAL(10, 2) NOT NULL,
                from_storage_id VARCHAR(20),
                to_storage_id VARCHAR(20),
                operator_id INTEGER NOT NULL,
                movement_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                reference_type VARCHAR(30),
                reference_number VARCHAR(50),
                reference_line INTEGER,
                reason_code VARCHAR(20),
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (batch_id) REFERENCES inventory_batches (batch_id),
                FOREIGN KEY (from_storage_id) REFERENCES storages (storage_id),
                FOREIGN KEY (to_storage_id) REFERENCES storages (storage_id),
                FOREIGN KEY (operator_id) REFERENCES users (user_id)
            )
        ''')
        
        # Create indexes for inventory_movements
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_inventory_movements_batch_id ON inventory_movements (batch_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_inventory_movements_date ON inventory_movements (movement_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_inventory_movements_operator ON inventory_movements (operator_id)')
        
        # Create trigger to update inventory_batches.updated_at
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS trigger_inventory_batches_updated_at
            AFTER UPDATE ON inventory_batches
            FOR EACH ROW
            BEGIN
                UPDATE inventory_batches 
                SET updated_at = CURRENT_TIMESTAMP 
                WHERE batch_id = NEW.batch_id;
            END
        ''')
        
        # Create trigger to update inventory_batch_storage.updated_at
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS trigger_inventory_batch_storage_updated_at
            AFTER UPDATE ON inventory_batch_storage
            FOR EACH ROW
            BEGIN
                UPDATE inventory_batch_storage 
                SET updated_at = CURRENT_TIMESTAMP 
                WHERE allocation_id = NEW.allocation_id;
            END
        ''')
        
        # Commit the changes
        conn.commit()
        print("✅ Successfully created inventory batch tracking tables")
        
        # Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'inventory_%'")
        tables = cursor.fetchall()
        print(f"✅ Created tables: {[table[0] for table in tables]}")
        
    except Exception as e:
        print(f"❌ Error creating inventory tables: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def migrate_existing_data():
    """Migrate existing storage history data to inventory batches (optional)"""
    print("Note: Data migration from existing storage_history to inventory_batches is optional")
    print("For now, new batches will be created as items are received going forward.")
    print("If you need to migrate existing data, please run a separate migration script.")


if __name__ == '__main__':
    print("🚀 Starting inventory batch tracking database migration...")
    print("This will create tables to support PM's batch management requirements:")
    print("- inventory_batches: Track items by source PO number")
    print("- inventory_batch_storage: Storage distribution")
    print("- inventory_movements: Enhanced movement history")
    print()
    
    create_inventory_tables()
    migrate_existing_data()
    
    print()
    print("🎉 Inventory batch tracking migration completed!")
    print("The system now supports:")
    print("- ✅ Batch tracking by source PO number")
    print("- ✅ Storage distribution tracking")
    print("- ✅ Enhanced movement history")
    print("- ✅ Inventory details view with tabs")
    print()
    print("Next: Start the backend server and test the new features!")