"""
Faceless YouTube Automation Platform
Copyright © 2025 Project Contributors

This file is part of the Faceless YouTube Automation Platform.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float, 
    ForeignKey, Index, Enum as SQLEnum, JSON, BigInteger, Numeric
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()


# ============================================
# ENUMS
# ============================================

class VideoStatus(str, enum.Enum):
    """Video generation status."""
    QUEUED = "queued"
    GENERATING = "generating"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class AssetType(str, enum.Enum):
    """Asset types."""
    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"
    MUSIC = "music"
    SOUND_EFFECT = "sound_effect"


class LicenseType(str, enum.Enum):
    """Asset license types."""
    CC0 = "cc0"  # Public domain
    CC_BY = "cc_by"  # Attribution required
    CC_BY_SA = "cc_by_sa"  # Attribution + Share Alike
    PEXELS = "pexels"  # Pexels License
    PIXABAY = "pixabay"  # Pixabay License
    UNSPLASH = "unsplash"  # Unsplash License
    CUSTOM = "custom"


class PlatformName(str, enum.Enum):
    """Supported platforms."""
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    YOUTUBE_SHORTS = "youtube_shorts"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    PINTEREST = "pinterest"
    SNAPCHAT = "snapchat"


class PublishStatus(str, enum.Enum):
    """Publishing status."""
    SCHEDULED = "scheduled"
    UPLOADING = "uploading"
    PUBLISHED = "published"
    FAILED = "failed"
    DELETED = "deleted"


# ============================================
# USER MODEL
# ============================================

class User(Base):
    """User account."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Profile
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Preferences (JSON)
    preferences = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime)
    
    # Relationships
    videos = relationship("Video", back_populates="user", cascade="all, delete-orphan")
    configurations = relationship("Configuration", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


# ============================================
# VIDEO MODEL
# ============================================

class Video(Base):
    """Generated video."""
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    script_id = Column(Integer, ForeignKey("scripts.id"))
    
    # Basic Info
    title = Column(String(255), nullable=False)
    description = Column(Text)
    niche = Column(String(100), index=True)  # meditation, sleep, focus, etc.
    style = Column(String(100))  # calm, energetic, peaceful, etc.
    
    # Video Properties
    duration_seconds = Column(Integer, nullable=False)
    resolution = Column(String(20), default="1080p")  # 1080p, 720p, 480p
    fps = Column(Integer, default=30)
    aspect_ratio = Column(String(10), default="16:9")  # 16:9, 9:16, 1:1
    
    # Files
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(BigInteger)
    thumbnail_path = Column(String(500))
    
    # SEO & Metadata
    tags = Column(JSON, default=list)  # List of tags
    keywords = Column(JSON, default=list)  # SEO keywords
    category = Column(String(100))
    language = Column(String(10), default="en")
    
    # Status
    status = Column(SQLEnum(VideoStatus), default=VideoStatus.QUEUED, nullable=False, index=True)
    error_message = Column(Text)
    
    # Generation Metadata
    generation_time_seconds = Column(Float)
    ai_model_used = Column(String(100))  # ollama:mistral, gpt-3.5-turbo, etc.
    tts_model_used = Column(String(100))  # coqui, pyttsx3, elevenlabs
    
    # Analytics Summary (updated periodically)
    total_views = Column(BigInteger, default=0)
    total_likes = Column(Integer, default=0)
    total_comments = Column(Integer, default=0)
    total_shares = Column(Integer, default=0)
    estimated_revenue = Column(Numeric(10, 2), default=0)
    
    # Additional Metadata (renamed from 'metadata' to avoid SQLAlchemy reserved attribute)
    video_metadata = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    published_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="videos")
    script = relationship("Script", back_populates="videos")
    video_assets = relationship("VideoAsset", back_populates="video", cascade="all, delete-orphan")
    publishes = relationship("Publish", back_populates="video", cascade="all, delete-orphan")
    analytics = relationship("Analytics", back_populates="video", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_video_user_created", "user_id", "created_at"),
        Index("idx_video_niche_status", "niche", "status"),
    )
    
    def __repr__(self):
        return f"<Video(id={self.id}, title='{self.title}', status='{self.status.value}')>"


# ============================================
# SCRIPT MODEL
# ============================================

class Script(Base):
    """Generated or uploaded script."""
    __tablename__ = "scripts"
    
    id = Column(Integer, primary_key=True)
    
    # Content
    content = Column(Text, nullable=False)
    title = Column(String(255))
    
    # Metadata
    niche = Column(String(100), index=True)
    style = Column(String(100))
    target_duration_seconds = Column(Integer)
    actual_word_count = Column(Integer)
    
    # Generation Info
    generator_model = Column(String(100))  # ollama:mistral, gpt-3.5-turbo, manual
    ai_confidence = Column(Float)  # 0.0-1.0
    prompt_used = Column(Text)
    
    # SEO
    keywords = Column(JSON, default=list)
    
    # Usage Tracking
    usage_count = Column(Integer, default=0)
    performance_score = Column(Float)  # Average video performance
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    videos = relationship("Video", back_populates="script")
    
    def __repr__(self):
        return f"<Script(id={self.id}, niche='{self.niche}', words={self.actual_word_count})>"


# ============================================
# ASSET MODEL
# ============================================

class Asset(Base):
    """Video, image, or audio asset."""
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True)
    
    # Basic Info
    asset_type = Column(SQLEnum(AssetType), nullable=False, index=True)
    source_platform = Column(String(50), nullable=False, index=True)  # pexels, pixabay, etc.
    source_id = Column(String(255))  # Original ID from source platform
    source_url = Column(String(500))
    
    # Files
    file_path = Column(String(500), nullable=False)
    thumbnail_path = Column(String(500))
    file_size_bytes = Column(BigInteger)
    
    # Media Properties
    width = Column(Integer)
    height = Column(Integer)
    duration_seconds = Column(Float)
    format = Column(String(20))  # mp4, jpg, mp3, etc.
    codec = Column(String(50))
    bitrate = Column(Integer)
    
    # License & Attribution
    license_type = Column(SQLEnum(LicenseType), nullable=False)
    attribution_required = Column(Boolean, default=False)
    attribution_text = Column(Text)
    author_name = Column(String(255))
    author_url = Column(String(500))
    
    # Quality & Classification
    quality_score = Column(Float, index=True)  # 0.0-1.0
    perceptual_hash = Column(String(64), index=True)  # For deduplication
    is_duplicate = Column(Boolean, default=False)
    original_asset_id = Column(Integer, ForeignKey("assets.id"))
    
    # Tags & Classification
    tags = Column(JSON, default=list)  # [{"tag": "nature", "confidence": 0.95}]
    emotion_tags = Column(JSON, default=list)  # ["calm", "peaceful"]
    theme_tags = Column(JSON, default=list)  # ["nature", "landscape"]
    color_palette = Column(JSON, default=list)  # ["#FF5733", "#C70039"]
    
    # Performance Tracking
    usage_count = Column(Integer, default=0)
    avg_video_views = Column(Float)
    avg_engagement_rate = Column(Float)
    
    # Status
    is_active = Column(Boolean, default=True)
    download_failed = Column(Boolean, default=False)
    
    # Metadata (renamed from 'metadata' to avoid SQLAlchemy reserved attribute)
    asset_metadata = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    last_used_at = Column(DateTime)
    
    # Relationships
    video_assets = relationship("VideoAsset", back_populates="asset")
    duplicates = relationship("Asset", remote_side=[id])
    
    # Indexes
    __table_args__ = (
        Index("idx_asset_type_quality", "asset_type", "quality_score"),
        Index("idx_asset_source_id", "source_platform", "source_id"),
        Index("idx_asset_performance", "avg_video_views", "avg_engagement_rate"),
    )
    
    def __repr__(self):
        return f"<Asset(id={self.id}, type='{self.asset_type.value}', source='{self.source_platform}')>"


# ============================================
# VIDEO-ASSET JUNCTION
# ============================================

class VideoAsset(Base):
    """Many-to-many relationship between videos and assets."""
    __tablename__ = "video_assets"
    
    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    
    # Timeline Position
    start_time_seconds = Column(Float, nullable=False)
    duration_seconds = Column(Float, nullable=False)
    order_index = Column(Integer, nullable=False)  # Order in video
    
    # Effects & Transforms
    effects = Column(JSON, default=dict)  # {"transition": "fade", "zoom": 1.2}
    volume = Column(Float, default=1.0)  # For audio assets
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    video = relationship("Video", back_populates="video_assets")
    asset = relationship("Asset", back_populates="video_assets")
    
    # Indexes
    __table_args__ = (
        Index("idx_video_asset_order", "video_id", "order_index"),
    )
    
    def __repr__(self):
        return f"<VideoAsset(video_id={self.video_id}, asset_id={self.asset_id})>"


# ============================================
# PLATFORM MODEL
# ============================================

class Platform(Base):
    """Publishing platform configuration."""
    __tablename__ = "platforms"
    
    id = Column(Integer, primary_key=True)
    name = Column(SQLEnum(PlatformName), unique=True, nullable=False)
    
    # Status
    enabled = Column(Boolean, default=True)
    is_configured = Column(Boolean, default=False)
    
    # API Configuration
    api_version = Column(String(20))
    credentials_encrypted = Column(Text)  # Encrypted JSON
    
    # Publishing Settings
    default_config = Column(JSON, default=dict)  # Default publish settings
    rate_limit_per_day = Column(Integer)
    max_video_size_mb = Column(Integer)
    supported_formats = Column(JSON, default=list)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    last_publish_at = Column(DateTime)
    
    # Relationships
    publishes = relationship("Publish", back_populates="platform")
    
    def __repr__(self):
        return f"<Platform(name='{self.name.value}', enabled={self.enabled})>"


# ============================================
# PUBLISH MODEL
# ============================================

class Publish(Base):
    """Video publish to platform."""
    __tablename__ = "publishes"
    
    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False, index=True)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False, index=True)
    
    # Platform Info
    platform_video_id = Column(String(255), index=True)  # ID on platform (YouTube video ID, etc.)
    url = Column(String(500))
    
    # Status
    status = Column(SQLEnum(PublishStatus), default=PublishStatus.SCHEDULED, nullable=False, index=True)
    error_message = Column(Text)
    
    # Scheduling
    scheduled_at = Column(DateTime, index=True)
    published_at = Column(DateTime)
    
    # Platform-Specific Metadata
    platform_metadata = Column(JSON, default=dict)  # Platform-specific fields
    
    # Performance Tracking
    views = Column(BigInteger, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    video = relationship("Video", back_populates="publishes")
    platform = relationship("Platform", back_populates="publishes")
    
    # Indexes
    __table_args__ = (
        Index("idx_publish_status_scheduled", "status", "scheduled_at"),
        Index("idx_publish_platform_video", "platform_id", "platform_video_id"),
    )
    
    def __repr__(self):
        return f"<Publish(id={self.id}, video_id={self.video_id}, status='{self.status.value}')>"


# ============================================
# ANALYTICS MODEL
# ============================================

class Analytics(Base):
    """Video analytics (time-series data)."""
    __tablename__ = "analytics"
    
    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False, index=True)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False, index=True)
    
    # Metrics
    views = Column(BigInteger, default=0)
    likes = Column(Integer, default=0)
    dislikes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    watch_time_minutes = Column(Float, default=0)
    
    # Engagement
    ctr = Column(Float)  # Click-through rate
    avg_view_duration_seconds = Column(Float)
    avg_view_percentage = Column(Float)
    
    # Revenue
    ad_revenue = Column(Numeric(10, 2), default=0)
    affiliate_revenue = Column(Numeric(10, 2), default=0)
    total_revenue = Column(Numeric(10, 2), default=0)
    
    # Audience
    unique_viewers = Column(Integer)
    subscriber_growth = Column(Integer)
    
    # Timestamps
    recorded_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    video = relationship("Video", back_populates="analytics")
    
    # Indexes
    __table_args__ = (
        Index("idx_analytics_video_recorded", "video_id", "recorded_at"),
        Index("idx_analytics_platform_recorded", "platform_id", "recorded_at"),
    )
    
    def __repr__(self):
        return f"<Analytics(video_id={self.video_id}, views={self.views}, recorded_at={self.recorded_at})>"


# ============================================
# CONFIGURATION MODEL
# ============================================

class Configuration(Base):
    """User configuration and preferences."""
    __tablename__ = "configurations"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Configuration
    config_key = Column(String(100), nullable=False)  # video_defaults, ai_settings, etc.
    config_value = Column(JSON, nullable=False)
    
    # Metadata
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="configurations")
    
    # Unique constraint
    __table_args__ = (
        Index("idx_config_user_key", "user_id", "config_key", unique=True),
    )
    
    def __repr__(self):
        return f"<Configuration(key='{self.config_key}', user_id={self.user_id})>"


# ============================================
# REVENUE MODEL
# ============================================

class Revenue(Base):
    """Revenue tracking."""
    __tablename__ = "revenue"
    
    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey("videos.id"), index=True)
    platform_id = Column(Integer, ForeignKey("platforms.id"), index=True)
    
    # Revenue Details
    revenue_type = Column(String(50), nullable=False)  # ad, affiliate, sponsorship
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")
    
    # Attribution
    source = Column(String(255))  # Specific affiliate link, ad network, etc.
    conversion_id = Column(String(255))
    
    # Metadata (renamed from 'metadata' to avoid SQLAlchemy reserved attribute)
    revenue_metadata = Column(JSON, default=dict)
    
    # Timestamps
    earned_at = Column(DateTime, nullable=False, index=True)
    recorded_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index("idx_revenue_video_earned", "video_id", "earned_at"),
        Index("idx_revenue_type_earned", "revenue_type", "earned_at"),
    )
    
    def __repr__(self):
        return f"<Revenue(amount={self.amount}, type='{self.revenue_type}', earned_at={self.earned_at})>"
