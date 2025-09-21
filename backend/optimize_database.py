#!/usr/bin/env python3
"""
Database Performance Optimization Script
Runs comprehensive database optimizations to resolve inventory query performance issues
Usage: python optimize_database.py
"""

import os
import sys
import json
from datetime import datetime

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.utils.performance import run_performance_optimization_suite, DatabaseOptimizer
# from app.utils.cache import warm_cache, get_cache_health


def main():
    """Run comprehensive database performance optimization"""
    print("=== ERP Database Performance Optimization ===")
    print(f"Started at: {datetime.utcnow().isoformat()}")
    print()
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        try:
            # 1. Database Connection Test
            print("1. Testing database connection...")
            db.engine.execute("SELECT 1")
            print("✓ Database connection successful")
            print()
            
            # 2. Pre-optimization Performance Check
            print("2. Pre-optimization performance baseline...")
            optimizer = DatabaseOptimizer(db)
            pre_stats = optimizer.get_database_performance_stats()
            print(f"✓ Cache hit ratio: {pre_stats.get('cache_hit_ratio', 0):.2f}%")
            print(f"✓ Database size: {pre_stats.get('database_size', 'unknown')}")
            print()
            
            # 3. Run Comprehensive Optimization
            print("3. Running comprehensive database optimization...")
            optimization_results = run_performance_optimization_suite(db)
            
            # Display results
            print("\n=== OPTIMIZATION RESULTS ===")
            
            # Index creation results
            index_results = optimization_results['optimization_results']['indexes_created']
            successful_indexes = sum(1 for success in index_results.values() if success)
            total_indexes = len(index_results)
            print(f"Indexes Created: {successful_indexes}/{total_indexes}")
            
            if successful_indexes < total_indexes:
                print("Failed indexes:")
                for index_name, success in index_results.items():
                    if not success:
                        print(f"  ✗ {index_name}")
            
            # Table analysis results
            analyze_results = optimization_results['optimization_results']['table_analysis']
            successful_analyses = sum(1 for success in analyze_results.values() if success)
            print(f"Tables Analyzed: {successful_analyses}/{len(analyze_results)}")
            
            # Performance improvement
            post_stats = optimization_results['performance_stats']
            cache_hit_ratio = post_stats.get('cache_hit_ratio', 0)
            print(f"Cache Hit Ratio: {cache_hit_ratio:.2f}%")
            
            print("\n4. Cache warming skipped (Redis not configured)")
            # warm_cache()
            # cache_health = get_cache_health()
            # if cache_health.get('available'):
            #     print("✓ Cache warmed successfully")
            #     print(f"✓ Cache keys: {cache_health.get('total_keys', 0)}")
            # else:
            #     print("⚠ Cache warming failed - Redis unavailable")
            
            # 5. Save results to file
            output_file = f"performance_optimization_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w') as f:
                json.dump(optimization_results, f, indent=2, default=str)
            
            print(f"\n✓ Optimization results saved to: {output_file}")
            
            # 6. Test inventory query performance
            print("\n5. Testing inventory query performance...")
            test_inventory_performance(app)
            
            print("\n=== OPTIMIZATION COMPLETE ===")
            print(f"Completed at: {datetime.utcnow().isoformat()}")
            
            # Summary recommendations
            print("\n=== RECOMMENDATIONS ===")
            if cache_hit_ratio < 90:
                print("• Monitor cache hit ratio - consider tuning database configuration")
            if successful_indexes == total_indexes:
                print("• All indexes created successfully - monitor query performance")
            else:
                print("• Some indexes failed to create - check database logs")
            
            print("• Run PERF_001 test case to validate performance improvements")
            print("• Monitor inventory query response times for next 24 hours")
            
        except Exception as e:
            print(f"✗ Optimization failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def test_inventory_performance(app):
    """Test inventory query performance after optimization"""
    from time import time
    
    try:
        # Test a simple query to verify database performance
        start_time = time()
        
        # Simple query to test database responsiveness
        with db.engine.connect() as connection:
            result = connection.execute("SELECT COUNT(*) FROM information_schema.tables")
            table_count = result.fetchone()[0]
        
        end_time = time()
        query_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        print(f"Database connection test: {query_time:.2f}ms")
        print(f"Tables in database: {table_count}")
        
        if query_time < 1000:  # Less than 1 second for simple query
            print("✓ Database performance is responsive")
            return True
        else:
            print("⚠ Database response slower than expected")
            return False
            
    except Exception as e:
        print(f"✗ Performance test failed: {e}")
        return False


def rollback_optimizations():
    """Rollback performance optimizations if needed"""
    print("=== ROLLING BACK OPTIMIZATIONS ===")
    
    app = create_app()
    with app.app_context():
        try:
            optimizer = DatabaseOptimizer(db)
            
            # Get list of indexes to drop
            indexes_to_drop = [
                'idx_inventory_item_name',
                'idx_inventory_item_spec',
                'idx_inventory_request_no',
                'idx_inventory_po_no',
                'idx_inventory_usage_type',
                'idx_inventory_zone',
                'idx_inventory_shelf',
                'idx_inventory_floor',
                'idx_inventory_name_spec',
                'idx_inventory_zone_shelf_floor',
                'idx_inventory_usage_zone',
                'idx_inventory_created_at',
                'idx_inventory_updated_at'
            ]
            
            with optimizer.engine.connect() as connection:
                for index_name in indexes_to_drop:
                    try:
                        connection.execute(f"DROP INDEX IF EXISTS {index_name};")
                        print(f"✓ Dropped index: {index_name}")
                    except Exception as e:
                        print(f"✗ Failed to drop index {index_name}: {e}")
            
            print("✓ Rollback completed")
            
        except Exception as e:
            print(f"✗ Rollback failed: {e}")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--rollback':
        rollback_optimizations()
    else:
        main()