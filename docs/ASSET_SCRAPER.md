# Asset Scraper System

The Faceless YouTube Asset Scraper provides a unified interface for fetching free stock media (videos, images, audio) from multiple sources with automatic caching, rate limiting, health monitoring, and failover capabilities.

## 🎯 Features

- **Multi-Source Support**: Pexels, Pixabay, Unsplash, and easily extensible
- **Automatic Caching**: Redis-backed with in-memory fallback (reduces API calls)
- **Rate Limiting**: Token bucket algorithm prevents API quota exhaustion
- **Health Monitoring**: Track scraper performance and automatically skip unhealthy sources
- **Automatic Failover**: Seamlessly switch between sources when one fails
- **Parallel Search**: Query multiple sources simultaneously for faster results
- **Proxy Support**: Route requests through proxies for reliability
- **Retry Logic**: Exponential backoff for transient failures

## 📦 Supported Sources

| Source       | Assets                | Attribution  | Commercial | API Limit      | Priority |
| ------------ | --------------------- | ------------ | ---------- | -------------- | -------- |
| **Pexels**   | Videos, Images        | Optional     | ✓ Yes      | 200/hour       | HIGH     |
| **Pixabay**  | Videos, Images, Audio | Not required | ✓ Yes      | 5000/hour      | HIGH     |
| **Unsplash** | Images                | Required     | ✓ Yes      | 50/hour (demo) | MEDIUM   |

## 🚀 Quick Start

### 1. Get API Keys

```bash
# Pexels (free, no credit card)
https://www.pexels.com/api/

# Pixabay (free, no credit card)
https://pixabay.com/api/docs/

# Unsplash (free, 50 requests/hour demo)
https://unsplash.com/developers
```

### 2. Configure Environment

```bash
# Add to .env file
PEXELS_API_KEY=your_pexels_key_here
PIXABAY_API_KEY=your_pixabay_key_here
UNSPLASH_ACCESS_KEY=your_unsplash_key_here
```

### 3. Basic Usage

```python
import asyncio
from src.services.asset_scraper import (
    AssetType,
    create_scraper_manager,
)

async def search_videos():
    # Create manager with all scrapers
    manager = create_scraper_manager(
        pexels_api_key="your_key",
        pixabay_api_key="your_key",
        unsplash_api_key="your_key",
    )

    try:
        # Search for videos
        results = await manager.search(
            query="ocean waves",
            asset_type=AssetType.VIDEO,
            limit=20,
        )

        for video in results:
            print(f"{video.title} - {video.url}")

    finally:
        await manager.close_all()

asyncio.run(search_videos())
```

## 📖 Usage Examples

### Example 1: Simple Video Search

```python
from src.services.asset_scraper import PexelsScraper, ScraperConfig, AssetType

async def search_pexels():
    config = ScraperConfig(
        api_key="your_pexels_api_key",
        cache_enabled=True,
        cache_ttl=3600,
    )

    async with PexelsScraper(config) as scraper:
        results = await scraper.search_with_cache(
            query="sunset",
            asset_type=AssetType.VIDEO,
            limit=10,
            orientation="landscape",
            min_width=1920,
            min_height=1080,
        )

        for video in results:
            print(f"{video.title}: {video.width}x{video.height}")
```

### Example 2: Multi-Source with Failover

```python
async def multi_source_search():
    manager = create_scraper_manager(
        pexels_api_key="key1",
        pixabay_api_key="key2",
    )

    try:
        # Automatically tries multiple sources
        results = await manager.search(
            "mountain landscape",
            AssetType.IMAGE,
            limit=30,
        )

        # Results from multiple sources
        sources = set(r.source for r in results)
        print(f"Got results from: {sources}")

    finally:
        await manager.close_all()
```

### Example 3: Parallel Search (Faster)

```python
async def fast_search():
    manager = create_scraper_manager(...)

    try:
        # Search all sources in parallel
        results = await manager.search_parallel(
            "nature",
            AssetType.VIDEO,
            limit=20,
        )

        print(f"Found {len(results)} videos")

    finally:
        await manager.close_all()
```

### Example 4: Diverse Results

```python
async def diverse_search():
    manager = create_scraper_manager(...)

    try:
        # Get interleaved results from all sources
        results = await manager.get_diverse_results(
            query="forest",
            asset_type=AssetType.VIDEO,
            total_limit=30,
            per_source_limit=10,
        )

        # Results are mixed from all sources
        for i, video in enumerate(results, 1):
            print(f"{i}. [{video.source}] {video.title}")

    finally:
        await manager.close_all()
```

### Example 5: Health Monitoring

```python
async def check_health():
    manager = create_scraper_manager(...)

    # Make some requests
    await manager.search("test", AssetType.VIDEO, limit=5)

    # Check scraper health
    health = manager.get_health_status()

    for source, status in health.items():
        print(f"{source}: {status['health']['success_rate']}%")

    await manager.close_all()
```

## 🔧 Configuration

### Scraper Configuration

```python
from src.services.asset_scraper import ScraperConfig

config = ScraperConfig(
    # API credentials
    api_key="your_api_key",
    api_secret=None,  # Some APIs need this

    # Rate limiting
    requests_per_minute=60,
    requests_per_hour=3600,

    # Retry logic
    max_retries=3,
    retry_delay=1.0,  # seconds
    retry_backoff=2.0,  # exponential multiplier

    # Timeout
    request_timeout=30,  # seconds

    # Proxy (optional)
    proxy_url="http://proxy.example.com:8080",
    proxy_auth={"username": "user", "password": "pass"},

    # Caching
    cache_enabled=True,
    cache_ttl=3600,  # 1 hour

    # Health monitoring
    health_check_interval=300,  # 5 minutes
    max_consecutive_failures=5,
)
```

### Environment Variables

```bash
# Asset scraper API keys
PEXELS_API_KEY=your_pexels_api_key
PIXABAY_API_KEY=your_pixabay_api_key
UNSPLASH_ACCESS_KEY=your_unsplash_access_key

# Scraper configuration
ASSET_SCRAPER_CACHE_ENABLED=true
ASSET_SCRAPER_CACHE_TTL=3600
ASSET_SCRAPER_MAX_RETRIES=3
ASSET_SCRAPER_REQUEST_TIMEOUT=30

# Proxy (optional)
ASSET_SCRAPER_PROXY_URL=http://proxy.example.com:8080
ASSET_SCRAPER_PROXY_USERNAME=user
ASSET_SCRAPER_PROXY_PASSWORD=pass
```

## 📊 Asset Metadata Structure

Each scraped asset includes comprehensive metadata:

```python
AssetMetadata(
    # Identifiers
    asset_id="unique_id",
    source="pexels",  # or pixabay, unsplash, etc.
    asset_type=AssetType.VIDEO,  # VIDEO, IMAGE, or AUDIO

    # URLs
    url="https://...",  # Direct download URL
    preview_url="https://...",  # Thumbnail/preview
    page_url="https://...",  # Web page

    # Properties
    title="Sunset Over Ocean",
    description="Beautiful sunset...",
    tags=["sunset", "ocean", "nature"],

    # Dimensions (video/image)
    width=1920,
    height=1080,
    duration=30,  # seconds (video/audio)
    file_size=15728640,  # bytes
    format="mp4",

    # Creator
    creator_name="John Doe",
    creator_url="https://...",

    # Licensing
    license="Pexels License",
    license_url="https://...",
    attribution_required=False,
    commercial_use=True,

    # Metadata
    scraped_at=datetime.utcnow(),
    popularity=1500,  # views/likes/downloads
)
```

## 🎨 Advanced Features

### Custom Scraper Implementation

```python
from src.services.asset_scraper import BaseScraper, AssetType

class MyCustomScraper(BaseScraper):
    @property
    def source_name(self) -> str:
        return "my_source"

    @property
    def base_url(self) -> str:
        return "https://api.mysource.com"

    async def search(
        self,
        query: str,
        asset_type: AssetType,
        limit: int = 20,
        **kwargs
    ) -> List[AssetMetadata]:
        # Implement search logic
        url = f"{self.base_url}/search?q={query}"
        response = await self._make_request("GET", url)

        # Parse and return results
        results = []
        for item in response["items"]:
            metadata = AssetMetadata(
                asset_id=item["id"],
                source=self.source_name,
                asset_type=asset_type,
                url=item["download_url"],
                # ... other fields
            )
            results.append(metadata)

        return results
```

### Rate Limiter

The built-in rate limiter uses a token bucket algorithm:

```python
from src.services.asset_scraper.base_scraper import RateLimiter

limiter = RateLimiter(
    requests_per_minute=60,
    requests_per_hour=3600,
)

# Acquire permission (blocks if rate limit exceeded)
await limiter.acquire()

# Make your request
response = await make_api_call()
```

### Health Monitoring

Track scraper health automatically:

```python
scraper = PexelsScraper(config)

# Health is tracked automatically
scraper.health_monitor.record_success()
scraper.health_monitor.record_failure()

# Check health
if scraper.health_monitor.is_healthy:
    results = await scraper.search(...)

# Get detailed stats
stats = scraper.health_monitor.get_stats()
print(f"Success rate: {stats['success_rate']}%")
```

## 🧪 Testing

### Run Unit Tests

```bash
# Run all tests
pytest tests/unit/test_asset_scraper.py -v

# Run specific test
pytest tests/unit/test_asset_scraper.py::test_scraper_config_defaults -v

# Run with coverage
pytest tests/unit/test_asset_scraper.py --cov=src.services.asset_scraper
```

### Integration Tests

Integration tests require real API keys:

```bash
# Set API keys
export PEXELS_API_KEY=your_key
export PIXABAY_API_KEY=your_key
export UNSPLASH_ACCESS_KEY=your_key

# Run integration tests
pytest tests/unit/test_asset_scraper.py -v -m "not skip"
```

## 🔍 Troubleshooting

### Issue: API Rate Limit Exceeded

**Symptom**: `RateLimitError` or 429 HTTP status

**Solution**:

```python
# Reduce rate limits
config = ScraperConfig(
    requests_per_minute=30,  # Lower limits
    requests_per_hour=1000,
)

# Or enable aggressive caching
config = ScraperConfig(
    cache_enabled=True,
    cache_ttl=7200,  # 2 hours
)
```

### Issue: All Scrapers Unhealthy

**Symptom**: `ValueError: No healthy scrapers available`

**Solution**:

```python
# Check health status
health = manager.get_health_status()
print(health)

# Reset health manually
for scraper in manager.scrapers.values():
    scraper.health_monitor.consecutive_failures = 0
    scraper.health_monitor.is_healthy = True
```

### Issue: Slow Search Performance

**Solution**:

```python
# Use parallel search
results = await manager.search_parallel(...)

# Reduce limit per source
results = await manager.get_diverse_results(
    query="...",
    asset_type=AssetType.VIDEO,
    total_limit=20,
    per_source_limit=5,  # Less per source = faster
)
```

### Issue: Cache Not Working

**Symptom**: All requests hit the API

**Solution**:

```python
# Verify cache is enabled
config = ScraperConfig(cache_enabled=True)

# Check cache stats
stats = await scraper.cache_manager.get_stats()
print(f"Hit rate: {stats['hit_rate']}%")

# Verify Redis connection
await scraper.cache_manager.ping()
```

## 📈 Performance Tips

1. **Enable Caching**: Reduces API calls by 80-90%

   ```python
   config = ScraperConfig(cache_enabled=True, cache_ttl=3600)
   ```

2. **Use Parallel Search**: 2-3x faster for multi-source queries

   ```python
   results = await manager.search_parallel(...)
   ```

3. **Limit Results**: Only request what you need

   ```python
   results = await manager.search(..., limit=10)  # Not 100
   ```

4. **Reuse Scrapers**: Don't create new instances for each search

   ```python
   # Good: Reuse scraper
   async with PexelsScraper(config) as scraper:
       for query in queries:
           results = await scraper.search(query, ...)

   # Bad: Create new each time
   for query in queries:
       scraper = PexelsScraper(config)
       results = await scraper.search(query, ...)
       await scraper.close()
   ```

5. **Monitor Health**: Skip unhealthy sources automatically
   ```python
   # Manager does this automatically
   healthy_scrapers = manager.get_healthy_scrapers(AssetType.VIDEO)
   ```

## 🚀 Production Deployment

### Docker Compose

```yaml
version: "3.8"

services:
  app:
    build: .
    environment:
      - PEXELS_API_KEY=${PEXELS_API_KEY}
      - PIXABAY_API_KEY=${PIXABAY_API_KEY}
      - UNSPLASH_ACCESS_KEY=${UNSPLASH_ACCESS_KEY}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

volumes:
  redis-data:
```

### Environment Variables

```bash
# Production settings
ASSET_SCRAPER_CACHE_ENABLED=true
ASSET_SCRAPER_CACHE_TTL=7200
ASSET_SCRAPER_MAX_RETRIES=5
ASSET_SCRAPER_REQUEST_TIMEOUT=60

# Use connection pooling
REDIS_POOL_MAX_CONNECTIONS=20
REDIS_POOL_TIMEOUT=30
```

### Monitoring

```python
# Add to your monitoring system
async def monitor_scrapers():
    manager = create_scraper_manager(...)

    while True:
        health = manager.get_health_status()

        for source, status in health.items():
            metrics.gauge(
                f"scraper.{source}.success_rate",
                status['health']['success_rate']
            )
            metrics.gauge(
                f"scraper.{source}.consecutive_failures",
                status['health']['consecutive_failures']
            )

        await asyncio.sleep(60)  # Check every minute
```

## 📚 API Reference

See inline documentation in source files:

- `base_scraper.py` - Base scraper class and components
- `pexels_scraper.py` - Pexels implementation
- `pixabay_scraper.py` - Pixabay implementation
- `unsplash_scraper.py` - Unsplash implementation
- `scraper_manager.py` - Manager for multiple scrapers

## 🤝 Contributing

To add a new scraper:

1. Inherit from `BaseScraper`
2. Implement required properties (`source_name`, `base_url`)
3. Implement `search()` method
4. Add to `create_scraper_manager()` helper
5. Write tests in `test_asset_scraper.py`
6. Update this documentation

## 📄 License

This scraper system is part of the Faceless YouTube project. See LICENSE for details.

**Note**: Each asset source has its own license requirements. Always check and comply with:

- Pexels License: https://www.pexels.com/license/
- Pixabay License: https://pixabay.com/service/license/
- Unsplash License: https://unsplash.com/license

## 🆘 Support

- Issues: https://github.com/sgbilod/faceless-youtube/issues
- Documentation: See `docs/` folder
- Examples: See `examples/asset_scraper_usage.py`
