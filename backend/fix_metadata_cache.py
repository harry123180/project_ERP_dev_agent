#!/usr/bin/env python3
"""
Critical Fix: SQLAlchemy Metadata Cache Issue for Requisitions
This script clears SQLAlchemy metadata cache and ensures database schema consistency
"""

import os
import sqlite3
from app import create_app, db
from sqlalchemy import text, MetaData

def fix_metadata_cache_issue():
    """Fix SQLAlchemy metadata cache issue that's causing enum constraint errors"""
    
    app = create_app()
    with app.app_context():
        try:
            print("🔍 Diagnosing SQLAlchemy metadata cache issue...")
            
            # Step 1: Clear SQLAlchemy metadata cache completely
            print("🧹 Clearing SQLAlchemy metadata cache...")
            db.metadata.clear()
            
            # Step 2: Force recreation of metadata from database
            print("🔄 Forcing metadata refresh from database...")
            db.metadata.reflect(bind=db.engine)
            
            # Step 3: Check if enum constraints exist in the database schema
            db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            if 'sqlite:///' in db_uri:
                db_path = db_uri.replace('sqlite:///', '')
                print(f"Database file: {db_path}")
                
                # Connect directly to SQLite
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check table schema for enum constraints
                cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='request_orders'")
                schema = cursor.fetchone()
                if schema:
                    schema_sql = schema[0]
                    print("Current schema:")
                    print(schema_sql)
                    
                    if 'usage_type_enum' in schema_sql or 'CHECK' in schema_sql:
                        print("🚨 Found enum constraints in database schema!")
                        
                        # Recreate table without constraints
                        print("🔧 Recreating table without enum constraints...")
                        
                        # Backup data
                        cursor.execute("CREATE TABLE request_orders_temp AS SELECT * FROM request_orders")
                        
                        # Drop original table
                        cursor.execute("DROP TABLE request_orders")
                        
                        # Create new table with clean schema
                        cursor.execute("""
                            CREATE TABLE request_orders (
                                request_order_no VARCHAR(50) PRIMARY KEY,
                                requester_id INTEGER NOT NULL,
                                requester_name VARCHAR(100) NOT NULL,
                                usage_type VARCHAR(20) NOT NULL,
                                project_id VARCHAR(50),
                                submit_date DATE,
                                order_status VARCHAR(20) NOT NULL DEFAULT 'draft',
                                created_at DATETIME,
                                updated_at DATETIME,
                                FOREIGN KEY (requester_id) REFERENCES users(user_id),
                                FOREIGN KEY (project_id) REFERENCES projects(project_id)
                            )
                        """)
                        
                        # Restore data
                        cursor.execute("INSERT INTO request_orders SELECT * FROM request_orders_temp")
                        
                        # Drop temporary table
                        cursor.execute("DROP TABLE request_orders_temp")
                        
                        conn.commit()
                        print("✅ Table recreated without constraints")
                    else:
                        print("✅ No enum constraints found in schema")
                
                conn.close()
            
            # Step 4: Force SQLAlchemy to completely forget old metadata
            print("🗑️ Purging SQLAlchemy engine metadata...")
            db.engine.dispose()
            
            # Step 5: Recreate metadata from scratch
            print("🆕 Creating fresh metadata...")
            db.metadata.clear()
            
            # Step 6: Test with fresh connection
            print("🧪 Testing with fresh SQLAlchemy connection...")
            
            # Import model with fresh metadata
            from app.models.request_order import RequestOrder
            
            # Test query that was failing
            orders = RequestOrder.query.all()
            print(f"✅ Successfully queried {len(orders)} requisitions")
            
            # Show sample data
            for order in orders[:3]:
                print(f"   - {order.request_order_no}: {order.usage_type} ({order.order_status})")
            
            # Step 7: Test specific problematic values
            chinese_orders = RequestOrder.query.filter_by(usage_type='消耗品').all()
            print(f"✅ Successfully queried {len(chinese_orders)} orders with Chinese usage_type")
            
            return True
            
        except Exception as e:
            print(f"❌ Error during metadata fix: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("🚀 Starting Critical Metadata Cache Fix")
    success = fix_metadata_cache_issue()
    if success:
        print("🎉 Metadata cache fix completed successfully!")
        print("🔄 Please restart your Flask application to apply changes")
    else:
        print("💥 Metadata cache fix failed")