#!/usr/bin/env python3
"""
Direct Status Fix
Directly trigger the enhanced status update logic from within the Flask app context
"""

import sys
import os

# Add backend directory to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

from app import create_app, db
from app.models.request_order import RequestOrder

def fix_requisition_status_directly(req_no):
    """Fix requisition status directly using the app context"""
    print(f"🔧 DIRECT STATUS FIX for {req_no}")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Find the requisition
            order = RequestOrder.query.filter_by(request_order_no=req_no).first()
            
            if not order:
                print(f"❌ Requisition {req_no} not found")
                return False
            
            print(f"✅ Found requisition: {req_no}")
            print(f"Current status: {order.order_status}")
            
            # Get summary
            summary = order.get_summary()
            print(f"Summary: {summary}")
            
            # Check if it needs fixing
            if (order.order_status == 'submitted' and 
                summary['pending_items'] == 0 and 
                summary['total_items'] > 0):
                
                print(f"🚨 Status mismatch confirmed - applying fix")
                
                # Call our enhanced status update method
                print(f"Calling update_status_after_review()...")
                order.update_status_after_review()
                
                print(f"Status after fix: {order.order_status}")
                
                if order.order_status == 'reviewed':
                    print(f"🎉 SUCCESS! Status updated to 'reviewed'")
                    return True
                else:
                    print(f"❌ Status still incorrect: {order.order_status}")
                    return False
            
            else:
                print(f"ℹ️  No fix needed - status is already correct or conditions not met")
                print(f"   Current status: {order.order_status}")
                print(f"   Pending items: {summary['pending_items']}")
                print(f"   Total items: {summary['total_items']}")
                return True
                
        except Exception as e:
            print(f"❌ Error during fix: {e}")
            return False

def scan_and_fix_all_problems():
    """Scan and fix all status problems"""
    print(f"🔍 SCANNING AND FIXING ALL STATUS PROBLEMS")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Find all submitted requisitions
            submitted_orders = RequestOrder.query.filter_by(order_status='submitted').all()
            
            print(f"Found {len(submitted_orders)} submitted requisitions")
            
            problems_found = 0
            problems_fixed = 0
            
            for order in submitted_orders:
                summary = order.get_summary()
                
                # Check if it's a problem case
                if summary['pending_items'] == 0 and summary['total_items'] > 0:
                    problems_found += 1
                    print(f"\n🚨 Problem: {order.request_order_no} ({order.requester_name})")
                    print(f"   Summary: {summary}")
                    
                    # Apply fix
                    print(f"   Applying fix...")
                    order.update_status_after_review()
                    
                    if order.order_status == 'reviewed':
                        problems_fixed += 1
                        print(f"   ✅ Fixed!")
                    else:
                        print(f"   ❌ Fix failed - status: {order.order_status}")
            
            print(f"\n📊 SCAN RESULTS:")
            print(f"Problems found: {problems_found}")
            print(f"Problems fixed: {problems_fixed}")
            print(f"Still broken: {problems_found - problems_fixed}")
            
            return problems_found, problems_fixed
            
        except Exception as e:
            print(f"❌ Error during scan: {e}")
            return 0, 0

def main():
    print("🚨 DIRECT STATUS FIX EXECUTION")
    print("="*50)
    
    # Fix specific REQ20250909002
    print("\nSTEP 1: Fix REQ20250909002 specifically")
    success = fix_requisition_status_directly("REQ20250909002")
    
    # Scan and fix all problems
    print("\nSTEP 2: Scan and fix all similar problems")
    found, fixed = scan_and_fix_all_problems()
    
    # Summary
    print("\n" + "="*50)
    print("📊 FINAL SUMMARY")
    print(f"REQ20250909002 fix: {'✅ SUCCESS' if success else '❌ FAILED'}")
    print(f"Total problems found: {found}")
    print(f"Total problems fixed: {fixed}")
    
    if success and fixed == found:
        print("🎉 ALL PROBLEMS RESOLVED!")
    elif fixed > 0:
        print("⚠️  PARTIAL SUCCESS - some issues remain")
    else:
        print("❌ NO FIXES APPLIED - investigation needed")

if __name__ == "__main__":
    main()