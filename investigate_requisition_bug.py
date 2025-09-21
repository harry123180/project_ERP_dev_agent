#!/usr/bin/env python3
"""
Critical Bug Investigation Script for REQ20250909001
Diagnoses status update issues for specific requisition
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.request_order import RequestOrder, RequestOrderItem
from datetime import datetime
import json

def investigate_requisition(req_no='REQ20250909001'):
    """Investigate specific requisition status issues"""
    print(f"=== INVESTIGATING REQUISITION {req_no} ===")
    print(f"Investigation time: {datetime.now()}")
    print()
    
    # Get the requisition
    requisition = RequestOrder.query.filter_by(request_order_no=req_no).first()
    
    if not requisition:
        print(f"ERROR: Requisition {req_no} not found!")
        return False
    
    print(f"Found requisition: {req_no}")
    print(f"Current Status: {requisition.order_status}")
    print(f"Requester: {requisition.requester_name}")
    print(f"Submit Date: {requisition.submit_date}")
    print()
    
    # Get all items for this requisition
    items = RequestOrderItem.query.filter_by(request_order_no=req_no).all()
    print(f"Number of items: {len(items)}")
    
    # Analyze item statuses
    status_counts = {}
    for item in items:
        status = item.item_status
        status_counts[status] = status_counts.get(status, 0) + 1
        print(f"Item {item.detail_id}: {item.item_name} - Status: {status}")
    
    print(f"\nItem Status Summary:")
    for status, count in status_counts.items():
        print(f"  {status}: {count} items")
    
    # Get summary using the method
    summary = requisition.get_summary()
    print(f"\nSummary from get_summary() method:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Check status update logic
    print(f"\n=== STATUS UPDATE LOGIC CHECK ===")
    print(f"Current order status: {requisition.order_status}")
    print(f"Should update if: order_status == 'submitted' AND pending_items == 0")
    print(f"Condition check: {requisition.order_status} == 'submitted' -> {requisition.order_status == 'submitted'}")
    print(f"Pending items: {summary['pending_items']}")
    print(f"Should update to 'reviewed': {requisition.order_status == 'submitted' and summary['pending_items'] == 0}")
    
    # Test the update method
    print(f"\n=== TESTING UPDATE METHOD ===")
    print(f"Before update: {requisition.order_status}")
    requisition.update_status_after_review()
    print(f"After update method: {requisition.order_status}")
    
    # Check if we need to commit
    if requisition.order_status == 'reviewed':
        try:
            db.session.commit()
            print("SUCCESS: Status updated to 'reviewed' and committed!")
            return True
        except Exception as e:
            print(f"ERROR committing changes: {e}")
            db.session.rollback()
            return False
    else:
        print("WARNING: Status was not updated by the method")
        return False

def main():
    app = create_app()
    with app.app_context():
        success = investigate_requisition('REQ20250909001')
        
        if success:
            print(f"\n=== VERIFICATION ===")
            # Verify the fix
            req = RequestOrder.query.filter_by(request_order_no='REQ20250909001').first()
            if req:
                print(f"Final status: {req.order_status}")
                print("BUG FIX SUCCESSFUL!" if req.order_status == 'reviewed' else "BUG FIX FAILED!")
            else:
                print("ERROR: Could not verify fix - requisition not found")

if __name__ == '__main__':
    main()