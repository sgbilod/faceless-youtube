"""
Scheduler Usage Examples

Comprehensive examples demonstrating all scheduler features:
1. Basic single video scheduling
2. Recurring schedules (daily/weekly/monthly)
3. Calendar management
4. Batch scheduling
5. Error handling and monitoring
"""

import asyncio
from datetime import datetime, timedelta, date, time

from services.scheduler import (
    ContentScheduler,
    ScheduleConfig,
    JobStatus,
    RecurringScheduler,
    RecurringConfig,
    DayOfWeek,
    CalendarManager,
    CalendarConfig,
    CalendarView
)

from services.script_generator import ScriptGenerator
from services.video_assembler import VideoAssembler, VideoConfig
from services.youtube_uploader import AuthManager, VideoUploader


# ===================================================================
# Example 1: Basic Single Video Scheduling
# ===================================================================

async def example_single_video():
    """Schedule single video for specific time"""
    print("\n=== Example 1: Single Video Scheduling ===\n")
    
    # Configure scheduler
    config = ScheduleConfig(
        jobs_storage_path="scheduled_jobs",
        output_dir="output_videos",
        max_retries=3,
        youtube_account="main"
    )
    
    # Initialize dependencies
    script_generator = ScriptGenerator()
    video_assembler = VideoAssembler(VideoConfig(quality="HD_1080P"))
    youtube_auth = AuthManager(credentials_path="client_secrets.json")
    youtube_uploader = VideoUploader(youtube_auth)
    
    # Create scheduler
    scheduler = ContentScheduler(
        config=config,
        script_generator=script_generator,
        video_assembler=video_assembler,
        youtube_auth=youtube_auth,
        youtube_uploader=youtube_uploader
    )
    
    # Schedule video for tomorrow at 10 AM
    tomorrow_10am = datetime.now() + timedelta(days=1)
    tomorrow_10am = tomorrow_10am.replace(hour=10, minute=0, second=0)
    
    job_id = await scheduler.schedule_video(
        topic="Introduction to Python Functions",
        scheduled_at=tomorrow_10am,
        publish_at=tomorrow_10am + timedelta(hours=2),  # Publish 2 hours after creation
        style="educational",
        duration_minutes=5,
        tags=["python", "tutorial", "functions", "programming"]
    )
    
    print(f"Scheduled video: {job_id}")
    print(f"Will be created at: {tomorrow_10am}")
    print(f"Will be published at: {tomorrow_10am + timedelta(hours=2)}")
    
    # Start scheduler (runs in background)
    await scheduler.start()
    
    # Monitor progress
    while True:
        job = await scheduler.get_job_status(job_id)
        
        print(f"\nStatus: {job.status.value}")
        print(f"Progress: {job.progress_percent}%")
        
        if job.current_stage:
            print(f"Current stage: {job.current_stage.value}")
        
        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
            break
        
        await asyncio.sleep(5)
    
    # Check final status
    if job.status == JobStatus.COMPLETED:
        print(f"\n✓ Video completed successfully!")
        print(f"  Script: {job.script_path}")
        print(f"  Video: {job.video_path}")
        print(f"  YouTube: {job.youtube_url}")
    else:
        print(f"\n✗ Video failed: {job.error_message}")
    
    await scheduler.stop()


# ===================================================================
# Example 2: Batch Scheduling
# ===================================================================

async def example_batch_scheduling():
    """Schedule multiple videos at once"""
    print("\n=== Example 2: Batch Scheduling ===\n")
    
    config = ScheduleConfig()
    scheduler = ContentScheduler(config=config)
    
    # Define multiple videos
    base_time = datetime.now() + timedelta(days=1)
    
    videos = [
        {
            "topic": "Python Variables and Data Types",
            "scheduled_at": base_time,
            "style": "educational",
            "duration_minutes": 5,
            "tags": ["python", "basics", "variables"]
        },
        {
            "topic": "Python Conditional Statements",
            "scheduled_at": base_time + timedelta(hours=6),
            "style": "educational",
            "duration_minutes": 6,
            "tags": ["python", "conditionals", "if-else"]
        },
        {
            "topic": "Python Loops Tutorial",
            "scheduled_at": base_time + timedelta(hours=12),
            "style": "educational",
            "duration_minutes": 7,
            "tags": ["python", "loops", "for", "while"]
        }
    ]
    
    # Schedule all videos
    job_ids = await scheduler.schedule_batch(videos)
    
    print(f"Scheduled {len(job_ids)} videos:")
    for i, job_id in enumerate(job_ids):
        print(f"  {i+1}. {job_id} - {videos[i]['topic']}")
    
    # Start scheduler
    await scheduler.start()
    
    # Get statistics
    stats = scheduler.get_statistics()
    print(f"\nScheduler statistics:")
    print(f"  Total jobs: {stats['total_jobs']}")
    print(f"  Active jobs: {stats['active_jobs']}")
    print(f"  Status counts: {stats['status_counts']}")
    
    await scheduler.stop()


# ===================================================================
# Example 3: Daily Recurring Schedule
# ===================================================================

async def example_daily_recurring():
    """Create daily recurring schedule"""
    print("\n=== Example 3: Daily Recurring Schedule ===\n")
    
    # Initialize schedulers
    content_scheduler = ContentScheduler(config=ScheduleConfig())
    recurring_scheduler = RecurringScheduler(
        content_scheduler=content_scheduler,
        config=RecurringConfig()
    )
    
    # Create daily schedule at 10 AM
    job_id = await recurring_scheduler.create_daily_schedule(
        name="Daily Python Tips",
        topic_template="Python Tip of the Day - {date}",
        hour=10,
        minute=0,
        style="educational",
        duration_minutes=3,
        tags=["python", "tips", "daily"]
    )
    
    print(f"Created daily schedule: {job_id}")
    
    # Get job details
    job = recurring_scheduler.get_job(job_id)
    print(f"Name: {job.name}")
    print(f"Pattern: {job.schedule_rule.pattern.value}")
    print(f"Time: {job.schedule_rule.hour}:{job.schedule_rule.minute:02d}")
    print(f"Next run: {job.next_run}")
    
    # Start scheduler
    await content_scheduler.start()
    await recurring_scheduler.start()
    
    print("\nScheduler running... Daily videos will be created at 10 AM")
    
    # Let it run for a while...
    await asyncio.sleep(60)
    
    await recurring_scheduler.stop()
    await content_scheduler.stop()


# ===================================================================
# Example 4: Weekly Recurring Schedule
# ===================================================================

async def example_weekly_recurring():
    """Create weekly recurring schedule"""
    print("\n=== Example 4: Weekly Recurring Schedule ===\n")
    
    content_scheduler = ContentScheduler(config=ScheduleConfig())
    recurring_scheduler = RecurringScheduler(
        content_scheduler=content_scheduler,
        config=RecurringConfig()
    )
    
    # Create weekly schedule: Monday, Wednesday, Friday at 2 PM
    job_id = await recurring_scheduler.create_weekly_schedule(
        name="Weekly Python Tutorials",
        topic_template="Python Tutorial - Week {week}, {weekday}",
        days=[DayOfWeek.MONDAY, DayOfWeek.WEDNESDAY, DayOfWeek.FRIDAY],
        hour=14,
        minute=30,
        style="educational",
        duration_minutes=10,
        tags=["python", "tutorial", "weekly"]
    )
    
    print(f"Created weekly schedule: {job_id}")
    
    job = recurring_scheduler.get_job(job_id)
    print(f"Name: {job.name}")
    print(f"Days: {[d.value for d in job.schedule_rule.days_of_week]}")
    print(f"Time: {job.schedule_rule.hour}:{job.schedule_rule.minute:02d}")
    print(f"Next run: {job.next_run}")
    
    await content_scheduler.start()
    await recurring_scheduler.start()
    
    print("\nScheduler running... Videos on Mon/Wed/Fri at 2:30 PM")
    
    await asyncio.sleep(60)
    
    await recurring_scheduler.stop()
    await content_scheduler.stop()


# ===================================================================
# Example 5: Monthly Recurring Schedule
# ===================================================================

async def example_monthly_recurring():
    """Create monthly recurring schedule"""
    print("\n=== Example 5: Monthly Recurring Schedule ===\n")
    
    content_scheduler = ContentScheduler(config=ScheduleConfig())
    recurring_scheduler = RecurringScheduler(
        content_scheduler=content_scheduler,
        config=RecurringConfig()
    )
    
    # Create monthly schedule: 1st and 15th at 9 AM
    job_id = await recurring_scheduler.create_monthly_schedule(
        name="Monthly Python Deep Dives",
        topic_template="Python Deep Dive - {month} {year} (Day {day})",
        days_of_month=[1, 15],
        hour=9,
        minute=0,
        style="advanced",
        duration_minutes=15,
        tags=["python", "deep-dive", "monthly", "advanced"]
    )
    
    print(f"Created monthly schedule: {job_id}")
    
    job = recurring_scheduler.get_job(job_id)
    print(f"Name: {job.name}")
    print(f"Days: {job.schedule_rule.days_of_month}")
    print(f"Time: {job.schedule_rule.hour}:{job.schedule_rule.minute:02d}")
    print(f"Next run: {job.next_run}")


# ===================================================================
# Example 6: Calendar Management
# ===================================================================

async def example_calendar_management():
    """Use calendar for content planning"""
    print("\n=== Example 6: Calendar Management ===\n")
    
    config = CalendarConfig(
        min_gap_hours=6,
        max_videos_per_day=3,
        preferred_hours=[10, 14, 18]  # 10 AM, 2 PM, 6 PM
    )
    
    calendar = CalendarManager(config=config)
    
    # Reserve slots for next week
    today = date.today()
    
    for day_offset in range(7):
        target_date = today + timedelta(days=day_offset + 1)
        
        # Skip weekends
        if target_date.weekday() >= 5:
            continue
        
        # Reserve slot at 10 AM
        scheduled_at = datetime.combine(target_date, time(10, 0))
        
        slot = await calendar.reserve_slot(
            scheduled_at=scheduled_at,
            topic=f"Python Tutorial - Day {day_offset + 1}",
            duration_minutes=5,
            style="educational",
            tags=["python", "tutorial"]
        )
        
        print(f"Reserved slot: {slot.id}")
        print(f"  Date: {scheduled_at}")
        print(f"  Topic: {slot.topic}")
        print(f"  Status: {slot.status.value}")
    
    # Get week view
    print("\n--- Week View ---")
    week_view = await calendar.get_week_view(start_date=today)
    
    for entry in week_view:
        print(f"\n{entry.date.strftime('%A, %B %d')}:")
        print(f"  Total slots: {entry.total_slots}")
        print(f"  Reserved: {entry.scheduled_slots}")
        
        for slot in entry.slots:
            print(f"    - {slot.scheduled_at.strftime('%I:%M %p')}: {slot.topic}")
    
    # Suggest optimal slots
    print("\n--- Optimal Slot Suggestions ---")
    suggestions = await calendar.suggest_optimal_slots(
        count=5,
        start_date=today + timedelta(days=7),
        days=14
    )
    
    for i, suggestion in enumerate(suggestions, 1):
        print(f"{i}. {suggestion.strftime('%A, %B %d at %I:%M %p')}")
    
    # Detect conflicts
    conflicts = await calendar.detect_conflicts()
    
    if conflicts:
        print(f"\n⚠ Found {len(conflicts)} conflicts:")
        for conflict in conflicts:
            print(f"  - {conflict['topic']}: {conflict['details']}")
    else:
        print("\n✓ No conflicts detected")
    
    # Get statistics
    stats = calendar.get_statistics()
    print(f"\nCalendar statistics:")
    print(f"  Total slots: {stats['total_slots']}")
    print(f"  Days with content: {stats['days_with_content']}")
    print(f"  Status counts: {stats['status_counts']}")


# ===================================================================
# Example 7: Complete Automation
# ===================================================================

async def example_complete_automation():
    """Set up complete automated system"""
    print("\n=== Example 7: Complete Automation ===\n")
    
    # Initialize all components
    schedule_config = ScheduleConfig(
        max_concurrent_jobs=2,
        youtube_account="main"
    )
    
    calendar_config = CalendarConfig(
        min_gap_hours=6,
        max_videos_per_day=3,
        preferred_hours=[10, 14, 18]
    )
    
    # Create components
    content_scheduler = ContentScheduler(config=schedule_config)
    recurring_scheduler = RecurringScheduler(
        content_scheduler=content_scheduler
    )
    calendar = CalendarManager(config=calendar_config)
    
    # Set up multiple recurring schedules
    schedules = [
        {
            "name": "Daily Python Tips",
            "type": "daily",
            "topic_template": "Python Tip #{date}",
            "hour": 10,
            "tags": ["python", "tips"]
        },
        {
            "name": "Weekly Tutorials",
            "type": "weekly",
            "topic_template": "Tutorial Week {week}",
            "days": [DayOfWeek.MONDAY, DayOfWeek.THURSDAY],
            "hour": 14,
            "tags": ["python", "tutorial"]
        },
        {
            "name": "Monthly Deep Dives",
            "type": "monthly",
            "topic_template": "Deep Dive {month}",
            "days_of_month": [1, 15],
            "hour": 18,
            "tags": ["python", "advanced"]
        }
    ]
    
    # Create all schedules
    job_ids = []
    
    for schedule in schedules:
        if schedule["type"] == "daily":
            job_id = await recurring_scheduler.create_daily_schedule(
                name=schedule["name"],
                topic_template=schedule["topic_template"],
                hour=schedule["hour"],
                minute=0,
                tags=schedule["tags"]
            )
        elif schedule["type"] == "weekly":
            job_id = await recurring_scheduler.create_weekly_schedule(
                name=schedule["name"],
                topic_template=schedule["topic_template"],
                days=schedule["days"],
                hour=schedule["hour"],
                minute=0,
                tags=schedule["tags"]
            )
        elif schedule["type"] == "monthly":
            job_id = await recurring_scheduler.create_monthly_schedule(
                name=schedule["name"],
                topic_template=schedule["topic_template"],
                days_of_month=schedule["days_of_month"],
                hour=schedule["hour"],
                minute=0,
                tags=schedule["tags"]
            )
        
        job_ids.append(job_id)
        print(f"Created schedule: {schedule['name']} ({job_id})")
    
    # Start all schedulers
    await content_scheduler.start()
    await recurring_scheduler.start()
    
    print(f"\n✓ Automation running with {len(job_ids)} recurring schedules")
    print("Videos will be created and uploaded automatically!")
    
    # Monitor statistics
    for _ in range(10):
        await asyncio.sleep(6)
        
        content_stats = content_scheduler.get_statistics()
        recurring_stats = recurring_scheduler.get_statistics()
        
        print(f"\nStatistics:")
        print(f"  Scheduled jobs: {content_stats['status_counts'].get('pending', 0)}")
        print(f"  Active jobs: {content_stats['active_jobs']}")
        print(f"  Completed: {content_stats['statistics']['total_completed']}")
        print(f"  Recurring schedules: {recurring_stats['enabled_jobs']}")
    
    await recurring_scheduler.stop()
    await content_scheduler.stop()


# ===================================================================
# Example 8: Error Handling and Monitoring
# ===================================================================

async def example_error_handling():
    """Demonstrate error handling and monitoring"""
    print("\n=== Example 8: Error Handling and Monitoring ===\n")
    
    config = ScheduleConfig(
        max_retries=3,
        retry_delay_minutes=2
    )
    
    scheduler = ContentScheduler(config=config)
    
    # Schedule video
    job_id = await scheduler.schedule_video(
        topic="Test Video with Monitoring",
        scheduled_at=datetime.now(),
        style="educational"
    )
    
    # Monitor with detailed logging
    print(f"Monitoring job: {job_id}")
    
    while True:
        job = await scheduler.get_job_status(job_id)
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Status: {job.status.value}")
        print(f"  Progress: {job.progress_percent}%")
        
        if job.current_stage:
            print(f"  Stage: {job.current_stage.value}")
        
        if job.error_message:
            print(f"  Error: {job.error_message}")
            print(f"  Retry count: {job.retry_count}/{config.max_retries}")
        
        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
            break
        
        await asyncio.sleep(5)
    
    # Final report
    print("\n=== Final Report ===")
    
    if job.status == JobStatus.COMPLETED:
        duration = (job.completed_at - job.started_at).total_seconds()
        print(f"✓ Success in {duration:.1f} seconds")
        print(f"  Retries: {job.retry_count}")
        print(f"  Script: {job.script_path}")
        print(f"  Video: {job.video_path}")
        print(f"  YouTube: {job.youtube_url}")
    else:
        print(f"✗ Failed after {job.retry_count} retries")
        print(f"  Error at: {job.error_stage}")
        print(f"  Error: {job.error_message}")


# ===================================================================
# Main
# ===================================================================

async def main():
    """Run all examples"""
    examples = [
        ("Single Video", example_single_video),
        ("Batch Scheduling", example_batch_scheduling),
        ("Daily Recurring", example_daily_recurring),
        ("Weekly Recurring", example_weekly_recurring),
        ("Monthly Recurring", example_monthly_recurring),
        ("Calendar Management", example_calendar_management),
        ("Complete Automation", example_complete_automation),
        ("Error Handling", example_error_handling)
    ]
    
    print("=" * 60)
    print("Scheduler Usage Examples")
    print("=" * 60)
    
    for i, (name, func) in enumerate(examples, 1):
        print(f"\n{i}. {name}")
    
    print("\nSelect example to run (1-8) or 'all': ", end="")
    
    # For demo purposes, just run example 6 (calendar management)
    # In real usage, get input from user
    choice = "6"
    
    if choice.lower() == "all":
        for name, func in examples:
            await func()
    else:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(examples):
                await examples[idx][1]()
            else:
                print("Invalid choice")
        except ValueError:
            print("Invalid input")


if __name__ == "__main__":
    asyncio.run(main())
