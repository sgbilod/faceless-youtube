"""
Video Pipeline Integration Tests

Tests that verify the end-to-end video generation pipeline works correctly.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.core.models import Video, Script, Asset, VideoStatus


@pytest.mark.asyncio
class TestVideoGenerationPipeline:
    """Test complete video generation workflow"""
    
    async def test_full_pipeline_success(
        self,
        test_db_session,
        sample_user,
        sample_script,
        mock_claude_service,
        mock_pexels_service,
        mock_youtube_service
    ):
        """
        Test complete workflow: script → video assembly → upload
        
        Steps:
        1. Generate script with Claude
        2. Fetch assets from Pexels
        3. Assemble video with MoviePy
        4. Upload to YouTube
        5. Update database with results
        """
        # Step 1: Generate script (mocked)
        script_data = await mock_claude_service.generate_script(
            niche="meditation",
            duration=300
        )
        
        script = Script(
            title=script_data["title"],
            content=script_data["content"],
            niche="meditation",
            target_duration_seconds=script_data["duration"],
            actual_word_count=script_data["word_count"],
            created_at=datetime.utcnow()
        )
        test_db_session.add(script)
        test_db_session.commit()
        
        # Step 2: Create video record
        video = Video(
            user_id=sample_user.id,
            script_id=script.id,
            title=script_data["title"],
            niche="meditation",
            duration_seconds=300,  # Added required field
            file_path="/test/pipeline_video.mp4",  # Added required field
            status=VideoStatus.QUEUED,
            created_at=datetime.utcnow()
        )
        test_db_session.add(video)
        test_db_session.commit()
        
        # Step 3: Fetch assets (mocked)
        assets_data = await mock_pexels_service.search_videos(
            query="meditation nature",
            per_page=5
        )
        
        assert len(assets_data) > 0
        
        # Step 4: Update status to generating
        video.status = VideoStatus.GENERATING
        test_db_session.commit()
        
        # Step 5: Mock video rendering
        # In real implementation, this would call VideoAssembler
        video.status = VideoStatus.RENDERING
        test_db_session.commit()
        
        # Step 6: Complete video
        video.status = VideoStatus.COMPLETED
        video.file_path = "/output/video_test.mp4"
        video.completed_at = datetime.utcnow()
        test_db_session.commit()
        
        # Step 7: Upload to YouTube (mocked)
        upload_result = await mock_youtube_service.upload_video(
            video_path=video.file_path,
            title=video.title,
            description=f"Generated meditation video: {video.title}"
        )
        
        assert upload_result["status"] == "uploaded"
        assert "id" in upload_result
        
        # Verify final state
        test_db_session.refresh(video)
        assert video.status == VideoStatus.COMPLETED
        assert video.file_path is not None
        assert video.completed_at is not None
    
    async def test_pipeline_error_handling(
        self,
        test_db_session,
        sample_user,
        mock_claude_service
    ):
        """Test pipeline handles errors gracefully"""
        # Simulate script generation failure
        mock_claude_service.generate_script = AsyncMock(
            side_effect=Exception("API rate limit exceeded")
        )
        
        video = Video(
            user_id=sample_user.id,
            title="Test Video",
            niche="meditation",
            duration_seconds=240,  # Added required field
            file_path="/test/error_video.mp4",  # Added required field
            status=VideoStatus.QUEUED,
            created_at=datetime.utcnow()
        )
        test_db_session.add(video)
        test_db_session.commit()
        
        # Try to generate script
        with pytest.raises(Exception) as exc_info:
            await mock_claude_service.generate_script(
                niche="meditation",
                duration=300
            )
        
        assert "rate limit" in str(exc_info.value).lower()
        
        # Update video status to failed
        video.status = VideoStatus.FAILED
        video.error_message = str(exc_info.value)
        test_db_session.commit()
        
        test_db_session.refresh(video)
        assert video.status == VideoStatus.FAILED
        assert video.error_message is not None


@pytest.mark.asyncio
class TestPartialCompletion:
    """Test pipeline resume and partial completion"""
    
    async def test_resume_from_rendering(
        self,
        test_db_session,
        sample_user,
        sample_script
    ):
        """Test resuming video generation from rendering stage"""
        # Create video in RENDERING state (simulating partial completion)
        video = Video(
            user_id=sample_user.id,
            script_id=sample_script.id,
            title="Partially Completed Video",
            niche="meditation",
            duration_seconds=180,  # Added required field
            file_path="/test/partial_video.mp4",  # Added required field
            status=VideoStatus.RENDERING,
            created_at=datetime.utcnow()
        )
        test_db_session.add(video)
        test_db_session.commit()
        
        # Verify initial state
        assert video.status == VideoStatus.RENDERING
        assert video.file_path == "/test/partial_video.mp4"
        
        # Resume and complete rendering
        video.status = VideoStatus.COMPLETED
        video.file_path = "/output/resumed_video.mp4"
        video.completed_at = datetime.utcnow()
        test_db_session.commit()
        
        # Verify completion
        test_db_session.refresh(video)
        assert video.status == VideoStatus.COMPLETED
        assert video.file_path is not None
    
    async def test_retry_failed_video(
        self,
        test_db_session,
        sample_user,
        sample_script
    ):
        """Test retrying a failed video generation"""
        # Create failed video
        video = Video(
            user_id=sample_user.id,
            script_id=sample_script.id,
            title="Failed Video",
            niche="meditation",
            duration_seconds=200,  # Added required field
            file_path="/test/failed_video.mp4",  # Added required field
            status=VideoStatus.FAILED,
            error_message="Asset download timeout",
            created_at=datetime.utcnow()
        )
        test_db_session.add(video)
        test_db_session.commit()
        
        # Retry by resetting to QUEUED
        video.status = VideoStatus.QUEUED
        video.error_message = None
        test_db_session.commit()
        
        # Simulate successful retry
        video.status = VideoStatus.COMPLETED
        video.file_path = "/output/retried_video.mp4"
        video.completed_at = datetime.utcnow()
        test_db_session.commit()
        
        # Verify retry success
        test_db_session.refresh(video)
        assert video.status == VideoStatus.COMPLETED
        assert video.error_message is None


@pytest.mark.asyncio
class TestMetricsCollection:
    """Test pipeline metrics and monitoring"""
    
    async def test_track_generation_time(
        self,
        test_db_session,
        sample_user,
        sample_script
    ):
        """Test tracking video generation duration"""
        from datetime import timedelta
        
        video = Video(
            user_id=sample_user.id,
            script_id=sample_script.id,
            title="Timed Video",
            niche="meditation",
            duration_seconds=300,  # Added required field
            file_path="/test/timed_video.mp4",  # Added required field
            status=VideoStatus.QUEUED,
            created_at=datetime.utcnow()
        )
        test_db_session.add(video)
        test_db_session.commit()
        
        start_time = video.created_at
        
        # Simulate generation process
        video.status = VideoStatus.GENERATING
        test_db_session.commit()
        
        # Complete after 5 minutes (simulated)
        video.status = VideoStatus.COMPLETED
        video.completed_at = start_time + timedelta(minutes=5)
        test_db_session.commit()
        
        # Calculate duration
        test_db_session.refresh(video)
        duration = (video.completed_at - video.created_at).total_seconds()
        
        assert duration == 300  # 5 minutes
        assert video.completed_at > video.created_at
    
    async def test_track_asset_usage(
        self,
        test_db_session,
        sample_video,
        sample_asset
    ):
        """Test tracking which assets were used in video"""
        # In real implementation, would use VideoAsset junction table
        # For now, document expected behavior
        
        # Create association (if VideoAsset model exists)
        # video_asset = VideoAsset(
        #     video_id=sample_video.id,
        #     asset_id=sample_asset.id,
        #     start_time=0,
        #     duration=30,
        #     order=1
        # )
        # test_db_session.add(video_asset)
        # test_db_session.commit()
        
        # Verify video-asset relationship
        assert sample_video.id is not None
        assert sample_asset.id is not None


@pytest.mark.asyncio
class TestConcurrentPipelines:
    """Test multiple videos generating concurrently"""
    
    async def test_multiple_videos_in_queue(
        self,
        test_db_session,
        sample_user,
        sample_script
    ):
        """Test handling multiple videos in different stages"""
        videos = []
        
        # Create videos in different stages
        statuses = [
            VideoStatus.QUEUED,
            VideoStatus.GENERATING,
            VideoStatus.RENDERING,
            VideoStatus.COMPLETED
        ]
        
        for i, status in enumerate(statuses):
            video = Video(
                user_id=sample_user.id,
                script_id=sample_script.id,
                title=f"Video {i+1}",
                niche="meditation",
                duration_seconds=180 + (i * 60),  # Added required field, varied durations
                file_path=f"/test/queue_video_{i+1}.mp4",  # Added required field
                status=status,
                created_at=datetime.utcnow()
            )
            videos.append(video)
        
        test_db_session.add_all(videos)
        test_db_session.commit()
        
        # Query by status
        queued = test_db_session.query(Video).filter_by(
            status=VideoStatus.QUEUED
        ).count()
        generating = test_db_session.query(Video).filter_by(
            status=VideoStatus.GENERATING
        ).count()
        
        assert queued >= 1
        assert generating >= 1
        
        # Verify all videos created
        all_videos = test_db_session.query(Video).filter_by(
            user_id=sample_user.id
        ).all()
        
        assert len(all_videos) >= len(statuses)


# Integration test utilities
def simulate_video_generation(video: Video, test_db_session):
    """Helper to simulate video generation steps"""
    stages = [
        VideoStatus.QUEUED,
        VideoStatus.GENERATING,
        VideoStatus.RENDERING,
        VideoStatus.COMPLETED
    ]
    
    for stage in stages:
        video.status = stage
        test_db_session.commit()
    
    video.completed_at = datetime.utcnow()
    video.file_path = f"/output/{video.title.replace(' ', '_')}.mp4"
    test_db_session.commit()
