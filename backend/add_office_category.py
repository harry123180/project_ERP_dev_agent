#!/usr/bin/env python
"""Add missing office category to database"""
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
    from app.models.item_category import ItemCategory

    app = create_app('production')
    with app.app_context():
        # 檢查現有分類
        categories = ItemCategory.query.all()
        print(f'Current categories: {[c.category_code for c in categories]}')

        # 建立缺少的office分類
        if not ItemCategory.query.filter_by(category_code='office').first():
            office_cat = ItemCategory(
                category_code='office',
                category_name='辦公用品',
                sort_order=5
            )
            db.session.add(office_cat)
            db.session.commit()
            print('Added office category')
        else:
            print('Office category already exists')

        # 列出所有分類
        print('\nAll categories:')
        categories = ItemCategory.query.all()
        for cat in categories:
            print(f'{cat.category_code}: {cat.category_name}')

except Exception as e:
    print(f'Error: {e}')