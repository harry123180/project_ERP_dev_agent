#!/usr/bin/env python
"""Check harry123180 user details"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Force PostgreSQL connection
database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:64946849@localhost:5432/erp_production')
os.environ['DATABASE_URL'] = database_url
os.environ['FLASK_ENV'] = 'production'

try:
    from app import create_app, db
    from app.models.user import User

    app = create_app('production')
    with app.app_context():
        user = User.query.filter_by(username='harry123180').first()
        if user:
            print(f"User found: {user.username}")
            print(f"User ID: {user.user_id}")
            print(f"Chinese name: '{user.chinese_name}'")
            print(f"Length of chinese_name: {len(user.chinese_name) if user.chinese_name else 0}")
            print(f"Is chinese_name empty? {user.chinese_name == ''}")
            print(f"Is chinese_name None? {user.chinese_name is None}")
        else:
            print("User harry123180 not found")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()