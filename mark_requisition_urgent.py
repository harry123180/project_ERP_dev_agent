#!/usr/bin/env python
"""
Script to mark a requisition as urgent for testing the urgent display features
"""
import os
import sys
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.request_order import RequestOrder

def mark_requisition_urgent(req_no):
    """Mark a requisition as urgent with expected delivery date and reason"""
    app = create_app()

    with app.app_context():
        # Find the requisition
        requisition = RequestOrder.query.filter_by(request_order_no=req_no).first()

        if not requisition:
            print(f"Error: Requisition {req_no} not found")
            return False

        # Mark as urgent
        requisition.is_urgent = True
        requisition.expected_delivery_date = datetime.now().date() + timedelta(days=3)  # 3 days from now
        requisition.urgent_reason = "緊急專案需求，需要立即處理以避免生產線停擺"

        try:
            db.session.commit()
            print(f"Successfully marked requisition {req_no} as urgent")
            print(f"  - Expected delivery: {requisition.expected_delivery_date}")
            print(f"  - Reason: {requisition.urgent_reason}")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error updating requisition: {e}")
            return False

if __name__ == "__main__":
    # Mark REQ20250916001 as urgent
    success = mark_requisition_urgent("REQ20250916001")

    if success:
        print("\n✓ Requisition has been marked as urgent.")
        print("You should now see:")
        print("  1. Red highlighting in the requisition list")
        print("  2. '加急' label in the status column")
        print("  3. Red background for the row")
        print("  4. Urgent indicator in the review dialog")
    else:
        print("\n✗ Failed to update requisition")