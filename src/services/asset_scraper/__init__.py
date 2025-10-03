"""
Faceless YouTube - Asset Scraper Package

Multi-source asset scraper with caching, rate limiting, and proxy support.
"""

from .base_scraper import BaseScraper, ScraperConfig, AssetType, AssetMetadata
from .pexels_scraper import PexelsScraper
from .pixabay_scraper import PixabayScraper
from .unsplash_scraper import UnsplashScraper
from .scraper_manager import ScraperManager

__all__ = [
    'BaseScraper',
    'ScraperConfig',
    'AssetType',
    'AssetMetadata',
    'PexelsScraper',
    'PixabayScraper',
    'UnsplashScraper',
    'ScraperManager',
]
