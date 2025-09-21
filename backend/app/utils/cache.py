"""
Redis Caching Layer Implementation
High-performance caching for ERP system with intelligent cache strategies
Architecture Lead: Winston
"""

import redis
import json
import logging
from functools import wraps
from typing import Any, Optional, Union, Dict, List
from datetime import datetime, timedelta
from flask import current_app
import pickle
import hashlib

logger = logging.getLogger(__name__)

class CacheManager:
    """Advanced Redis cache manager with multiple strategies"""
    
    def __init__(self, redis_url: str = None):
        # Default to local Redis if no URL provided and no app context
        try:
            self.redis_url = redis_url or current_app.config.get('REDIS_URL', 'redis://localhost:6379/0')
        except RuntimeError:
            # Working outside of application context
            self.redis_url = redis_url or 'redis://localhost:6379/0'
        
        self.redis_client = None
        self.default_timeout = 300  # 5 minutes
        self.connect()
    
    def connect(self):
        """Establish Redis connection with retry logic"""
        try:
            self.redis_client = redis.Redis.from_url(
                self.redis_url,
                decode_responses=False,  # Handle binary data
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache connection established successfully")
            
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.redis_client = None
    
    def is_available(self) -> bool:
        """Check if Redis is available"""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.ping()
            return True
        except:
            return False
    
    def _serialize(self, data: Any) -> bytes:
        """Serialize data for storage"""
        try:
            # Use pickle for complex objects, JSON for simple ones
            if isinstance(data, (dict, list, str, int, float, bool)) or data is None:
                return json.dumps(data, default=str).encode('utf-8')
            else:
                return pickle.dumps(data)
        except Exception as e:
            logger.error(f"Serialization error: {e}")
            return pickle.dumps(data)
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize data from storage"""
        try:
            # Try JSON first (most common)
            return json.loads(data.decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError):
            try:
                # Fall back to pickle
                return pickle.loads(data)
            except Exception as e:
                logger.error(f"Deserialization error: {e}")
                return None
    
    def _generate_key(self, namespace: str, key: str) -> str:
        """Generate cache key with namespace"""
        return f"erp:{namespace}:{key}"
    
    def get(self, namespace: str, key: str) -> Any:
        """Get value from cache"""
        if not self.is_available():
            return None
        
        try:
            cache_key = self._generate_key(namespace, key)
            data = self.redis_client.get(cache_key)
            
            if data is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return self._deserialize(data)
            else:
                logger.debug(f"Cache miss: {cache_key}")
                return None
                
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, namespace: str, key: str, value: Any, timeout: int = None) -> bool:
        """Set value in cache"""
        if not self.is_available():
            return False
        
        try:
            cache_key = self._generate_key(namespace, key)
            serialized_data = self._serialize(value)
            timeout = timeout or self.default_timeout
            
            result = self.redis_client.setex(cache_key, timeout, serialized_data)
            
            if result:
                logger.debug(f"Cache set: {cache_key} (TTL: {timeout}s)")
                return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
        
        return False
    
    def delete(self, namespace: str, key: str) -> bool:
        """Delete specific key from cache"""
        if not self.is_available():
            return False
        
        try:
            cache_key = self._generate_key(namespace, key)
            result = self.redis_client.delete(cache_key)
            
            if result:
                logger.debug(f"Cache delete: {cache_key}")
                return True
                
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
        
        return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate multiple keys matching pattern"""
        if not self.is_available():
            return 0
        
        try:
            keys = self.redis_client.keys(f"erp:{pattern}")
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Cache invalidation: {deleted} keys deleted for pattern {pattern}")
                return deleted
                
        except Exception as e:
            logger.error(f"Cache pattern invalidation error: {e}")
        
        return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.is_available():
            return {'available': False}
        
        try:
            info = self.redis_client.info()
            
            return {
                'available': True,
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory_human', '0B'),
                'used_memory_peak': info.get('used_memory_peak_human', '0B'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': self._calculate_hit_rate(info),
                'total_keys': self._count_erp_keys()
            }
            
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {'available': False, 'error': str(e)}
    
    def _calculate_hit_rate(self, info: Dict) -> float:
        """Calculate cache hit rate percentage"""
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        total = hits + misses
        
        if total == 0:
            return 0.0
        
        return round((hits / total) * 100, 2)
    
    def _count_erp_keys(self) -> int:
        """Count ERP-related keys"""
        try:
            keys = self.redis_client.keys('erp:*')
            return len(keys)
        except:
            return 0

# Global cache manager instance
cache_manager = CacheManager()

# Cache configuration for different data types
CACHE_CONFIGS = {
    'default': {
        'timeout': 300,  # 5 minutes
        'key_prefix': 'default'
    },
    'master_data': {
        'timeout': 3600,  # 1 hour
        'key_prefix': 'master'
    },
    'user_session': {
        'timeout': 1800,  # 30 minutes
        'key_prefix': 'session'
    },
    'query_results': {
        'timeout': 600,  # 10 minutes
        'key_prefix': 'query'
    },
    'dashboard_stats': {
        'timeout': 180,  # 3 minutes
        'key_prefix': 'stats'
    },
    'projects': {
        'timeout': 900,  # 15 minutes
        'key_prefix': 'projects'
    },
    'storage': {
        'timeout': 600,  # 10 minutes
        'key_prefix': 'storage'
    },
    'suppliers': {
        'timeout': 1800,  # 30 minutes
        'key_prefix': 'suppliers'
    }
}

def cache_result(cache_type: str = 'default', key_func: callable = None, timeout: int = None):
    """
    Decorator for caching function results
    
    Args:
        cache_type: Type of cache configuration to use
        key_func: Function to generate cache key (receives function args)
        timeout: Override default timeout
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            config = CACHE_CONFIGS.get(cache_type, CACHE_CONFIGS['default'])
            
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [
                    func.__name__,
                    hashlib.md5(str(args).encode() + str(kwargs).encode()).hexdigest()[:8]
                ]
                cache_key = ':'.join(key_parts)
            
            namespace = config['key_prefix']
            
            # Try to get from cache first
            cached_result = cache_manager.get(namespace, cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            
            # Cache the result
            cache_timeout = timeout or config['timeout']
            cache_manager.set(namespace, cache_key, result, cache_timeout)
            
            return result
        
        return wrapper
    return decorator

def invalidate_cache(pattern: str):
    """Invalidate cache entries matching pattern"""
    return cache_manager.invalidate_pattern(pattern)

def cache_set(namespace: str, key: str, value: Any, timeout: int = None):
    """Set cache value directly"""
    return cache_manager.set(namespace, key, value, timeout)

def cache_get(namespace: str, key: str):
    """Get cache value directly"""
    return cache_manager.get(namespace, key)

def cache_delete(namespace: str, key: str):
    """Delete cache value directly"""
    return cache_manager.delete(namespace, key)

# Specific cache helpers for common ERP operations
class ERPCache:
    """ERP-specific cache operations"""
    
    @staticmethod
    def cache_user_session(user_id: int, session_data: Dict, timeout: int = 1800):
        """Cache user session data"""
        return cache_set('user_session', f'user:{user_id}', session_data, timeout)
    
    @staticmethod
    def get_user_session(user_id: int) -> Optional[Dict]:
        """Get cached user session"""
        return cache_get('user_session', f'user:{user_id}')
    
    @staticmethod
    def cache_dashboard_stats(stats: Dict, timeout: int = 180):
        """Cache dashboard statistics"""
        return cache_set('dashboard_stats', 'main', stats, timeout)
    
    @staticmethod
    def get_dashboard_stats() -> Optional[Dict]:
        """Get cached dashboard stats"""
        return cache_get('dashboard_stats', 'main')
    
    @staticmethod
    def cache_supplier_list(suppliers: List[Dict], timeout: int = 1800):
        """Cache supplier list"""
        return cache_set('suppliers', 'list:all', suppliers, timeout)
    
    @staticmethod
    def get_supplier_list() -> Optional[List[Dict]]:
        """Get cached supplier list"""
        return cache_get('suppliers', 'list:all')
    
    @staticmethod
    def cache_storage_tree(tree: Dict, timeout: int = 600):
        """Cache storage hierarchy tree"""
        return cache_set('storage', 'tree:hierarchy', tree, timeout)
    
    @staticmethod
    def get_storage_tree() -> Optional[Dict]:
        """Get cached storage tree"""
        return cache_get('storage', 'tree:hierarchy')
    
    @staticmethod
    def invalidate_project_cache(project_id: int = None):
        """Invalidate project-related cache"""
        if project_id:
            invalidate_cache(f'projects:*:{project_id}')
        else:
            invalidate_cache('projects:*')
    
    @staticmethod
    def invalidate_storage_cache():
        """Invalidate storage-related cache"""
        invalidate_cache('storage:*')
    
    @staticmethod
    def invalidate_supplier_cache():
        """Invalidate supplier-related cache"""
        invalidate_cache('suppliers:*')

# Cache warming functions
def warm_cache():
    """Warm up cache with frequently accessed data"""
    logger.info("Starting cache warming process")
    
    try:
        from app.models import Supplier, User, SystemSettings
        
        # Warm supplier cache
        suppliers = Supplier.query.filter_by(is_active=True).all()
        supplier_data = [
            {
                'id': s.id,
                'supplier_id': s.supplier_id,
                'supplier_name_zh': s.supplier_name_zh,
                'supplier_region': s.supplier_region
            }
            for s in suppliers
        ]
        ERPCache.cache_supplier_list(supplier_data)
        
        # Warm system settings cache
        settings = SystemSettings.query.all()
        settings_data = {
            setting.setting_key: setting.setting_value 
            for setting in settings
        }
        cache_set('master_data', 'system_settings', settings_data, 3600)
        
        logger.info("Cache warming completed successfully")
        
    except Exception as e:
        logger.error(f"Cache warming error: {e}")

def get_cache_health() -> Dict[str, Any]:
    """Get comprehensive cache health information"""
    stats = cache_manager.get_stats()
    
    # Add custom ERP cache metrics
    stats.update({
        'timestamp': datetime.utcnow().isoformat(),
        'cache_configs': list(CACHE_CONFIGS.keys()),
        'warming_status': 'enabled' if cache_manager.is_available() else 'disabled'
    })
    
    return stats

# Background cache maintenance
class CacheMaintenance:
    """Background cache maintenance operations"""
    
    @staticmethod
    def cleanup_expired():
        """Clean up expired cache entries (Redis handles this automatically)"""
        pass
    
    @staticmethod
    def refresh_master_data():
        """Refresh master data cache"""
        try:
            from app.models import Supplier, SystemSettings, ItemCategory
            
            # Refresh suppliers
            suppliers = Supplier.query.filter_by(is_active=True).all()
            supplier_data = [
                {
                    'id': s.id,
                    'supplier_id': s.supplier_id,
                    'supplier_name_zh': s.supplier_name_zh,
                    'supplier_region': s.supplier_region
                }
                for s in suppliers
            ]
            ERPCache.cache_supplier_list(supplier_data, timeout=1800)
            
            # Refresh system settings
            settings = SystemSettings.query.all()
            settings_data = {
                setting.setting_key: setting.setting_value 
                for setting in settings
            }
            cache_set('master_data', 'system_settings', settings_data, timeout=3600)
            
            logger.info("Master data cache refreshed")
            
        except Exception as e:
            logger.error(f"Master data cache refresh error: {e}")
    
    @staticmethod
    def generate_cache_report() -> Dict[str, Any]:
        """Generate detailed cache usage report"""
        stats = get_cache_health()
        
        # Add usage patterns
        report = {
            'overall_health': stats,
            'cache_types': {},
            'recommendations': []
        }
        
        # Analyze cache types
        for cache_type, config in CACHE_CONFIGS.items():
            try:
                keys = cache_manager.redis_client.keys(f'erp:{config["key_prefix"]}:*')
                report['cache_types'][cache_type] = {
                    'key_count': len(keys),
                    'timeout': config['timeout']
                }
            except:
                report['cache_types'][cache_type] = {
                    'key_count': 0,
                    'timeout': config['timeout']
                }
        
        # Generate recommendations
        if stats.get('hit_rate', 0) < 80:
            report['recommendations'].append('Consider increasing cache timeouts for frequently accessed data')
        
        if stats.get('used_memory_peak', '0').replace('M', '').replace('K', '').replace('B', '').isdigit():
            memory_mb = float(stats.get('used_memory_peak', '0M').replace('M', '').replace('K', '').replace('B', ''))
            if memory_mb > 100:
                report['recommendations'].append('Monitor Redis memory usage - consider increasing memory limit')
        
        return report