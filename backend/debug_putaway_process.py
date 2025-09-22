#!/usr/bin/env python
"""Test the complete putaway process step by step"""
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
    from app.models.inventory import InventoryBatch, InventoryBatchStorage
    from app.models.receiving import PendingStorageItem
    from app.models.storage import Storage, StorageHistory
    from datetime import datetime

    app = create_app('production')
    with app.app_context():
        print("=== TESTING PUTAWAY PROCESS ===\n")

        # Get a pending item
        pending_item = PendingStorageItem.query.filter_by(storage_status='pending').first()
        if not pending_item:
            print("No pending items found!")
            exit(0)

        print(f"Testing with pending item: ID={pending_item.pending_id}, Name={pending_item.item_name}")

        # Step 1: Create storage location
        print("\n1. Creating storage location...")
        try:
            storage = Storage.create_storage_location('Z1', 'A', 1, 1, 1)
            db.session.add(storage)
            db.session.flush()
            print(f"   ✓ Storage created: {storage.storage_id}")
        except Exception as e:
            print(f"   ✗ Storage creation failed: {e}")
            db.session.rollback()
            exit(1)

        # Step 2: Create inventory batch
        print("\n2. Creating inventory batch...")
        try:
            batch = InventoryBatch(
                item_name=pending_item.item_name,
                item_specification=pending_item.item_specification or '',
                unit=pending_item.unit,
                source_type='RECEIVED',
                source_po_number=pending_item.source_po_number,
                source_line_number=pending_item.pending_id,
                original_quantity=float(pending_item.quantity),
                current_quantity=float(pending_item.quantity),
                batch_status='active',
                received_date=pending_item.arrival_date,
                receiver_id=19,
                receiver_name=pending_item.receiver or 'Test User'
            )
            db.session.add(batch)
            db.session.flush()
            print(f"   ✓ Batch created: ID={batch.batch_id}")
        except Exception as e:
            print(f"   ✗ Batch creation failed: {e}")
            db.session.rollback()
            exit(1)

        # Step 3: Create batch storage allocation
        print("\n3. Creating batch storage allocation...")
        try:
            batch_storage = InventoryBatchStorage(
                batch_id=batch.batch_id,
                storage_id=storage.storage_id,
                quantity=float(pending_item.quantity)
            )
            db.session.add(batch_storage)
            db.session.flush()
            print("   ✓ Batch storage allocation created")
        except Exception as e:
            print(f"   ✗ Batch storage allocation failed: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            exit(1)

        # Step 4: Create storage history
        print("\n4. Creating storage history...")
        try:
            history = StorageHistory.create_in_record(
                storage_id=storage.storage_id,
                item_id=pending_item.item_name,
                quantity=float(pending_item.quantity),
                operator_id=19,
                source_type='RECEIVED',
                source_no=pending_item.source_po_number,
                remarks=f"Putaway from PO {pending_item.source_po_number}"
            )
            db.session.add(history)
            db.session.flush()
            print("   ✓ Storage history created")
        except Exception as e:
            print(f"   ✗ Storage history creation failed: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            exit(1)

        # Step 5: Update pending item status
        print("\n5. Updating pending item status...")
        try:
            pending_item.assign_storage(storage.storage_id)
            pending_item.mark_as_stored()
            db.session.flush()
            print("   ✓ Pending item status updated")
        except Exception as e:
            print(f"   ✗ Status update failed: {e}")
            db.session.rollback()
            exit(1)

        print("\n=== ALL STEPS COMPLETED SUCCESSFULLY ===")
        print("Rolling back test data (not saving to database)...")
        db.session.rollback()
        print("Test complete!")

except Exception as e:
    print(f"Script error: {e}")
    import traceback
    traceback.print_exc()