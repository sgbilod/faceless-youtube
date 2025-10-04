# Video Assembler Documentation

**Complete Video Production Pipeline for Faceless YouTube Content**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Architecture](#architecture)
4. [Components](#components)
5. [Configuration](#configuration)
6. [Usage Guide](#usage-guide)
7. [API Reference](#api-reference)
8. [Quality Presets](#quality-presets)
9. [Voice Options](#voice-options)
10. [Troubleshooting](#troubleshooting)
11. [Performance Optimization](#performance-optimization)
12. [Production Deployment](#production-deployment)

---

## Overview

The Video Assembler is a complete end-to-end video production system that transforms text scripts into professional YouTube videos. It combines AI-generated narration, visual assets, transitions, and background music into polished videos ready for upload.

### ✨ Key Features

- **Text-to-Speech**: High-quality AI narration with multiple voices (Coqui TTS)
- **Timeline Building**: Automatic scene composition with transitions
- **Video Rendering**: Professional video output with MoviePy
- **Quality Presets**: From draft (360p) to 4K UHD
- **Batch Processing**: Generate multiple videos in parallel
- **Progress Tracking**: Real-time assembly progress callbacks
- **Caching**: Smart caching for audio and rendered segments
- **Error Recovery**: Automatic retry and fallback handling

### 🎯 Use Cases

- Meditation and mindfulness videos
- Motivational content
- Educational explainers
- "Top 10" fact videos
- Story narration
- Philosophy discussions
- Any faceless content format

---

## Quick Start

### 1. Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install FFmpeg (required for video/audio processing)
# Windows: choco install ffmpeg
# Mac: brew install ffmpeg
# Linux: sudo apt install ffmpeg

# Install ImageMagick (optional, for advanced text effects)
# Windows: Download from https://imagemagick.org/
# Mac: brew install imagemagick
# Linux: sudo apt install imagemagick
```

### 2. Download TTS Models

TTS models download automatically on first use, but you can pre-download:

```python
from TTS.api import TTS

# Download models
TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")
TTS(model_name="tts_models/en/vctk/vits")
```

### 3. Basic Usage

```python
from src.services.video_assembler import VideoAssembler
from pathlib import Path

# Initialize
assembler = VideoAssembler()

# Prepare inputs
script = "Your video script here..."
assets = [Path("video1.mp4"), Path("image1.jpg")]

# Assemble
result = await assembler.assemble(
    script=script,
    niche="meditation",
    assets=assets,
    title="My First Video"
)

print(f"Video created: {result.video_path}")
```

---

## Architecture

The Video Assembler consists of four main components working together:

```
┌─────────────────────────────────────────────────────────────┐
│                     VIDEO ASSEMBLER                         │
│                    (Orchestration Layer)                    │
└─────────────┬───────────────┬──────────────┬────────────────┘
              │               │              │
         ┌────▼────┐    ┌────▼─────┐   ┌───▼──────┐
         │   TTS   │    │ Timeline │   │ Renderer │
         │ Engine  │    │ Builder  │   │          │
         └─────────┘    └──────────┘   └──────────┘
              │               │              │
         ┌────▼────┐    ┌────▼─────┐   ┌───▼──────┐
         │ Coqui   │    │  Scene   │   │ MoviePy  │
         │  TTS    │    │ Composer │   │  + FFmpeg│
         └─────────┘    └──────────┘   └──────────┘
```

### Component Responsibilities

1. **TTS Engine**: Converts text to speech audio
2. **Timeline Builder**: Creates scene composition
3. **Video Renderer**: Renders final video file
4. **Video Assembler**: Coordinates all components

---

## Components

### 1. TTS Engine (`tts_engine.py`)

Generates natural-sounding narration from text.

**Features**:

- 7 pre-configured voices (male/female, various tones)
- SSML support for pauses, emphasis, rate control
- Audio format conversion (WAV, MP3, OGG)
- Speaking rate adjustment (0.5x - 2.0x)
- Automatic caching for performance
- Batch generation for multiple segments

**Voice Options**:

- `FEMALE_CALM`: Meditation, relaxation content
- `FEMALE_ENERGETIC`: Motivation, energetic content
- `MALE_DEEP`: Facts, authoritative narration
- `MALE_FRIENDLY`: Stories, casual tone
- `FAST_FEMALE/MALE`: Lower quality but faster

**Example**:

```python
from src.services.video_assembler import TTSEngine, Voice

tts = TTSEngine()
result = await tts.generate(
    text="Welcome to this meditation",
    voice=Voice.FEMALE_CALM,
    speaking_rate=0.9
)
```

---

### 2. Timeline Builder (`timeline_builder.py`)

Constructs video timeline from scripts and assets.

**Features**:

- Scene creation with assets and narration
- Automatic asset-to-narration synchronization
- Transition effects (fade, dissolve, wipe, zoom)
- Text overlay support with positioning
- Background music integration
- Duration optimization
- Timeline validation

**Scene Structure**:

```python
Scene:
  - Assets (videos/images)
  - Narration audio
  - Text overlays
  - Duration
  - Transitions (in/out)
```

**Example**:

```python
from src.services.video_assembler import TimelineBuilder

builder = TimelineBuilder()
timeline = await builder.build(
    script_segments=["Segment 1", "Segment 2"],
    narration_paths=[Path("audio1.wav"), Path("audio2.wav")],
    assets=[Path("video1.mp4"), Path("video2.mp4")]
)
```

---

### 3. Video Renderer (`video_renderer.py`)

Renders timeline to final video file.

**Features**:

- Multiple quality presets (720p to 4K)
- Progress tracking with callbacks
- GPU acceleration support
- Multi-threaded encoding
- Watermark support
- Thumbnail generation
- Platform-optimized exports (YouTube, Instagram, TikTok)

**Quality Presets**:

- `DRAFT`: 640x360, 30fps (fast preview)
- `HD_720P`: 1280x720, 30fps, 5 Mbps
- `HD_1080P`: 1920x1080, 30fps, 8 Mbps
- `HD_1080P_60`: 1920x1080, 60fps, 12 Mbps
- `UHD_4K`: 3840x2160, 30fps, 35 Mbps

**Example**:

```python
from src.services.video_assembler import VideoRenderer, QualityPreset

renderer = VideoRenderer()
result = await renderer.render(
    timeline=timeline,
    output_path=Path("output.mp4"),
    quality=QualityPreset.HD_1080P
)
```

---

### 4. Video Assembler (`video_assembler.py`)

Main orchestration service.

**Features**:

- End-to-end automation
- Script segmentation
- Component coordination
- Progress tracking
- Error recovery with retries
- Batch processing
- Cache management
- Time estimation

**Example**:

```python
from src.services.video_assembler import VideoAssembler

assembler = VideoAssembler()
result = await assembler.assemble(
    script="Your script...",
    niche="meditation",
    assets=[Path("video1.mp4")]
)
```

---

## Configuration

### VideoConfig

Complete configuration for video assembly:

```python
from src.services.video_assembler import VideoConfig, Voice, QualityPreset

config = VideoConfig(
    # TTS Settings
    voice=Voice.FEMALE_CALM,
    speaking_rate=1.0,

    # Timeline Settings
    target_duration=300.0,  # 5 minutes
    add_captions=False,

    # Rendering Settings
    quality=QualityPreset.HD_1080P,

    # Music
    background_music_path=Path("music.mp3"),
    music_volume=0.3,

    # Watermark
    add_watermark=True,
    watermark_text="@YourChannel",

    # Output
    output_dir=Path("output_videos"),

    # Performance
    max_retries=3,
    enable_cache=True,
)
```

### TTSConfig

Text-to-speech configuration:

```python
from src.services.video_assembler import TTSConfig

tts_config = TTSConfig(
    voice=Voice.FEMALE_CALM,
    language="en",
    speaking_rate=1.0,
    pitch_shift=0.0,
    volume=1.0,
    sample_rate=22050,  # or 44100 for higher quality
    enable_cache=True,
    use_gpu=False,
)
```

### TimelineConfig

Timeline building configuration:

```python
from src.services.video_assembler import TimelineConfig, TransitionType

timeline_config = TimelineConfig(
    target_duration=300.0,
    min_scene_duration=3.0,
    max_scene_duration=10.0,
    default_transition=TransitionType.FADE,
    transition_duration=0.5,
    add_captions=True,
    resolution=(1920, 1080),
    fps=30,
)
```

### RenderConfig

Video rendering configuration:

```python
from src.services.video_assembler import RenderConfig, QualityPreset

render_config = RenderConfig(
    quality=QualityPreset.HD_1080P,
    threads=4,
    use_gpu=False,
    add_watermark=True,
    watermark_text="@YourChannel",
)
```

---

## Usage Guide

### Basic Video Assembly

```python
assembler = VideoAssembler()

result = await assembler.assemble(
    script="Your meditation script here...",
    niche="meditation",
    assets=[Path("nature.mp4"), Path("sunset.jpg")],
    title="Morning Meditation"
)

if result.status == VideoStatus.COMPLETED:
    print(f"Success: {result.video_path}")
else:
    print(f"Failed: {result.errors}")
```

### With Progress Tracking

```python
def progress_callback(status: str, progress: float):
    print(f"{status}: {progress*100:.0f}%")

result = await assembler.assemble(
    script=script,
    niche=niche,
    assets=assets,
    progress_callback=progress_callback
)
```

### Batch Processing

```python
videos = [
    ("Script 1", "meditation", [Path("v1.mp4")]),
    ("Script 2", "motivation", [Path("v2.mp4")]),
    ("Script 3", "facts", [Path("v3.mp4")]),
]

results = await assembler.assemble_batch(videos)

for result in results:
    print(f"{result.title}: {result.status}")
```

### Custom Quality Settings

```python
config = VideoConfig(
    quality=QualityPreset.UHD_4K,
    voice=Voice.MALE_DEEP,
    add_watermark=True,
)

assembler = VideoAssembler(config=config)
```

### With Background Music

```python
config = VideoConfig(
    background_music_path=Path("background.mp3"),
    music_volume=0.25,
)

assembler = VideoAssembler(config=config)
```

---

## API Reference

### VideoAssembler

Main orchestration class.

#### Methods

**`async assemble(...) -> AssembledVideo`**

Assemble complete video from script and assets.

Parameters:

- `script` (str): Video script text
- `niche` (str): Content niche
- `assets` (List[Path]): Visual asset paths
- `title` (Optional[str]): Video title
- `progress_callback` (Optional[Callable]): Progress updates

Returns: `AssembledVideo` with metadata

**`async assemble_batch(...) -> List[AssembledVideo]`**

Assemble multiple videos in parallel.

**`async cleanup_temp_files(max_age_hours: int) -> int`**

Clean up old temporary files.

**`estimate_assembly_time(script: str, asset_count: int) -> float`**

Estimate total assembly time in seconds.

---

### TTSEngine

Text-to-speech generation.

#### Methods

**`async generate(text: str, ...) -> TTSResult`**

Generate speech audio from text.

**`async generate_batch(texts: List[str], ...) -> List[TTSResult]`**

Generate audio for multiple text segments.

**`async estimate_duration(text: str, speaking_rate: float) -> float`**

Estimate audio duration without generating.

---

### TimelineBuilder

Timeline composition.

#### Methods

**`async build(...) -> Timeline`**

Build complete timeline from components.

**`async optimize_timeline(timeline: Timeline) -> Timeline`**

Optimize timeline for better pacing.

**`validate_timeline(timeline: Timeline) -> List[str]`**

Validate timeline for issues.

---

### VideoRenderer

Video rendering.

#### Methods

**`async render(timeline: Timeline, ...) -> RenderResult`**

Render timeline to video file.

**`async create_thumbnail(...) -> Path`**

Create video thumbnail from timestamp.

**`estimate_render_time(timeline: Timeline, quality: QualityPreset) -> float`**

Estimate render time based on timeline and quality.

---

## Quality Presets

### YouTube Recommendations

| Preset        | Resolution | FPS | Bitrate | Use Case                         |
| ------------- | ---------- | --- | ------- | -------------------------------- |
| `HD_720P`     | 1280x720   | 30  | 5 Mbps  | Standard quality, fast upload    |
| `HD_1080P`    | 1920x1080  | 30  | 8 Mbps  | **Recommended** for most content |
| `HD_1080P_60` | 1920x1080  | 60  | 12 Mbps | Smooth motion, gaming            |
| `UHD_4K`      | 3840x2160  | 30  | 35 Mbps | Premium quality, large files     |

### Social Media Presets

| Preset             | Resolution | Format | Platform                   |
| ------------------ | ---------- | ------ | -------------------------- |
| `INSTAGRAM_SQUARE` | 1080x1080  | 1:1    | Instagram Feed             |
| `INSTAGRAM_STORY`  | 1080x1920  | 9:16   | Instagram/Facebook Stories |
| `TIKTOK`           | 1080x1920  | 9:16   | TikTok, YouTube Shorts     |

### Draft Preset

| Preset  | Resolution | Use Case               |
| ------- | ---------- | ---------------------- |
| `DRAFT` | 640x360    | Quick preview, testing |

---

## Voice Options

### Available Voices

**Female Voices**:

- `FEMALE_CALM`: Soft, soothing, ideal for meditation
- `FEMALE_ENERGETIC`: Upbeat, motivational content

**Male Voices**:

- `MALE_DEEP`: Authoritative, facts, education
- `MALE_FRIENDLY`: Casual, storytelling

**Fast Voices** (lower quality, faster generation):

- `FAST_FEMALE`
- `FAST_MALE`

### Voice Selection Guide

| Content Type | Recommended Voice | Speaking Rate |
| ------------ | ----------------- | ------------- |
| Meditation   | FEMALE_CALM       | 0.8 - 0.9     |
| Motivation   | FEMALE_ENERGETIC  | 1.0 - 1.1     |
| Facts        | MALE_DEEP         | 0.95 - 1.05   |
| Stories      | MALE_FRIENDLY     | 1.0           |
| Education    | MALE_DEEP         | 0.9 - 1.0     |

---

## Troubleshooting

### FFmpeg Not Found

**Error**: `FFmpeg not found`

**Solution**:

```bash
# Install FFmpeg
# Windows: choco install ffmpeg
# Mac: brew install ffmpeg
# Linux: sudo apt install ffmpeg

# Verify installation
ffmpeg -version
```

---

### TTS Model Download Fails

**Error**: `Failed to download TTS model`

**Solution**:

```python
# Manual download
from TTS.api import TTS
TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")
```

---

### Out of Memory During Rendering

**Error**: `MemoryError` or system slowdown

**Solutions**:

1. Use lower quality preset (DRAFT or HD_720P)
2. Reduce number of scenes
3. Close other applications
4. Increase system swap/page file
5. Process in batches with cleanup between

```python
# Lower quality
config = VideoConfig(quality=QualityPreset.HD_720P)

# Cleanup between batches
await assembler.cleanup_temp_files(max_age_hours=1)
```

---

### Slow Rendering

**Problem**: Video takes very long to render

**Solutions**:

1. Use `DRAFT` preset for testing
2. Enable GPU acceleration (if available)
3. Reduce video duration
4. Use fewer transitions
5. Use multi-threading

```python
render_config = RenderConfig(
    quality=QualityPreset.DRAFT,
    threads=8,  # More threads
    use_gpu=True,
)
```

---

### Audio/Video Out of Sync

**Problem**: Narration doesn't match video

**Solution**:

- Ensure all audio files are valid
- Check narration file durations
- Validate timeline before rendering

```python
issues = builder.validate_timeline(timeline)
if issues:
    print(f"Timeline issues: {issues}")
```

---

## Performance Optimization

### 1. Enable Caching

```python
config = VideoConfig(
    enable_cache=True,
    cache_ttl=3600,  # 1 hour
)
```

**Impact**: 50-100x faster for repeated content

---

### 2. Batch Processing

```python
# Process multiple videos at once
results = await assembler.assemble_batch(videos)
```

**Impact**: Better resource utilization

---

### 3. Use Appropriate Quality

```python
# Draft for testing
config = VideoConfig(quality=QualityPreset.DRAFT)

# 1080p for final
config = VideoConfig(quality=QualityPreset.HD_1080P)
```

**Impact**: DRAFT renders 5-10x faster

---

### 4. Optimize Assets

- Use videos instead of high-res images when possible
- Compress large video files before use
- Keep asset resolution close to target resolution
- Limit scene count (3-10 scenes ideal)

---

### 5. Cleanup Regularly

```python
# Clean up old files weekly
await assembler.cleanup_temp_files(max_age_hours=168)
```

---

## Production Deployment

### System Requirements

**Minimum**:

- CPU: 4 cores
- RAM: 8GB
- Storage: 50GB SSD
- OS: Windows 10, macOS 10.15+, Ubuntu 20.04+

**Recommended**:

- CPU: 8+ cores
- RAM: 16GB+
- Storage: 500GB SSD
- GPU: NVIDIA (for acceleration)

---

### Dependencies

```bash
# Core dependencies
pip install moviepy TTS pydub

# System dependencies
# FFmpeg (required)
# ImageMagick (optional)
```

---

### Monitoring

Track key metrics:

- Assembly time (target: < 2x video duration)
- Render time (varies by quality)
- Cache hit rate (target: > 60%)
- Error rate (target: < 5%)

---

### Error Handling

```python
try:
    result = await assembler.assemble(...)
    if result.status == VideoStatus.FAILED:
        logger.error(f"Assembly failed: {result.errors}")
        # Implement retry or alerting
except Exception as e:
    logger.exception("Unexpected error")
    # Implement error recovery
```

---

### Scaling

**Single Server**:

- Process 10-20 videos/day
- Use queue system (Celery)

**Multi-Server**:

- Load balancer
- Shared storage (NFS, S3)
- Distributed queue

---

## Best Practices

### ✅ Do

- Validate assets before assembly
- Use caching for repeated content
- Monitor assembly times
- Clean up old files regularly
- Use appropriate quality for platform
- Test with DRAFT preset first
- Keep scripts concise (3-10 minutes)
- Use consistent asset aspect ratios

### ❌ Don't

- Render 4K for social media shorts
- Mix portrait/landscape assets
- Use very long scripts (>15 minutes)
- Forget to clean up temp files
- Ignore validation warnings
- Skip progress tracking in production
- Use maximum quality for all content

---

## License

Part of the Faceless YouTube project. See LICENSE for details.

---

## Support

For issues and questions:

1. Check troubleshooting section
2. Review examples in `examples/video_assembler_usage.py`
3. Check logs for detailed error messages
4. Verify all dependencies are installed

---

**Next Steps**: Task #8 - YouTube Upload Automation
