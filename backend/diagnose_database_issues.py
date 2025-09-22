#!/usr/bin/env python
"""Comprehensive database issue diagnosis tool for PostgreSQL"""
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
    from app.models.inventory import InventoryBatch
    from app.models.receiving import PendingStorageItem
    from sqlalchemy import text
    from datetime import datetime

    app = create_app('production')
    with app.app_context():
        print("=== DATABASE DIAGNOSIS TOOL ===\n")

        # Test 1: Check pending storage items
        print("1. Checking pending storage items:")
        pending_items = PendingStorageItem.query.filter_by(storage_status='pending').all()
        print(f"   Found {len(pending_items)} pending items")
        if pending_items:
            item = pending_items[0]
            print(f"   Sample item: ID={item.pending_id}, Name={item.item_name}")

        # Test 2: Check inventory_batches table structure
        print("\n2. Checking inventory_batches table structure:")
        result = db.session.execute(text("""
            SELECT column_name, data_type, character_maximum_length, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'inventory_batches'
            ORDER BY ordinal_position
        """))

        print("   Key columns:")
        for row in result:
            col_name, data_type, max_len, nullable = row
            if max_len:
                print(f"   - {col_name}: {data_type}({max_len}) [null={nullable}]")
            else:
                print(f"   - {col_name}: {data_type} [null={nullable}]")

        # Test 3: Try to create a test inventory batch
        print("\n3. Testing inventory batch creation:")
        if pending_items:
            test_item = pending_items[0]
            test_batch = InventoryBatch(
                item_name=test_item.item_name,
                item_specification=test_item.item_specification or '',
                unit=test_item.unit,
                source_type='RECEIVED',
                source_po_number=test_item.source_po_number,
                source_line_number=1,  # Use small number for test
                original_quantity=float(test_item.quantity),
                current_quantity=float(test_item.quantity),
                batch_status='active',
                received_date=test_item.arrival_date,
                receiver_id=19,  # harry's user_id in remote
                receiver_name=test_item.receiver or 'Test User'
            )

            try:
                db.session.add(test_batch)
                db.session.flush()
                print(f"   ✓ Test batch created successfully (ID: {test_batch.batch_id})")
                db.session.rollback()  # Don't save test data
            except Exception as e:
                print(f"   ✗ Failed to create batch: {e}")
                db.session.rollback()

        # Test 4: Check for any constraint violations
        print("\n4. Checking foreign key constraints on inventory_batches:")
        result = db.session.execute(text("""
            SELECT
                kcu.column_name,
                ccu.table_name AS foreign_table,
                ccu.column_name AS foreign_column
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.table_name = 'inventory_batches'
            AND tc.constraint_type = 'FOREIGN KEY'
        """))

        for row in result:
            print(f"   - {row[0]} -> {row[1]}.{row[2]}")

        print("\n=== DIAGNOSIS COMPLETE ===")
        print("\nRecommendations:")
        print("- If string truncation errors occur, check VARCHAR field lengths")
        print("- If foreign key errors occur, verify referenced records exist")
        print("- Check that all required fields are provided with valid data")

except Exception as e:
    print(f"Script error: {e}")
    import traceback
    traceback.print_exc()