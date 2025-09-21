#!/usr/bin/env python3
"""
Requisition Status Consistency Monitor & Auto-Fix
This script provides defensive mechanisms to prevent and fix status update bugs
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import create_app, db
from app.models.request_order import RequestOrder, RequestOrderItem
from sqlalchemy import text
from datetime import datetime, timedelta
# import schedule
# import time

# Create app context
app = create_app('development')

class StatusConsistencyMonitor:
    def __init__(self):
        self.app = app
        self.fixes_applied = 0
        self.problems_detected = 0
    
    def scan_and_fix_inconsistent_statuses(self):
        """Scan for and fix inconsistent requisition statuses"""
        with self.app.app_context():
            print(f"[MONITOR] Starting status consistency scan at {datetime.now().isoformat()}")
            
            try:
                # Find all submitted requisitions
                submitted_orders = RequestOrder.query.filter_by(order_status='submitted').all()
                problems_found = []
                
                for order in submitted_orders:
                    summary = order.get_summary()
                    
                    # Check if all items are reviewed but status is still submitted
                    if (summary['total_items'] > 0 and 
                        summary['pending_items'] == 0):
                        
                        problems_found.append({
                            'order': order,
                            'summary': summary,
                            'issue': 'All items reviewed but status still submitted'
                        })
                
                print(f"[MONITOR] Found {len(problems_found)} status inconsistencies")
                self.problems_detected += len(problems_found)
                
                # Fix each problem
                for problem in problems_found:
                    order = problem['order']
                    old_status = order.order_status
                    
                    print(f"[FIX] Fixing {order.request_order_no}: {old_status} -> reviewed")
                    
                    # Apply the fix
                    order.update_status_after_review()
                    
                    if order.order_status == 'reviewed':
                        print(f"[FIX] ✅ Successfully fixed {order.request_order_no}")
                        self.fixes_applied += 1
                    else:
                        print(f"[FIX] ❌ Failed to fix {order.request_order_no}")
                
                # Log summary
                if problems_found:
                    print(f"[MONITOR] Applied {len(problems_found)} fixes")
                else:
                    print(f"[MONITOR] No status inconsistencies found")
                
            except Exception as e:
                print(f"[MONITOR] Error during scan: {e}")
    
    def validate_api_endpoints_call_status_update(self):
        """Validate that API endpoints properly call status update methods"""
        with self.app.app_context():
            print(f"[VALIDATION] Checking API endpoint status update calls...")
            
            # This would check the actual API routes to ensure they call update_status_after_review
            # For now, we'll add enhanced logging to detect when updates are missed
            
            # Find recently updated items that might have missed status updates
            recent_threshold = datetime.utcnow() - timedelta(hours=1)
            
            recent_approvals = RequestOrderItem.query.filter(
                RequestOrderItem.item_status == 'approved',
                RequestOrderItem.updated_at >= recent_threshold
            ).all()
            
            suspicious_orders = set()
            for item in recent_approvals:
                order = item.request_order
                if order.order_status == 'submitted':
                    summary = order.get_summary()
                    if summary['pending_items'] == 0:
                        suspicious_orders.add(order.request_order_no)
            
            if suspicious_orders:
                print(f"[VALIDATION] ⚠️  Found {len(suspicious_orders)} orders with recent approvals but wrong status:")
                for order_no in suspicious_orders:
                    print(f"[VALIDATION]    {order_no}")
            else:
                print(f"[VALIDATION] ✅ No suspicious recent status updates found")
    
    def generate_status_consistency_report(self):
        """Generate a comprehensive status consistency report"""
        with self.app.app_context():
            print(f"\n=== STATUS CONSISTENCY REPORT ===")
            print(f"Generated at: {datetime.now().isoformat()}")
            
            # Overall statistics
            total_orders = RequestOrder.query.count()
            submitted_orders = RequestOrder.query.filter_by(order_status='submitted').count()
            reviewed_orders = RequestOrder.query.filter_by(order_status='reviewed').count()
            draft_orders = RequestOrder.query.filter_by(order_status='draft').count()
            
            print(f"\nOverall Statistics:")
            print(f"  Total Orders: {total_orders}")
            print(f"  Draft Orders: {draft_orders}")
            print(f"  Submitted Orders: {submitted_orders}")
            print(f"  Reviewed Orders: {reviewed_orders}")
            
            # Check for problems
            submitted_list = RequestOrder.query.filter_by(order_status='submitted').all()
            problems = []
            
            for order in submitted_list:
                summary = order.get_summary()
                if summary['total_items'] > 0 and summary['pending_items'] == 0:
                    problems.append(order.request_order_no)
            
            print(f"\nStatus Consistency Issues:")
            print(f"  Problems Detected: {len(problems)}")
            print(f"  Problems Fixed (this session): {self.fixes_applied}")
            print(f"  Total Problems Found (this session): {self.problems_detected}")
            
            if problems:
                print(f"  Current Problems: {', '.join(problems)}")
            else:
                print(f"  ✅ No current status consistency issues")
    
    def run_maintenance_cycle(self):
        """Run a complete maintenance cycle"""
        print(f"\n{'='*50}")
        print(f"REQUISITION STATUS MAINTENANCE CYCLE")
        print(f"{'='*50}")
        
        self.scan_and_fix_inconsistent_statuses()
        self.validate_api_endpoints_call_status_update()
        self.generate_status_consistency_report()
        
        print(f"\nMaintenance cycle completed at {datetime.now().isoformat()}")

def create_scheduled_monitor():
    """Create a scheduled monitor that runs periodically"""
    print("Scheduled monitoring disabled - install 'schedule' package to enable")
    print("Run immediate fix instead...")
    run_immediate_fix()

def run_immediate_fix():
    """Run an immediate fix cycle"""
    monitor = StatusConsistencyMonitor()
    monitor.run_maintenance_cycle()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--scheduled":
        create_scheduled_monitor()
    else:
        run_immediate_fix()