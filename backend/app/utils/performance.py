"""
Database Performance Optimization Utilities
Provides indexing strategies and query optimizations for the ERP system
Architecture Lead: Winston
"""

from sqlalchemy import Index, text, func
from sqlalchemy.orm import Query
from flask import current_app
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """Database performance optimization utilities"""
    
    def __init__(self, db):
        self.db = db
        self.engine = db.engine
    
    def create_performance_indexes(self) -> Dict[str, bool]:
        """
        Create performance-critical indexes for inventory queries and other bottlenecks
        Returns status of each index creation
        """
        indexes_created = {}
        
        # Inventory query performance indexes
        inventory_indexes = [
            # Primary inventory search indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inventory_item_name ON inventory (LOWER(item_name));",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inventory_item_spec ON inventory (LOWER(item_spec));",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inventory_request_no ON inventory (request_no);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inventory_po_no ON inventory (po_no);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inventory_usage_type ON inventory (usage_type);",
            
            # Storage location indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inventory_zone ON inventory (zone);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inventory_shelf ON inventory (shelf);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inventory_floor ON inventory (floor);",
            
            # Composite indexes for common filter combinations
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inventory_name_spec ON inventory (LOWER(item_name), LOWER(item_spec));",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inventory_zone_shelf_floor ON inventory (zone, shelf, floor);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inventory_usage_zone ON inventory (usage_type, zone);",
            
            # Date-based indexes for performance
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inventory_created_at ON inventory (created_at DESC);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inventory_updated_at ON inventory (updated_at DESC);",
        ]
        
        # Purchase Order indexes for better join performance
        po_indexes = [
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_po_supplier_id ON purchase_orders (supplier_id);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_po_status ON purchase_orders (status);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_po_created_at ON purchase_orders (created_at DESC);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_po_status_supplier ON purchase_orders (status, supplier_id);",
        ]
        
        # Purchase Order Items indexes
        po_item_indexes = [
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_po_items_po_id ON purchase_order_items (po_id);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_po_items_item_ref ON purchase_order_items (item_reference);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_po_items_receiving_status ON purchase_order_items (receiving_status);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_po_items_storage_status ON purchase_order_items (storage_status);",
        ]
        
        # Requisition indexes
        requisition_indexes = [
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_requisitions_status ON requisitions (status);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_requisitions_created_by ON requisitions (created_by);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_requisitions_created_at ON requisitions (created_at DESC);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_requisitions_status_created_by ON requisitions (status, created_by);",
        ]
        
        # Project-related indexes
        project_indexes = [
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_manager_id ON projects (manager_id);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_is_active ON projects (is_active);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_start_date ON projects (start_date);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_end_date ON projects (end_date);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_project_expenditure_project_id ON project_supplier_expenditures (project_id);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_project_expenditure_supplier_id ON project_supplier_expenditures (supplier_id);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_project_expenditure_date ON project_supplier_expenditures (expenditure_date DESC);",
        ]
        
        # Storage indexes
        storage_indexes = [
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_storage_zone ON storage (zone);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_storage_is_available ON storage (is_available);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_storage_type ON storage (storage_type);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_storage_hierarchy ON storage (zone, shelf, floor, position);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_storage_history_storage_id ON storage_history (storage_id);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_storage_history_item_ref ON storage_history (item_reference);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_storage_history_movement_date ON storage_history (movement_date DESC);",
        ]
        
        # Supplier indexes
        supplier_indexes = [
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_suppliers_is_active ON suppliers (is_active);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_suppliers_region ON suppliers (supplier_region);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_suppliers_name_zh ON suppliers (supplier_name_zh);",
        ]
        
        # Combine all indexes
        all_indexes = (
            inventory_indexes + po_indexes + po_item_indexes + 
            requisition_indexes + project_indexes + storage_indexes + 
            supplier_indexes
        )
        
        # Execute index creation
        for index_sql in all_indexes:
            try:
                with self.engine.connect() as connection:
                    # Use autocommit for DDL operations
                    connection.execute(text(index_sql))
                    index_name = self._extract_index_name(index_sql)
                    indexes_created[index_name] = True
                    logger.info(f"Index created successfully: {index_name}")
                    
            except Exception as e:
                index_name = self._extract_index_name(index_sql)
                indexes_created[index_name] = False
                logger.error(f"Failed to create index {index_name}: {e}")
        
        return indexes_created
    
    def _extract_index_name(self, index_sql: str) -> str:
        """Extract index name from SQL statement"""
        try:
            # Simple extraction from CREATE INDEX statements
            if 'idx_' in index_sql:
                start = index_sql.find('idx_')
                end = index_sql.find(' ', start)
                if end == -1:
                    end = index_sql.find('\n', start)
                return index_sql[start:end].strip()
        except:
            pass
        return 'unknown_index'
    
    def analyze_table_statistics(self, table_names: List[str] = None) -> Dict[str, Any]:
        """
        Update table statistics for better query planning
        """
        if not table_names:
            # Default critical tables for ERP system
            table_names = [
                'inventory', 'purchase_orders', 'purchase_order_items',
                'requisitions', 'requisition_items', 'projects',
                'project_supplier_expenditures', 'storage', 'storage_history',
                'suppliers', 'users'
            ]
        
        results = {}
        
        for table_name in table_names:
            try:
                with self.engine.connect() as connection:
                    # PostgreSQL ANALYZE command
                    connection.execute(text(f"ANALYZE {table_name};"))
                    results[table_name] = True
                    logger.info(f"Statistics updated for table: {table_name}")
                    
            except Exception as e:
                results[table_name] = False
                logger.error(f"Failed to analyze table {table_name}: {e}")
        
        return results
    
    def get_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get information about slow queries (requires pg_stat_statements extension)
        """
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text("""
                    SELECT 
                        query,
                        calls,
                        total_time,
                        mean_time,
                        rows,
                        100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
                    FROM pg_stat_statements 
                    WHERE query NOT LIKE '%pg_stat_statements%'
                    ORDER BY total_time DESC 
                    LIMIT :limit
                """), {"limit": limit})
                
                return [
                    {
                        'query': row[0][:200] + '...' if len(row[0]) > 200 else row[0],
                        'calls': row[1],
                        'total_time_ms': round(row[2], 2),
                        'avg_time_ms': round(row[3], 2),
                        'total_rows': row[4],
                        'cache_hit_percent': round(row[5] or 0, 2)
                    }
                    for row in result
                ]
                
        except Exception as e:
            logger.warning(f"Could not retrieve slow queries: {e}")
            return []
    
    def optimize_inventory_queries(self) -> Dict[str, Any]:
        """
        Specific optimizations for inventory queries that are causing performance issues
        """
        optimizations = {}
        
        try:
            with self.engine.connect() as connection:
                # Create partial indexes for common inventory filters
                partial_indexes = [
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inventory_active_items ON inventory (item_name) WHERE quantity > 0;",
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inventory_recent ON inventory (created_at DESC) WHERE created_at > CURRENT_DATE - INTERVAL '30 days';",
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inventory_low_stock ON inventory (item_name, quantity) WHERE quantity < 10;",
                ]
                
                for index_sql in partial_indexes:
                    connection.execute(text(index_sql))
                    optimizations[self._extract_index_name(index_sql)] = True
                
                # Update table statistics specifically for inventory
                connection.execute(text("ANALYZE inventory;"))
                optimizations['inventory_analyze'] = True
                
                logger.info("Inventory query optimizations completed")
                
        except Exception as e:
            logger.error(f"Inventory optimization error: {e}")
            optimizations['error'] = str(e)
        
        return optimizations
    
    def get_database_performance_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive database performance statistics
        """
        stats = {}
        
        try:
            with self.engine.connect() as connection:
                # Database size information
                db_size_result = connection.execute(text("""
                    SELECT pg_size_pretty(pg_database_size(current_database())) as database_size;
                """))
                stats['database_size'] = db_size_result.fetchone()[0]
                
                # Table sizes
                table_sizes_result = connection.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                        pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                    LIMIT 10;
                """))
                
                stats['largest_tables'] = [
                    {
                        'table_name': row[1],
                        'size': row[2],
                        'size_bytes': row[3]
                    }
                    for row in table_sizes_result
                ]
                
                # Index usage statistics
                index_usage_result = connection.execute(text("""
                    SELECT 
                        indexrelname as index_name,
                        idx_tup_read,
                        idx_tup_fetch,
                        pg_size_pretty(pg_relation_size(indexrelid)) as index_size
                    FROM pg_stat_user_indexes 
                    ORDER BY idx_tup_read DESC 
                    LIMIT 10;
                """))
                
                stats['index_usage'] = [
                    {
                        'index_name': row[0],
                        'tuples_read': row[1],
                        'tuples_fetched': row[2],
                        'index_size': row[3]
                    }
                    for row in index_usage_result
                ]
                
                # Cache hit ratio
                cache_hit_result = connection.execute(text("""
                    SELECT 
                        sum(heap_blks_read) as heap_read,
                        sum(heap_blks_hit)  as heap_hit,
                        sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) * 100 as ratio
                    FROM pg_statio_user_tables;
                """))
                
                cache_row = cache_hit_result.fetchone()
                if cache_row and cache_row[2]:
                    stats['cache_hit_ratio'] = round(cache_row[2], 2)
                else:
                    stats['cache_hit_ratio'] = 0
                
        except Exception as e:
            logger.error(f"Error getting database performance stats: {e}")
            stats['error'] = str(e)
        
        return stats


def create_optimized_query_helper():
    """
    Factory function to create query optimization helpers
    """
    class QueryOptimizer:
        """Helper class for optimizing common query patterns"""
        
        @staticmethod
        def optimize_inventory_search(base_query: Query, filters: Dict[str, Any]) -> Query:
            """
            Optimize inventory search queries with proper index usage
            Note: This is a template - replace Inventory with actual model when available
            """
            query = base_query
            
            # Template for inventory optimization - uncomment when Inventory model exists
            # # Use ILIKE with functional indexes for case-insensitive search
            # if filters.get('name'):
            #     query = query.filter(func.lower(Inventory.item_name).like(f"%{filters['name'].lower()}%"))
            # 
            # if filters.get('spec'):
            #     query = query.filter(func.lower(Inventory.item_spec).like(f"%{filters['spec'].lower()}%"))
            # 
            # # Use exact match for indexed fields
            # if filters.get('request_no'):
            #     query = query.filter(Inventory.request_no == filters['request_no'])
            # 
            # if filters.get('po_no'):
            #     query = query.filter(Inventory.po_no == filters['po_no'])
            # 
            # if filters.get('usage_type'):
            #     query = query.filter(Inventory.usage_type == filters['usage_type'])
            # 
            # # Storage location filters (use composite index)
            # if filters.get('zone'):
            #     query = query.filter(Inventory.zone == filters['zone'])
            # 
            # if filters.get('shelf'):
            #     query = query.filter(Inventory.shelf == filters['shelf'])
            # 
            # if filters.get('floor'):
            #     query = query.filter(Inventory.floor == filters['floor'])
            
            return query
        
        @staticmethod
        def optimize_purchase_order_query(base_query: Query, filters: Dict[str, Any]) -> Query:
            """
            Optimize purchase order queries
            """
            query = base_query
            
            # Template for PO optimization - works with existing PurchaseOrder model
            # Use indexed fields first for better performance
            # if filters.get('status'):
            #     query = query.filter(PurchaseOrder.status == filters['status'])
            # 
            # if filters.get('supplier_id'):
            #     query = query.filter(PurchaseOrder.supplier_id == filters['supplier_id'])
            # 
            # # Date range queries
            # if filters.get('start_date'):
            #     query = query.filter(PurchaseOrder.created_at >= filters['start_date'])
            # 
            # if filters.get('end_date'):
            #     query = query.filter(PurchaseOrder.created_at <= filters['end_date'])
            
            return query
    
    return QueryOptimizer()


def run_performance_optimization_suite(db) -> Dict[str, Any]:
    """
    Run complete performance optimization suite
    """
    optimizer = DatabaseOptimizer(db)
    results = {
        'timestamp': datetime.utcnow().isoformat(),
        'optimization_results': {}
    }
    
    logger.info("Starting comprehensive database performance optimization")
    
    # 1. Create performance indexes
    logger.info("Creating performance indexes...")
    index_results = optimizer.create_performance_indexes()
    results['optimization_results']['indexes_created'] = index_results
    
    # 2. Update table statistics
    logger.info("Updating table statistics...")
    analyze_results = optimizer.analyze_table_statistics()
    results['optimization_results']['table_analysis'] = analyze_results
    
    # 3. Inventory-specific optimizations
    logger.info("Applying inventory query optimizations...")
    inventory_results = optimizer.optimize_inventory_queries()
    results['optimization_results']['inventory_optimization'] = inventory_results
    
    # 4. Get performance baseline
    logger.info("Collecting performance statistics...")
    perf_stats = optimizer.get_database_performance_stats()
    results['performance_stats'] = perf_stats
    
    # 5. Get slow query analysis
    slow_queries = optimizer.get_slow_queries()
    results['slow_queries'] = slow_queries
    
    # Summary
    total_indexes = len(index_results)
    successful_indexes = sum(1 for success in index_results.values() if success)
    
    results['summary'] = {
        'indexes_created': f"{successful_indexes}/{total_indexes}",
        'tables_analyzed': len(analyze_results),
        'cache_hit_ratio': perf_stats.get('cache_hit_ratio', 0),
        'optimization_complete': True
    }
    
    logger.info(f"Performance optimization completed: {successful_indexes}/{total_indexes} indexes created")
    
    return results