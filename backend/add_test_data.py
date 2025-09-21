#!/usr/bin/env python3

import os
import sys
from datetime import datetime, date
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import User, Supplier, RequestOrder, PurchaseOrder, RequestOrderItem, PurchaseOrderItem

def add_test_data():
    """Add test requisition and purchase order data"""
    app = create_app()
    
    with app.app_context():
        print("=== Adding Test Data ===")
        
        # Get admin user (should exist)
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("✗ Admin user not found!")
            return False
            
        print(f"✓ Found admin user: {admin_user.chinese_name}")
        
        # Get suppliers (should exist)
        suppliers = Supplier.query.all()
        print(f"✓ Found {len(suppliers)} suppliers")
        
        if len(suppliers) < 2:
            print("✗ Need at least 2 suppliers for test data")
            return False
        
        # Create test requisitions
        print("\n--- Creating Test Requisitions ---")
        
        # Requisition 1: Pending
        req1 = RequestOrder(
            request_order_no='REQ20250910001',
            requester_id=admin_user.user_id,
            requester_name=admin_user.chinese_name,
            usage_type='production',
            project_id='PRJ001',
            submit_date=datetime.now(),
            order_status='pending'
        )
        
        # Requisition 2: Approved 
        req2 = RequestOrder(
            request_order_no='REQ20250910002',
            requester_id=admin_user.user_id,
            requester_name=admin_user.chinese_name,
            usage_type='research',
            project_id='PRJ002',
            submit_date=datetime.now(),
            order_status='approved'
        )
        
        # Requisition 3: Completed
        req3 = RequestOrder(
            request_order_no='REQ20250910003',
            requester_id=admin_user.user_id,
            requester_name=admin_user.chinese_name,
            usage_type='maintenance',
            project_id='PRJ003',
            submit_date=datetime.now(),
            order_status='completed'
        )
        
        db.session.add_all([req1, req2, req3])
        db.session.flush()  # Flush to get IDs
        
        print(f"✓ Created requisition: {req1.request_order_no}")
        print(f"✓ Created requisition: {req2.request_order_no}")
        print(f"✓ Created requisition: {req3.request_order_no}")
        
        # Create test purchase orders
        print("\n--- Creating Test Purchase Orders ---")
        
        supplier1 = suppliers[0]  # TSMC
        supplier2 = suppliers[1]  # Intel
        
        # Purchase Order 1: From approved requisition
        po1 = PurchaseOrder(
            purchase_order_no='PO20250910001',
            supplier_id=supplier1.supplier_id,
            supplier_name=supplier1.supplier_name_zh,
            supplier_address=supplier1.supplier_address or 'N/A',
            contact_phone=supplier1.supplier_phone,
            contact_person=supplier1.supplier_contact_person or 'N/A',
            supplier_tax_id=supplier1.supplier_tax_id or 'N/A',
            order_date=date.today(),
            quotation_no='Q2025001',
            delivery_address='公司總部',
            creation_date=datetime.now(),
            creator_id=admin_user.user_id,
            output_person_id=admin_user.user_id,
            notes='測試採購單 - 生產用料',
            purchase_status='pending',
            shipping_status='not_shipped',
            subtotal_int=50000,  # $500.00 in cents
            tax_decimal1=5.0,     # 5% tax
            grand_total_int=52500, # $525.00 in cents
            billing_status='pending',
            payment_method='monthly'
        )
        
        # Purchase Order 2: Different supplier
        po2 = PurchaseOrder(
            purchase_order_no='PO20250910002',
            supplier_id=supplier2.supplier_id,
            supplier_name=supplier2.supplier_name_zh,
            supplier_address=supplier2.supplier_address or 'N/A',
            contact_phone=supplier2.supplier_phone,
            contact_person=supplier2.supplier_contact_person or 'N/A',
            supplier_tax_id=supplier2.supplier_tax_id or 'N/A',
            order_date=date.today(),
            quotation_no='Q2025002',
            delivery_address='研發中心',
            creation_date=datetime.now(),
            creator_id=admin_user.user_id,
            output_person_id=admin_user.user_id,
            notes='測試採購單 - 研發設備',
            purchase_status='confirmed',
            shipping_status='shipped',
            subtotal_int=120000,  # $1200.00 in cents
            tax_decimal1=5.0,      # 5% tax
            grand_total_int=126000, # $1260.00 in cents
            billing_status='paid',
            payment_method='net60',
            shipped_at=datetime.now(),
            carrier='順豐快遞',
            tracking_no='SF123456789'
        )
        
        db.session.add_all([po1, po2])
        db.session.flush()  # Flush to get IDs
        
        print(f"✓ Created purchase order: {po1.purchase_order_no}")
        print(f"✓ Created purchase order: {po2.purchase_order_no}")
        
        # Commit all changes
        try:
            db.session.commit()
            print("\n✓ All test data committed successfully!")
            
            # Verify the data
            print("\n--- Verification ---")
            req_count = RequestOrder.query.count()
            po_count = PurchaseOrder.query.count()
            print(f"✓ Total requisitions: {req_count}")
            print(f"✓ Total purchase orders: {po_count}")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error committing data: {e}")
            return False

if __name__ == "__main__":
    success = add_test_data()
    if success:
        print("\n🎉 Test data added successfully!")
    else:
        print("\n❌ Failed to add test data!")
        sys.exit(1)