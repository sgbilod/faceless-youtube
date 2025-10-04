"""
YouTube Uploader Usage Examples

Demonstrates practical usage of YouTube upload automation.
"""

import asyncio
from pathlib import Path
from datetime import datetime, timedelta

from services.youtube_uploader import (
    AuthManager,
    AuthConfig,
    VideoUploader,
    UploadConfig,
    VideoMetadata,
    PrivacyStatus,
    Category,
    UploadQueue,
    QueueConfig,
    QueuePriority,
    AnalyticsTracker,
    AnalyticsConfig
)


# ============================================
# EXAMPLE 1: First-Time Setup and Authentication
# ============================================

async def example_1_first_time_setup():
    """
    Example 1: First-time setup and authentication
    
    Before using the YouTube uploader, you need to:
    1. Create a project in Google Cloud Console
    2. Enable YouTube Data API v3
    3. Create OAuth2 credentials
    4. Download client secrets JSON
    """
    print("=" * 60)
    print("EXAMPLE 1: First-Time Setup and Authentication")
    print("=" * 60)
    
    # Initialize auth manager
    auth_config = AuthConfig(
        client_secrets_path="client_secrets.json",
        token_storage_path="youtube_tokens"
    )
    
    auth = AuthManager(auth_config)
    
    # First-time authentication (opens browser)
    print("\n1. Starting OAuth2 authentication...")
    print("   (This will open your browser for authorization)")
    
    try:
        credentials = await auth.authenticate(account_name="main")
        
        print(f"\n✅ Authentication successful!")
        print(f"   Channel: {credentials.channel_title}")
        print(f"   Channel ID: {credentials.channel_id}")
        print(f"   Token expires: {credentials.expiry}")
    
    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
    
    print("\n" + "=" * 60 + "\n")


# ============================================
# EXAMPLE 2: Basic Video Upload
# ============================================

async def example_2_basic_upload():
    """
    Example 2: Basic video upload with minimal configuration
    """
    print("=" * 60)
    print("EXAMPLE 2: Basic Video Upload")
    print("=" * 60)
    
    # Initialize
    auth = AuthManager(AuthConfig(client_secrets_path="client_secrets.json"))
    uploader = VideoUploader(auth)
    
    # Create metadata
    metadata = VideoMetadata(
        title="My First YouTube Video",
        description="This is a test video uploaded via API",
        tags=["test", "api", "automation"],
        category=Category.EDUCATION,
        privacy_status=PrivacyStatus.PRIVATE
    )
    
    # Upload
    print("\n1. Uploading video...")
    
    try:
        result = await uploader.upload(
            account_name="main",
            video_path="path/to/video.mp4",
            metadata=metadata
        )
        
        print(f"\n✅ Upload successful!")
        print(f"   Video ID: {result.video_id}")
        print(f"   URL: {result.url}")
        print(f"   Upload time: {result.upload_time_seconds:.1f}s")
        print(f"   File size: {result.file_size_bytes / 1024 / 1024:.1f} MB")
    
    except Exception as e:
        print(f"\n❌ Upload failed: {e}")
    
    print("\n" + "=" * 60 + "\n")


# ============================================
# EXAMPLE 3: Upload with Thumbnail and Progress Tracking
# ============================================

async def example_3_upload_with_thumbnail():
    """
    Example 3: Upload with custom thumbnail and progress tracking
    """
    print("=" * 60)
    print("EXAMPLE 3: Upload with Thumbnail and Progress")
    print("=" * 60)
    
    auth = AuthManager(AuthConfig(client_secrets_path="client_secrets.json"))
    uploader = VideoUploader(auth)
    
    metadata = VideoMetadata(
        title="Video with Custom Thumbnail",
        description="Demonstrates thumbnail upload and progress tracking",
        tags=["tutorial", "example"],
        privacy_status=PrivacyStatus.UNLISTED
    )
    
    # Progress callback
    def progress_callback(percent: float):
        print(f"\r   Progress: {percent:.0f}%", end="", flush=True)
    
    print("\n1. Uploading video with thumbnail...")
    
    try:
        result = await uploader.upload(
            account_name="main",
            video_path="video.mp4",
            metadata=metadata,
            thumbnail_path="thumbnail.jpg",  # Custom thumbnail
            progress_callback=progress_callback
        )
        
        print(f"\n\n✅ Upload complete!")
        print(f"   Video: {result.url}")
        print(f"   Thumbnail: {result.thumbnail_url}")
    
    except Exception as e:
        print(f"\n\n❌ Upload failed: {e}")
    
    print("\n" + "=" * 60 + "\n")


# ============================================
# EXAMPLE 4: Scheduled Upload (Publish Later)
# ============================================

async def example_4_scheduled_upload():
    """
    Example 4: Schedule video to publish at specific time
    """
    print("=" * 60)
    print("EXAMPLE 4: Scheduled Upload")
    print("=" * 60)
    
    auth = AuthManager(AuthConfig(client_secrets_path="client_secrets.json"))
    uploader = VideoUploader(auth)
    
    # Schedule for 2 days from now at 10 AM
    publish_time = datetime.now() + timedelta(days=2)
    publish_time = publish_time.replace(hour=10, minute=0, second=0)
    
    metadata = VideoMetadata(
        title="Scheduled Video Release",
        description="This video will be published automatically",
        tags=["scheduled", "automation"],
        privacy_status=PrivacyStatus.PRIVATE,  # Upload as private
        publish_at=publish_time  # Schedule publish time
    )
    
    print(f"\n1. Scheduling video for: {publish_time}")
    
    try:
        result = await uploader.upload(
            account_name="main",
            video_path="scheduled_video.mp4",
            metadata=metadata
        )
        
        print(f"\n✅ Video scheduled!")
        print(f"   Video ID: {result.video_id}")
        print(f"   Will publish at: {publish_time}")
    
    except Exception as e:
        print(f"\n❌ Scheduling failed: {e}")
    
    print("\n" + "=" * 60 + "\n")


# ============================================
# EXAMPLE 5: Upload Queue with Multiple Videos
# ============================================

async def example_5_upload_queue():
    """
    Example 5: Upload multiple videos using queue system
    """
    print("=" * 60)
    print("EXAMPLE 5: Upload Queue")
    print("=" * 60)
    
    auth = AuthManager(AuthConfig(client_secrets_path="client_secrets.json"))
    uploader = VideoUploader(auth)
    
    queue_config = QueueConfig(
        max_concurrent_uploads=2,  # Upload 2 videos at once
        auto_start=True
    )
    
    queue = UploadQueue(auth, uploader, queue_config)
    
    # Add multiple videos to queue
    videos = [
        {
            "title": "Video 1: Introduction",
            "file": "video1.mp4",
            "priority": QueuePriority.HIGH
        },
        {
            "title": "Video 2: Tutorial Part 1",
            "file": "video2.mp4",
            "priority": QueuePriority.NORMAL
        },
        {
            "title": "Video 3: Tutorial Part 2",
            "file": "video3.mp4",
            "priority": QueuePriority.NORMAL
        },
        {
            "title": "Video 4: Conclusion",
            "file": "video4.mp4",
            "priority": QueuePriority.LOW
        }
    ]
    
    print(f"\n1. Adding {len(videos)} videos to queue...")
    
    item_ids = []
    for video in videos:
        metadata = VideoMetadata(
            title=video["title"],
            description=f"Part of video series",
            tags=["series", "tutorial"],
            privacy_status=PrivacyStatus.UNLISTED
        )
        
        item_id = await queue.add(
            account_name="main",
            video_path=video["file"],
            metadata=metadata,
            priority=video["priority"]
        )
        
        item_ids.append(item_id)
        print(f"   Added: {video['title']} (priority: {video['priority'].value})")
    
    print(f"\n2. Starting queue processing...")
    await queue.start()
    
    # Monitor progress
    print(f"\n3. Monitoring uploads...")
    while True:
        summary = queue.get_queue_summary()
        
        print(f"\r   Active: {summary['active_uploads']} | " +
              f"Queued: {summary['status_counts']['queued']} | " +
              f"Completed: {summary['status_counts']['completed']}",
              end="", flush=True)
        
        # Check if all completed
        if summary['status_counts']['completed'] == len(videos):
            break
        
        await asyncio.sleep(1)
    
    print(f"\n\n✅ All uploads completed!")
    
    # Show results
    for item_id in item_ids:
        status = queue.get_status(item_id)
        if status and status['upload_result']:
            result = status['upload_result']
            print(f"   • {result['title']}: {result['url']}")
    
    print("\n" + "=" * 60 + "\n")


# ============================================
# EXAMPLE 6: Upload with Captions/Subtitles
# ============================================

async def example_6_upload_with_captions():
    """
    Example 6: Upload video with multiple caption files
    """
    print("=" * 60)
    print("EXAMPLE 6: Upload with Captions")
    print("=" * 60)
    
    auth = AuthManager(AuthConfig(client_secrets_path="client_secrets.json"))
    uploader = VideoUploader(auth)
    
    metadata = VideoMetadata(
        title="Multilingual Video Tutorial",
        description="Video with English and Spanish captions",
        tags=["tutorial", "multilingual"],
        privacy_status=PrivacyStatus.PUBLIC
    )
    
    # Caption files
    captions = [
        {
            "file": "captions_en.srt",
            "language": "en",
            "name": "English"
        },
        {
            "file": "captions_es.srt",
            "language": "es",
            "name": "Spanish"
        }
    ]
    
    print("\n1. Uploading video with captions...")
    
    try:
        result = await uploader.upload(
            account_name="main",
            video_path="multilingual_video.mp4",
            metadata=metadata,
            captions=captions
        )
        
        print(f"\n✅ Upload complete with {len(captions)} caption tracks!")
        print(f"   Video: {result.url}")
    
    except Exception as e:
        print(f"\n❌ Upload failed: {e}")
    
    print("\n" + "=" * 60 + "\n")


# ============================================
# EXAMPLE 7: Playlist Management
# ============================================

async def example_7_playlist_management():
    """
    Example 7: Create playlist and add videos
    """
    print("=" * 60)
    print("EXAMPLE 7: Playlist Management")
    print("=" * 60)
    
    auth = AuthManager(AuthConfig(client_secrets_path="client_secrets.json"))
    uploader = VideoUploader(auth)
    
    # Create playlist
    print("\n1. Creating playlist...")
    
    try:
        playlist_id = await uploader.create_playlist(
            account_name="main",
            title="Python Tutorial Series",
            description="Complete Python programming course",
            privacy_status=PrivacyStatus.PUBLIC
        )
        
        print(f"   ✅ Playlist created: {playlist_id}")
        
        # Upload videos to playlist
        print(f"\n2. Uploading videos to playlist...")
        
        for i in range(1, 4):
            metadata = VideoMetadata(
                title=f"Python Tutorial - Part {i}",
                description=f"Part {i} of Python tutorial series",
                tags=["python", "tutorial", "programming"],
                privacy_status=PrivacyStatus.PUBLIC,
                playlist_id=playlist_id  # Auto-add to playlist
            )
            
            result = await uploader.upload(
                account_name="main",
                video_path=f"tutorial_part_{i}.mp4",
                metadata=metadata
            )
            
            print(f"   ✅ Part {i} uploaded: {result.video_id}")
        
        print(f"\n✅ All videos added to playlist!")
        print(f"   Playlist URL: https://www.youtube.com/playlist?list={playlist_id}")
    
    except Exception as e:
        print(f"\n❌ Failed: {e}")
    
    print("\n" + "=" * 60 + "\n")


# ============================================
# EXAMPLE 8: Analytics and Performance Tracking
# ============================================

async def example_8_analytics():
    """
    Example 8: Track video and channel analytics
    """
    print("=" * 60)
    print("EXAMPLE 8: Analytics Tracking")
    print("=" * 60)
    
    auth = AuthManager(AuthConfig(client_secrets_path="client_secrets.json"))
    tracker = AnalyticsTracker(auth)
    
    # Get video stats
    print("\n1. Getting video statistics...")
    
    try:
        video_stats = await tracker.get_video_stats(
            account_name="main",
            video_id="your_video_id"
        )
        
        print(f"\n📊 Video: {video_stats.title}")
        print(f"   Views: {video_stats.views:,}")
        print(f"   Likes: {video_stats.likes:,}")
        print(f"   Comments: {video_stats.comments:,}")
        print(f"   Watch time: {video_stats.watch_time_minutes:,} minutes")
        print(f"   Engagement rate: {video_stats.engagement_rate:.2%}")
        
        # Get channel stats
        print(f"\n2. Getting channel statistics...")
        
        channel_stats = await tracker.get_channel_stats("main")
        
        print(f"\n📺 Channel: {channel_stats.channel_title}")
        print(f"   Subscribers: {channel_stats.subscribers:,}")
        print(f"   Total views: {channel_stats.total_views:,}")
        print(f"   Videos: {channel_stats.total_videos}")
        print(f"   Subscribers (30d): +{channel_stats.subscribers_gained_30d:,}")
        
        # Get top videos
        print(f"\n3. Getting top performing videos...")
        
        top_videos = await tracker.get_top_videos(
            account_name="main",
            max_results=5
        )
        
        print(f"\n🏆 Top 5 Videos:")
        for i, video in enumerate(top_videos, 1):
            print(f"   {i}. {video.title}")
            print(f"      Views: {video.views:,} | Likes: {video.likes:,}")
    
    except Exception as e:
        print(f"\n❌ Failed: {e}")
    
    print("\n" + "=" * 60 + "\n")


# ============================================
# EXAMPLE 9: Complete Workflow (Integration with Video Assembler)
# ============================================

async def example_9_complete_workflow():
    """
    Example 9: Complete workflow from video creation to upload
    
    This demonstrates integration with the video assembly service (Task #7)
    """
    print("=" * 60)
    print("EXAMPLE 9: Complete Workflow")
    print("=" * 60)
    
    # Step 1: Assemble video (from Task #7)
    print("\n1. Assembling video...")
    
    from services.video_assembler import VideoAssembler, VideoConfig
    from services.script_generator import ScriptGenerator
    
    try:
        # Generate script
        script_gen = ScriptGenerator()
        script = await script_gen.generate(
            topic="Introduction to Python Programming",
            style="educational",
            duration_minutes=5
        )
        
        print(f"   ✅ Script generated: {len(script.content)} words")
        
        # Assemble video
        assembler = VideoAssembler(VideoConfig())
        video_result = await assembler.assemble(
            script_text=script.content,
            assets_dir="assets/python_tutorial"
        )
        
        print(f"   ✅ Video assembled: {video_result.output_path}")
        
        # Step 2: Upload to YouTube
        print(f"\n2. Uploading to YouTube...")
        
        auth = AuthManager(AuthConfig(client_secrets_path="client_secrets.json"))
        uploader = VideoUploader(auth)
        
        metadata = VideoMetadata(
            title=script.title,
            description=script.description,
            tags=script.tags,
            category=Category.EDUCATION,
            privacy_status=PrivacyStatus.PUBLIC
        )
        
        upload_result = await uploader.upload(
            account_name="main",
            video_path=video_result.output_path,
            metadata=metadata,
            thumbnail_path=video_result.thumbnail_path
        )
        
        print(f"   ✅ Upload complete!")
        print(f"   URL: {upload_result.url}")
        
        # Step 3: Track performance
        print(f"\n3. Setting up analytics tracking...")
        
        tracker = AnalyticsTracker(auth)
        
        # Wait for video to process
        print(f"   Waiting for video processing...")
        success = await uploader.wait_for_processing(
            "main",
            upload_result.video_id,
            max_wait_seconds=300
        )
        
        if success:
            # Get initial stats
            stats = await tracker.get_video_stats("main", upload_result.video_id)
            print(f"   ✅ Video live! Initial views: {stats.views}")
        
        print(f"\n✅ Complete workflow finished!")
        print(f"   • Script generated")
        print(f"   • Video assembled")
        print(f"   • Uploaded to YouTube")
        print(f"   • Analytics tracking enabled")
    
    except Exception as e:
        print(f"\n❌ Workflow failed: {e}")
    
    print("\n" + "=" * 60 + "\n")


# ============================================
# EXAMPLE 10: Error Handling and Retry Logic
# ============================================

async def example_10_error_handling():
    """
    Example 10: Robust error handling and retry logic
    """
    print("=" * 60)
    print("EXAMPLE 10: Error Handling")
    print("=" * 60)
    
    auth = AuthManager(AuthConfig(client_secrets_path="client_secrets.json"))
    
    # Custom upload config with retry settings
    upload_config = UploadConfig(
        max_retries=5,
        retry_delay_seconds=5
    )
    
    uploader = VideoUploader(auth, upload_config)
    
    metadata = VideoMetadata(
        title="Test Video with Retry Logic",
        description="Demonstrates error handling",
        tags=["test"],
        privacy_status=PrivacyStatus.PRIVATE
    )
    
    print("\n1. Attempting upload with retry logic...")
    
    try:
        result = await uploader.upload(
            account_name="main",
            video_path="test_video.mp4",
            metadata=metadata
        )
        
        print(f"\n✅ Upload successful!")
        print(f"   Video ID: {result.video_id}")
    
    except FileNotFoundError as e:
        print(f"\n❌ File not found: {e}")
        print(f"   Please check the video path")
    
    except ValueError as e:
        print(f"\n❌ Invalid metadata: {e}")
        print(f"   Please check title, tags, etc.")
    
    except Exception as e:
        print(f"\n❌ Upload failed: {e}")
        print(f"   The uploader tried {upload_config.max_retries} times")
        print(f"   Consider checking:")
        print(f"   • Network connection")
        print(f"   • YouTube API quota")
        print(f"   • Video file format/size")
    
    print("\n" + "=" * 60 + "\n")


# ============================================
# MAIN
# ============================================

async def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("YouTube Uploader - Usage Examples")
    print("=" * 60 + "\n")
    
    # Note: These examples require actual YouTube API credentials
    # Uncomment the ones you want to run:
    
    # await example_1_first_time_setup()
    # await example_2_basic_upload()
    # await example_3_upload_with_thumbnail()
    # await example_4_scheduled_upload()
    # await example_5_upload_queue()
    # await example_6_upload_with_captions()
    # await example_7_playlist_management()
    # await example_8_analytics()
    # await example_9_complete_workflow()
    # await example_10_error_handling()
    
    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60 + "\n")
    
    print("To run these examples:")
    print("1. Set up YouTube API credentials")
    print("2. Download client_secrets.json")
    print("3. Uncomment desired examples in main()")
    print("4. Run: python examples/youtube_uploader_usage.py")


if __name__ == "__main__":
    asyncio.run(main())
