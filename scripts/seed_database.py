"""
Database Seed Data Script

Populates the database with sample data for development and testing.
Includes users, platforms, niches, videos, and related entities.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from src.core.database import SessionLocal, engine
from src.core.models import (
    Base, User, Platform, Video, Script,
    Asset, VideoAsset, Publish, Configuration, Analytics, Revenue,
    PlatformName
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================
# SAMPLE DATA DEFINITIONS
# ============================================

SAMPLE_USERS = [
    {
        "username": "demo_user",
        "email": "demo@faceless-youtube.com",
        "password_hash": "$2b$12$dummy.hash.for.development.purposes.only",  # Dummy hash for development
        "is_active": True,
    },
    {
        "username": "test_creator",
        "email": "test@faceless-youtube.com",
        "password_hash": "$2b$12$dummy.hash.for.development.purposes.only",  # Dummy hash for development
        "is_active": True,
    },
]

SAMPLE_PLATFORMS = [
    {
        "name": PlatformName.YOUTUBE,
        "enabled": True,
        "is_configured": False,
        "default_config": {
            "visibility": "public",
            "category": "Education",
            "tags": ["meditation", "relaxation", "sleep"],
            "allow_comments": True,
            "allow_ratings": True
        }
    },
    {
        "name": PlatformName.TIKTOK,
        "enabled": False,
        "is_configured": False,
        "default_config": {
            "visibility": "public",
            "allow_comments": True,
            "allow_duet": True,
            "allow_stitch": True
        }
    },
    {
        "name": PlatformName.INSTAGRAM,
        "enabled": False,
        "is_configured": False,
        "default_config": {
            "visibility": "public",
            "allow_comments": True
        }
    },
]

SAMPLE_NICHES = [
    "Sleep Meditation",
    "Focus & Productivity",
    "Anxiety Relief",
    "Morning Motivation",
]

SAMPLE_SCRIPTS = [
    """Welcome to this peaceful sleep meditation. 
    Find a comfortable position and close your eyes. 
    Take a deep breath in... and slowly exhale. 
    Let go of the tension in your body. 
    Feel yourself becoming more relaxed with each breath.""",
    
    """It's time to focus and be productive. 
    Clear your mind of distractions. 
    Breathe deeply and center yourself. 
    You are capable and ready to accomplish your goals.""",
    
    """Take a moment to release your anxiety. 
    Notice your breath flowing naturally. 
    You are safe. You are calm. You are at peace. 
    Let worry fade away with each exhale.""",
]

SAMPLE_ASSETS = [
    {
        "asset_type": "video",
        "source": "Pexels",
        "url": "https://example.com/nature-scene-1.mp4",
        "title": "Peaceful Nature Scene",
        "description": "Calm forest with gentle stream",
        "keywords": ["nature", "forest", "stream", "peaceful", "calm"],
        "duration": 30,
        "resolution": "1920x1080",
        "file_size": 15728640,  # 15MB
        "license_type": "Creative Commons Zero"
    },
    {
        "asset_type": "video",
        "source": "Pexels",
        "url": "https://example.com/ocean-waves.mp4",
        "title": "Ocean Waves",
        "description": "Soothing ocean waves at sunset",
        "keywords": ["ocean", "waves", "sunset", "beach", "relaxing"],
        "duration": 45,
        "resolution": "1920x1080",
        "file_size": 23592960,  # 22.5MB
        "license_type": "Creative Commons Zero"
    },
    {
        "asset_type": "audio",
        "source": "Freesound",
        "url": "https://example.com/ambient-music.mp3",
        "title": "Ambient Meditation Music",
        "description": "Soft ambient background music",
        "keywords": ["ambient", "music", "meditation", "relaxing", "background"],
        "duration": 600,
        "license_type": "Creative Commons Attribution"
    },
]

SAMPLE_CONFIGS = [
    {
        "key": "ai_provider",
        "value": "ollama",
        "category": "ai",
        "description": "Primary AI provider for script generation"
    },
    {
        "key": "tts_provider",
        "value": "coqui",
        "category": "voice",
        "description": "Text-to-speech provider"
    },
    {
        "key": "video_resolution",
        "value": "1080p",
        "category": "video",
        "description": "Default video resolution"
    },
    {
        "key": "max_concurrent_renders",
        "value": "3",
        "category": "performance",
        "description": "Maximum concurrent video rendering jobs"
    },
]


# ============================================
# SEEDING FUNCTIONS
# ============================================

def seed_users(db: Session) -> list[User]:
    """Create sample users."""
    logger.info("Creating sample users...")
    users = []
    
    for user_data in SAMPLE_USERS:
        user = User(**user_data)
        db.add(user)
        users.append(user)
    
    db.commit()
    logger.info(f"✅ Created {len(users)} users")
    return users


def seed_platforms(db: Session) -> list[Platform]:
    """Create sample platforms."""
    logger.info("Creating sample platforms...")
    platforms = []
    
    for platform_data in SAMPLE_PLATFORMS:
        platform = Platform(**platform_data)
        db.add(platform)
        platforms.append(platform)
    
    db.commit()
    logger.info(f"✅ Created {len(platforms)} platforms")
    return platforms


def seed_assets(db: Session) -> list[Asset]:
    """Create sample assets."""
    logger.info("Creating sample assets...")
    assets = []
    
    for asset_data in SAMPLE_ASSETS:
        asset = Asset(**asset_data)
        db.add(asset)
        assets.append(asset)
    
    db.commit()
    logger.info(f"✅ Created {len(assets)} assets")
    return assets


def seed_scripts(db: Session) -> list[Script]:
    """Create sample scripts."""
    logger.info("Creating sample scripts...")
    scripts = []
    
    for i, script_content in enumerate(SAMPLE_SCRIPTS):
        script = Script(
            content=script_content,
            word_count=len(script_content.split()),
            ai_provider="ollama",
            ai_model="mistral",
            generation_time_seconds=random.uniform(5.0, 15.0)
        )
        db.add(script)
        scripts.append(script)
    
    db.commit()
    logger.info(f"✅ Created {len(scripts)} scripts")
    return scripts


def seed_videos(db: Session, users: list[User], scripts: list[Script]) -> list[Video]:
    """Create sample videos."""
    logger.info("Creating sample videos...")
    videos = []
    
    for i in range(5):
        user = random.choice(users)
        niche = random.choice(SAMPLE_NICHES)
        script = scripts[i % len(scripts)] if i < len(scripts) else None
        
        video = Video(
            user_id=user.id,
            script_id=script.id if script else None,
            title=f"Sample {niche} Video #{i+1}",
            description=f"This is a sample video for {niche}",
            niche=niche,
            style="calm",
            status="completed" if i < 3 else "queued",
            duration_seconds=random.randint(300, 900),
            file_path=f"/output_videos/video_{i+1}.mp4" if i < 3 else f"/tmp/video_{i+1}.mp4",
            thumbnail_path=f"/output_videos/video_{i+1}_thumb.jpg" if i < 3 else None,
            file_size_bytes=random.randint(10000000, 50000000) if i < 3 else None,
            resolution="1920x1080",
            tags=["meditation", "relaxation", "sleep"],
            keywords=["meditation", "relaxation"],
            category="Education",
            total_views=random.randint(0, 10000) if i < 3 else 0,
            total_likes=random.randint(0, 500) if i < 3 else 0,
            total_comments=random.randint(0, 50) if i < 3 else 0,
            generation_time_seconds=random.uniform(60.0, 180.0) if i < 3 else None,
            ai_model_used="ollama:mistral",
            tts_model_used="coqui",
            created_at=datetime.now() - timedelta(days=random.randint(1, 30))
        )
        db.add(video)
        videos.append(video)
    
    db.commit()
    logger.info(f"✅ Created {len(videos)} videos")
    return videos


def seed_video_assets(db: Session, videos: list[Video], assets: list[Asset]) -> list[VideoAsset]:
    """Link assets to videos."""
    logger.info("Linking assets to videos...")
    video_assets = []
    
    # Link video assets to first 3 completed videos
    for video in videos[:3]:
        for i, asset in enumerate(random.sample(assets[:2], 2)):  # 2 video assets
            video_asset = VideoAsset(
                video_id=video.id,
                asset_id=asset.id,
                sequence_order=i,
                start_time_seconds=i * 30.0,
                duration_seconds=30.0
            )
            db.add(video_asset)
            video_assets.append(video_asset)
    
    db.commit()
    logger.info(f"✅ Created {len(video_assets)} video-asset links")
    return video_assets


def seed_publishes(db: Session, videos: list[Video], platforms: list[Platform]) -> list[Publish]:
    """Create sample publish records."""
    logger.info("Creating publish records...")
    publishes = []
    
    youtube = next(p for p in platforms if p.name == PlatformName.YOUTUBE)
    
    for video in videos[:3]:  # Only completed videos
        publish = Publish(
            video_id=video.id,
            platform_id=youtube.id,
            status="success",
            platform_video_id=f"YT_{random.randint(100000, 999999)}",
            platform_url=f"https://youtube.com/watch?v=sample{video.id}",
            published_at=video.created_at + timedelta(hours=1)
        )
        db.add(publish)
        publishes.append(publish)
    
    db.commit()
    logger.info(f"✅ Created {len(publishes)} publish records")
    return publishes


def seed_configs(db: Session) -> list[Configuration]:
    """Create sample system configurations."""
    logger.info("Creating system configurations...")
    configs = []
    
    for config_data in SAMPLE_CONFIGS:
        config = Configuration(**config_data)
        db.add(config)
        configs.append(config)
    
    db.commit()
    logger.info(f"✅ Created {len(configs)} system configs")
    return configs


def seed_analytics(db: Session, videos: list[Video]) -> list[Analytics]:
    """Create sample analytics records."""
    logger.info("Creating analytics records...")
    analytics_records = []
    
    for video in videos[:3]:  # Only completed videos
        # Create analytics for different dates
        for days_ago in [7, 14, 30]:
            analytic = Analytics(
                video_id=video.id,
                date=datetime.now().date() - timedelta(days=days_ago),
                views=random.randint(100, 1000),
                likes=random.randint(10, 100),
                comments=random.randint(0, 20),
                shares=random.randint(0, 50),
                watch_time_seconds=random.randint(5000, 50000),
                impressions=random.randint(1000, 10000),
                click_through_rate=random.uniform(0.01, 0.10),
                average_view_duration_seconds=random.randint(60, 600)
            )
            db.add(analytic)
            analytics_records.append(analytic)
    
    db.commit()
    logger.info(f"✅ Created {len(analytics_records)} analytics records")
    return analytics_records


# ============================================
# MAIN SEEDING FUNCTION
# ============================================

def seed_database(clear_existing: bool = False) -> None:
    """
    Seed the database with sample data.
    
    Args:
        clear_existing: If True, drop all tables before seeding (WARNING: destructive!)
    """
    try:
        logger.info("="*70)
        logger.info("DATABASE SEEDING")
        logger.info("="*70)
        
        if clear_existing:
            logger.warning("⚠️  Dropping all existing tables...")
            Base.metadata.drop_all(bind=engine)
            logger.info("Creating fresh tables...")
            Base.metadata.create_all(bind=engine)
        
        db = SessionLocal()
        
        try:
            # Seed in order (respecting foreign key constraints)
            users = seed_users(db)
            platforms = seed_platforms(db)
            assets = seed_assets(db)
            scripts = seed_scripts(db)
            videos = seed_videos(db, users, scripts)
            video_assets = seed_video_assets(db, videos, assets)
            publishes = seed_publishes(db, videos, platforms)
            configs = seed_configs(db)
            analytics = seed_analytics(db, videos)
            
            logger.info("\n" + "="*70)
            logger.info("SEEDING SUMMARY")
            logger.info("="*70)
            logger.info(f"Users:            {len(users)}")
            logger.info(f"Platforms:        {len(platforms)}")
            logger.info(f"Assets:           {len(assets)}")
            logger.info(f"Scripts:          {len(scripts)}")
            logger.info(f"Videos:           {len(videos)}")
            logger.info(f"Video-Assets:     {len(video_assets)}")
            logger.info(f"Publishes:        {len(publishes)}")
            logger.info(f"Configurations:   {len(configs)}")
            logger.info(f"Analytics:        {len(analytics)}")
            logger.info("="*70)
            logger.info("✅ Database seeding completed successfully!")
            
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"❌ Seeding failed: {e}")
        logger.exception("Full error details:")
        sys.exit(1)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Seed database with sample data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Seed database (keep existing data)
  python scripts/seed_database.py
  
  # Clear existing data and seed fresh
  python scripts/seed_database.py --clear
        """
    )
    
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing data before seeding (WARNING: destructive!)"
    )
    
    args = parser.parse_args()
    
    if args.clear:
        response = input("⚠️  This will DELETE ALL existing data! Continue? (yes/no): ").strip().lower()
        if response != "yes":
            logger.info("❌ Seeding cancelled")
            sys.exit(0)
    
    seed_database(clear_existing=args.clear)


if __name__ == "__main__":
    main()
