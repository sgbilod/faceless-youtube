"""
Faceless YouTube - Asset Scraper Tests

Test suite for asset scraper functionality.
"""

import pytest
import asyncio
from datetime import datetime
from typing import List

from src.services.asset_scraper import (
    BaseScraper,
    ScraperConfig,
    AssetType,
    AssetMetadata,
    PexelsScraper,
    PixabayScraper,
    UnsplashScraper,
    ScraperManager,
    create_scraper_manager,
)


# ============================================
# MOCK SCRAPER FOR TESTING
# ============================================

class MockScraper(BaseScraper):
    """Mock scraper for testing"""
    
    def __init__(self, config: ScraperConfig, source_name: str = "mock"):
        super().__init__(config)
        self._source_name = source_name
        self._should_fail = False
    
    @property
    def source_name(self) -> str:
        return self._source_name
    
    @property
    def base_url(self) -> str:
        return "https://mock.example.com"
    
    async def search(
        self,
        query: str,
        asset_type: AssetType,
        limit: int = 20,
        **kwargs
    ) -> List[AssetMetadata]:
        if self._should_fail:
            raise Exception("Mock scraper failure")
        
        # Return mock results
        results = []
        for i in range(min(limit, 5)):
            results.append(AssetMetadata(
                asset_id=f"{self.source_name}_{i}",
                source=self.source_name,
                asset_type=asset_type,
                url=f"https://mock.example.com/asset_{i}.mp4",
                title=f"{query} - Result {i}",
                commercial_use=True,
            ))
        
        return results


# ============================================
# CONFIGURATION TESTS
# ============================================

def test_scraper_config_defaults():
    """Test default scraper configuration"""
    config = ScraperConfig()
    
    assert config.requests_per_minute == 60
    assert config.requests_per_hour == 3600
    assert config.max_retries == 3
    assert config.retry_delay == 1.0
    assert config.cache_enabled is True
    assert config.cache_ttl == 3600


def test_scraper_config_custom():
    """Test custom scraper configuration"""
    config = ScraperConfig(
        api_key="test_key",
        requests_per_minute=100,
        cache_ttl=7200,
    )
    
    assert config.api_key == "test_key"
    assert config.requests_per_minute == 100
    assert config.cache_ttl == 7200


# ============================================
# BASE SCRAPER TESTS
# ============================================

@pytest.mark.asyncio
async def test_base_scraper_cache_key_generation():
    """Test cache key generation"""
    config = ScraperConfig()
    scraper = MockScraper(config)
    
    key1 = scraper._generate_cache_key("nature", limit=10)
    key2 = scraper._generate_cache_key("nature", limit=10)
    key3 = scraper._generate_cache_key("nature", limit=20)
    
    # Same parameters should generate same key
    assert key1 == key2
    
    # Different parameters should generate different key
    assert key1 != key3
    
    await scraper.close()


@pytest.mark.asyncio
async def test_base_scraper_health_monitoring():
    """Test health monitoring"""
    config = ScraperConfig(max_consecutive_failures=3)
    scraper = MockScraper(config)
    
    # Initially healthy
    assert scraper.health_monitor.is_healthy is True
    
    # Record successes
    scraper.health_monitor.record_success()
    scraper.health_monitor.record_success()
    assert scraper.health_monitor.successful_requests == 2
    
    # Record failures
    scraper.health_monitor.record_failure()
    scraper.health_monitor.record_failure()
    assert scraper.health_monitor.failed_requests == 2
    assert scraper.health_monitor.is_healthy is True  # Still under threshold
    
    # Exceed failure threshold
    scraper.health_monitor.record_failure()
    assert scraper.health_monitor.is_healthy is False
    
    # Recovery
    scraper.health_monitor.record_success()
    assert scraper.health_monitor.is_healthy is True
    assert scraper.health_monitor.consecutive_failures == 0
    
    await scraper.close()


@pytest.mark.asyncio
async def test_base_scraper_context_manager():
    """Test async context manager"""
    config = ScraperConfig()
    
    async with MockScraper(config) as scraper:
        assert scraper is not None
        results = await scraper.search("test", AssetType.VIDEO, limit=3)
        assert len(results) == 3
    
    # Session should be closed after context
    assert scraper._session is None or scraper._session.closed


# ============================================
# ASSET METADATA TESTS
# ============================================

def test_asset_metadata_creation():
    """Test creating asset metadata"""
    metadata = AssetMetadata(
        asset_id="test_123",
        source="test_source",
        asset_type=AssetType.VIDEO,
        url="https://example.com/video.mp4",
        title="Test Video",
        width=1920,
        height=1080,
        duration=60,
        commercial_use=True,
    )
    
    assert metadata.asset_id == "test_123"
    assert metadata.source == "test_source"
    assert metadata.asset_type == AssetType.VIDEO
    assert metadata.width == 1920
    assert metadata.height == 1080
    assert metadata.commercial_use is True


def test_asset_metadata_serialization():
    """Test asset metadata serialization"""
    metadata = AssetMetadata(
        asset_id="test_456",
        source="test",
        asset_type=AssetType.IMAGE,
        url="https://example.com/image.jpg",
    )
    
    # Convert to dict
    data = metadata.dict()
    assert isinstance(data, dict)
    assert data["asset_id"] == "test_456"
    assert data["asset_type"] == "image"
    
    # Reconstruct from dict
    metadata2 = AssetMetadata(**data)
    assert metadata2.asset_id == metadata.asset_id
    assert metadata2.source == metadata.source


# ============================================
# SCRAPER MANAGER TESTS
# ============================================

@pytest.mark.asyncio
async def test_scraper_manager_registration():
    """Test registering scrapers"""
    manager = ScraperManager()
    
    config = ScraperConfig()
    scraper1 = MockScraper(config, "source1")
    scraper2 = MockScraper(config, "source2")
    
    manager.register_scraper(scraper1)
    manager.register_scraper(scraper2)
    
    assert len(manager.scrapers) == 2
    assert manager.get_scraper("source1") == scraper1
    assert manager.get_scraper("source2") == scraper2
    
    await manager.close_all()


@pytest.mark.asyncio
async def test_scraper_manager_search():
    """Test searching with scraper manager"""
    manager = ScraperManager()
    
    config = ScraperConfig()
    scraper = MockScraper(config, "test_source")
    manager.register_scraper(scraper)
    
    results = await manager.search("nature", AssetType.VIDEO, limit=3)
    
    assert len(results) <= 3
    assert all(r.source == "test_source" for r in results)
    assert all(r.asset_type == AssetType.VIDEO for r in results)
    
    await manager.close_all()


@pytest.mark.asyncio
async def test_scraper_manager_failover():
    """Test automatic failover between scrapers"""
    manager = ScraperManager()
    
    config = ScraperConfig()
    
    # Create scrapers - first one will fail
    scraper1 = MockScraper(config, "failing_source")
    scraper1._should_fail = True
    
    scraper2 = MockScraper(config, "working_source")
    
    manager.register_scraper(scraper1)
    manager.register_scraper(scraper2)
    
    # Search should failover to second scraper
    results = await manager.search("test", AssetType.VIDEO, limit=5)
    
    assert len(results) > 0
    assert all(r.source == "working_source" for r in results)
    
    await manager.close_all()


@pytest.mark.asyncio
async def test_scraper_manager_parallel_search():
    """Test parallel search across scrapers"""
    manager = ScraperManager()
    
    config = ScraperConfig()
    scraper1 = MockScraper(config, "source1")
    scraper2 = MockScraper(config, "source2")
    
    manager.register_scraper(scraper1)
    manager.register_scraper(scraper2)
    
    results = await manager.search_parallel("test", AssetType.IMAGE, limit=10)
    
    # Should have results from both scrapers
    sources = set(r.source for r in results)
    assert len(sources) == 2
    assert "source1" in sources
    assert "source2" in sources
    
    await manager.close_all()


@pytest.mark.asyncio
async def test_scraper_manager_diverse_results():
    """Test getting diverse results from multiple sources"""
    manager = ScraperManager()
    
    config = ScraperConfig()
    scraper1 = MockScraper(config, "source1")
    scraper2 = MockScraper(config, "source2")
    
    manager.register_scraper(scraper1)
    manager.register_scraper(scraper2)
    
    results = await manager.get_diverse_results(
        "test",
        AssetType.VIDEO,
        total_limit=10,
        per_source_limit=5
    )
    
    # Results should be interleaved from both sources
    assert len(results) <= 10
    
    # Check that both sources are represented
    sources = [r.source for r in results]
    assert "source1" in sources
    assert "source2" in sources
    
    await manager.close_all()


@pytest.mark.asyncio
async def test_scraper_manager_health_status():
    """Test getting health status"""
    manager = ScraperManager()
    
    config = ScraperConfig()
    scraper = MockScraper(config, "test_source")
    manager.register_scraper(scraper)
    
    # Record some activity
    scraper.health_monitor.record_success()
    scraper.health_monitor.record_success()
    scraper.health_monitor.record_failure()
    
    status = manager.get_health_status()
    
    assert "test_source" in status
    assert status["test_source"]["health"]["total_requests"] == 3
    assert status["test_source"]["health"]["successful_requests"] == 2
    assert status["test_source"]["health"]["failed_requests"] == 1
    
    await manager.close_all()


@pytest.mark.asyncio
async def test_scraper_manager_context_manager():
    """Test scraper manager as context manager"""
    async with ScraperManager() as manager:
        config = ScraperConfig()
        scraper = MockScraper(config)
        manager.register_scraper(scraper)
        
        results = await manager.search("test", AssetType.VIDEO)
        assert len(results) > 0


# ============================================
# INTEGRATION TESTS (require API keys)
# ============================================

@pytest.mark.skip(reason="Requires API keys")
@pytest.mark.asyncio
async def test_pexels_integration():
    """Integration test with real Pexels API"""
    config = ScraperConfig(api_key="YOUR_PEXELS_API_KEY")
    
    async with PexelsScraper(config) as scraper:
        results = await scraper.search_with_cache(
            "nature",
            AssetType.VIDEO,
            limit=5
        )
        
        assert len(results) > 0
        assert all(r.source == "pexels" for r in results)
        assert all(r.commercial_use is True for r in results)


@pytest.mark.skip(reason="Requires API keys")
@pytest.mark.asyncio
async def test_pixabay_integration():
    """Integration test with real Pixabay API"""
    config = ScraperConfig(api_key="YOUR_PIXABAY_API_KEY")
    
    async with PixabayScraper(config) as scraper:
        results = await scraper.search_with_cache(
            "ocean",
            AssetType.VIDEO,
            limit=5
        )
        
        assert len(results) > 0
        assert all(r.source == "pixabay" for r in results)


@pytest.mark.skip(reason="Requires API keys")
@pytest.mark.asyncio
async def test_unsplash_integration():
    """Integration test with real Unsplash API"""
    config = ScraperConfig(api_key="YOUR_UNSPLASH_ACCESS_KEY")
    
    async with UnsplashScraper(config) as scraper:
        results = await scraper.search_with_cache(
            "mountains",
            AssetType.IMAGE,
            limit=5
        )
        
        assert len(results) > 0
        assert all(r.source == "unsplash" for r in results)
        assert all(r.attribution_required is True for r in results)


# ============================================
# RATE LIMITING TESTS
# ============================================

@pytest.mark.asyncio
async def test_rate_limiter():
    """Test rate limiter functionality"""
    from src.services.asset_scraper.base_scraper import RateLimiter
    
    limiter = RateLimiter(requests_per_minute=5, requests_per_hour=100)
    
    # Should be able to acquire 5 tokens quickly
    start = asyncio.get_event_loop().time()
    for _ in range(5):
        await limiter.acquire()
    elapsed = asyncio.get_event_loop().time() - start
    
    assert elapsed < 1.0  # Should be fast
    
    # 6th request should be rate limited
    # (We'll skip this to keep tests fast)
    # await limiter.acquire()  # Would wait ~60 seconds


# ============================================
# RUN TESTS
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
