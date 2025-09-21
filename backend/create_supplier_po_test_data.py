#!/usr/bin/env python
"""
Create test purchase orders for suppliers
"""

from app import create_app, db
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from app.models.supplier import Supplier
from datetime import datetime, timedelta
import random

def create_test_purchase_orders():
    """Create test purchase orders for suppliers"""
    app = create_app()
    
    with app.app_context():
        try:
            # Get all suppliers
            suppliers = Supplier.query.all()
            if not suppliers:
                print("No suppliers found. Please run create_supplier_test_data.py first.")
                return
            
            # Sample PO statuses for variety
            statuses = ['order_created', 'outputted', 'confirmed', 'shipped', 'arrived', 'completed']
            
            created_count = 0
            
            for supplier in suppliers:
                # Create 3-5 purchase orders per supplier
                num_orders = random.randint(3, 5)
                
                for i in range(num_orders):
                    po_no = f"PO{datetime.now().strftime('%Y%m%d')}{supplier.supplier_id}{i+1:03d}"
                    
                    # Check if PO already exists
                    existing = PurchaseOrder.query.filter_by(purchase_order_no=po_no).first()
                    if existing:
                        continue
                    
                    # Create purchase order
                    order_date = datetime.now() - timedelta(days=random.randint(1, 60))
                    expected_delivery = order_date + timedelta(days=random.randint(7, 30))
                    
                    po = PurchaseOrder(
                        purchase_order_no=po_no,
                        supplier_id=supplier.supplier_id,
                        supplier_name=supplier.supplier_name_zh,
                        supplier_address=supplier.supplier_address,
                        contact_phone=supplier.supplier_phone,
                        contact_person=supplier.supplier_contact_person,
                        supplier_tax_id=supplier.supplier_tax_id,
                        order_date=order_date.date(),
                        expected_delivery_date=expected_delivery.date(),
                        purchase_status=random.choice(statuses),
                        subtotal_int=random.randint(10000, 500000),
                        tax_decimal1=0.05,
                        grand_total_int=random.randint(10500, 525000),
                        payment_method=supplier.payment_terms or 'net_30',
                        creator_id='admin',
                        created_at=order_date,
                        updated_at=datetime.now()
                    )
                    
                    # Set delivery status based on purchase status
                    if po.purchase_status in ['completed', 'arrived']:
                        po.delivery_status = 'delivered'
                    elif po.purchase_status == 'shipped':
                        po.delivery_status = 'in_transit'
                    else:
                        po.delivery_status = 'pending'
                    
                    db.session.add(po)
                    
                    # Create 2-5 items per PO
                    num_items = random.randint(2, 5)
                    for j in range(num_items):
                        item = PurchaseOrderItem(
                            purchase_order_no=po_no,
                            item_name=f"測試物料{j+1}",
                            item_quantity=random.randint(1, 100),
                            item_unit='個',
                            unit_price=random.randint(100, 10000),
                            item_specification=f"規格{j+1}",
                            item_model=f"MODEL{random.randint(1000, 9999)}",
                            line_status='order_created'
                        )
                        db.session.add(item)
                    
                    created_count += 1
                    print(f"Created PO: {po_no} for {supplier.supplier_name_zh}")
            
            db.session.commit()
            
            print(f"\n✅ Purchase order test data created successfully!")
            print(f"   Created: {created_count} purchase orders")
            
            # Display summary
            total_pos = PurchaseOrder.query.count()
            print(f"\n📊 Purchase Order Summary:")
            print(f"   Total purchase orders: {total_pos}")
            
            for status in statuses:
                count = PurchaseOrder.query.filter_by(purchase_status=status).count()
                print(f"   {status}: {count}")
            
        except Exception as e:
            print(f"Error creating purchase order test data: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == '__main__':
    create_test_purchase_orders()