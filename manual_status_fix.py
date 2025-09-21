#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app, db
from app.models.request_order import RequestOrder

def fix_status():
    app = create_app()
    with app.app_context():
        req = RequestOrder.query.filter_by(request_order_no='REQ20250909036').first()
        if req:
            print(f"Before: {req.order_status}")
            req.update_status_after_review()
            print(f"After: {req.order_status}")
            db.session.commit()
            print("Committed")
        else:
            print("Not found")

if __name__ == "__main__":
    fix_status()
