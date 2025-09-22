#!/usr/bin/env python
"""Create test international POs with shipped status for consolidation testing"""
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Force PostgreSQL connection
database_url = 'postgresql://postgres:64946849@localhost:5432/erp_production'
os.environ['DATABASE_URL'] = database_url
os.environ['FLASK_ENV'] = 'production'

print(f"[DB] Connecting to: {database_url}")

try:
    from app import create_app, db
    from app.models import PurchaseOrder, Supplier
    from sqlalchemy import text

    app = create_app('production')
    with app.app_context():
        print("=== CHECKING AND UPDATING INTERNATIONAL POs ===\n")

        # First, check existing international POs
        print("1. Checking existing international POs...")
        intl_pos = db.session.query(PurchaseOrder)\
            .join(Supplier, PurchaseOrder.supplier_id == Supplier.supplier_id)\
            .filter(Supplier.supplier_region == 'international')\
            .all()

        print(f"   Found {len(intl_pos)} international POs")

        if intl_pos:
            # Update some to 'shipped' status for testing
            print("\n2. Updating POs to 'shipped' status...")
            count = 0
            for po in intl_pos[:3]:  # Update first 3 POs
                if po.purchase_status == 'purchased' and not po.consolidation_id:
                    po.delivery_status = 'shipped'
                    po.expected_delivery_date = datetime.now() + timedelta(days=7)
                    po.updated_at = datetime.now()
                    count += 1
                    print(f"   ✓ Updated {po.purchase_order_no} to 'shipped' status")

            if count > 0:
                db.session.commit()
                print(f"\n   Successfully updated {count} POs to 'shipped' status")
            else:
                print("   No POs needed updating")

        # Verify the update
        print("\n3. Verifying international POs with 'shipped' status...")
        shipped_pos = db.session.query(PurchaseOrder)\
            .join(Supplier, PurchaseOrder.supplier_id == Supplier.supplier_id)\
            .filter(Supplier.supplier_region == 'international')\
            .filter(PurchaseOrder.delivery_status == 'shipped')\
            .filter(PurchaseOrder.consolidation_id == None)\
            .all()

        print(f"   Found {len(shipped_pos)} eligible POs for consolidation:")
        for po in shipped_pos:
            print(f"      - {po.purchase_order_no}: {po.supplier_name} (Status: {po.delivery_status})")

        if not shipped_pos:
            print("\n   WARNING: No international POs with 'shipped' status found!")
            print("   You may need to create some test purchase orders first.")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()