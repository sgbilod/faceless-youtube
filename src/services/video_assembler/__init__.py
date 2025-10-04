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
from .timeline_builder import TimelineBuilder, Scene, Transition, TimelineConfig
from .video_renderer import VideoRenderer, RenderConfig, QualityPreset
from .video_assembler import VideoAssembler, VideoConfig, AssembledVideo

__all__ = [
    # TTS
    "TTSEngine",
    "TTSConfig",
    "Voice",
    "TTSResult",
    # Timeline
    "TimelineBuilder",
    "Scene",
    "Transition",
    "TimelineConfig",
    # Renderer
    "VideoRenderer",
    "RenderConfig",
    "QualityPreset",
    # Main Assembler
    "VideoAssembler",
    "VideoConfig",
    "AssembledVideo",
]

__version__ = "1.0.0"
