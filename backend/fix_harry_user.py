#!/usr/bin/env python
"""Fix harry123180 user chinese_name in PostgreSQL"""
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
    from app.models.user import User

    app = create_app('production')
    with app.app_context():
        user = User.query.filter_by(username='harry123180').first()
        if user:
            print(f"User found: {user.username}")
            print(f"Current chinese_name: '{user.chinese_name}'")

            if not user.chinese_name or user.chinese_name == '':
                user.chinese_name = 'Harry'  # Set a default name
                db.session.commit()
                print("Updated chinese_name to 'Harry'")
            else:
                print("Chinese name already set, no update needed")
        else:
            print("User harry123180 not found")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()