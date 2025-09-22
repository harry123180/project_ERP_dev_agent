#!/usr/bin/env python
"""Diagnose putaway storage assignment error"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Force PostgreSQL connection
database_url = 'postgresql://postgres:64946849@localhost:5432/erp_production'
os.environ['DATABASE_URL'] = database_url
os.environ['FLASK_ENV'] = 'production'

print(f"[DB] Connecting to: {database_url}")

try:
    from app import create_app, db
    from sqlalchemy import text

    app = create_app('production')
    with app.app_context():
        print("=== DIAGNOSING PUTAWAY ERROR ===\n")

        # Check inventory_batches table structure
        print("Checking inventory_batches table structure:")
        result = db.session.execute(text("""
            SELECT column_name, data_type, is_nullable, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'inventory_batches'
            AND column_name IN ('source_line_number', 'batch_status')
            ORDER BY ordinal_position
        """))

        for row in result:
            print(f"  - {row[0]}: {row[1]} (nullable: {row[2]}, max_length: {row[3]})")

        # Check constraints
        print("\nChecking constraints on inventory_batches:")
        result = db.session.execute(text("""
            SELECT
                tc.constraint_name,
                tc.constraint_type,
                kcu.column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_name = 'inventory_batches'
            AND tc.constraint_type IN ('PRIMARY KEY', 'FOREIGN KEY', 'UNIQUE')
        """))

        for row in result:
            print(f"  - {row[2]}: {row[1]} (constraint: {row[0]})")

except Exception as e:
    print(f"Script error: {e}")
    import traceback
    traceback.print_exc()