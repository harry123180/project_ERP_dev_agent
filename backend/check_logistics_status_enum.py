#!/usr/bin/env python
"""Check consolidation_logistics_status_enum values in PostgreSQL"""
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
        print("=== CHECKING CONSOLIDATION LOGISTICS STATUS ENUM VALUES ===\n")

        # Check enum values
        result = db.session.execute(text("""
            SELECT unnest(enum_range(NULL::consolidation_logistics_status_enum))::text as enum_value
        """))

        print("Allowed logistics_status values:")
        allowed_values = []
        for row in result:
            allowed_values.append(row[0])
            print(f"   - '{row[0]}'")

        print(f"\nTotal: {len(allowed_values)} allowed values")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()