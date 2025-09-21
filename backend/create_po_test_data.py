#!/usr/bin/env python3
"""
Create test purchase order data to verify button logic fixes
"""

import sys
import os
from app import create_app, db
from app.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from datetime import datetime

def create_test_purchase_orders():
    """Create test purchase orders with different statuses"""
    app = create_app()
    
    with app.app_context():
        # Clear existing purchase orders
        PurchaseOrderItem.query.delete()
        PurchaseOrder.query.delete()
        db.session.commit()
        
        # Create test purchase orders with different statuses
        test_pos = [
            {
                'purchase_order_no': 'PO20250910001',
                'supplier_id': 'S001',
                'supplier_name': '測試供應商A',
                'purchase_status': 'pending',  # This should show edit button
                'subtotal_int': 100000,
                'tax_decimal1': 5000.0,
                'grand_total_int': 105000,
                'creator_id': 1,  # Required field
                'created_at': datetime.utcnow()
            },
            {
                'purchase_order_no': 'PO20250910002',
                'supplier_id': 'S002',
                'supplier_name': '測試供應商B',
                'purchase_status': 'order_created',  # This should show edit button
                'subtotal_int': 200000,
                'tax_decimal1': 10000.0,
                'grand_total_int': 210000,
                'creator_id': 1,  # Required field
                'created_at': datetime.utcnow()
            },
            {
                'purchase_order_no': 'PO20250910003',
                'supplier_id': 'S003',
                'supplier_name': '測試供應商C',
                'purchase_status': 'outputted',  # This should NOT show edit button
                'subtotal_int': 300000,
                'tax_decimal1': 15000.0,
                'grand_total_int': 315000,
                'creator_id': 1,  # Required field
                'created_at': datetime.utcnow()
            },
            {
                'purchase_order_no': 'PO20250910004',
                'supplier_id': 'S004',
                'supplier_name': '測試供應商D',
                'purchase_status': 'purchased',  # This should NOT show edit button
                'subtotal_int': 400000,
                'tax_decimal1': 20000.0,
                'grand_total_int': 420000,
                'creator_id': 1,  # Required field
                'created_at': datetime.utcnow()
            }
        ]
        
        for po_data in test_pos:
            po = PurchaseOrder(**po_data)
            db.session.add(po)
            
            # Add some items for each PO
            item = PurchaseOrderItem(
                purchase_order_no=po_data['purchase_order_no'],
                item_name=f"測試商品 - {po_data['purchase_order_no']}",
                item_quantity=1,
                item_unit='個',
                unit_price=po_data['subtotal_int'],
                line_subtotal_int=po_data['subtotal_int'],
                created_at=datetime.utcnow()
            )
            db.session.add(item)
        
        db.session.commit()
        print("Test purchase orders created successfully!")
        
        # Verify the data
        pos = PurchaseOrder.query.all()
        print(f"\nCreated {len(pos)} purchase orders:")
        for po in pos:
            print(f"- {po.purchase_order_no}: {po.supplier_name} ({po.purchase_status})")

if __name__ == '__main__':
    create_test_purchase_orders()