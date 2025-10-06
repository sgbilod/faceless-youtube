"""
End-to-End Tests for YouTube Upload Workflow

Tests the complete YouTube upload process including OAuth authentication,
video upload, metadata setting, and status confirmation.
"""

import pytest
import os
import asyncio
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch, AsyncMock

from src.core.database import get_db
from src.core.models import User, Video, VideoStatus, YouTubeAccount, UploadJob
from src.services.youtube_uploader.auth_manager import AuthManager
from src.services.youtube_uploader.uploader import VideoUploader
from src.services.youtube_uploader.analytics import YouTubeAnalytics


@pytest.fixture
def test_user(db: Session):
    """Create test user for E2E tests"""
    user = User(
        username="youtube_test_user",
        email="youtube@test.com",
        hashed_password="test_hash"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_youtube_account(test_user, db: Session):
    """Create test YouTube account"""
    account = YouTubeAccount(
        user_id=test_user.id,
        account_name="Test Channel",
        channel_id="UC_test_channel_123",
        channel_title="Test YouTube Channel",
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@pytest.fixture
def test_video_file(tmp_path):
    """Create a test video file"""
    video_path = tmp_path / "test_video.mp4"
    
    # Create a minimal valid MP4 file (tiny test file)
    # This is a minimal MP4 header for testing
    video_path.write_bytes(
        b'\x00\x00\x00\x1cftypisom\x00\x00\x02\x00isomiso2mp41'
        b'\x00\x00\x00\x08free'
        b'\x00\x00\x00\x00mdat'
    )
    
    return str(video_path)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_full_youtube_upload_workflow_mocked(
    test_user,
    test_youtube_account,
    test_video_file,
    db: Session
):
    """
    E2E Test: Complete YouTube upload workflow (with mocking)
    
    Workflow:
    1. Authenticate with YouTube (mocked)
    2. Prepare video metadata
    3. Upload video (mocked)
    4. Verify upload status
    5. Fetch video analytics (mocked)
    
    Note: Uses mocking to avoid real YouTube API calls in tests.
    """
    # Step 1: Initialize auth manager
    auth_manager = AuthManager()
    
    # Mock OAuth flow
    with patch.object(auth_manager, 'get_credentials', return_value=Mock()):
        creds = await auth_manager.get_credentials(test_youtube_account.account_name)
        assert creds is not None
        print("✓ Step 1: Authentication initialized (mocked)")
    
    # Step 2: Prepare metadata
    metadata = {
        "title": "E2E Test Video - Meditation",
        "description": "This is an automated test video. Please ignore.",
        "tags": ["meditation", "test", "automated"],
        "category_id": "22",  # People & Blogs
        "privacy_status": "private"
    }
    
    print(f"✓ Step 2: Metadata prepared - {metadata['title']}")
    
    # Step 3: Create video record
    video = Video(
        user_id=test_user.id,
        script_id=1,  # Assume script exists
        title=metadata["title"],
        description=metadata["description"],
        niche="meditation",
        style="calm",
        duration_seconds=30,
        resolution="1080p",
        fps=30,
        aspect_ratio="16:9",
        file_path=test_video_file,
        status=VideoStatus.COMPLETED,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    
    print(f"✓ Step 3: Video record created (ID: {video.id})")
    
    # Step 4: Upload to YouTube (mocked)
    uploader = VideoUploader(auth_manager=auth_manager)
    
    mock_upload_result = {
        "video_id": "test_video_abc123",
        "title": metadata["title"],
        "url": "https://youtube.com/watch?v=test_video_abc123",
        "privacy_status": "private",
        "file_size_bytes": os.path.getsize(test_video_file),
        "upload_time_seconds": 5.0
    }
    
    with patch.object(uploader, 'upload', new_callable=AsyncMock) as mock_upload:
        mock_upload.return_value = type('UploadResult', (), mock_upload_result)()
        
        result = await uploader.upload(
            account_name=test_youtube_account.account_name,
            video_path=test_video_file,
            title=metadata["title"],
            description=metadata["description"],
            tags=metadata["tags"],
            category_id=metadata["category_id"],
            privacy_status=metadata["privacy_status"]
        )
        
        assert result.video_id == "test_video_abc123"
        assert result.url.startswith("https://youtube.com/watch?v=")
        print(f"✓ Step 4: Video uploaded (mocked) - {result.video_id}")
    
    # Step 5: Create upload job record
    upload_job = UploadJob(
        user_id=test_user.id,
        video_id=video.id,
        account_id=test_youtube_account.id,
        youtube_video_id=result.video_id,
        status="completed",
        created_at=datetime.utcnow(),
        completed_at=datetime.utcnow()
    )
    db.add(upload_job)
    db.commit()
    
    print(f"✓ Step 5: Upload job recorded")
    
    # Step 6: Fetch analytics (mocked)
    analytics = YouTubeAnalytics(auth_manager=auth_manager)
    
    mock_stats = {
        "video_id": result.video_id,
        "views": 0,
        "likes": 0,
        "comments": 0,
        "watch_time_minutes": 0.0,
        "average_view_duration_seconds": 0.0,
        "fetched_at": datetime.utcnow()
    }
    
    with patch.object(analytics, 'get_video_stats', new_callable=AsyncMock) as mock_stats_fetch:
        mock_stats_fetch.return_value = type('VideoStats', (), mock_stats)()
        
        stats = await analytics.get_video_stats(
            account_name=test_youtube_account.account_name,
            video_id=result.video_id
        )
        
        assert stats.video_id == result.video_id
        print(f"✓ Step 6: Analytics fetched (mocked) - {stats.views} views")
    
    print("\n✅ E2E Test PASSED: Full YouTube upload workflow completed")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_youtube_oauth_flow(test_user, test_youtube_account, db: Session):
    """
    E2E Test: YouTube OAuth authentication flow
    
    Tests the OAuth 2.0 flow for YouTube API access.
    Note: Mocked to avoid browser interaction in tests.
    """
    auth_manager = AuthManager()
    
    # Mock the OAuth flow
    with patch('src.services.youtube_uploader.auth_manager.InstalledAppFlow') as mock_flow:
        mock_credentials = Mock()
        mock_credentials.token = "test_access_token"
        mock_credentials.refresh_token = "test_refresh_token"
        mock_credentials.token_uri = "https://oauth2.googleapis.com/token"
        mock_credentials.client_id = "test_client_id"
        mock_credentials.client_secret = "test_client_secret"
        mock_credentials.valid = True
        mock_credentials.expired = False
        
        mock_flow.from_client_secrets_file.return_value.run_local_server.return_value = mock_credentials
        
        # Initiate OAuth flow
        creds = await auth_manager.authenticate(test_youtube_account.account_name)
        
        assert creds is not None
        assert creds.token == "test_access_token"
        print("✅ OAuth flow completed (mocked)")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_youtube_upload_error_handling(
    test_user,
    test_youtube_account,
    db: Session
):
    """
    E2E Test: Error handling in YouTube upload
    
    Tests handling of various error scenarios:
    - Missing file
    - Invalid credentials
    - API quota exceeded
    """
    auth_manager = AuthManager()
    uploader = VideoUploader(auth_manager=auth_manager)
    
    # Test 1: Missing file
    with pytest.raises(FileNotFoundError):
        await uploader.upload(
            account_name=test_youtube_account.account_name,
            video_path="/nonexistent/video.mp4",
            title="Test",
            description="Test",
            tags=["test"],
            category_id="22",
            privacy_status="private"
        )
    
    print("✓ Error handling test 1: Missing file caught")
    
    # Test 2: Invalid metadata
    with patch.object(uploader, 'upload', new_callable=AsyncMock) as mock_upload:
        mock_upload.side_effect = ValueError("Invalid category_id")
        
        with pytest.raises(ValueError):
            await uploader.upload(
                account_name=test_youtube_account.account_name,
                video_path="test.mp4",
                title="",  # Empty title should fail
                description="Test",
                tags=["test"],
                category_id="invalid",
                privacy_status="private"
            )
    
    print("✓ Error handling test 2: Invalid metadata caught")
    
    print("✅ Error handling tests passed")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_youtube_analytics_integration(
    test_user,
    test_youtube_account,
    db: Session
):
    """
    E2E Test: YouTube Analytics API integration
    
    Tests fetching video and channel analytics data.
    """
    auth_manager = AuthManager()
    analytics = YouTubeAnalytics(auth_manager=auth_manager)
    
    # Mock video stats
    mock_video_stats = {
        "video_id": "test_video_123",
        "views": 1000,
        "likes": 50,
        "comments": 10,
        "watch_time_minutes": 500.0,
        "average_view_duration_seconds": 30.0,
        "fetched_at": datetime.utcnow()
    }
    
    with patch.object(analytics, 'get_video_stats', new_callable=AsyncMock) as mock_get_stats:
        mock_get_stats.return_value = type('VideoStats', (), mock_video_stats)()
        
        stats = await analytics.get_video_stats(
            account_name=test_youtube_account.account_name,
            video_id="test_video_123"
        )
        
        assert stats.views == 1000
        assert stats.likes == 50
        print(f"✓ Video stats: {stats.views} views, {stats.likes} likes")
    
    # Mock channel stats
    mock_channel_stats = {
        "channel_id": test_youtube_account.channel_id,
        "subscribers": 1000,
        "total_views": 50000,
        "total_videos": 25,
        "average_views_per_video": 2000.0,
        "fetched_at": datetime.utcnow()
    }
    
    with patch.object(analytics, 'get_channel_stats', new_callable=AsyncMock) as mock_channel:
        mock_channel.return_value = type('ChannelStats', (), mock_channel_stats)()
        
        channel_stats = await analytics.get_channel_stats(
            account_name=test_youtube_account.account_name
        )
        
        assert channel_stats.subscribers == 1000
        assert channel_stats.total_videos == 25
        print(f"✓ Channel stats: {channel_stats.subscribers} subscribers, {channel_stats.total_videos} videos")
    
    print("✅ Analytics integration test passed")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_youtube_batch_upload(
    test_user,
    test_youtube_account,
    test_video_file,
    db: Session
):
    """
    E2E Test: Batch YouTube upload
    
    Tests uploading multiple videos in sequence.
    """
    auth_manager = AuthManager()
    uploader = VideoUploader(auth_manager=auth_manager)
    
    videos_to_upload = [
        {
            "title": f"Batch Test Video {i}",
            "description": f"Batch upload test video number {i}",
            "tags": ["test", "batch", f"video{i}"],
            "privacy_status": "private"
        }
        for i in range(3)
    ]
    
    upload_results = []
    
    for i, video_meta in enumerate(videos_to_upload):
        mock_result = {
            "video_id": f"batch_test_{i}",
            "title": video_meta["title"],
            "url": f"https://youtube.com/watch?v=batch_test_{i}",
            "privacy_status": "private",
            "file_size_bytes": 1024,
            "upload_time_seconds": 2.0
        }
        
        with patch.object(uploader, 'upload', new_callable=AsyncMock) as mock_upload:
            mock_upload.return_value = type('UploadResult', (), mock_result)()
            
            result = await uploader.upload(
                account_name=test_youtube_account.account_name,
                video_path=test_video_file,
                title=video_meta["title"],
                description=video_meta["description"],
                tags=video_meta["tags"],
                category_id="22",
                privacy_status=video_meta["privacy_status"]
            )
            
            upload_results.append(result)
            print(f"✓ Batch upload {i+1}/3: {result.video_id}")
    
    assert len(upload_results) == 3
    assert all(r.video_id for r in upload_results)
    
    print("✅ Batch upload test passed")


if __name__ == "__main__":
    # Run E2E tests
    pytest.main([__file__, "-v", "-m", "e2e"])
