#!/usr/bin/env python3
"""
PM Emergency Diagnosis: Find out why approval fails
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.request_order import RequestOrder, RequestOrderItem
from app.models.supplier import Supplier

def diagnose_approval():
    app = create_app()
    
    with app.app_context():
        print("🔍 PM EMERGENCY DIAGNOSIS: APPROVAL FAILURE")
        print("=" * 50)
        
        # Find the most recent submitted requisition
        recent_req = RequestOrder.query.filter_by(order_status='submitted').order_by(RequestOrder.created_at.desc()).first()
        
        if not recent_req:
            print("❌ No submitted requisitions found")
            return
            
        print(f"📋 Found requisition: {recent_req.request_order_no}")
        print(f"📋 Status: {recent_req.order_status}")
        
        # Get first item to test approval
        item = RequestOrderItem.query.filter_by(request_order_no=recent_req.request_order_no).first()
        
        if not item:
            print("❌ No items found in requisition")
            return
            
        print(f"📦 Item: {item.detail_id} - {item.item_name}")
        print(f"📦 Current status: {item.item_status}")
        
        # Check if supplier exists
        supplier = Supplier.query.filter_by(supplier_id='T001').first()
        print(f"🏭 Supplier T001 exists: {supplier is not None}")
        if supplier:
            print(f"🏭 Supplier name: {supplier.supplier_name_zh}")
        
        # Check current item validation
        print(f"\n🧪 VALIDATION CHECKS:")
        print(f"- Item status is 'submitted': {item.item_status == 'submitted'}")
        print(f"- Item has no supplier: {item.supplier_id is None}")
        print(f"- Item has no unit price: {item.unit_price is None}")
        
        # Try to manually approve
        print(f"\n🎯 ATTEMPTING MANUAL APPROVAL:")
        try:
            # Set supplier and price
            item.supplier_id = 'T001'
            item.unit_price = 75.00
            item.item_status = 'reviewed'
            
            print(f"✅ Set supplier: {item.supplier_id}")
            print(f"✅ Set price: {item.unit_price}")
            print(f"✅ Set status: {item.item_status}")
            
            # Save the item
            db.session.add(item)
            db.session.flush()
            print(f"✅ Item changes flushed")
            
            # Check if all items are reviewed
            summary = recent_req.get_summary()
            print(f"📊 Summary after item approval: {summary}")
            
            all_reviewed = (
                summary['total_items'] > 0 and
                summary['pending_items'] == 0 and
                recent_req.order_status == 'submitted'
            )
            
            print(f"🔍 Should update status: {all_reviewed}")
            
            if all_reviewed:
                print(f"🎯 CALLING update_status_after_review()...")
                recent_req.update_status_after_review()
                print(f"📋 Status after update: {recent_req.order_status}")
                
            # Commit changes
            db.session.commit()
            print(f"✅ All changes committed")
            
            # Final verification
            final_req = RequestOrder.query.filter_by(request_order_no=recent_req.request_order_no).first()
            final_item = RequestOrderItem.query.filter_by(detail_id=item.detail_id).first()
            
            print(f"\n🎉 FINAL RESULTS:")
            print(f"📋 Requisition status: {final_req.order_status}")
            print(f"📦 Item status: {final_item.item_status}")
            print(f"🏭 Item supplier: {final_item.supplier_id}")
            print(f"💰 Item price: {final_item.unit_price}")
            
            if final_req.order_status == 'reviewed':
                print(f"🎉 SUCCESS: Status correctly updated to 'reviewed'!")
            else:
                print(f"❌ FAILED: Status still '{final_req.order_status}'")
                
        except Exception as e:
            print(f"❌ ERROR during manual approval: {e}")
            db.session.rollback()

if __name__ == "__main__":
    diagnose_approval()