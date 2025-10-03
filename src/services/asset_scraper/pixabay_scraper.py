"""
Faceless YouTube - Pixabay Scraper

Scrapes free images, videos, and audio from Pixabay API.
"""

from typing import Dict, List, Optional, Any
from urllib.parse import urlencode

from .base_scraper import (
    BaseScraper,
    ScraperConfig,
    AssetType,
    AssetMetadata,
)


class PixabayScraper(BaseScraper):
    """
    Scraper for Pixabay free stock media.
    
    API Documentation: https://pixabay.com/api/docs/
    
    Features:
    - Free API (no limits with API key)
    - Videos, images, and music
    - No attribution required
    - Commercial use allowed
    """
    
    @property
    def source_name(self) -> str:
        return "pixabay"
    
    @property
    def base_url(self) -> str:
        return "https://pixabay.com/api"
    
    async def search(
        self,
        query: str,
        asset_type: AssetType,
        limit: int = 20,
        **kwargs
    ) -> List[AssetMetadata]:
        """
        Search Pixabay for media assets.
        
        Args:
            query: Search query
            asset_type: VIDEO, IMAGE, or AUDIO
            limit: Max results (default 20, max 200 per request)
            **kwargs: Additional parameters:
                - orientation: 'horizontal', 'vertical', or 'all'
                - category: Category filter (e.g., 'nature', 'music', 'travel')
                - min_width: Minimum width
                - min_height: Minimum height
                - safesearch: Enable safe search (default True)
                - order: 'popular' or 'latest'
        
        Returns:
            List of asset metadata
        """
        if asset_type == AssetType.VIDEO:
            return await self._search_videos(query, limit, **kwargs)
        elif asset_type == AssetType.IMAGE:
            return await self._search_images(query, limit, **kwargs)
        elif asset_type == AssetType.AUDIO:
            return await self._search_audio(query, limit, **kwargs)
        else:
            raise ValueError(f"Unknown asset type: {asset_type}")
    
    async def _search_videos(
        self,
        query: str,
        limit: int = 20,
        orientation: str = "all",
        category: Optional[str] = None,
        min_width: Optional[int] = None,
        min_height: Optional[int] = None,
        safesearch: bool = True,
        order: str = "popular",
        **kwargs
    ) -> List[AssetMetadata]:
        """Search for videos"""
        if not self.config.api_key:
            raise ValueError("Pixabay API key is required")
        
        # Build query parameters
        params = {
            "key": self.config.api_key,
            "q": query,
            "per_page": min(limit, 200),
            "video_type": "all",
            "safesearch": "true" if safesearch else "false",
            "order": order,
        }
        
        if orientation != "all":
            params["orientation"] = orientation
        if category:
            params["category"] = category
        if min_width:
            params["min_width"] = min_width
        if min_height:
            params["min_height"] = min_height
        
        # Make request
        url = f"{self.base_url}/videos/?{urlencode(params)}"
        response = await self._make_request("GET", url)
        
        # Parse results
        results = []
        for video in response.get("hits", []):
            # Get best quality video
            videos = video.get("videos", {})
            
            # Prefer higher quality
            video_url = None
            width = None
            height = None
            file_size = None
            
            for quality in ["large", "medium", "small", "tiny"]:
                if quality in videos:
                    video_data = videos[quality]
                    video_url = video_data.get("url")
                    width = video_data.get("width")
                    height = video_data.get("height")
                    file_size = video_data.get("size")
                    break
            
            if not video_url:
                continue
            
            # Parse tags
            tags = video.get("tags", "").split(", ") if video.get("tags") else []
            
            metadata = AssetMetadata(
                asset_id=str(video["id"]),
                source=self.source_name,
                asset_type=AssetType.VIDEO,
                url=video_url,
                preview_url=video.get("picture_id"),
                page_url=video.get("pageURL"),
                title=tags[0] if tags else query,
                tags=tags,
                duration=video.get("duration"),
                width=width,
                height=height,
                file_size=file_size,
                format="mp4",
                creator_name=video.get("user"),
                creator_url=f"https://pixabay.com/users/{video.get('user')}-{video.get('user_id')}/",
                license="Pixabay License",
                license_url="https://pixabay.com/service/license/",
                attribution_required=False,
                commercial_use=True,
                popularity=video.get("views", 0) + video.get("downloads", 0),
            )
            results.append(metadata)
        
        return results[:limit]
    
    async def _search_images(
        self,
        query: str,
        limit: int = 20,
        image_type: str = "all",
        orientation: str = "all",
        category: Optional[str] = None,
        min_width: Optional[int] = None,
        min_height: Optional[int] = None,
        safesearch: bool = True,
        order: str = "popular",
        **kwargs
    ) -> List[AssetMetadata]:
        """Search for images"""
        if not self.config.api_key:
            raise ValueError("Pixabay API key is required")
        
        params = {
            "key": self.config.api_key,
            "q": query,
            "per_page": min(limit, 200),
            "image_type": image_type,
            "safesearch": "true" if safesearch else "false",
            "order": order,
        }
        
        if orientation != "all":
            params["orientation"] = orientation
        if category:
            params["category"] = category
        if min_width:
            params["min_width"] = min_width
        if min_height:
            params["min_height"] = min_height
        
        url = f"{self.base_url}/?{urlencode(params)}"
        response = await self._make_request("GET", url)
        
        results = []
        for image in response.get("hits", []):
            tags = image.get("tags", "").split(", ") if image.get("tags") else []
            
            metadata = AssetMetadata(
                asset_id=str(image["id"]),
                source=self.source_name,
                asset_type=AssetType.IMAGE,
                url=image.get("largeImageURL") or image.get("webformatURL"),
                preview_url=image.get("previewURL"),
                page_url=image.get("pageURL"),
                title=tags[0] if tags else query,
                tags=tags,
                width=image.get("imageWidth"),
                height=image.get("imageHeight"),
                file_size=image.get("imageSize"),
                format="jpg",
                creator_name=image.get("user"),
                creator_url=f"https://pixabay.com/users/{image.get('user')}-{image.get('user_id')}/",
                license="Pixabay License",
                license_url="https://pixabay.com/service/license/",
                attribution_required=False,
                commercial_use=True,
                popularity=image.get("views", 0) + image.get("downloads", 0),
            )
            results.append(metadata)
        
        return results[:limit]
    
    async def _search_audio(
        self,
        query: str,
        limit: int = 20,
        category: Optional[str] = None,
        order: str = "popular",
        **kwargs
    ) -> List[AssetMetadata]:
        """Search for music/audio"""
        if not self.config.api_key:
            raise ValueError("Pixabay API key is required")
        
        params = {
            "key": self.config.api_key,
            "q": query,
            "per_page": min(limit, 200),
            "order": order,
        }
        
        if category:
            params["category"] = category
        
        # Note: Pixabay music API is at /music/ endpoint
        url = f"https://pixabay.com/api/music/?{urlencode(params)}"
        response = await self._make_request("GET", url)
        
        results = []
        for audio in response.get("hits", []):
            tags = audio.get("tags", "").split(", ") if audio.get("tags") else []
            
            metadata = AssetMetadata(
                asset_id=str(audio["id"]),
                source=self.source_name,
                asset_type=AssetType.AUDIO,
                url=audio.get("audio"),
                preview_url=audio.get("preview"),
                page_url=audio.get("pageURL"),
                title=audio.get("name", tags[0] if tags else query),
                tags=tags,
                duration=audio.get("duration"),
                format="mp3",
                creator_name=audio.get("artist"),
                creator_url=f"https://pixabay.com/users/{audio.get('artist')}-{audio.get('user_id')}/",
                license="Pixabay License",
                license_url="https://pixabay.com/service/license/",
                attribution_required=False,
                commercial_use=True,
            )
            results.append(metadata)
        
        return results[:limit]
