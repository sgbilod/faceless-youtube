"""
Video Assembler Usage Examples

This file demonstrates how to use the complete video assembly service
to create faceless YouTube videos from scripts and assets.

Prerequisites:
1. Install dependencies: pip install -r requirements.txt
2. Install Coqui TTS: pip install TTS
3. Install FFmpeg: https://ffmpeg.org/download.html
4. Download TTS models (happens automatically on first use)

Features demonstrated:
- Basic video assembly
- Custom voice and quality settings
- Batch processing
- Progress tracking
- Error handling
- Thumbnail creation
"""

import asyncio
from pathlib import Path
from src.services.video_assembler import (
    VideoAssembler,
    VideoConfig,
    Voice,
    QualityPreset,
    VideoStatus,
)


# ============================
# Example 1: Simple Video Assembly
# ============================
async def example_1_basic_assembly():
    """Assemble a basic video from script and assets."""
    print("\n=== Example 1: Basic Video Assembly ===\n")
    
    # Initialize assembler
    assembler = VideoAssembler()
    
    # Prepare script
    script = """
    Welcome to this peaceful morning meditation.
    
    Find a comfortable seated position and gently close your eyes.
    
    Take a deep breath in through your nose, filling your lungs completely.
    
    Hold for a moment, then slowly release through your mouth.
    
    With each breath, feel yourself becoming more relaxed and centered.
    """
    
    # Prepare assets (videos or images)
    assets = [
        Path("assets/nature_scene1.mp4"),
        Path("assets/sunrise.jpg"),
        Path("assets/calm_water.mp4"),
    ]
    
    # Assemble video
    result = await assembler.assemble(
        script=script,
        niche="meditation",
        assets=assets,
        title="5-Minute Morning Meditation",
    )
    
    if result.status == VideoStatus.COMPLETED:
        print(f"✓ Video created: {result.video_path}")
        print(f"  Duration: {result.duration:.1f}s")
        print(f"  File size: {result.file_size / 1024 / 1024:.1f} MB")
        print(f"  Scenes: {result.scene_count}")
    else:
        print(f"✗ Assembly failed: {result.errors}")


# ============================
# Example 2: Custom Voice and Quality
# ============================
async def example_2_custom_settings():
    """Use custom voice, quality, and watermark."""
    print("\n=== Example 2: Custom Settings ===\n")
    
    # Custom configuration
    config = VideoConfig(
        # Voice settings
        voice=Voice.MALE_DEEP,  # Use male voice
        speaking_rate=0.9,  # Slightly slower
        
        # Video quality
        quality=QualityPreset.UHD_4K,  # 4K resolution
        
        # Watermark
        add_watermark=True,
        watermark_text="@YourChannel",
        
        # Output
        output_dir=Path("output/premium"),
    )
    
    assembler = VideoAssembler(config=config)
    
    script = """
    In today's video, we explore five fascinating facts about space.
    
    Number one: A day on Venus is longer than its year.
    
    Number two: There are more stars than grains of sand on Earth.
    
    Number three: Neutron stars can spin 600 times per second.
    
    Number four: One spoonful of neutron star weighs 6 billion tons.
    
    Number five: The universe is expanding faster than the speed of light.
    """
    
    assets = [
        Path("assets/space_1.mp4"),
        Path("assets/space_2.mp4"),
        Path("assets/space_3.mp4"),
    ]
    
    result = await assembler.assemble(
        script=script,
        niche="facts",
        assets=assets,
        title="5 Mind-Blowing Space Facts",
    )
    
    print(f"Video: {result.video_path}")
    print(f"Quality: {result.resolution[0]}x{result.resolution[1]} @ {result.fps}fps")
    print(f"Voice: {result.voice_used}")


# ============================
# Example 3: Progress Tracking
# ============================
async def example_3_progress_tracking():
    """Track video assembly progress."""
    print("\n=== Example 3: Progress Tracking ===\n")
    
    assembler = VideoAssembler()
    
    # Progress callback
    def progress_callback(status: str, progress: float):
        bar_length = 40
        filled = int(bar_length * progress)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"\r{status:<25} [{bar}] {progress*100:.0f}%", end="", flush=True)
    
    script = """
    Let's explore the power of daily habits.
    
    Small actions, repeated consistently, create massive results over time.
    
    Start with just one habit. Make it so easy you can't say no.
    
    Track your progress. Celebrate small wins.
    
    Remember: You don't rise to the level of your goals.
    You fall to the level of your systems.
    """
    
    assets = [Path(f"assets/motivation_{i}.mp4") for i in range(1, 6)]
    
    result = await assembler.assemble(
        script=script,
        niche="motivation",
        assets=assets,
        title="The Power of Daily Habits",
        progress_callback=progress_callback,
    )
    
    print(f"\n✓ Complete! {result.video_path}")


# ============================
# Example 4: Batch Processing
# ============================
async def example_4_batch_processing():
    """Generate multiple videos in one go."""
    print("\n=== Example 4: Batch Processing ===\n")
    
    assembler = VideoAssembler(
        config=VideoConfig(
            quality=QualityPreset.HD_1080P,
            enable_cache=True,  # Speed up repeated content
        )
    )
    
    # Prepare multiple videos
    videos = [
        (
            "Morning meditation for peace and clarity.",
            "meditation",
            [Path("assets/nature1.mp4"), Path("assets/nature2.mp4")],
        ),
        (
            "Evening meditation for deep relaxation.",
            "meditation",
            [Path("assets/sunset1.mp4"), Path("assets/sunset2.mp4")],
        ),
        (
            "Quick breathing exercise for stress relief.",
            "meditation",
            [Path("assets/calm1.mp4"), Path("assets/calm2.mp4")],
        ),
    ]
    
    # Batch progress callback
    def batch_progress(current: int, total: int, status: str, progress: float):
        print(f"Video {current}/{total} - {status}: {progress*100:.0f}%")
    
    results = await assembler.assemble_batch(
        scripts=videos,
        progress_callback=batch_progress,
    )
    
    # Summary
    print(f"\n=== Batch Complete ===")
    successful = sum(1 for r in results if r.status == VideoStatus.COMPLETED)
    print(f"Successful: {successful}/{len(results)}")
    
    for i, result in enumerate(results, 1):
        status_icon = "✓" if result.status == VideoStatus.COMPLETED else "✗"
        print(f"{status_icon} Video {i}: {result.video_path}")


# ============================
# Example 5: With Background Music
# ============================
async def example_5_background_music():
    """Add background music to video."""
    print("\n=== Example 5: Background Music ===\n")
    
    config = VideoConfig(
        background_music_path=Path("assets/meditation_music.mp3"),
        music_volume=0.25,  # Quiet background music
    )
    
    assembler = VideoAssembler(config=config)
    
    script = """
    Welcome to this 10-minute guided sleep meditation.
    
    Lie down in a comfortable position.
    
    Let your body sink into the bed.
    
    Release all tension from your muscles.
    
    Breathe slowly and deeply.
    
    Feel yourself drifting into peaceful sleep.
    """
    
    assets = [
        Path("assets/stars1.mp4"),
        Path("assets/moon.jpg"),
        Path("assets/night_sky.mp4"),
    ]
    
    result = await assembler.assemble(
        script=script,
        niche="meditation",
        assets=assets,
        title="10-Minute Sleep Meditation",
    )
    
    print(f"Video with music: {result.video_path}")
    print(f"Has background music: {result.has_background_music}")


# ============================
# Example 6: Error Handling
# ============================
async def example_6_error_handling():
    """Handle assembly errors gracefully."""
    print("\n=== Example 6: Error Handling ===\n")
    
    assembler = VideoAssembler()
    
    try:
        # Attempt with potentially missing assets
        result = await assembler.assemble(
            script="Test script",
            niche="test",
            assets=[Path("nonexistent.mp4")],
        )
        
        if result.status == VideoStatus.FAILED:
            print(f"Assembly failed (expected):")
            for error in result.errors:
                print(f"  - {error}")
            
            # Could implement retry logic here
            print("\n Retrying with fallback assets...")
            
    except Exception as e:
        print(f"Error: {e}")
        print("Implement your error recovery logic here")


# ============================
# Example 7: Custom Timeline
# ============================
async def example_7_custom_timeline():
    """Use custom timeline settings."""
    print("\n=== Example 7: Custom Timeline ===\n")
    
    from src.services.video_assembler import TimelineConfig, TransitionType
    
    # Custom timeline configuration
    timeline_config = TimelineConfig(
        target_duration=180.0,  # Exactly 3 minutes
        min_scene_duration=5.0,
        max_scene_duration=15.0,
        default_transition=TransitionType.DISSOLVE,
        transition_duration=0.8,  # Slower transitions
        add_captions=True,  # Add text overlays
    )
    
    config = VideoConfig(
        timeline_config=timeline_config,
        quality=QualityPreset.HD_1080P,
    )
    
    assembler = VideoAssembler(config=config)
    
    script = """
    Philosophy teaches us to question everything.
    
    What is the good life? How should we live?
    
    The Stoics believed in focusing on what we can control.
    
    Accept what you cannot change, and change what you can.
    
    Find peace in the present moment.
    """
    
    assets = [
        Path("assets/philosophy1.mp4"),
        Path("assets/philosophy2.jpg"),
        Path("assets/philosophy3.mp4"),
    ]
    
    result = await assembler.assemble(
        script=script,
        niche="philosophy",
        assets=assets,
        title="Stoic Philosophy Explained",
    )
    
    print(f"Video duration: {result.duration:.1f}s (target: 180s)")
    print(f"Scenes: {result.scene_count}")


# ============================
# Example 8: Estimate Before Assembly
# ============================
async def example_8_time_estimation():
    """Estimate assembly time before starting."""
    print("\n=== Example 8: Time Estimation ===\n")
    
    assembler = VideoAssembler(
        config=VideoConfig(quality=QualityPreset.HD_1080P)
    )
    
    script = "This is a test script with approximately fifty words. " * 10
    
    # Estimate time
    estimated_time = await assembler.estimate_assembly_time(
        script=script,
        asset_count=5
    )
    
    print(f"Estimated assembly time: {estimated_time:.1f} seconds")
    print(f"That's about {estimated_time/60:.1f} minutes")
    
    # Decide whether to proceed
    if estimated_time < 300:  # Less than 5 minutes
        print("✓ Quick assembly - proceeding...")
    else:
        print("⚠ Long assembly - consider batch processing overnight")


# ============================
# Example 9: Cleanup Old Files
# ============================
async def example_9_cleanup():
    """Clean up old temporary files."""
    print("\n=== Example 9: Cleanup ===\n")
    
    assembler = VideoAssembler()
    
    # Clean up files older than 24 hours
    deleted = await assembler.cleanup_temp_files(max_age_hours=24)
    
    print(f"Cleaned up {deleted} old files")
    
    # Also clean up TTS cache
    tts_deleted = await assembler.tts_engine.cleanup_cache(max_age_days=7)
    
    print(f"Cleaned up {tts_deleted} old TTS files")


# ============================
# Example 10: Complete Workflow
# ============================
async def example_10_complete_workflow():
    """Complete workflow from script generation to video."""
    print("\n=== Example 10: Complete Workflow ===\n")
    
    # This would integrate with script generator (Task #6)
    from src.services.script_generator import ScriptGenerator, ScriptConfig, NicheType
    
    # 1. Generate script with AI
    print("Step 1: Generating script with AI...")
    script_gen = ScriptGenerator()
    generated_script = await script_gen.generate(
        topic="Morning Gratitude Practice",
        config=ScriptConfig(
            duration_minutes=5,
            niche=NicheType.MEDITATION,
        )
    )
    
    print(f"✓ Script generated: {generated_script.word_count} words")
    
    # 2. Download assets (would use asset scraper from Task #5)
    print("\nStep 2: Using pre-downloaded assets...")
    assets = [
        Path("assets/gratitude1.mp4"),
        Path("assets/gratitude2.jpg"),
    ]
    
    # 3. Assemble video
    print("\nStep 3: Assembling video...")
    assembler = VideoAssembler(
        config=VideoConfig(
            voice=Voice.FEMALE_CALM,
            quality=QualityPreset.HD_1080P,
            add_watermark=True,
            watermark_text="@YourChannel",
        )
    )
    
    result = await assembler.assemble(
        script=generated_script.script,
        niche="meditation",
        assets=assets,
        title=generated_script.title,
        progress_callback=lambda s, p: print(f"  {s}: {p*100:.0f}%"),
    )
    
    # 4. Summary
    print(f"\n=== Complete ===")
    print(f"Video: {result.video_path}")
    print(f"Thumbnail: {result.thumbnail_path}")
    print(f"Duration: {result.duration:.1f}s")
    print(f"Assembly time: {result.assembly_time:.1f}s")
    print(f"Quality: {result.resolution[0]}x{result.resolution[1]}")
    
    # 5. Next steps (would be Task #8: YouTube upload)
    print(f"\nNext: Upload to YouTube!")


# ============================
# Main Runner
# ============================
async def main():
    """Run all examples."""
    examples = [
        ("Basic Assembly", example_1_basic_assembly),
        ("Custom Settings", example_2_custom_settings),
        ("Progress Tracking", example_3_progress_tracking),
        ("Batch Processing", example_4_batch_processing),
        ("Background Music", example_5_background_music),
        ("Error Handling", example_6_error_handling),
        ("Custom Timeline", example_7_custom_timeline),
        ("Time Estimation", example_8_time_estimation),
        ("Cleanup", example_9_cleanup),
        ("Complete Workflow", example_10_complete_workflow),
    ]
    
    print("=" * 60)
    print("VIDEO ASSEMBLER USAGE EXAMPLES")
    print("=" * 60)
    
    for name, example_func in examples:
        try:
            await example_func()
        except Exception as e:
            print(f"\n⚠ {name} failed: {e}")
        
        print("\n" + "-" * 60)
    
    print("\n✓ All examples completed!")


if __name__ == "__main__":
    # Run examples
    asyncio.run(main())
