"""
Faceless YouTube - Base Asset Scraper

Abstract base class for all asset scrapers with caching, rate limiting, and health monitoring.
"""

import asyncio
import hashlib
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
from urllib.parse import quote

import aiohttp
from pydantic import BaseModel, HttpUrl, Field

from src.utils.cache import CacheManager, cached


class AssetType(str, Enum):
    """Types of media assets that can be scraped"""
    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"


class AssetMetadata(BaseModel):
    """Metadata for a scraped asset"""
    
    # Core identifiers
    asset_id: str = Field(..., description="Unique ID from the source platform")
    source: str = Field(..., description="Source platform (e.g., 'pexels', 'pixabay')")
    asset_type: AssetType = Field(..., description="Type of asset")
    
    # URLs and access
    url: HttpUrl = Field(..., description="Direct download/access URL")
    preview_url: Optional[HttpUrl] = Field(None, description="Preview/thumbnail URL")
    page_url: Optional[HttpUrl] = Field(None, description="Web page URL")
    
    # Asset properties
    title: Optional[str] = Field(None, description="Asset title/name")
    description: Optional[str] = Field(None, description="Asset description")
    tags: List[str] = Field(default_factory=list, description="Associated tags/keywords")
    duration: Optional[int] = Field(None, description="Duration in seconds (for video/audio)")
    width: Optional[int] = Field(None, description="Width in pixels (for images/video)")
    height: Optional[int] = Field(None, description="Height in pixels (for images/video)")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    format: Optional[str] = Field(None, description="File format (e.g., 'mp4', 'jpg')")
    
    # Creator information
    creator_name: Optional[str] = Field(None, description="Creator/photographer name")
    creator_url: Optional[HttpUrl] = Field(None, description="Creator profile URL")
    
    # Licensing
    license: str = Field(default="unknown", description="License type")
    license_url: Optional[HttpUrl] = Field(None, description="License details URL")
    attribution_required: bool = Field(default=True, description="Whether attribution is required")
    commercial_use: bool = Field(default=False, description="Whether commercial use is allowed")
    
    # Metadata
    scraped_at: datetime = Field(default_factory=datetime.utcnow, description="When asset was scraped")
    popularity: Optional[int] = Field(None, description="Views/downloads/likes count")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


@dataclass
class ScraperConfig:
    """Configuration for a scraper instance"""
    
    # API credentials (optional for free sources)
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    
    # Rate limiting
    requests_per_minute: int = 60
    requests_per_hour: int = 3600
    
    # Retry configuration
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds
    retry_backoff: float = 2.0  # exponential backoff multiplier
    
    # Timeout settings
    request_timeout: int = 30  # seconds
    
    # Proxy configuration
    proxy_url: Optional[str] = None
    proxy_auth: Optional[Dict[str, str]] = None
    
    # Caching
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 1 hour default
    
    # Health check
    health_check_interval: int = 300  # 5 minutes
    max_consecutive_failures: int = 5


class RateLimiter:
    """Token bucket rate limiter for API requests"""
    
    def __init__(self, requests_per_minute: int, requests_per_hour: int):
        self.rpm = requests_per_minute
        self.rph = requests_per_hour
        
        # Token buckets
        self.minute_tokens = requests_per_minute
        self.hour_tokens = requests_per_hour
        
        # Last refill times
        self.last_minute_refill = time.time()
        self.last_hour_refill = time.time()
        
        self.lock = asyncio.Lock()
    
    async def acquire(self) -> None:
        """Acquire permission to make a request, blocking if necessary"""
        async with self.lock:
            while True:
                self._refill_tokens()
                
                if self.minute_tokens >= 1 and self.hour_tokens >= 1:
                    self.minute_tokens -= 1
                    self.hour_tokens -= 1
                    return
                
                # Calculate wait time
                wait_time = min(
                    (60 - (time.time() - self.last_minute_refill)),
                    (3600 - (time.time() - self.last_hour_refill))
                )
                
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
    
    def _refill_tokens(self) -> None:
        """Refill token buckets based on elapsed time"""
        now = time.time()
        
        # Refill minute bucket
        if now - self.last_minute_refill >= 60:
            self.minute_tokens = self.rpm
            self.last_minute_refill = now
        
        # Refill hour bucket
        if now - self.last_hour_refill >= 3600:
            self.hour_tokens = self.rph
            self.last_hour_refill = now


class HealthMonitor:
    """Monitor scraper health and track failures"""
    
    def __init__(self, max_consecutive_failures: int = 5):
        self.max_consecutive_failures = max_consecutive_failures
        self.consecutive_failures = 0
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.last_success_time: Optional[datetime] = None
        self.last_failure_time: Optional[datetime] = None
        self.is_healthy = True
    
    def record_success(self) -> None:
        """Record a successful request"""
        self.consecutive_failures = 0
        self.total_requests += 1
        self.successful_requests += 1
        self.last_success_time = datetime.utcnow()
        self.is_healthy = True
    
    def record_failure(self) -> None:
        """Record a failed request"""
        self.consecutive_failures += 1
        self.total_requests += 1
        self.failed_requests += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.consecutive_failures >= self.max_consecutive_failures:
            self.is_healthy = False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get health statistics"""
        success_rate = (
            self.successful_requests / self.total_requests * 100
            if self.total_requests > 0
            else 0
        )
        
        return {
            "is_healthy": self.is_healthy,
            "consecutive_failures": self.consecutive_failures,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": round(success_rate, 2),
            "last_success": self.last_success_time.isoformat() if self.last_success_time else None,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None,
        }


class BaseScraper(ABC):
    """
    Abstract base class for all asset scrapers.
    
    Provides:
    - Rate limiting
    - Request retry logic
    - Caching integration
    - Health monitoring
    - Proxy support
    """
    
    def __init__(self, config: ScraperConfig, cache_manager: Optional[CacheManager] = None):
        self.config = config
        self.cache_manager = cache_manager or CacheManager()
        
        # Initialize components
        self.rate_limiter = RateLimiter(
            config.requests_per_minute,
            config.requests_per_hour
        )
        self.health_monitor = HealthMonitor(config.max_consecutive_failures)
        
        # HTTP session (will be created async)
        self._session: Optional[aiohttp.ClientSession] = None
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Name of the asset source (e.g., 'pexels')"""
        pass
    
    @property
    @abstractmethod
    def base_url(self) -> str:
        """Base URL for API requests"""
        pass
    
    @property
    def cache_key_prefix(self) -> str:
        """Prefix for cache keys"""
        return f"asset_scraper:{self.source_name}"
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.request_timeout)
            
            connector_kwargs = {}
            if self.config.proxy_url:
                connector_kwargs['proxy'] = self.config.proxy_url
                if self.config.proxy_auth:
                    connector_kwargs['proxy_auth'] = aiohttp.BasicAuth(
                        self.config.proxy_auth['username'],
                        self.config.proxy_auth['password']
                    )
            
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                **connector_kwargs
            )
        
        return self._session
    
    async def close(self) -> None:
        """Close HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    def _generate_cache_key(self, query: str, **kwargs) -> str:
        """Generate a cache key for a search query"""
        # Include all parameters in cache key
        params_str = f"{query}:" + ":".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        return f"{self.cache_key_prefix}:search:{params_hash}"
    
    async def _make_request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make an HTTP request with retry logic and rate limiting.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            **kwargs: Additional arguments for aiohttp request
        
        Returns:
            Response JSON data
        
        Raises:
            aiohttp.ClientError: If request fails after all retries
        """
        # Wait for rate limiter
        await self.rate_limiter.acquire()
        
        session = await self._get_session()
        
        for attempt in range(self.config.max_retries):
            try:
                async with session.request(method, url, **kwargs) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    # Record success
                    self.health_monitor.record_success()
                    
                    return data
            
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                # Record failure
                self.health_monitor.record_failure()
                
                # Last attempt - raise error
                if attempt == self.config.max_retries - 1:
                    raise
                
                # Calculate backoff delay
                delay = self.config.retry_delay * (self.config.retry_backoff ** attempt)
                await asyncio.sleep(delay)
    
    @abstractmethod
    async def search(
        self,
        query: str,
        asset_type: AssetType,
        limit: int = 20,
        **kwargs
    ) -> List[AssetMetadata]:
        """
        Search for assets matching the query.
        
        Args:
            query: Search query string
            asset_type: Type of assets to search for
            limit: Maximum number of results
            **kwargs: Additional search parameters
        
        Returns:
            List of asset metadata
        """
        pass
    
    async def search_with_cache(
        self,
        query: str,
        asset_type: AssetType,
        limit: int = 20,
        **kwargs
    ) -> List[AssetMetadata]:
        """
        Search for assets with caching.
        
        Args:
            query: Search query string
            asset_type: Type of assets to search for
            limit: Maximum number of results
            **kwargs: Additional search parameters
        
        Returns:
            List of asset metadata
        """
        if not self.config.cache_enabled:
            return await self.search(query, asset_type, limit, **kwargs)
        
        # Generate cache key
        cache_key = self._generate_cache_key(
            query,
            asset_type=asset_type.value,
            limit=limit,
            **kwargs
        )
        
        # Try cache first
        cached_results = await self.cache_manager.get(cache_key)
        if cached_results is not None:
            # Reconstruct AssetMetadata objects from cached dicts
            return [AssetMetadata(**item) for item in cached_results]
        
        # Cache miss - fetch from source
        results = await self.search(query, asset_type, limit, **kwargs)
        
        # Cache results (convert to dicts for JSON serialization)
        results_dicts = [item.dict() for item in results]
        await self.cache_manager.set(
            cache_key,
            results_dicts,
            ttl=self.config.cache_ttl
        )
        
        return results
    
    def get_health_stats(self) -> Dict[str, Any]:
        """Get scraper health statistics"""
        return {
            "source": self.source_name,
            "health": self.health_monitor.get_stats(),
            "rate_limiter": {
                "minute_tokens": self.rate_limiter.minute_tokens,
                "hour_tokens": self.rate_limiter.hour_tokens,
            }
        }
