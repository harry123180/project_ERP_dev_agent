#!/usr/bin/env python
"""Import database fixtures from JSON files"""
import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', 'backend', '.env'))

from app import create_app, db
from app.models import User, Supplier, ItemCategory, SystemSettings
from werkzeug.security import generate_password_hash

def parse_datetime(date_string):
    """Parse ISO datetime string"""
    if date_string:
        return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
    return None

def import_users(data):
    """Import users from fixture data"""
    count = 0
    for item in data:
        # Check if user already exists
        existing = User.query.filter_by(username=item['username']).first()
        if existing:
            print(f"⚠️  User '{item['username']}' already exists, skipping")
            continue

        user = User(
            chinese_name=item['chinese_name'],
            username=item['username'],
            password=item['password'],  # Already hashed from export
            department=item.get('department'),
            job_title=item.get('job_title'),
            role=item['role'],
            is_active=item.get('is_active', True)
        )

        # Set timestamps if available
        if item.get('created_at'):
            user.created_at = parse_datetime(item['created_at'])
        if item.get('updated_at'):
            user.updated_at = parse_datetime(item['updated_at'])

        db.session.add(user)
        count += 1

    return count

def import_suppliers(data):
    """Import suppliers from fixture data"""
    count = 0
    for item in data:
        # Check if supplier already exists
        existing = Supplier.query.filter_by(supplier_id=item['supplier_id']).first()
        if existing:
            print(f"⚠️  Supplier '{item['supplier_id']}' already exists, skipping")
            continue

        supplier = Supplier(**{k: v for k, v in item.items() if k != 'created_at' and k != 'updated_at'})

        # Set timestamps if available
        if item.get('created_at'):
            supplier.created_at = parse_datetime(item['created_at'])
        if item.get('updated_at'):
            supplier.updated_at = parse_datetime(item['updated_at'])

        db.session.add(supplier)
        count += 1

    return count

def import_categories(data):
    """Import item categories from fixture data"""
    count = 0
    for item in data:
        # Check if category already exists
        existing = ItemCategory.query.filter_by(category_code=item['category_code']).first()
        if existing:
            print(f"⚠️  Category '{item['category_code']}' already exists, skipping")
            continue

        category = ItemCategory(**item)
        db.session.add(category)
        count += 1

    return count

def import_system_settings(data):
    """Import system settings from fixture data"""
    count = 0
    for item in data:
        # Check if setting already exists
        existing = SystemSettings.query.filter_by(
            setting_type=item['setting_type'],
            setting_key=item['setting_key']
        ).first()

        if existing:
            # Update existing setting
            existing.setting_value = item['setting_value']
            existing.setting_description = item.get('setting_description')
            print(f"🔄 Updated setting '{item['setting_key']}'")
        else:
            # Create new setting
            setting = SystemSettings(**item)
            db.session.add(setting)
            count += 1

    return count

def import_fixtures(force=False):
    """Import all fixtures from JSON files"""

    # Ensure PostgreSQL connection
    os.environ['FLASK_ENV'] = 'production'

    app = create_app('production')

    with app.app_context():
        fixtures_dir = Path(__file__).parent.parent / 'fixtures'

        if not fixtures_dir.exists():
            print("❌ Fixtures directory not found. Run export_fixtures.py first.")
            return False

        print("🔄 Importing database fixtures...")

        # Check metadata
        metadata_file = fixtures_dir / 'metadata.json'
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            print(f"📊 Fixture metadata: {metadata['exported_at']}")
            print(f"📋 Total records to import: {sum(metadata['tables'].values())}")

        total_imported = 0

        # Import Users
        users_file = fixtures_dir / 'users.json'
        if users_file.exists():
            with open(users_file, 'r', encoding='utf-8') as f:
                users_data = json.load(f)
            count = import_users(users_data)
            total_imported += count
            print(f"✅ Imported {count} users")

        # Import Suppliers
        suppliers_file = fixtures_dir / 'suppliers.json'
        if suppliers_file.exists():
            with open(suppliers_file, 'r', encoding='utf-8') as f:
                suppliers_data = json.load(f)
            count = import_suppliers(suppliers_data)
            total_imported += count
            print(f"✅ Imported {count} suppliers")

        # Import Categories
        categories_file = fixtures_dir / 'categories.json'
        if categories_file.exists():
            with open(categories_file, 'r', encoding='utf-8') as f:
                categories_data = json.load(f)
            count = import_categories(categories_data)
            total_imported += count
            print(f"✅ Imported {count} categories")

        # Import System Settings
        settings_file = fixtures_dir / 'system_settings.json'
        if settings_file.exists():
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings_data = json.load(f)
            count = import_system_settings(settings_data)
            total_imported += count
            print(f"✅ Imported {count} system settings")

        # Commit all changes
        try:
            db.session.commit()
            print(f"\n🎉 Import completed successfully!")
            print(f"📊 Total records imported: {total_imported}")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Import failed during commit: {str(e)}")
            return False

        return True

if __name__ == '__main__':
    try:
        force = '--force' in sys.argv
        import_fixtures(force=force)
    except Exception as e:
        print(f"❌ Import failed: {str(e)}")
        sys.exit(1)