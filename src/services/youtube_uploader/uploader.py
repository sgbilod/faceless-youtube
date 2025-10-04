"""
YouTube Video Upload Service

Handles video uploads to YouTube with:
- Resumable uploads for large files
- Automatic retry with exponential backoff
- Progress tracking
- Metadata management (title, description, tags, category, privacy)
- Thumbnail upload
- Playlist management
- Caption/subtitle upload
- End card management
"""

import os
import logging
import asyncio
import mimetypes
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError, ResumableUploadError
import httplib2

from pydantic import BaseModel, Field, validator
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from .auth_manager import AuthManager

logger = logging.getLogger(__name__)


class UploadStatus(str, Enum):
    """Upload status"""
    PENDING = "pending"
    PREPARING = "preparing"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PrivacyStatus(str, Enum):
    """Video privacy status"""
    PUBLIC = "public"
    UNLISTED = "unlisted"
    PRIVATE = "private"


class Category(str, Enum):
    """YouTube video categories"""
    FILM_ANIMATION = "1"
    AUTOS_VEHICLES = "2"
    MUSIC = "10"
    PETS_ANIMALS = "15"
    SPORTS = "17"
    TRAVEL_EVENTS = "19"
    GAMING = "20"
    PEOPLE_BLOGS = "22"
    COMEDY = "23"
    ENTERTAINMENT = "24"
    NEWS_POLITICS = "25"
    HOWTO_STYLE = "26"
    EDUCATION = "27"
    SCIENCE_TECHNOLOGY = "28"
    NONPROFITS_ACTIVISM = "29"


@dataclass
class UploadConfig:
    """Upload configuration"""
    chunk_size: int = 1024 * 1024 * 10  # 10MB chunks
    max_retries: int = 5
    retry_delay_seconds: int = 2
    timeout_seconds: int = 600
    notify_subscribers: bool = True
    auto_levels: bool = True  # Auto color correction
    stabilize: bool = False  # Video stabilization
    
    # Default metadata
    default_privacy: PrivacyStatus = PrivacyStatus.PRIVATE
    default_category: Category = Category.EDUCATION
    default_language: str = "en"
    default_tags: List[str] = field(default_factory=list)


class VideoMetadata(BaseModel):
    """Video metadata"""
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=5000)
    tags: List[str] = Field(default_factory=list, max_items=500)
    category: Category = Category.EDUCATION
    privacy_status: PrivacyStatus = PrivacyStatus.PRIVATE
    language: str = "en"
    
    # Optional metadata
    default_audio_language: Optional[str] = None
    recording_date: Optional[datetime] = None
    license: str = "youtube"  # "youtube" or "creativeCommon"
    embeddable: bool = True
    public_stats_viewable: bool = True
    made_for_kids: bool = False
    
    # Scheduling
    publish_at: Optional[datetime] = None  # Schedule publish time
    
    # Playlist
    playlist_id: Optional[str] = None
    
    @validator("title")
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()
    
    @validator("tags")
    def validate_tags(cls, v):
        # YouTube has character limit for all tags combined
        total_chars = sum(len(tag) for tag in v)
        if total_chars > 500:
            raise ValueError("Total tag characters exceed 500 limit")
        return v


class UploadResult(BaseModel):
    """Upload result"""
    video_id: str
    url: str
    title: str
    status: UploadStatus
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Upload stats
    file_size_bytes: int
    duration_seconds: Optional[float] = None
    upload_time_seconds: float
    
    # Metadata
    privacy_status: PrivacyStatus
    thumbnail_url: Optional[str] = None
    playlist_id: Optional[str] = None
    
    # Processing info
    processing_status: Optional[str] = None
    error_message: Optional[str] = None


class VideoUploader:
    """
    YouTube video uploader with resumable uploads
    
    Features:
    - Resumable uploads for large files
    - Automatic retry with exponential backoff
    - Progress tracking with callbacks
    - Thumbnail upload
    - Playlist management
    - Caption upload
    - End card management
    
    Example:
        uploader = VideoUploader(auth_manager=auth)
        
        result = await uploader.upload(
            account_name="main",
            video_path="video.mp4",
            metadata=VideoMetadata(
                title="My Video",
                description="Description",
                tags=["tag1", "tag2"],
                privacy_status=PrivacyStatus.PUBLIC
            ),
            thumbnail_path="thumbnail.jpg",
            progress_callback=lambda p: print(f"Progress: {p}%")
        )
        
        print(f"Video URL: {result.url}")
    """
    
    def __init__(
        self,
        auth_manager: AuthManager,
        config: Optional[UploadConfig] = None
    ):
        self.auth_manager = auth_manager
        self.config = config or UploadConfig()
        self._upload_tasks: Dict[str, asyncio.Task] = {}
    
    async def upload(
        self,
        account_name: str,
        video_path: str,
        metadata: VideoMetadata,
        thumbnail_path: Optional[str] = None,
        captions: Optional[List[Dict[str, str]]] = None,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> UploadResult:
        """
        Upload video to YouTube
        
        Args:
            account_name: Account to upload to
            video_path: Path to video file
            metadata: Video metadata
            thumbnail_path: Optional thumbnail image path
            captions: Optional list of caption files [{"file": "path.srt", "language": "en"}]
            progress_callback: Optional callback for progress updates (0-100)
        
        Returns:
            UploadResult with video ID and URL
        
        Raises:
            FileNotFoundError: If video file not found
            ValueError: If metadata invalid
            HttpError: If upload fails
        """
        video_path = Path(video_path)
        
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        logger.info(f"Starting upload: {video_path.name} to {account_name}")
        
        start_time = datetime.utcnow()
        
        try:
            # Get YouTube client
            youtube = await self.auth_manager.get_youtube_client(account_name)
            
            # Report progress
            if progress_callback:
                progress_callback(0)
            
            # Upload video
            video_id = await self._upload_video(
                youtube,
                video_path,
                metadata,
                progress_callback
            )
            
            logger.info(f"Video uploaded successfully: {video_id}")
            
            # Upload thumbnail if provided
            thumbnail_url = None
            if thumbnail_path:
                thumbnail_url = await self.upload_thumbnail(
                    account_name,
                    video_id,
                    thumbnail_path
                )
            
            # Upload captions if provided
            if captions:
                await self._upload_captions(youtube, video_id, captions)
            
            # Add to playlist if specified
            if metadata.playlist_id:
                await self.add_to_playlist(
                    account_name,
                    video_id,
                    metadata.playlist_id
                )
            
            # Calculate upload time
            upload_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Get file size
            file_size = video_path.stat().st_size
            
            # Create result
            result = UploadResult(
                video_id=video_id,
                url=f"https://www.youtube.com/watch?v={video_id}",
                title=metadata.title,
                status=UploadStatus.COMPLETED,
                file_size_bytes=file_size,
                upload_time_seconds=upload_time,
                privacy_status=metadata.privacy_status,
                thumbnail_url=thumbnail_url,
                playlist_id=metadata.playlist_id,
                processing_status="processing"
            )
            
            if progress_callback:
                progress_callback(100)
            
            logger.info(f"Upload completed in {upload_time:.1f}s: {result.url}")
            return result
        
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=2, max=60),
        retry=retry_if_exception_type((HttpError, ResumableUploadError))
    )
    async def _upload_video(
        self,
        youtube,
        video_path: Path,
        metadata: VideoMetadata,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> str:
        """Upload video with retry logic"""
        
        # Prepare request body
        body = {
            "snippet": {
                "title": metadata.title,
                "description": metadata.description or "",
                "tags": metadata.tags,
                "categoryId": metadata.category.value,
                "defaultLanguage": metadata.language,
            },
            "status": {
                "privacyStatus": metadata.privacy_status.value,
                "embeddable": metadata.embeddable,
                "license": metadata.license,
                "publicStatsViewable": metadata.public_stats_viewable,
                "madeForKids": metadata.made_for_kids,
                "selfDeclaredMadeForKids": metadata.made_for_kids,
            }
        }
        
        # Add optional fields
        if metadata.default_audio_language:
            body["snippet"]["defaultAudioLanguage"] = metadata.default_audio_language
        
        if metadata.recording_date:
            body["recordingDetails"] = {
                "recordingDate": metadata.recording_date.isoformat()
            }
        
        # Schedule publish time
        if metadata.publish_at:
            body["status"]["publishAt"] = metadata.publish_at.isoformat()
        
        # Create media upload
        media = MediaFileUpload(
            str(video_path),
            chunksize=self.config.chunk_size,
            resumable=True,
            mimetype=self._get_mimetype(video_path)
        )
        
        # Create insert request
        request = youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media,
            notifySubscribers=self.config.notify_subscribers
        )
        
        # Upload with progress tracking
        response = None
        last_progress = 0
        
        while response is None:
            try:
                status, response = await asyncio.to_thread(request.next_chunk)
                
                if status:
                    progress = int(status.progress() * 80)  # 0-80% for upload
                    if progress > last_progress and progress_callback:
                        progress_callback(progress)
                        last_progress = progress
            
            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504]:
                    # Retryable error
                    logger.warning(f"Retryable error: {e}")
                    raise
                else:
                    # Non-retryable error
                    logger.error(f"Upload failed: {e}")
                    raise
        
        # Extract video ID
        video_id = response["id"]
        
        # Update progress to processing
        if progress_callback:
            progress_callback(90)
        
        return video_id
    
    def _get_mimetype(self, file_path: Path) -> str:
        """Get MIME type for file"""
        mimetype, _ = mimetypes.guess_type(str(file_path))
        return mimetype or "application/octet-stream"
    
    async def upload_thumbnail(
        self,
        account_name: str,
        video_id: str,
        thumbnail_path: str
    ) -> str:
        """
        Upload custom thumbnail for video
        
        Args:
            account_name: Account name
            video_id: Video ID
            thumbnail_path: Path to thumbnail image (JPG/PNG, max 2MB)
        
        Returns:
            Thumbnail URL
        """
        thumbnail_path = Path(thumbnail_path)
        
        if not thumbnail_path.exists():
            raise FileNotFoundError(f"Thumbnail not found: {thumbnail_path}")
        
        # Check file size (max 2MB)
        if thumbnail_path.stat().st_size > 2 * 1024 * 1024:
            raise ValueError("Thumbnail must be less than 2MB")
        
        youtube = await self.auth_manager.get_youtube_client(account_name)
        
        # Upload thumbnail
        await asyncio.to_thread(
            youtube.thumbnails().set,
            videoId=video_id,
            media_body=MediaFileUpload(
                str(thumbnail_path),
                mimetype=self._get_mimetype(thumbnail_path)
            )
        ).execute()
        
        # Thumbnail URL
        thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
        
        logger.info(f"Thumbnail uploaded for video {video_id}")
        return thumbnail_url
    
    async def _upload_captions(
        self,
        youtube,
        video_id: str,
        captions: List[Dict[str, str]]
    ):
        """Upload captions/subtitles"""
        for caption in captions:
            caption_file = Path(caption["file"])
            language = caption.get("language", "en")
            name = caption.get("name", f"{language} caption")
            
            if not caption_file.exists():
                logger.warning(f"Caption file not found: {caption_file}")
                continue
            
            try:
                await asyncio.to_thread(
                    youtube.captions().insert,
                    part="snippet",
                    body={
                        "snippet": {
                            "videoId": video_id,
                            "language": language,
                            "name": name,
                            "isDraft": False
                        }
                    },
                    media_body=MediaFileUpload(
                        str(caption_file),
                        mimetype="application/octet-stream"
                    )
                ).execute()
                
                logger.info(f"Caption uploaded: {language}")
            except Exception as e:
                logger.error(f"Failed to upload caption {language}: {e}")
    
    async def update_metadata(
        self,
        account_name: str,
        video_id: str,
        metadata: VideoMetadata
    ):
        """Update video metadata"""
        youtube = await self.auth_manager.get_youtube_client(account_name)
        
        body = {
            "id": video_id,
            "snippet": {
                "title": metadata.title,
                "description": metadata.description or "",
                "tags": metadata.tags,
                "categoryId": metadata.category.value,
            },
            "status": {
                "privacyStatus": metadata.privacy_status.value,
            }
        }
        
        await asyncio.to_thread(
            youtube.videos().update,
            part="snippet,status",
            body=body
        ).execute()
        
        logger.info(f"Metadata updated for video {video_id}")
    
    async def delete_video(self, account_name: str, video_id: str):
        """Delete video"""
        youtube = await self.auth_manager.get_youtube_client(account_name)
        
        await asyncio.to_thread(
            youtube.videos().delete,
            id=video_id
        ).execute()
        
        logger.info(f"Video deleted: {video_id}")
    
    async def add_to_playlist(
        self,
        account_name: str,
        video_id: str,
        playlist_id: str,
        position: Optional[int] = None
    ):
        """Add video to playlist"""
        youtube = await self.auth_manager.get_youtube_client(account_name)
        
        body = {
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": video_id
                }
            }
        }
        
        if position is not None:
            body["snippet"]["position"] = position
        
        await asyncio.to_thread(
            youtube.playlistItems().insert,
            part="snippet",
            body=body
        ).execute()
        
        logger.info(f"Video {video_id} added to playlist {playlist_id}")
    
    async def create_playlist(
        self,
        account_name: str,
        title: str,
        description: Optional[str] = None,
        privacy_status: PrivacyStatus = PrivacyStatus.PRIVATE
    ) -> str:
        """Create new playlist"""
        youtube = await self.auth_manager.get_youtube_client(account_name)
        
        body = {
            "snippet": {
                "title": title,
                "description": description or "",
            },
            "status": {
                "privacyStatus": privacy_status.value
            }
        }
        
        response = await asyncio.to_thread(
            youtube.playlists().insert,
            part="snippet,status",
            body=body
        ).execute()
        
        playlist_id = response["id"]
        logger.info(f"Playlist created: {playlist_id} - {title}")
        return playlist_id
    
    async def get_video_status(
        self,
        account_name: str,
        video_id: str
    ) -> Dict[str, Any]:
        """Get video processing status"""
        youtube = await self.auth_manager.get_youtube_client(account_name)
        
        response = await asyncio.to_thread(
            youtube.videos().list,
            part="status,processingDetails",
            id=video_id
        ).execute()
        
        if not response.get("items"):
            raise ValueError(f"Video not found: {video_id}")
        
        video = response["items"][0]
        
        return {
            "upload_status": video["status"]["uploadStatus"],
            "privacy_status": video["status"]["privacyStatus"],
            "license": video["status"]["license"],
            "embeddable": video["status"]["embeddable"],
            "public_stats_viewable": video["status"]["publicStatsViewable"],
            "processing_status": video.get("processingDetails", {}).get("processingStatus"),
            "processing_progress": video.get("processingDetails", {}).get("processingProgress"),
        }
    
    async def wait_for_processing(
        self,
        account_name: str,
        video_id: str,
        max_wait_seconds: int = 600,
        check_interval_seconds: int = 10
    ) -> bool:
        """
        Wait for video processing to complete
        
        Args:
            account_name: Account name
            video_id: Video ID
            max_wait_seconds: Maximum time to wait
            check_interval_seconds: Interval between checks
        
        Returns:
            True if processing completed, False if timeout
        """
        start_time = datetime.utcnow()
        
        while True:
            status = await self.get_video_status(account_name, video_id)
            processing_status = status.get("processing_status")
            
            if processing_status == "succeeded":
                logger.info(f"Video processing completed: {video_id}")
                return True
            
            elif processing_status == "failed":
                logger.error(f"Video processing failed: {video_id}")
                return False
            
            # Check timeout
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed >= max_wait_seconds:
                logger.warning(f"Processing timeout for video {video_id}")
                return False
            
            # Wait before next check
            await asyncio.sleep(check_interval_seconds)
    
    def cancel_upload(self, upload_id: str):
        """Cancel ongoing upload"""
        if upload_id in self._upload_tasks:
            self._upload_tasks[upload_id].cancel()
            logger.info(f"Upload cancelled: {upload_id}")
