#!/usr/bin/env python
"""Export database fixtures to JSON files"""
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

def serialize_model(obj):
    """Convert SQLAlchemy model to dict"""
    data = {}
    for column in obj.__table__.columns:
        value = getattr(obj, column.name)
        if value is not None:
            if isinstance(value, datetime):
                data[column.name] = value.isoformat()
            else:
                data[column.name] = value
        else:
            data[column.name] = None
    return data

def export_fixtures():
    """Export all test data to JSON fixtures"""

    # Ensure PostgreSQL connection
    os.environ['FLASK_ENV'] = 'production'

    app = create_app('production')

    with app.app_context():
        fixtures_dir = Path(__file__).parent.parent / 'fixtures'
        fixtures_dir.mkdir(exist_ok=True)

        print("🔄 Exporting database fixtures...")

        # Export Users
        users = User.query.all()
        users_data = [serialize_model(user) for user in users]
        with open(fixtures_dir / 'users.json', 'w', encoding='utf-8') as f:
            json.dump(users_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Exported {len(users_data)} users")

        # Export Suppliers
        suppliers = Supplier.query.all()
        suppliers_data = [serialize_model(supplier) for supplier in suppliers]
        with open(fixtures_dir / 'suppliers.json', 'w', encoding='utf-8') as f:
            json.dump(suppliers_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Exported {len(suppliers_data)} suppliers")

        # Export Item Categories
        categories = ItemCategory.query.all()
        categories_data = [serialize_model(category) for category in categories]
        with open(fixtures_dir / 'categories.json', 'w', encoding='utf-8') as f:
            json.dump(categories_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Exported {len(categories_data)} categories")

        # Export System Settings
        settings = SystemSettings.query.all()
        settings_data = [serialize_model(setting) for setting in settings]
        with open(fixtures_dir / 'system_settings.json', 'w', encoding='utf-8') as f:
            json.dump(settings_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Exported {len(settings_data)} system settings")

        # Create metadata file
        metadata = {
            'exported_at': datetime.now().isoformat(),
            'database_url': os.environ.get('DATABASE_URL', '').split('@')[1] if '@' in os.environ.get('DATABASE_URL', '') else 'unknown',
            'tables': {
                'users': len(users_data),
                'suppliers': len(suppliers_data),
                'categories': len(categories_data),
                'system_settings': len(settings_data)
            }
        }

        with open(fixtures_dir / 'metadata.json', 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        print(f"\n🎉 Fixtures exported successfully!")
        print(f"📁 Location: {fixtures_dir}")
        print(f"📊 Total records: {sum(metadata['tables'].values())}")
        print(f"⏰ Exported at: {metadata['exported_at']}")

        return True

if __name__ == '__main__':
    try:
        export_fixtures()
    except Exception as e:
        print(f"❌ Export failed: {str(e)}")
        sys.exit(1)