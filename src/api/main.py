"""
FastAPI Web Dashboard Backend

REST API for controlling and monitoring the scheduler system:
- Job management (create, list, cancel, pause, resume)
- Calendar views and planning
- Analytics and statistics
- Real-time updates via WebSocket
- Recurring schedule management
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from pydantic import BaseModel, Field
import asyncio
import logging
import os

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import security middleware
from src.api.middleware.security import SecurityHeadersMiddleware
from src.api.middleware.logging import RequestLoggingMiddleware

# Import logging configuration
from src.utils.logging_config import setup_logging

# Import Prometheus metrics
try:
    from prometheus_fastapi_instrumentator import Instrumentator
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logging.warning("prometheus-fastapi-instrumentator not installed")

from src.api.auth import (
    Token,
    create_access_token,
    get_current_user,
    authenticate_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

from services.scheduler import (
    ContentScheduler,
    ScheduleConfig,
    ScheduledJob,
    JobStatus,
    RecurringScheduler,
    RecurringConfig,
    RecurringJob,
    RecurringPattern,
    DayOfWeek,
    CalendarManager,
    CalendarConfig,
    CalendarEntry,
    ContentSlot
)

logger = logging.getLogger(__name__)

# Setup structured logging at module load
setup_logging(
    level=os.getenv("LOG_LEVEL", "INFO"),
    log_file="logs/app.log",
    json_logs=os.getenv("JSON_LOGS", "true").lower() == "true"
)

# ===================================================================
# FastAPI App
# ===================================================================

app = FastAPI(
    title="Faceless YouTube Dashboard API",
    description="REST API for automated video creation and scheduling",
    version="2.0.0"
)

# ===================================================================
# MIDDLEWARE (Order matters! Applied in reverse order)
# ===================================================================

# 1. Trusted Host Protection
allowed_hosts = os.getenv(
    "ALLOWED_HOSTS",
    "localhost,127.0.0.1,*.localhost"
).split(",")

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=allowed_hosts
)

# 2. CORS (Restrict origins in production)
cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    max_age=3600,
)

# 3. Security Headers
app.add_middleware(SecurityHeadersMiddleware)

# 4. Request Logging
app.add_middleware(RequestLoggingMiddleware)

# Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ===================================================================
# Global State
# ===================================================================

# Scheduler instances (initialized on startup)
content_scheduler: Optional[ContentScheduler] = None
recurring_scheduler: Optional[RecurringScheduler] = None
calendar_manager: Optional[CalendarManager] = None

# WebSocket connections for real-time updates
active_websockets: List[WebSocket] = []

# ===================================================================
# Request/Response Models
# ===================================================================

class ScheduleVideoRequest(BaseModel):
    """Request to schedule video"""
    topic: str
    scheduled_at: datetime
    publish_at: Optional[datetime] = None
    style: str = "educational"
    duration_minutes: int = 5
    tags: List[str] = Field(default_factory=list)


class JobResponse(BaseModel):
    """Job status response"""
    id: str
    topic: str
    status: str
    progress_percent: float
    current_stage: Optional[str]
    scheduled_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    script_path: Optional[str]
    video_path: Optional[str]
    youtube_url: Optional[str]
    error_message: Optional[str]
    retry_count: int
    
    class Config:
        from_attributes = True


class CreateRecurringRequest(BaseModel):
    """Request to create recurring schedule"""
    name: str
    pattern: str  # daily, weekly, monthly
    topic_template: str
    hour: int = 10
    minute: int = 0
    days_of_week: Optional[List[str]] = None  # For weekly
    days_of_month: Optional[List[int]] = None  # For monthly
    style: str = "educational"
    duration_minutes: int = 5
    tags: List[str] = Field(default_factory=list)


class RecurringJobResponse(BaseModel):
    """Recurring job response"""
    id: str
    name: str
    pattern: str
    topic_template: str
    enabled: bool
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    run_count: int
    failure_count: int


class CalendarSlotRequest(BaseModel):
    """Request to reserve calendar slot"""
    scheduled_at: datetime
    topic: str
    duration_minutes: int = 5
    style: str = "educational"
    tags: List[str] = Field(default_factory=list)


class StatisticsResponse(BaseModel):
    """System statistics"""
    total_jobs: int
    active_jobs: int
    completed_jobs: int
    failed_jobs: int
    recurring_schedules: int
    calendar_slots: int


# ===================================================================
# Startup/Shutdown
# ===================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize schedulers and monitoring on startup"""
    global content_scheduler, recurring_scheduler, calendar_manager
    
    logger.info(
        "Starting Faceless YouTube API",
        extra={
            "version": "2.0.0",
            "event": "startup",
            "log_level": os.getenv("LOG_LEVEL", "INFO")
        }
    )
    
    # Initialize Prometheus metrics
    if PROMETHEUS_AVAILABLE:
        Instrumentator().instrument(app).expose(app)
        logger.info("Prometheus metrics enabled at /metrics")
    
    logger.info("Initializing schedulers...")
    
    # Initialize content scheduler
    config = ScheduleConfig(
        jobs_storage_path="scheduled_jobs",
        output_dir="output_videos",
        max_retries=3,
        check_interval_seconds=10
    )
    content_scheduler = ContentScheduler(config=config)
    
    # Load existing jobs
    await content_scheduler.load_jobs()
    
    # Start scheduler
    await content_scheduler.start()
    
    # Initialize recurring scheduler
    recurring_scheduler = RecurringScheduler(
        content_scheduler=content_scheduler,
        config=RecurringConfig()
    )
    await recurring_scheduler.start()
    
    # Initialize calendar manager
    calendar_manager = CalendarManager(config=CalendarConfig())
    
    logger.info("Schedulers initialized and running")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global content_scheduler, recurring_scheduler
    
    logger.info("Shutting down schedulers...")
    
    if content_scheduler:
        await content_scheduler.stop()
    
    if recurring_scheduler:
        await recurring_scheduler.stop()
    
    logger.info("Schedulers stopped")


# ===================================================================
# Health Check
# ===================================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "schedulers": {
            "content_scheduler": content_scheduler is not None,
            "recurring_scheduler": recurring_scheduler is not None,
            "calendar_manager": calendar_manager is not None
        }
    }


# ===================================================================
# Authentication
# ===================================================================

@app.post("/api/auth/login", response_model=Token)
@limiter.limit("5/minute")  # Prevent brute force attacks
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """
    Login endpoint to obtain JWT access token.
    
    **Rate Limited:** 5 requests per minute per IP to prevent brute force.
    
    **Demo Credentials:**
    - Username: admin
    - Password: admin
    
    **IMPORTANT:** Change credentials in production!
    
    Args:
        username: User's username
        password: User's password
        
    Returns:
        JWT access token
        
    Raises:
        HTTP 401: If credentials are invalid
        HTTP 429: If rate limit exceeded
    """
    # Authenticate user
    is_valid = await authenticate_user(username, password)
    
    if not is_valid:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


# ===================================================================
# Job Management Endpoints
# ===================================================================

@app.post("/api/jobs/schedule", response_model=Dict[str, str])
@limiter.limit("10/minute")  # Prevent abuse
async def schedule_video(
    request: Request,
    job_request: ScheduleVideoRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Schedule single video (PROTECTED - Requires Authentication).
    
    **Authentication Required:** Include JWT token in Authorization header:
    ```
    Authorization: Bearer <your_jwt_token>
    ```
    
    **Rate Limited:** 10 video schedules per minute
    """
    if not content_scheduler:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    try:
        job_id = await content_scheduler.schedule_video(
            topic=job_request.topic,
            scheduled_at=job_request.scheduled_at,
            publish_at=job_request.publish_at,
            style=job_request.style,
            duration_minutes=job_request.duration_minutes,
            tags=job_request.tags
        )
        
        # Notify WebSocket clients
        await broadcast_update({
            "type": "job_created",
            "job_id": job_id,
            "topic": request.topic
        })
        
        return {"job_id": job_id, "status": "scheduled"}
    
    except Exception as e:
        logger.error(f"Failed to schedule video: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs", response_model=List[JobResponse])
async def list_jobs(status: Optional[str] = None):
    """List all jobs with optional status filter"""
    if not content_scheduler:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    try:
        status_filter = JobStatus(status) if status else None
        jobs = content_scheduler.get_all_jobs(status_filter=status_filter)
        
        return [
            JobResponse(
                id=job.id,
                topic=job.topic,
                status=job.status.value,
                progress_percent=job.progress_percent,
                current_stage=job.current_stage.value if job.current_stage else None,
                scheduled_at=job.scheduled_at,
                started_at=job.started_at,
                completed_at=job.completed_at,
                script_path=job.script_path,
                video_path=job.video_path,
                youtube_url=job.youtube_url,
                error_message=job.error_message,
                retry_count=job.retry_count
            )
            for job in jobs
        ]
    
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    """Get single job details"""
    if not content_scheduler:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    job = await content_scheduler.get_job_status(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobResponse(
        id=job.id,
        topic=job.topic,
        status=job.status.value,
        progress_percent=job.progress_percent,
        current_stage=job.current_stage.value if job.current_stage else None,
        scheduled_at=job.scheduled_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        script_path=job.script_path,
        video_path=job.video_path,
        youtube_url=job.youtube_url,
        error_message=job.error_message,
        retry_count=job.retry_count
    )


@app.post("/api/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancel job"""
    if not content_scheduler:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    try:
        await content_scheduler.cancel_job(job_id)
        
        await broadcast_update({
            "type": "job_cancelled",
            "job_id": job_id
        })
        
        return {"status": "cancelled"}
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to cancel job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/jobs/{job_id}/pause")
async def pause_job(job_id: str):
    """Pause job"""
    if not content_scheduler:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    try:
        await content_scheduler.pause_job(job_id)
        
        await broadcast_update({
            "type": "job_paused",
            "job_id": job_id
        })
        
        return {"status": "paused"}
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to pause job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/jobs/{job_id}/resume")
async def resume_job(job_id: str):
    """Resume paused job"""
    if not content_scheduler:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    try:
        await content_scheduler.resume_job(job_id)
        
        await broadcast_update({
            "type": "job_resumed",
            "job_id": job_id
        })
        
        return {"status": "resumed"}
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to resume job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ===================================================================
# Recurring Schedule Endpoints
# ===================================================================

@app.post("/api/recurring/create", response_model=Dict[str, str])
async def create_recurring_schedule(request: CreateRecurringRequest):
    """Create recurring schedule"""
    if not recurring_scheduler:
        raise HTTPException(status_code=500, detail="Recurring scheduler not initialized")
    
    try:
        # Determine schedule type and create
        if request.pattern == "daily":
            job_id = await recurring_scheduler.create_daily_schedule(
                name=request.name,
                topic_template=request.topic_template,
                hour=request.hour,
                minute=request.minute,
                style=request.style,
                duration_minutes=request.duration_minutes,
                tags=request.tags
            )
        
        elif request.pattern == "weekly":
            if not request.days_of_week:
                raise HTTPException(status_code=400, detail="days_of_week required for weekly pattern")
            
            days = [DayOfWeek(d) for d in request.days_of_week]
            
            job_id = await recurring_scheduler.create_weekly_schedule(
                name=request.name,
                topic_template=request.topic_template,
                days=days,
                hour=request.hour,
                minute=request.minute,
                style=request.style,
                duration_minutes=request.duration_minutes,
                tags=request.tags
            )
        
        elif request.pattern == "monthly":
            if not request.days_of_month:
                raise HTTPException(status_code=400, detail="days_of_month required for monthly pattern")
            
            job_id = await recurring_scheduler.create_monthly_schedule(
                name=request.name,
                topic_template=request.topic_template,
                days_of_month=request.days_of_month,
                hour=request.hour,
                minute=request.minute,
                style=request.style,
                duration_minutes=request.duration_minutes,
                tags=request.tags
            )
        
        else:
            raise HTTPException(status_code=400, detail=f"Invalid pattern: {request.pattern}")
        
        return {"job_id": job_id, "status": "created"}
    
    except Exception as e:
        logger.error(f"Failed to create recurring schedule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/recurring", response_model=List[RecurringJobResponse])
async def list_recurring_schedules():
    """List all recurring schedules"""
    if not recurring_scheduler:
        raise HTTPException(status_code=500, detail="Recurring scheduler not initialized")
    
    jobs = recurring_scheduler.get_all_jobs()
    
    return [
        RecurringJobResponse(
            id=job.id,
            name=job.name,
            pattern=job.schedule_rule.pattern.value,
            topic_template=job.topic_template,
            enabled=job.enabled,
            last_run=job.last_run,
            next_run=job.next_run,
            run_count=job.run_count,
            failure_count=job.failure_count
        )
        for job in jobs
    ]


@app.post("/api/recurring/{job_id}/pause")
async def pause_recurring_schedule(job_id: str):
    """Pause recurring schedule"""
    if not recurring_scheduler:
        raise HTTPException(status_code=500, detail="Recurring scheduler not initialized")
    
    try:
        await recurring_scheduler.pause_job(job_id)
        return {"status": "paused"}
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/recurring/{job_id}/resume")
async def resume_recurring_schedule(job_id: str):
    """Resume recurring schedule"""
    if not recurring_scheduler:
        raise HTTPException(status_code=500, detail="Recurring scheduler not initialized")
    
    try:
        await recurring_scheduler.resume_job(job_id)
        return {"status": "resumed"}
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/api/recurring/{job_id}")
async def delete_recurring_schedule(job_id: str):
    """Delete recurring schedule"""
    if not recurring_scheduler:
        raise HTTPException(status_code=500, detail="Recurring scheduler not initialized")
    
    try:
        await recurring_scheduler.delete_job(job_id)
        return {"status": "deleted"}
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ===================================================================
# Calendar Endpoints
# ===================================================================

@app.post("/api/calendar/slots", response_model=Dict[str, str])
async def reserve_calendar_slot(request: CalendarSlotRequest):
    """Reserve calendar slot"""
    if not calendar_manager:
        raise HTTPException(status_code=500, detail="Calendar manager not initialized")
    
    try:
        slot = await calendar_manager.reserve_slot(
            scheduled_at=request.scheduled_at,
            topic=request.topic,
            duration_minutes=request.duration_minutes,
            style=request.style,
            tags=request.tags
        )
        
        return {"slot_id": slot.id, "status": slot.status.value}
    
    except Exception as e:
        logger.error(f"Failed to reserve slot: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/calendar/day/{date_str}")
async def get_calendar_day(date_str: str):
    """Get calendar for specific day"""
    if not calendar_manager:
        raise HTTPException(status_code=500, detail="Calendar manager not initialized")
    
    try:
        target_date = date.fromisoformat(date_str)
        entry = await calendar_manager.get_day_view(target_date)
        
        return {
            "date": entry.date.isoformat(),
            "total_slots": entry.total_slots,
            "available_slots": entry.available_slots,
            "scheduled_slots": entry.scheduled_slots,
            "slots": [
                {
                    "id": slot.id,
                    "scheduled_at": slot.scheduled_at.isoformat(),
                    "topic": slot.topic,
                    "status": slot.status.value,
                    "duration_minutes": slot.duration_minutes
                }
                for slot in entry.slots
            ]
        }
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format (use YYYY-MM-DD)")
    except Exception as e:
        logger.error(f"Failed to get day view: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/calendar/week/{date_str}")
async def get_calendar_week(date_str: str):
    """Get calendar for week starting on date"""
    if not calendar_manager:
        raise HTTPException(status_code=500, detail="Calendar manager not initialized")
    
    try:
        start_date = date.fromisoformat(date_str)
        week_view = await calendar_manager.get_week_view(start_date)
        
        return [
            {
                "date": entry.date.isoformat(),
                "total_slots": entry.total_slots,
                "scheduled_slots": entry.scheduled_slots,
                "slots": [
                    {
                        "id": slot.id,
                        "scheduled_at": slot.scheduled_at.isoformat(),
                        "topic": slot.topic,
                        "status": slot.status.value
                    }
                    for slot in entry.slots
                ]
            }
            for entry in week_view
        ]
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    except Exception as e:
        logger.error(f"Failed to get week view: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/calendar/suggestions")
async def get_slot_suggestions(count: int = 5, days: int = 30):
    """Get optimal slot suggestions"""
    if not calendar_manager:
        raise HTTPException(status_code=500, detail="Calendar manager not initialized")
    
    try:
        suggestions = await calendar_manager.suggest_optimal_slots(
            count=count,
            start_date=date.today(),
            days=days
        )
        
        return {
            "suggestions": [dt.isoformat() for dt in suggestions]
        }
    
    except Exception as e:
        logger.error(f"Failed to get suggestions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/calendar/conflicts")
async def get_calendar_conflicts():
    """Get all calendar conflicts"""
    if not calendar_manager:
        raise HTTPException(status_code=500, detail="Calendar manager not initialized")
    
    try:
        conflicts = await calendar_manager.detect_conflicts()
        return {"conflicts": conflicts}
    
    except Exception as e:
        logger.error(f"Failed to detect conflicts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ===================================================================
# Statistics Endpoints
# ===================================================================

@app.get("/api/statistics", response_model=StatisticsResponse)
async def get_statistics():
    """Get system statistics"""
    if not content_scheduler or not recurring_scheduler or not calendar_manager:
        raise HTTPException(status_code=500, detail="Schedulers not initialized")
    
    content_stats = content_scheduler.get_statistics()
    recurring_stats = recurring_scheduler.get_statistics()
    calendar_stats = calendar_manager.get_statistics()
    
    return StatisticsResponse(
        total_jobs=content_stats["total_jobs"],
        active_jobs=content_stats["active_jobs"],
        completed_jobs=content_stats["statistics"]["total_completed"],
        failed_jobs=content_stats["statistics"]["total_failed"],
        recurring_schedules=recurring_stats["total_jobs"],
        calendar_slots=calendar_stats["total_slots"]
    )


# ===================================================================
# WebSocket for Real-time Updates
# ===================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    active_websockets.append(websocket)
    
    try:
        # Send initial status
        stats = get_statistics() if all([content_scheduler, recurring_scheduler, calendar_manager]) else None
        if stats:
            await websocket.send_json({
                "type": "initial_stats",
                "data": stats.dict()
            })
        
        # Keep connection alive and listen for client messages
        while True:
            data = await websocket.receive_text()
            
            # Handle client requests (e.g., subscribe to specific job updates)
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        active_websockets.remove(websocket)
        logger.info("WebSocket disconnected")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        active_websockets.remove(websocket)


async def broadcast_update(message: Dict[str, Any]):
    """Broadcast update to all connected WebSocket clients"""
    if not active_websockets:
        return
    
    disconnected = []
    
    for websocket in active_websockets:
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
            disconnected.append(websocket)
    
    # Remove disconnected clients
    for websocket in disconnected:
        active_websockets.remove(websocket)


# ===================================================================
# Background Task for Job Monitoring
# ===================================================================

async def monitor_jobs():
    """Background task to monitor jobs and send updates"""
    while True:
        await asyncio.sleep(5)
        
        if not content_scheduler:
            continue
        
        # Get active jobs
        jobs = content_scheduler.get_all_jobs()
        active_jobs = [j for j in jobs if j.status not in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]]
        
        if active_jobs:
            # Broadcast status updates
            for job in active_jobs:
                await broadcast_update({
                    "type": "job_update",
                    "job_id": job.id,
                    "status": job.status.value,
                    "progress": job.progress_percent,
                    "stage": job.current_stage.value if job.current_stage else None
                })


@app.on_event("startup")
async def start_monitoring():
    """Start background monitoring task"""
    asyncio.create_task(monitor_jobs())


# ===================================================================
# Main Entry Point
# ===================================================================

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Default to localhost for security, allow override via environment
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8000"))
    workers = int(os.getenv("API_WORKERS", "1"))
    
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=os.getenv("DEBUG", "false").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info"),
        workers=workers if workers > 1 else None
    )
