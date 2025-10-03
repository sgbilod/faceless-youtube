"""
Faceless YouTube - Pexels Video Scraper

Scrapes free stock videos from Pexels API.
"""

from typing import Dict, List, Optional, Any
from urllib.parse import urlencode

from .base_scraper import (
    BaseScraper,
    ScraperConfig,
    AssetType,
    AssetMetadata,
)


class PexelsScraper(BaseScraper):
    """
    Scraper for Pexels free stock videos and images.
    
    API Documentation: https://www.pexels.com/api/documentation/
    
    Features:
    - Free API with generous limits (200 requests/hour)
    - High-quality videos and images
    - No attribution required (but appreciated)
    - Commercial use allowed
    """
    
    @property
    def source_name(self) -> str:
        return "pexels"
    
    @property
    def base_url(self) -> str:
        return "https://api.pexels.com"
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with API key"""
        if not self.config.api_key:
            raise ValueError("Pexels API key is required")
        
        return {
            "Authorization": self.config.api_key,
        }
    
    async def search(
        self,
        query: str,
        asset_type: AssetType,
        limit: int = 20,
        **kwargs
    ) -> List[AssetMetadata]:
        """
        Search Pexels for videos or images.
        
        Args:
            query: Search query
            asset_type: VIDEO or IMAGE
            limit: Max results (default 20, max 80 per request)
            **kwargs: Additional parameters:
                - orientation: 'landscape', 'portrait', or 'square'
                - size: 'large', 'medium', or 'small' (images only)
                - min_width: Minimum width in pixels
                - min_height: Minimum height in pixels
                - min_duration: Minimum duration in seconds (videos only)
                - max_duration: Maximum duration in seconds (videos only)
        
        Returns:
            List of asset metadata
        """
        if asset_type == AssetType.VIDEO:
            return await self._search_videos(query, limit, **kwargs)
        elif asset_type == AssetType.IMAGE:
            return await self._search_images(query, limit, **kwargs)
        else:
            raise ValueError(f"Pexels does not support asset type: {asset_type}")
    
    async def _search_videos(
        self,
        query: str,
        limit: int = 20,
        orientation: Optional[str] = None,
        min_width: Optional[int] = None,
        min_height: Optional[int] = None,
        min_duration: Optional[int] = None,
        max_duration: Optional[int] = None,
        **kwargs
    ) -> List[AssetMetadata]:
        """Search for videos"""
        # Build query parameters
        params = {
            "query": query,
            "per_page": min(limit, 80),  # Max 80 per request
        }
        
        if orientation:
            params["orientation"] = orientation
        if min_width:
            params["min_width"] = min_width
        if min_height:
            params["min_height"] = min_height
        if min_duration:
            params["min_duration"] = min_duration
        if max_duration:
            params["max_duration"] = max_duration
        
        # Make request
        url = f"{self.base_url}/videos/search?{urlencode(params)}"
        response = await self._make_request("GET", url, headers=self._get_headers())
        
        # Parse results
        results = []
        for video in response.get("videos", []):
            # Get best quality video file
            video_files = video.get("video_files", [])
            if not video_files:
                continue
            
            # Sort by quality (higher quality first)
            video_files.sort(key=lambda x: x.get("quality", ""), reverse=True)
            best_file = video_files[0]
            
            metadata = AssetMetadata(
                asset_id=str(video["id"]),
                source=self.source_name,
                asset_type=AssetType.VIDEO,
                url=best_file["link"],
                preview_url=video.get("image"),
                page_url=video.get("url"),
                title=query,  # Pexels doesn't provide titles
                tags=[],
                duration=video.get("duration"),
                width=best_file.get("width"),
                height=best_file.get("height"),
                file_size=best_file.get("file_size"),
                format=best_file.get("file_type", "mp4"),
                creator_name=video.get("user", {}).get("name"),
                creator_url=video.get("user", {}).get("url"),
                license="Pexels License",
                license_url="https://www.pexels.com/license/",
                attribution_required=False,
                commercial_use=True,
            )
            results.append(metadata)
        
        return results[:limit]
    
    async def _search_images(
        self,
        query: str,
        limit: int = 20,
        orientation: Optional[str] = None,
        size: Optional[str] = None,
        **kwargs
    ) -> List[AssetMetadata]:
        """Search for images"""
        # Build query parameters
        params = {
            "query": query,
            "per_page": min(limit, 80),
        }
        
        if orientation:
            params["orientation"] = orientation
        if size:
            params["size"] = size
        
        # Make request
        url = f"{self.base_url}/v1/search?{urlencode(params)}"
        response = await self._make_request("GET", url, headers=self._get_headers())
        
        # Parse results
        results = []
        for photo in response.get("photos", []):
            # Get original image URL
            src = photo.get("src", {})
            
            metadata = AssetMetadata(
                asset_id=str(photo["id"]),
                source=self.source_name,
                asset_type=AssetType.IMAGE,
                url=src.get("original"),
                preview_url=src.get("medium"),
                page_url=photo.get("url"),
                title=photo.get("alt"),
                tags=[],
                width=photo.get("width"),
                height=photo.get("height"),
                format="jpg",
                creator_name=photo.get("photographer"),
                creator_url=photo.get("photographer_url"),
                license="Pexels License",
                license_url="https://www.pexels.com/license/",
                attribution_required=False,
                commercial_use=True,
            )
            results.append(metadata)
        
        return results[:limit]
    
    async def get_popular_videos(
        self,
        limit: int = 20,
        min_width: Optional[int] = None,
        min_height: Optional[int] = None,
        min_duration: Optional[int] = None,
        max_duration: Optional[int] = None,
    ) -> List[AssetMetadata]:
        """
        Get popular/curated videos from Pexels.
        
        Args:
            limit: Max results
            min_width: Minimum width
            min_height: Minimum height
            min_duration: Minimum duration in seconds
            max_duration: Maximum duration in seconds
        
        Returns:
            List of popular video metadata
        """
        params = {
            "per_page": min(limit, 80),
        }
        
        if min_width:
            params["min_width"] = min_width
        if min_height:
            params["min_height"] = min_height
        if min_duration:
            params["min_duration"] = min_duration
        if max_duration:
            params["max_duration"] = max_duration
        
        url = f"{self.base_url}/videos/popular?{urlencode(params)}"
        response = await self._make_request("GET", url, headers=self._get_headers())
        
        # Parse results (same as search)
        results = []
        for video in response.get("videos", []):
            video_files = video.get("video_files", [])
            if not video_files:
                continue
            
            video_files.sort(key=lambda x: x.get("quality", ""), reverse=True)
            best_file = video_files[0]
            
            metadata = AssetMetadata(
                asset_id=str(video["id"]),
                source=self.source_name,
                asset_type=AssetType.VIDEO,
                url=best_file["link"],
                preview_url=video.get("image"),
                page_url=video.get("url"),
                title="Popular Video",
                tags=[],
                duration=video.get("duration"),
                width=best_file.get("width"),
                height=best_file.get("height"),
                file_size=best_file.get("file_size"),
                format=best_file.get("file_type", "mp4"),
                creator_name=video.get("user", {}).get("name"),
                creator_url=video.get("user", {}).get("url"),
                license="Pexels License",
                license_url="https://www.pexels.com/license/",
                attribution_required=False,
                commercial_use=True,
            )
            results.append(metadata)
        
        return results[:limit]
