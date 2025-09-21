#!/usr/bin/env python3
"""
Critical Bug Fix: Database Enum Mismatch
Fix for P0-001: Requisition listing HTTP 500 error
"""

from app import create_app, db
from sqlalchemy import text

def fix_enum_mismatch():
    """Fix the usage_type_enum mismatch between model and database"""
    
    app = create_app()
    with app.app_context():
        try:
            print("🔍 Diagnosing enum issue...")
            
            # Check current enum values
            result = db.session.execute(text("SELECT unnest(enum_range(NULL::usage_type_enum))"))
            current_values = [row[0] for row in result]
            print(f"Current database enum values: {current_values}")
            
            expected_values = ['daily', 'project', '消耗品']
            missing_values = [v for v in expected_values if v not in current_values]
            
            if missing_values:
                print(f"Missing enum values: {missing_values}")
                
                # Add missing enum values
                for value in missing_values:
                    print(f"Adding enum value: {value}")
                    db.session.execute(text(f"ALTER TYPE usage_type_enum ADD VALUE '{value}'"))
                
                db.session.commit()
                print("✅ Successfully updated enum type")
            else:
                print("✅ All enum values are present")
                
            # Test the fix by querying requisitions
            from app.models.request_order import RequestOrder
            orders = RequestOrder.query.all()
            print(f"✅ Successfully loaded {len(orders)} requisitions")
            
            # Test specific cases
            daily_orders = RequestOrder.query.filter_by(usage_type='daily').count()
            project_orders = RequestOrder.query.filter_by(usage_type='project').count()
            consumable_orders = RequestOrder.query.filter_by(usage_type='消耗品').count()
            
            print(f"📊 Breakdown:")
            print(f"   Daily orders: {daily_orders}")
            print(f"   Project orders: {project_orders}")
            print(f"   Consumable orders (消耗品): {consumable_orders}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error during fix: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("🚀 Starting Critical Bug Fix for P0-001")
    success = fix_enum_mismatch()
    if success:
        print("🎉 Bug fix completed successfully!")
    else:
        print("💥 Bug fix failed - manual intervention required")