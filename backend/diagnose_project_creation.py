#!/usr/bin/env python
"""Diagnose project creation failure"""
import os
from dotenv import load_dotenv
from datetime import datetime, date

# Load environment variables
load_dotenv()

# Force PostgreSQL connection
database_url = 'postgresql://postgres:64946849@localhost:5432/erp_production'
os.environ['DATABASE_URL'] = database_url
os.environ['FLASK_ENV'] = 'production'

print(f"[DB] Connecting to: {database_url}")

try:
    from app import create_app, db
    from app.models.project import Project
    from sqlalchemy import text

    app = create_app('production')
    with app.app_context():
        print("=== DIAGNOSING PROJECT CREATION ===\n")

        # Check projects table structure
        print("1. Checking projects table structure:")
        result = db.session.execute(text("""
            SELECT column_name, data_type, character_maximum_length, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'projects'
            ORDER BY ordinal_position
        """))

        columns = {}
        for row in result:
            col_name, data_type, max_len, nullable = row
            columns[col_name] = {
                'type': data_type,
                'max_len': max_len,
                'nullable': nullable
            }
            if max_len:
                print(f"   - {col_name}: {data_type}({max_len}) [null={nullable}]")
            else:
                print(f"   - {col_name}: {data_type} [null={nullable}]")

        # Check required fields
        print("\n2. Required fields check:")
        required_fields = ['project_code', 'project_name', 'project_status']
        for field in required_fields:
            if field in columns:
                print(f"   ✓ {field} exists: {columns[field]['type']} (nullable: {columns[field]['nullable']})")
            else:
                print(f"   ✗ {field} MISSING!")

        # Test creating a project
        print("\n3. Testing project creation:")
        test_project = Project(
            project_code='TEST001',
            project_name='Test Project',
            description='Test Description',
            project_status='active',
            start_date=date.today(),
            budget=10000.0,
            customer_name='Test Customer'
        )

        try:
            db.session.add(test_project)
            db.session.flush()
            print(f"   ✓ Test project created successfully (ID: {test_project.project_id})")
            db.session.rollback()  # Don't save test data
        except Exception as e:
            print(f"   ✗ Failed to create project: {e}")
            db.session.rollback()

            # Check specific constraint
            if 'StringDataRightTruncation' in str(type(e)):
                print("\n   ERROR: String field too long!")
                print("   Check field lengths in your request")
            elif 'ForeignKeyViolation' in str(type(e)):
                print("\n   ERROR: Foreign key constraint violation!")
                print("   Check that referenced records exist")
            elif 'NotNullViolation' in str(type(e)):
                print("\n   ERROR: Required field is NULL!")
                print("   Check that all required fields are provided")

        # Check for unique constraints
        print("\n4. Checking unique constraints on projects:")
        result = db.session.execute(text("""
            SELECT
                tc.constraint_name,
                string_agg(kcu.column_name, ', ') as columns
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_name = 'projects'
            AND tc.constraint_type = 'UNIQUE'
            GROUP BY tc.constraint_name
        """))

        for row in result:
            print(f"   - {row[1]}: {row[0]}")

        print("\n=== DIAGNOSIS COMPLETE ===")
        print("\nCommon 422 error causes:")
        print("- Missing required fields (project_code, project_name, project_status)")
        print("- Invalid date format (should be YYYY-MM-DD)")
        print("- String fields exceeding maximum length")
        print("- Invalid project_status value")
        print("- Duplicate project_code (if unique constraint exists)")

except Exception as e:
    print(f"Script error: {e}")
    import traceback
    traceback.print_exc()