#!/usr/bin/env python
"""Debug requisition creation issue - Safe diagnostic script"""
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Force PostgreSQL connection
database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:64946849@localhost:5432/erp_production')
os.environ['DATABASE_URL'] = database_url
os.environ['FLASK_ENV'] = 'production'

print(f"[DB] Connecting to: {database_url}")

try:
    from app import create_app, db
    from app.models.request_order import RequestOrder
    from sqlalchemy import text

    app = create_app('production')

    with app.app_context():
        print("=== DEBUGGING REQUISITION CREATION ISSUE ===")

        # 1. Check database connection
        print("\n1. Testing database connection...")
        try:
            result = db.session.execute(text("SELECT 1"))
            print("✓ Database connection OK")
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
            exit(1)

        # 2. Check RequestOrder table structure
        print("\n2. Checking RequestOrder table structure...")
        try:
            result = db.session.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'request_orders'
                ORDER BY ordinal_position
            """))

            columns = {}
            for row in result:
                columns[row[0]] = {'type': row[1], 'nullable': row[2]}

            # Check critical fields
            critical_fields = [
                'request_order_no', 'requester_id', 'requester_name',
                'usage_type', 'order_status', 'is_urgent',
                'expected_delivery_date', 'urgent_reason'
            ]

            missing_fields = []
            for field in critical_fields:
                if field in columns:
                    print(f"✓ {field}: {columns[field]['type']} (nullable: {columns[field]['nullable']})")
                else:
                    missing_fields.append(field)
                    print(f"✗ MISSING: {field}")

            if missing_fields:
                print(f"\nERROR: Missing fields: {missing_fields}")
                print("Database schema is incomplete.")
                exit(1)
            else:
                print("\n✓ All required fields exist")

        except Exception as e:
            print(f"✗ Error checking table structure: {e}")
            exit(1)

        # 3. Test model instantiation
        print("\n3. Testing RequestOrder model...")
        try:
            test_order = RequestOrder(
                request_order_no='DEBUG_TEST_001',
                requester_id=1,
                requester_name='Debug Test User',
                usage_type='daily',
                order_status='draft',
                is_urgent=False
            )
            print("✓ RequestOrder model instantiation OK")
        except Exception as e:
            print(f"✗ RequestOrder model error: {e}")
            exit(1)

        # 4. Test basic database insertion (without commit)
        print("\n4. Testing database insertion...")
        try:
            db.session.add(test_order)
            db.session.flush()  # Test without commit
            print("✓ Database insertion test OK")
            db.session.rollback()  # Rollback test data
        except Exception as e:
            print(f"✗ Database insertion failed: {e}")
            db.session.rollback()
            print("\nThis suggests the issue is with database constraints or data validation")
            print("Detailed error:", str(e))
            exit(1)

        # 5. Check user exists
        print("\n5. Checking if test user exists...")
        try:
            from app.models.user import User
            test_user = User.query.filter_by(username='harry123180').first()
            if test_user:
                print(f"✓ User harry123180 exists: ID={test_user.user_id}, Role={test_user.role}")
            else:
                print("✗ User harry123180 not found")
        except Exception as e:
            print(f"✗ Error checking user: {e}")

        print("\n=== DIAGNOSIS COMPLETE ===")
        print("If all tests pass, the issue is likely in:")
        print("1. Frontend data format")
        print("2. API request validation")
        print("3. Missing foreign key references (project_id, etc.)")

except Exception as e:
    print(f"SCRIPT ERROR: {e}")
    import traceback
    traceback.print_exc()