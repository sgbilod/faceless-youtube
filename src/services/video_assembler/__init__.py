"""
Video Assembler Service

This package provides complete video assembly capabilities, combining:
- Script generation (AI-powered content)
- Asset management (videos, images, music)
- Text-to-Speech (TTS) for narration
- Timeline composition and transitions
- Video rendering and export

Main Components:
- TTSEngine: Convert scripts to speech with multiple voices
- TimelineBuilder: Compose scenes with assets and transitions
- VideoRenderer: Render final videos with quality presets
- VideoAssembler: Orchestrate the entire assembly process

Usage:
    from src.services.video_assembler import VideoAssembler, VideoConfig
    
    assembler = VideoAssembler()
    video = await assembler.assemble(
        script=generated_script,
        assets=downloaded_assets,
        config=VideoConfig(resolution="1080p", fps=30)
    )
"""

from .tts_engine import TTSEngine, TTSConfig, Voice, TTSResult
from .timeline_builder import (
    TimelineBuilder, 
    Scene as BuilderScene,  # Dataclass version
    Transition, 
    TransitionType,
    TimelineConfig,
    Timeline as BuilderTimeline,  # Dataclass version
    Asset,  # Dataclass Asset
    AssetType,  # Enum for asset types
    BackgroundMusic,
)
from .timeline import Scene, Timeline  # Pydantic versions
from .video_renderer import VideoRenderer, RenderConfig, QualityPreset
from .video_assembler import VideoAssembler, VideoConfig, AssembledVideo

# Import additional items that tests might need
try:
    from .video_renderer import QualitySettings
except ImportError:
    QualitySettings = None

try:
    from .video_assembler import VideoStatus
except ImportError:
    from src.core.models import VideoStatus

__all__ = [
    # TTS
    "TTSEngine",
    "TTSConfig",
    "Voice",
    "TTSResult",
    # Timeline (Pydantic models for tests/API)
    "Scene",
    "Timeline",
    # Timeline Builder (dataclass versions for internal use)
    "TimelineBuilder",
    "BuilderScene",
    "BuilderTimeline",
    "Transition",
    "TransitionType",
    "TimelineConfig",
    "Asset",
    "AssetType",
    "BackgroundMusic",
    # Renderer
    "VideoRenderer",
    "RenderConfig",
    "QualityPreset",
    "QualitySettings",
    # Main Assembler
    "VideoAssembler",
    "VideoConfig",
    "AssembledVideo",
    "VideoStatus",
]

__version__ = "1.0.0"
