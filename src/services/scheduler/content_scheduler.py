"""
Content Scheduler

Orchestrates complete content creation and publishing workflow:
1. Generate script (Task #6)
2. Assemble video (Task #7)
3. Upload to YouTube (Task #8)
4. Track analytics

Handles scheduling, retry logic, and status tracking.
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

from services.script_generator import ScriptGenerator, GenerationConfig
from services.video_assembler import VideoAssembler, VideoConfig as AssemblerConfig
from services.youtube_uploader import (
    AuthManager,
    VideoUploader,
    VideoMetadata,
    PrivacyStatus,
    Category
)

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job execution status"""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    GENERATING_SCRIPT = "generating_script"
    ASSEMBLING_VIDEO = "assembling_video"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class JobType(str, Enum):
    """Job type"""
    SINGLE_VIDEO = "single_video"
    RECURRING = "recurring"
    BATCH = "batch"
    MANUAL = "manual"


class WorkflowStage(str, Enum):
    """Workflow execution stages"""
    SCRIPT_GENERATION = "script_generation"
    ASSET_SELECTION = "asset_selection"
    VIDEO_ASSEMBLY = "video_assembly"
    THUMBNAIL_CREATION = "thumbnail_creation"
    METADATA_PREPARATION = "metadata_preparation"
    YOUTUBE_UPLOAD = "youtube_upload"
    ANALYTICS_TRACKING = "analytics_tracking"


@dataclass
class ScheduleConfig:
    """Scheduler configuration"""
    # Storage
    jobs_storage_path: str = "scheduled_jobs"
    output_dir: str = "output_videos"
    assets_dir: str = "assets"
    
    # Retry settings
    max_retries: int = 3
    retry_delay_minutes: int = 10
    
    # Execution settings
    max_concurrent_jobs: int = 1  # Videos are heavy, process one at a time
    check_interval_seconds: int = 60
    
    # YouTube settings
    youtube_account: str = "main"
    default_privacy: PrivacyStatus = PrivacyStatus.PRIVATE
    default_category: Category = Category.EDUCATION
    
    # Content settings
    default_video_duration: int = 5  # minutes
    default_quality: str = "HD_1080P"
    
    # Notifications
    enable_notifications: bool = True
    notification_email: Optional[str] = None


class ScheduledJob(BaseModel):
    """Scheduled job model"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    job_type: JobType
    status: JobStatus = JobStatus.PENDING
    
    # Content details
    topic: str
    style: str = "educational"
    duration_minutes: int = 5
    
    # Scheduling
    scheduled_at: datetime
    publish_at: Optional[datetime] = None  # When to publish on YouTube
    
    # Execution tracking
    current_stage: Optional[WorkflowStage] = None
    retry_count: int = 0
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    category: Category = Category.EDUCATION
    privacy_status: PrivacyStatus = PrivacyStatus.PRIVATE
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results
    script_path: Optional[str] = None
    video_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    youtube_video_id: Optional[str] = None
    youtube_url: Optional[str] = None
    
    # Error tracking
    error_message: Optional[str] = None
    error_stage: Optional[WorkflowStage] = None
    
    # Progress
    progress_percent: float = 0.0
    stage_progress: Dict[str, float] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True


class ContentScheduler:
    """
    Content creation scheduler
    
    Orchestrates complete workflow:
    1. Script generation (AI)
    2. Video assembly (TTS, timeline, rendering)
    3. YouTube upload (with metadata)
    4. Analytics tracking
    
    Features:
    - Automatic workflow execution
    - Retry logic with exponential backoff
    - Progress tracking
    - Error handling and recovery
    - Concurrent job management
    - Job cancellation
    - Status monitoring
    
    Example:
        scheduler = ContentScheduler(config=ScheduleConfig())
        
        # Schedule video for tomorrow at 10 AM
        job_id = await scheduler.schedule_video(
            topic="Python Functions Tutorial",
            scheduled_at=tomorrow_10am,
            publish_at=tomorrow_12pm,  # Publish 2 hours after creation
            style="educational",
            tags=["python", "tutorial", "programming"]
        )
        
        # Start scheduler
        await scheduler.start()
        
        # Monitor job
        status = await scheduler.get_job_status(job_id)
        print(f"Progress: {status.progress_percent}%")
    """
    
    def __init__(
        self,
        config: ScheduleConfig,
        script_generator: Optional[ScriptGenerator] = None,
        video_assembler: Optional[VideoAssembler] = None,
        youtube_auth: Optional[AuthManager] = None,
        youtube_uploader: Optional[VideoUploader] = None
    ):
        self.config = config
        
        # Initialize components
        self.script_generator = script_generator or ScriptGenerator()
        self.video_assembler = video_assembler or VideoAssembler(
            AssemblerConfig(quality=config.default_quality)
        )
        self.youtube_auth = youtube_auth
        self.youtube_uploader = youtube_uploader or (
            VideoUploader(youtube_auth) if youtube_auth else None
        )
        
        # Job management
        self._jobs: Dict[str, ScheduledJob] = {}
        self._active_jobs: Dict[str, asyncio.Task] = {}
        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None
        
        # Storage
        self._storage_path = Path(config.jobs_storage_path)
        self._storage_path.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self._stats = {
            "total_scheduled": 0,
            "total_completed": 0,
            "total_failed": 0,
            "total_cancelled": 0
        }
    
    async def schedule_video(
        self,
        topic: str,
        scheduled_at: datetime,
        publish_at: Optional[datetime] = None,
        style: str = "educational",
        duration_minutes: int = 5,
        tags: Optional[List[str]] = None,
        category: Category = Category.EDUCATION,
        privacy_status: PrivacyStatus = PrivacyStatus.PRIVATE
    ) -> str:
        """
        Schedule video creation and upload
        
        Args:
            topic: Video topic
            scheduled_at: When to create the video
            publish_at: When to publish on YouTube (None = publish immediately)
            style: Content style
            duration_minutes: Target duration
            tags: Video tags
            category: YouTube category
            privacy_status: Privacy setting
        
        Returns:
            Job ID
        """
        job = ScheduledJob(
            job_type=JobType.SINGLE_VIDEO,
            topic=topic,
            style=style,
            duration_minutes=duration_minutes,
            scheduled_at=scheduled_at,
            publish_at=publish_at,
            tags=tags or [],
            category=category,
            privacy_status=privacy_status
        )
        
        self._jobs[job.id] = job
        self._stats["total_scheduled"] += 1
        
        logger.info(f"Scheduled video: {job.id} - {topic} at {scheduled_at}")
        
        # Save to storage
        await self._save_job(job)
        
        return job.id
    
    async def schedule_batch(
        self,
        videos: List[Dict[str, Any]]
    ) -> List[str]:
        """Schedule multiple videos"""
        job_ids = []
        
        for video_data in videos:
            job_id = await self.schedule_video(**video_data)
            job_ids.append(job_id)
        
        logger.info(f"Scheduled {len(job_ids)} videos")
        return job_ids
    
    async def start(self):
        """Start scheduler"""
        if self._running:
            logger.warning("Scheduler already running")
            return
        
        self._running = True
        self._scheduler_task = asyncio.create_task(self._run_scheduler())
        logger.info("Scheduler started")
    
    async def stop(self):
        """Stop scheduler"""
        if not self._running:
            return
        
        self._running = False
        
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Scheduler stopped")
    
    async def _run_scheduler(self):
        """Main scheduler loop"""
        while self._running:
            try:
                # Check for due jobs
                now = datetime.utcnow()
                
                for job in list(self._jobs.values()):
                    if job.status == JobStatus.PENDING and job.scheduled_at <= now:
                        # Check concurrent limit
                        if len(self._active_jobs) < self.config.max_concurrent_jobs:
                            await self._start_job(job)
                
                # Clean up completed tasks
                completed = [
                    job_id for job_id, task in self._active_jobs.items()
                    if task.done()
                ]
                
                for job_id in completed:
                    del self._active_jobs[job_id]
                
                # Wait before next check
                await asyncio.sleep(self.config.check_interval_seconds)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(self.config.check_interval_seconds)
    
    async def _start_job(self, job: ScheduledJob):
        """Start job execution"""
        job.status = JobStatus.SCHEDULED
        job.started_at = datetime.utcnow()
        
        logger.info(f"Starting job: {job.id} - {job.topic}")
        
        # Create task
        task = asyncio.create_task(self._execute_job(job))
        self._active_jobs[job.id] = task
        
        await self._save_job(job)
    
    async def _execute_job(self, job: ScheduledJob):
        """Execute complete workflow"""
        try:
            # Stage 1: Generate Script
            job.status = JobStatus.GENERATING_SCRIPT
            job.current_stage = WorkflowStage.SCRIPT_GENERATION
            job.progress_percent = 10
            await self._save_job(job)
            
            logger.info(f"[{job.id}] Generating script...")
            
            script = await self.script_generator.generate(
                topic=job.topic,
                style=job.style,
                duration_minutes=job.duration_minutes
            )
            
            # Save script
            script_path = self._storage_path / f"{job.id}_script.txt"
            script_path.write_text(script.content)
            job.script_path = str(script_path)
            job.stage_progress[WorkflowStage.SCRIPT_GENERATION.value] = 100
            job.progress_percent = 30
            await self._save_job(job)
            
            logger.info(f"[{job.id}] Script generated: {len(script.content)} chars")
            
            # Stage 2: Assemble Video
            job.status = JobStatus.ASSEMBLING_VIDEO
            job.current_stage = WorkflowStage.VIDEO_ASSEMBLY
            job.progress_percent = 40
            await self._save_job(job)
            
            logger.info(f"[{job.id}] Assembling video...")
            
            video_result = await self.video_assembler.assemble(
                script_text=script.content,
                assets_dir=self.config.assets_dir,
                output_dir=self.config.output_dir
            )
            
            job.video_path = video_result.output_path
            job.thumbnail_path = video_result.thumbnail_path
            job.stage_progress[WorkflowStage.VIDEO_ASSEMBLY.value] = 100
            job.progress_percent = 70
            await self._save_job(job)
            
            logger.info(f"[{job.id}] Video assembled: {video_result.output_path}")
            
            # Stage 3: Upload to YouTube (if configured)
            if self.youtube_uploader:
                job.status = JobStatus.UPLOADING
                job.current_stage = WorkflowStage.YOUTUBE_UPLOAD
                job.progress_percent = 80
                await self._save_job(job)
                
                logger.info(f"[{job.id}] Uploading to YouTube...")
                
                # Prepare metadata
                metadata = VideoMetadata(
                    title=script.title,
                    description=script.description,
                    tags=job.tags or script.tags,
                    category=job.category,
                    privacy_status=job.privacy_status,
                    publish_at=job.publish_at
                )
                
                # Upload
                upload_result = await self.youtube_uploader.upload(
                    account_name=self.config.youtube_account,
                    video_path=job.video_path,
                    metadata=metadata,
                    thumbnail_path=job.thumbnail_path
                )
                
                job.youtube_video_id = upload_result.video_id
                job.youtube_url = upload_result.url
                job.stage_progress[WorkflowStage.YOUTUBE_UPLOAD.value] = 100
                job.progress_percent = 95
                await self._save_job(job)
                
                logger.info(f"[{job.id}] Uploaded: {upload_result.url}")
            
            # Complete
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.progress_percent = 100
            self._stats["total_completed"] += 1
            await self._save_job(job)
            
            logger.info(f"[{job.id}] Completed successfully!")
        
        except Exception as e:
            logger.error(f"[{job.id}] Job failed: {e}", exc_info=True)
            
            job.retry_count += 1
            job.error_message = str(e)
            job.error_stage = job.current_stage
            
            # Retry logic
            if job.retry_count < self.config.max_retries:
                logger.info(f"[{job.id}] Scheduling retry {job.retry_count}/{self.config.max_retries}")
                
                # Schedule retry
                job.status = JobStatus.PENDING
                job.scheduled_at = datetime.utcnow() + timedelta(
                    minutes=self.config.retry_delay_minutes * job.retry_count
                )
                await self._save_job(job)
            else:
                # Max retries reached
                job.status = JobStatus.FAILED
                job.completed_at = datetime.utcnow()
                self._stats["total_failed"] += 1
                await self._save_job(job)
                
                logger.error(f"[{job.id}] Failed permanently after {job.retry_count} retries")
    
    async def get_job_status(self, job_id: str) -> Optional[ScheduledJob]:
        """Get job status"""
        return self._jobs.get(job_id)
    
    async def cancel_job(self, job_id: str):
        """Cancel job"""
        job = self._jobs.get(job_id)
        
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        # Cancel active task
        if job_id in self._active_jobs:
            self._active_jobs[job_id].cancel()
            del self._active_jobs[job_id]
        
        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.utcnow()
        self._stats["total_cancelled"] += 1
        await self._save_job(job)
        
        logger.info(f"Job cancelled: {job_id}")
    
    async def pause_job(self, job_id: str):
        """Pause job (only pending jobs)"""
        job = self._jobs.get(job_id)
        
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        if job.status != JobStatus.PENDING:
            raise ValueError(f"Can only pause pending jobs, current: {job.status}")
        
        job.status = JobStatus.PAUSED
        await self._save_job(job)
        
        logger.info(f"Job paused: {job_id}")
    
    async def resume_job(self, job_id: str):
        """Resume paused job"""
        job = self._jobs.get(job_id)
        
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        if job.status != JobStatus.PAUSED:
            raise ValueError(f"Can only resume paused jobs, current: {job.status}")
        
        job.status = JobStatus.PENDING
        await self._save_job(job)
        
        logger.info(f"Job resumed: {job_id}")
    
    def get_all_jobs(
        self,
        status_filter: Optional[JobStatus] = None
    ) -> List[ScheduledJob]:
        """Get all jobs with optional filter"""
        jobs = list(self._jobs.values())
        
        if status_filter:
            jobs = [j for j in jobs if j.status == status_filter]
        
        return sorted(jobs, key=lambda j: j.scheduled_at)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        status_counts = {}
        for status in JobStatus:
            status_counts[status.value] = sum(
                1 for job in self._jobs.values()
                if job.status == status
            )
        
        return {
            "total_jobs": len(self._jobs),
            "active_jobs": len(self._active_jobs),
            "status_counts": status_counts,
            "statistics": self._stats,
            "running": self._running
        }
    
    async def _save_job(self, job: ScheduledJob):
        """Save job to storage"""
        job_file = self._storage_path / f"{job.id}.json"
        
        with open(job_file, "w") as f:
            f.write(job.json(indent=2))
    
    async def load_jobs(self):
        """Load jobs from storage"""
        for job_file in self._storage_path.glob("*.json"):
            if job_file.stem.endswith("_script"):
                continue
            
            try:
                with open(job_file) as f:
                    job = ScheduledJob.parse_raw(f.read())
                    self._jobs[job.id] = job
                    
                    logger.info(f"Loaded job: {job.id} - {job.status}")
            except Exception as e:
                logger.error(f"Failed to load job {job_file}: {e}")
    
    async def clean_old_jobs(self, days: int = 30):
        """Remove completed/failed jobs older than specified days"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        removed = 0
        for job in list(self._jobs.values()):
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                if job.completed_at and job.completed_at < cutoff:
                    # Remove from memory
                    del self._jobs[job.id]
                    
                    # Remove from storage
                    job_file = self._storage_path / f"{job.id}.json"
                    if job_file.exists():
                        job_file.unlink()
                    
                    removed += 1
        
        logger.info(f"Cleaned {removed} old jobs")
        return removed
