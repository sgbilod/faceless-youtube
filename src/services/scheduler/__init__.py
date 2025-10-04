"""
Content Scheduling System

Automates the entire content creation and publishing pipeline:
- Schedule creation (generate scripts, assemble videos, upload to YouTube)
- Recurring schedules (daily, weekly, monthly patterns)
- Content calendar management
- Job execution with retry and monitoring
- Workflow orchestration
- Performance tracking

Components:
- ContentScheduler: Manages scheduled content creation tasks
- JobExecutor: Executes background jobs with retry logic
- RecurringScheduler: Handles recurring schedule patterns
- CalendarManager: Manages content calendar and planning

Usage:
    from services.scheduler import ContentScheduler, ScheduleConfig
    
    scheduler = ContentScheduler(config=ScheduleConfig())
    
    # Schedule single video
    job_id = await scheduler.schedule_video(
        topic="Python Tutorial",
        publish_at=datetime(2024, 12, 25, 10, 0),
        style="educational"
    )
    
    # Create recurring schedule
    schedule_id = await scheduler.create_recurring(
        pattern="daily",
        time="10:00",
        topics=["Tech News", "Tutorial", "Review"]
    )
"""

from .content_scheduler import (
    ContentScheduler,
    ScheduleConfig,
    ScheduledJob,
    JobStatus,
    JobType,
    WorkflowStage
)

from .job_executor import (
    JobExecutor,
    ExecutorConfig,
    ExecutionResult,
    ExecutionStatus,
    RetryStrategy
)

from .recurring_scheduler import (
    RecurringScheduler,
    RecurringConfig,
    RecurringPattern,
    ScheduleRule,
    RecurringJob,
    DayOfWeek
)

from .calendar_manager import (
    CalendarManager,
    CalendarConfig,
    CalendarEntry,
    CalendarView,
    ContentSlot,
    ContentSlotStatus
)

__all__ = [
    # Content Scheduler
    "ContentScheduler",
    "ScheduleConfig",
    "ScheduledJob",
    "JobStatus",
    "JobType",
    "WorkflowStage",
    
    # Job Executor
    "JobExecutor",
    "ExecutorConfig",
    "ExecutionResult",
    "ExecutionStatus",
    "RetryStrategy",
    
    # Recurring Scheduler
    "RecurringScheduler",
    "RecurringConfig",
    "RecurringPattern",
    "ScheduleRule",
    "RecurringJob",
    "DayOfWeek",
    
    # Calendar Manager
    "CalendarManager",
    "CalendarConfig",
    "CalendarEntry",
    "CalendarView",
    "ContentSlot",
    "ContentSlotStatus",
]

__version__ = "1.0.0"
