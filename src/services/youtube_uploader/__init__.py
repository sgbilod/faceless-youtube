"""
YouTube Upload Automation Service

This module provides comprehensive YouTube upload automation with:
- OAuth2 authentication with token management
- Resumable uploads with automatic retry
- Upload queue with priority and scheduling
- Video metadata management (title, description, tags, thumbnail)
- Analytics tracking for video performance
- Playlist management
- Caption/subtitle upload
- End card and info card management

Components:
- AuthManager: Handles OAuth2 authentication and token refresh
- VideoUploader: Core upload functionality with resumable uploads
- UploadQueue: Manages multiple uploads with priority and scheduling
- Analytics: Tracks video performance and channel statistics

Usage:
    from services.youtube_uploader import VideoUploader, AuthManager
    
    # Initialize
    auth = AuthManager(client_secrets_path="client_secrets.json")
    uploader = VideoUploader(auth_manager=auth)
    
    # Upload video
    result = await uploader.upload(
        video_path="video.mp4",
        title="My Video",
        description="Video description",
        tags=["tag1", "tag2"],
        thumbnail_path="thumbnail.jpg"
    )
"""

from .auth_manager import (
    AuthManager,
    AuthConfig,
    AuthStatus,
    YouTubeCredentials
)

from .uploader import (
    VideoUploader,
    UploadConfig,
    UploadStatus,
    VideoMetadata,
    PrivacyStatus,
    Category,
    UploadResult
)

from .queue_manager import (
    UploadQueue,
    QueueConfig,
    QueueItem,
    QueuePriority,
    QueueStatus
)

from .analytics import (
    AnalyticsTracker,
    AnalyticsConfig,
    VideoStats,
    ChannelStats,
    PerformanceMetrics
)

__all__ = [
    # Authentication
    "AuthManager",
    "AuthConfig",
    "AuthStatus",
    "YouTubeCredentials",
    
    # Upload
    "VideoUploader",
    "UploadConfig",
    "UploadStatus",
    "VideoMetadata",
    "PrivacyStatus",
    "Category",
    "UploadResult",
    
    # Queue Management
    "UploadQueue",
    "QueueConfig",
    "QueueItem",
    "QueuePriority",
    "QueueStatus",
    
    # Analytics
    "AnalyticsTracker",
    "AnalyticsConfig",
    "VideoStats",
    "ChannelStats",
    "PerformanceMetrics",
]

__version__ = "1.0.0"
