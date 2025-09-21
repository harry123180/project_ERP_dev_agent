#!/usr/bin/env python
"""
Test Flask application with PostgreSQL
"""
import os
import sys

# Set PostgreSQL environment variables
os.environ['USE_POSTGRESQL'] = 'true'
os.environ['POSTGRES_USER'] = 'erp_user'
os.environ['POSTGRES_PASSWORD'] = '271828'
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '5432'
os.environ['POSTGRES_DB'] = 'erp_database'

# Change to backend directory
os.chdir('backend')

# Import and run the app
from app import create_app, db
from app.models import User

print("="*50)
print("Testing Flask Application with PostgreSQL")
print("="*50)

# Create app instance
app = create_app('development')

with app.app_context():
    try:
        # Test database connection
        print("\n1. Testing database connection...")
        db.engine.execute("SELECT 1")
        print("✓ Database connected successfully")

        # Check tables
        print("\n2. Checking tables...")
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"✓ Found {len(tables)} tables: {', '.join(tables)}")

        # Create a test user if needed
        print("\n3. Creating test admin user...")
        from werkzeug.security import generate_password_hash

        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                chinese_name='系統管理員',
                username='admin',
                password=generate_password_hash('admin123'),
                department='IT',
                role='Admin',
                is_active=True
            )
            db.session.add(admin)
            db.session.commit()
            print("✓ Admin user created")
        else:
            print("✓ Admin user already exists")

        # Query test
        print("\n4. Testing query...")
        users = User.query.all()
        print(f"✓ Found {len(users)} users in database")

        print("\n" + "="*50)
        print("✅ PostgreSQL setup complete!")
        print("="*50)
        print("\nYou can now run the application with:")
        print("  cd backend")
        print("  set USE_POSTGRESQL=true")
        print("  python app.py")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)