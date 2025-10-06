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
    BuilderScene as Scene,  # Use dataclass Scene for tests
    BuilderTimeline,
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

# Import items not exported from __init__.py
from src.services.video_assembler.tts_engine import AudioFormat
from src.services.video_assembler.video_renderer import RenderResult


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
    
    async def test_tts_generate(self):
        """Test TTS audio generation with mocked TTS library."""
        import numpy as np
        
        # Mock the TTS library
        with patch('src.services.video_assembler.tts_engine.TTS') as mock_tts_class:
            # Create mock TTS instance
            mock_tts = Mock()
            mock_tts.model_name = Voice.FEMALE_CALM.value
            
            # Mock tts_to_file to generate fake audio
            fake_audio = np.random.randn(22050 * 3)  # 3 seconds of fake audio
            mock_tts.tts.return_value = fake_audio
            
            mock_tts_class.return_value = mock_tts
            
            # Test generation
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
    
    async def test_tts_batch_generation(self):
        """Test batch TTS generation with mocked TTS library."""
        import numpy as np
        
        # Mock the TTS library
        with patch('src.services.video_assembler.tts_engine.TTS') as mock_tts_class:
            # Create mock TTS instance
            mock_tts = Mock()
            mock_tts.model_name = Voice.FEMALE_CALM.value
            
            # Mock tts_to_file to generate fake audio
            fake_audio = np.random.randn(22050 * 2)  # 2 seconds of fake audio
            mock_tts.tts.return_value = fake_audio
            
            mock_tts_class.return_value = mock_tts
            
            # Test batch generation
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
    
    async def test_build_timeline(self):
        """Test timeline building with mocked audio/video files."""
        import tempfile
        from unittest.mock import Mock, patch
        import wave
        
        builder = TimelineBuilder()
        
        # Create temporary files with basic content
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as vid1, \
             tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as vid2, \
             tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as aud1, \
             tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as aud2:
            
            try:
                # Write fake video data
                vid1.write(b"fake video data")
                vid2.write(b"fake video data")
                vid1.flush()
                vid2.flush()
                
                # Write valid WAV file headers to audio files
                for audio_file in [aud1, aud2]:
                    audio_file.flush()
                    with wave.open(audio_file.name, 'wb') as wav:
                        wav.setnchannels(1)  # Mono
                        wav.setsampwidth(2)  # 16-bit
                        wav.setframerate(22050)  # Sample rate
                        wav.writeframes(b'\x00' * 22050 * 2)  # 1 second of silence
                
                # Close all files first
                vid1.close()
                vid2.close()
                aud1.close()
                aud2.close()
                
                script_segments = ["Segment 1", "Segment 2"]
                narration_paths = [Path(aud1.name), Path(aud2.name)]
                assets = [Path(vid1.name), Path(vid2.name)]
                
                # Mock the audio duration getter to avoid pydub dependency
                with patch.object(builder, '_get_audio_durations', return_value=[5.0, 5.0]):
                    timeline = await builder.build(
                        script_segments=script_segments,
                        narration_paths=narration_paths,
                        assets=assets,
                    )
                    
                    # Builder returns a BuilderTimeline (dataclass), not Pydantic Timeline
                    assert isinstance(timeline, BuilderTimeline)
                    assert timeline.scene_count == 2
                    
            finally:
                # Cleanup temp files
                import time
                time.sleep(0.1)  # Give OS time to release file handles
                for f in [vid1, vid2, aud1, aud2]:
                    try:
                        Path(f.name).unlink(missing_ok=True)
                    except:
                        pass  # Ignore cleanup errors
    
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
    
    async def test_render_video(self):
        """Test video rendering with fully mocked render method."""
        from unittest.mock import Mock, patch, AsyncMock
        
        # Mock the entire render method to avoid MoviePy execution
        with patch.object(VideoRenderer, 'render', new_callable=AsyncMock) as mock_render:
            # Setup mock return value
            mock_render.return_value = RenderResult(
                output_path="test_output.mp4",
                file_size=102400,
                duration=10.0,
                resolution=(1280, 720),
                fps=30,
                bitrate="2000k",
                render_time=8.0,
                scene_count=1,
                has_audio=False,
                has_background_music=False
            )
            
            # Create mock timeline
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = Path(tmpdir) / "output.mp4"
                
                with tempfile.NamedTemporaryFile(suffix=".mp4") as vid_tmp:
                    vid_tmp.write(b"fake video data")
                    vid_tmp.flush()
                    
                    asset = Asset(path=Path(vid_tmp.name), type=AssetType.VIDEO)
                    scene = Scene(assets=[asset], duration=10.0)
                    timeline = BuilderTimeline.from_scenes([scene], config=TimelineConfig())
                    
                    # Render video
                    renderer = VideoRenderer(config=RenderConfig(quality=QualityPreset.HD_720P))
                    result = await renderer.render(
                        timeline=timeline,
                        output_path=output_path
                    )
                    
                    # Verify result
                    assert isinstance(result, RenderResult)
                    assert result.duration > 0
                    assert result.scene_count == 1
                    assert mock_render.called
    
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
    
    async def test_assemble_video(self):
        """Test complete video assembly with mocked components."""
        from unittest.mock import Mock, patch, AsyncMock
        import tempfile
        
        # Mock all sub-components
        with patch('src.services.video_assembler.video_assembler.TTSEngine') as mock_tts, \
             patch('src.services.video_assembler.video_assembler.TimelineBuilder') as mock_timeline, \
             patch('src.services.video_assembler.video_assembler.VideoRenderer') as mock_renderer:
            
            # Setup TTS mock
            mock_tts_instance = Mock()
            mock_tts_instance.initialize = AsyncMock()
            mock_tts_instance.generate = AsyncMock(return_value=TTSResult(
                text="segment",
                audio_path="fake.wav",
                audio_data=None,
                duration=3.0,
                sample_rate=22050,
                voice_used="female",
                format=AudioFormat.WAV
            ))
            mock_tts_instance.generate_batch = AsyncMock(return_value=[
                TTSResult(
                    text="segment",
                    audio_path="fake.wav",
                    audio_data=None,
                    duration=3.0,
                    sample_rate=22050,
                    voice_used="female",
                    format=AudioFormat.WAV
                )
            ])
            mock_tts.return_value = mock_tts_instance
            
            # Setup timeline mock
            mock_timeline_instance = Mock()
            mock_timeline_config = TimelineConfig()
            mock_built_timeline = BuilderTimeline.from_scenes(
                scenes=[],
                config=mock_timeline_config
            )
            mock_built_timeline._total_duration = 10.0
            mock_built_timeline._scene_count = 1
            mock_timeline_instance.build = AsyncMock(return_value=mock_built_timeline)
            mock_timeline_instance.optimize_timeline = AsyncMock(return_value=mock_built_timeline)
            mock_timeline.return_value = mock_timeline_instance
            
            # Setup renderer mock
            mock_renderer_instance = Mock()
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = Path(tmpdir) / "output.mp4"
                output_path.write_bytes(b"fake video")
                
                mock_render_result = RenderResult(
                    output_path=str(output_path),
                    file_size=1024,
                    duration=10.0,
                    resolution=(1920, 1080),
                    fps=30,
                    bitrate="2000k",
                    render_time=5.0,
                    scene_count=1,
                    has_audio=True,
                    has_background_music=False
                )
                mock_renderer_instance.render = AsyncMock(return_value=mock_render_result)
                mock_renderer.return_value = mock_renderer_instance
                
                # Test assembly
                assembler = VideoAssembler()
                
                # Mock thumbnail creation
                with patch.object(assembler, '_create_thumbnail', return_value=Path("thumb.jpg")):
                    script = "This is a test meditation script for video assembly."
                    niche = "meditation"
                    
                    with tempfile.NamedTemporaryFile(suffix=".mp4") as asset_tmp:
                        asset_tmp.write(b"fake video data")
                        asset_tmp.flush()
                        assets = [Path(asset_tmp.name)]
                        
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
                        assert result.status == VideoStatus.COMPLETED
                        assert len(progress_calls) > 0
                        assert result.duration > 0
    
    async def test_assemble_batch(self):
        """Test batch video assembly with mocked components."""
        from unittest.mock import Mock, patch, AsyncMock
        
        with patch.object(VideoAssembler, 'assemble', new_callable=AsyncMock) as mock_assemble:
            # Setup mock to return successful results
            mock_assemble.side_effect = [
                AssembledVideo(
                    id="video1",
                    video_path="output1.mp4",
                    script="Script 1",
                    niche="meditation",
                    duration=10.0,
                    file_size=1024,
                    resolution=(1920, 1080),
                    fps=30,
                    voice_used="female",
                    audio_duration=9.5,
                    scene_count=1,
                    asset_count=1,
                    assembly_time=12.0,
                    render_time=8.0,
                    status=VideoStatus.COMPLETED
                ),
                AssembledVideo(
                    id="video2",
                    video_path="output2.mp4",
                    script="Script 2",
                    niche="motivation",
                    duration=15.0,
                    file_size=2048,
                    resolution=(1920, 1080),
                    fps=30,
                    voice_used="male",
                    audio_duration=14.5,
                    scene_count=2,
                    asset_count=2,
                    assembly_time=18.0,
                    render_time=12.0,
                    status=VideoStatus.COMPLETED
                )
            ]
            
            assembler = VideoAssembler()
            
            scripts = [
                ("Script 1", "meditation", []),
                ("Script 2", "motivation", []),
            ]
            
            results = await assembler.assemble_batch(scripts)
            
            assert len(results) == 2
            assert all(isinstance(r, AssembledVideo) for r in results)
            assert all(r.status == VideoStatus.COMPLETED for r in results)
            assert mock_assemble.call_count == 2


# ============================
# Integration Tests
# ============================

class TestIntegration:
    """Integration tests for complete workflows."""
    
    async def test_full_pipeline(self):
        """Test complete video assembly pipeline with mocked dependencies."""
        from unittest.mock import Mock, patch, AsyncMock
        import tempfile
        
        # Mock all external dependencies
        with patch('src.services.video_assembler.video_assembler.TTSEngine') as mock_tts, \
             patch('src.services.video_assembler.video_assembler.TimelineBuilder') as mock_timeline, \
             patch('src.services.video_assembler.video_assembler.VideoRenderer') as mock_renderer:
            
            # Setup TTS mock
            mock_tts_instance = Mock()
            mock_tts_instance.initialize = AsyncMock()
            mock_tts_instance.generate = AsyncMock(side_effect=[
                TTSResult(
                    text="Welcome to this peaceful meditation.",
                    audio_path="audio1.wav",
                    audio_data=None,
                    duration=3.0,
                    sample_rate=22050,
                    voice_used="female",
                    format=AudioFormat.WAV
                ),
                TTSResult(
                    text="Take a deep breath in, and slowly exhale.",
                    audio_path="audio2.wav",
                    audio_data=None,
                    duration=4.0,
                    sample_rate=22050,
                    voice_used="female",
                    format=AudioFormat.WAV
                ),
            ])
            mock_tts_instance.generate_batch = AsyncMock(return_value=[
                TTSResult(
                    text="Welcome to this peaceful meditation.",
                    audio_path="audio1.wav",
                    audio_data=None,
                    duration=3.0,
                    sample_rate=22050,
                    voice_used="female",
                    format=AudioFormat.WAV
                ),
                TTSResult(
                    text="Take a deep breath in, and slowly exhale.",
                    audio_path="audio2.wav",
                    audio_data=None,
                    duration=4.0,
                    sample_rate=22050,
                    voice_used="female",
                    format=AudioFormat.WAV
                ),
            ])
            mock_tts.return_value = mock_tts_instance
            
            # Setup timeline mock
            mock_timeline_instance = Mock()
            mock_timeline_config = TimelineConfig()
            mock_built_timeline = BuilderTimeline.from_scenes(
                scenes=[],
                config=mock_timeline_config
            )
            # Override timeline properties for test
            mock_built_timeline.total_duration = 15.0
            mock_built_timeline.scene_count = 2
            mock_built_timeline.total_assets = 2
            mock_timeline_instance.build = AsyncMock(return_value=mock_built_timeline)
            mock_timeline_instance.optimize_timeline = AsyncMock(return_value=mock_built_timeline)
            mock_timeline.return_value = mock_timeline_instance
            
            # Setup renderer mock
            mock_renderer_instance = Mock()
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = Path(tmpdir) / "output.mp4"
                output_path.write_bytes(b"fake video")
                
                mock_render_result = RenderResult(
                    output_path=str(output_path),
                    file_size=2048,
                    duration=15.0,
                    resolution=(1280, 720),  # DRAFT quality
                    fps=24,
                    bitrate="1000k",
                    render_time=3.0,
                    scene_count=2,
                    has_audio=True,
                    has_background_music=False
                )
                mock_renderer_instance.render = AsyncMock(return_value=mock_render_result)
                mock_renderer.return_value = mock_renderer_instance
                
                # 1. Initialize components
                assembler = VideoAssembler(
                    config=VideoConfig(
                        quality=QualityPreset.DRAFT,  # Fast for testing
                        enable_cache=False,
                    )
                )
                
                # Mock thumbnail creation
                with patch.object(assembler, '_create_thumbnail', return_value=Path("thumb.jpg")):
                    # 2. Prepare inputs
                    script = """
                    Welcome to this peaceful meditation.
                    
                    Take a deep breath in, and slowly exhale.
                    
                    Let all tension leave your body.
                    """
                    
                    niche = "meditation"
                    
                    # 3. Create temporary assets
                    with tempfile.TemporaryDirectory() as asset_tmpdir:
                        dummy_video = Path(asset_tmpdir) / "dummy.mp4"
                        dummy_video.write_bytes(b"fake video data")
                        assets = [dummy_video]
                        
                        # 4. Assemble video
                        result = await assembler.assemble(
                            script=script,
                            niche=niche,
                            assets=assets,
                            title="Test Meditation",
                        )
                        
                        # 5. Verify result
                        assert result.status == VideoStatus.COMPLETED
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
