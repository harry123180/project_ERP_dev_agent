#!/usr/bin/env python
"""Initialize PostgreSQL database for ERP system"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set PostgreSQL connection
os.environ['DATABASE_URL'] = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/erp_production')
os.environ['FLASK_ENV'] = 'production'

from app import create_app, db
from app.models import User

app = create_app('production')

with app.app_context():
    # Create all tables
    db.create_all()
    print("✓ Database tables created")
    
    # Check if admin exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        # Create admin user
        admin = User(
            username='admin',
            email='admin@example.com',
            role='admin',
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✓ Admin user created (username: admin, password: admin123)")
    else:
        print("✓ Admin user already exists")
    
    print("\n✅ PostgreSQL database initialized successfully!")
    print("\nYou can now start the application with:")
    print("  python app.py")
    print("\nOr for production with PostgreSQL:")
    print("  python run_with_postgres.py")