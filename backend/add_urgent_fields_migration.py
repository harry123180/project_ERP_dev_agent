#!/usr/bin/env python3
"""
Migration script to add urgent fields to request_orders table
"""

import sqlite3
import os
from datetime import datetime

def add_urgent_fields():
    """Add urgent fields to request_orders table"""
    db_path = 'erp_development.db'

    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("Adding urgent fields to request_orders table...")

        # Check if columns already exist
        cursor.execute("PRAGMA table_info(request_orders)")
        columns = [column[1] for column in cursor.fetchall()]

        # Add is_urgent column if it doesn't exist
        if 'is_urgent' not in columns:
            cursor.execute("ALTER TABLE request_orders ADD COLUMN is_urgent BOOLEAN DEFAULT FALSE")
            print("✓ Added is_urgent column")
        else:
            print("✓ is_urgent column already exists")

        # Add expected_delivery_date column if it doesn't exist
        if 'expected_delivery_date' not in columns:
            cursor.execute("ALTER TABLE request_orders ADD COLUMN expected_delivery_date DATE")
            print("✓ Added expected_delivery_date column")
        else:
            print("✓ expected_delivery_date column already exists")

        # Add urgent_reason column if it doesn't exist
        if 'urgent_reason' not in columns:
            cursor.execute("ALTER TABLE request_orders ADD COLUMN urgent_reason TEXT")
            print("✓ Added urgent_reason column")
        else:
            print("✓ urgent_reason column already exists")

        # Set default values for existing records
        cursor.execute("UPDATE request_orders SET is_urgent = FALSE WHERE is_urgent IS NULL")
        print("✓ Set default values for existing records")

        conn.commit()
        print("✓ Migration completed successfully")

        # Verify the changes
        cursor.execute("PRAGMA table_info(request_orders)")
        columns_after = cursor.fetchall()
        print("\nCurrent table structure:")
        for column in columns_after:
            print(f"  - {column[1]} {column[2]}")

        return True

    except Exception as e:
        print(f"Error during migration: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Starting urgent fields migration...")
    success = add_urgent_fields()
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")