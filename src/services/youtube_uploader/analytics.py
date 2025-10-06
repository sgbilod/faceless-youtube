"""
YouTube Analytics Tracker

Tracks video and channel performance:
- Video statistics (views, likes, comments, watch time)
- Channel statistics (subscribers, total views)
- Performance metrics over time
- Engagement analysis
- Revenue tracking (if monetized)
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from pydantic import BaseModel, Field

from .auth_manager import AuthManager

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Metric types"""
    VIEWS = "views"
    WATCH_TIME = "estimatedMinutesWatched"
    AVERAGE_VIEW_DURATION = "averageViewDuration"
    LIKES = "likes"
    DISLIKES = "dislikes"
    COMMENTS = "comments"
    SHARES = "shares"
    SUBSCRIBERS_GAINED = "subscribersGained"
    SUBSCRIBERS_LOST = "subscribersLost"
    REVENUE = "estimatedRevenue"


@dataclass
class AnalyticsConfig:
    """Analytics configuration"""
    cache_duration_minutes: int = 60
    include_revenue: bool = False  # Requires monetization
    default_metrics: List[MetricType] = None
    
    def __post_init__(self):
        if self.default_metrics is None:
            self.default_metrics = [
                MetricType.VIEWS,
                MetricType.WATCH_TIME,
                MetricType.LIKES,
                MetricType.COMMENTS
            ]


class VideoStats(BaseModel):
    """Video statistics"""
    video_id: str
    title: str
    published_at: datetime
    
    # View metrics
    views: int = 0
    watch_time_minutes: int = 0
    average_view_duration_seconds: int = 0
    
    # Engagement metrics
    likes: int = 0
    dislikes: int = 0
    comments: int = 0
    shares: int = 0
    
    # Engagement rates
    like_rate: float = 0.0  # likes / views
    comment_rate: float = 0.0  # comments / views
    engagement_rate: float = 0.0  # (likes + comments) / views
    
    # Traffic sources (top 5)
    traffic_sources: Dict[str, int] = Field(default_factory=dict)
    
    # Demographics (top countries)
    top_countries: Dict[str, int] = Field(default_factory=dict)
    
    # Retention
    average_percentage_viewed: float = 0.0
    
    # Revenue (if monetized)
    estimated_revenue: Optional[float] = None
    
    # Updated timestamp
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ChannelStats(BaseModel):
    """Channel statistics"""
    channel_id: str
    channel_title: str
    
    # Subscriber metrics
    subscribers: int = 0
    subscribers_gained_30d: int = 0
    subscribers_lost_30d: int = 0
    net_subscribers_30d: int = 0
    
    # View metrics
    total_views: int = 0
    views_30d: int = 0
    watch_time_hours_30d: int = 0
    
    # Engagement metrics
    likes_30d: int = 0
    comments_30d: int = 0
    shares_30d: int = 0
    
    # Video metrics
    total_videos: int = 0
    videos_published_30d: int = 0
    
    # Revenue (if monetized)
    estimated_revenue_30d: Optional[float] = None
    
    # Updated timestamp
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PerformanceMetrics(BaseModel):
    """Performance metrics over time with time-series data"""
    video_id: Optional[str] = None
    channel_id: Optional[str] = None
    start_date: datetime
    end_date: datetime
    
    # Time-series data (lists of values, one per day)
    daily_views: List[int] = Field(default_factory=list)
    daily_watch_time: List[int] = Field(default_factory=list)
    daily_subscribers_gained: List[int] = Field(default_factory=list)
    
    # Totals for period
    total_views: int = 0
    total_watch_time_minutes: int = 0
    total_likes: int = 0
    total_comments: int = 0
    total_shares: int = 0
    total_subscribers_gained: int = 0
    total_subscribers_lost: int = 0
    
    # Averages
    average_daily_views: float = 0.0
    average_engagement_rate: float = 0.0


class AnalyticsTracker:
    """
    YouTube analytics tracker
    
    Features:
    - Video statistics (views, watch time, engagement)
    - Channel statistics (subscribers, total views)
    - Performance metrics over time
    - Traffic source analysis
    - Demographic analysis
    - Revenue tracking (if monetized)
    
    Example:
        tracker = AnalyticsTracker(auth_manager=auth)
        
        # Get video stats
        stats = await tracker.get_video_stats(
            account_name="main",
            video_id="abc123"
        )
        
        print(f"Views: {stats.views}")
        print(f"Likes: {stats.likes}")
        print(f"Engagement: {stats.engagement_rate:.2%}")
        
        # Get channel stats
        channel_stats = await tracker.get_channel_stats("main")
        print(f"Subscribers: {channel_stats.subscribers}")
        
        # Get performance over time
        metrics = await tracker.get_performance_metrics(
            account_name="main",
            video_id="abc123",
            days=30
        )
    """
    
    def __init__(
        self,
        auth_manager: AuthManager,
        config: Optional[AnalyticsConfig] = None
    ):
        self.auth_manager = auth_manager
        self.config = config or AnalyticsConfig()
        self._cache: Dict[str, Any] = {}
    
    async def get_video_stats(
        self,
        account_name: str,
        video_id: str,
        use_cache: bool = True
    ) -> VideoStats:
        """
        Get video statistics
        
        Args:
            account_name: Account name
            video_id: Video ID
            use_cache: Use cached data if available
        
        Returns:
            VideoStats with current statistics
        """
        # Check cache
        cache_key = f"video_stats:{video_id}"
        if use_cache and cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if datetime.utcnow() - cached_time < timedelta(minutes=self.config.cache_duration_minutes):
                return cached_data
        
        youtube = await self.auth_manager.get_youtube_client(account_name)
        
        # Get video details
        video_list = youtube.videos().list(
            part="snippet,statistics",
            id=video_id
        )
        video_response = await asyncio.to_thread(video_list.execute)
        
        if not video_response.get("items"):
            raise ValueError(f"Video not found: {video_id}")
        
        video = video_response["items"][0]
        snippet = video["snippet"]
        statistics = video["statistics"]
        
        # Get analytics data (requires YouTube Analytics API)
        try:
            analytics_data = await self._get_video_analytics(
                account_name,
                video_id,
                days=30
            )
        except Exception as e:
            logger.warning(f"Failed to get analytics data: {e}")
            analytics_data = {}
        
        # Calculate engagement rates
        views = int(statistics.get("viewCount", 0))
        likes = int(statistics.get("likeCount", 0))
        comments = int(statistics.get("commentCount", 0))
        
        like_rate = likes / views if views > 0 else 0
        comment_rate = comments / views if views > 0 else 0
        engagement_rate = (likes + comments) / views if views > 0 else 0
        
        # Create stats object
        stats = VideoStats(
            video_id=video_id,
            title=snippet["title"],
            published_at=datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00")),
            views=views,
            likes=likes,
            dislikes=int(statistics.get("dislikeCount", 0)),
            comments=comments,
            like_rate=like_rate,
            comment_rate=comment_rate,
            engagement_rate=engagement_rate,
            watch_time_minutes=analytics_data.get("watch_time_minutes", 0),
            average_view_duration_seconds=analytics_data.get("average_view_duration", 0),
            traffic_sources=analytics_data.get("traffic_sources", {}),
            top_countries=analytics_data.get("top_countries", {}),
            average_percentage_viewed=analytics_data.get("average_percentage_viewed", 0.0),
            estimated_revenue=analytics_data.get("revenue") if self.config.include_revenue else None
        )
        
        # Cache
        self._cache[cache_key] = (stats, datetime.utcnow())
        
        return stats
    
    async def _get_video_analytics(
        self,
        account_name: str,
        video_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get video analytics data from YouTube Analytics API v2"""
        try:
            from googleapiclient.discovery import build
            
            # Get authenticated credentials
            credentials = await self.auth_manager.get_credentials(account_name)
            if not credentials:
                logger.warning(f"No credentials for {account_name}")
                return {}
            
            # Build YouTube Analytics service
            youtube_analytics = build(
                "youtubeAnalytics", "v2",
                credentials=credentials,
                cache_discovery=False
            )
            
            # Calculate date range
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=days)
            
            # Query analytics data
            response = youtube_analytics.reports().query(
                ids=f"channel==MINE",
                startDate=start_date.isoformat(),
                endDate=end_date.isoformat(),
                metrics="views,estimatedMinutesWatched,likes,comments,shares,subscribersGained",
                dimensions="day",
                filters=f"video=={video_id}",
                sort="day"
            ).execute()
            
            # Parse time-series data
            analytics_data = {
                "video_id": video_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "time_series": [],
                "totals": {}
            }
            
            if "rows" in response:
                # Process time-series data
                for row in response["rows"]:
                    analytics_data["time_series"].append({
                        "date": row[0],
                        "views": row[1],
                        "watch_time_minutes": row[2],
                        "likes": row[3],
                        "comments": row[4],
                        "shares": row[5],
                        "subscribers_gained": row[6]
                    })
                
                # Calculate totals
                analytics_data["totals"] = {
                    "views": sum(row[1] for row in response["rows"]),
                    "watch_time_minutes": sum(row[2] for row in response["rows"]),
                    "likes": sum(row[3] for row in response["rows"]),
                    "comments": sum(row[4] for row in response["rows"]),
                    "shares": sum(row[5] for row in response["rows"]),
                    "subscribers_gained": sum(row[6] for row in response["rows"])
                }
            
            logger.info(f"Retrieved analytics for video {video_id}: {len(analytics_data['time_series'])} data points")
            return analytics_data
            
        except Exception as e:
            logger.error(f"Failed to get video analytics: {e}", exc_info=True)
            return {}
    
    async def get_channel_stats(
        self,
        account_name: str,
        use_cache: bool = True
    ) -> ChannelStats:
        """
        Get channel statistics
        
        Args:
            account_name: Account name
            use_cache: Use cached data if available
        
        Returns:
            ChannelStats with current statistics
        """
        # Check cache
        cache_key = f"channel_stats:{account_name}"
        if use_cache and cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if datetime.utcnow() - cached_time < timedelta(minutes=self.config.cache_duration_minutes):
                return cached_data
        
        youtube = await self.auth_manager.get_youtube_client(account_name)
        
        # Get channel details
        channel_list = youtube.channels().list(
            part="snippet,statistics,contentDetails",
            mine=True
        )
        channel_response = await asyncio.to_thread(channel_list.execute)
        
        if not channel_response.get("items"):
            raise ValueError("Channel not found")
        
        channel = channel_response["items"][0]
        snippet = channel["snippet"]
        statistics = channel["statistics"]
        
        # Get 30-day analytics
        try:
            analytics_data = await self._get_channel_analytics(
                account_name,
                days=30
            )
        except Exception as e:
            logger.warning(f"Failed to get channel analytics: {e}")
            analytics_data = {}
        
        # Create stats object
        stats = ChannelStats(
            channel_id=channel["id"],
            channel_title=snippet["title"],
            subscribers=int(statistics.get("subscriberCount", 0)),
            total_views=int(statistics.get("viewCount", 0)),
            total_videos=int(statistics.get("videoCount", 0)),
            subscribers_gained_30d=analytics_data.get("subscribers_gained", 0),
            subscribers_lost_30d=analytics_data.get("subscribers_lost", 0),
            net_subscribers_30d=analytics_data.get("net_subscribers", 0),
            views_30d=analytics_data.get("views", 0),
            watch_time_hours_30d=analytics_data.get("watch_time_hours", 0),
            likes_30d=analytics_data.get("likes", 0),
            comments_30d=analytics_data.get("comments", 0),
            shares_30d=analytics_data.get("shares", 0),
            videos_published_30d=analytics_data.get("videos_published", 0),
            estimated_revenue_30d=analytics_data.get("revenue") if self.config.include_revenue else None
        )
        
        # Cache
        self._cache[cache_key] = (stats, datetime.utcnow())
        
        return stats
    
    async def _get_channel_analytics(
        self,
        account_name: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get channel analytics data from YouTube Analytics API v2"""
        try:
            from googleapiclient.discovery import build
            
            # Get authenticated credentials
            credentials = await self.auth_manager.get_credentials(account_name)
            if not credentials:
                logger.warning(f"No credentials for {account_name}")
                return {}
            
            # Build YouTube Analytics service
            youtube_analytics = build(
                "youtubeAnalytics", "v2",
                credentials=credentials,
                cache_discovery=False
            )
            
            # Calculate date range
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=days)
            
            # Query channel analytics
            response = youtube_analytics.reports().query(
                ids="channel==MINE",
                startDate=start_date.isoformat(),
                endDate=end_date.isoformat(),
                metrics="views,estimatedMinutesWatched,likes,comments,shares,subscribersGained,subscribersLost",
                dimensions="day",
                sort="day"
            ).execute()
            
            # Parse time-series data
            analytics_data = {
                "account_name": account_name,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "time_series": [],
                "totals": {}
            }
            
            if "rows" in response:
                # Process time-series data
                for row in response["rows"]:
                    analytics_data["time_series"].append({
                        "date": row[0],
                        "views": row[1],
                        "watch_time_minutes": row[2],
                        "likes": row[3],
                        "comments": row[4],
                        "shares": row[5],
                        "subscribers_gained": row[6],
                        "subscribers_lost": row[7]
                    })
                
                # Calculate totals
                analytics_data["totals"] = {
                    "views": sum(row[1] for row in response["rows"]),
                    "watch_time_minutes": sum(row[2] for row in response["rows"]),
                    "likes": sum(row[3] for row in response["rows"]),
                    "comments": sum(row[4] for row in response["rows"]),
                    "shares": sum(row[5] for row in response["rows"]),
                    "subscribers_gained": sum(row[6] for row in response["rows"]),
                    "subscribers_lost": sum(row[7] for row in response["rows"]),
                    "net_subscribers": sum(row[6] - row[7] for row in response["rows"])
                }
            
            logger.info(f"Retrieved channel analytics for {account_name}: {len(analytics_data['time_series'])} data points")
            return analytics_data
            
        except Exception as e:
            logger.error(f"Failed to get channel analytics: {e}", exc_info=True)
            return {}
    
    async def get_performance_metrics(
        self,
        account_name: str,
        video_id: Optional[str] = None,
        days: int = 30
    ) -> PerformanceMetrics:
        """
        Get performance metrics over time with time-series data from Analytics API
        
        Args:
            account_name: Account name
            video_id: Optional video ID (if None, returns channel metrics)
            days: Number of days to analyze
        
        Returns:
            PerformanceMetrics with daily breakdown and time-series data
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        if video_id:
            # Get video analytics with time-series data
            analytics_data = await self._get_video_analytics(account_name, video_id, days)
            
            if analytics_data and \"totals\" in analytics_data:
                # Use Analytics API time-series data
                totals = analytics_data[\"totals\"]
                time_series = analytics_data.get(\"time_series\", [])
                
                # Calculate engagement rate
                views = totals.get(\"views\", 0)
                likes = totals.get(\"likes\", 0)
                comments = totals.get(\"comments\", 0)
                engagement_rate = ((likes + comments) / views * 100) if views > 0 else 0.0
                
                return PerformanceMetrics(
                    video_id=video_id,
                    start_date=start_date,
                    end_date=end_date,
                    total_views=views,
                    total_watch_time_minutes=totals.get(\"watch_time_minutes\", 0),
                    total_likes=likes,
                    total_comments=comments,
                    total_shares=totals.get(\"shares\", 0),
                    average_engagement_rate=engagement_rate,
                    daily_views=[point[\"views\"] for point in time_series],
                    daily_watch_time=[point[\"watch_time_minutes\"] for point in time_series]
                )
            else:
                # Fallback to basic video stats if Analytics API fails
                stats = await self.get_video_stats(account_name, video_id)
                
                return PerformanceMetrics(
                    video_id=video_id,
                    start_date=start_date,
                    end_date=end_date,
                    total_views=stats.views,
                    total_watch_time_minutes=stats.watch_time_minutes,
                    total_likes=stats.likes,
                    total_comments=stats.comments,
                    average_engagement_rate=stats.engagement_rate
                )
        else:
            # Get channel analytics with time-series data
            analytics_data = await self._get_channel_analytics(account_name, days)
            
            if analytics_data and \"totals\" in analytics_data:
                # Use Analytics API time-series data
                totals = analytics_data[\"totals\"]
                time_series = analytics_data.get(\"time_series\", [])
                
                return PerformanceMetrics(
                    channel_id=account_name,
                    start_date=start_date,
                    end_date=end_date,
                    total_views=totals.get(\"views\", 0),
                    total_watch_time_minutes=totals.get(\"watch_time_minutes\", 0),
                    total_likes=totals.get(\"likes\", 0),
                    total_comments=totals.get(\"comments\", 0),
                    total_shares=totals.get(\"shares\", 0),
                    total_subscribers_gained=totals.get(\"subscribers_gained\", 0),
                    total_subscribers_lost=totals.get(\"subscribers_lost\", 0),
                    average_daily_views=totals.get(\"views\", 0) / days if days > 0 else 0,
                    daily_views=[point[\"views\"] for point in time_series],
                    daily_watch_time=[point[\"watch_time_minutes\"] for point in time_series],
                    daily_subscribers_gained=[point[\"subscribers_gained\"] for point in time_series]
                )
            else:
                # Fallback to basic channel stats if Analytics API fails
                stats = await self.get_channel_stats(account_name)
                
                return PerformanceMetrics(
                    channel_id=stats.channel_id,
                    start_date=start_date,
                    end_date=end_date,
                    total_views=stats.views_30d,
                    total_watch_time_minutes=stats.watch_time_hours_30d * 60,
                    total_likes=stats.likes_30d,
                    total_comments=stats.comments_30d,
                    total_subscribers_gained=stats.subscribers_gained_30d,
                    average_daily_views=stats.views_30d / days if days > 0 else 0
                )
    
    async def get_top_videos(
        self,
        account_name: str,
        max_results: int = 10,
        order_by: str = "viewCount"  # viewCount, rating, relevance, date
    ) -> List[VideoStats]:
        """
        Get top performing videos
        
        Args:
            account_name: Account name
            max_results: Maximum number of videos
            order_by: Sort order
        
        Returns:
            List of VideoStats for top videos
        """
        youtube = await self.auth_manager.get_youtube_client(account_name)
        
        # Get channel's videos
        search_list = youtube.search().list(
            part="id",
            forMine=True,
            type="video",
            maxResults=max_results,
            order=order_by
        )
        search_response = await asyncio.to_thread(search_list.execute)
        
        # Get stats for each video
        video_ids = [item["id"]["videoId"] for item in search_response.get("items", [])]
        
        stats_list = []
        for video_id in video_ids:
            try:
                stats = await self.get_video_stats(account_name, video_id)
                stats_list.append(stats)
            except Exception as e:
                logger.warning(f"Failed to get stats for video {video_id}: {e}")
        
        return stats_list
    
    async def get_recent_comments(
        self,
        account_name: str,
        video_id: Optional[str] = None,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get recent comments
        
        Args:
            account_name: Account name
            video_id: Optional video ID (if None, returns all channel comments)
            max_results: Maximum number of comments
        
        Returns:
            List of comment dictionaries
        """
        youtube = await self.auth_manager.get_youtube_client(account_name)
        
        params = {
            "part": "snippet",
            "maxResults": max_results,
            "textFormat": "plainText"
        }
        
        if video_id:
            params["videoId"] = video_id
        else:
            params["allThreadsRelatedToChannelId"] = (
                await self.get_channel_stats(account_name)
            ).channel_id
        
        comments_list = youtube.commentThreads().list(**params)
        response = await asyncio.to_thread(comments_list.execute)
        
        comments = []
        for item in response.get("items", []):
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "comment_id": item["id"],
                "video_id": snippet.get("videoId"),
                "author": snippet["authorDisplayName"],
                "text": snippet["textDisplay"],
                "like_count": snippet["likeCount"],
                "published_at": datetime.fromisoformat(
                    snippet["publishedAt"].replace("Z", "+00:00")
                ),
                "updated_at": datetime.fromisoformat(
                    snippet["updatedAt"].replace("Z", "+00:00")
                )
            })
        
        return comments
    
    async def compare_videos(
        self,
        account_name: str,
        video_ids: List[str]
    ) -> Dict[str, VideoStats]:
        """
        Compare multiple videos
        
        Args:
            account_name: Account name
            video_ids: List of video IDs to compare
        
        Returns:
            Dictionary mapping video IDs to VideoStats
        """
        comparison = {}
        
        for video_id in video_ids:
            try:
                stats = await self.get_video_stats(account_name, video_id)
                comparison[video_id] = stats
            except Exception as e:
                logger.warning(f"Failed to get stats for video {video_id}: {e}")
        
        return comparison
    
    def clear_cache(self):
        """Clear analytics cache"""
        self._cache.clear()
        logger.info("Analytics cache cleared")
