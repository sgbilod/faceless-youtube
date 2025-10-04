"""
Upload Queue Manager

Manages multiple YouTube uploads with:
- Priority queue for upload ordering
- Scheduling for future uploads
- Concurrent upload limits
- Upload retry management
- Progress tracking across queue
- Batch upload operations
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field

from .uploader import VideoUploader, VideoMetadata, UploadResult, UploadStatus
from .auth_manager import AuthManager

logger = logging.getLogger(__name__)


class QueuePriority(str, Enum):
    """Upload priority"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class QueueStatus(str, Enum):
    """Queue item status"""
    QUEUED = "queued"
    SCHEDULED = "scheduled"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class QueueConfig:
    """Queue configuration"""
    max_concurrent_uploads: int = 2
    retry_failed_uploads: bool = True
    max_retries: int = 3
    retry_delay_minutes: int = 5
    auto_start: bool = True
    cleanup_completed: bool = True
    cleanup_after_hours: int = 24


class QueueItem(BaseModel):
    """Queue item"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    account_name: str
    video_path: str
    metadata: VideoMetadata
    thumbnail_path: Optional[str] = None
    captions: Optional[List[Dict[str, str]]] = None
    
    # Queue properties
    priority: QueuePriority = QueuePriority.NORMAL
    status: QueueStatus = QueueStatus.QUEUED
    scheduled_time: Optional[datetime] = None
    
    # Progress tracking
    progress_percent: float = 0.0
    retry_count: int = 0
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Result
    upload_result: Optional[UploadResult] = None
    error_message: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True


class UploadQueue:
    """
    Manages queue of YouTube uploads
    
    Features:
    - Priority-based queue ordering
    - Concurrent upload limits
    - Upload scheduling
    - Automatic retry on failure
    - Progress tracking across all uploads
    - Batch operations
    
    Example:
        queue = UploadQueue(
            auth_manager=auth,
            uploader=uploader,
            config=QueueConfig(max_concurrent_uploads=2)
        )
        
        # Add to queue
        item_id = await queue.add(
            account_name="main",
            video_path="video.mp4",
            metadata=VideoMetadata(...),
            priority=QueuePriority.HIGH
        )
        
        # Start processing
        await queue.start()
        
        # Check status
        status = queue.get_status(item_id)
        
        # Wait for completion
        result = await queue.wait_for_completion(item_id)
    """
    
    def __init__(
        self,
        auth_manager: AuthManager,
        uploader: VideoUploader,
        config: Optional[QueueConfig] = None
    ):
        self.auth_manager = auth_manager
        self.uploader = uploader
        self.config = config or QueueConfig()
        
        self._queue: List[QueueItem] = []
        self._active_uploads: Dict[str, asyncio.Task] = {}
        self._processing = False
        self._process_task: Optional[asyncio.Task] = None
        
        # Statistics
        self._stats = {
            "total_added": 0,
            "total_completed": 0,
            "total_failed": 0,
            "total_cancelled": 0,
        }
    
    async def add(
        self,
        account_name: str,
        video_path: str,
        metadata: VideoMetadata,
        thumbnail_path: Optional[str] = None,
        captions: Optional[List[Dict[str, str]]] = None,
        priority: QueuePriority = QueuePriority.NORMAL,
        scheduled_time: Optional[datetime] = None
    ) -> str:
        """
        Add video to upload queue
        
        Args:
            account_name: Account to upload to
            video_path: Path to video file
            metadata: Video metadata
            thumbnail_path: Optional thumbnail path
            captions: Optional captions
            priority: Upload priority
            scheduled_time: Optional scheduled upload time
        
        Returns:
            Queue item ID
        """
        item = QueueItem(
            account_name=account_name,
            video_path=video_path,
            metadata=metadata,
            thumbnail_path=thumbnail_path,
            captions=captions,
            priority=priority,
            scheduled_time=scheduled_time,
            status=QueueStatus.SCHEDULED if scheduled_time else QueueStatus.QUEUED
        )
        
        self._queue.append(item)
        self._stats["total_added"] += 1
        
        logger.info(f"Added to queue: {item.id} - {metadata.title} (priority: {priority.value})")
        
        # Auto-start if enabled
        if self.config.auto_start and not self._processing:
            await self.start()
        
        return item.id
    
    async def add_batch(
        self,
        items: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Add multiple videos to queue
        
        Args:
            items: List of item dictionaries
        
        Returns:
            List of queue item IDs
        """
        item_ids = []
        
        for item_data in items:
            item_id = await self.add(**item_data)
            item_ids.append(item_id)
        
        logger.info(f"Added {len(item_ids)} items to queue")
        return item_ids
    
    async def start(self):
        """Start processing queue"""
        if self._processing:
            logger.warning("Queue already processing")
            return
        
        self._processing = True
        self._process_task = asyncio.create_task(self._process_queue())
        logger.info("Queue processing started")
    
    async def stop(self):
        """Stop processing queue"""
        if not self._processing:
            return
        
        self._processing = False
        
        if self._process_task:
            self._process_task.cancel()
            try:
                await self._process_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Queue processing stopped")
    
    async def _process_queue(self):
        """Process queue items"""
        while self._processing:
            try:
                # Clean up completed uploads
                self._cleanup_active_uploads()
                
                # Check if we can start new uploads
                available_slots = self.config.max_concurrent_uploads - len(self._active_uploads)
                
                if available_slots > 0:
                    # Get next items to process
                    items_to_start = self._get_next_items(available_slots)
                    
                    # Start uploads
                    for item in items_to_start:
                        await self._start_upload(item)
                
                # Wait before next check
                await asyncio.sleep(1)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in queue processing: {e}")
                await asyncio.sleep(5)
    
    def _get_next_items(self, count: int) -> List[QueueItem]:
        """Get next items to process based on priority and schedule"""
        # Filter ready items
        now = datetime.utcnow()
        ready_items = [
            item for item in self._queue
            if item.status == QueueStatus.QUEUED
            and (not item.scheduled_time or item.scheduled_time <= now)
        ]
        
        # Sort by priority (urgent > high > normal > low) and creation time
        priority_order = {
            QueuePriority.URGENT: 0,
            QueuePriority.HIGH: 1,
            QueuePriority.NORMAL: 2,
            QueuePriority.LOW: 3
        }
        
        ready_items.sort(
            key=lambda x: (priority_order[x.priority], x.created_at)
        )
        
        return ready_items[:count]
    
    def _cleanup_active_uploads(self):
        """Remove completed/failed tasks from active uploads"""
        completed = [
            item_id for item_id, task in self._active_uploads.items()
            if task.done()
        ]
        
        for item_id in completed:
            del self._active_uploads[item_id]
    
    async def _start_upload(self, item: QueueItem):
        """Start upload for queue item"""
        item.status = QueueStatus.UPLOADING
        item.started_at = datetime.utcnow()
        
        logger.info(f"Starting upload: {item.id} - {item.metadata.title}")
        
        # Create upload task
        task = asyncio.create_task(
            self._upload_with_retry(item)
        )
        
        self._active_uploads[item.id] = task
    
    async def _upload_with_retry(self, item: QueueItem):
        """Upload with retry logic"""
        while item.retry_count < self.config.max_retries:
            try:
                # Progress callback
                def progress_callback(percent: float):
                    item.progress_percent = percent
                
                # Upload
                result = await self.uploader.upload(
                    account_name=item.account_name,
                    video_path=item.video_path,
                    metadata=item.metadata,
                    thumbnail_path=item.thumbnail_path,
                    captions=item.captions,
                    progress_callback=progress_callback
                )
                
                # Success
                item.status = QueueStatus.COMPLETED
                item.completed_at = datetime.utcnow()
                item.upload_result = result
                self._stats["total_completed"] += 1
                
                logger.info(f"Upload completed: {item.id} - {result.url}")
                return
            
            except Exception as e:
                item.retry_count += 1
                item.error_message = str(e)
                
                logger.error(f"Upload failed (attempt {item.retry_count}): {item.id} - {e}")
                
                # Check if should retry
                if item.retry_count < self.config.max_retries and self.config.retry_failed_uploads:
                    # Wait before retry
                    await asyncio.sleep(self.config.retry_delay_minutes * 60)
                    logger.info(f"Retrying upload: {item.id}")
                else:
                    # Max retries reached
                    item.status = QueueStatus.FAILED
                    item.completed_at = datetime.utcnow()
                    self._stats["total_failed"] += 1
                    logger.error(f"Upload failed permanently: {item.id}")
                    return
    
    def get_item(self, item_id: str) -> Optional[QueueItem]:
        """Get queue item by ID"""
        for item in self._queue:
            if item.id == item_id:
                return item
        return None
    
    def get_status(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get status of queue item"""
        item = self.get_item(item_id)
        
        if not item:
            return None
        
        return {
            "id": item.id,
            "status": item.status.value,
            "progress_percent": item.progress_percent,
            "retry_count": item.retry_count,
            "created_at": item.created_at,
            "started_at": item.started_at,
            "completed_at": item.completed_at,
            "error_message": item.error_message,
            "upload_result": item.upload_result.dict() if item.upload_result else None
        }
    
    async def wait_for_completion(
        self,
        item_id: str,
        timeout_seconds: Optional[int] = None
    ) -> Optional[UploadResult]:
        """
        Wait for upload to complete
        
        Args:
            item_id: Queue item ID
            timeout_seconds: Optional timeout
        
        Returns:
            UploadResult if successful, None otherwise
        """
        start_time = datetime.utcnow()
        
        while True:
            item = self.get_item(item_id)
            
            if not item:
                return None
            
            if item.status == QueueStatus.COMPLETED:
                return item.upload_result
            
            elif item.status in [QueueStatus.FAILED, QueueStatus.CANCELLED]:
                return None
            
            # Check timeout
            if timeout_seconds:
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                if elapsed >= timeout_seconds:
                    return None
            
            await asyncio.sleep(1)
    
    async def cancel(self, item_id: str):
        """Cancel upload"""
        item = self.get_item(item_id)
        
        if not item:
            raise ValueError(f"Item not found: {item_id}")
        
        # Cancel if active
        if item_id in self._active_uploads:
            self._active_uploads[item_id].cancel()
            del self._active_uploads[item_id]
        
        item.status = QueueStatus.CANCELLED
        item.completed_at = datetime.utcnow()
        self._stats["total_cancelled"] += 1
        
        logger.info(f"Upload cancelled: {item_id}")
    
    async def retry(self, item_id: str):
        """Retry failed upload"""
        item = self.get_item(item_id)
        
        if not item:
            raise ValueError(f"Item not found: {item_id}")
        
        if item.status != QueueStatus.FAILED:
            raise ValueError(f"Item not in failed state: {item_id}")
        
        # Reset item
        item.status = QueueStatus.QUEUED
        item.retry_count = 0
        item.error_message = None
        item.progress_percent = 0.0
        item.started_at = None
        item.completed_at = None
        
        logger.info(f"Upload queued for retry: {item_id}")
    
    def get_queue_summary(self) -> Dict[str, Any]:
        """Get queue summary"""
        status_counts = {}
        for status in QueueStatus:
            status_counts[status.value] = sum(
                1 for item in self._queue if item.status == status
            )
        
        return {
            "total_items": len(self._queue),
            "active_uploads": len(self._active_uploads),
            "processing": self._processing,
            "status_counts": status_counts,
            "statistics": self._stats
        }
    
    def get_all_items(
        self,
        status_filter: Optional[QueueStatus] = None
    ) -> List[QueueItem]:
        """Get all queue items with optional status filter"""
        if status_filter:
            return [item for item in self._queue if item.status == status_filter]
        return self._queue.copy()
    
    async def clear_completed(self):
        """Remove completed items from queue"""
        self._queue = [
            item for item in self._queue
            if item.status not in [QueueStatus.COMPLETED, QueueStatus.CANCELLED]
        ]
        logger.info("Cleared completed items from queue")
    
    async def clear_all(self):
        """Clear entire queue (cancels active uploads)"""
        # Cancel active uploads
        for item_id in list(self._active_uploads.keys()):
            await self.cancel(item_id)
        
        self._queue.clear()
        logger.info("Queue cleared")
