#!/usr/bin/env python3
"""
Critical Bug Fix: SQLite Enum Constraint Issue
Fix for P0-001: Requisition listing fails due to SQLite enum constraint
"""

from app import create_app, db
from sqlalchemy import text

def fix_sqlite_enum_issue():
    """Fix the SQLite enum constraint issue"""
    
    app = create_app()
    with app.app_context():
        try:
            print("🔍 Analyzing SQLite database...")
            
            # Check if we have any data that violates the constraint
            result = db.session.execute(text("SELECT DISTINCT usage_type FROM request_orders"))
            existing_values = [row[0] for row in result]
            print(f"Existing usage_type values in database: {existing_values}")
            
            # Check model definition
            from app.models.request_order import RequestOrder
            print("Model expects enum values: ['daily', 'project', '消耗品']")
            
            # The issue is SQLAlchemy's enum constraint with SQLite
            # In SQLite, we need to handle this differently
            
            # Let's check if there are problematic records
            problematic_records = []
            valid_values = ['daily', 'project', '消耗品']
            
            for value in existing_values:
                if value not in valid_values:
                    count = db.session.execute(text(f"SELECT COUNT(*) FROM request_orders WHERE usage_type = '{value}'")).scalar()
                    problematic_records.append((value, count))
                    print(f"Found {count} records with invalid usage_type: '{value}'")
            
            if problematic_records:
                print("\n🔧 Fixing invalid records...")
                # Convert invalid values to valid ones
                for invalid_value, count in problematic_records:
                    # Map invalid values to valid ones
                    if '消耗' in invalid_value or 'consumable' in invalid_value.lower():
                        new_value = '消耗品'
                    else:
                        new_value = 'daily'  # default fallback
                    
                    print(f"Converting '{invalid_value}' -> '{new_value}' ({count} records)")
                    db.session.execute(text(f"UPDATE request_orders SET usage_type = '{new_value}' WHERE usage_type = '{invalid_value}'"))
                
                db.session.commit()
                print("✅ Records updated successfully")
            else:
                print("✅ No problematic records found")
            
            # Now test if we can query all records
            orders = RequestOrder.query.all()
            print(f"✅ Successfully loaded {len(orders)} requisitions")
            
            # Test the API endpoint that was failing
            print("\n🧪 Testing requisition listing...")
            orders = RequestOrder.query.limit(5).all()
            for order in orders:
                print(f"   - {order.request_order_no}: {order.usage_type}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error during fix: {str(e)}")
            db.session.rollback()
            
            # Let's try a different approach - disable enum constraint temporarily
            try:
                print("\n🔄 Attempting alternative fix...")
                
                # Check table structure
                result = db.session.execute(text("PRAGMA table_info(request_orders)"))
                columns = result.fetchall()
                for col in columns:
                    if col[1] == 'usage_type':
                        print(f"usage_type column: {col}")
                
                # If all else fails, we can rebuild the model without strict enum
                return False
                
            except Exception as e2:
                print(f"❌ Alternative fix failed: {str(e2)}")
                return False

if __name__ == "__main__":
    print("🚀 Starting Critical Bug Fix for SQLite Enum Issue")
    success = fix_sqlite_enum_issue()
    if success:
        print("🎉 Bug fix completed successfully!")
    else:
        print("💥 Bug fix failed - need model adjustment")