"""
Comprehensive Tests for Video Assembler Service

Tests cover:
- TTS Engine (voice generation, caching, SSML)
- Timeline Builder (scene creation, transitions, optimization)
- Video Renderer (composition, effects, export)
- Video Assembler (full pipeline integration)

Run with: pytest tests/unit/test_video_assembler.py -v
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import tempfile

from src.services.video_assembler import (
    # TTS
    TTSEngine,
    TTSConfig,
    Voice,
    TTSResult,
    # Timeline
    TimelineBuilder,
    Timeline,
    Scene,
    Asset,
    AssetType,
    Transition,
    TransitionType,
    TimelineConfig,
    BackgroundMusic,
    # Renderer
    VideoRenderer,
    RenderConfig,
    QualityPreset,
    QualitySettings,
    # Assembler
    VideoAssembler,
    VideoConfig,
    AssembledVideo,
    VideoStatus,
)


# ============================
# TTS Engine Tests
# ============================

class TestTTSEngine:
    """Tests for TTSEngine."""
    
    def test_tts_config_defaults(self):
        """Test default TTS configuration."""
        config = TTSConfig()
        
        assert config.voice == Voice.FEMALE_CALM
        assert config.speaking_rate == 1.0
        assert config.sample_rate == 22050
        assert config.enable_cache is True
    
    def test_tts_config_custom(self):
        """Test custom TTS configuration."""
        config = TTSConfig(
            voice=Voice.MALE_DEEP,
            speaking_rate=0.8,
            sample_rate=44100,
            enable_cache=False,
        )
        
        assert config.voice == Voice.MALE_DEEP
        assert config.speaking_rate == 0.8
        assert config.sample_rate == 44100
        assert config.enable_cache is False
    
    @pytest.mark.skip(reason="Requires Coqui TTS installation")
    async def test_tts_generate(self):
        """Test TTS audio generation."""
        engine = TTSEngine()
        await engine.initialize()
        
        result = await engine.generate(
            text="This is a test of text-to-speech.",
            voice=Voice.FEMALE_CALM,
            save_to_file=False,
        )
        
        assert isinstance(result, TTSResult)
        assert result.duration > 0
        assert result.audio_data is not None
        assert result.voice_used == Voice.FEMALE_CALM.value
    
    @pytest.mark.skip(reason="Requires Coqui TTS installation")
    async def test_tts_batch_generation(self):
        """Test batch TTS generation."""
        engine = TTSEngine()
        await engine.initialize()
        
        texts = [
            "First segment.",
            "Second segment.",
            "Third segment.",
        ]
        
        results = await engine.generate_batch(texts)
        
        assert len(results) == 3
        assert all(isinstance(r, TTSResult) for r in results)
        assert all(r.duration > 0 for r in results)
    
    async def test_tts_duration_estimation(self):
        """Test TTS duration estimation."""
        engine = TTSEngine()
        
        text = "This is a test with approximately ten words here."
        duration = await engine.estimate_duration(text, speaking_rate=1.0)
        
        # ~10 words at 150 wpm = ~4 seconds
        assert 3 < duration < 6
    
    def test_tts_cache_key_generation(self):
        """Test cache key generation."""
        engine = TTSEngine()
        
        key1 = engine._get_cache_key("test", Voice.FEMALE_CALM, 1.0)
        key2 = engine._get_cache_key("test", Voice.FEMALE_CALM, 1.0)
        key3 = engine._get_cache_key("test", Voice.MALE_DEEP, 1.0)
        
        assert key1 == key2  # Same inputs = same key
        assert key1 != key3  # Different voice = different key


# ============================
# Timeline Builder Tests
# ============================

class TestTimelineBuilder:
    """Tests for TimelineBuilder."""
    
    def test_timeline_config_defaults(self):
        """Test default timeline configuration."""
        config = TimelineConfig()
        
        assert config.min_scene_duration == 3.0
        assert config.max_scene_duration == 10.0
        assert config.default_transition == TransitionType.FADE
        assert config.fps == 30
    
    def test_scene_creation(self):
        """Test scene creation with assets."""
        with tempfile.NamedTemporaryFile(suffix=".mp4") as tmp:
            tmp.write(b"fake video data")
            tmp.flush()
            
            asset = Asset(
                path=Path(tmp.name),
                type=AssetType.VIDEO,
                duration=5.0,
            )
            
            scene = Scene(
                assets=[asset],
                duration=5.0,
                script_segment="Test scene",
            )
            
            assert len(scene.assets) == 1
            assert scene.duration == 5.0
            assert scene.script_segment == "Test scene"
    
    def test_transition_creation(self):
        """Test transition creation."""
        transition = Transition(
            type=TransitionType.FADE,
            duration=0.5,
        )
        
        assert transition.type == TransitionType.FADE
        assert transition.duration == 0.5
    
    def test_transition_validation(self):
        """Test transition parameter validation."""
        # Negative duration should raise error
        with pytest.raises(ValueError):
            Transition(duration=-1.0)
        
        # Too long duration should raise error
        with pytest.raises(ValueError):
            Transition(duration=5.0)
    
    def test_detect_asset_type(self):
        """Test asset type detection."""
        builder = TimelineBuilder()
        
        assert builder._detect_asset_type(Path("video.mp4")) == AssetType.VIDEO
        assert builder._detect_asset_type(Path("image.jpg")) == AssetType.IMAGE
        assert builder._detect_asset_type(Path("photo.png")) == AssetType.IMAGE
        
        with pytest.raises(ValueError):
            builder._detect_asset_type(Path("unknown.xyz"))
    
    @pytest.mark.skip(reason="Requires audio files")
    async def test_build_timeline(self):
        """Test timeline building."""
        builder = TimelineBuilder()
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix=".mp4") as vid1, \
             tempfile.NamedTemporaryFile(suffix=".mp4") as vid2, \
             tempfile.NamedTemporaryFile(suffix=".wav") as aud1, \
             tempfile.NamedTemporaryFile(suffix=".wav") as aud2:
            
            script_segments = ["Segment 1", "Segment 2"]
            narration_paths = [Path(aud1.name), Path(aud2.name)]
            assets = [Path(vid1.name), Path(vid2.name)]
            
            timeline = await builder.build(
                script_segments=script_segments,
                narration_paths=narration_paths,
                assets=assets,
            )
            
            assert isinstance(timeline, Timeline)
            assert timeline.scene_count == 2
    
    def test_timeline_from_scenes(self):
        """Test Timeline creation from scenes."""
        with tempfile.NamedTemporaryFile(suffix=".mp4") as tmp:
            tmp.write(b"fake video data")
            tmp.flush()
            
            asset = Asset(path=Path(tmp.name), type=AssetType.VIDEO)
            scene1 = Scene(assets=[asset], duration=5.0)
            scene2 = Scene(assets=[asset], duration=7.0)
            
            timeline = Timeline.from_scenes(
                scenes=[scene1, scene2],
                config=TimelineConfig(),
            )
            
            assert timeline.scene_count == 2
            assert timeline.total_duration == 12.0
            assert timeline.video_assets > 0


# ============================
# Video Renderer Tests
# ============================

class TestVideoRenderer:
    """Tests for VideoRenderer."""
    
    def test_quality_preset_settings(self):
        """Test quality preset to settings conversion."""
        settings_1080p = QualitySettings.from_preset(QualityPreset.HD_1080P)
        
        assert settings_1080p.resolution == (1920, 1080)
        assert settings_1080p.fps == 30
        assert settings_1080p.bitrate == "8000k"
        
        settings_4k = QualitySettings.from_preset(QualityPreset.UHD_4K)
        
        assert settings_4k.resolution == (3840, 2160)
        assert settings_4k.fps == 30
        assert settings_4k.bitrate == "35000k"
    
    def test_render_config_defaults(self):
        """Test default render configuration."""
        config = RenderConfig()
        
        assert config.quality == QualityPreset.HD_1080P
        assert config.threads == 4
        assert config.use_gpu is False
        assert config.add_watermark is False
    
    def test_render_config_custom_quality(self):
        """Test custom quality settings."""
        custom = QualitySettings(
            resolution=(1280, 720),
            fps=60,
            bitrate="10000k",
            preset="fast",
        )
        
        config = RenderConfig(custom_settings=custom)
        settings = config.get_quality_settings()
        
        assert settings.resolution == (1280, 720)
        assert settings.fps == 60
        assert settings.preset == "fast"
    
    @pytest.mark.skip(reason="Requires MoviePy and video files")
    async def test_render_video(self):
        """Test video rendering."""
        renderer = VideoRenderer()
        
        # Create mock timeline
        # (Actual test would need real video/audio files)
        pass
    
    def test_estimate_render_time(self):
        """Test render time estimation."""
        renderer = VideoRenderer()
        
        # Create mock timeline
        with tempfile.NamedTemporaryFile(suffix=".mp4") as tmp:
            tmp.write(b"fake video data")
            tmp.flush()
            
            asset = Asset(path=Path(tmp.name), type=AssetType.VIDEO)
            scene = Scene(assets=[asset], duration=10.0)
            
            timeline = Timeline.from_scenes(
                scenes=[scene],
                config=TimelineConfig(),
            )
            
            # Estimate for 1080p
            estimate = renderer.estimate_render_time(
                timeline,
                QualityPreset.HD_1080P
            )
            
            # Should be positive and reasonable
            assert estimate > 0
            assert estimate < 1000  # Not crazy long


# ============================
# Video Assembler Tests
# ============================

class TestVideoAssembler:
    """Tests for VideoAssembler (full pipeline)."""
    
    def test_video_config_defaults(self):
        """Test default video configuration."""
        config = VideoConfig()
        
        assert config.voice == Voice.FEMALE_CALM
        assert config.speaking_rate == 1.0
        assert config.quality == QualityPreset.HD_1080P
        assert config.enable_cache is True
    
    def test_assembled_video_model(self):
        """Test AssembledVideo model creation."""
        video = AssembledVideo(
            video_path="/path/to/video.mp4",
            script="Test script",
            niche="meditation",
            duration=60.0,
            file_size=1024*1024,
            resolution=(1920, 1080),
            fps=30,
            voice_used=Voice.FEMALE_CALM.value,
            audio_duration=58.0,
            scene_count=3,
            asset_count=3,
            assembly_time=120.0,
            render_time=90.0,
        )
        
        assert video.duration == 60.0
        assert video.scene_count == 3
        assert video.status == VideoStatus.COMPLETED
    
    def test_script_splitting(self):
        """Test script segmentation."""
        assembler = VideoAssembler()
        
        # Test paragraph splitting
        script1 = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        segments1 = assembler._split_script(script1)
        
        assert len(segments1) == 3
        assert "First" in segments1[0]
        assert "Second" in segments1[1]
        
        # Test sentence splitting
        script2 = "First sentence. Second sentence. Third sentence."
        segments2 = assembler._split_script(script2)
        
        assert len(segments2) >= 1
    
    @pytest.mark.skip(reason="Requires full pipeline dependencies")
    async def test_assemble_video(self):
        """Test complete video assembly."""
        assembler = VideoAssembler()
        
        script = "This is a test meditation script for video assembly."
        niche = "meditation"
        
        # Would need real assets
        with tempfile.NamedTemporaryFile(suffix=".mp4") as tmp:
            tmp.write(b"fake video data")
            tmp.flush()
            
            assets = [Path(tmp.name)]
            
            # Mock progress callback
            progress_calls = []
            def progress_callback(status: str, progress: float):
                progress_calls.append((status, progress))
            
            result = await assembler.assemble(
                script=script,
                niche=niche,
                assets=assets,
                progress_callback=progress_callback,
            )
            
            assert isinstance(result, AssembledVideo)
            assert result.status in [VideoStatus.COMPLETED, VideoStatus.FAILED]
            assert len(progress_calls) > 0
    
    @pytest.mark.skip(reason="Requires full pipeline dependencies")
    async def test_assemble_batch(self):
        """Test batch video assembly."""
        assembler = VideoAssembler()
        
        scripts = [
            ("Script 1", "meditation", []),
            ("Script 2", "motivation", []),
        ]
        
        results = await assembler.assemble_batch(scripts)
        
        assert len(results) == 2
        assert all(isinstance(r, AssembledVideo) for r in results)


# ============================
# Integration Tests
# ============================

class TestIntegration:
    """Integration tests for complete workflows."""
    
    @pytest.mark.skip(reason="Requires all dependencies")
    async def test_full_pipeline(self):
        """Test complete video assembly pipeline."""
        # 1. Initialize components
        assembler = VideoAssembler(
            config=VideoConfig(
                quality=QualityPreset.DRAFT,  # Fast for testing
                enable_cache=False,
            )
        )
        
        # 2. Prepare inputs
        script = """
        Welcome to this peaceful meditation.
        
        Take a deep breath in, and slowly exhale.
        
        Let all tension leave your body.
        """
        
        niche = "meditation"
        
        # 3. Create temporary assets
        with tempfile.TemporaryDirectory() as tmpdir:
            # Would create real test assets here
            assets = []
            
            # 4. Assemble video
            result = await assembler.assemble(
                script=script,
                niche=niche,
                assets=assets or [Path(tmpdir) / "dummy.mp4"],
                title="Test Meditation",
            )
            
            # 5. Verify result
            assert result.status == VideoStatus.COMPLETED
            assert Path(result.video_path).exists()
            assert result.duration > 0
            assert result.scene_count > 0


# ============================
# Performance Tests
# ============================

class TestPerformance:
    """Performance and optimization tests."""
    
    async def test_tts_caching_benefit(self):
        """Test that caching improves TTS performance."""
        engine = TTSEngine(
            config=TTSConfig(enable_cache=True)
        )
        
        # First generation (cache miss) would be slower
        # Second generation (cache hit) should be much faster
        
        # Note: Actual performance test would measure times
        # This is a placeholder for the pattern
        pass
    
    def test_render_time_estimation_accuracy(self):
        """Test that render time estimates are reasonable."""
        renderer = VideoRenderer()
        
        # Create test timeline
        with tempfile.NamedTemporaryFile(suffix=".mp4") as tmp:
            tmp.write(b"fake video data")
            tmp.flush()
            
            asset = Asset(path=Path(tmp.name), type=AssetType.VIDEO)
            scenes = [Scene(assets=[asset], duration=10.0) for _ in range(5)]
            
            timeline = Timeline.from_scenes(
                scenes=scenes,
                config=TimelineConfig(),
            )
            
            # Get estimates for different qualities
            draft_time = renderer.estimate_render_time(timeline, QualityPreset.DRAFT)
            hd_time = renderer.estimate_render_time(timeline, QualityPreset.HD_1080P)
            uhd_time = renderer.estimate_render_time(timeline, QualityPreset.UHD_4K)
            
            # Higher quality should take longer
            assert draft_time < hd_time < uhd_time


# ============================
# Error Handling Tests
# ============================

class TestErrorHandling:
    """Tests for error handling and recovery."""
    
    def test_invalid_asset_path(self):
        """Test handling of missing asset files."""
        with pytest.raises(FileNotFoundError):
            Asset(
                path=Path("/nonexistent/file.mp4"),
                type=AssetType.VIDEO,
            )
    
    def test_invalid_scene_duration(self):
        """Test handling of invalid scene durations."""
        with tempfile.NamedTemporaryFile(suffix=".mp4") as tmp:
            tmp.write(b"fake video data")
            tmp.flush()
            
            asset = Asset(path=Path(tmp.name), type=AssetType.VIDEO)
            
            with pytest.raises(ValueError):
                Scene(assets=[asset], duration=-5.0)
    
    def test_empty_script_handling(self):
        """Test handling of empty scripts."""
        assembler = VideoAssembler()
        
        segments = assembler._split_script("")
        
        # Should return at least one segment
        assert len(segments) >= 1
    
    async def test_assembly_failure_graceful(self):
        """Test that assembly failures are handled gracefully."""
        assembler = VideoAssembler()
        
        # Intentionally cause failure with invalid inputs
        result = await assembler.assemble(
            script="Test",
            niche="test",
            assets=[],  # No assets
        )
        
        # Should return failed status, not crash
        assert result.status == VideoStatus.FAILED
        assert len(result.errors) > 0


# ============================
# Fixtures
# ============================

@pytest.fixture
def sample_script():
    """Sample script for testing."""
    return """
    Welcome to this guided meditation session.
    
    Find a comfortable position and close your eyes.
    
    Take a deep breath in through your nose.
    
    Hold for a moment, then slowly exhale.
    
    Continue breathing naturally and deeply.
    """


@pytest.fixture
def sample_assets(tmp_path):
    """Create sample asset files for testing."""
    # Create dummy video file
    video1 = tmp_path / "video1.mp4"
    video1.write_bytes(b"fake video data")
    
    video2 = tmp_path / "video2.mp4"
    video2.write_bytes(b"fake video data 2")
    
    return [video1, video2]


@pytest.fixture
def sample_audio(tmp_path):
    """Create sample audio file for testing."""
    audio = tmp_path / "narration.wav"
    audio.write_bytes(b"fake audio data")
    
    return audio


# ============================
# Main Test Runner
# ============================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
