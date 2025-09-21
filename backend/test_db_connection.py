#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from config import Config

def test_database_config():
    """Test database configuration and connection"""
    print("=== Database Configuration Test ===")
    
    # Check environment variables
    print(f"DATABASE_URL: {os.environ.get('DATABASE_URL', 'NOT SET')}")
    print(f"DATABASE_URL_FALLBACK: {os.environ.get('DATABASE_URL_FALLBACK', 'NOT SET')}")
    print(f"FLASK_ENV: {os.environ.get('FLASK_ENV', 'NOT SET')}")
    
    # Check config
    config = Config()
    print(f"Config SQLALCHEMY_DATABASE_URI: {config.SQLALCHEMY_DATABASE_URI}")
    
    # Test actual database connection
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(config.SQLALCHEMY_DATABASE_URI, echo=False)
        
        # Show the actual path being used
        if config.SQLALCHEMY_DATABASE_URI.startswith('sqlite:'):
            db_path = config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')
            full_path = os.path.abspath(db_path)
            print(f"Database file path: {full_path}")
            print(f"Database file exists: {os.path.exists(full_path)}")
            if os.path.exists(full_path):
                print(f"Database file size: {os.path.getsize(full_path)} bytes")
        
        with engine.connect() as connection:
            # Test basic query
            result = connection.execute(text("SELECT COUNT(*) as supplier_count FROM suppliers"))
            supplier_count = result.fetchone()[0]
            print(f"✓ Database connection successful!")
            print(f"✓ Supplier count: {supplier_count}")
            
            # Check request orders
            result = connection.execute(text("SELECT COUNT(*) as order_count FROM request_orders"))
            order_count = result.fetchone()[0]
            print(f"✓ Request order count: {order_count}")
            
            # Check purchase orders
            result = connection.execute(text("SELECT COUNT(*) as po_count FROM purchase_orders"))
            po_count = result.fetchone()[0]
            print(f"✓ Purchase order count: {po_count}")
            
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_database_config()