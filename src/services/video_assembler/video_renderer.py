"""
Video Renderer using MoviePy

This module renders final videos from timelines using MoviePy,
with support for quality presets, progress tracking, and effects.

Features:
- Multiple quality presets (720p, 1080p, 4K)
- Progress tracking and callbacks
- GPU acceleration support (if available)
- Multi-threading for faster encoding
- Video effects (transitions, overlays, filters)
- Audio mixing and normalization
- Export optimization for YouTube/social media

Usage:
    renderer = VideoRenderer()
    result = await renderer.render(
        timeline=built_timeline,
        output_path="output.mp4",
        config=RenderConfig(quality=QualityPreset.HD_1080P)
    )
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field

try:
    from moviepy import VideoFileClip
    from moviepy import ImageClip
    from moviepy import CompositeVideoClip
    from moviepy import AudioFileClip
    from moviepy import CompositeAudioClip
    from moviepy import concatenate_videoclips
    from moviepy import TextClip
    # MoviePy 2.x changed the fx imports - they're now methods on clips
    # from moviepy.video.fx import fadein, fadeout, resize  # Old MoviePy 1.x
    # from moviepy.audio.fx import audio_fadein, audio_fadeout, volumex  # Old MoviePy 1.x
    MOVIEPY_AVAILABLE = True
except ImportError as e:
    VideoFileClip = None
    MOVIEPY_AVAILABLE = False
    import warnings
    warnings.warn(f"MoviePy not fully available: {e}")

from .timeline_builder import Timeline, Scene, TransitionType, AssetType

logger = logging.getLogger(__name__)


class QualityPreset(str, Enum):
    """Video quality presets optimized for different platforms."""
    
    # YouTube recommended
    HD_720P = "720p"  # 1280x720, 30fps, 5 Mbps
    HD_1080P = "1080p"  # 1920x1080, 30fps, 8 Mbps
    HD_1080P_60 = "1080p60"  # 1920x1080, 60fps, 12 Mbps
    UHD_4K = "4k"  # 3840x2160, 30fps, 35 Mbps
    
    # Social media optimized
    INSTAGRAM_SQUARE = "instagram_square"  # 1080x1080, 30fps
    INSTAGRAM_STORY = "instagram_story"  # 1080x1920, 30fps
    TIKTOK = "tiktok"  # 1080x1920, 30fps
    
    # Draft/preview
    DRAFT = "draft"  # 640x360, 30fps, fast encode


@dataclass
class QualitySettings:
    """Quality settings for video encoding."""
    resolution: tuple[int, int]
    fps: int
    bitrate: str
    audio_bitrate: str = "192k"
    codec: str = "libx264"
    audio_codec: str = "aac"
    preset: str = "medium"  # ultrafast, fast, medium, slow, slower
    
    @classmethod
    def from_preset(cls, preset: QualityPreset) -> "QualitySettings":
        """Create settings from quality preset."""
        presets = {
            QualityPreset.HD_720P: cls(
                resolution=(1280, 720),
                fps=30,
                bitrate="5000k",
                preset="medium"
            ),
            QualityPreset.HD_1080P: cls(
                resolution=(1920, 1080),
                fps=30,
                bitrate="8000k",
                preset="medium"
            ),
            QualityPreset.HD_1080P_60: cls(
                resolution=(1920, 1080),
                fps=60,
                bitrate="12000k",
                preset="slow"
            ),
            QualityPreset.UHD_4K: cls(
                resolution=(3840, 2160),
                fps=30,
                bitrate="35000k",
                preset="slow"
            ),
            QualityPreset.INSTAGRAM_SQUARE: cls(
                resolution=(1080, 1080),
                fps=30,
                bitrate="8000k",
                preset="medium"
            ),
            QualityPreset.INSTAGRAM_STORY: cls(
                resolution=(1080, 1920),
                fps=30,
                bitrate="8000k",
                preset="medium"
            ),
            QualityPreset.TIKTOK: cls(
                resolution=(1080, 1920),
                fps=30,
                bitrate="8000k",
                preset="medium"
            ),
            QualityPreset.DRAFT: cls(
                resolution=(640, 360),
                fps=30,
                bitrate="1500k",
                preset="ultrafast"
            ),
        }
        return presets[preset]


@dataclass
class RenderConfig:
    """Configuration for video rendering."""
    
    # Quality
    quality: QualityPreset = QualityPreset.HD_1080P
    custom_settings: Optional[QualitySettings] = None
    
    # Performance
    threads: int = 4
    use_gpu: bool = False
    
    # Output
    output_format: str = "mp4"
    temp_audiofile: Optional[Path] = None
    remove_temp: bool = True
    
    # Progress
    verbose: bool = True
    logger: Optional[str] = "bar"  # 'bar' or None
    
    # Effects
    add_watermark: bool = False
    watermark_text: Optional[str] = None
    watermark_position: str = "bottom_right"
    
    def get_quality_settings(self) -> QualitySettings:
        """Get quality settings (custom or from preset)."""
        if self.custom_settings:
            return self.custom_settings
        return QualitySettings.from_preset(self.quality)


class RenderResult(BaseModel):
    """Result of video rendering."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    output_path: str
    file_size: int  # bytes
    duration: float  # seconds
    resolution: tuple[int, int]
    fps: int
    bitrate: str
    
    # Timing
    render_time: float  # seconds
    rendered_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Metadata
    scene_count: int
    has_audio: bool
    has_background_music: bool
    
    class Config:
        arbitrary_types_allowed = True


class VideoRenderer:
    """
    Render videos from timelines using MoviePy.
    
    Handles video composition, transitions, effects, audio mixing,
    and export with quality optimization.
    """
    
    def __init__(self, config: Optional[RenderConfig] = None):
        """
        Initialize video renderer.
        
        Args:
            config: Render configuration
        """
        if VideoFileClip is None:
            raise ImportError(
                "MoviePy not installed. Install with: pip install moviepy"
            )
        
        self.config = config or RenderConfig()
        self._progress_callback: Optional[Callable[[float], None]] = None
    
    async def render(
        self,
        timeline: Timeline,
        output_path: Path,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> RenderResult:
        """
        Render timeline to video file.
        
        Args:
            timeline: Timeline to render
            output_path: Output video file path
            progress_callback: Optional callback for progress updates (0.0-1.0)
        
        Returns:
            RenderResult with metadata
        """
        import time
        
        self._progress_callback = progress_callback
        start_time = time.time()
        
        logger.info(f"Starting render: {timeline.scene_count} scenes, "
                   f"{timeline.total_duration:.1f}s")
        
        # Get quality settings
        quality = self.config.get_quality_settings()
        
        # Build video composition
        logger.info("Building video composition...")
        video_clips = await self._build_video_clips(timeline, quality)
        
        if self._progress_callback:
            self._progress_callback(0.3)
        
        # Composite video
        logger.info("Compositing video...")
        final_video = concatenate_videoclips(video_clips, method="compose")
        
        # Add background music if present
        if timeline.background_music:
            logger.info("Adding background music...")
            final_video = await self._add_background_music(
                final_video,
                timeline.background_music
            )
        
        if self._progress_callback:
            self._progress_callback(0.5)
        
        # Add watermark if enabled
        if self.config.add_watermark and self.config.watermark_text:
            logger.info("Adding watermark...")
            final_video = self._add_watermark(
                final_video,
                self.config.watermark_text
            )
        
        # Render to file
        logger.info(f"Rendering to {output_path}...")
        await self._write_video_file(
            final_video,
            output_path,
            quality
        )
        
        # Cleanup
        final_video.close()
        for clip in video_clips:
            clip.close()
        
        if self._progress_callback:
            self._progress_callback(1.0)
        
        # Calculate metrics
        render_time = time.time() - start_time
        file_size = output_path.stat().st_size
        
        result = RenderResult(
            output_path=str(output_path),
            file_size=file_size,
            duration=timeline.total_duration,
            resolution=quality.resolution,
            fps=quality.fps,
            bitrate=quality.bitrate,
            render_time=render_time,
            scene_count=timeline.scene_count,
            has_audio=timeline.has_narration,
            has_background_music=timeline.background_music is not None,
        )
        
        logger.info(f"Render complete: {render_time:.1f}s, "
                   f"{file_size / 1024 / 1024:.1f} MB")
        
        return result
    
    async def _build_video_clips(
        self,
        timeline: Timeline,
        quality: QualitySettings
    ) -> List:
        """
        Build video clips from timeline scenes.
        
        Args:
            timeline: Timeline with scenes
            quality: Quality settings for resolution/fps
        
        Returns:
            List of MoviePy clips
        """
        clips = []
        
        for scene in timeline.scenes:
            # Build scene clip
            scene_clip = await self._build_scene_clip(scene, quality)
            
            # Add transition effects
            if scene.transition_out:
                scene_clip = self._add_transition_out(
                    scene_clip,
                    scene.transition_out
                )
            
            clips.append(scene_clip)
        
        return clips
    
    async def _build_scene_clip(
        self,
        scene: Scene,
        quality: QualitySettings
    ) -> "CompositeVideoClip":
        """
        Build a single scene clip with assets and narration.
        
        Args:
            scene: Scene to build
            quality: Quality settings
        
        Returns:
            Composite video clip
        """
        # Load visual assets
        visual_clips = []
        
        for asset in scene.assets:
            if asset.type == AssetType.VIDEO:
                clip = await self._load_video_asset(asset, scene.duration, quality)
            elif asset.type == AssetType.IMAGE:
                clip = await self._load_image_asset(asset, scene.duration, quality)
            else:
                continue
            
            visual_clips.append(clip)
        
        # Composite visual layers
        if not visual_clips:
            raise ValueError(f"Scene {scene.id} has no valid visual assets")
        
        visual = CompositeVideoClip(
            visual_clips,
            size=quality.resolution
        ).set_duration(scene.duration)
        
        # Add narration audio
        if scene.narration_path:
            narration = AudioFileClip(str(scene.narration_path))
            narration = narration.volumex(scene.narration_volume)
            visual = visual.set_audio(narration)
        
        # Add text overlays
        for overlay in scene.text_overlays:
            text_clip = self._create_text_overlay(overlay, quality.resolution)
            visual = CompositeVideoClip([visual, text_clip])
        
        return visual
    
    async def _load_video_asset(
        self,
        asset,
        scene_duration: float,
        quality: QualitySettings
    ) -> "VideoFileClip":
        """Load and process video asset."""
        loop = asyncio.get_event_loop()
        
        clip = await loop.run_in_executor(
            None,
            VideoFileClip,
            str(asset.path)
        )
        
        # Trim to duration
        if asset.video_start or asset.video_end:
            start = asset.video_start
            end = asset.video_end or clip.duration
            clip = clip.subclip(start, end)
        
        # Ensure clip matches scene duration
        if clip.duration > scene_duration:
            clip = clip.subclip(0, scene_duration)
        elif clip.duration < scene_duration:
            # Loop video to fill duration
            n_loops = int(scene_duration / clip.duration) + 1
            clip = concatenate_videoclips([clip] * n_loops)
            clip = clip.subclip(0, scene_duration)
        
        # Resize to target resolution
        clip = clip.resize(quality.resolution)
        
        # Apply transformations
        if asset.opacity != 1.0:
            clip = clip.set_opacity(asset.opacity)
        
        return clip
    
    async def _load_image_asset(
        self,
        asset,
        scene_duration: float,
        quality: QualitySettings
    ) -> "ImageClip":
        """Load and process image asset."""
        loop = asyncio.get_event_loop()
        
        clip = await loop.run_in_executor(
            None,
            ImageClip,
            str(asset.path)
        )
        
        clip = clip.set_duration(scene_duration)
        clip = clip.resize(quality.resolution)
        
        if asset.opacity != 1.0:
            clip = clip.set_opacity(asset.opacity)
        
        return clip
    
    def _add_transition_out(self, clip, transition) -> "VideoFileClip":
        """Add transition effect to clip."""
        if transition.type == TransitionType.FADE:
            clip = fadeout(clip, transition.duration)
        elif transition.type == TransitionType.DISSOLVE:
            clip = fadeout(clip, transition.duration)
        # Add more transition types as needed
        
        return clip
    
    async def _add_background_music(
        self,
        video_clip,
        music
    ):
        """Add background music to video."""
        loop = asyncio.get_event_loop()
        
        # Load music
        music_clip = await loop.run_in_executor(
            None,
            AudioFileClip,
            str(music.path)
        )
        
        # Trim or loop to video duration
        video_duration = video_clip.duration
        
        if music.loop and music_clip.duration < video_duration:
            # Loop music
            n_loops = int(video_duration / music_clip.duration) + 1
            music_clip = concatenate_audioclips([music_clip] * n_loops)
        
        music_clip = music_clip.subclip(0, min(music_clip.duration, video_duration))
        
        # Apply volume and fades
        music_clip = music_clip.volumex(music.volume)
        
        if music.fade_in > 0:
            music_clip = audio_fadein(music_clip, music.fade_in)
        
        if music.fade_out > 0:
            music_clip = audio_fadeout(music_clip, music.fade_out)
        
        # Mix with existing audio
        if video_clip.audio:
            final_audio = CompositeAudioClip([video_clip.audio, music_clip])
        else:
            final_audio = music_clip
        
        return video_clip.set_audio(final_audio)
    
    def _create_text_overlay(self, overlay, resolution: tuple[int, int]):
        """Create text overlay clip."""
        # Position mapping
        positions = {
            "top": ("center", 50),
            "center": ("center", "center"),
            "bottom": ("center", resolution[1] - 100),
            "top_left": (50, 50),
            "top_right": (resolution[0] - 250, 50),
            "bottom_left": (50, resolution[1] - 100),
            "bottom_right": (resolution[0] - 250, resolution[1] - 100),
        }
        
        pos = positions.get(overlay.position.value, ("center", "bottom"))
        
        # Create text clip
        text_clip = TextClip(
            overlay.text,
            fontsize=overlay.font_size,
            font=overlay.font_family,
            color=overlay.font_color,
            bg_color=overlay.background_color,
            method='caption',
            size=(resolution[0] - 100, None)
        )
        
        # Set position and duration
        text_clip = text_clip.set_position(pos)
        
        duration = overlay.duration if overlay.duration else None
        if duration:
            text_clip = text_clip.set_duration(duration)
        
        # Add fade effects
        if overlay.fade_in > 0:
            text_clip = fadein(text_clip, overlay.fade_in)
        
        if overlay.fade_out > 0:
            text_clip = fadeout(text_clip, overlay.fade_out)
        
        return text_clip
    
    def _add_watermark(self, video_clip, text: str):
        """Add watermark to video."""
        resolution = video_clip.size
        
        watermark = TextClip(
            text,
            fontsize=24,
            color='white',
            font='Arial',
        ).set_opacity(0.5)
        
        # Position watermark
        if self.config.watermark_position == "bottom_right":
            pos = (resolution[0] - watermark.w - 20, resolution[1] - watermark.h - 20)
        elif self.config.watermark_position == "bottom_left":
            pos = (20, resolution[1] - watermark.h - 20)
        elif self.config.watermark_position == "top_right":
            pos = (resolution[0] - watermark.w - 20, 20)
        else:  # top_left
            pos = (20, 20)
        
        watermark = watermark.set_position(pos).set_duration(video_clip.duration)
        
        return CompositeVideoClip([video_clip, watermark])
    
    async def _write_video_file(
        self,
        clip,
        output_path: Path,
        quality: QualitySettings
    ) -> None:
        """Write video clip to file."""
        loop = asyncio.get_event_loop()
        
        await loop.run_in_executor(
            None,
            clip.write_videofile,
            str(output_path),
            quality.fps,
            quality.codec,
            quality.bitrate,
            quality.audio_codec,
            quality.audio_bitrate,
            quality.preset,
            self.config.threads,
            self.config.logger,
        )
    
    async def create_thumbnail(
        self,
        video_path: Path,
        output_path: Path,
        timestamp: float = 1.0,
        resolution: tuple[int, int] = (1280, 720)
    ) -> Path:
        """
        Create video thumbnail from specific timestamp.
        
        Args:
            video_path: Source video path
            output_path: Output thumbnail path
            timestamp: Time in video to capture (seconds)
            resolution: Thumbnail resolution
        
        Returns:
            Path to created thumbnail
        """
        loop = asyncio.get_event_loop()
        
        # Load video
        clip = await loop.run_in_executor(
            None,
            VideoFileClip,
            str(video_path)
        )
        
        # Get frame at timestamp
        frame = clip.get_frame(timestamp)
        
        # Save as image
        from PIL import Image
        img = Image.fromarray(frame)
        img = img.resize(resolution, Image.LANCZOS)
        
        await loop.run_in_executor(
            None,
            img.save,
            str(output_path)
        )
        
        clip.close()
        
        return output_path
    
    def estimate_render_time(
        self,
        timeline: Timeline,
        quality: QualityPreset
    ) -> float:
        """
        Estimate render time based on timeline and quality.
        
        Args:
            timeline: Timeline to render
            quality: Quality preset
        
        Returns:
            Estimated time in seconds
        """
        # Rough estimates based on benchmarks
        # These vary widely based on hardware
        multipliers = {
            QualityPreset.DRAFT: 0.5,
            QualityPreset.HD_720P: 1.0,
            QualityPreset.HD_1080P: 2.0,
            QualityPreset.HD_1080P_60: 3.0,
            QualityPreset.UHD_4K: 8.0,
            QualityPreset.INSTAGRAM_SQUARE: 1.5,
            QualityPreset.INSTAGRAM_STORY: 1.5,
            QualityPreset.TIKTOK: 1.5,
        }
        
        multiplier = multipliers.get(quality, 2.0)
        
        # Base estimate: video_duration * multiplier
        estimate = timeline.total_duration * multiplier
        
        # Adjust for scene count (more scenes = more processing)
        estimate *= (1 + (timeline.scene_count * 0.05))
        
        return estimate
