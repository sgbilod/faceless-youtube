"""
YouTube Uploader Test Suite

Tests for YouTube upload automation with mocked API calls.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import json

from services.youtube_uploader import (
    AuthManager,
    AuthConfig,
    AuthStatus,
    YouTubeCredentials,
    VideoUploader,
    UploadConfig,
    UploadStatus,
    VideoMetadata,
    PrivacyStatus,
    Category,
    UploadResult,
    UploadQueue,
    QueueConfig,
    QueueItem,
    QueuePriority,
    QueueStatus,
    AnalyticsTracker,
    AnalyticsConfig,
    VideoStats,
    ChannelStats
)


# ============================================
# FIXTURES
# ============================================

@pytest.fixture
def temp_dir():
    """Create temporary directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def auth_config(temp_dir):
    """Auth configuration"""
    return AuthConfig(
        client_secrets_path=str(temp_dir / "client_secrets.json"),
        token_storage_path=str(temp_dir / "tokens"),
        encrypt_tokens=False  # Disable for testing
    )


@pytest.fixture
def upload_config():
    """Upload configuration"""
    return UploadConfig(
        chunk_size=1024 * 1024,  # 1MB for testing
        max_retries=3
    )


@pytest.fixture
def queue_config():
    """Queue configuration"""
    return QueueConfig(
        max_concurrent_uploads=2,
        auto_start=False  # Manual control in tests
    )


@pytest.fixture
def sample_metadata():
    """Sample video metadata"""
    return VideoMetadata(
        title="Test Video",
        description="Test description",
        tags=["test", "video"],
        category=Category.EDUCATION,
        privacy_status=PrivacyStatus.PRIVATE
    )


@pytest.fixture
def sample_video(temp_dir):
    """Create sample video file"""
    video_path = temp_dir / "test_video.mp4"
    video_path.write_bytes(b"fake video content" * 1000)
    return video_path


@pytest.fixture
def sample_thumbnail(temp_dir):
    """Create sample thumbnail"""
    thumbnail_path = temp_dir / "thumbnail.jpg"
    thumbnail_path.write_bytes(b"fake image content")
    return thumbnail_path


@pytest.fixture
def mock_credentials():
    """Mock YouTube credentials"""
    return YouTubeCredentials(
        account_name="test_account",
        email="test@example.com",
        channel_id="UC_test123",
        channel_title="Test Channel",
        token="test_token",
        refresh_token="test_refresh",
        token_uri="https://oauth2.googleapis.com/token",
        client_id="test_client_id",
        client_secret="test_client_secret",
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
        expiry=datetime.utcnow() + timedelta(hours=1)
    )


# ============================================
# AUTH MANAGER TESTS
# ============================================

class TestAuthManager:
    """Test AuthManager"""
    
    def test_auth_config_defaults(self):
        """Test auth config defaults"""
        config = AuthConfig(client_secrets_path="secrets.json")
        
        assert config.redirect_port == 8080
        assert config.encrypt_tokens is True
        assert config.auto_refresh is True
        assert len(config.scopes) == 3
    
    @pytest.mark.asyncio
    async def test_save_and_load_credentials(self, auth_config, mock_credentials, temp_dir):
        """Test credential save and load"""
        auth = AuthManager(auth_config)
        
        # Save credentials
        await auth.save_credentials(mock_credentials)
        
        # Load credentials
        loaded = await auth.load_credentials("test_account")
        
        assert loaded.account_name == mock_credentials.account_name
        assert loaded.channel_id == mock_credentials.channel_id
        assert loaded.token == mock_credentials.token
    
    @pytest.mark.asyncio
    async def test_list_accounts(self, auth_config, mock_credentials):
        """Test listing accounts"""
        auth = AuthManager(auth_config)
        
        # Save multiple accounts
        await auth.save_credentials(mock_credentials)
        
        creds2 = mock_credentials.copy()
        creds2.account_name = "account2"
        await auth.save_credentials(creds2)
        
        # List accounts
        accounts = await auth.list_accounts()
        
        assert len(accounts) == 2
        assert "test_account" in accounts
        assert "account2" in accounts
    
    @pytest.mark.asyncio
    async def test_remove_account(self, auth_config, mock_credentials):
        """Test removing account"""
        auth = AuthManager(auth_config)
        
        await auth.save_credentials(mock_credentials)
        await auth.remove_account("test_account")
        
        accounts = await auth.list_accounts()
        assert "test_account" not in accounts
    
    @pytest.mark.asyncio
    async def test_get_auth_status(self, auth_config, mock_credentials):
        """Test getting auth status"""
        auth = AuthManager(auth_config)
        
        # Not authenticated
        status = await auth.get_auth_status("nonexistent")
        assert status == AuthStatus.NOT_AUTHENTICATED
        
        # Authenticated
        await auth.save_credentials(mock_credentials)
        status = await auth.get_auth_status("test_account")
        # Will be NOT_AUTHENTICATED without actual API validation
        assert status in [AuthStatus.AUTHENTICATED, AuthStatus.NOT_AUTHENTICATED]


# ============================================
# VIDEO UPLOADER TESTS
# ============================================

class TestVideoUploader:
    """Test VideoUploader"""
    
    def test_upload_config_defaults(self):
        """Test upload config defaults"""
        config = UploadConfig()
        
        assert config.chunk_size == 1024 * 1024 * 10
        assert config.max_retries == 5
        assert config.default_privacy == PrivacyStatus.PRIVATE
        assert config.default_category == Category.EDUCATION
    
    def test_video_metadata_validation(self):
        """Test metadata validation"""
        # Valid metadata
        metadata = VideoMetadata(
            title="Test Video",
            description="Description"
        )
        assert metadata.title == "Test Video"
        
        # Empty title should fail
        with pytest.raises(ValueError):
            VideoMetadata(title="")
        
        # Tags exceeding limit
        long_tags = ["x" * 100 for _ in range(10)]  # Total > 500 chars
        with pytest.raises(ValueError):
            VideoMetadata(title="Test", tags=long_tags)
    
    @pytest.mark.asyncio
    @patch("services.youtube_uploader.uploader.AuthManager")
    async def test_upload_with_mock(self, mock_auth, upload_config, sample_metadata, sample_video):
        """Test upload with mocked API"""
        # Mock auth manager
        mock_auth_instance = Mock()
        mock_youtube = Mock()
        mock_auth_instance.get_youtube_client = AsyncMock(return_value=mock_youtube)
        
        # Mock upload response
        mock_insert = Mock()
        mock_insert.next_chunk = Mock(return_value=(None, {"id": "test_video_id"}))
        mock_youtube.videos().insert = Mock(return_value=mock_insert)
        
        uploader = VideoUploader(mock_auth_instance, upload_config)
        
        # Mock the actual upload method
        with patch.object(uploader, '_upload_video', return_value="test_video_id"):
            result = await uploader.upload(
                account_name="test",
                video_path=str(sample_video),
                metadata=sample_metadata
            )
            
            assert result.video_id == "test_video_id"
            assert result.status == UploadStatus.COMPLETED


# ============================================
# UPLOAD QUEUE TESTS
# ============================================

class TestUploadQueue:
    """Test UploadQueue"""
    
    def test_queue_config_defaults(self):
        """Test queue config defaults"""
        config = QueueConfig()
        
        assert config.max_concurrent_uploads == 2
        assert config.retry_failed_uploads is True
        assert config.max_retries == 3
        assert config.auto_start is True
    
    @pytest.mark.asyncio
    async def test_add_to_queue(self, queue_config, sample_metadata, sample_video):
        """Test adding items to queue"""
        mock_auth = Mock()
        mock_uploader = Mock()
        
        queue = UploadQueue(mock_auth, mock_uploader, queue_config)
        
        item_id = await queue.add(
            account_name="test",
            video_path=str(sample_video),
            metadata=sample_metadata,
            priority=QueuePriority.HIGH
        )
        
        assert item_id is not None
        
        # Check item in queue
        item = queue.get_item(item_id)
        assert item is not None
        assert item.priority == QueuePriority.HIGH
        assert item.status == QueueStatus.QUEUED
    
    @pytest.mark.asyncio
    async def test_queue_priority_ordering(self, queue_config, sample_metadata, sample_video):
        """Test queue priority ordering"""
        mock_auth = Mock()
        mock_uploader = Mock()
        
        queue = UploadQueue(mock_auth, mock_uploader, queue_config)
        
        # Add items with different priorities
        low_id = await queue.add(
            account_name="test",
            video_path=str(sample_video),
            metadata=sample_metadata,
            priority=QueuePriority.LOW
        )
        
        urgent_id = await queue.add(
            account_name="test",
            video_path=str(sample_video),
            metadata=sample_metadata,
            priority=QueuePriority.URGENT
        )
        
        normal_id = await queue.add(
            account_name="test",
            video_path=str(sample_video),
            metadata=sample_metadata,
            priority=QueuePriority.NORMAL
        )
        
        # Get next items
        next_items = queue._get_next_items(3)
        
        # Urgent should be first
        assert next_items[0].id == urgent_id
        assert next_items[1].id == normal_id
        assert next_items[2].id == low_id
    
    @pytest.mark.asyncio
    async def test_queue_summary(self, queue_config, sample_metadata, sample_video):
        """Test queue summary"""
        mock_auth = Mock()
        mock_uploader = Mock()
        
        queue = UploadQueue(mock_auth, mock_uploader, queue_config)
        
        # Add items
        await queue.add(
            account_name="test",
            video_path=str(sample_video),
            metadata=sample_metadata
        )
        
        await queue.add(
            account_name="test",
            video_path=str(sample_video),
            metadata=sample_metadata
        )
        
        summary = queue.get_queue_summary()
        
        assert summary["total_items"] == 2
        assert summary["processing"] is False
        assert summary["status_counts"]["queued"] == 2


# ============================================
# ANALYTICS TRACKER TESTS
# ============================================

class TestAnalyticsTracker:
    """Test AnalyticsTracker"""
    
    def test_analytics_config_defaults(self):
        """Test analytics config defaults"""
        config = AnalyticsConfig()
        
        assert config.cache_duration_minutes == 60
        assert config.include_revenue is False
        assert len(config.default_metrics) == 4
    
    @pytest.mark.asyncio
    @patch("services.youtube_uploader.analytics.AuthManager")
    async def test_get_video_stats_with_mock(self, mock_auth):
        """Test getting video stats with mocked API"""
        # Mock auth manager and YouTube API
        mock_auth_instance = Mock()
        mock_youtube = Mock()
        mock_auth_instance.get_youtube_client = AsyncMock(return_value=mock_youtube)
        
        # Mock API response
        mock_response = {
            "items": [{
                "id": "test_video",
                "snippet": {
                    "title": "Test Video",
                    "publishedAt": "2024-01-01T00:00:00Z"
                },
                "statistics": {
                    "viewCount": "1000",
                    "likeCount": "50",
                    "commentCount": "10"
                }
            }]
        }
        
        mock_youtube.videos().list().execute = Mock(return_value=mock_response)
        
        tracker = AnalyticsTracker(mock_auth_instance)
        
        # Mock the asyncio.to_thread
        with patch("asyncio.to_thread", side_effect=lambda f, **kwargs: mock_response):
            stats = await tracker.get_video_stats("test", "test_video", use_cache=False)
            
            assert stats.video_id == "test_video"
            assert stats.title == "Test Video"
            assert stats.views == 1000
            assert stats.likes == 50
            assert stats.comments == 10
            assert stats.engagement_rate > 0


# ============================================
# INTEGRATION TESTS
# ============================================

class TestIntegration:
    """Integration tests"""
    
    @pytest.mark.skip("Requires actual YouTube API credentials")
    @pytest.mark.asyncio
    async def test_full_upload_workflow(self, auth_config, sample_video, sample_metadata):
        """Test complete upload workflow"""
        # This test requires actual credentials and should be run manually
        auth = AuthManager(auth_config)
        uploader = VideoUploader(auth)
        
        result = await uploader.upload(
            account_name="test",
            video_path=str(sample_video),
            metadata=sample_metadata
        )
        
        assert result.video_id is not None
        assert result.status == UploadStatus.COMPLETED


# ============================================
# PERFORMANCE TESTS
# ============================================

class TestPerformance:
    """Performance tests"""
    
    @pytest.mark.asyncio
    async def test_queue_handling_multiple_items(self, queue_config, sample_metadata, sample_video):
        """Test queue handling many items"""
        mock_auth = Mock()
        mock_uploader = Mock()
        
        queue = UploadQueue(mock_auth, mock_uploader, queue_config)
        
        # Add 100 items
        import time
        start = time.time()
        
        for i in range(100):
            await queue.add(
                account_name="test",
                video_path=str(sample_video),
                metadata=sample_metadata
            )
        
        elapsed = time.time() - start
        
        assert len(queue._queue) == 100
        assert elapsed < 1.0  # Should complete in < 1 second


# ============================================
# ERROR HANDLING TESTS
# ============================================

class TestErrorHandling:
    """Error handling tests"""
    
    @pytest.mark.asyncio
    async def test_upload_nonexistent_file(self, upload_config, sample_metadata):
        """Test uploading nonexistent file"""
        mock_auth = Mock()
        uploader = VideoUploader(mock_auth, upload_config)
        
        with pytest.raises(FileNotFoundError):
            await uploader.upload(
                account_name="test",
                video_path="nonexistent.mp4",
                metadata=sample_metadata
            )
    
    @pytest.mark.asyncio
    async def test_queue_cancel_upload(self, queue_config, sample_metadata, sample_video):
        """Test canceling upload"""
        mock_auth = Mock()
        mock_uploader = Mock()
        
        queue = UploadQueue(mock_auth, mock_uploader, queue_config)
        
        item_id = await queue.add(
            account_name="test",
            video_path=str(sample_video),
            metadata=sample_metadata
        )
        
        await queue.cancel(item_id)
        
        item = queue.get_item(item_id)
        assert item.status == QueueStatus.CANCELLED
    
    @pytest.mark.asyncio
    async def test_invalid_thumbnail_size(self, upload_config, temp_dir):
        """Test thumbnail size validation"""
        mock_auth = Mock()
        uploader = VideoUploader(mock_auth, upload_config)
        
        # Create large thumbnail (> 2MB)
        large_thumbnail = temp_dir / "large.jpg"
        large_thumbnail.write_bytes(b"x" * (3 * 1024 * 1024))
        
        with pytest.raises(ValueError, match="2MB"):
            await uploader.upload_thumbnail(
                "test",
                "video_id",
                str(large_thumbnail)
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
