"""
Input validation and sanitization for API endpoints

Provides Pydantic models with comprehensive validation:
- Input sanitization (XSS, injection prevention)
- Type validation
- Format validation (emails, URLs, dates)
- Length constraints
- Pattern matching
- File upload validation

All user inputs should be validated using these models.
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from fastapi import UploadFile, HTTPException
import re
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class ContentNiche(str, Enum):
    """Valid content niches"""
    MEDITATION = "meditation"
    AFFIRMATION = "affirmation"
    MOTIVATION = "motivation"
    SLEEP = "sleep"
    MINDFULNESS = "mindfulness"
    HEALING = "healing"
    GRATITUDE = "gratitude"


class VideoPrivacy(str, Enum):
    """YouTube privacy settings"""
    PUBLIC = "public"
    UNLISTED = "unlisted"
    PRIVATE = "private"


# ============================================================================
# REQUEST MODELS
# ============================================================================

class VideoScheduleRequest(BaseModel):
    """Request model for scheduling a video generation"""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    title: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Video title",
        examples=["Deep Sleep Meditation with Ocean Sounds"]
    )
    
    niche: ContentNiche = Field(
        ...,
        description="Content niche/category"
    )
    
    scheduled_time: Optional[datetime] = Field(
        None,
        description="When to publish (ISO 8601 format)"
    )
    
    description: Optional[str] = Field(
        None,
        max_length=5000,
        description="Video description"
    )
    
    tags: Optional[List[str]] = Field(
        None,
        max_items=30,
        description="Video tags (max 30)"
    )
    
    privacy: VideoPrivacy = Field(
        default=VideoPrivacy.PUBLIC,
        description="YouTube privacy setting"
    )
    
    @field_validator('title')
    @classmethod
    def sanitize_title(cls, v: str) -> str:
        """Remove HTML tags and dangerous characters from title"""
        # Remove HTML/XML tags
        v = re.sub(r'<[^>]+>', '', v)
        # Remove excessive whitespace
        v = ' '.join(v.split())
        # Remove potentially dangerous characters
        v = re.sub(r'[<>"\'`]', '', v)
        
        if not v:
            raise ValueError("Title cannot be empty after sanitization")
        
        return v
    
    @field_validator('description')
    @classmethod
    def sanitize_description(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize description text"""
        if v is None:
            return v
        
        # Remove script tags (XSS prevention)
        v = re.sub(
            r'<script[^>]*>.*?</script>',
            '',
            v,
            flags=re.DOTALL | re.IGNORECASE
        )
        
        # Remove other potentially dangerous tags
        dangerous_tags = ['iframe', 'object', 'embed', 'applet']
        for tag in dangerous_tags:
            v = re.sub(
                f'<{tag}[^>]*>.*?</{tag}>',
                '',
                v,
                flags=re.DOTALL | re.IGNORECASE
            )
        
        # Remove excessive whitespace
        v = ' '.join(v.split())
        
        return v
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate and sanitize tags"""
        if v is None:
            return v
        
        validated_tags = []
        for tag in v:
            # Remove special characters (YouTube doesn't allow them anyway)
            tag = re.sub(r'[^a-zA-Z0-9\s-]', '', tag)
            # Trim and limit length
            tag = tag.strip()[:50]
            
            if tag:
                validated_tags.append(tag)
        
        return validated_tags[:30]  # YouTube limit
    
    @field_validator('scheduled_time')
    @classmethod
    def validate_future_time(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure scheduled time is in the future"""
        if v and v <= datetime.now():
            raise ValueError("Scheduled time must be in the future")
        return v


class ScriptGenerationRequest(BaseModel):
    """Request model for script generation"""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    niche: ContentNiche = Field(
        ...,
        description="Content niche"
    )
    
    duration_minutes: int = Field(
        default=10,
        ge=1,
        le=60,
        description="Desired duration in minutes"
    )
    
    tone: Optional[str] = Field(
        default="calm",
        max_length=50,
        description="Tone/mood (calm, energetic, peaceful, etc.)"
    )
    
    keywords: Optional[List[str]] = Field(
        None,
        max_items=10,
        description="Keywords to include"
    )
    
    @field_validator('tone')
    @classmethod
    def sanitize_tone(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize tone input"""
        if v is None:
            return v
        
        # Only allow letters, spaces, hyphens
        v = re.sub(r'[^a-zA-Z\s-]', '', v)
        v = v.strip()
        
        return v if v else "calm"
    
    @field_validator('keywords')
    @classmethod
    def validate_keywords(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate keywords"""
        if v is None:
            return v
        
        validated = []
        for kw in v:
            kw = re.sub(r'[^a-zA-Z0-9\s-]', '', kw)
            kw = kw.strip()[:30]
            if kw:
                validated.append(kw)
        
        return validated[:10]


class UserRegistrationRequest(BaseModel):
    """Request model for user registration"""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    username: str = Field(
        ...,
        min_length=3,
        max_length=30,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Username (alphanumeric, underscore, hyphen only)",
        examples=["john_doe", "creator-2024"]
    )
    
    email: str = Field(
        ...,
        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        description="Valid email address",
        examples=["user@example.com"]
    )
    
    password: str = Field(
        ...,
        min_length=12,
        max_length=128,
        description="Strong password (min 12 characters)"
    )
    
    full_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Full name"
    )
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Additional email validation"""
        v = v.lower().strip()
        
        # Check for suspicious patterns
        if '..' in v or v.startswith('.') or v.endswith('.'):
            raise ValueError("Invalid email format")
        
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Ensure password meets complexity requirements"""
        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain uppercase letter")
        if not re.search(r'[a-z]', v):
            raise ValueError("Password must contain lowercase letter")
        if not re.search(r'[0-9]', v):
            raise ValueError("Password must contain digit")
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>_\-+=]', v):
            raise ValueError("Password must contain special character")
        
        # Check for common weak passwords
        common_passwords = {
            'password123', 'admin123456', 'qwerty123456',
            'letmein12345', 'welcome12345'
        }
        if v.lower() in common_passwords:
            raise ValueError("Password is too common")
        
        return v
    
    @field_validator('full_name')
    @classmethod
    def sanitize_name(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize full name"""
        if v is None:
            return v
        
        # Only allow letters, spaces, hyphens, apostrophes
        v = re.sub(r'[^a-zA-Z\s\'-]', '', v)
        v = ' '.join(v.split())  # Normalize whitespace
        
        return v if v else None


class UserLoginRequest(BaseModel):
    """Request model for user login"""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    username: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Username or email"
    )
    
    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Password"
    )


# ============================================================================
# FILE UPLOAD VALIDATION
# ============================================================================

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/gif",
    "image/webp"
}

ALLOWED_VIDEO_TYPES = {
    "video/mp4",
    "video/mpeg",
    "video/quicktime",
    "video/x-msvideo",
    "video/webm"
}

ALLOWED_AUDIO_TYPES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/ogg",
    "audio/webm"
}

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500 MB
MAX_AUDIO_SIZE = 50 * 1024 * 1024  # 50 MB


async def validate_image_upload(file: UploadFile) -> None:
    """
    Validate image file upload
    
    Raises:
        HTTPException: If validation fails
    """
    # Check content type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid image type: {file.content_type}. "
                f"Allowed: {', '.join(ALLOWED_IMAGE_TYPES)}"
            )
        )
    
    # Check filename
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")
    
    # Sanitize filename
    safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '', file.filename)
    if not safe_filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    # Check file extension
    ext = safe_filename.lower().split('.')[-1]
    if ext not in {'jpg', 'jpeg', 'png', 'gif', 'webp'}:
        raise HTTPException(status_code=400, detail="Invalid file extension")
    
    # Check file size
    contents = await file.read()
    file_size = len(contents)
    await file.seek(0)  # Reset file pointer
    
    if file_size > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Image too large. Max: {MAX_IMAGE_SIZE / 1024 / 1024}MB"
        )
    
    if file_size == 0:
        raise HTTPException(status_code=400, detail="Empty file")


async def validate_video_upload(file: UploadFile) -> None:
    """
    Validate video file upload
    
    Raises:
        HTTPException: If validation fails
    """
    # Check content type
    if file.content_type not in ALLOWED_VIDEO_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid video type: {file.content_type}. "
                f"Allowed: {', '.join(ALLOWED_VIDEO_TYPES)}"
            )
        )
    
    # Check filename
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")
    
    # Sanitize filename
    safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '', file.filename)
    if not safe_filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    # Check file extension
    ext = safe_filename.lower().split('.')[-1]
    if ext not in {'mp4', 'mpeg', 'mov', 'avi', 'webm'}:
        raise HTTPException(status_code=400, detail="Invalid file extension")
    
    # Check file size
    contents = await file.read()
    file_size = len(contents)
    await file.seek(0)
    
    if file_size > MAX_VIDEO_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Video too large. Max: {MAX_VIDEO_SIZE / 1024 / 1024}MB"
        )
    
    if file_size == 0:
        raise HTTPException(status_code=400, detail="Empty file")


async def validate_audio_upload(file: UploadFile) -> None:
    """
    Validate audio file upload
    
    Raises:
        HTTPException: If validation fails
    """
    # Check content type
    if file.content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid audio type: {file.content_type}. "
                f"Allowed: {', '.join(ALLOWED_AUDIO_TYPES)}"
            )
        )
    
    # Check filename
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")
    
    # Sanitize filename
    safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '', file.filename)
    if not safe_filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    # Check file extension
    ext = safe_filename.lower().split('.')[-1]
    if ext not in {'mp3', 'mpeg', 'wav', 'ogg', 'webm'}:
        raise HTTPException(status_code=400, detail="Invalid file extension")
    
    # Check file size
    contents = await file.read()
    file_size = len(contents)
    await file.seek(0)
    
    if file_size > MAX_AUDIO_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Audio too large. Max: {MAX_AUDIO_SIZE / 1024 / 1024}MB"
        )
    
    if file_size == 0:
        raise HTTPException(status_code=400, detail="Empty file")
