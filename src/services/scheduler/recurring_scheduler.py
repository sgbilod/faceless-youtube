"""
Recurring Scheduler

Pattern-based scheduling for recurring video creation:
- Daily schedules (every day at specific time)
- Weekly schedules (specific days of week)
- Monthly schedules (specific days of month)
- Custom cron expressions
- APScheduler integration
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, time
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.job import Job

logger = logging.getLogger(__name__)


class RecurringPattern(str, Enum):
    """Recurring pattern types"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    INTERVAL = "interval"
    CRON = "cron"


class DayOfWeek(str, Enum):
    """Days of week"""
    MONDAY = "mon"
    TUESDAY = "tue"
    WEDNESDAY = "wed"
    THURSDAY = "thu"
    FRIDAY = "fri"
    SATURDAY = "sat"
    SUNDAY = "sun"


@dataclass
class RecurringConfig:
    """Recurring scheduler configuration"""
    timezone: str = "UTC"
    coalesce: bool = True  # Combine missed runs
    max_instances: int = 3  # Max concurrent instances
    misfire_grace_time: int = 3600  # 1 hour grace for missed jobs


class ScheduleRule(BaseModel):
    """Schedule rule definition"""
    pattern: RecurringPattern
    
    # Time settings
    hour: int = 10  # Default 10 AM
    minute: int = 0
    
    # Weekly settings
    days_of_week: Optional[List[DayOfWeek]] = None
    
    # Monthly settings
    days_of_month: Optional[List[int]] = None
    
    # Interval settings
    interval_hours: Optional[int] = None
    interval_minutes: Optional[int] = None
    
    # Cron expression
    cron_expression: Optional[str] = None
    
    # Validity
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    class Config:
        arbitrary_types_allowed = True


class RecurringJob(BaseModel):
    """Recurring job definition"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    
    # Content settings
    topic_template: str  # e.g., "Daily Python Tip #{date}"
    style: str = "educational"
    duration_minutes: int = 5
    tags_template: List[str] = Field(default_factory=list)
    
    # Schedule
    schedule_rule: ScheduleRule
    
    # Status
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Execution tracking
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    failure_count: int = 0
    
    # APScheduler job ID
    apscheduler_job_id: Optional[str] = None


class RecurringScheduler:
    """
    Recurring schedule manager
    
    Creates repeating schedules using APScheduler:
    - Daily videos at specific time
    - Weekly videos on specific days
    - Monthly videos on specific dates
    - Custom intervals
    - Cron expressions
    
    Features:
    - Dynamic topic generation using templates
    - Automatic retry on failure
    - Execution tracking
    - Enable/disable schedules
    - Next run prediction
    
    Example:
        # Daily video at 10 AM
        scheduler = RecurringScheduler(content_scheduler)
        
        job = await scheduler.create_daily_schedule(
            name="Daily Python Tips",
            topic_template="Python Tip of the Day - {date}",
            hour=10,
            minute=0,
            tags=["python", "tutorial", "daily"]
        )
        
        # Weekly videos on Mon/Wed/Fri
        job = await scheduler.create_weekly_schedule(
            name="Weekly Python Tutorials",
            topic_template="Python Tutorial - Week {week}",
            days=[DayOfWeek.MONDAY, DayOfWeek.WEDNESDAY, DayOfWeek.FRIDAY],
            hour=14,
            minute=30
        )
        
        await scheduler.start()
    """
    
    def __init__(
        self,
        content_scheduler,  # ContentScheduler instance
        config: Optional[RecurringConfig] = None
    ):
        self.content_scheduler = content_scheduler
        self.config = config or RecurringConfig()
        
        # APScheduler
        self._scheduler = AsyncIOScheduler(
            timezone=self.config.timezone
        )
        
        # Job tracking
        self._jobs: Dict[str, RecurringJob] = {}
        
        # Statistics
        self._stats = {
            "total_jobs": 0,
            "active_jobs": 0,
            "total_runs": 0,
            "total_failures": 0
        }
    
    async def create_daily_schedule(
        self,
        name: str,
        topic_template: str,
        hour: int = 10,
        minute: int = 0,
        style: str = "educational",
        duration_minutes: int = 5,
        tags: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """
        Create daily recurring schedule
        
        Args:
            name: Schedule name
            topic_template: Topic template (use {date}, {time}, etc.)
            hour: Hour (0-23)
            minute: Minute (0-59)
            style: Content style
            duration_minutes: Video duration
            tags: Video tags
            start_date: Start date (None = now)
            end_date: End date (None = forever)
        
        Returns:
            Job ID
        """
        rule = ScheduleRule(
            pattern=RecurringPattern.DAILY,
            hour=hour,
            minute=minute,
            start_date=start_date,
            end_date=end_date
        )
        
        return await self._create_recurring_job(
            name=name,
            topic_template=topic_template,
            schedule_rule=rule,
            style=style,
            duration_minutes=duration_minutes,
            tags=tags or []
        )
    
    async def create_weekly_schedule(
        self,
        name: str,
        topic_template: str,
        days: List[DayOfWeek],
        hour: int = 10,
        minute: int = 0,
        style: str = "educational",
        duration_minutes: int = 5,
        tags: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """Create weekly recurring schedule"""
        rule = ScheduleRule(
            pattern=RecurringPattern.WEEKLY,
            days_of_week=days,
            hour=hour,
            minute=minute,
            start_date=start_date,
            end_date=end_date
        )
        
        return await self._create_recurring_job(
            name=name,
            topic_template=topic_template,
            schedule_rule=rule,
            style=style,
            duration_minutes=duration_minutes,
            tags=tags or []
        )
    
    async def create_monthly_schedule(
        self,
        name: str,
        topic_template: str,
        days_of_month: List[int],
        hour: int = 10,
        minute: int = 0,
        style: str = "educational",
        duration_minutes: int = 5,
        tags: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """Create monthly recurring schedule"""
        rule = ScheduleRule(
            pattern=RecurringPattern.MONTHLY,
            days_of_month=days_of_month,
            hour=hour,
            minute=minute,
            start_date=start_date,
            end_date=end_date
        )
        
        return await self._create_recurring_job(
            name=name,
            topic_template=topic_template,
            schedule_rule=rule,
            style=style,
            duration_minutes=duration_minutes,
            tags=tags or []
        )
    
    async def create_interval_schedule(
        self,
        name: str,
        topic_template: str,
        interval_hours: Optional[int] = None,
        interval_minutes: Optional[int] = None,
        style: str = "educational",
        duration_minutes: int = 5,
        tags: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """Create interval-based schedule (e.g., every 3 hours)"""
        rule = ScheduleRule(
            pattern=RecurringPattern.INTERVAL,
            interval_hours=interval_hours,
            interval_minutes=interval_minutes,
            start_date=start_date,
            end_date=end_date
        )
        
        return await self._create_recurring_job(
            name=name,
            topic_template=topic_template,
            schedule_rule=rule,
            style=style,
            duration_minutes=duration_minutes,
            tags=tags or []
        )
    
    async def create_cron_schedule(
        self,
        name: str,
        topic_template: str,
        cron_expression: str,
        style: str = "educational",
        duration_minutes: int = 5,
        tags: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """
        Create schedule from cron expression
        
        Example expressions:
        - "0 10 * * *" - Daily at 10 AM
        - "0 14 * * 1,3,5" - Mon/Wed/Fri at 2 PM
        - "0 9 1,15 * *" - 1st and 15th at 9 AM
        """
        rule = ScheduleRule(
            pattern=RecurringPattern.CRON,
            cron_expression=cron_expression,
            start_date=start_date,
            end_date=end_date
        )
        
        return await self._create_recurring_job(
            name=name,
            topic_template=topic_template,
            schedule_rule=rule,
            style=style,
            duration_minutes=duration_minutes,
            tags=tags or []
        )
    
    async def _create_recurring_job(
        self,
        name: str,
        topic_template: str,
        schedule_rule: ScheduleRule,
        style: str,
        duration_minutes: int,
        tags: List[str]
    ) -> str:
        """Create recurring job"""
        job = RecurringJob(
            name=name,
            topic_template=topic_template,
            schedule_rule=schedule_rule,
            style=style,
            duration_minutes=duration_minutes,
            tags_template=tags
        )
        
        # Store job
        self._jobs[job.id] = job
        self._stats["total_jobs"] += 1
        
        # Add to APScheduler
        await self._schedule_job(job)
        
        logger.info(f"Created recurring job: {job.id} - {name}")
        
        return job.id
    
    async def _schedule_job(self, job: RecurringJob):
        """Schedule job in APScheduler"""
        rule = job.schedule_rule
        
        # Create trigger based on pattern
        if rule.pattern == RecurringPattern.DAILY:
            trigger = CronTrigger(
                hour=rule.hour,
                minute=rule.minute,
                start_date=rule.start_date,
                end_date=rule.end_date,
                timezone=self.config.timezone
            )
        
        elif rule.pattern == RecurringPattern.WEEKLY:
            trigger = CronTrigger(
                day_of_week=",".join(d.value for d in rule.days_of_week),
                hour=rule.hour,
                minute=rule.minute,
                start_date=rule.start_date,
                end_date=rule.end_date,
                timezone=self.config.timezone
            )
        
        elif rule.pattern == RecurringPattern.MONTHLY:
            trigger = CronTrigger(
                day=",".join(str(d) for d in rule.days_of_month),
                hour=rule.hour,
                minute=rule.minute,
                start_date=rule.start_date,
                end_date=rule.end_date,
                timezone=self.config.timezone
            )
        
        elif rule.pattern == RecurringPattern.INTERVAL:
            trigger = IntervalTrigger(
                hours=rule.interval_hours or 0,
                minutes=rule.interval_minutes or 0,
                start_date=rule.start_date,
                end_date=rule.end_date,
                timezone=self.config.timezone
            )
        
        elif rule.pattern == RecurringPattern.CRON:
            trigger = CronTrigger.from_crontab(
                rule.cron_expression,
                timezone=self.config.timezone
            )
        
        else:
            raise ValueError(f"Unknown pattern: {rule.pattern}")
        
        # Add job to scheduler
        apscheduler_job = self._scheduler.add_job(
            func=self._execute_recurring_job,
            trigger=trigger,
            args=[job.id],
            id=job.id,
            name=job.name,
            coalesce=self.config.coalesce,
            max_instances=self.config.max_instances,
            misfire_grace_time=self.config.misfire_grace_time
        )
        
        job.apscheduler_job_id = apscheduler_job.id
        # Get next_run_time from trigger, not job object
        job.next_run = trigger.get_next_fire_time(None, datetime.now()) if hasattr(trigger, 'get_next_fire_time') else None
        
        if job.enabled:
            self._stats["active_jobs"] += 1
        
        logger.info(f"Scheduled: {job.name} - Next run: {job.next_run}")
    
    async def _execute_recurring_job(self, job_id: str):
        """Execute recurring job"""
        job = self._jobs.get(job_id)
        
        if not job or not job.enabled:
            return
        
        try:
            logger.info(f"Executing recurring job: {job.name}")
            
            # Generate topic from template
            now = datetime.now()
            topic = self._format_topic(job.topic_template, now)
            
            # Schedule video creation
            scheduled_job_id = await self.content_scheduler.schedule_video(
                topic=topic,
                scheduled_at=now,  # Execute immediately
                style=job.style,
                duration_minutes=job.duration_minutes,
                tags=job.tags_template
            )
            
            # Update job
            job.last_run = now
            job.run_count += 1
            self._stats["total_runs"] += 1
            
            # Update next run
            apscheduler_job = self._scheduler.get_job(job.id)
            if apscheduler_job and hasattr(apscheduler_job, 'trigger'):
                # Get next fire time from the trigger
                job.next_run = apscheduler_job.trigger.get_next_fire_time(None, datetime.now()) if hasattr(apscheduler_job.trigger, 'get_next_fire_time') else None
            
            logger.info(
                f"Scheduled video: {scheduled_job_id} for recurring job: {job.name}"
            )
        
        except Exception as e:
            logger.error(f"Recurring job failed: {job.name} - {e}", exc_info=True)
            
            job.failure_count += 1
            self._stats["total_failures"] += 1
    
    def _format_topic(self, template: str, dt: datetime) -> str:
        """Format topic template with date/time variables"""
        replacements = {
            "{date}": dt.strftime("%Y-%m-%d"),
            "{time}": dt.strftime("%H:%M"),
            "{datetime}": dt.strftime("%Y-%m-%d %H:%M"),
            "{year}": str(dt.year),
            "{month}": dt.strftime("%B"),
            "{month_num}": str(dt.month),
            "{day}": str(dt.day),
            "{weekday}": dt.strftime("%A"),
            "{week}": str(dt.isocalendar()[1]),
            "{timestamp}": str(int(dt.timestamp()))
        }
        
        result = template
        for key, value in replacements.items():
            result = result.replace(key, value)
        
        return result
    
    async def start(self):
        """Start scheduler"""
        self._scheduler.start()
        logger.info("Recurring scheduler started")
    
    async def stop(self):
        """Stop scheduler"""
        self._scheduler.shutdown()
        logger.info("Recurring scheduler stopped")
    
    async def pause_job(self, job_id: str):
        """Pause recurring job"""
        job = self._jobs.get(job_id)
        
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        if not job.enabled:
            return
        
        job.enabled = False
        self._scheduler.pause_job(job.id)
        self._stats["active_jobs"] -= 1
        
        logger.info(f"Paused recurring job: {job.name}")
    
    async def resume_job(self, job_id: str):
        """Resume paused job"""
        job = self._jobs.get(job_id)
        
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        if job.enabled:
            return
        
        job.enabled = True
        self._scheduler.resume_job(job.id)
        self._stats["active_jobs"] += 1
        
        # Update next run
        apscheduler_job = self._scheduler.get_job(job.id)
        if apscheduler_job and hasattr(apscheduler_job, 'trigger'):
            # Get next fire time from the trigger
            job.next_run = apscheduler_job.trigger.get_next_fire_time(None, datetime.now()) if hasattr(apscheduler_job.trigger, 'get_next_fire_time') else None
        
        logger.info(f"Resumed recurring job: {job.name} - Next: {job.next_run}")
    
    async def delete_job(self, job_id: str):
        """Delete recurring job"""
        job = self._jobs.get(job_id)
        
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        # Remove from APScheduler
        self._scheduler.remove_job(job.id)
        
        # Remove from tracking
        del self._jobs[job_id]
        
        if job.enabled:
            self._stats["active_jobs"] -= 1
        
        logger.info(f"Deleted recurring job: {job.name}")
    
    def get_job(self, job_id: str) -> Optional[RecurringJob]:
        """Get job by ID"""
        return self._jobs.get(job_id)
    
    def get_all_jobs(self, enabled_only: bool = False) -> List[RecurringJob]:
        """Get all jobs"""
        jobs = list(self._jobs.values())
        
        if enabled_only:
            jobs = [j for j in jobs if j.enabled]
        
        return sorted(jobs, key=lambda j: j.name)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        return {
            "total_jobs": len(self._jobs),
            "enabled_jobs": sum(1 for j in self._jobs.values() if j.enabled),
            "statistics": self._stats,
            "running": self._scheduler.running
        }
