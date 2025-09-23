#!/usr/bin/env python
"""Check consolidation data directly in database"""
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
        print("=== CHECKING CONSOLIDATIONS IN DATABASE ===\n")

        # Check consolidations table
        result = db.session.execute(text("""
            SELECT consolidation_id, consolidation_name, logistics_status,
                   created_by, created_at
            FROM consolidations
            ORDER BY created_at DESC
        """))

        consolidations = []
        for row in result:
            consolidations.append({
                'id': row[0],
                'name': row[1],
                'status': row[2],
                'created_by': row[3],
                'created_at': row[4]
            })

        print(f"Found {len(consolidations)} consolidations in database:")
        for c in consolidations:
            print(f"\nConsolidation: {c['id']}")
            print(f"  Name: {c['name']}")
            print(f"  Status: {c['status']}")
            print(f"  Created by: {c['created_by']}")
            print(f"  Created at: {c['created_at']}")

            # Check consolidation_pos for this consolidation
            pos_result = db.session.execute(text("""
                SELECT cp.consolidation_id, cp.purchase_order_id,
                       po.purchase_order_no, po.supplier_name
                FROM consolidation_pos cp
                LEFT JOIN purchase_orders po ON cp.purchase_order_id = po.purchase_order_id
                WHERE cp.consolidation_id = :consolidation_id
            """), {'consolidation_id': c['id']})

            pos = []
            for po_row in pos_result:
                pos.append({
                    'po_id': po_row[1],
                    'po_no': po_row[2],
                    'supplier': po_row[3]
                })

            print(f"  Linked POs: {len(pos)}")
            for po in pos:
                print(f"    - PO {po['po_no']}: {po['supplier']}")

        if not consolidations:
            print("No consolidations found in database!")

            # Check if consolidation_pos has any orphaned records
            print("\n=== CHECKING CONSOLIDATION_POS TABLE ===")
            orphaned = db.session.execute(text("""
                SELECT consolidation_id, purchase_order_id
                FROM consolidation_pos
            """))

            orphaned_count = 0
            for row in orphaned:
                orphaned_count += 1
                print(f"Found record: consolidation_id={row[0]}, po_id={row[1]}")

            if orphaned_count == 0:
                print("No records in consolidation_pos table")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()