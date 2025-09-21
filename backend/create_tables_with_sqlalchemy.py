#!/usr/bin/env python3
"""
Create receiving tables using SQLAlchemy
"""

from app import create_app, db
from app.models.receiving import ReceivingRecord, PendingStorageItem
from app.models.storage import Storage, StorageHistory

def create_tables():
    app = create_app()
    
    with app.app_context():
        print("Creating receiving tables with SQLAlchemy...")
        
        try:
            # Create all tables defined in models
            db.create_all()
            print("✅ Successfully created all tables!")
            
            # Verify the tables were created
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            receiving_tables = [t for t in tables if 'receiving' in t or 'pending' in t or 'storage' in t]
            print(f"Tables found: {receiving_tables}")
            
            if 'receiving_records' in tables:
                print("✅ receiving_records table exists")
            else:
                print("❌ receiving_records table missing")
                
            if 'pending_storage_items' in tables:
                print("✅ pending_storage_items table exists")
            else:
                print("❌ pending_storage_items table missing")
                
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            return False
    
    return True

if __name__ == "__main__":
    create_tables()