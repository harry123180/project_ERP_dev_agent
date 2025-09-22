#!/usr/bin/env python
"""Initialize PostgreSQL database for ERP system"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set PostgreSQL connection from .env
database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/erp_production')
os.environ['DATABASE_URL'] = database_url
os.environ['FLASK_ENV'] = 'production'

print(f"[DB] Connecting to: {database_url}")

try:
    from app import create_app, db
    from app.models import User, Supplier, ItemCategory, SystemSettings
    from werkzeug.security import generate_password_hash

    # Create Flask app with production config
    app = create_app('production')

    with app.app_context():
        # Create all tables
        print("Creating database tables...")
        db.create_all()
        print("✓ Database tables created")

        # Check if admin exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            # Create admin user (based on seed_db in app.py)
            admin = User(
                chinese_name='系統管理員',
                username='admin',
                password=generate_password_hash('admin123'),
                department='IT部門',
                job_title='系統管理員',
                role='Admin'
            )
            db.session.add(admin)

            # Create test procurement user
            procurement = User(
                chinese_name='採購專員',
                username='procurement',
                password=generate_password_hash('proc123'),
                department='採購部',
                job_title='採購專員',
                role='Procurement'
            )
            db.session.add(procurement)

            print("✓ Creating users...")
        else:
            print("✓ Admin user already exists")

        # Check if suppliers exist
        supplier_count = Supplier.query.count()
        if supplier_count == 0:
            # Create sample suppliers (from seed_db)
            supplier1 = Supplier(
                supplier_id='T001',
                supplier_name_zh='台積電',
                supplier_name_en='TSMC',
                supplier_region='domestic',
                supplier_phone='02-12345678',
                supplier_email='contact@tsmc.com',
                payment_terms='月結30天'
            )

            supplier2 = Supplier(
                supplier_id='I001',
                supplier_name_zh='英特爾',
                supplier_name_en='Intel Corporation',
                supplier_region='international',
                supplier_phone='+1-408-765-8080',
                supplier_email='contact@intel.com',
                payment_terms='月結60天'
            )

            db.session.add_all([supplier1, supplier2])
            print("✓ Creating sample suppliers...")
        else:
            print(f"✓ {supplier_count} suppliers already exist")

        # Check if categories exist
        category_count = ItemCategory.query.count()
        if category_count == 0:
            # Create item categories
            categories = [
                ItemCategory(category_code='01', category_name='電子元件', sort_order=1),
                ItemCategory(category_code='02', category_name='機械零件', sort_order=2),
                ItemCategory(category_code='03', category_name='辦公用品', sort_order=3),
                ItemCategory(category_code='04', category_name='實驗設備', sort_order=4),
            ]
            db.session.add_all(categories)
            print("✓ Creating item categories...")
        else:
            print(f"✓ {category_count} categories already exist")

        # Check if system settings exist
        settings_count = SystemSettings.query.count()
        if settings_count == 0:
            # Create system settings
            settings = [
                SystemSettings(
                    setting_type='tax',
                    setting_key='default_tax_rate',
                    setting_value='5.0',
                    setting_description='預設稅率(%)'
                ),
                SystemSettings(
                    setting_type='system',
                    setting_key='company_name',
                    setting_value='創新科技股份有限公司',
                    setting_description='公司名稱'
                ),
            ]
            db.session.add_all(settings)
            print("✓ Creating system settings...")
        else:
            print(f"✓ {settings_count} settings already exist")

        # Commit all changes
        db.session.commit()

        print("\n✅ PostgreSQL database initialized successfully!")
        print("\n登入帳號:")
        print("  管理員 - username: admin, password: admin123")
        print("  採購員 - username: procurement, password: proc123")
        print("\n您現在可以啟動應用程式:")
        print("  python app.py")
        print("\n或使用 Flask CLI:")
        print("  flask run --host=0.0.0.0 --port=5000")

except Exception as e:
    print(f"\n❌ 錯誤: {str(e)}")
    print("\n可能的原因:")
    print("1. PostgreSQL 服務未啟動")
    print("2. 資料庫 'erp_production' 不存在")
    print("3. .env 文件中的 DATABASE_URL 設定錯誤")
    print("4. 缺少必要的 Python 套件")
    print("\n請檢查後重試")
    sys.exit(1)