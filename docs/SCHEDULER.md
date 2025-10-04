# Scheduler Documentation

## Overview

The Scheduler system automates the complete content creation and publishing workflow for faceless YouTube videos. It orchestrates script generation, video assembly, and YouTube uploads on a flexible schedule.

## Table of Contents

- [Architecture](#architecture)
- [Components](#components)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Scheduling Patterns](#scheduling-patterns)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────┐
│                   Scheduler System                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────┐      ┌────────────────────────┐  │
│  │ RecurringScheduler│────▶│  ContentScheduler     │  │
│  │  (Patterns)      │      │  (Orchestration)      │  │
│  └─────────────────┘      └────────────────────────┘  │
│           │                         │                  │
│           │                         ▼                  │
│           │              ┌────────────────────────┐    │
│           │              │    JobExecutor         │    │
│           │              │  (Background Exec)     │    │
│           │              └────────────────────────┘    │
│           │                         │                  │
│           ▼                         ▼                  │
│  ┌─────────────────┐      ┌────────────────────────┐  │
│  │ CalendarManager │      │  Workflow Pipeline     │  │
│  │  (Planning)     │      │                        │  │
│  └─────────────────┘      │  1. Script Generator   │  │
│                            │  2. Video Assembler    │  │
│                            │  3. YouTube Uploader   │  │
│                            └────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Workflow Stages

1. **Script Generation** - AI generates video script
2. **Asset Selection** - Select background videos and audio
3. **Video Assembly** - TTS, timeline, rendering
4. **Thumbnail Creation** - Generate video thumbnail
5. **Metadata Preparation** - Prepare YouTube metadata
6. **YouTube Upload** - Upload with metadata
7. **Analytics Tracking** - Track performance

---

## Components

### ContentScheduler

Main orchestration service that manages the complete workflow.

**Key Features:**

- Schedule single videos
- Batch scheduling
- Automatic retry with exponential backoff
- Progress tracking
- Job cancellation/pause/resume
- Execution history

**Usage:**

```python
from services.scheduler import ContentScheduler, ScheduleConfig

scheduler = ContentScheduler(config=ScheduleConfig())

# Schedule video
job_id = await scheduler.schedule_video(
    topic="Python Functions Tutorial",
    scheduled_at=datetime(2024, 12, 25, 10, 0),
    publish_at=datetime(2024, 12, 25, 12, 0),
    style="educational",
    duration_minutes=5,
    tags=["python", "tutorial"]
)

# Start scheduler
await scheduler.start()

# Monitor progress
job = await scheduler.get_job_status(job_id)
print(f"Progress: {job.progress_percent}%")
```

### JobExecutor

Background execution engine with retry logic.

**Key Features:**

- Async job execution
- Configurable retry strategies (fixed, exponential, linear)
- Concurrent job limits
- Timeout handling
- Progress callbacks
- Execution history

**Retry Strategies:**

- **NONE**: No retries
- **FIXED_DELAY**: Fixed delay between retries
- **EXPONENTIAL_BACKOFF**: 2^n \* base_delay (default)
- **LINEAR_BACKOFF**: n \* base_delay

**Usage:**

```python
from services.scheduler import JobExecutor, ExecutorConfig, RetryStrategy

executor = JobExecutor(config=ExecutorConfig(
    max_concurrent_jobs=3,
    max_retries=3,
    retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
    base_retry_delay_seconds=60
))

result = await executor.execute(
    job_func=my_async_function,
    job_args={"param": "value"},
    job_id="my-job",
    timeout=3600
)

if result.status == ExecutionStatus.COMPLETED:
    print(f"Success! Result: {result.result_data}")
```

### RecurringScheduler

Pattern-based scheduling using APScheduler.

**Key Features:**

- Daily schedules
- Weekly schedules (specific days)
- Monthly schedules (specific dates)
- Interval schedules
- Custom cron expressions
- Dynamic topic generation
- Pause/resume schedules

**Usage:**

```python
from services.scheduler import RecurringScheduler, DayOfWeek

scheduler = RecurringScheduler(content_scheduler)

# Daily at 10 AM
await scheduler.create_daily_schedule(
    name="Daily Python Tips",
    topic_template="Python Tip - {date}",
    hour=10,
    minute=0
)

# Weekly: Mon/Wed/Fri at 2 PM
await scheduler.create_weekly_schedule(
    name="Weekly Tutorials",
    topic_template="Tutorial Week {week}",
    days=[DayOfWeek.MONDAY, DayOfWeek.WEDNESDAY, DayOfWeek.FRIDAY],
    hour=14,
    minute=0
)

# Monthly: 1st and 15th at 9 AM
await scheduler.create_monthly_schedule(
    name="Monthly Deep Dives",
    topic_template="Deep Dive {month} {year}",
    days_of_month=[1, 15],
    hour=9,
    minute=0
)

await scheduler.start()
```

**Topic Template Variables:**

- `{date}` - 2024-06-15
- `{time}` - 14:30
- `{datetime}` - 2024-06-15 14:30
- `{year}` - 2024
- `{month}` - June
- `{month_num}` - 6
- `{day}` - 15
- `{weekday}` - Saturday
- `{week}` - 24 (week number)
- `{timestamp}` - 1718456400 (Unix timestamp)

### CalendarManager

Content calendar and planning system.

**Key Features:**

- Visual calendar representation
- Conflict detection (time and topic)
- Optimal slot suggestions
- Content gap analysis
- Day/week/month views
- Slot reservation
- Utilization tracking

**Usage:**

```python
from services.scheduler import CalendarManager, CalendarConfig

calendar = CalendarManager(config=CalendarConfig(
    min_gap_hours=6,
    max_videos_per_day=3,
    preferred_hours=[10, 14, 18]
))

# Reserve slot
slot = await calendar.reserve_slot(
    scheduled_at=datetime(2024, 12, 25, 10, 0),
    topic="Python Tutorial",
    duration_minutes=5
)

# Get week view
week_view = await calendar.get_week_view(start_date=date.today())

for entry in week_view:
    print(f"{entry.date}: {entry.total_slots} slots")

# Suggest optimal slots
suggestions = await calendar.suggest_optimal_slots(
    count=5,
    start_date=date.today(),
    days=30
)

# Detect conflicts
conflicts = await calendar.detect_conflicts()
```

---

## Installation

### Prerequisites

```bash
pip install apscheduler pydantic asyncio
```

### Dependencies

The scheduler integrates with:

- **ScriptGenerator** (Task #6) - AI script generation
- **VideoAssembler** (Task #7) - Video production
- **YouTubeUploader** (Task #8) - YouTube uploads
- **CacheManager** (Task #4) - State caching

---

## Quick Start

### Complete Automation Setup

```python
import asyncio
from datetime import datetime, timedelta
from services.scheduler import (
    ContentScheduler,
    RecurringScheduler,
    CalendarManager,
    ScheduleConfig,
    DayOfWeek
)

async def setup_automation():
    # Initialize scheduler
    scheduler = ContentScheduler(config=ScheduleConfig(
        jobs_storage_path="scheduled_jobs",
        output_dir="output_videos",
        max_retries=3,
        youtube_account="main"
    ))

    # Create recurring schedules
    recurring = RecurringScheduler(scheduler)

    # Daily tips at 10 AM
    await recurring.create_daily_schedule(
        name="Daily Python Tips",
        topic_template="Python Tip #{date}",
        hour=10,
        tags=["python", "tips", "daily"]
    )

    # Weekly tutorials
    await recurring.create_weekly_schedule(
        name="Weekly Tutorials",
        topic_template="Python Tutorial - Week {week}",
        days=[DayOfWeek.MONDAY, DayOfWeek.THURSDAY],
        hour=14,
        tags=["python", "tutorial"]
    )

    # Start automation
    await scheduler.start()
    await recurring.start()

    print("Automation running! Videos will be created automatically.")

    # Monitor
    while True:
        stats = scheduler.get_statistics()
        print(f"Active jobs: {stats['active_jobs']}, "
              f"Completed: {stats['statistics']['total_completed']}")

        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(setup_automation())
```

---

## API Reference

### ContentScheduler

#### Methods

##### `schedule_video()`

Schedule single video for creation and upload.

```python
async def schedule_video(
    topic: str,
    scheduled_at: datetime,
    publish_at: Optional[datetime] = None,
    style: str = "educational",
    duration_minutes: int = 5,
    tags: Optional[List[str]] = None,
    category: Category = Category.EDUCATION,
    privacy_status: PrivacyStatus = PrivacyStatus.PRIVATE
) -> str
```

**Parameters:**

- `topic` - Video topic (required)
- `scheduled_at` - When to create video (required)
- `publish_at` - When to publish (None = immediately)
- `style` - Content style (default: "educational")
- `duration_minutes` - Target duration (default: 5)
- `tags` - YouTube tags
- `category` - YouTube category
- `privacy_status` - Privacy setting

**Returns:** Job ID (str)

##### `schedule_batch()`

Schedule multiple videos at once.

```python
async def schedule_batch(
    videos: List[Dict[str, Any]]
) -> List[str]
```

**Parameters:**

- `videos` - List of video configs (each with schedule_video params)

**Returns:** List of job IDs

##### `get_job_status()`

Get job status and progress.

```python
async def get_job_status(job_id: str) -> Optional[ScheduledJob]
```

**Returns:** ScheduledJob with status, progress, results

##### `cancel_job()`

Cancel scheduled or active job.

```python
async def cancel_job(job_id: str)
```

##### `pause_job()` / `resume_job()`

Pause or resume pending job.

```python
async def pause_job(job_id: str)
async def resume_job(job_id: str)
```

##### `get_all_jobs()`

Get all jobs with optional filter.

```python
def get_all_jobs(
    status_filter: Optional[JobStatus] = None
) -> List[ScheduledJob]
```

##### `get_statistics()`

Get scheduler statistics.

```python
def get_statistics() -> Dict[str, Any]
```

**Returns:**

```python
{
    "total_jobs": 10,
    "active_jobs": 2,
    "status_counts": {
        "pending": 3,
        "completed": 5,
        "failed": 2
    },
    "statistics": {
        "total_scheduled": 10,
        "total_completed": 5,
        "total_failed": 2
    },
    "running": True
}
```

### JobExecutor

#### Methods

##### `execute()`

Execute job with retry logic.

```python
async def execute(
    job_func: Callable,
    job_args: Optional[Dict[str, Any]] = None,
    job_id: Optional[str] = None,
    max_retries: Optional[int] = None,
    retry_strategy: Optional[RetryStrategy] = None,
    timeout: Optional[int] = None,
    progress_callback: Optional[Callable] = None
) -> ExecutionResult
```

##### `execute_batch()`

Execute multiple jobs.

```python
async def execute_batch(
    jobs: List[Dict[str, Any]],
    fail_fast: bool = False
) -> List[ExecutionResult]
```

##### `cancel_execution()`

Cancel active execution.

```python
async def cancel_execution(execution_id: str)
```

### RecurringScheduler

#### Methods

##### `create_daily_schedule()`

Create daily recurring schedule.

```python
async def create_daily_schedule(
    name: str,
    topic_template: str,
    hour: int = 10,
    minute: int = 0,
    style: str = "educational",
    duration_minutes: int = 5,
    tags: Optional[List[str]] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> str
```

##### `create_weekly_schedule()`

Create weekly recurring schedule.

```python
async def create_weekly_schedule(
    name: str,
    topic_template: str,
    days: List[DayOfWeek],
    hour: int = 10,
    minute: int = 0,
    ...
) -> str
```

##### `create_monthly_schedule()`

Create monthly recurring schedule.

```python
async def create_monthly_schedule(
    name: str,
    topic_template: str,
    days_of_month: List[int],  # 1-31
    hour: int = 10,
    minute: int = 0,
    ...
) -> str
```

##### `create_cron_schedule()`

Create schedule from cron expression.

```python
async def create_cron_schedule(
    name: str,
    topic_template: str,
    cron_expression: str,  # e.g., "0 10 * * *"
    ...
) -> str
```

### CalendarManager

#### Methods

##### `reserve_slot()`

Reserve calendar slot.

```python
async def reserve_slot(
    scheduled_at: datetime,
    topic: str,
    duration_minutes: Optional[int] = None,
    ...
) -> ContentSlot
```

##### `get_day_view()`

Get calendar for single day.

```python
async def get_day_view(target_date: date) -> CalendarEntry
```

##### `get_week_view()`

Get calendar for week.

```python
async def get_week_view(start_date: date) -> List[CalendarEntry]
```

##### `get_month_view()`

Get calendar for month.

```python
async def get_month_view(year: int, month: int) -> List[CalendarEntry]
```

##### `suggest_optimal_slots()`

Suggest optimal time slots.

```python
async def suggest_optimal_slots(
    count: int,
    start_date: Optional[date] = None,
    days: int = 30,
    preferred_hours: Optional[List[int]] = None
) -> List[datetime]
```

##### `detect_conflicts()`

Detect scheduling conflicts.

```python
async def detect_conflicts() -> List[Dict[str, Any]]
```

---

## Scheduling Patterns

### Daily Schedules

Videos created every day at specific time.

```python
# Every day at 10 AM
await scheduler.create_daily_schedule(
    name="Daily Videos",
    topic_template="Daily Video - {date}",
    hour=10,
    minute=0
)
```

### Weekly Schedules

Videos on specific days of week.

```python
# Monday, Wednesday, Friday at 2 PM
await scheduler.create_weekly_schedule(
    name="MWF Videos",
    topic_template="Video - {weekday}",
    days=[DayOfWeek.MONDAY, DayOfWeek.WEDNESDAY, DayOfWeek.FRIDAY],
    hour=14,
    minute=0
)
```

### Monthly Schedules

Videos on specific dates each month.

```python
# 1st and 15th of each month at 9 AM
await scheduler.create_monthly_schedule(
    name="Bi-Monthly Videos",
    topic_template="Video - {month} {day}",
    days_of_month=[1, 15],
    hour=9,
    minute=0
)
```

### Interval Schedules

Videos at regular intervals.

```python
# Every 6 hours
await scheduler.create_interval_schedule(
    name="6-Hour Videos",
    topic_template="Video #{timestamp}",
    interval_hours=6
)
```

### Cron Schedules

Advanced patterns using cron expressions.

```python
# Monday-Friday at 9 AM and 5 PM
await scheduler.create_cron_schedule(
    name="Business Hours",
    topic_template="Video {time}",
    cron_expression="0 9,17 * * 1-5"
)
```

**Common Cron Patterns:**

- `0 10 * * *` - Daily at 10 AM
- `0 14 * * 1,3,5` - Mon/Wed/Fri at 2 PM
- `0 9 1,15 * *` - 1st and 15th at 9 AM
- `0 */6 * * *` - Every 6 hours
- `0 9-17 * * 1-5` - Every hour 9AM-5PM, Mon-Fri

---

## Best Practices

### 1. Schedule Management

**DO:**

- Use recurring schedules for consistent content
- Set reasonable gaps between videos (6+ hours)
- Use calendar to visualize schedule
- Monitor job statistics regularly

**DON'T:**

- Schedule too many videos simultaneously
- Ignore conflicts and warnings
- Skip error handling
- Forget to clean old jobs

### 2. Error Handling

Always wrap scheduler operations in try/except:

```python
try:
    job_id = await scheduler.schedule_video(
        topic="My Video",
        scheduled_at=tomorrow
    )
except Exception as e:
    logger.error(f"Scheduling failed: {e}")
    # Handle error
```

### 3. Resource Management

Limit concurrent jobs to avoid overload:

```python
config = ScheduleConfig(
    max_concurrent_jobs=2,  # Process 2 videos at once
    max_retries=3,
    check_interval_seconds=60
)
```

### 4. Monitoring

Implement monitoring for production:

```python
async def monitor_scheduler(scheduler):
    while True:
        stats = scheduler.get_statistics()

        # Alert if too many failures
        if stats['statistics']['total_failed'] > 10:
            send_alert("High failure rate!")

        # Log progress
        logger.info(f"Active: {stats['active_jobs']}, "
                    f"Completed: {stats['statistics']['total_completed']}")

        await asyncio.sleep(300)  # Check every 5 minutes
```

### 5. Job Persistence

Jobs are automatically saved to disk. Load on startup:

```python
scheduler = ContentScheduler(config=ScheduleConfig())
await scheduler.load_jobs()  # Restore jobs from disk
await scheduler.start()
```

### 6. Calendar Planning

Use calendar to avoid conflicts:

```python
# Check for conflicts before scheduling
conflicts = await calendar.detect_conflicts()

if conflicts:
    logger.warning(f"Found {len(conflicts)} conflicts")
    # Resolve conflicts...

# Get optimal suggestions
suggestions = await calendar.suggest_optimal_slots(count=5)

# Schedule at optimal times
for slot_time in suggestions:
    await scheduler.schedule_video(
        topic=f"Video at {slot_time}",
        scheduled_at=slot_time
    )
```

---

## Troubleshooting

### Issue: Jobs not executing

**Symptoms:** Jobs stay in PENDING status

**Solutions:**

1. Check scheduler is started: `await scheduler.start()`
2. Verify scheduled time is in future
3. Check concurrent job limit
4. Review logs for errors

### Issue: High failure rate

**Symptoms:** Many jobs in FAILED status

**Solutions:**

1. Check external service credentials (YouTube, Ollama)
2. Increase retry count and delay
3. Verify network connectivity
4. Check resource availability (disk, memory)

### Issue: Conflicts detected

**Symptoms:** Calendar shows CONFLICT status

**Solutions:**

1. Increase min_gap_hours in CalendarConfig
2. Reduce max_videos_per_day
3. Use calendar.suggest_optimal_slots() for better times
4. Review and adjust blackout days

### Issue: Recurring schedules not triggering

**Symptoms:** Recurring jobs not creating videos

**Solutions:**

1. Verify recurring scheduler is started: `await recurring.start()`
2. Check job is enabled: `job.enabled == True`
3. Verify cron expression syntax
4. Check timezone settings
5. Review APScheduler logs

### Issue: Out of disk space

**Symptoms:** Video assembly fails

**Solutions:**

1. Implement automatic cleanup:
   ```python
   await scheduler.clean_old_jobs(days=30)
   ```
2. Monitor disk usage
3. Compress or delete old videos
4. Use external storage

### Debug Mode

Enable detailed logging:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('services.scheduler')
logger.setLevel(logging.DEBUG)
```

---

## Performance Optimization

### 1. Concurrent Job Limits

```python
config = ScheduleConfig(
    max_concurrent_jobs=2  # Adjust based on system resources
)
```

### 2. Retry Strategy

```python
executor_config = ExecutorConfig(
    retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
    base_retry_delay_seconds=60,
    max_retry_delay_seconds=3600
)
```

### 3. Caching

Jobs and results are automatically cached. Clean periodically:

```python
# Clean jobs older than 30 days
await scheduler.clean_old_jobs(days=30)

# Clean execution history
await executor.clean_history()
```

---

## Contributing

See main project README for contribution guidelines.

---

## License

Copyright (c) 2024 DOPPELGANGER STUDIO. All Rights Reserved.

---

## Support

For issues or questions:

- Check troubleshooting section
- Review examples in `examples/scheduler_usage.py`
- Check logs for error details
- Review test suite for usage patterns

---

**Last Updated:** December 2024  
**Version:** 1.0.0
