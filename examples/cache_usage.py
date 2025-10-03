"""
Redis Caching Layer - Usage Examples

Demonstrates various ways to use the caching layer in the application.
"""

import asyncio
import time
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.cache import CacheManager, cached, cache_invalidate, CacheContext


# ============================================
# EXAMPLE 1: BASIC CACHE OPERATIONS
# ============================================

async def example_basic_operations():
    """Basic cache set/get/delete operations."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Cache Operations")
    print("="*60)
    
    # Initialize cache
    cache = CacheManager()
    await cache.connect()
    
    # Set value with 60-second TTL
    await cache.set("user:123", {"name": "John", "age": 30}, ttl=60)
    print("✅ Set user:123")
    
    # Get value
    user = await cache.get("user:123")
    print(f"📥 Retrieved: {user}")
    
    # Check if exists
    exists = await cache.exists("user:123")
    print(f"🔍 Exists: {exists}")
    
    # Delete
    await cache.delete("user:123")
    print("🗑️  Deleted user:123")
    
    await cache.disconnect()


# ============================================
# EXAMPLE 2: DECORATOR-BASED CACHING
# ============================================

async def example_decorator_caching():
    """Using @cached decorator for automatic caching."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Decorator-Based Caching")
    print("="*60)
    
    # Initialize cache
    cache = CacheManager()
    await cache.connect()
    
    @cached(ttl=300, key_prefix="video")
    async def get_video_metadata(video_id: int):
        """Expensive database query (simulated)."""
        print(f"  🔄 Fetching video {video_id} from database...")
        await asyncio.sleep(0.5)  # Simulate slow query
        return {
            "id": video_id,
            "title": f"Video {video_id}",
            "duration": 600,
            "views": 1000,
        }
    
    # First call - will hit database
    print("\n🔵 First call (cache miss):")
    start = time.time()
    video1 = await get_video_metadata(123)
    duration1 = time.time() - start
    print(f"  Result: {video1}")
    print(f"  ⏱️  Time: {duration1:.3f}s")
    
    # Second call - will use cache
    print("\n🟢 Second call (cache hit):")
    start = time.time()
    video2 = await get_video_metadata(123)
    duration2 = time.time() - start
    print(f"  Result: {video2}")
    print(f"  ⏱️  Time: {duration2:.3f}s")
    print(f"  🚀 Speedup: {duration1/duration2:.1f}x faster!")
    
    await cache.disconnect()


# ============================================
# EXAMPLE 3: CACHE INVALIDATION
# ============================================

async def example_cache_invalidation():
    """Using @cache_invalidate to clear cache on updates."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Cache Invalidation")
    print("="*60)
    
    # Initialize cache
    cache = CacheManager()
    await cache.connect()
    
    # Simulated database
    fake_db = {"user:1": {"id": 1, "name": "Alice", "email": "alice@example.com"}}
    
    @cached(ttl=300, key_prefix="user")
    async def get_user(user_id: int):
        """Get user from database."""
        print(f"  🔄 Fetching user {user_id} from database...")
        await asyncio.sleep(0.1)
        return fake_db.get(f"user:{user_id}")
    
    @cache_invalidate(key_prefix="user")
    async def update_user(user_id: int, **updates):
        """Update user and invalidate cache."""
        print(f"  💾 Updating user {user_id} in database...")
        key = f"user:{user_id}"
        if key in fake_db:
            fake_db[key].update(updates)
        return fake_db[key]
    
    # Get user (cache miss)
    print("\n1️⃣ Initial fetch:")
    user = await get_user(1)
    print(f"   User: {user}")
    
    # Get user again (cache hit)
    print("\n2️⃣ Second fetch (cached):")
    user = await get_user(1)
    print(f"   User: {user}")
    
    # Update user (invalidates cache)
    print("\n3️⃣ Update user:")
    await update_user(1, name="Alice Updated")
    print("   ✅ Cache invalidated")
    
    # Get user again (cache miss - refetch from DB)
    print("\n4️⃣ Fetch after update:")
    user = await get_user(1)
    print(f"   User: {user}")
    
    await cache.disconnect()


# ============================================
# EXAMPLE 4: CONTEXT MANAGER
# ============================================

async def example_context_manager():
    """Using cache context manager."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Context Manager")
    print("="*60)
    
    async with CacheContext() as cache:
        # Set multiple values
        await cache.set("config:api_key", "sk-secret-key", ttl=3600)
        await cache.set("config:max_retries", 3, ttl=3600)
        await cache.set("config:timeout", 30, ttl=3600)
        print("✅ Set configuration values")
        
        # Get values
        api_key = await cache.get("config:api_key")
        max_retries = await cache.get("config:max_retries")
        timeout = await cache.get("config:timeout")
        
        print(f"📥 API Key: {api_key}")
        print(f"📥 Max Retries: {max_retries}")
        print(f"📥 Timeout: {timeout}s")


# ============================================
# EXAMPLE 5: PATTERN-BASED OPERATIONS
# ============================================

async def example_pattern_operations():
    """Pattern-based cache operations."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Pattern-Based Operations")
    print("="*60)
    
    cache = CacheManager()
    await cache.connect()
    
    # Set multiple related keys
    await cache.set("user:1:profile", {"name": "Alice"})
    await cache.set("user:1:settings", {"theme": "dark"})
    await cache.set("user:1:preferences", {"lang": "en"})
    await cache.set("user:2:profile", {"name": "Bob"})
    await cache.set("post:1", {"title": "Hello"})
    print("✅ Set multiple keys")
    
    # Clear all user:1 keys
    print("\n🗑️  Clearing user:1 keys...")
    deleted = await cache.clear("user:1:*")
    print(f"   Deleted {deleted} keys")
    
    # Verify user:1 keys are gone
    profile = await cache.get("user:1:profile")
    print(f"   user:1:profile: {profile}")  # Should be None
    
    # Verify user:2 and post keys remain
    user2 = await cache.get("user:2:profile")
    post = await cache.get("post:1")
    print(f"   user:2:profile: {user2}")  # Should exist
    print(f"   post:1: {post}")  # Should exist
    
    await cache.disconnect()


# ============================================
# EXAMPLE 6: CACHE STATISTICS
# ============================================

async def example_cache_statistics():
    """Monitoring cache performance."""
    print("\n" + "="*60)
    print("EXAMPLE 6: Cache Statistics")
    print("="*60)
    
    cache = CacheManager()
    await cache.connect()
    
    # Reset stats
    cache.stats = {
        "hits": 0,
        "misses": 0,
        "sets": 0,
        "deletes": 0,
        "errors": 0,
    }
    
    # Perform operations
    await cache.set("key1", "value1")
    await cache.set("key2", "value2")
    
    await cache.get("key1")  # Hit
    await cache.get("key1")  # Hit
    await cache.get("key3")  # Miss
    
    await cache.delete("key1")
    
    # Get statistics
    stats = await cache.get_stats()
    
    print("\n📊 Cache Statistics:")
    print(f"   Hits: {stats['hits']}")
    print(f"   Misses: {stats['misses']}")
    print(f"   Sets: {stats['sets']}")
    print(f"   Deletes: {stats['deletes']}")
    print(f"   Errors: {stats['errors']}")
    print(f"   Hit Rate: {stats['hit_rate']:.2%}")
    print(f"   Using Redis: {stats['using_redis']}")
    
    await cache.disconnect()


# ============================================
# EXAMPLE 7: REAL-WORLD SCENARIO
# ============================================

async def example_real_world_video_generation():
    """Real-world scenario: Video generation pipeline."""
    print("\n" + "="*60)
    print("EXAMPLE 7: Real-World Video Generation")
    print("="*60)
    
    cache = CacheManager()
    await cache.connect()
    
    # Cache expensive AI script generation
    @cached(ttl=3600, key_prefix="script")
    async def generate_script(niche: str, duration: int):
        """Generate video script using AI (expensive)."""
        print(f"  🤖 Generating script for {niche} ({duration}s)...")
        await asyncio.sleep(1.0)  # Simulate AI processing
        return {
            "niche": niche,
            "duration": duration,
            "content": f"AI-generated script for {niche}...",
            "word_count": 150,
        }
    
    # Cache asset searches
    @cached(ttl=1800, key_prefix="assets")
    async def search_assets(query: str, count: int = 5):
        """Search for video assets (expensive API calls)."""
        print(f"  🔍 Searching assets for '{query}'...")
        await asyncio.sleep(0.5)  # Simulate API call
        return [
            {"id": i, "url": f"https://example.com/asset_{i}.mp4"}
            for i in range(count)
        ]
    
    # Generate video (uses cached functions)
    print("\n🎬 Generating video:")
    print("-" * 60)
    
    # First generation (all cache misses)
    print("\n1️⃣ First video generation:")
    start = time.time()
    
    script = await generate_script("meditation", 600)
    assets = await search_assets("peaceful nature", 3)
    
    duration1 = time.time() - start
    print(f"  ✅ Generated in {duration1:.2f}s")
    
    # Second generation with same parameters (all cache hits)
    print("\n2️⃣ Second video generation (cached):")
    start = time.time()
    
    script = await generate_script("meditation", 600)
    assets = await search_assets("peaceful nature", 3)
    
    duration2 = time.time() - start
    print(f"  ✅ Generated in {duration2:.2f}s")
    print(f"  🚀 {duration1/duration2:.1f}x faster with caching!")
    
    await cache.disconnect()


# ============================================
# MAIN
# ============================================

async def main():
    """Run all examples."""
    print("\n" + "🎯 " + "="*56 + " 🎯")
    print("   Redis Caching Layer - Usage Examples")
    print("🎯 " + "="*56 + " 🎯")
    
    await example_basic_operations()
    await example_decorator_caching()
    await example_cache_invalidation()
    await example_context_manager()
    await example_pattern_operations()
    await example_cache_statistics()
    await example_real_world_video_generation()
    
    print("\n" + "="*60)
    print("✅ All examples completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
