"""
Faceless YouTube - Scraper Manager

Manages multiple asset scrapers with failover and load balancing.
"""

import asyncio
from typing import Dict, List, Optional, Set, Any
from enum import Enum

from .base_scraper import (
    BaseScraper,
    ScraperConfig,
    AssetType,
    AssetMetadata,
)
from .pexels_scraper import PexelsScraper
from .pixabay_scraper import PixabayScraper
from .unsplash_scraper import UnsplashScraper
from src.utils.cache import CacheManager


class ScraperPriority(str, Enum):
    """Priority levels for scrapers"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ScraperManager:
    """
    Manages multiple asset scrapers with:
    - Automatic failover
    - Load balancing
    - Health monitoring
    - Unified search interface
    """
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        """
        Initialize scraper manager.
        
        Args:
            cache_manager: Optional cache manager instance
        """
        self.cache_manager = cache_manager or CacheManager()
        self.scrapers: Dict[str, BaseScraper] = {}
        self.priorities: Dict[str, ScraperPriority] = {}
        self._initialized = False
    
    def register_scraper(
        self,
        scraper: BaseScraper,
        priority: ScraperPriority = ScraperPriority.MEDIUM
    ) -> None:
        """
        Register a scraper with the manager.
        
        Args:
            scraper: Scraper instance
            priority: Priority level for this scraper
        """
        self.scrapers[scraper.source_name] = scraper
        self.priorities[scraper.source_name] = priority
    
    def get_scraper(self, source_name: str) -> Optional[BaseScraper]:
        """Get a specific scraper by name"""
        return self.scrapers.get(source_name)
    
    def get_healthy_scrapers(self, asset_type: AssetType) -> List[BaseScraper]:
        """
        Get all healthy scrapers that support the given asset type.
        
        Args:
            asset_type: Type of assets needed
        
        Returns:
            List of healthy scrapers, sorted by priority
        """
        healthy = []
        
        for source_name, scraper in self.scrapers.items():
            # Check health
            if not scraper.health_monitor.is_healthy:
                continue
            
            # Check if scraper supports this asset type
            # (We'll try and let it fail gracefully if not supported)
            healthy.append((scraper, self.priorities.get(source_name, ScraperPriority.MEDIUM)))
        
        # Sort by priority (HIGH > MEDIUM > LOW)
        priority_order = {
            ScraperPriority.HIGH: 0,
            ScraperPriority.MEDIUM: 1,
            ScraperPriority.LOW: 2,
        }
        healthy.sort(key=lambda x: priority_order[x[1]])
        
        return [scraper for scraper, _ in healthy]
    
    async def search(
        self,
        query: str,
        asset_type: AssetType,
        limit: int = 20,
        sources: Optional[List[str]] = None,
        use_cache: bool = True,
        **kwargs
    ) -> List[AssetMetadata]:
        """
        Search for assets across multiple scrapers with automatic failover.
        
        Args:
            query: Search query
            asset_type: Type of assets to search for
            limit: Maximum total results
            sources: Optional list of source names to use (if None, uses all healthy)
            use_cache: Whether to use caching
            **kwargs: Additional search parameters passed to scrapers
        
        Returns:
            List of asset metadata from successful scrapers
        """
        # Get scrapers to use
        if sources:
            scrapers = [self.scrapers[name] for name in sources if name in self.scrapers]
        else:
            scrapers = self.get_healthy_scrapers(asset_type)
        
        if not scrapers:
            raise ValueError(f"No healthy scrapers available for {asset_type}")
        
        # Try each scraper until we get results
        all_results = []
        per_scraper_limit = max(1, limit // len(scrapers))
        
        for scraper in scrapers:
            try:
                if use_cache:
                    results = await scraper.search_with_cache(
                        query, asset_type, per_scraper_limit, **kwargs
                    )
                else:
                    results = await scraper.search(
                        query, asset_type, per_scraper_limit, **kwargs
                    )
                
                all_results.extend(results)
                
                # If we have enough results, stop
                if len(all_results) >= limit:
                    break
            
            except Exception as e:
                # Log error but continue with next scraper
                print(f"Scraper {scraper.source_name} failed: {e}")
                continue
        
        return all_results[:limit]
    
    async def search_parallel(
        self,
        query: str,
        asset_type: AssetType,
        limit: int = 20,
        sources: Optional[List[str]] = None,
        use_cache: bool = True,
        **kwargs
    ) -> List[AssetMetadata]:
        """
        Search for assets across multiple scrapers in parallel.
        
        Faster than sequential search but uses more resources.
        
        Args:
            query: Search query
            asset_type: Type of assets to search for
            limit: Maximum total results
            sources: Optional list of source names to use
            use_cache: Whether to use caching
            **kwargs: Additional search parameters
        
        Returns:
            List of asset metadata from all scrapers combined
        """
        # Get scrapers to use
        if sources:
            scrapers = [self.scrapers[name] for name in sources if name in self.scrapers]
        else:
            scrapers = self.get_healthy_scrapers(asset_type)
        
        if not scrapers:
            raise ValueError(f"No healthy scrapers available for {asset_type}")
        
        # Create search tasks
        per_scraper_limit = max(1, limit // len(scrapers))
        
        async def search_one(scraper: BaseScraper) -> List[AssetMetadata]:
            try:
                if use_cache:
                    return await scraper.search_with_cache(
                        query, asset_type, per_scraper_limit, **kwargs
                    )
                else:
                    return await scraper.search(
                        query, asset_type, per_scraper_limit, **kwargs
                    )
            except Exception as e:
                print(f"Scraper {scraper.source_name} failed: {e}")
                return []
        
        # Execute searches in parallel
        results_lists = await asyncio.gather(
            *[search_one(scraper) for scraper in scrapers],
            return_exceptions=True
        )
        
        # Combine results
        all_results = []
        for results in results_lists:
            if isinstance(results, list):
                all_results.extend(results)
        
        return all_results[:limit]
    
    async def get_diverse_results(
        self,
        query: str,
        asset_type: AssetType,
        total_limit: int = 30,
        per_source_limit: int = 10,
        use_cache: bool = True,
        **kwargs
    ) -> List[AssetMetadata]:
        """
        Get diverse results from multiple sources.
        
        Ensures representation from different scrapers for variety.
        
        Args:
            query: Search query
            asset_type: Type of assets to search for
            total_limit: Maximum total results
            per_source_limit: Maximum results per source
            use_cache: Whether to use caching
            **kwargs: Additional search parameters
        
        Returns:
            List of diverse asset metadata
        """
        scrapers = self.get_healthy_scrapers(asset_type)
        
        if not scrapers:
            raise ValueError(f"No healthy scrapers available for {asset_type}")
        
        # Search each scraper
        async def search_one(scraper: BaseScraper) -> List[AssetMetadata]:
            try:
                if use_cache:
                    return await scraper.search_with_cache(
                        query, asset_type, per_source_limit, **kwargs
                    )
                else:
                    return await scraper.search(
                        query, asset_type, per_source_limit, **kwargs
                    )
            except Exception:
                return []
        
        results_lists = await asyncio.gather(
            *[search_one(scraper) for scraper in scrapers]
        )
        
        # Interleave results for diversity
        diverse_results = []
        max_len = max(len(r) for r in results_lists) if results_lists else 0
        
        for i in range(max_len):
            for results in results_lists:
                if i < len(results):
                    diverse_results.append(results[i])
                    if len(diverse_results) >= total_limit:
                        return diverse_results
        
        return diverse_results
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all scrapers"""
        status = {}
        
        for source_name, scraper in self.scrapers.items():
            status[source_name] = {
                "priority": self.priorities.get(source_name, ScraperPriority.MEDIUM).value,
                **scraper.get_health_stats()
            }
        
        return status
    
    async def close_all(self) -> None:
        """Close all scrapers"""
        for scraper in self.scrapers.values():
            await scraper.close()
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close_all()


# Helper function to create a fully configured scraper manager
def create_scraper_manager(
    pexels_api_key: Optional[str] = None,
    pixabay_api_key: Optional[str] = None,
    unsplash_api_key: Optional[str] = None,
    cache_manager: Optional[CacheManager] = None,
) -> ScraperManager:
    """
    Create a scraper manager with all available scrapers.
    
    Args:
        pexels_api_key: Pexels API key
        pixabay_api_key: Pixabay API key
        unsplash_api_key: Unsplash API key
        cache_manager: Optional cache manager
    
    Returns:
        Configured ScraperManager instance
    """
    manager = ScraperManager(cache_manager)
    
    # Register Pexels (HIGH priority - great videos, no attribution)
    if pexels_api_key:
        pexels_config = ScraperConfig(
            api_key=pexels_api_key,
            requests_per_minute=50,
            requests_per_hour=200,
        )
        manager.register_scraper(
            PexelsScraper(pexels_config, cache_manager),
            ScraperPriority.HIGH
        )
    
    # Register Pixabay (HIGH priority - videos, images, audio)
    if pixabay_api_key:
        pixabay_config = ScraperConfig(
            api_key=pixabay_api_key,
            requests_per_minute=100,
            requests_per_hour=5000,
        )
        manager.register_scraper(
            PixabayScraper(pixabay_config, cache_manager),
            ScraperPriority.HIGH
        )
    
    # Register Unsplash (MEDIUM priority - requires attribution)
    if unsplash_api_key:
        unsplash_config = ScraperConfig(
            api_key=unsplash_api_key,
            requests_per_minute=50,
            requests_per_hour=5000,
        )
        manager.register_scraper(
            UnsplashScraper(unsplash_config, cache_manager),
            ScraperPriority.MEDIUM
        )
    
    return manager
