"""
Database Performance Optimization Utilities
Advanced database connection pooling and query optimization
Architecture Lead: Winston
"""

import logging
import time
from functools import wraps
from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager
from sqlalchemy import create_engine, event, pool, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool
from flask import current_app, g
import threading
import queue

logger = logging.getLogger(__name__)

class DatabaseConnectionManager:
    """Advanced database connection pool manager"""
    
    def __init__(self):
        self.engines = {}
        self.session_factories = {}
        self.connection_stats = {
            'total_connections': 0,
            'active_connections': 0,
            'query_count': 0,
            'slow_queries': 0,
            'failed_queries': 0,
            'connection_errors': 0
        }
        self.slow_query_threshold = 1.0  # seconds
        self.query_log = queue.Queue(maxsize=1000)
        self._lock = threading.Lock()
    
    def create_optimized_engine(self, database_url: str, **kwargs) -> Engine:
        """Create optimized database engine with advanced pooling"""
        
        # Enhanced connection pool settings
        engine_config = {
            'poolclass': QueuePool,
            'pool_size': 20,              # Base connection pool size
            'max_overflow': 40,           # Additional connections during peaks  
            'pool_recycle': 300,          # Recycle connections every 5 minutes
            'pool_pre_ping': True,        # Validate connections before use
            'pool_reset_on_return': 'commit',  # Reset connections on return
            'echo': current_app.config.get('SQLALCHEMY_ECHO', False),
            'echo_pool': current_app.config.get('DEBUG', False),
            'connect_args': {
                'connect_timeout': 30,
                'application_name': 'erp_backend',
                'options': '-c statement_timeout=30000'  # 30 second query timeout
            }
        }
        
        # Override with custom settings
        engine_config.update(kwargs)
        
        try:
            engine = create_engine(database_url, **engine_config)
            
            # Add event listeners for monitoring
            self._setup_engine_listeners(engine)
            
            logger.info(f"Database engine created successfully with pool size {engine_config['pool_size']}")
            return engine
            
        except Exception as e:
            logger.error(f"Failed to create database engine: {e}")
            raise
    
    def _setup_engine_listeners(self, engine: Engine):
        """Setup event listeners for database monitoring"""
        
        @event.listens_for(engine, "connect")
        def on_connect(dbapi_conn, connection_record):
            with self._lock:
                self.connection_stats['total_connections'] += 1
                self.connection_stats['active_connections'] += 1
        
        @event.listens_for(engine, "close")
        def on_close(dbapi_conn, connection_record):
            with self._lock:
                self.connection_stats['active_connections'] -= 1
        
        @event.listens_for(engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
        
        @event.listens_for(engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            execution_time = time.time() - context._query_start_time
            
            with self._lock:
                self.connection_stats['query_count'] += 1
                
                if execution_time > self.slow_query_threshold:
                    self.connection_stats['slow_queries'] += 1
                    
                    # Log slow query details
                    try:
                        self.query_log.put_nowait({
                            'timestamp': time.time(),
                            'execution_time': execution_time,
                            'statement': statement[:500],  # Truncate long statements
                            'parameters': str(parameters)[:200] if parameters else None
                        })
                    except queue.Full:
                        pass  # Queue is full, skip logging
        
        @event.listens_for(engine, "dbapi_error")
        def on_dbapi_error(exception, connection_record, statement, parameters, context, is_disconnect):
            with self._lock:
                self.connection_stats['failed_queries'] += 1
                if is_disconnect:
                    self.connection_stats['connection_errors'] += 1
                    
            logger.error(f"Database error: {exception}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get current connection statistics"""
        with self._lock:
            stats = self.connection_stats.copy()
        
        # Add calculated metrics
        stats['slow_query_percentage'] = (
            (stats['slow_queries'] / stats['query_count'] * 100) 
            if stats['query_count'] > 0 else 0
        )
        
        stats['error_rate'] = (
            (stats['failed_queries'] / stats['query_count'] * 100) 
            if stats['query_count'] > 0 else 0
        )
        
        return stats
    
    def get_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent slow queries"""
        queries = []
        
        try:
            while not self.query_log.empty() and len(queries) < limit:
                queries.append(self.query_log.get_nowait())
        except queue.Empty:
            pass
        
        # Sort by execution time (slowest first)
        queries.sort(key=lambda x: x['execution_time'], reverse=True)
        
        return queries[:limit]

# Global database connection manager
db_manager = DatabaseConnectionManager()

class QueryOptimizer:
    """Database query optimization utilities"""
    
    @staticmethod
    def optimize_pagination_query(query, page: int, page_size: int, max_page_size: int = 100):
        """Optimize pagination queries with limits"""
        # Ensure reasonable page size
        page_size = min(page_size, max_page_size)
        page = max(1, page)
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Apply limit and offset
        paginated_query = query.offset(offset).limit(page_size)
        
        return paginated_query
    
    @staticmethod
    def add_query_hints(query, hints: List[str]):
        """Add PostgreSQL query hints for optimization"""
        # PostgreSQL doesn't have traditional hints, but we can use comments
        # and specific query patterns for optimization
        
        if 'use_index' in hints:
            # Force index usage through query structure
            pass
        
        if 'parallel' in hints and hasattr(query, 'execution_options'):
            # Enable parallel execution
            query = query.execution_options(
                postgresql_readonly=True,
                postgresql_autocommit=True
            )
        
        return query
    
    @staticmethod
    def analyze_query_plan(session, query):
        """Analyze query execution plan"""
        try:
            # Get the compiled query
            compiled = query.statement.compile(compile_kwargs={"literal_binds": True})
            
            # Execute EXPLAIN ANALYZE
            explain_query = text(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {compiled}")
            result = session.execute(explain_query).fetchone()[0]
            
            return result
            
        except Exception as e:
            logger.error(f"Query plan analysis failed: {e}")
            return None

def optimize_query_performance(func):
    """Decorator to optimize database query performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Log slow queries for analysis
            if execution_time > db_manager.slow_query_threshold:
                logger.warning(f"Slow query detected: {func.__name__} took {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Query optimization error in {func.__name__}: {e}")
            raise
            
    return wrapper

@contextmanager
def optimized_db_session(read_only: bool = False):
    """Context manager for optimized database sessions"""
    from app import db
    
    session = db.session
    
    try:
        # Configure session for optimization
        if read_only:
            session.execute(text("SET TRANSACTION READ ONLY"))
        
        # Set query timeout
        session.execute(text("SET statement_timeout = '30s'"))
        
        yield session
        
        if not read_only:
            session.commit()
            
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()

class BatchProcessor:
    """Efficient batch processing for database operations"""
    
    @staticmethod
    def batch_insert(session, model_class, data_list: List[Dict], batch_size: int = 1000):
        """Efficient batch insert operation"""
        if not data_list:
            return 0
        
        total_inserted = 0
        
        try:
            for i in range(0, len(data_list), batch_size):
                batch = data_list[i:i + batch_size]
                
                # Use bulk_insert_mappings for better performance
                session.bulk_insert_mappings(model_class, batch)
                session.flush()
                
                total_inserted += len(batch)
                
                # Commit periodically to avoid long transactions
                if total_inserted % (batch_size * 5) == 0:
                    session.commit()
            
            session.commit()
            return total_inserted
            
        except Exception as e:
            session.rollback()
            logger.error(f"Batch insert error: {e}")
            raise
    
    @staticmethod
    def batch_update(session, model_class, updates: List[Dict], batch_size: int = 500):
        """Efficient batch update operation"""
        if not updates:
            return 0
        
        total_updated = 0
        
        try:
            for i in range(0, len(updates), batch_size):
                batch = updates[i:i + batch_size]
                
                # Use bulk_update_mappings for better performance
                session.bulk_update_mappings(model_class, batch)
                session.flush()
                
                total_updated += len(batch)
                
                # Commit periodically
                if total_updated % (batch_size * 5) == 0:
                    session.commit()
            
            session.commit()
            return total_updated
            
        except Exception as e:
            session.rollback()
            logger.error(f"Batch update error: {e}")
            raise

class DatabaseHealthChecker:
    """Database health monitoring and diagnostics"""
    
    @staticmethod
    def check_connection_health() -> Dict[str, Any]:
        """Check database connection health"""
        from app import db
        
        try:
            # Test basic connectivity
            start_time = time.time()
            db.session.execute(text('SELECT 1'))
            connection_time = time.time() - start_time
            
            # Get database statistics
            stats_query = text("""
                SELECT 
                    (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
                    (SELECT count(*) FROM pg_stat_activity) as total_connections,
                    (SELECT setting FROM pg_settings WHERE name = 'max_connections') as max_connections
            """)
            
            stats = db.session.execute(stats_query).fetchone()
            
            return {
                'status': 'healthy',
                'connection_time_ms': round(connection_time * 1000, 2),
                'active_connections': stats[0] if stats else 0,
                'total_connections': stats[1] if stats else 0,
                'max_connections': int(stats[2]) if stats else 0,
                'connection_utilization': round((stats[1] / int(stats[2])) * 100, 2) if stats else 0,
                'stats': db_manager.get_connection_stats()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'connection_time_ms': None
            }
    
    @staticmethod
    def get_database_metrics() -> Dict[str, Any]:
        """Get comprehensive database metrics"""
        from app import db
        
        try:
            metrics_query = text("""
                SELECT 
                    pg_size_pretty(pg_database_size(current_database())) as database_size,
                    (SELECT count(*) FROM pg_stat_user_tables) as table_count,
                    (SELECT count(*) FROM pg_stat_user_indexes) as index_count,
                    (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_queries,
                    (SELECT count(*) FROM pg_stat_activity WHERE state = 'idle in transaction') as idle_transactions
            """)
            
            result = db.session.execute(metrics_query).fetchone()
            
            # Get slow queries
            slow_queries = db_manager.get_slow_queries(5)
            
            return {
                'database_size': result[0] if result else 'Unknown',
                'table_count': result[1] if result else 0,
                'index_count': result[2] if result else 0,
                'active_queries': result[3] if result else 0,
                'idle_transactions': result[4] if result else 0,
                'recent_slow_queries': len(slow_queries),
                'slow_query_details': slow_queries
            }
            
        except Exception as e:
            logger.error(f"Database metrics error: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def check_table_health() -> Dict[str, Any]:
        """Check health of individual tables"""
        from app import db
        
        try:
            table_stats_query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_tuples,
                    n_dead_tup as dead_tuples,
                    last_vacuum,
                    last_autovacuum,
                    last_analyze,
                    last_autoanalyze
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                ORDER BY n_live_tup DESC
                LIMIT 20
            """)
            
            results = db.session.execute(table_stats_query).fetchall()
            
            tables = []
            for row in results:
                tables.append({
                    'table_name': row[1],
                    'inserts': row[2],
                    'updates': row[3],
                    'deletes': row[4],
                    'live_tuples': row[5],
                    'dead_tuples': row[6],
                    'last_vacuum': row[7].isoformat() if row[7] else None,
                    'last_autovacuum': row[8].isoformat() if row[8] else None,
                    'last_analyze': row[9].isoformat() if row[9] else None,
                    'last_autoanalyze': row[10].isoformat() if row[10] else None,
                    'dead_tuple_ratio': round((row[6] / row[5]) * 100, 2) if row[5] > 0 else 0
                })
            
            return {
                'tables': tables,
                'total_tables_analyzed': len(tables)
            }
            
        except Exception as e:
            logger.error(f"Table health check error: {e}")
            return {'error': str(e)}

# Database maintenance utilities
class DatabaseMaintenance:
    """Database maintenance and optimization tasks"""
    
    @staticmethod
    def update_table_statistics():
        """Update table statistics for query optimization"""
        from app import db
        
        try:
            # Analyze all tables
            analyze_query = text("ANALYZE")
            db.session.execute(analyze_query)
            db.session.commit()
            
            logger.info("Table statistics updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Statistics update failed: {e}")
            return False
    
    @staticmethod
    def vacuum_tables(full: bool = False):
        """Vacuum database tables to reclaim space"""
        from app import db
        
        try:
            if full:
                vacuum_query = text("VACUUM FULL")
            else:
                vacuum_query = text("VACUUM")
            
            # Note: VACUUM cannot be run inside a transaction block
            db.session.close()
            
            with db.engine.connect() as connection:
                connection.execute(vacuum_query)
            
            logger.info(f"Database vacuum {'FULL' if full else ''} completed")
            return True
            
        except Exception as e:
            logger.error(f"Vacuum failed: {e}")
            return False
    
    @staticmethod
    def reindex_tables(table_names: List[str] = None):
        """Reindex database tables for better performance"""
        from app import db
        
        try:
            if table_names:
                for table_name in table_names:
                    reindex_query = text(f"REINDEX TABLE {table_name}")
                    db.session.execute(reindex_query)
            else:
                # Reindex all tables
                reindex_query = text("REINDEX DATABASE current_database()")
                db.session.execute(reindex_query)
            
            db.session.commit()
            logger.info("Database reindexing completed")
            return True
            
        except Exception as e:
            logger.error(f"Reindexing failed: {e}")
            return False