"""
Timeline and Scene classes for video assembly

Represents the structure of a video timeline with scenes,
transitions, and timing information.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import timedelta


class Scene(BaseModel):
    """
    Represents a single scene in the video timeline.
    
    A scene is a continuous segment with a single visual asset,
    optional audio, and optional text overlays.
    """
    
    start_time: float = Field(..., description="Start time in seconds", ge=0)
    duration: float = Field(..., description="Duration in seconds", gt=0)
    asset_path: str = Field(..., description="Path to video/image asset")
    audio_path: Optional[str] = Field(None, description="Optional audio track")
    text_overlay: Optional[str] = Field(None, description="Optional text to display")
    transition: str = Field("fade", description="Transition effect (fade, cut, slide, etc.)")
    
    # Visual effects
    zoom_level: float = Field(1.0, description="Zoom level (1.0 = no zoom)", ge=0.1, le=5.0)
    pan_x: float = Field(0.0, description="Horizontal pan offset")
    pan_y: float = Field(0.0, description="Vertical pan offset")
    opacity: float = Field(1.0, description="Opacity level", ge=0.0, le=1.0)
    
    # Audio settings
    volume: float = Field(1.0, description="Audio volume", ge=0.0, le=2.0)
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @property
    def end_time(self) -> float:
        """Calculate end time based on start + duration"""
        return self.start_time + self.duration
    
    def overlaps(self, other: 'Scene') -> bool:
        """Check if this scene overlaps with another scene"""
        return (self.start_time < other.end_time and 
                self.end_time > other.start_time)
    
    def __repr__(self):
        return f"<Scene {self.start_time:.1f}s-{self.end_time:.1f}s: {self.asset_path}>"
    
    class Config:
        """Pydantic configuration"""
        validate_assignment = True


class Timeline(BaseModel):
    """
    Represents the complete video timeline.
    
    Contains all scenes, background audio, and global settings
    for video rendering.
    """
    
    scenes: List[Scene] = Field(default_factory=list, description="List of scenes in order")
    total_duration: float = Field(0.0, description="Total timeline duration in seconds", ge=0)
    background_audio: Optional[str] = Field(None, description="Background music path")
    background_volume: float = Field(0.3, description="Background music volume", ge=0.0, le=1.0)
    
    # Video settings
    resolution: tuple = Field((1920, 1080), description="Video resolution (width, height)")
    fps: int = Field(30, description="Frames per second", ge=1, le=120)
    aspect_ratio: str = Field("16:9", description="Aspect ratio (16:9, 9:16, 1:1)")
    
    # Color grading
    brightness: float = Field(1.0, description="Global brightness", ge=0.0, le=2.0)
    contrast: float = Field(1.0, description="Global contrast", ge=0.0, le=2.0)
    saturation: float = Field(1.0, description="Global saturation", ge=0.0, le=2.0)
    
    # Metadata
    title: Optional[str] = Field(None, description="Video title")
    description: Optional[str] = Field(None, description="Video description")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    def add_scene(self, scene: Scene, auto_position: bool = True) -> None:
        """
        Add a scene to the timeline.
        
        Args:
            scene: Scene to add
            auto_position: If True, automatically set start_time after last scene
        """
        if auto_position and self.scenes:
            # Set start time to end of last scene
            scene.start_time = self.scenes[-1].end_time
        
        self.scenes.append(scene)
        self._update_duration()
    
    def insert_scene(self, scene: Scene, index: int) -> None:
        """
        Insert a scene at a specific index.
        
        Args:
            scene: Scene to insert
            index: Position to insert at
        """
        self.scenes.insert(index, scene)
        self._recalculate_timings()
        self._update_duration()
    
    def remove_scene(self, index: int) -> Scene:
        """
        Remove a scene by index.
        
        Args:
            index: Index of scene to remove
            
        Returns:
            Removed scene
        """
        scene = self.scenes.pop(index)
        self._recalculate_timings()
        self._update_duration()
        return scene
    
    def get_scene_at_time(self, time: float) -> Optional[Scene]:
        """
        Get the scene at a specific time.
        
        Args:
            time: Time in seconds
            
        Returns:
            Scene at that time, or None if no scene found
        """
        for scene in self.scenes:
            if scene.start_time <= time < scene.end_time:
                return scene
        return None
    
    def get_scenes_by_asset(self, asset_path: str) -> List[Scene]:
        """
        Get all scenes using a specific asset.
        
        Args:
            asset_path: Path to asset
            
        Returns:
            List of scenes using that asset
        """
        return [scene for scene in self.scenes if scene.asset_path == asset_path]
    
    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate timeline integrity.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        if not self.scenes:
            issues.append("Timeline has no scenes")
            return False, issues
        
        # Check for gaps or overlaps
        for i in range(len(self.scenes) - 1):
            current_end = self.scenes[i].end_time
            next_start = self.scenes[i + 1].start_time
            
            gap = next_start - current_end
            
            if gap > 0.1:  # Gap larger than 100ms
                issues.append(
                    f"Gap detected between scene {i} and {i+1}: {gap:.2f}s"
                )
            elif gap < -0.01:  # Overlap (with 10ms tolerance)
                issues.append(
                    f"Overlap detected between scene {i} and {i+1}: {abs(gap):.2f}s"
                )
        
        # Check for zero-duration scenes
        for i, scene in enumerate(self.scenes):
            if scene.duration <= 0:
                issues.append(f"Scene {i} has zero or negative duration")
        
        # Check resolution
        width, height = self.resolution
        if width <= 0 or height <= 0:
            issues.append(f"Invalid resolution: {width}x{height}")
        
        # Check FPS
        if self.fps < 1 or self.fps > 120:
            issues.append(f"Invalid FPS: {self.fps}")
        
        return len(issues) == 0, issues
    
    def _update_duration(self) -> None:
        """Update total duration based on scenes"""
        if self.scenes:
            self.total_duration = max(scene.end_time for scene in self.scenes)
        else:
            self.total_duration = 0.0
    
    def _recalculate_timings(self) -> None:
        """Recalculate all scene start times to be continuous"""
        current_time = 0.0
        for scene in self.scenes:
            scene.start_time = current_time
            current_time += scene.duration
    
    def get_summary(self) -> str:
        """
        Get a human-readable summary of the timeline.
        
        Returns:
            Summary string
        """
        duration_str = str(timedelta(seconds=int(self.total_duration)))
        return (
            f"Timeline: {len(self.scenes)} scenes, "
            f"{duration_str} duration, "
            f"{self.resolution[0]}x{self.resolution[1]} @ {self.fps}fps"
        )
    
    @classmethod
    def from_scenes(
        cls,
        scenes: List,  # Accept any scene type
        config: Optional[Dict[str, Any]] = None,
        background_audio: Optional[str] = None
    ) -> 'Timeline':
        """
        Create a Timeline from a list of scenes.
        
        Args:
            scenes: List of Scene objects (Pydantic or dataclass)
            config: Optional configuration dict with resolution, fps, etc.
            background_audio: Optional background music path
            
        Returns:
            Timeline object
        """
        # Convert BuilderScenes (dataclass) to Pydantic Scenes if needed
        pydantic_scenes = []
        for scene in scenes:
            if isinstance(scene, Scene):
                # Already a Pydantic Scene
                pydantic_scenes.append(scene)
            else:
                # Convert from BuilderScene (dataclass) to Pydantic Scene
                # Extract basic info from BuilderScene
                asset_path = scene.assets[0].path if scene.assets else "/tmp/default.mp4"
                pydantic_scenes.append(Scene(
                    start_time=0.0,  # Will be recalculated
                    duration=scene.duration,
                    asset_path=str(asset_path) if hasattr(asset_path, '__fspath__') else asset_path,
                ))
        
        timeline = cls(
            scenes=pydantic_scenes,
            background_audio=background_audio
        )
        
        # Apply config if provided
        if config:
            if hasattr(config, 'resolution'):
                timeline.resolution = config.resolution
            elif isinstance(config, dict) and 'resolution' in config:
                timeline.resolution = config['resolution']
                
            if hasattr(config, 'fps'):
                timeline.fps = config.fps
            elif isinstance(config, dict) and 'fps' in config:
                timeline.fps = config['fps']
        
        timeline._recalculate_timings()
        timeline._update_duration()
        return timeline
    
    @property
    def scene_count(self) -> int:
        """Get number of scenes in timeline"""
        return len(self.scenes)
    
    @property
    def video_assets(self) -> int:
        """Count video assets across all scenes"""
        # This is a simplified version - real implementation would check asset types
        return len([s for s in self.scenes if s.asset_path])
    
    def __repr__(self):
        return f"<Timeline {len(self.scenes)} scenes, {self.total_duration:.1f}s>"
    
    class Config:
        """Pydantic configuration"""
        validate_assignment = True
        arbitrary_types_allowed = True
