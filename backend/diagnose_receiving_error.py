#!/usr/bin/env python
"""Diagnose receiving error in detail"""
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
    from app.models.receiving import ReceivingRecord
    from app.models.purchase_order import PurchaseOrderItem
    from sqlalchemy import text

    app = create_app('production')
    with app.app_context():
        print("=== DIAGNOSING RECEIVING ERROR ===\n")

        # Check if the PO item exists with the exact detail_id
        print("1. Checking PO item existence:")
        po_item = PurchaseOrderItem.query.filter_by(
            detail_id=1,
            purchase_order_no='PO20250923001'
        ).first()

        if po_item:
            print(f"✓ PO item found: detail_id={po_item.detail_id}")
        else:
            print("✗ PO item NOT found")

        # Check foreign key constraint on receiving_records table
        print("\n2. Checking foreign key constraints:")
        result = db.session.execute(text("""
            SELECT
                tc.constraint_name,
                tc.constraint_type,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.table_name = 'receiving_records'
            AND tc.constraint_type = 'FOREIGN KEY'
        """))

        for row in result:
            print(f"  - {row[2]} -> {row[3]}.{row[4]} (constraint: {row[0]})")

        # Try to insert a test receiving record
        print("\n3. Testing receiving record insertion:")
        test_record = ReceivingRecord(
            purchase_order_no='PO20250923001',
            po_item_detail_id=1,
            requisition_number='REQ20250923002',
            consolidation_number='',
            item_name='Test Item',
            item_specification='Test Spec',
            quantity_shipped=1,
            quantity_received=1,
            unit='個',
            receiver_id=19,
            receiver_name='Test User',
            receiving_status='received_pending_storage'
        )

        try:
            db.session.add(test_record)
            db.session.flush()
            print("✓ Test receiving record created successfully")
            print(f"  - receiving_id: {test_record.receiving_id}")
            db.session.rollback()
        except Exception as e:
            print(f"✗ Failed to create receiving record: {e}")
            db.session.rollback()

            # Check the exact error
            import traceback
            traceback.print_exc()

except Exception as e:
    print(f"Script error: {e}")
    import traceback
    traceback.print_exc()