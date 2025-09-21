#!/usr/bin/env python3
"""
Direct Database Diagnostic for Requisition Status Bug
Bypasses API layer to check database directly
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.request_order import RequestOrder, RequestOrderItem
from app.models.user import User
from sqlalchemy import text
from datetime import datetime

# Create app context
app = create_app('development')

def diagnose_database():
    """Direct database diagnosis"""
    print("=== DATABASE DIAGNOSTIC ===")
    print(f"Starting at {datetime.now().isoformat()}")
    
    with app.app_context():
        print("\n1. DATABASE CONNECTION TEST")
        print("=" * 40)
        try:
            # Test basic connection
            result = db.session.execute(text("SELECT 1")).scalar()
            print(f"✅ Database connection: OK (result: {result})")
        except Exception as e:
            print(f"❌ Database connection: FAILED - {e}")
            return
        
        print("\n2. REQUISITION TABLE STRUCTURE")
        print("=" * 40)
        try:
            # Check table exists and structure
            result = db.session.execute(text("PRAGMA table_info(request_orders)")).fetchall()
            print("Request Orders table columns:")
            for row in result:
                print(f"  {row[1]}: {row[2]} ({'NOT NULL' if row[3] else 'NULLABLE'})")
        except Exception as e:
            print(f"❌ Table structure check failed: {e}")
        
        print("\n3. SEARCH FOR REQ20250909004")
        print("=" * 40)
        try:
            # Direct SQL search for the problematic requisition
            result = db.session.execute(
                text("SELECT * FROM request_orders WHERE request_order_no LIKE '%20250909004%'")
            ).fetchall()
            
            if result:
                print(f"✅ Found {len(result)} matching records:")
                for row in result:
                    print(f"  {row}")
            else:
                print("❌ No records found matching REQ20250909004")
                
            # Search more broadly
            result = db.session.execute(
                text("SELECT * FROM request_orders WHERE request_order_no LIKE '%20250909%'")
            ).fetchall()
            
            print(f"\nBroader search (all 20250909):")
            print(f"Found {len(result)} records")
            for row in result:
                print(f"  {dict(row._mapping)}")
                
        except Exception as e:
            print(f"❌ Search failed: {e}")
        
        print("\n4. ALL REQUISITIONS STATUS ANALYSIS")
        print("=" * 40)
        try:
            # Get all requisitions using ORM
            orders = RequestOrder.query.all()
            print(f"Total requisitions in system: {len(orders)}")
            
            status_counts = {}
            problem_orders = []
            
            for order in orders:
                status = order.order_status
                status_counts[status] = status_counts.get(status, 0) + 1
                
                # Check for status problems
                summary = order.get_summary()
                if (status == 'submitted' and 
                    summary['total_items'] > 0 and 
                    summary['pending_items'] == 0):
                    problem_orders.append({
                        'order_no': order.request_order_no,
                        'status': status,
                        'summary': summary,
                        'requester': order.requester_name
                    })
            
            print("Status distribution:")
            for status, count in status_counts.items():
                print(f"  {status}: {count}")
            
            print(f"\nProblematic orders (submitted but all items reviewed): {len(problem_orders)}")
            for problem in problem_orders:
                print(f"  {problem['order_no']}: {problem['status']} - {problem['summary']}")
                
        except Exception as e:
            print(f"❌ Status analysis failed: {e}")
        
        print("\n5. CREATE TEST REQUISITION")
        print("=" * 40)
        try:
            # Create test requisition to verify workflow
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                print("❌ Admin user not found")
                return
            
            # Generate unique test number
            today_str = datetime.now().strftime('%Y%m%d')
            test_prefix = f"TESTDBG{today_str}"
            existing = RequestOrder.query.filter(
                RequestOrder.request_order_no.like(f"{test_prefix}%")
            ).count()
            test_req_no = f"{test_prefix}{existing + 1:03d}"
            
            # Create test order
            test_order = RequestOrder(
                request_order_no=test_req_no,
                requester_id=admin_user.user_id,
                requester_name=admin_user.chinese_name,
                usage_type='daily'
            )
            
            db.session.add(test_order)
            db.session.flush()
            
            # Add test item
            test_item = RequestOrderItem(
                request_order_no=test_req_no,
                item_name='Database Test Item',
                item_quantity=1,
                item_unit='pcs',
                item_specification='Testing status update',
                item_description='Database diagnostic test'
            )
            
            db.session.add(test_item)
            db.session.commit()
            
            print(f"✅ Created test requisition: {test_req_no}")
            
            # Submit it
            test_order.submit()
            db.session.commit()
            print(f"✅ Submitted test requisition for review")
            
            # Approve the item
            test_item.approve('T001', 100.0, 'DB test approval')
            print(f"✅ Approved test item")
            
            # Test status update
            old_status = test_order.order_status
            test_order.update_status_after_review()
            new_status = test_order.order_status
            
            print(f"Status update test: {old_status} → {new_status}")
            
            if new_status == 'reviewed':
                print("✅ Status update working correctly!")
            else:
                print("❌ Status update bug reproduced!")
                
        except Exception as e:
            print(f"❌ Test creation failed: {e}")
            db.session.rollback()

def main():
    diagnose_database()
    print(f"\nCompleted at {datetime.now().isoformat()}")

if __name__ == "__main__":
    main()