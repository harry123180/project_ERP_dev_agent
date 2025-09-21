#!/usr/bin/env python3
"""
Database migration script for Delivery Management with Consolidation Orders feature
Adds missing columns to existing tables for the delivery management functionality
"""

import sqlite3
import sys
from pathlib import Path

# Database path
DB_PATH = "erp_development.db"

def run_migration():
    """Execute database migration for delivery management feature"""
    print("🚀 Starting database migration for Delivery Management feature...")
    
    try:
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if database exists
        if not Path(DB_PATH).exists():
            print(f"❌ Database file {DB_PATH} not found!")
            return False
        
        print("✅ Connected to database successfully")
        
        # Migration 1: Add delivery management columns to purchase_orders table
        print("\n📋 Adding delivery management columns to purchase_orders table...")
        
        delivery_columns = [
            ("delivery_status", "TEXT DEFAULT 'not_shipped' CHECK (delivery_status IN ('not_shipped', 'shipped', 'foreign_customs', 'taiwan_customs', 'in_transit', 'delivered'))"),
            ("expected_delivery_date", "DATE"),
            ("actual_delivery_date", "DATE"),
            ("consolidation_id", "TEXT"),
            ("remarks", "TEXT"),
            ("status_update_required", "BOOLEAN DEFAULT 0")
        ]
        
        for column_name, column_def in delivery_columns:
            try:
                cursor.execute(f"ALTER TABLE purchase_orders ADD COLUMN {column_name} {column_def}")
                print(f"  ✅ Added column: {column_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print(f"  ⚠️  Column {column_name} already exists, skipping")
                else:
                    print(f"  ❌ Error adding column {column_name}: {e}")
                    
        # Migration 2: Update shipment_consolidations table structure
        print("\n📋 Updating shipment_consolidations table structure...")
        
        consolidation_columns = [
            ("consolidation_name", "TEXT"),
            ("logistics_status", "TEXT DEFAULT 'shipped' CHECK (logistics_status IN ('shipped', 'foreign_customs', 'taiwan_customs', 'in_transit', 'delivered'))"),
            ("expected_delivery_date", "DATE"),
            ("actual_delivery_date", "DATE"),
            ("carrier", "TEXT"),
            ("tracking_number", "TEXT"),
            ("customs_declaration_no", "TEXT"),
            ("logistics_notes", "TEXT"),
            ("remarks", "TEXT"),
            ("created_by", "INTEGER"),
            ("total_weight", "REAL"),
            ("total_volume", "REAL")
        ]
        
        for column_name, column_def in consolidation_columns:
            try:
                cursor.execute(f"ALTER TABLE shipment_consolidations ADD COLUMN {column_name} {column_def}")
                print(f"  ✅ Added column: {column_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print(f"  ⚠️  Column {column_name} already exists, skipping")
                else:
                    print(f"  ❌ Error adding column {column_name}: {e}")
        
        # Migration 3: Create remarks_history table for audit trail
        print("\n📋 Creating remarks_history table...")
        
        create_remarks_history = """
        CREATE TABLE IF NOT EXISTS remarks_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_order_no TEXT,
            consolidation_id TEXT,
            old_remarks TEXT,
            new_remarks TEXT,
            changed_by INTEGER NOT NULL,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            change_type TEXT CHECK (change_type IN ('po_remarks', 'consolidation_remarks')) NOT NULL,
            FOREIGN KEY (purchase_order_no) REFERENCES purchase_orders(purchase_order_no),
            FOREIGN KEY (consolidation_id) REFERENCES shipment_consolidations(consolidation_id),
            FOREIGN KEY (changed_by) REFERENCES users(user_id)
        )
        """
        
        try:
            cursor.execute(create_remarks_history)
            print("  ✅ Created remarks_history table")
        except sqlite3.OperationalError as e:
            if "already exists" in str(e).lower():
                print("  ⚠️  remarks_history table already exists, skipping")
            else:
                print(f"  ❌ Error creating remarks_history table: {e}")
        
        # Migration 4: Update existing purchase orders with status_update_required flag
        print("\n📋 Updating existing purchase orders with status_update_required flag...")
        
        try:
            # Set status_update_required = 1 for purchased orders that don't have delivery status updated
            cursor.execute("""
                UPDATE purchase_orders 
                SET status_update_required = 1 
                WHERE purchase_status = 'purchased' 
                AND (delivery_status IS NULL OR delivery_status = 'not_shipped')
            """)
            
            affected_rows = cursor.rowcount
            print(f"  ✅ Updated {affected_rows} purchase orders with status_update_required flag")
        except sqlite3.OperationalError as e:
            print(f"  ❌ Error updating status_update_required: {e}")
        
        # Migration 5: Add foreign key constraint for consolidation_id (informational - SQLite doesn't enforce FK constraints by default)
        print("\n📋 Adding consolidation_id foreign key relationship...")
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_purchase_orders_consolidation_id 
                ON purchase_orders(consolidation_id)
            """)
            print("  ✅ Created index for consolidation_id foreign key")
        except sqlite3.OperationalError as e:
            print(f"  ❌ Error creating consolidation_id index: {e}")
        
        # Commit all changes
        conn.commit()
        print("\n✅ All migrations completed successfully!")
        
        # Verify the migrations
        print("\n🔍 Verifying migrations...")
        
        # Check purchase_orders columns
        cursor.execute("PRAGMA table_info(purchase_orders)")
        po_columns = [row[1] for row in cursor.fetchall()]
        required_po_cols = ['delivery_status', 'expected_delivery_date', 'consolidation_id', 'remarks', 'status_update_required']
        
        missing_po_cols = [col for col in required_po_cols if col not in po_columns]
        if missing_po_cols:
            print(f"  ❌ Missing purchase_orders columns: {missing_po_cols}")
        else:
            print("  ✅ All purchase_orders columns present")
        
        # Check consolidation columns
        cursor.execute("PRAGMA table_info(shipment_consolidations)")
        consolidation_columns = [row[1] for row in cursor.fetchall()]
        required_consolidation_cols = ['consolidation_name', 'logistics_status', 'remarks', 'created_by']
        
        missing_consolidation_cols = [col for col in required_consolidation_cols if col not in consolidation_columns]
        if missing_consolidation_cols:
            print(f"  ❌ Missing consolidation columns: {missing_consolidation_cols}")
        else:
            print("  ✅ All consolidation columns present")
        
        # Check remarks_history table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='remarks_history'")
        if cursor.fetchone():
            print("  ✅ remarks_history table exists")
        else:
            print("  ❌ remarks_history table missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()
            print("🔒 Database connection closed")

def main():
    """Main function"""
    print("=" * 60)
    print("DATABASE MIGRATION: Delivery Management with Consolidation Orders")
    print("=" * 60)
    
    success = run_migration()
    
    if success:
        print("\n🎉 Database migration completed successfully!")
        print("You can now run the delivery management tests.")
    else:
        print("\n💥 Database migration failed!")
        print("Please check the error messages above and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()