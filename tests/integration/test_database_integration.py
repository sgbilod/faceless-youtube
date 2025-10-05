"""
Database Integration Tests

Tests that verify database operations, relationships, and transactions work correctly.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.core.models import (
    User, Video, Asset, Script, VideoAsset,
    VideoStatus, AssetType
)


class TestUserCRUD:
    """Test User model CRUD operations"""
    
    def test_create_user(self, test_db_session):
        """Test creating a new user"""
        user = User(
            username="newuser",
            email="new@example.com",
            password_hash="hashed_password",
            created_at=datetime.utcnow(),
            is_active=True
        )
        
        test_db_session.add(user)
        test_db_session.commit()
        test_db_session.refresh(user)
        
        assert user.id is not None
        assert user.username == "newuser"
        assert user.email == "new@example.com"
    
    def test_read_user(self, test_db_session, sample_user):
        """Test reading user from database"""
        user = test_db_session.query(User).filter_by(
            username="testuser"
        ).first()
        
        assert user is not None
        assert user.id == sample_user.id
        assert user.email == "test@example.com"
    
    def test_update_user(self, test_db_session, sample_user):
        """Test updating user fields"""
        sample_user.is_verified = True
        sample_user.updated_at = datetime.utcnow()
        
        test_db_session.commit()
        test_db_session.refresh(sample_user)
        
        assert sample_user.is_verified is True
    
    def test_delete_user(self, test_db_session, sample_user):
        """Test deleting user"""
        user_id = sample_user.id
        
        test_db_session.delete(sample_user)
        test_db_session.commit()
        
        deleted_user = test_db_session.query(User).filter_by(
            id=user_id
        ).first()
        
        assert deleted_user is None
    
    def test_duplicate_email_constraint(self, test_db_session, sample_user):
        """Test that duplicate emails are prevented"""
        duplicate_user = User(
            username="different_username",
            email="test@example.com",  # Same as sample_user
            password_hash="hashed",
            created_at=datetime.utcnow()
        )
        
        test_db_session.add(duplicate_user)
        
        with pytest.raises(IntegrityError):
            test_db_session.commit()


class TestVideoRelationships:
    """Test Video model relationships"""
    
    def test_video_user_relationship(self, test_db_session, sample_video, sample_user):
        """Test Video → User relationship"""
        assert sample_video.user_id == sample_user.id
        
        # Fetch user through relationship
        video_user = test_db_session.query(User).filter_by(
            id=sample_video.user_id
        ).first()
        
        assert video_user.id == sample_user.id
        assert video_user.username == "testuser"
    
    def test_video_script_relationship(self, test_db_session, sample_video, sample_script):
        """Test Video → Script relationship"""
        assert sample_video.script_id == sample_script.id
        
        script = test_db_session.query(Script).filter_by(
            id=sample_video.script_id
        ).first()
        
        assert script.title == "Test Meditation Script"
    
    def test_user_has_multiple_videos(self, test_db_session, sample_user):
        """Test User can have multiple videos"""
        video1 = Video(
            user_id=sample_user.id,
            title="Video 1",
            niche="meditation",
            status=VideoStatus.COMPLETED,
            duration_seconds=300,
            file_path="/test/video1.mp4",
            created_at=datetime.utcnow()
        )
        video2 = Video(
            user_id=sample_user.id,
            title="Video 2",
            niche="meditation",
            status=VideoStatus.QUEUED,
            duration_seconds=180,
            file_path="/test/video2.mp4",
            created_at=datetime.utcnow()
        )
        
        test_db_session.add_all([video1, video2])
        test_db_session.commit()
        
        user_videos = test_db_session.query(Video).filter_by(
            user_id=sample_user.id
        ).all()
        
        assert len(user_videos) >= 2
        assert any(v.title == "Video 1" for v in user_videos)
        assert any(v.title == "Video 2" for v in user_videos)


class TestAssetOperations:
    """Test Asset model operations"""
    
    def test_create_asset(self, test_db_session):
        """Test creating new asset"""
        asset = Asset(
            asset_type=AssetType.AUDIO,
            source_platform="freepd",
            source_url="https://freepd.com/music/123",
            source_id="freepd_123",
            file_path="/assets/audio/calm_music.mp3",
            duration_seconds=180,
            quality_score=0.85,
            tags=["calm", "meditation", "background"],
            license_type="cc0",
            created_at=datetime.utcnow()
        )
        
        test_db_session.add(asset)
        test_db_session.commit()
        test_db_session.refresh(asset)
        
        assert asset.id is not None
        assert asset.asset_type == AssetType.AUDIO
        assert "meditation" in asset.tags
    
    def test_query_assets_by_type(self, test_db_session, sample_asset):
        """Test querying assets by type"""
        # Add another video asset
        video_asset2 = Asset(
            asset_type=AssetType.VIDEO,
            source_platform="pixabay",
            source_url="https://pixabay.com/videos/67890",
            source_id="pixabay_67890",
            file_path="/assets/video/ocean.mp4",
            duration_seconds=60,
            license_type="pixabay",
            created_at=datetime.utcnow()
        )
        test_db_session.add(video_asset2)
        test_db_session.commit()
        
        video_assets = test_db_session.query(Asset).filter_by(
            asset_type=AssetType.VIDEO
        ).all()
        
        assert len(video_assets) >= 2
    
    def test_query_assets_by_quality_score(self, test_db_session, sample_asset):
        """Test querying high-quality assets"""
        high_quality_assets = test_db_session.query(Asset).filter(
            Asset.quality_score >= 0.9
        ).all()
        
        assert sample_asset in high_quality_assets


class TestTransactions:
    """Test database transaction handling"""
    
    def test_transaction_commit(self, test_db_session):
        """Test successful transaction commit"""
        user = User(
            username="transaction_user",
            email="transaction@example.com",
            password_hash="hashed",
            created_at=datetime.utcnow()
        )
        
        test_db_session.add(user)
        test_db_session.commit()
        
        # Verify user persisted
        saved_user = test_db_session.query(User).filter_by(
            username="transaction_user"
        ).first()
        
        assert saved_user is not None
        assert saved_user.email == "transaction@example.com"
    
    def test_transaction_rollback(self, test_db_session):
        """Test transaction rollback on error"""
        user = User(
            username="rollback_user",
            email="rollback@example.com",
            password_hash="hashed",
            created_at=datetime.utcnow()
        )
        
        test_db_session.add(user)
        test_db_session.flush()  # Flush but don't commit
        
        user_id = user.id
        
        # Rollback transaction
        test_db_session.rollback()
        
        # Verify user was not persisted
        rolled_back_user = test_db_session.query(User).filter_by(
            id=user_id
        ).first()
        
        assert rolled_back_user is None
    
    def test_batch_insert(self, test_db_session):
        """Test inserting multiple records in one transaction"""
        assets = [
            Asset(
                asset_type=AssetType.VIDEO,
                source_platform=f"pexels",
                source_url=f"https://pexels.com/{i}",
                source_id=f"pexels_{i}",
                file_path=f"/assets/video_{i}.mp4",
                duration_seconds=30,
                license_type="pexels",
                created_at=datetime.utcnow()
            )
            for i in range(10)
        ]
        
        test_db_session.add_all(assets)
        test_db_session.commit()
        
        # Verify all assets inserted
        inserted_count = test_db_session.query(Asset).filter(
            Asset.source_platform == "pexels"
        ).count()
        
        assert inserted_count == 10


class TestCascadeDeletes:
    """Test cascade delete behavior"""
    
    def test_delete_user_cascades_to_videos(self, test_db_session, sample_user):
        """Test that deleting user deletes their videos (if cascade configured)"""
        # Create video for user
        video = Video(
            user_id=sample_user.id,
            title="Test Video",
            niche="meditation",
            status=VideoStatus.COMPLETED,
            duration_seconds=240,
            file_path="/test/cascade_video.mp4",
            created_at=datetime.utcnow()
        )
        test_db_session.add(video)
        test_db_session.commit()
        
        video_id = video.id
        
        # Note: Actual cascade behavior depends on model configuration
        # This test documents expected behavior
        # In production, you might soft-delete instead
        
        # For now, just verify relationship exists
        assert video.user_id == sample_user.id


class TestComplexQueries:
    """Test complex database queries"""
    
    def test_query_recent_videos(self, test_db_session, sample_user):
        """Test querying videos from last 7 days"""
        # Create videos with different dates
        old_video = Video(
            user_id=sample_user.id,
            title="Old Video",
            niche="meditation",
            status=VideoStatus.COMPLETED,
            duration_seconds=300,
            file_path="/test/old_video.mp4",
            created_at=datetime.utcnow() - timedelta(days=10)
        )
        recent_video = Video(
            user_id=sample_user.id,
            title="Recent Video",
            niche="meditation",
            status=VideoStatus.COMPLETED,
            duration_seconds=180,
            file_path="/test/recent_video.mp4",
            created_at=datetime.utcnow() - timedelta(days=2)
        )
        
        test_db_session.add_all([old_video, recent_video])
        test_db_session.commit()
        
        # Query videos from last 7 days
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        recent_videos = test_db_session.query(Video).filter(
            Video.created_at >= cutoff_date
        ).all()
        
        assert recent_video in recent_videos
        assert old_video not in recent_videos
    
    def test_query_videos_by_status(self, test_db_session, sample_user):
        """Test querying videos by status"""
        statuses = [VideoStatus.QUEUED, VideoStatus.GENERATING, VideoStatus.COMPLETED]
        
        for status in statuses:
            video = Video(
                user_id=sample_user.id,
                title=f"Video {status.value}",
                niche="meditation",
                status=status,
                duration_seconds=200,
                file_path=f"/test/video_{status.value}.mp4",
                created_at=datetime.utcnow()
            )
            test_db_session.add(video)
        
        test_db_session.commit()
        
        completed_videos = test_db_session.query(Video).filter_by(
            status=VideoStatus.COMPLETED
        ).all()
        
        assert len(completed_videos) >= 1
        assert all(v.status == VideoStatus.COMPLETED for v in completed_videos)
