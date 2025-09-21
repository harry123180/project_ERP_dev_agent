#!/usr/bin/env python3
"""
Comprehensive Requisition Status Fix Script
Identifies and fixes all requisitions with status update issues
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.request_order import RequestOrder, RequestOrderItem
from datetime import datetime
import json

def find_stuck_requisitions():
    """Find all requisitions stuck in 'submitted' status that should be 'reviewed'"""
    print("=== FINDING STUCK REQUISITIONS ===")
    
    stuck_requisitions = []
    
    # Get all submitted requisitions
    submitted_reqs = RequestOrder.query.filter_by(order_status='submitted').all()
    print(f"Found {len(submitted_reqs)} requisitions in 'submitted' status")
    
    for req in submitted_reqs:
        summary = req.get_summary()
        if summary['pending_items'] == 0 and summary['total_items'] > 0:
            stuck_requisitions.append({
                'request_order_no': req.request_order_no,
                'requester_name': req.requester_name,
                'submit_date': req.submit_date,
                'summary': summary
            })
            print(f"STUCK: {req.request_order_no} - {req.requester_name} - Total: {summary['total_items']}, Pending: {summary['pending_items']}")
    
    print(f"Found {len(stuck_requisitions)} stuck requisitions")
    return stuck_requisitions

def fix_stuck_requisitions():
    """Fix all stuck requisitions"""
    print("\n=== FIXING STUCK REQUISITIONS ===")
    
    fixed_count = 0
    failed_fixes = []
    
    # Get all submitted requisitions
    submitted_reqs = RequestOrder.query.filter_by(order_status='submitted').all()
    
    for req in submitted_reqs:
        summary = req.get_summary()
        if summary['pending_items'] == 0 and summary['total_items'] > 0:
            print(f"Fixing {req.request_order_no}...")
            try:
                old_status = req.order_status
                req.update_status_after_review()
                new_status = req.order_status
                
                if old_status != new_status:
                    db.session.commit()
                    print(f"  SUCCESS: {req.request_order_no} updated from '{old_status}' to '{new_status}'")
                    fixed_count += 1
                else:
                    print(f"  NO CHANGE: {req.request_order_no} remains '{old_status}'")
            except Exception as e:
                db.session.rollback()
                error_msg = f"Failed to fix {req.request_order_no}: {str(e)}"
                print(f"  ERROR: {error_msg}")
                failed_fixes.append(error_msg)
    
    print(f"\nFixed {fixed_count} requisitions")
    if failed_fixes:
        print(f"Failed to fix {len(failed_fixes)} requisitions:")
        for error in failed_fixes:
            print(f"  - {error}")
    
    return fixed_count, failed_fixes

def add_logging_to_status_updates():
    """Add better logging to understand when status updates fail"""
    print("\n=== ADDING ENHANCED LOGGING ===")
    
    # This would be a code enhancement to add to the models
    enhancement_code = '''
def update_status_after_review(self):
    """Update order status based on item review status - ENHANCED WITH LOGGING"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"[STATUS UPDATE] Checking {self.request_order_no}, current status: {self.order_status}")
    
    if self.order_status != 'submitted':
        logger.info(f"[STATUS UPDATE] Skipping {self.request_order_no} - not in submitted status")
        return  # Only update if currently submitted
        
    summary = self.get_summary()
    total_items = summary['total_items']
    pending_items = summary['pending_items']
    
    logger.info(f"[STATUS UPDATE] {self.request_order_no} - Total items: {total_items}, Pending: {pending_items}")
    
    # If all items have been reviewed (no pending items), update to reviewed
    if total_items > 0 and pending_items == 0:
        logger.info(f"[STATUS UPDATE] Updating {self.request_order_no} to reviewed status")
        self.order_status = 'reviewed'
        logger.info(f"[STATUS UPDATE] Successfully updated {self.request_order_no} to reviewed")
    else:
        logger.info(f"[STATUS UPDATE] Not updating {self.request_order_no} - conditions not met")
    '''
    
    print("Enhanced logging code to add to RequestOrder model:")
    print(enhancement_code)
    
    return enhancement_code

def generate_fix_report():
    """Generate a comprehensive report of the fix"""
    report = {
        'timestamp': datetime.now().isoformat(),
        'investigation_summary': {
            'primary_issue': 'REQ20250909001 stuck in submitted status despite all items approved',
            'root_cause': 'Status update method works correctly, but may not be called in all scenarios',
            'solution': 'Applied manual status update and identified other affected requisitions'
        }
    }
    
    # Find stuck requisitions for report
    stuck_reqs = find_stuck_requisitions()
    
    # Fix stuck requisitions
    fixed_count, failed_fixes = fix_stuck_requisitions()
    
    report['results'] = {
        'stuck_requisitions_found': len(stuck_reqs),
        'requisitions_fixed': fixed_count,
        'failed_fixes': failed_fixes,
        'stuck_requisitions_details': stuck_reqs
    }
    
    return report

def main():
    app = create_app()
    with app.app_context():
        print("COMPREHENSIVE REQUISITION STATUS FIX SCRIPT")
        print("=" * 50)
        print(f"Execution time: {datetime.now()}")
        print()
        
        # Generate comprehensive report
        report = generate_fix_report()
        
        # Save report
        report_filename = f"requisition_status_fix_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n=== SUMMARY ===")
        print(f"Stuck requisitions found: {report['results']['stuck_requisitions_found']}")
        print(f"Requisitions fixed: {report['results']['requisitions_fixed']}")
        print(f"Failed fixes: {len(report['results']['failed_fixes'])}")
        print(f"Report saved to: {report_filename}")
        
        if report['results']['failed_fixes']:
            print("\nFailed fixes:")
            for error in report['results']['failed_fixes']:
                print(f"  - {error}")

if __name__ == '__main__':
    main()