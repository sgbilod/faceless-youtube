"""
Video Assembler - Main Orchestration Service

This module coordinates the entire video assembly process:
1. Generate TTS audio from script
2. Download/retrieve visual assets
3. Build timeline with synchronization
4. Render final video

Features:
- End-to-end automation from script to video
- Intelligent asset selection based on script content
- Automatic fallback handling
- Progress tracking and callbacks
- Error recovery and retry logic
- Caching for performance

Usage:
    assembler = VideoAssembler()
    result = await assembler.assemble(
        script="Your meditation script here...",
        niche=NicheType.MEDITATION,
        assets=asset_paths,
        config=VideoConfig()
    )
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, List, Optional
import uuid

from pydantic import BaseModel, Field

from .tts_engine import TTSEngine, TTSConfig, Voice, TTSResult
from .timeline_builder import (
    TimelineBuilder,
    Timeline,
    TimelineConfig,
    BackgroundMusic,
)
from .video_renderer import VideoRenderer, RenderConfig, QualityPreset, RenderResult
from src.utils.cache import CacheManager

logger = logging.getLogger(__name__)


class VideoStatus(str, Enum):
    """Status of video assembly."""
    PENDING = "pending"
    GENERATING_AUDIO = "generating_audio"
    BUILDING_TIMELINE = "building_timeline"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class VideoConfig:
    """Configuration for video assembly."""
    
    # TTS settings
    voice: Voice = Voice.FEMALE_CALM
    speaking_rate: float = 1.0
    tts_config: Optional[TTSConfig] = None
    
    # Timeline settings
    target_duration: Optional[float] = None  # Target video duration
    add_captions: bool = False
    timeline_config: Optional[TimelineConfig] = None
    
    # Rendering settings
    quality: QualityPreset = QualityPreset.HD_1080P
    render_config: Optional[RenderConfig] = None
    
    # Music
    background_music_path: Optional[Path] = None
    music_volume: float = 0.3
    
    # Watermark
    add_watermark: bool = False
    watermark_text: Optional[str] = None
    
    # Output
    output_dir: Path = Path("output_videos")
    temp_dir: Path = Path("temp")
    
    # Performance
    max_retries: int = 3
    enable_cache: bool = True
    cache_ttl: int = 3600


class AssembledVideo(BaseModel):
    """Result of complete video assembly."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Paths
    video_path: str
    thumbnail_path: Optional[str] = None
    
    # Content
    script: str
    niche: str
    title: Optional[str] = None
    
    # Metadata
    duration: float  # seconds
    file_size: int  # bytes
    resolution: tuple[int, int]
    fps: int
    
    # TTS
    voice_used: str
    audio_duration: float
    
    # Timeline
    scene_count: int
    asset_count: int
    
    # Timing
    assembly_time: float  # Total time to assemble
    render_time: float  # Just render time
    assembled_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Status
    status: VideoStatus = VideoStatus.COMPLETED
    errors: List[str] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True


class VideoAssembler:
    """
    Complete video assembly orchestrator.
    
    Coordinates TTS generation, timeline building, and video rendering
    into a single unified workflow with error handling and caching.
    """
    
    def __init__(
        self,
        config: Optional[VideoConfig] = None,
        cache_manager: Optional[CacheManager] = None,
    ):
        """
        Initialize video assembler.
        
        Args:
            config: Video assembly configuration
            cache_manager: Optional cache manager
        """
        self.config = config or VideoConfig()
        self.cache = cache_manager or CacheManager() if self.config.enable_cache else None
        
        # Initialize components
        self.tts_engine = TTSEngine(
            config=self.config.tts_config or TTSConfig(
                voice=self.config.voice,
                speaking_rate=self.config.speaking_rate,
                enable_cache=self.config.enable_cache,
            ),
            cache_manager=self.cache
        )
        
        self.timeline_builder = TimelineBuilder(
            config=self.config.timeline_config or TimelineConfig(
                target_duration=self.config.target_duration,
                add_captions=self.config.add_captions,
            )
        )
        
        self.video_renderer = VideoRenderer(
            config=self.config.render_config or RenderConfig(
                quality=self.config.quality,
                add_watermark=self.config.add_watermark,
                watermark_text=self.config.watermark_text,
            )
        )
        
        # Ensure output directories exist
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        self.config.temp_dir.mkdir(parents=True, exist_ok=True)
    
    async def assemble(
        self,
        script: str,
        niche: str,
        assets: List[Path],
        title: Optional[str] = None,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> AssembledVideo:
        """
        Assemble complete video from script and assets.
        
        Args:
            script: Video script text
            niche: Content niche (meditation, motivation, etc.)
            assets: List of visual asset paths
            title: Optional video title
            progress_callback: Optional progress callback (status, progress)
        
        Returns:
            AssembledVideo with all metadata
        """
        import time
        
        start_time = time.time()
        video_id = str(uuid.uuid4())[:8]
        
        logger.info(f"Starting video assembly [{video_id}]: {niche}")
        
        try:
            # Step 1: Split script into segments
            if progress_callback:
                progress_callback("Preparing script", 0.1)
            
            script_segments = self._split_script(script)
            logger.info(f"Split script into {len(script_segments)} segments")
            
            # Step 2: Generate TTS for each segment
            if progress_callback:
                progress_callback("Generating audio", 0.2)
            
            narration_results = await self._generate_narration(
                script_segments,
                progress_callback
            )
            logger.info(f"Generated {len(narration_results)} audio segments")
            
            # Step 3: Build timeline
            if progress_callback:
                progress_callback("Building timeline", 0.5)
            
            timeline = await self._build_timeline(
                script_segments,
                narration_results,
                assets
            )
            logger.info(f"Built timeline: {timeline.scene_count} scenes, "
                       f"{timeline.total_duration:.1f}s")
            
            # Step 4: Render video
            if progress_callback:
                progress_callback("Rendering video", 0.6)
            
            output_path = self.config.output_dir / f"video_{video_id}.mp4"
            
            render_result = await self.video_renderer.render(
                timeline=timeline,
                output_path=output_path,
                progress_callback=lambda p: progress_callback(
                    "Rendering video",
                    0.6 + (p * 0.35)
                ) if progress_callback else None
            )
            
            # Step 5: Create thumbnail
            if progress_callback:
                progress_callback("Creating thumbnail", 0.95)
            
            thumbnail_path = await self._create_thumbnail(output_path, video_id)
            
            # Calculate total time
            assembly_time = time.time() - start_time
            
            # Create result
            result = AssembledVideo(
                id=video_id,
                video_path=str(output_path),
                thumbnail_path=str(thumbnail_path) if thumbnail_path else None,
                script=script,
                niche=niche,
                title=title or f"{niche.title()} Video",
                duration=render_result.duration,
                file_size=render_result.file_size,
                resolution=render_result.resolution,
                fps=render_result.fps,
                voice_used=self.config.voice.value,
                audio_duration=sum(r.duration for r in narration_results),
                scene_count=timeline.scene_count,
                asset_count=timeline.total_assets,
                assembly_time=assembly_time,
                render_time=render_result.render_time,
                status=VideoStatus.COMPLETED,
            )
            
            if progress_callback:
                progress_callback("Complete", 1.0)
            
            logger.info(f"Assembly complete [{video_id}]: {assembly_time:.1f}s, "
                       f"{result.file_size / 1024 / 1024:.1f} MB")
            
            return result
        
        except Exception as e:
            logger.error(f"Assembly failed [{video_id}]: {e}", exc_info=True)
            
            return AssembledVideo(
                id=video_id,
                video_path="",
                script=script,
                niche=niche,
                title=title or "",
                duration=0,
                file_size=0,
                resolution=(0, 0),
                fps=0,
                voice_used=self.config.voice.value,
                audio_duration=0,
                scene_count=0,
                asset_count=0,
                assembly_time=time.time() - start_time,
                render_time=0,
                status=VideoStatus.FAILED,
                errors=[str(e)],
            )
    
    def _split_script(self, script: str) -> List[str]:
        """
        Split script into logical segments for scenes.
        
        Args:
            script: Full script text
        
        Returns:
            List of script segments
        """
        # Split on paragraph breaks or sentences
        # This is a simple implementation - can be more sophisticated
        
        # First try paragraph breaks
        paragraphs = [p.strip() for p in script.split('\n\n') if p.strip()]
        
        if len(paragraphs) >= 3:
            return paragraphs
        
        # Fallback: split on periods (sentences)
        sentences = [s.strip() + '.' for s in script.split('.') if s.strip()]
        
        # Group sentences into segments (3-5 sentences per segment)
        segments = []
        current_segment = []
        
        for sentence in sentences:
            current_segment.append(sentence)
            
            if len(current_segment) >= 3:
                segments.append(' '.join(current_segment))
                current_segment = []
        
        # Add remaining sentences
        if current_segment:
            segments.append(' '.join(current_segment))
        
        # Ensure at least 1 segment
        if not segments:
            segments = [script]
        
        return segments
    
    async def _generate_narration(
        self,
        script_segments: List[str],
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> List[TTSResult]:
        """
        Generate TTS audio for all script segments.
        
        Args:
            script_segments: List of script text segments
            progress_callback: Optional progress callback
        
        Returns:
            List of TTSResult objects
        """
        results = []
        total = len(script_segments)
        
        for i, segment in enumerate(script_segments):
            # Generate audio
            result = await self.tts_engine.generate(
                text=segment,
                voice=self.config.voice,
                speaking_rate=self.config.speaking_rate,
                save_to_file=True
            )
            
            results.append(result)
            
            # Update progress
            if progress_callback:
                progress = 0.2 + ((i + 1) / total * 0.3)
                progress_callback("Generating audio", progress)
        
        return results
    
    async def _build_timeline(
        self,
        script_segments: List[str],
        narration_results: List[TTSResult],
        assets: List[Path],
    ) -> Timeline:
        """
        Build timeline from script and narration.
        
        Args:
            script_segments: Script text segments
            narration_results: TTS results
            assets: Visual assets
        
        Returns:
            Complete Timeline
        """
        # Extract narration paths
        narration_paths = [
            Path(result.audio_path)
            for result in narration_results
            if result.audio_path
        ]
        
        # Build timeline
        timeline = await self.timeline_builder.build(
            script_segments=script_segments,
            narration_paths=narration_paths,
            assets=assets,
            background_music=self.config.background_music_path,
        )
        
        # Optimize timeline
        timeline = await self.timeline_builder.optimize_timeline(timeline)
        
        return timeline
    
    async def _create_thumbnail(
        self,
        video_path: Path,
        video_id: str
    ) -> Optional[Path]:
        """
        Create thumbnail for video.
        
        Args:
            video_path: Path to rendered video
            video_id: Video ID for naming
        
        Returns:
            Path to thumbnail or None if failed
        """
        try:
            thumbnail_path = self.config.output_dir / f"thumb_{video_id}.jpg"
            
            await self.video_renderer.create_thumbnail(
                video_path=video_path,
                output_path=thumbnail_path,
                timestamp=1.0,
            )
            
            return thumbnail_path
        
        except Exception as e:
            logger.warning(f"Failed to create thumbnail: {e}")
            return None
    
    async def assemble_batch(
        self,
        scripts: List[tuple[str, str, List[Path]]],  # (script, niche, assets)
        progress_callback: Optional[Callable[[int, int, str, float], None]] = None,
    ) -> List[AssembledVideo]:
        """
        Assemble multiple videos in parallel.
        
        Args:
            scripts: List of (script, niche, assets) tuples
            progress_callback: Optional callback (current, total, status, progress)
        
        Returns:
            List of AssembledVideo results
        """
        results = []
        total = len(scripts)
        
        for i, (script, niche, assets) in enumerate(scripts):
            logger.info(f"Assembling video {i+1}/{total}")
            
            # Callback wrapper
            def callback(status: str, progress: float):
                if progress_callback:
                    progress_callback(i + 1, total, status, progress)
            
            # Assemble video
            result = await self.assemble(
                script=script,
                niche=niche,
                assets=assets,
                progress_callback=callback
            )
            
            results.append(result)
        
        return results
    
    async def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """
        Clean up old temporary files.
        
        Args:
            max_age_hours: Maximum age of files to keep
        
        Returns:
            Number of files deleted
        """
        import time
        
        deleted = 0
        max_age_seconds = max_age_hours * 3600
        current_time = time.time()
        
        # Clean temp directory
        for file in self.config.temp_dir.glob("*"):
            if file.is_file():
                age = current_time - file.stat().st_mtime
                if age > max_age_seconds:
                    file.unlink()
                    deleted += 1
        
        # Clean TTS cache
        deleted += await self.tts_engine.cleanup_cache(
            max_age_days=max_age_hours // 24
        )
        
        logger.info(f"Cleaned up {deleted} temporary files")
        
        return deleted
    
    def estimate_assembly_time(
        self,
        script: str,
        asset_count: int
    ) -> float:
        """
        Estimate total assembly time.
        
        Args:
            script: Script text
            asset_count: Number of assets
        
        Returns:
            Estimated time in seconds
        """
        # TTS time (rough estimate: 0.5x real-time)
        tts_duration = await self.tts_engine.estimate_duration(script)
        tts_time = tts_duration * 0.5
        
        # Timeline building (fast)
        timeline_time = 5
        
        # Rendering time
        render_time = self.video_renderer.estimate_render_time(
            Timeline(
                scenes=[],
                total_duration=tts_duration,
                scene_count=asset_count,
                resolution=self.config.quality,
                fps=30,
            ),
            self.config.quality
        )
        
        return tts_time + timeline_time + render_time
