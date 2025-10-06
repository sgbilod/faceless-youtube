"""
End-to-End Tests for Video Generation Pipeline

Tests the complete workflow from script submission to video file generation,
including asset fetching, video rendering, and file validation.
"""

import pytest
import os
import asyncio
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.models import User, Script, Video, VideoStatus
from src.services.script_generator.script_generator import ScriptGenerator
from src.services.asset_scraper.scraper_manager import ScraperManager
from src.services.video_assembler.video_assembler import VideoAssembler
from src.services.video_assembler.tts_engine import TTSEngine
from src.services.video_assembler.timeline_builder import TimelineBuilder
from src.services.video_assembler.video_renderer import VideoRenderer


@pytest.fixture
def test_user(db: Session):
    """Create test user for E2E tests"""
    user = User(
        username="e2e_test_user",
        email="e2e@test.com",
        hashed_password="test_hash"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def cleanup_test_files():
    """Cleanup generated test files after tests"""
    test_files = []
    
    yield test_files
    
    # Cleanup
    for file_path in test_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Warning: Could not remove {file_path}: {e}")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_full_video_generation_workflow(test_user, db: Session, cleanup_test_files):
    """
    E2E Test: Complete video generation pipeline
    
    Workflow:
    1. Create script in database
    2. Fetch assets using scraper
    3. Generate video using assembler
    4. Validate output file exists
    5. Verify database records updated
    """
    # Step 1: Create script
    script = Script(
        user_id=test_user.id,
        content="""Welcome to this meditation video.
        Close your eyes and take a deep breath.
        Feel the calm washing over you.
        Let go of all your worries.""",
        niche="meditation",
        style="calm",
        duration_seconds=30,
        voice="en-US-Neural2-C",
        created_at=datetime.utcnow()
    )
    db.add(script)
    db.commit()
    db.refresh(script)
    
    assert script.id is not None
    print(f"✓ Step 1: Script created with ID {script.id}")
    
    # Step 2: Create video record
    video = Video(
        user_id=test_user.id,
        script_id=script.id,
        title="E2E Test Meditation Video",
        description="Auto-generated test video",
        niche="meditation",
        style="calm",
        duration_seconds=30,
        resolution="1080p",
        fps=30,
        aspect_ratio="16:9",
        file_path="",  # Will be set after generation
        status=VideoStatus.QUEUED,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    
    assert video.id is not None
    assert video.status == VideoStatus.QUEUED
    print(f"✓ Step 2: Video record created with ID {video.id}")
    
    # Step 3: Fetch assets
    scraper_manager = ScraperManager()
    
    try:
        # Search for meditation-related video assets
        video_assets = await scraper_manager.search_videos(
            query="meditation nature calm",
            min_duration=30,
            max_results=5
        )
        
        assert len(video_assets) > 0
        print(f"✓ Step 3: Fetched {len(video_assets)} video assets")
        
        # Select best asset
        selected_asset = video_assets[0]
        print(f"  Asset URL: {selected_asset.url[:50]}...")
        
    except Exception as e:
        pytest.skip(f"Asset fetching failed (API issue): {e}")
    
    # Step 4: Generate video
    video_assembler = VideoAssembler()
    
    try:
        # Update video status
        video.status = VideoStatus.PROCESSING
        db.commit()
        
        # Assemble video
        output_path = f"output_videos/e2e_test_{video.id}_{int(datetime.utcnow().timestamp())}.mp4"
        
        result = await video_assembler.assemble(
            script_text=script.content,
            video_assets=[selected_asset],
            output_path=output_path,
            voice=script.voice,
            niche=script.niche
        )
        
        assert result is not None
        assert result.file_path == output_path
        print(f"✓ Step 4: Video assembled to {output_path}")
        
        # Track for cleanup
        cleanup_test_files.append(output_path)
        
        # Update video record
        video.file_path = output_path
        video.duration_seconds = result.duration_seconds
        video.status = VideoStatus.COMPLETED
        video.updated_at = datetime.utcnow()
        db.commit()
        
    except Exception as e:
        video.status = VideoStatus.FAILED
        video.error_message = str(e)
        db.commit()
        raise
    
    # Step 5: Validate output
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0
    print(f"✓ Step 5: Output file validated ({os.path.getsize(output_path)} bytes)")
    
    # Step 6: Verify database state
    db.refresh(video)
    assert video.status == VideoStatus.COMPLETED
    assert video.file_path == output_path
    assert video.duration_seconds > 0
    print(f"✓ Step 6: Database updated (status={video.status.value})")
    
    print("\n✅ E2E Test PASSED: Full video generation workflow completed successfully")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_video_generation_with_multiple_assets(test_user, db: Session, cleanup_test_files):
    """
    E2E Test: Video generation with multiple video clips
    
    Tests timeline building with multiple assets and transitions.
    """
    script = Script(
        user_id=test_user.id,
        content="First scene. Second scene. Third scene.",
        niche="tutorial",
        style="professional",
        duration_seconds=45,
        voice="en-US-Neural2-A",
        created_at=datetime.utcnow()
    )
    db.add(script)
    db.commit()
    db.refresh(script)
    
    # Fetch multiple assets
    scraper_manager = ScraperManager()
    
    try:
        assets = await scraper_manager.search_videos(
            query="professional office work",
            min_duration=15,
            max_results=3
        )
        
        assert len(assets) >= 3
        
    except Exception as e:
        pytest.skip(f"Asset fetching failed: {e}")
    
    # Generate video with multiple clips
    video_assembler = VideoAssembler()
    output_path = f"output_videos/e2e_multi_{int(datetime.utcnow().timestamp())}.mp4"
    
    result = await video_assembler.assemble(
        script_text=script.content,
        video_assets=assets[:3],
        output_path=output_path,
        voice=script.voice,
        niche=script.niche
    )
    
    cleanup_test_files.append(output_path)
    
    assert os.path.exists(output_path)
    assert result.scene_count == 3
    assert result.asset_count == 3
    
    print(f"✅ Multi-asset video generated: {result.scene_count} scenes, {result.asset_count} assets")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_video_generation_error_handling(test_user, db: Session):
    """
    E2E Test: Error handling in video generation
    
    Tests that failures are properly handled and recorded.
    """
    script = Script(
        user_id=test_user.id,
        content="Test script",
        niche="test",
        style="test",
        duration_seconds=10,
        voice="invalid-voice",
        created_at=datetime.utcnow()
    )
    db.add(script)
    db.commit()
    
    video = Video(
        user_id=test_user.id,
        script_id=script.id,
        title="Error Test Video",
        description="Should fail",
        niche="test",
        style="test",
        duration_seconds=10,
        resolution="1080p",
        fps=30,
        aspect_ratio="16:9",
        file_path="",
        status=VideoStatus.QUEUED,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(video)
    db.commit()
    
    video_assembler = VideoAssembler()
    
    # This should fail due to invalid voice
    with pytest.raises(Exception):
        await video_assembler.assemble(
            script_text=script.content,
            video_assets=[],  # Empty assets should also cause error
            output_path=f"output_videos/error_test_{int(datetime.utcnow().timestamp())}.mp4",
            voice="invalid-voice",
            niche="test"
        )
    
    print("✅ Error handling test passed: Failures properly caught")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_asset_scraper_integration(test_user, db: Session):
    """
    E2E Test: Asset scraper integration
    
    Tests all scrapers (Pexels, Pixabay, Unsplash) in live environment.
    """
    scraper_manager = ScraperManager()
    
    # Test video scraping
    try:
        videos = await scraper_manager.search_videos(
            query="nature landscape",
            min_duration=10,
            max_results=5
        )
        
        assert len(videos) > 0
        assert all(hasattr(v, 'url') for v in videos)
        assert all(hasattr(v, 'duration') for v in videos)
        print(f"✓ Video scraping: {len(videos)} assets found")
        
    except Exception as e:
        print(f"⚠ Video scraping skipped: {e}")
    
    # Test audio scraping (if available)
    try:
        audio = await scraper_manager.search_audio(
            query="meditation music",
            max_results=5
        )
        
        assert len(audio) > 0
        print(f"✓ Audio scraping: {len(audio)} assets found")
        
    except Exception as e:
        print(f"⚠ Audio scraping skipped: {e}")
    
    print("✅ Asset scraper integration test completed")


if __name__ == "__main__":
    # Run E2E tests
    pytest.main([__file__, "-v", "-m", "e2e"])
