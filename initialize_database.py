#!/usr/bin/env python3
"""
Database initialization script for ERP system with Delivery Management
Creates all tables with proper schema including delivery management fields
"""

import os
import sys
sys.path.append('backend')

from app import create_app, db
from werkzeug.security import generate_password_hash

def initialize_database():
    """Initialize database with all tables and sample data"""
    print("🚀 Initializing ERP Database with Delivery Management...")
    
    # Create Flask app
    app = create_app('development')
    
    with app.app_context():
        try:
            # Drop all existing tables to start fresh
            print("🗑️  Dropping existing tables...")
            db.drop_all()
            
            # Create all tables with new schema
            print("📋 Creating database tables...")
            db.create_all()
            
            # Import all models to ensure they're registered
            from app.models import (
                User, Supplier, ItemCategory, SystemSettings, 
                RequestOrder, RequestOrderDetail, PurchaseOrder, PurchaseOrderItem,
                ShipmentConsolidation, LogisticsEvent, ConsolidationPO,
                RemarksHistory
            )
            
            print("✅ Database tables created successfully")
            
            # Create sample data
            print("📝 Creating sample data...")
            
            # Create admin user
            admin_user = User(
                chinese_name='系統管理員',
                username='admin',
                password=generate_password_hash('admin123'),
                department='IT',
                role='Admin'
            )
            db.session.add(admin_user)
            
            # Create procurement user
            proc_user = User(
                chinese_name='採購專員',
                username='procurement',
                password=generate_password_hash('proc123'),
                department='採購部',
                role='Procurement'
            )
            db.session.add(proc_user)
            
            # Create requisitioner user
            req_user = User(
                chinese_name='請購人員',
                username='requisitioner',
                password=generate_password_hash('req123'),
                department='業務部',
                role='Requisitioner'
            )
            db.session.add(req_user)
            
            # Create sample suppliers
            domestic_supplier = Supplier(
                supplier_id='S001',
                supplier_name='台灣本土供應商',
                supplier_region='domestic',
                contact_person='張經理',
                contact_phone='02-12345678',
                address='台北市信義區信義路一號'
            )
            db.session.add(domestic_supplier)
            
            international_supplier = Supplier(
                supplier_id='S002',
                supplier_name='海外國際供應商',
                supplier_region='international',
                contact_person='John Smith',
                contact_phone='+1-555-123-4567',
                address='123 International Blvd, USA'
            )
            db.session.add(international_supplier)
            
            # Create item categories
            categories = [
                ItemCategory(category_id='C001', category_name='辦公用品'),
                ItemCategory(category_id='C002', category_name='電腦設備'),
                ItemCategory(category_id='C003', category_name='文具用品')
            ]
            for category in categories:
                db.session.add(category)
            
            # Create system settings
            settings = SystemSettings(
                setting_key='company_name',
                setting_value='測試公司股份有限公司'
            )
            db.session.add(settings)
            
            db.session.commit()
            print("✅ Sample data created successfully")
            
            # Verify tables exist
            print("🔍 Verifying table creation...")
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            required_tables = [
                'users', 'suppliers', 'purchase_orders', 'purchase_order_items',
                'shipment_consolidations', 'consolidation_pos', 'remarks_history'
            ]
            
            missing_tables = [table for table in required_tables if table not in tables]
            
            if missing_tables:
                print(f"⚠️  Missing tables: {missing_tables}")
            else:
                print("✅ All required tables created")
            
            # Check purchase_orders columns specifically
            po_columns = [col['name'] for col in inspector.get_columns('purchase_orders')]
            delivery_columns = [
                'delivery_status', 'expected_delivery_date', 'actual_delivery_date',
                'consolidation_id', 'remarks', 'status_update_required'
            ]
            
            missing_po_columns = [col for col in delivery_columns if col not in po_columns]
            if missing_po_columns:
                print(f"⚠️  Missing purchase_orders columns: {missing_po_columns}")
            else:
                print("✅ All delivery management columns present in purchase_orders")
            
            # Check consolidations columns
            consolidation_columns = [col['name'] for col in inspector.get_columns('shipment_consolidations')]
            required_consolidation_columns = [
                'consolidation_name', 'logistics_status', 'remarks', 'created_by'
            ]
            
            missing_consolidation_columns = [col for col in required_consolidation_columns if col not in consolidation_columns]
            if missing_consolidation_columns:
                print(f"⚠️  Missing consolidation columns: {missing_consolidation_columns}")
            else:
                print("✅ All delivery management columns present in shipment_consolidations")
            
            print("\n🎉 Database initialization completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    success = initialize_database()
    if not success:
        sys.exit(1)