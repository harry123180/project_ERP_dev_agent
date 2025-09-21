# Redis Cache Management System
# Multi-layer caching strategy with intelligent invalidation

import json
import time
import redis
import logging
from functools import wraps
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RedisCacheManager:
    """Advanced Redis cache management with multi-layer strategy"""
    
    def __init__(self, redis_url: str, default_ttl: int = 3600):
        """
        Initialize Redis cache manager
        
        Args:
            redis_url: Redis connection URL
            default_ttl: Default time-to-live in seconds
        """
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.default_ttl = default_ttl
        self.local_cache = {}  # Application-level cache
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }
        
        # Cache key prefixes for different data types
        self.key_prefixes = {
            'user': 'user:',
            'supplier': 'supplier:',
            'requisition': 'req:',
            'purchase_order': 'po:',
            'session': 'session:',
            'permissions': 'perm:',
            'settings': 'settings:',
            'dashboard': 'dashboard:'
        }
    
    def get(self, key: str, fetch_func=None, ttl: Optional[int] = None) -> Any:
        """
        Get data with multi-layer fallback strategy
        
        Args:
            key: Cache key
            fetch_func: Function to fetch data if not in cache
            ttl: Time-to-live override
            
        Returns:
            Cached data or fetched data
        """
        # L1: Application cache (fastest)
        if key in self.local_cache:
            cache_data = self.local_cache[key]
            if not self._is_expired(cache_data):
                self.cache_stats['hits'] += 1
                logger.debug(f"L1 cache hit for key: {key}")
                return cache_data['data']
            else:
                # Remove expired data from local cache
                del self.local_cache[key]
        
        # L2: Redis cache (distributed)
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                data = json.loads(cached_data)
                # Store in local cache for faster access
                self._store_local(key, data, ttl or self.default_ttl)
                self.cache_stats['hits'] += 1
                logger.debug(f"L2 cache hit for key: {key}")
                return data
        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Redis cache error for key {key}: {e}")
        
        # L3: Fetch from source
        if fetch_func:
            try:
                data = fetch_func()
                self.set(key, data, ttl)
                self.cache_stats['misses'] += 1
                logger.debug(f"Cache miss, fetched data for key: {key}")
                return data
            except Exception as e:
                logger.error(f"Failed to fetch data for key {key}: {e}")
                raise
        
        self.cache_stats['misses'] += 1
        return None
    
    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> bool:
        """
        Store data in both Redis and local cache
        
        Args:
            key: Cache key
            data: Data to cache
            ttl: Time-to-live in seconds
            
        Returns:
            Success status
        """
        ttl = ttl or self.default_ttl
        
        try:
            # Store in Redis
            serialized_data = json.dumps(data, default=str)
            self.redis_client.setex(key, ttl, serialized_data)
            
            # Store in local cache
            self._store_local(key, data, ttl)
            
            self.cache_stats['sets'] += 1
            logger.debug(f"Cached data for key: {key} with TTL: {ttl}")
            return True
            
        except (redis.RedisError, TypeError) as e:
            logger.error(f"Failed to cache data for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete data from both caches
        
        Args:
            key: Cache key
            
        Returns:
            Success status
        """
        try:
            # Delete from Redis
            self.redis_client.delete(key)
            
            # Delete from local cache
            if key in self.local_cache:
                del self.local_cache[key]
            
            self.cache_stats['deletes'] += 1
            logger.debug(f"Deleted cache for key: {key}")
            return True
            
        except redis.RedisError as e:
            logger.error(f"Failed to delete cache for key {key}: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate multiple keys matching pattern
        
        Args:
            pattern: Key pattern (e.g., 'user:*', 'req:*')
            
        Returns:
            Number of keys deleted
        """
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                # Delete from Redis
                deleted_count = self.redis_client.delete(*keys)
                
                # Delete from local cache
                local_deleted = 0
                for key in list(self.local_cache.keys()):
                    if self._matches_pattern(key, pattern):
                        del self.local_cache[key]
                        local_deleted += 1
                
                logger.info(f"Invalidated {deleted_count} Redis keys and {local_deleted} local keys for pattern: {pattern}")
                return deleted_count
            
            return 0
            
        except redis.RedisError as e:
            logger.error(f"Failed to invalidate pattern {pattern}: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        redis_info = {}
        try:
            redis_info = self.redis_client.info('memory')
        except redis.RedisError:
            pass
        
        return {
            'cache_stats': self.cache_stats,
            'hit_rate': round(hit_rate, 2),
            'local_cache_size': len(self.local_cache),
            'redis_info': redis_info
        }
    
    def _store_local(self, key: str, data: Any, ttl: int):
        """Store data in local cache with expiration"""
        # Limit local cache size
        if len(self.local_cache) >= 1000:
            # Remove oldest entries
            sorted_items = sorted(
                self.local_cache.items(),
                key=lambda x: x[1]['timestamp']
            )
            for old_key, _ in sorted_items[:100]:  # Remove 100 oldest
                del self.local_cache[old_key]
        
        self.local_cache[key] = {
            'data': data,
            'timestamp': time.time(),
            'ttl': ttl
        }
    
    def _is_expired(self, cache_data: Dict) -> bool:
        """Check if local cache data is expired"""
        return time.time() > (cache_data['timestamp'] + cache_data['ttl'])
    
    def _matches_pattern(self, key: str, pattern: str) -> bool:
        """Check if key matches pattern"""
        if pattern.endswith('*'):
            return key.startswith(pattern[:-1])
        return key == pattern


class CacheDecorator:
    """Decorator for automatic caching of function results"""
    
    def __init__(self, cache_manager: RedisCacheManager):
        self.cache_manager = cache_manager
    
    def cache_result(self, key_template: str, ttl: int = 3600, key_args: List[str] = None):
        """
        Decorator to cache function results
        
        Args:
            key_template: Template for cache key (e.g., 'user:{user_id}')
            ttl: Time-to-live in seconds
            key_args: List of argument names to use in key formatting
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Build cache key
                if key_args:
                    key_values = {}
                    # Get values from kwargs
                    for arg_name in key_args:
                        if arg_name in kwargs:
                            key_values[arg_name] = kwargs[arg_name]
                    
                    # Get values from args if function has them
                    if hasattr(func, '__code__'):
                        arg_names = func.__code__.co_varnames[:func.__code__.co_argcount]
                        for i, arg_name in enumerate(arg_names):
                            if arg_name in key_args and i < len(args):
                                key_values[arg_name] = args[i]
                    
                    cache_key = key_template.format(**key_values)
                else:
                    # Use function name and hash of arguments
                    args_hash = hash(str(args) + str(sorted(kwargs.items())))
                    cache_key = f"{func.__name__}:{args_hash}"
                
                # Try to get from cache
                def fetch_data():
                    return func(*args, **kwargs)
                
                result = self.cache_manager.get(cache_key, fetch_data, ttl)
                return result
            
            return wrapper
        return decorator


class BusinessCacheManager:
    """Business-specific cache management"""
    
    def __init__(self, cache_manager: RedisCacheManager):
        self.cache_manager = cache_manager
        self.decorator = CacheDecorator(cache_manager)
    
    @property
    def cache_user_data(self):
        """Cache user data"""
        return self.decorator.cache_result('user:{user_id}', ttl=1800, key_args=['user_id'])
    
    @property
    def cache_supplier_data(self):
        """Cache supplier data"""
        return self.decorator.cache_result('supplier:{supplier_id}', ttl=3600, key_args=['supplier_id'])
    
    @property
    def cache_permissions(self):
        """Cache user permissions"""
        return self.decorator.cache_result('perm:{user_id}', ttl=1800, key_args=['user_id'])
    
    def invalidate_user_cache(self, user_id: int):
        """Invalidate all cache related to a user"""
        patterns = [
            f'user:{user_id}',
            f'perm:{user_id}',
            f'session:*:{user_id}'
        ]
        for pattern in patterns:
            self.cache_manager.invalidate_pattern(pattern)
    
    def invalidate_supplier_cache(self, supplier_id: str = None):
        """Invalidate supplier cache"""
        if supplier_id:
            self.cache_manager.delete(f'supplier:{supplier_id}')
        else:
            self.cache_manager.invalidate_pattern('supplier:*')
    
    def warm_up_cache(self):
        """Pre-warm cache with frequently accessed data"""
        try:
            # This would be called on application startup
            logger.info("Starting cache warm-up process")
            
            # Warm up active suppliers
            self._warm_up_suppliers()
            
            # Warm up system settings
            self._warm_up_settings()
            
            # Warm up user permissions for recent users
            self._warm_up_user_permissions()
            
            logger.info("Cache warm-up completed")
            
        except Exception as e:
            logger.error(f"Cache warm-up failed: {e}")
    
    def _warm_up_suppliers(self):
        """Pre-load active suppliers into cache"""
        # This would fetch active suppliers and cache them
        # Implementation depends on your data access layer
        pass
    
    def _warm_up_settings(self):
        """Pre-load system settings into cache"""
        # This would fetch system settings and cache them
        pass
    
    def _warm_up_user_permissions(self):
        """Pre-load permissions for recently active users"""
        # This would fetch and cache permissions for active users
        pass


# Global cache manager instance
cache_manager = None
business_cache = None

def init_cache_manager(redis_url: str):
    """Initialize global cache manager"""
    global cache_manager, business_cache
    cache_manager = RedisCacheManager(redis_url)
    business_cache = BusinessCacheManager(cache_manager)
    return cache_manager, business_cache


# Example usage decorators
def cached_user_data(ttl: int = 1800):
    """Decorator for caching user data"""
    if business_cache:
        return business_cache.cache_user_data
    return lambda func: func


def cached_supplier_data(ttl: int = 3600):
    """Decorator for caching supplier data"""
    if business_cache:
        return business_cache.cache_supplier_data
    return lambda func: func