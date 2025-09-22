#!/usr/bin/env python
"""Update database schema for remote deployment"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set PostgreSQL connection from .env
database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:64946849@localhost:5432/erp_production')
os.environ['DATABASE_URL'] = database_url
os.environ['FLASK_ENV'] = 'production'

print(f"[DB] Connecting to: {database_url}")

try:
    from app import create_app, db

    # Create Flask app with production config
    app = create_app('production')

    with app.app_context():
        print("Dropping and recreating all tables...")
        db.drop_all()
        db.create_all()
        print("Database schema updated successfully")

        # Check if request_orders table has new columns
        result = db.engine.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'request_orders'")
        columns = [row[0] for row in result]
        print(f"RequestOrder columns: {columns}")

        # Check for urgent fields
        urgent_fields = ['is_urgent', 'expected_delivery_date', 'urgent_reason']
        missing_fields = []

        for field in urgent_fields:
            if field in columns:
                print(f"[OK] {field} column exists")
            else:
                print(f"[ERROR] {field} column missing")
                missing_fields.append(field)

        if not missing_fields:
            print("All required columns exist - schema update successful!")
        else:
            print(f"Missing columns: {missing_fields}")

except Exception as e:
    print(f"Error: {str(e)}")
    print("\nPossible causes:")
    print("1. PostgreSQL service not running")
    print("2. Database 'erp_production' does not exist")
    print("3. Incorrect DATABASE_URL in .env file")
    print("4. Missing required Python packages")
    print("\nPlease check and try again")