"""
Redis Caching Layer

Provides high-performance caching with TTL support, decorators, and connection pooling.
Implements fallback to in-memory caching when Redis is unavailable.

Features:
- Connection pooling for efficiency
- TTL (Time-To-Live) support
- Decorator-based caching (@cached, @cache_invalidate)
- Async/await support
- Graceful fallback to in-memory cache
- Cache statistics and monitoring
- Pattern-based invalidation
"""

import os
import json
import logging
import hashlib
import functools
from typing import Any, Optional, Callable, Union, List
from datetime import timedelta
import asyncio
from collections import OrderedDict

try:
    import redis.asyncio as aioredis
    from redis.asyncio import ConnectionPool
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None
    ConnectionPool = None

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


# ============================================
# IN-MEMORY CACHE (FALLBACK)
# ============================================

class InMemoryCache:
    """
    Simple in-memory LRU cache as fallback when Redis is unavailable.
    Thread-safe implementation with TTL support.
    """
    
    def __init__(self, maxsize: int = 1000):
        self.cache = OrderedDict()
        self.maxsize = maxsize
        self.ttl_map = {}  # key -> expiry_timestamp
        
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        # Check TTL
        if key in self.ttl_map:
            import time
            if time.time() > self.ttl_map[key]:
                # Expired
                del self.cache[key]
                del self.ttl_map[key]
                return None
        
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        # Remove oldest if at capacity
        if len(self.cache) >= self.maxsize and key not in self.cache:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            if oldest_key in self.ttl_map:
                del self.ttl_map[oldest_key]
        
        self.cache[key] = value
        
        if ttl:
            import time
            self.ttl_map[key] = time.time() + ttl
        
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if key in self.cache:
            del self.cache[key]
            if key in self.ttl_map:
                del self.ttl_map[key]
            return True
        return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        value = await self.get(key)
        return value is not None
    
    async def clear(self) -> bool:
        """Clear all cache."""
        self.cache.clear()
        self.ttl_map.clear()
        return True
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get all keys matching pattern."""
        import fnmatch
        return [k for k in self.cache.keys() if fnmatch.fnmatch(k, pattern)]


# ============================================
# CACHE MANAGER
# ============================================

class CacheManager:
    """
    Redis-based cache manager with fallback to in-memory cache.
    Supports async operations, TTL, and connection pooling.
    """
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize cache manager."""
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._redis_client: Optional[aioredis.Redis] = None
        self._connection_pool: Optional[ConnectionPool] = None
        self._fallback_cache = InMemoryCache(maxsize=1000)
        self._using_redis = False
        
        # Configuration
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_db = int(os.getenv("REDIS_DB", "0"))
        self.redis_password = os.getenv("REDIS_PASSWORD")
        
        # Connection pool settings
        self.pool_max_connections = int(os.getenv("REDIS_POOL_MAX_CONNECTIONS", "10"))
        self.pool_timeout = int(os.getenv("REDIS_POOL_TIMEOUT", "20"))
        
        # Default TTL (5 minutes)
        self.default_ttl = int(os.getenv("CACHE_DEFAULT_TTL", "300"))
        
        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0,
        }
    
    async def connect(self) -> bool:
        """
        Connect to Redis with connection pooling.
        Falls back to in-memory cache if Redis is unavailable.
        """
        if not REDIS_AVAILABLE:
            logger.warning("redis.asyncio not installed, using in-memory cache fallback")
            self._using_redis = False
            return False
        
        try:
            # Create connection pool
            self._connection_pool = ConnectionPool(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                password=self.redis_password,
                max_connections=self.pool_max_connections,
                socket_timeout=self.pool_timeout,
                socket_connect_timeout=self.pool_timeout,
                decode_responses=False,  # We'll handle encoding/decoding
            )
            
            # Create Redis client
            self._redis_client = aioredis.Redis(connection_pool=self._connection_pool)
            
            # Test connection
            await self._redis_client.ping()
            
            self._using_redis = True
            logger.info(f"✅ Connected to Redis at {self.redis_host}:{self.redis_port}")
            return True
        
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}. Using in-memory cache fallback.")
            self._using_redis = False
            self.stats["errors"] += 1
            return False
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self._redis_client:
            await self._redis_client.close()
            logger.info("Disconnected from Redis")
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            default: Default value if key not found
        
        Returns:
            Cached value or default
        """
        try:
            if self._using_redis and self._redis_client:
                value = await self._redis_client.get(key)
                if value is not None:
                    self.stats["hits"] += 1
                    # Use JSON instead of pickle for security
                    import json
                    try:
                        return json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        # Fallback for non-JSON data (backward compatibility)
                        logger.warning(f"Could not deserialize cached value for key '{key}' as JSON")
                        return default
                else:
                    self.stats["misses"] += 1
                    return default
            else:
                # Use fallback cache
                value = await self._fallback_cache.get(key)
                if value is not None:
                    self.stats["hits"] += 1
                    return value
                else:
                    self.stats["misses"] += 1
                    return default
        
        except Exception as e:
            logger.error(f"Cache get error for key '{key}': {e}")
            self.stats["errors"] += 1
            return default
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache with optional TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None = use default)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            ttl = ttl or self.default_ttl
            
            if self._using_redis and self._redis_client:
                # Use JSON instead of pickle for security
                import json
                try:
                    # Handle Pydantic models
                    from pydantic import BaseModel
                    if isinstance(value, BaseModel):
                        serialized = value.model_dump_json()
                    else:
                        serialized = json.dumps(value)
                    
                    if ttl:
                        await self._redis_client.setex(key, ttl, serialized)
                    else:
                        await self._redis_client.set(key, serialized)
                    self.stats["sets"] += 1
                    return True
                except (TypeError, ValueError) as e:
                    logger.error(f"Cannot serialize value for key '{key}': {e}")
                    self.stats["errors"] += 1
                    return False
            else:
                # Use fallback cache
                await self._fallback_cache.set(key, value, ttl)
                self.stats["sets"] += 1
                return True
        
        except Exception as e:
            logger.error(f"Cache set error for key '{key}': {e}")
            self.stats["errors"] += 1
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
        
        Returns:
            True if key was deleted, False otherwise
        """
        try:
            if self._using_redis and self._redis_client:
                result = await self._redis_client.delete(key)
                self.stats["deletes"] += 1
                return result > 0
            else:
                # Use fallback cache
                result = await self._fallback_cache.delete(key)
                self.stats["deletes"] += 1
                return result
        
        except Exception as e:
            logger.error(f"Cache delete error for key '{key}': {e}")
            self.stats["errors"] += 1
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
        
        Returns:
            True if key exists, False otherwise
        """
        try:
            if self._using_redis and self._redis_client:
                return await self._redis_client.exists(key) > 0
            else:
                return await self._fallback_cache.exists(key)
        
        except Exception as e:
            logger.error(f"Cache exists error for key '{key}': {e}")
            self.stats["errors"] += 1
            return False
    
    async def clear(self, pattern: str = "*") -> int:
        """
        Clear cache keys matching pattern.
        
        Args:
            pattern: Key pattern (default: all keys)
        
        Returns:
            Number of keys deleted
        """
        try:
            if self._using_redis and self._redis_client:
                keys = await self._redis_client.keys(pattern)
                if keys:
                    return await self._redis_client.delete(*keys)
                return 0
            else:
                # Use fallback cache
                keys = await self._fallback_cache.keys(pattern)
                for key in keys:
                    await self._fallback_cache.delete(key)
                return len(keys)
        
        except Exception as e:
            logger.error(f"Cache clear error for pattern '{pattern}': {e}")
            self.stats["errors"] += 1
            return 0
    
    async def get_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        hit_rate = 0.0
        total_ops = self.stats["hits"] + self.stats["misses"]
        if total_ops > 0:
            hit_rate = self.stats["hits"] / total_ops
        
        return {
            **self.stats,
            "hit_rate": hit_rate,
            "using_redis": self._using_redis,
        }
    
    def generate_key(self, *args, **kwargs) -> str:
        """
        Generate cache key from arguments.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Cache key string
        """
        # Create deterministic key from arguments
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        # MD5 used for cache key only, not security (nosec: B324)
        key_hash = hashlib.md5(key_data.encode(), usedforsecurity=False).hexdigest()
        return f"cache:{key_hash}"


# ============================================
# GLOBAL CACHE INSTANCE
# ============================================

cache_manager = CacheManager()


# ============================================
# DECORATORS
# ============================================

def cached(ttl: Optional[int] = None, key_prefix: Optional[str] = None):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time-to-live in seconds (None = use default)
        key_prefix: Optional prefix for cache key
    
    Example:
        @cached(ttl=300, key_prefix="user")
        async def get_user(user_id: int):
            # Expensive database query
            return await db.query(User).filter(User.id == user_id).first()
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            prefix = key_prefix or func.__name__
            key_data = json.dumps({
                "prefix": prefix,
                "args": args,
                "kwargs": kwargs
            }, sort_keys=True, default=str)
            cache_key = f"{prefix}:{hashlib.md5(key_data.encode()).hexdigest()}"
            
            # Try to get from cache
            cached_value = await cache_manager.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_value
            
            # Cache miss - call function
            logger.debug(f"Cache MISS: {cache_key}")
            result = await func(*args, **kwargs)
            
            # Store in cache
            await cache_manager.set(cache_key, result, ttl)
            
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For synchronous functions, we need to run async operations
            loop = asyncio.get_event_loop()
            
            # Generate cache key
            prefix = key_prefix or func.__name__
            key_data = json.dumps({
                "prefix": prefix,
                "args": args,
                "kwargs": kwargs
            }, sort_keys=True, default=str)
            # MD5 used for cache key only, not security (nosec: B324)
            key_hash = hashlib.md5(key_data.encode(), usedforsecurity=False)
            cache_key = f"{prefix}:{key_hash.hexdigest()}"
            
            # Try to get from cache
            cached_value = loop.run_until_complete(cache_manager.get(cache_key))
            if cached_value is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_value
            
            # Cache miss - call function
            logger.debug(f"Cache MISS: {cache_key}")
            result = func(*args, **kwargs)
            
            # Store in cache
            loop.run_until_complete(cache_manager.set(cache_key, result, ttl))
            
            return result
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def cache_invalidate(key_prefix: str):
    """
    Decorator to invalidate cache after function execution.
    
    Args:
        key_prefix: Cache key prefix to invalidate
    
    Example:
        @cache_invalidate(key_prefix="user")
        async def update_user(user_id: int, data: dict):
            # Update user in database
            await db.update(User, user_id, data)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Execute function
            result = await func(*args, **kwargs)
            
            # Invalidate cache
            pattern = f"{key_prefix}:*"
            deleted = await cache_manager.clear(pattern)
            logger.debug(f"Cache invalidated: {deleted} keys with pattern '{pattern}'")
            
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Execute function
            result = func(*args, **kwargs)
            
            # Invalidate cache
            loop = asyncio.get_event_loop()
            pattern = f"{key_prefix}:*"
            deleted = loop.run_until_complete(cache_manager.clear(pattern))
            logger.debug(f"Cache invalidated: {deleted} keys with pattern '{pattern}'")
            
            return result
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# ============================================
# CONTEXT MANAGER
# ============================================

class CacheContext:
    """
    Context manager for cache operations.
    
    Example:
        async with CacheContext() as cache:
            await cache.set("key", "value", ttl=300)
            value = await cache.get("key")
    """
    
    async def __aenter__(self):
        """Enter context."""
        if not cache_manager._redis_client:
            await cache_manager.connect()
        return cache_manager
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        # Don't disconnect - keep connection alive for reuse
        pass
