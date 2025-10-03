# Redis Caching Layer Documentation

## Overview

The Redis caching layer provides high-performance, distributed caching with automatic fallback to in-memory caching when Redis is unavailable. It's designed for production use with connection pooling, TTL support, and comprehensive error handling.

## Features

✅ **Redis-first with Graceful Fallback**
- Automatically connects to Redis if available
- Falls back to in-memory LRU cache if Redis is unavailable
- Transparent operation regardless of backend

✅ **High Performance**
- Connection pooling for efficiency
- Async/await support for non-blocking operations
- Pickle serialization for complex Python objects

✅ **Developer-Friendly**
- Simple decorators: `@cached`, `@cache_invalidate`
- Context manager support
- Type hints throughout

✅ **Production-Ready**
- Comprehensive error handling
- Statistics tracking (hits, misses, hit rate)
- Pattern-based cache invalidation
- TTL (Time-To-Live) support

---

## Quick Start

### 1. Install Dependencies

```bash
pip install redis hiredis
```

### 2. Configure Environment

Add to your `.env` file:

```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
CACHE_DEFAULT_TTL=300  # 5 minutes
```

### 3. Start Redis (Optional)

```bash
# Using Docker
docker run -d -p 6379:6379 redis:alpine

# Or install locally
# macOS: brew install redis && brew services start redis
# Ubuntu: sudo apt install redis-server && sudo systemctl start redis
# Windows: Use WSL or Docker
```

**Note:** Redis is optional! The system will automatically fall back to in-memory caching if Redis is not available.

---

## Usage Examples

### Basic Operations

```python
from src.utils.cache import CacheManager

# Initialize cache
cache = CacheManager()
await cache.connect()

# Set value with 60-second TTL
await cache.set("user:123", {"name": "John"}, ttl=60)

# Get value
user = await cache.get("user:123")

# Delete value
await cache.delete("user:123")

# Check if exists
exists = await cache.exists("user:123")

# Clear pattern
await cache.clear("user:*")

await cache.disconnect()
```

### Decorator-Based Caching

```python
from src.utils.cache import cached, cache_invalidate

# Cache expensive operations
@cached(ttl=300, key_prefix="video")
async def get_video_metadata(video_id: int):
    """This will be cached for 5 minutes."""
    # Expensive database query
    return await db.query(Video).filter(Video.id == video_id).first()

# Automatically invalidate cache on updates
@cache_invalidate(key_prefix="video")
async def update_video(video_id: int, data: dict):
    """This will clear all 'video:*' cache entries."""
    await db.update(Video, video_id, data)
```

### Context Manager

```python
from src.utils.cache import CacheContext

async with CacheContext() as cache:
    await cache.set("key", "value")
    value = await cache.get("key")
```

---

## Real-World Examples

### Example 1: Caching AI Script Generation

```python
from src.utils.cache import cached

@cached(ttl=3600, key_prefix="script")  # Cache for 1 hour
async def generate_script(niche: str, duration: int):
    """Generate video script using AI (expensive operation)."""
    # This expensive AI call will only run once per hour
    # for the same niche/duration combination
    response = await ollama_client.generate(
        prompt=f"Generate a {duration}-second script for {niche}"
    )
    return response.text

# First call - AI generation (~10 seconds)
script = await generate_script("meditation", 600)

# Second call - cached (~0.001 seconds) ⚡
script = await generate_script("meditation", 600)
```

### Example 2: Caching Asset Searches

```python
from src.utils.cache import cached

@cached(ttl=1800, key_prefix="assets")  # Cache for 30 minutes
async def search_assets(query: str, count: int = 5):
    """Search Pexels for video assets (limited API calls)."""
    # External API call - cached to avoid rate limits
    response = await pexels_client.search_videos(query, per_page=count)
    return response.videos

# First call - API request
assets = await search_assets("peaceful nature", 5)

# Subsequent calls - cached (saves API quota)
assets = await search_assets("peaceful nature", 5)
```

### Example 3: User Session Caching

```python
from src.utils.cache import cached, cache_invalidate

@cached(ttl=600, key_prefix="session")
async def get_user_session(session_id: str):
    """Get user session from database."""
    return await db.query(Session).filter(Session.id == session_id).first()

@cache_invalidate(key_prefix="session")
async def logout_user(session_id: str):
    """Logout user and invalidate session cache."""
    await db.delete(Session, session_id)
```

### Example 4: Database Query Caching

```python
from src.utils.cache import cached

@cached(ttl=60, key_prefix="popular_videos")
async def get_popular_videos(limit: int = 10):
    """Get popular videos (expensive aggregation query)."""
    return await db.query(Video).order_by(Video.views.desc()).limit(limit).all()

@cached(ttl=300, key_prefix="video_count")
async def get_total_video_count():
    """Get total video count (cached for 5 minutes)."""
    return await db.query(Video).count()
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_HOST` | `localhost` | Redis server hostname |
| `REDIS_PORT` | `6379` | Redis server port |
| `REDIS_DB` | `0` | Redis database number (0-15) |
| `REDIS_PASSWORD` | - | Redis password (optional) |
| `REDIS_POOL_MAX_CONNECTIONS` | `10` | Max connections in pool |
| `REDIS_POOL_TIMEOUT` | `20` | Connection timeout (seconds) |
| `CACHE_DEFAULT_TTL` | `300` | Default TTL (seconds) |

### Programmatic Configuration

```python
cache = CacheManager()

# Override defaults
cache.redis_host = "cache.example.com"
cache.redis_port = 6380
cache.default_ttl = 600  # 10 minutes

await cache.connect()
```

---

## API Reference

### CacheManager

#### Methods

**`async connect() -> bool`**
- Connect to Redis or initialize fallback cache
- Returns: `True` if Redis connected, `False` if using fallback

**`async disconnect()`**
- Disconnect from Redis

**`async get(key: str, default: Any = None) -> Any`**
- Get value from cache
- Returns cached value or `default` if not found

**`async set(key: str, value: Any, ttl: Optional[int] = None) -> bool`**
- Set value in cache with optional TTL
- Returns: `True` if successful

**`async delete(key: str) -> bool`**
- Delete key from cache
- Returns: `True` if key was deleted

**`async exists(key: str) -> bool`**
- Check if key exists in cache

**`async clear(pattern: str = "*") -> int`**
- Clear cache keys matching pattern
- Returns: Number of keys deleted

**`async get_stats() -> dict`**
- Get cache statistics (hits, misses, hit rate, etc.)

---

## Cache Statistics

```python
cache = CacheManager()
await cache.connect()

# Perform operations...
await cache.set("key1", "value1")
await cache.get("key1")  # Hit
await cache.get("key2")  # Miss

# Get statistics
stats = await cache.get_stats()
print(f"Hit Rate: {stats['hit_rate']:.2%}")
print(f"Total Hits: {stats['hits']}")
print(f"Total Misses: {stats['misses']}")
print(f"Using Redis: {stats['using_redis']}")
```

---

## Best Practices

### 1. **Choose Appropriate TTL Values**

```python
# Short TTL for frequently changing data
@cached(ttl=60)  # 1 minute
async def get_active_users():
    pass

# Medium TTL for semi-static data
@cached(ttl=300)  # 5 minutes
async def get_video_metadata(video_id):
    pass

# Long TTL for rarely changing data
@cached(ttl=3600)  # 1 hour
async def get_platform_config():
    pass
```

### 2. **Use Descriptive Key Prefixes**

```python
@cached(key_prefix="user_profile")
async def get_user_profile(user_id):
    pass

@cached(key_prefix="user_settings")
async def get_user_settings(user_id):
    pass

# Easy to clear all user data
await cache.clear("user_*")
```

### 3. **Invalidate Cache on Updates**

```python
@cache_invalidate(key_prefix="video")
async def update_video(video_id, data):
    """Always invalidate cache when data changes."""
    await db.update(Video, video_id, data)
```

### 4. **Handle Cache Failures Gracefully**

The caching layer automatically handles failures, but you can also implement additional fallbacks:

```python
async def get_critical_data(key):
    """Critical data with multiple fallback layers."""
    # Try cache first
    cached_data = await cache.get(key)
    if cached_data:
        return cached_data
    
    # Try database
    try:
        data = await db.query(...)
        await cache.set(key, data, ttl=300)
        return data
    except Exception as e:
        logger.error(f"Database error: {e}")
        # Return stale cache if available
        return await cache.get(key, default={})
```

### 5. **Monitor Cache Performance**

```python
# Log cache statistics periodically
async def log_cache_stats():
    stats = await cache.get_stats()
    logger.info(f"Cache hit rate: {stats['hit_rate']:.2%}")
    
    if stats['hit_rate'] < 0.5:
        logger.warning("Low cache hit rate - consider adjusting TTL values")
```

---

## Testing

Run the test suite:

```bash
# Run all cache tests
pytest tests/unit/test_cache.py -v

# Run specific test
pytest tests/unit/test_cache.py::test_cached_decorator -v

# Run with coverage
pytest tests/unit/test_cache.py --cov=src.utils.cache
```

---

## Troubleshooting

### Issue: Cache not working

**Solution:** Check if Redis is running or if fallback cache is enabled:

```python
cache = CacheManager()
await cache.connect()
stats = await cache.get_stats()
print(f"Using Redis: {stats['using_redis']}")
```

### Issue: High cache misses

**Possible causes:**
1. TTL too short - increase TTL values
2. Cache keys not matching - check key generation
3. Cache being cleared too frequently

**Solution:** Monitor statistics and adjust TTL:

```python
stats = await cache.get_stats()
if stats['hit_rate'] < 0.5:
    # Increase TTL or investigate key patterns
    pass
```

### Issue: Memory usage growing

**Solution:** 
1. Reduce TTL values
2. Clear old entries periodically
3. Set memory limits in Redis config

```bash
# In redis.conf
maxmemory 256mb
maxmemory-policy allkeys-lru
```

---

## Performance Tips

1. **Use connection pooling** (already configured)
2. **Batch operations** when possible
3. **Cache aggregation results** instead of individual queries
4. **Use appropriate TTL** - longer for static data
5. **Monitor hit rates** - aim for >70% hit rate

---

## Production Deployment

### Docker Compose Setup

```yaml
services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
  
  app:
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - CACHE_DEFAULT_TTL=300

volumes:
  redis-data:
```

### Kubernetes Setup

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cache-config
data:
  REDIS_HOST: "redis-service"
  REDIS_PORT: "6379"
  CACHE_DEFAULT_TTL: "300"
```

---

## Migration from Other Caching Systems

### From Memcached

```python
# Old (Memcached)
memcache_client.set("key", "value", expire=60)
value = memcache_client.get("key")

# New (Redis Cache)
await cache.set("key", "value", ttl=60)
value = await cache.get("key")
```

### From Django Cache

```python
# Old (Django)
from django.core.cache import cache
cache.set("key", "value", 60)

# New (Redis Cache)
from src.utils.cache import cache_manager
await cache_manager.set("key", "value", ttl=60)
```

---

## Related Documentation

- [Redis Documentation](https://redis.io/docs/)
- [Redis Python Client](https://redis-py.readthedocs.io/)
- [Async Python Patterns](https://docs.python.org/3/library/asyncio.html)

---

## Support

For issues or questions:
1. Check this documentation
2. Review example code in `examples/cache_usage.py`
3. Run tests to verify functionality
4. Check application logs for error messages

---

**Last Updated:** October 3, 2025  
**Version:** 1.0  
**Maintainer:** Development Team
