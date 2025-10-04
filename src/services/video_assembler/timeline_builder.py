"""
Timeline Builder for Video Composition

This module manages the video timeline, combining scripts, assets, and transitions
into a cohesive composition ready for rendering.

Features:
- Scene management with assets and narration
- Automatic asset synchronization with script timing
- Transition effects between scenes
- Background music management
- Text overlay support
- Duration calculations and optimization
- Asset validation and fallback handling

Usage:
    builder = TimelineBuilder()
    timeline = await builder.build(
        script=generated_script,
        assets=downloaded_assets,
        config=TimelineConfig(target_duration=300)
    )
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import uuid

from pydantic import BaseModel, Field
import numpy as np


class TransitionType(str, Enum):
    """Types of transitions between scenes."""
    CUT = "cut"  # Instant cut
    FADE = "fade"  # Cross-fade
    DISSOLVE = "dissolve"  # Dissolve transition
    WIPE = "wipe"  # Wipe left/right
    SLIDE = "slide"  # Slide in/out
    ZOOM = "zoom"  # Zoom in/out


class AssetType(str, Enum):
    """Types of visual assets."""
    VIDEO = "video"
    IMAGE = "image"
    TEXT = "text"
    SHAPE = "shape"


class TextPosition(str, Enum):
    """Text overlay positions."""
    TOP = "top"
    CENTER = "center"
    BOTTOM = "bottom"
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"


@dataclass
class Transition:
    """Transition between scenes."""
    type: TransitionType = TransitionType.FADE
    duration: float = 0.5  # seconds
    
    # Transition parameters
    easing: str = "ease_in_out"  # ease_in, ease_out, ease_in_out, linear
    
    def __post_init__(self):
        """Validate transition parameters."""
        if self.duration < 0:
            raise ValueError("Transition duration must be non-negative")
        if self.duration > 3.0:
            raise ValueError("Transition duration should not exceed 3 seconds")


@dataclass
class TextOverlay:
    """Text overlay on a scene."""
    text: str
    position: TextPosition = TextPosition.BOTTOM
    start_time: float = 0.0  # Relative to scene start
    duration: Optional[float] = None  # None = full scene duration
    
    # Styling
    font_size: int = 48
    font_family: str = "Arial"
    font_color: str = "#FFFFFF"
    background_color: Optional[str] = "rgba(0, 0, 0, 0.7)"  # Semi-transparent
    padding: int = 20
    
    # Animation
    fade_in: float = 0.5
    fade_out: float = 0.5


@dataclass
class Asset:
    """Visual asset for a scene."""
    path: Path
    type: AssetType
    
    # Timing
    start_time: float = 0.0  # When to start in scene
    duration: Optional[float] = None  # None = calculate from file
    
    # Video specific
    video_start: float = 0.0  # Start offset in source video
    video_end: Optional[float] = None  # End offset in source video
    
    # Transformations
    scale: float = 1.0  # Scale factor
    position: Tuple[int, int] = (0, 0)  # (x, y) position
    rotation: float = 0.0  # Degrees
    opacity: float = 1.0  # 0.0-1.0
    
    # Effects
    blur: float = 0.0  # Blur amount
    brightness: float = 1.0  # Brightness multiplier
    contrast: float = 1.0  # Contrast multiplier
    
    def __post_init__(self):
        """Validate asset parameters."""
        if not self.path.exists():
            raise FileNotFoundError(f"Asset not found: {self.path}")
        
        if self.opacity < 0 or self.opacity > 1:
            raise ValueError("Opacity must be between 0 and 1")


@dataclass
class Scene:
    """A scene in the timeline."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Content
    assets: List[Asset] = field(default_factory=list)
    narration_path: Optional[Path] = None
    text_overlays: List[TextOverlay] = field(default_factory=list)
    
    # Timing
    start_time: float = 0.0  # Start time in timeline
    duration: float = 5.0  # Scene duration
    
    # Transition
    transition_in: Optional[Transition] = None
    transition_out: Optional[Transition] = field(
        default_factory=lambda: Transition(type=TransitionType.FADE)
    )
    
    # Audio
    narration_volume: float = 1.0
    
    # Metadata
    script_segment: Optional[str] = None  # Associated script text
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate scene parameters."""
        if self.duration <= 0:
            raise ValueError("Scene duration must be positive")
        
        if not self.assets and not self.narration_path:
            raise ValueError("Scene must have at least one asset or narration")


@dataclass
class BackgroundMusic:
    """Background music for timeline."""
    path: Path
    start_time: float = 0.0
    duration: Optional[float] = None  # None = use full track
    volume: float = 0.3  # Lower than narration
    fade_in: float = 2.0
    fade_out: float = 3.0
    loop: bool = True  # Loop if shorter than video


@dataclass
class TimelineConfig:
    """Configuration for timeline building."""
    
    # Duration
    target_duration: Optional[float] = None  # Target video duration (seconds)
    min_scene_duration: float = 3.0  # Minimum scene length
    max_scene_duration: float = 10.0  # Maximum scene length
    
    # Transitions
    default_transition: TransitionType = TransitionType.FADE
    transition_duration: float = 0.5
    
    # Assets
    prefer_videos: bool = True  # Prefer video assets over images
    image_duration: float = 5.0  # Duration for static images
    video_clip_max: float = 10.0  # Max duration for video clips
    
    # Text overlays
    add_captions: bool = False  # Add text captions from script
    caption_position: TextPosition = TextPosition.BOTTOM
    
    # Music
    background_music: Optional[BackgroundMusic] = None
    music_volume: float = 0.3
    
    # Quality
    resolution: Tuple[int, int] = (1920, 1080)  # (width, height)
    fps: int = 30


class Timeline(BaseModel):
    """Complete video timeline."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scenes: List[Scene]
    background_music: Optional[BackgroundMusic] = None
    
    # Metadata
    total_duration: float
    scene_count: int
    resolution: Tuple[int, int]
    fps: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Statistics
    total_assets: int = 0
    video_assets: int = 0
    image_assets: int = 0
    has_narration: bool = False
    
    class Config:
        arbitrary_types_allowed = True
    
    @classmethod
    def from_scenes(
        cls,
        scenes: List[Scene],
        config: TimelineConfig,
        background_music: Optional[BackgroundMusic] = None
    ):
        """Create timeline from scenes."""
        total_duration = sum(s.duration for s in scenes)
        
        # Count assets
        total_assets = sum(len(s.assets) for s in scenes)
        video_assets = sum(
            1 for s in scenes for a in s.assets
            if a.type == AssetType.VIDEO
        )
        image_assets = sum(
            1 for s in scenes for a in s.assets
            if a.type == AssetType.IMAGE
        )
        has_narration = any(s.narration_path for s in scenes)
        
        return cls(
            scenes=scenes,
            background_music=background_music,
            total_duration=total_duration,
            scene_count=len(scenes),
            resolution=config.resolution,
            fps=config.fps,
            total_assets=total_assets,
            video_assets=video_assets,
            image_assets=image_assets,
            has_narration=has_narration,
        )


class TimelineBuilder:
    """
    Build video timelines from scripts and assets.
    
    Manages scene creation, asset assignment, transition timing,
    and synchronization of narration with visual content.
    """
    
    def __init__(self, config: Optional[TimelineConfig] = None):
        """
        Initialize timeline builder.
        
        Args:
            config: Timeline configuration
        """
        self.config = config or TimelineConfig()
    
    async def build(
        self,
        script_segments: List[str],
        narration_paths: List[Path],
        assets: List[Path],
        background_music: Optional[Path] = None,
    ) -> Timeline:
        """
        Build complete timeline from components.
        
        Args:
            script_segments: List of script text segments
            narration_paths: List of narration audio files (one per segment)
            assets: List of visual asset paths
            background_music: Optional background music path
        
        Returns:
            Complete Timeline object
        """
        if len(script_segments) != len(narration_paths):
            raise ValueError("Script segments and narration paths must match")
        
        # Get narration durations
        narration_durations = await self._get_audio_durations(narration_paths)
        
        # Create scenes
        scenes = await self._create_scenes(
            script_segments,
            narration_paths,
            narration_durations,
            assets
        )
        
        # Add background music if provided
        bg_music = None
        if background_music:
            bg_music = BackgroundMusic(
                path=background_music,
                volume=self.config.music_volume,
                duration=sum(s.duration for s in scenes)
            )
        
        # Create timeline
        timeline = Timeline.from_scenes(
            scenes=scenes,
            config=self.config,
            background_music=bg_music
        )
        
        return timeline
    
    async def _create_scenes(
        self,
        script_segments: List[str],
        narration_paths: List[Path],
        narration_durations: List[float],
        assets: List[Path],
    ) -> List[Scene]:
        """
        Create scenes from script segments and assets.
        
        Args:
            script_segments: Script text for each scene
            narration_paths: Audio files for narration
            narration_durations: Duration of each narration
            assets: Available visual assets
        
        Returns:
            List of Scene objects
        """
        scenes = []
        current_time = 0.0
        
        # Assign assets to scenes (cycle through available assets)
        asset_index = 0
        
        for i, (segment, narration_path, duration) in enumerate(
            zip(script_segments, narration_paths, narration_durations)
        ):
            # Get asset for this scene
            asset_path = assets[asset_index % len(assets)]
            asset_index += 1
            
            # Detect asset type
            asset_type = self._detect_asset_type(asset_path)
            
            # Create asset
            asset = Asset(
                path=asset_path,
                type=asset_type,
                duration=duration if asset_type == AssetType.IMAGE else None
            )
            
            # Create scene
            scene = Scene(
                assets=[asset],
                narration_path=narration_path,
                start_time=current_time,
                duration=duration,
                script_segment=segment,
                transition_out=Transition(
                    type=self.config.default_transition,
                    duration=self.config.transition_duration
                )
            )
            
            # Add captions if enabled
            if self.config.add_captions:
                scene.text_overlays.append(
                    TextOverlay(
                        text=segment[:100] + "..." if len(segment) > 100 else segment,
                        position=self.config.caption_position,
                        duration=duration
                    )
                )
            
            scenes.append(scene)
            current_time += duration
        
        return scenes
    
    def _detect_asset_type(self, path: Path) -> AssetType:
        """
        Detect asset type from file extension.
        
        Args:
            path: Asset file path
        
        Returns:
            AssetType enum value
        """
        ext = path.suffix.lower()
        
        video_exts = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
        image_exts = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
        
        if ext in video_exts:
            return AssetType.VIDEO
        elif ext in image_exts:
            return AssetType.IMAGE
        else:
            raise ValueError(f"Unsupported asset type: {ext}")
    
    async def _get_audio_durations(self, paths: List[Path]) -> List[float]:
        """
        Get durations of audio files.
        
        Args:
            paths: List of audio file paths
        
        Returns:
            List of durations in seconds
        """
        from pydub import AudioSegment
        
        durations = []
        loop = asyncio.get_event_loop()
        
        for path in paths:
            duration = await loop.run_in_executor(
                None,
                self._get_audio_duration_sync,
                path
            )
            durations.append(duration)
        
        return durations
    
    def _get_audio_duration_sync(self, path: Path) -> float:
        """Get audio duration synchronously."""
        from pydub import AudioSegment
        
        audio = AudioSegment.from_file(str(path))
        return len(audio) / 1000.0  # Convert ms to seconds
    
    async def optimize_timeline(self, timeline: Timeline) -> Timeline:
        """
        Optimize timeline for better pacing and flow.
        
        Args:
            timeline: Timeline to optimize
        
        Returns:
            Optimized timeline
        """
        scenes = timeline.scenes
        
        # Adjust scene durations to fit target
        if self.config.target_duration:
            scenes = await self._adjust_to_target_duration(
                scenes,
                self.config.target_duration
            )
        
        # Balance scene lengths
        scenes = await self._balance_scene_lengths(scenes)
        
        # Optimize transitions
        scenes = await self._optimize_transitions(scenes)
        
        # Rebuild timeline
        return Timeline.from_scenes(
            scenes=scenes,
            config=self.config,
            background_music=timeline.background_music
        )
    
    async def _adjust_to_target_duration(
        self,
        scenes: List[Scene],
        target: float
    ) -> List[Scene]:
        """Adjust scene durations to match target."""
        current_total = sum(s.duration for s in scenes)
        
        if current_total == target:
            return scenes
        
        # Calculate scale factor
        scale = target / current_total
        
        # Adjust each scene proportionally
        for scene in scenes:
            new_duration = scene.duration * scale
            
            # Clamp to min/max
            new_duration = max(
                self.config.min_scene_duration,
                min(self.config.max_scene_duration, new_duration)
            )
            
            scene.duration = new_duration
        
        return scenes
    
    async def _balance_scene_lengths(self, scenes: List[Scene]) -> List[Scene]:
        """Balance scene lengths for better pacing."""
        # Calculate average
        avg_duration = np.mean([s.duration for s in scenes])
        
        # Adjust outliers
        for scene in scenes:
            if scene.duration < avg_duration * 0.5:
                scene.duration = avg_duration * 0.7
            elif scene.duration > avg_duration * 2.0:
                scene.duration = avg_duration * 1.5
        
        return scenes
    
    async def _optimize_transitions(self, scenes: List[Scene]) -> List[Scene]:
        """Optimize transition timing and types."""
        for i, scene in enumerate(scenes):
            # No transition on last scene
            if i == len(scenes) - 1:
                scene.transition_out = None
                continue
            
            # Adjust transition based on scene content
            # (You can add more sophisticated logic here)
            if scene.duration < 4.0:
                # Quick scenes get quick transitions
                scene.transition_out.duration = 0.3
            else:
                # Longer scenes can have smoother transitions
                scene.transition_out.duration = 0.7
        
        return scenes
    
    def validate_timeline(self, timeline: Timeline) -> List[str]:
        """
        Validate timeline for issues.
        
        Args:
            timeline: Timeline to validate
        
        Returns:
            List of validation warnings/errors
        """
        issues = []
        
        # Check total duration
        if timeline.total_duration < 10:
            issues.append("Video is very short (< 10 seconds)")
        
        if timeline.total_duration > 900:
            issues.append("Video is very long (> 15 minutes)")
        
        # Check scene count
        if timeline.scene_count < 3:
            issues.append("Very few scenes (< 3)")
        
        # Check asset availability
        for scene in timeline.scenes:
            for asset in scene.assets:
                if not asset.path.exists():
                    issues.append(f"Missing asset: {asset.path}")
            
            if scene.narration_path and not scene.narration_path.exists():
                issues.append(f"Missing narration: {scene.narration_path}")
        
        return issues
    
    async def export_timeline_json(
        self,
        timeline: Timeline,
        output_path: Path
    ) -> None:
        """
        Export timeline to JSON for inspection or editing.
        
        Args:
            timeline: Timeline to export
            output_path: Path to save JSON file
        """
        import json
        
        data = timeline.dict()
        
        # Convert Path objects to strings
        data_str = json.dumps(data, indent=2, default=str)
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            output_path.write_text,
            data_str
        )
