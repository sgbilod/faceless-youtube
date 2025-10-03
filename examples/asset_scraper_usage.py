"""
Faceless YouTube - Asset Scraper Usage Examples

Demonstrates how to use the asset scraper system.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.asset_scraper import (
    AssetType,
    ScraperConfig,
    PexelsScraper,
    PixabayScraper,
    UnsplashScraper,
    ScraperManager,
    create_scraper_manager,
)
from src.utils.cache import CacheManager


# ============================================
# EXAMPLE 1: SIMPLE VIDEO SEARCH
# ============================================

async def example_simple_search():
    """Example: Simple video search with Pexels"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Simple Video Search (Pexels)")
    print("="*60)
    
    # Configure scraper
    config = ScraperConfig(
        api_key="YOUR_PEXELS_API_KEY",  # Get from https://www.pexels.com/api/
        cache_enabled=True,
        cache_ttl=3600,
    )
    
    # Create scraper
    async with PexelsScraper(config) as scraper:
        # Search for nature videos
        results = await scraper.search_with_cache(
            query="ocean waves",
            asset_type=AssetType.VIDEO,
            limit=5,
            orientation="landscape",
            min_width=1920,
            min_height=1080,
        )
        
        # Display results
        print(f"\nFound {len(results)} videos:")
        for i, video in enumerate(results, 1):
            print(f"\n{i}. {video.title}")
            print(f"   URL: {video.url}")
            print(f"   Size: {video.width}x{video.height}")
            print(f"   Duration: {video.duration}s")
            print(f"   Creator: {video.creator_name}")
            print(f"   Commercial use: {video.commercial_use}")


# ============================================
# EXAMPLE 2: MULTI-SOURCE SEARCH
# ============================================

async def example_multi_source():
    """Example: Search across multiple sources with fallover"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Multi-Source Search with Failover")
    print("="*60)
    
    # Create scraper manager
    manager = create_scraper_manager(
        pexels_api_key="YOUR_PEXELS_API_KEY",
        pixabay_api_key="YOUR_PIXABAY_API_KEY",
        unsplash_api_key="YOUR_UNSPLASH_ACCESS_KEY",
    )
    
    try:
        # Search for images across all sources
        results = await manager.search(
            query="mountain sunset",
            asset_type=AssetType.IMAGE,
            limit=15,
            use_cache=True,
        )
        
        # Group by source
        by_source = {}
        for result in results:
            if result.source not in by_source:
                by_source[result.source] = []
            by_source[result.source].append(result)
        
        print(f"\nFound {len(results)} images from {len(by_source)} sources:")
        for source, items in by_source.items():
            print(f"\n{source.upper()}: {len(items)} images")
            for item in items[:3]:  # Show first 3
                print(f"  - {item.title[:50]}...")
    
    finally:
        await manager.close_all()


# ============================================
# EXAMPLE 3: PARALLEL SEARCH FOR SPEED
# ============================================

async def example_parallel_search():
    """Example: Parallel search for faster results"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Parallel Search (Faster)")
    print("="*60)
    
    manager = create_scraper_manager(
        pexels_api_key="YOUR_PEXELS_API_KEY",
        pixabay_api_key="YOUR_PIXABAY_API_KEY",
    )
    
    try:
        import time
        
        # Sequential search
        start = time.time()
        results_seq = await manager.search(
            "nature",
            AssetType.VIDEO,
            limit=10,
        )
        seq_time = time.time() - start
        
        # Parallel search
        start = time.time()
        results_par = await manager.search_parallel(
            "nature",
            AssetType.VIDEO,
            limit=10,
        )
        par_time = time.time() - start
        
        print(f"\nSequential: {len(results_seq)} results in {seq_time:.2f}s")
        print(f"Parallel:   {len(results_par)} results in {par_time:.2f}s")
        print(f"Speedup:    {seq_time/par_time:.2f}x")
    
    finally:
        await manager.close_all()


# ============================================
# EXAMPLE 4: DIVERSE RESULTS
# ============================================

async def example_diverse_results():
    """Example: Get diverse results from multiple sources"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Diverse Results (Interleaved)")
    print("="*60)
    
    manager = create_scraper_manager(
        pexels_api_key="YOUR_PEXELS_API_KEY",
        pixabay_api_key="YOUR_PIXABAY_API_KEY",
    )
    
    try:
        # Get diverse results (interleaved from sources)
        results = await manager.get_diverse_results(
            query="forest",
            asset_type=AssetType.VIDEO,
            total_limit=20,
            per_source_limit=10,
        )
        
        print(f"\nGot {len(results)} diverse results:")
        for i, result in enumerate(results, 1):
            print(f"{i}. [{result.source:8}] {result.title[:40]}")
    
    finally:
        await manager.close_all()


# ============================================
# EXAMPLE 5: HEALTH MONITORING
# ============================================

async def example_health_monitoring():
    """Example: Monitor scraper health"""
    print("\n" + "="*60)
    print("EXAMPLE 5: Health Monitoring")
    print("="*60)
    
    manager = create_scraper_manager(
        pexels_api_key="YOUR_PEXELS_API_KEY",
        pixabay_api_key="YOUR_PIXABAY_API_KEY",
    )
    
    try:
        # Make some requests
        await manager.search("test", AssetType.VIDEO, limit=5)
        await manager.search("example", AssetType.IMAGE, limit=5)
        
        # Check health
        health = manager.get_health_status()
        
        print("\nScraper Health Status:")
        for source, status in health.items():
            health_info = status['health']
            print(f"\n{source.upper()}:")
            print(f"  Status: {'✓ Healthy' if health_info['is_healthy'] else '✗ Unhealthy'}")
            print(f"  Total requests: {health_info['total_requests']}")
            print(f"  Success rate: {health_info['success_rate']}%")
            print(f"  Consecutive failures: {health_info['consecutive_failures']}")
    
    finally:
        await manager.close_all()


# ============================================
# EXAMPLE 6: SPECIFIC SOURCE SEARCH
# ============================================

async def example_specific_source():
    """Example: Search specific sources only"""
    print("\n" + "="*60)
    print("EXAMPLE 6: Specific Source Search")
    print("="*60)
    
    manager = create_scraper_manager(
        pexels_api_key="YOUR_PEXELS_API_KEY",
        pixabay_api_key="YOUR_PIXABAY_API_KEY",
        unsplash_api_key="YOUR_UNSPLASH_ACCESS_KEY",
    )
    
    try:
        # Search only Pexels and Pixabay (skip Unsplash)
        results = await manager.search(
            query="beach",
            asset_type=AssetType.VIDEO,
            limit=10,
            sources=["pexels", "pixabay"],  # Specify sources
        )
        
        sources_used = set(r.source for r in results)
        print(f"\nSearched only: pexels, pixabay")
        print(f"Got results from: {', '.join(sources_used)}")
        print(f"Total results: {len(results)}")
    
    finally:
        await manager.close_all()


# ============================================
# EXAMPLE 7: ADVANCED FILTERING
# ============================================

async def example_advanced_filtering():
    """Example: Advanced search with filters"""
    print("\n" + "="*60)
    print("EXAMPLE 7: Advanced Filtering")
    print("="*60)
    
    config = ScraperConfig(api_key="YOUR_PEXELS_API_KEY")
    
    async with PexelsScraper(config) as scraper:
        # Search with specific requirements
        results = await scraper.search_with_cache(
            query="waterfall",
            asset_type=AssetType.VIDEO,
            limit=10,
            orientation="portrait",  # Vertical videos for mobile
            min_width=1080,
            min_height=1920,
            min_duration=10,  # At least 10 seconds
            max_duration=30,  # At most 30 seconds
        )
        
        print(f"\nFound {len(results)} portrait videos (1080x1920+, 10-30s):")
        for video in results:
            print(f"  - {video.width}x{video.height}, {video.duration}s")


# ============================================
# EXAMPLE 8: CACHING BENEFITS
# ============================================

async def example_caching_benefits():
    """Example: Demonstrate caching performance"""
    print("\n" + "="*60)
    print("EXAMPLE 8: Caching Performance Benefits")
    print("="*60)
    
    import time
    
    config = ScraperConfig(
        api_key="YOUR_PEXELS_API_KEY",
        cache_enabled=True,
    )
    
    async with PexelsScraper(config) as scraper:
        query = "sunset timelapse"
        
        # First search (cache miss)
        start = time.time()
        results1 = await scraper.search_with_cache(
            query, AssetType.VIDEO, limit=10
        )
        time1 = time.time() - start
        
        # Second search (cache hit)
        start = time.time()
        results2 = await scraper.search_with_cache(
            query, AssetType.VIDEO, limit=10
        )
        time2 = time.time() - start
        
        print(f"\nFirst search (API):   {time1:.3f}s")
        print(f"Second search (cache): {time2:.3f}s")
        print(f"Speedup: {time1/time2:.1f}x faster!")
        
        # Get cache stats
        stats = await scraper.cache_manager.get_stats()
        print(f"\nCache stats:")
        print(f"  Hit rate: {stats['hit_rate']:.1f}%")
        print(f"  Hits: {stats['hits']}")
        print(f"  Misses: {stats['misses']}")


# ============================================
# EXAMPLE 9: POPULAR/CURATED CONTENT
# ============================================

async def example_popular_content():
    """Example: Get popular/curated content"""
    print("\n" + "="*60)
    print("EXAMPLE 9: Popular & Curated Content")
    print("="*60)
    
    # Pexels popular videos
    pexels_config = ScraperConfig(api_key="YOUR_PEXELS_API_KEY")
    async with PexelsScraper(pexels_config) as scraper:
        popular = await scraper.get_popular_videos(limit=5)
        print(f"\nPexels Popular Videos: {len(popular)}")
        for video in popular:
            print(f"  - {video.title}")
    
    # Unsplash curated photos
    unsplash_config = ScraperConfig(api_key="YOUR_UNSPLASH_ACCESS_KEY")
    async with UnsplashScraper(unsplash_config) as scraper:
        curated = await scraper.get_curated_photos(limit=5)
        print(f"\nUnsplash Curated Photos: {len(curated)}")
        for photo in curated:
            print(f"  - {photo.title}")


# ============================================
# RUN ALL EXAMPLES
# ============================================

async def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("FACELESS YOUTUBE - ASSET SCRAPER EXAMPLES")
    print("="*60)
    
    print("\nNOTE: These examples require API keys!")
    print("Get API keys from:")
    print("  - Pexels: https://www.pexels.com/api/")
    print("  - Pixabay: https://pixabay.com/api/docs/")
    print("  - Unsplash: https://unsplash.com/developers")
    
    # Uncomment to run examples (requires API keys)
    # await example_simple_search()
    # await example_multi_source()
    # await example_parallel_search()
    # await example_diverse_results()
    # await example_health_monitoring()
    # await example_specific_source()
    # await example_advanced_filtering()
    # await example_caching_benefits()
    # await example_popular_content()
    
    print("\n✓ Asset scraper examples ready to run!")
    print("  Add your API keys and uncomment examples in main()")


if __name__ == "__main__":
    asyncio.run(main())
