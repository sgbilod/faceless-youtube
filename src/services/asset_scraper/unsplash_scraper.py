"""
Faceless YouTube - Unsplash Scraper

Scrapes free high-quality images from Unsplash API.
"""

from typing import Dict, List, Optional, Any
from urllib.parse import urlencode

from .base_scraper import (
    BaseScraper,
    ScraperConfig,
    AssetType,
    AssetMetadata,
)


class UnsplashScraper(BaseScraper):
    """
    Scraper for Unsplash free stock photos.
    
    API Documentation: https://unsplash.com/documentation
    
    Features:
    - Free API (50 requests/hour demo, 5000/hour production)
    - High-quality professional photography
    - Attribution required (photographer name + Unsplash)
    - Commercial use allowed
    """
    
    @property
    def source_name(self) -> str:
        return "unsplash"
    
    @property
    def base_url(self) -> str:
        return "https://api.unsplash.com"
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with API key"""
        if not self.config.api_key:
            raise ValueError("Unsplash API key (Access Key) is required")
        
        return {
            "Authorization": f"Client-ID {self.config.api_key}",
        }
    
    async def search(
        self,
        query: str,
        asset_type: AssetType,
        limit: int = 20,
        **kwargs
    ) -> List[AssetMetadata]:
        """
        Search Unsplash for images.
        
        Args:
            query: Search query
            asset_type: Must be IMAGE (Unsplash only has photos)
            limit: Max results (default 20, max 30 per request)
            **kwargs: Additional parameters:
                - orientation: 'landscape', 'portrait', or 'squarish'
                - color: Color filter (e.g., 'black_and_white', 'red', 'blue')
                - order_by: 'relevant' or 'latest'
        
        Returns:
            List of asset metadata
        """
        if asset_type != AssetType.IMAGE:
            raise ValueError(f"Unsplash only supports images, not {asset_type}")
        
        return await self._search_photos(query, limit, **kwargs)
    
    async def _search_photos(
        self,
        query: str,
        limit: int = 20,
        orientation: Optional[str] = None,
        color: Optional[str] = None,
        order_by: str = "relevant",
        **kwargs
    ) -> List[AssetMetadata]:
        """Search for photos"""
        # Build query parameters
        params = {
            "query": query,
            "per_page": min(limit, 30),  # Max 30 per request
            "order_by": order_by,
        }
        
        if orientation:
            params["orientation"] = orientation
        if color:
            params["color"] = color
        
        # Make request
        url = f"{self.base_url}/search/photos?{urlencode(params)}"
        response = await self._make_request("GET", url, headers=self._get_headers())
        
        # Parse results
        results = []
        for photo in response.get("results", []):
            # Get URLs
            urls = photo.get("urls", {})
            user = photo.get("user", {})
            
            # Extract tags
            tags = []
            for tag in photo.get("tags", []):
                if isinstance(tag, dict):
                    tags.append(tag.get("title", ""))
                else:
                    tags.append(str(tag))
            
            metadata = AssetMetadata(
                asset_id=photo["id"],
                source=self.source_name,
                asset_type=AssetType.IMAGE,
                url=urls.get("raw") or urls.get("full"),
                preview_url=urls.get("small"),
                page_url=photo.get("links", {}).get("html"),
                title=photo.get("alt_description") or photo.get("description") or query,
                description=photo.get("description"),
                tags=tags,
                width=photo.get("width"),
                height=photo.get("height"),
                format="jpg",
                creator_name=user.get("name"),
                creator_url=user.get("links", {}).get("html"),
                license="Unsplash License",
                license_url="https://unsplash.com/license",
                attribution_required=True,
                commercial_use=True,
                popularity=photo.get("likes", 0),
            )
            results.append(metadata)
        
        return results[:limit]
    
    async def get_random_photos(
        self,
        count: int = 10,
        query: Optional[str] = None,
        orientation: Optional[str] = None,
        collections: Optional[List[str]] = None,
    ) -> List[AssetMetadata]:
        """
        Get random photos from Unsplash.
        
        Args:
            count: Number of photos (max 30)
            query: Optional search query to filter random photos
            orientation: 'landscape', 'portrait', or 'squarish'
            collections: List of collection IDs to filter from
        
        Returns:
            List of random photo metadata
        """
        params = {
            "count": min(count, 30),
        }
        
        if query:
            params["query"] = query
        if orientation:
            params["orientation"] = orientation
        if collections:
            params["collections"] = ",".join(collections)
        
        url = f"{self.base_url}/photos/random?{urlencode(params)}"
        response = await self._make_request("GET", url, headers=self._get_headers())
        
        # Response can be a single photo or list
        photos = response if isinstance(response, list) else [response]
        
        results = []
        for photo in photos:
            urls = photo.get("urls", {})
            user = photo.get("user", {})
            
            tags = []
            for tag in photo.get("tags", []):
                if isinstance(tag, dict):
                    tags.append(tag.get("title", ""))
                else:
                    tags.append(str(tag))
            
            metadata = AssetMetadata(
                asset_id=photo["id"],
                source=self.source_name,
                asset_type=AssetType.IMAGE,
                url=urls.get("raw") or urls.get("full"),
                preview_url=urls.get("small"),
                page_url=photo.get("links", {}).get("html"),
                title=photo.get("alt_description") or photo.get("description") or "Random Photo",
                description=photo.get("description"),
                tags=tags,
                width=photo.get("width"),
                height=photo.get("height"),
                format="jpg",
                creator_name=user.get("name"),
                creator_url=user.get("links", {}).get("html"),
                license="Unsplash License",
                license_url="https://unsplash.com/license",
                attribution_required=True,
                commercial_use=True,
                popularity=photo.get("likes", 0),
            )
            results.append(metadata)
        
        return results
    
    async def get_curated_photos(
        self,
        limit: int = 20,
        order_by: str = "latest",
    ) -> List[AssetMetadata]:
        """
        Get curated/editorial photos from Unsplash.
        
        Args:
            limit: Max results (max 30 per request)
            order_by: 'latest' or 'oldest' or 'popular'
        
        Returns:
            List of curated photo metadata
        """
        params = {
            "per_page": min(limit, 30),
            "order_by": order_by,
        }
        
        url = f"{self.base_url}/photos?{urlencode(params)}"
        response = await self._make_request("GET", url, headers=self._get_headers())
        
        results = []
        for photo in response:
            urls = photo.get("urls", {})
            user = photo.get("user", {})
            
            tags = []
            for tag in photo.get("tags", []):
                if isinstance(tag, dict):
                    tags.append(tag.get("title", ""))
                else:
                    tags.append(str(tag))
            
            metadata = AssetMetadata(
                asset_id=photo["id"],
                source=self.source_name,
                asset_type=AssetType.IMAGE,
                url=urls.get("raw") or urls.get("full"),
                preview_url=urls.get("small"),
                page_url=photo.get("links", {}).get("html"),
                title=photo.get("alt_description") or photo.get("description") or "Curated Photo",
                description=photo.get("description"),
                tags=tags,
                width=photo.get("width"),
                height=photo.get("height"),
                format="jpg",
                creator_name=user.get("name"),
                creator_url=user.get("links", {}).get("html"),
                license="Unsplash License",
                license_url="https://unsplash.com/license",
                attribution_required=True,
                commercial_use=True,
                popularity=photo.get("likes", 0),
            )
            results.append(metadata)
        
        return results[:limit]
