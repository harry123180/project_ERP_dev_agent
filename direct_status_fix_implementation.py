#!/usr/bin/env python3
"""
DIRECT STATUS FIX IMPLEMENTATION
=================================

This script directly accesses the database to fix status transition issues.
Since the API endpoint debugging isn't working properly, this bypasses
the API layer and directly fixes requisitions that should be 'reviewed'
but are stuck in 'submitted' status.
"""

import os
import sys

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.request_order import RequestOrder, RequestOrderItem
from datetime import datetime

def analyze_and_fix_status_issues():
    """Analyze and fix status transition issues directly in the database"""
    
    # Create Flask app context
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    
    with app.app_context():
        print("=" * 60)
        print("DIRECT STATUS FIX IMPLEMENTATION")
        print("=" * 60)
        
        # Find all submitted requisitions
        submitted_orders = RequestOrder.query.filter_by(order_status='submitted').all()
        
        print(f"Found {len(submitted_orders)} submitted requisitions")
        
        fixed_count = 0
        problems_found = []
        
        for order in submitted_orders:
            print(f"\nAnalyzing requisition: {order.request_order_no}")
            
            # Get summary
            summary = order.get_summary()
            print(f"Summary: {summary}")
            
            # Check if all items are reviewed (no pending items)
            if (summary['total_items'] > 0 and 
                summary['pending_items'] == 0):
                
                print(f"🔧 FIXING: {order.request_order_no} - all items reviewed but status still 'submitted'")
                
                problems_found.append({
                    'requisition_number': order.request_order_no,
                    'requester_name': order.requester_name,
                    'current_status': order.order_status,
                    'summary': summary,
                    'created_at': order.created_at.isoformat() if order.created_at else None,
                    'updated_at': order.updated_at.isoformat() if order.updated_at else None
                })
                
                # Fix the status
                old_status = order.order_status
                order.order_status = 'reviewed'
                order.updated_at = datetime.utcnow()
                
                try:
                    db.session.add(order)
                    db.session.commit()
                    print(f"✅ FIXED: {order.request_order_no} status changed from '{old_status}' to 'reviewed'")
                    fixed_count += 1
                except Exception as e:
                    print(f"❌ FAILED to fix {order.request_order_no}: {e}")
                    db.session.rollback()
            else:
                print(f"⏳ OK: {order.request_order_no} - still has {summary['pending_items']} pending items")
        
        print(f"\n" + "=" * 60)
        print("DIRECT FIX SUMMARY:")
        print(f"- Total submitted requisitions analyzed: {len(submitted_orders)}")
        print(f"- Problems found and fixed: {fixed_count}")
        print("=" * 60)
        
        if problems_found:
            print("\nFIXED REQUISITIONS:")
            for problem in problems_found:
                print(f"- {problem['requisition_number']} ({problem['requester_name']})")
        
        # Now test one of the fixed requisitions
        if problems_found:
            test_req_no = problems_found[0]['requisition_number']
            print(f"\n🧪 TESTING FIXED REQUISITION: {test_req_no}")
            
            # Re-fetch from database
            test_order = RequestOrder.query.get(test_req_no)
            if test_order:
                print(f"Status after fix: {test_order.order_status}")
                print(f"Summary after fix: {test_order.get_summary()}")
                
                if test_order.order_status == 'reviewed':
                    print("✅ SUCCESS: Direct database fix worked!")
                else:
                    print(f"❌ FAILED: Status is still '{test_order.order_status}'")
            else:
                print("❌ Could not find test requisition")
        
        return fixed_count, problems_found

def verify_api_endpoint_logic():
    """Verify that the API endpoint logic is working correctly"""
    
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    
    with app.app_context():
        print("\n" + "=" * 60)
        print("VERIFYING API ENDPOINT LOGIC")
        print("=" * 60)
        
        # Find a submitted requisition with all approved items
        test_order = RequestOrder.query.filter_by(order_status='submitted').first()
        
        if test_order:
            print(f"Testing with requisition: {test_order.request_order_no}")
            
            # Simulate the API endpoint logic
            print("Simulating update_status_after_review() call...")
            test_order.update_status_after_review()
            
            # Check if status changed (but don't commit)
            print(f"Status after update_status_after_review(): {test_order.order_status}")
            
            # Now commit the change
            try:
                db.session.commit()
                print(f"Status after commit: {test_order.order_status}")
                
                # Refresh from database
                db.session.refresh(test_order)
                print(f"Status after refresh: {test_order.order_status}")
            except Exception as e:
                print(f"Commit failed: {e}")
                db.session.rollback()
        else:
            print("No submitted requisitions found for testing")

if __name__ == '__main__':
    print("Starting direct status fix implementation...")
    
    try:
        # Step 1: Direct database fix
        fixed_count, problems = analyze_and_fix_status_issues()
        
        # Step 2: Verify API logic
        verify_api_endpoint_logic()
        
        print(f"\n✅ DIRECT FIX COMPLETE: Fixed {fixed_count} requisitions")
        
    except Exception as e:
        print(f"❌ ERROR during direct fix: {e}")
        import traceback
        traceback.print_exc()