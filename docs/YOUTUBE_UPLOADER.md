# YouTube Upload Automation

Complete guide for the YouTube Upload Automation service.

## Overview

The YouTube Upload Automation service provides comprehensive YouTube integration with:

- **OAuth2 Authentication**: Secure Google account authorization with token management
- **Resumable Uploads**: Handle large video files with automatic resume on failure
- **Upload Queue**: Manage multiple uploads with priority and scheduling
- **Analytics Tracking**: Monitor video and channel performance
- **Playlist Management**: Create and manage playlists programmatically
- **Caption Support**: Upload multilingual subtitles
- **Scheduling**: Schedule videos for future publication
- **Progress Tracking**: Real-time upload progress monitoring

## Table of Contents

- [Quick Start](#quick-start)
- [Setup Guide](#setup-guide)
- [Components](#components)
- [Authentication](#authentication)
- [Uploading Videos](#uploading-videos)
- [Upload Queue](#upload-queue)
- [Analytics](#analytics)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Quick Start

### Prerequisites

1. **Google Cloud Project** with YouTube Data API v3 enabled
2. **OAuth2 Credentials** (client secrets JSON file)
3. **Python 3.10+** with required dependencies

### Installation

Dependencies are already in `requirements.txt`:

```bash
pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
```

### Basic Usage

```python
import asyncio
from services.youtube_uploader import (
    AuthManager,
    AuthConfig,
    VideoUploader,
    VideoMetadata,
    PrivacyStatus,
    Category
)

async def upload_video():
    # Initialize authentication
    auth = AuthManager(AuthConfig(
        client_secrets_path="client_secrets.json"
    ))
    
    # Authenticate (first time only)
    await auth.authenticate(account_name="main")
    
    # Create uploader
    uploader = VideoUploader(auth)
    
    # Define metadata
    metadata = VideoMetadata(
        title="My Video Title",
        description="Video description here",
        tags=["tag1", "tag2", "tag3"],
        category=Category.EDUCATION,
        privacy_status=PrivacyStatus.PUBLIC
    )
    
    # Upload
    result = await uploader.upload(
        account_name="main",
        video_path="video.mp4",
        metadata=metadata,
        thumbnail_path="thumbnail.jpg"
    )
    
    print(f"Uploaded: {result.url}")

# Run
asyncio.run(upload_video())
```

## Setup Guide

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Note your project ID

### Step 2: Enable YouTube Data API

1. Navigate to **APIs & Services > Library**
2. Search for "YouTube Data API v3"
3. Click **Enable**

### Step 3: Create OAuth2 Credentials

1. Navigate to **APIs & Services > Credentials**
2. Click **Create Credentials > OAuth 2.0 Client ID**
3. Configure consent screen if prompted:
   - User Type: **External**
   - Add test users if needed
4. Application type: **Desktop app**
5. Download the JSON file
6. Rename to `client_secrets.json`
7. Place in your project root

### Step 4: First Authentication

```python
from services.youtube_uploader import AuthManager, AuthConfig

async def authenticate():
    auth = AuthManager(AuthConfig(
        client_secrets_path="client_secrets.json"
    ))
    
    # This will open browser for authorization
    credentials = await auth.authenticate(account_name="main")
    print(f"Authenticated: {credentials.channel_title}")

asyncio.run(authenticate())
```

The tokens are saved in `youtube_tokens/` and auto-refresh when needed.

## Components

### 1. AuthManager

Handles OAuth2 authentication and token management.

**Features:**
- OAuth2 web flow with browser authorization
- Token encryption and secure storage
- Automatic token refresh
- Multiple account support
- Credential validation

**Key Methods:**
- `authenticate()` - Initial OAuth2 flow
- `load_credentials()` - Load saved credentials
- `get_youtube_client()` - Get authenticated API client
- `refresh_token()` - Manual token refresh
- `list_accounts()` - List authenticated accounts

### 2. VideoUploader

Core video upload functionality with resumable uploads.

**Features:**
- Resumable uploads for large files
- Automatic retry with exponential backoff
- Progress tracking callbacks
- Thumbnail upload
- Caption/subtitle upload
- Playlist integration
- Video status monitoring

**Key Methods:**
- `upload()` - Upload video
- `upload_thumbnail()` - Upload custom thumbnail
- `update_metadata()` - Update video metadata
- `add_to_playlist()` - Add video to playlist
- `create_playlist()` - Create new playlist
- `wait_for_processing()` - Wait for video processing

### 3. UploadQueue

Manages multiple uploads with priority and scheduling.

**Features:**
- Priority-based queue (LOW, NORMAL, HIGH, URGENT)
- Concurrent upload limits
- Scheduled uploads
- Automatic retry on failure
- Progress tracking across all uploads
- Batch operations

**Key Methods:**
- `add()` - Add video to queue
- `add_batch()` - Add multiple videos
- `start()` / `stop()` - Control queue processing
- `get_status()` - Check upload status
- `wait_for_completion()` - Wait for specific upload
- `cancel()` - Cancel upload

### 4. AnalyticsTracker

Tracks video and channel performance.

**Features:**
- Video statistics (views, likes, comments, watch time)
- Channel statistics (subscribers, total views)
- Performance metrics over time
- Top videos ranking
- Comment retrieval
- Video comparison

**Key Methods:**
- `get_video_stats()` - Get video statistics
- `get_channel_stats()` - Get channel statistics
- `get_top_videos()` - Get top performing videos
- `get_recent_comments()` - Get recent comments
- `compare_videos()` - Compare multiple videos

## Authentication

### OAuth2 Flow

The authentication process:

1. **Initial Auth**: Opens browser for user authorization
2. **Token Storage**: Saves encrypted tokens locally
3. **Auto Refresh**: Automatically refreshes expired tokens
4. **Multi-Account**: Supports multiple YouTube accounts

### Configuration

```python
auth_config = AuthConfig(
    client_secrets_path="client_secrets.json",
    token_storage_path="youtube_tokens",  # Where to store tokens
    scopes=[  # YouTube API scopes
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube",
        "https://www.googleapis.com/auth/youtube.force-ssl",
    ],
    redirect_port=8080,  # Local server port
    encrypt_tokens=True,  # Encrypt stored tokens
    auto_refresh=True,  # Auto refresh expiring tokens
    refresh_threshold_minutes=10  # Refresh if < 10 min left
)
```

### Multiple Accounts

```python
# Authenticate multiple accounts
await auth.authenticate(account_name="main_channel")
await auth.authenticate(account_name="backup_channel")

# List accounts
accounts = await auth.list_accounts()

# Use specific account
await uploader.upload(
    account_name="main_channel",
    video_path="video.mp4",
    metadata=metadata
)
```

### Token Management

```python
# Check auth status
status = await auth.get_auth_status("main")

# Manual refresh
await auth.refresh_token("main")

# Remove account
await auth.remove_account("old_account")
```

## Uploading Videos

### Basic Upload

```python
metadata = VideoMetadata(
    title="Video Title",
    description="Video description",
    tags=["tag1", "tag2"],
    category=Category.EDUCATION,
    privacy_status=PrivacyStatus.PUBLIC
)

result = await uploader.upload(
    account_name="main",
    video_path="video.mp4",
    metadata=metadata
)

print(f"Video ID: {result.video_id}")
print(f"URL: {result.url}")
```

### With Thumbnail

```python
result = await uploader.upload(
    account_name="main",
    video_path="video.mp4",
    metadata=metadata,
    thumbnail_path="thumbnail.jpg"  # JPG or PNG, max 2MB
)
```

### With Progress Tracking

```python
def progress_callback(percent: float):
    print(f"Progress: {percent:.1f}%")

result = await uploader.upload(
    account_name="main",
    video_path="video.mp4",
    metadata=metadata,
    progress_callback=progress_callback
)
```

### With Captions

```python
captions = [
    {"file": "captions_en.srt", "language": "en", "name": "English"},
    {"file": "captions_es.srt", "language": "es", "name": "Spanish"}
]

result = await uploader.upload(
    account_name="main",
    video_path="video.mp4",
    metadata=metadata,
    captions=captions
)
```

### Scheduled Upload

```python
from datetime import datetime, timedelta

publish_time = datetime.now() + timedelta(days=1)

metadata = VideoMetadata(
    title="Scheduled Video",
    description="Will publish tomorrow",
    privacy_status=PrivacyStatus.PRIVATE,
    publish_at=publish_time  # Schedule publish time
)

result = await uploader.upload(
    account_name="main",
    video_path="video.mp4",
    metadata=metadata
)
```

## Upload Queue

### Basic Queue Usage

```python
from services.youtube_uploader import UploadQueue, QueueConfig, QueuePriority

queue = UploadQueue(
    auth_manager=auth,
    uploader=uploader,
    config=QueueConfig(
        max_concurrent_uploads=2,
        auto_start=True
    )
)

# Add videos
item_id = await queue.add(
    account_name="main",
    video_path="video.mp4",
    metadata=metadata,
    priority=QueuePriority.HIGH
)

# Wait for completion
result = await queue.wait_for_completion(item_id)
```

### Batch Upload

```python
videos = [
    {
        "account_name": "main",
        "video_path": "video1.mp4",
        "metadata": metadata1,
        "priority": QueuePriority.HIGH
    },
    {
        "account_name": "main",
        "video_path": "video2.mp4",
        "metadata": metadata2,
        "priority": QueuePriority.NORMAL
    }
]

item_ids = await queue.add_batch(videos)

# Monitor progress
summary = queue.get_queue_summary()
print(f"Queued: {summary['status_counts']['queued']}")
print(f"Active: {summary['active_uploads']}")
print(f"Completed: {summary['status_counts']['completed']}")
```

### Priority System

- **URGENT**: Upload immediately (skip queue)
- **HIGH**: High priority (process before normal)
- **NORMAL**: Default priority
- **LOW**: Low priority (process last)

### Queue Management

```python
# Start/stop processing
await queue.start()
await queue.stop()

# Cancel upload
await queue.cancel(item_id)

# Retry failed upload
await queue.retry(item_id)

# Clear completed items
await queue.clear_completed()
```

## Analytics

### Video Statistics

```python
tracker = AnalyticsTracker(auth)

stats = await tracker.get_video_stats(
    account_name="main",
    video_id="abc123"
)

print(f"Views: {stats.views:,}")
print(f"Likes: {stats.likes:,}")
print(f"Comments: {stats.comments:,}")
print(f"Watch time: {stats.watch_time_minutes:,} min")
print(f"Engagement rate: {stats.engagement_rate:.2%}")
```

### Channel Statistics

```python
channel_stats = await tracker.get_channel_stats("main")

print(f"Subscribers: {channel_stats.subscribers:,}")
print(f"Total views: {channel_stats.total_views:,}")
print(f"Videos: {channel_stats.total_videos}")
print(f"Subscribers (30d): +{channel_stats.subscribers_gained_30d:,}")
```

### Top Videos

```python
top_videos = await tracker.get_top_videos(
    account_name="main",
    max_results=10,
    order_by="viewCount"  # viewCount, rating, date
)

for video in top_videos:
    print(f"{video.title}: {video.views:,} views")
```

### Recent Comments

```python
comments = await tracker.get_recent_comments(
    account_name="main",
    video_id="abc123",  # Optional, None for all channel comments
    max_results=50
)

for comment in comments:
    print(f"{comment['author']}: {comment['text']}")
```

## Configuration

### Upload Configuration

```python
upload_config = UploadConfig(
    chunk_size=1024 * 1024 * 10,  # 10MB chunks
    max_retries=5,
    retry_delay_seconds=2,
    timeout_seconds=600,
    notify_subscribers=True,  # Notify subscribers of new video
    auto_levels=True,  # Auto color correction
    stabilize=False,  # Video stabilization
    default_privacy=PrivacyStatus.PRIVATE,
    default_category=Category.EDUCATION,
    default_language="en"
)
```

### Queue Configuration

```python
queue_config = QueueConfig(
    max_concurrent_uploads=2,  # Max parallel uploads
    retry_failed_uploads=True,  # Auto retry failed uploads
    max_retries=3,  # Max retry attempts
    retry_delay_minutes=5,  # Delay between retries
    auto_start=True,  # Auto start processing
    cleanup_completed=True,  # Remove completed items
    cleanup_after_hours=24  # Remove after 24 hours
)
```

### Analytics Configuration

```python
analytics_config = AnalyticsConfig(
    cache_duration_minutes=60,  # Cache stats for 1 hour
    include_revenue=False,  # Include revenue (needs monetization)
    default_metrics=[
        MetricType.VIEWS,
        MetricType.WATCH_TIME,
        MetricType.LIKES,
        MetricType.COMMENTS
    ]
)
```

## API Reference

### VideoMetadata

```python
VideoMetadata(
    title: str,  # 1-100 characters
    description: str = None,  # Max 5000 characters
    tags: List[str] = [],  # Max 500 total characters
    category: Category = Category.EDUCATION,
    privacy_status: PrivacyStatus = PrivacyStatus.PRIVATE,
    language: str = "en",
    embeddable: bool = True,
    public_stats_viewable: bool = True,
    made_for_kids: bool = False,
    publish_at: datetime = None,  # Schedule publish
    playlist_id: str = None  # Auto-add to playlist
)
```

### UploadResult

```python
UploadResult(
    video_id: str,  # YouTube video ID
    url: str,  # Video URL
    title: str,
    status: UploadStatus,
    uploaded_at: datetime,
    file_size_bytes: int,
    duration_seconds: float,
    upload_time_seconds: float,
    privacy_status: PrivacyStatus,
    thumbnail_url: str = None,
    playlist_id: str = None
)
```

### VideoStats

```python
VideoStats(
    video_id: str,
    title: str,
    published_at: datetime,
    views: int,
    watch_time_minutes: int,
    likes: int,
    comments: int,
    like_rate: float,  # likes / views
    comment_rate: float,  # comments / views
    engagement_rate: float,  # (likes + comments) / views
    traffic_sources: Dict[str, int],
    top_countries: Dict[str, int],
    updated_at: datetime
)
```

## Troubleshooting

### Authentication Issues

**Problem**: Browser doesn't open during authentication

**Solution**:
```python
# Manually copy authorization URL
auth_config = AuthConfig(
    client_secrets_path="client_secrets.json"
)
auth = AuthManager(auth_config)

# The URL will be printed to console
# Copy and paste in browser
```

**Problem**: "Access blocked: This app's request is invalid"

**Solution**:
- Check OAuth consent screen configuration
- Add test users if app not verified
- Verify redirect URI matches

### Upload Issues

**Problem**: "Upload failed: Quota exceeded"

**Solution**:
- Check [YouTube API quota](https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas)
- Default quota: 10,000 units/day
- Each upload costs ~1600 units
- Request quota increase if needed

**Problem**: "Invalid video format"

**Solution**:
- Supported formats: MOV, MPEG4, MP4, AVI, WMV, MPEGPS, FLV, 3GPP, WebM
- Max file size: 256GB (128GB recommended)
- Use FFmpeg to convert if needed:
  ```bash
  ffmpeg -i input.mov -c:v libx264 -c:a aac output.mp4
  ```

**Problem**: Upload stalls or times out

**Solution**:
- Check network connection
- Reduce chunk size for unstable connections:
  ```python
  config = UploadConfig(chunk_size=1024 * 1024 * 5)  # 5MB chunks
  ```
- Increase timeout:
  ```python
  config = UploadConfig(timeout_seconds=1200)  # 20 minutes
  ```

### Queue Issues

**Problem**: Queue not processing

**Solution**:
```python
# Check if queue is started
summary = queue.get_queue_summary()
if not summary['processing']:
    await queue.start()

# Check for failed items
failed_items = queue.get_all_items(status_filter=QueueStatus.FAILED)
for item in failed_items:
    print(f"Failed: {item.error_message}")
    await queue.retry(item.id)
```

**Problem**: Uploads fail repeatedly

**Solution**:
- Check error messages
- Verify video file integrity
- Check API quota
- Increase retry delay:
  ```python
  config = QueueConfig(retry_delay_minutes=10)
  ```

### Analytics Issues

**Problem**: Analytics data is empty or zero

**Solution**:
- YouTube Data API v3 has limited analytics
- For detailed analytics, enable YouTube Analytics API
- Some metrics require monetization
- Stats may take 24-48 hours to populate

## Best Practices

### 1. Authentication

✅ **DO:**
- Store `client_secrets.json` securely (never commit to git)
- Use token encryption (enabled by default)
- Implement proper error handling for expired tokens
- Use different accounts for testing and production

❌ **DON'T:**
- Share client secrets or tokens
- Commit credentials to version control
- Disable token encryption in production
- Use production account for testing

### 2. Uploads

✅ **DO:**
- Use progress callbacks for long uploads
- Implement proper error handling
- Validate video files before uploading
- Use appropriate privacy settings
- Add thumbnails for better engagement
- Use descriptive titles and tags

❌ **DON'T:**
- Upload without validation
- Ignore API quota limits
- Upload without thumbnails
- Use generic titles
- Spam tags
- Upload copyrighted content

### 3. Queue Management

✅ **DO:**
- Use priorities appropriately
- Monitor queue status
- Handle failed uploads
- Clear completed items regularly
- Set reasonable concurrent limits

❌ **DON'T:**
- Mark everything as URGENT
- Ignore failed uploads
- Set too high concurrent limits (use 2-3)
- Let queue grow indefinitely

### 4. Performance

✅ **DO:**
- Use queue for multiple uploads
- Enable caching for analytics
- Batch similar operations
- Monitor upload times
- Optimize video files before upload

❌ **DON'T:**
- Upload uncompressed videos
- Make redundant API calls
- Disable caching
- Upload during peak hours if possible

### 5. Security

✅ **DO:**
- Use environment variables for sensitive data
- Implement access controls
- Log upload activities
- Regular credential rotation
- Monitor API usage

❌ **DON'T:**
- Hardcode credentials
- Share API keys
- Expose tokens in logs
- Ignore security warnings

## Integration with Video Assembler

Complete workflow from video creation to upload:

```python
from services.video_assembler import VideoAssembler, VideoConfig
from services.script_generator import ScriptGenerator
from services.youtube_uploader import (
    AuthManager,
    VideoUploader,
    VideoMetadata,
    Category,
    PrivacyStatus
)

async def complete_workflow():
    # 1. Generate script
    script_gen = ScriptGenerator()
    script = await script_gen.generate(
        topic="Python Tutorial",
        style="educational"
    )
    
    # 2. Assemble video
    assembler = VideoAssembler(VideoConfig())
    video = await assembler.assemble(
        script_text=script.content,
        assets_dir="assets/python"
    )
    
    # 3. Upload to YouTube
    auth = AuthManager(AuthConfig(
        client_secrets_path="client_secrets.json"
    ))
    
    uploader = VideoUploader(auth)
    
    metadata = VideoMetadata(
        title=script.title,
        description=script.description,
        tags=script.tags,
        category=Category.EDUCATION,
        privacy_status=PrivacyStatus.PUBLIC
    )
    
    result = await uploader.upload(
        account_name="main",
        video_path=video.output_path,
        metadata=metadata,
        thumbnail_path=video.thumbnail_path
    )
    
    print(f"Complete! {result.url}")

asyncio.run(complete_workflow())
```

## Additional Resources

- [YouTube Data API Documentation](https://developers.google.com/youtube/v3)
- [YouTube API Quota Calculator](https://developers.google.com/youtube/v3/determine_quota_cost)
- [OAuth2 Setup Guide](https://developers.google.com/youtube/registering_an_application)
- [Video Format Specifications](https://support.google.com/youtube/answer/1722171)

## Support

For issues or questions:

1. Check [Troubleshooting](#troubleshooting) section
2. Review [API Reference](#api-reference)
3. See [examples/youtube_uploader_usage.py](../examples/youtube_uploader_usage.py)
4. Check YouTube API status
5. Review quota limits

---

**Task #8 Complete**: YouTube Upload Automation ready for production use!
