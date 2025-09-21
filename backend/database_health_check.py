#!/usr/bin/env python3
"""
Database Health Check Script
Validates database connectivity and configuration alignment
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_database_connection():
    """Check database connectivity and return status"""
    database_url = os.environ.get('DATABASE_URL')
    fallback_url = os.environ.get('DATABASE_URL_FALLBACK')
    
    print("=== Database Health Check ===")
    print(f"Primary DATABASE_URL: {database_url}")
    print(f"Fallback DATABASE_URL_FALLBACK: {fallback_url}")
    print()
    
    # Test primary database
    if database_url:
        try:
            print(f"Testing primary database connection...")
            engine = create_engine(database_url)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test"))
                if result.fetchone()[0] == 1:
                    print("✅ PRIMARY DATABASE: Connection successful")
                    print(f"   Database type: {engine.dialect.name}")
                    print(f"   Database URL: {database_url}")
                    return True, "primary", database_url
        except Exception as e:
            print(f"❌ PRIMARY DATABASE: Connection failed")
            print(f"   Error: {str(e)}")
            print(f"   URL: {database_url}")
    
    # Test fallback database if primary fails
    if fallback_url:
        try:
            print(f"\nTesting fallback database connection...")
            engine = create_engine(fallback_url)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test"))
                if result.fetchone()[0] == 1:
                    print("⚠️  FALLBACK DATABASE: Connection successful")
                    print(f"   Database type: {engine.dialect.name}")
                    print(f"   Database URL: {fallback_url}")
                    return True, "fallback", fallback_url
        except Exception as e:
            print(f"❌ FALLBACK DATABASE: Connection failed")
            print(f"   Error: {str(e)}")
            print(f"   URL: {fallback_url}")
    
    print(f"\n❌ NO DATABASE: All database connections failed")
    return False, "none", None

def check_database_alignment():
    """Check if database configuration aligns with specifications"""
    print("\n=== Database Specification Alignment ===")
    
    database_url = os.environ.get('DATABASE_URL', '')
    spec_database = "PostgreSQL 17"
    
    if 'postgresql' in database_url.lower():
        print(f"✅ Database type aligns with specification")
        print(f"   Specification: {spec_database}")
        print(f"   Configuration: PostgreSQL (from DATABASE_URL)")
    elif 'sqlite' in database_url.lower():
        print(f"⚠️  Database type differs from specification")
        print(f"   Specification: {spec_database}")
        print(f"   Configuration: SQLite (from DATABASE_URL)")
        print(f"   Note: This may be acceptable for development/testing")
    else:
        print(f"❓ Unable to determine database type from URL")
        print(f"   Specification: {spec_database}")
        print(f"   Configuration: {database_url}")

def provide_recommendations():
    """Provide recommendations based on findings"""
    print("\n=== Recommendations ===")
    
    success, db_type, db_url = check_database_connection()
    
    if not success:
        print("🔧 IMMEDIATE ACTION REQUIRED:")
        print("   1. Install and start PostgreSQL server")
        print("   2. Create database: createdb erp_development")
        print("   3. Verify connection with: psql postgresql://postgres:password@localhost:5432/erp_development")
        print("   4. Alternative: Install Redis and keep SQLite for quick testing")
        return False
    
    if db_type == "fallback":
        print("🔧 RECOMMENDED ACTIONS:")
        print("   1. Install PostgreSQL for better production alignment")
        print("   2. Current SQLite setup is functional but not ideal for production")
        print("   3. Consider setting up PostgreSQL for development consistency")
    
    if db_type == "primary":
        if 'postgresql' in db_url.lower():
            print("✅ OPTIMAL CONFIGURATION:")
            print("   1. Database type aligns with production specifications")
            print("   2. Ready for production deployment")
            print("   3. Consider setting up connection pooling for production")
        else:
            print("⚠️  CONFIGURATION NOTES:")
            print("   1. Primary database connected successfully")
            print("   2. Verify this aligns with your production requirements")
    
    return True

def check_redis_connection():
    """Check Redis connectivity for caching layer"""
    print("\n=== Redis Health Check ===")
    
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    print(f"Redis URL: {redis_url}")
    
    try:
        import redis
        r = redis.from_url(redis_url)
        r.ping()
        print("✅ REDIS: Connection successful")
        print("   Caching layer is operational")
        return True
    except ImportError:
        print("⚠️  REDIS: redis package not installed")
        print("   Install with: pip install redis")
        return False
    except Exception as e:
        print(f"❌ REDIS: Connection failed")
        print(f"   Error: {str(e)}")
        print(f"   Note: Redis is optional but recommended for production")
        return False

def main():
    """Main health check function"""
    print("🔍 ERP System Database Health Check")
    print("=" * 50)
    
    # Check database connectivity
    db_success = check_database_connection()
    
    # Check database alignment with specs
    check_database_alignment()
    
    # Check Redis connectivity
    redis_success = check_redis_connection()
    
    # Provide recommendations
    overall_success = provide_recommendations()
    
    print("\n" + "=" * 50)
    if db_success[0] and overall_success:
        print("✅ OVERALL STATUS: System ready for development")
        sys.exit(0)
    else:
        print("⚠️  OVERALL STATUS: System needs configuration attention")
        sys.exit(1)

if __name__ == "__main__":
    main()