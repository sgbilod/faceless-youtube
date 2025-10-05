"""
Scheduler Test Suite

Comprehensive tests for all scheduler components:
- ContentScheduler
- JobExecutor
- RecurringScheduler
- CalendarManager
"""

import pytest
import asyncio
from datetime import datetime, timedelta, date, time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path

# Scheduler components
from src.services.scheduler import (
    ContentScheduler,
    ScheduleConfig,
    ScheduledJob,
    JobStatus,
    JobType,
    WorkflowStage,
    JobExecutor,
    ExecutorConfig,
    ExecutionResult,
    ExecutionStatus,
    RetryStrategy,
    RecurringScheduler,
    RecurringConfig,
    RecurringJob,
    RecurringPattern,
    ScheduleRule,
    DayOfWeek,
    CalendarManager,
    CalendarConfig,
    CalendarEntry,
    CalendarView,
    ContentSlot,
    ContentSlotStatus
)


# ===================================================================
# Fixtures
# ===================================================================

@pytest.fixture
def temp_storage(tmp_path):
    """Temporary storage directory"""
    storage = tmp_path / "scheduled_jobs"
    storage.mkdir()
    return str(storage)


@pytest.fixture
def schedule_config(temp_storage):
    """Schedule configuration"""
    return ScheduleConfig(
        jobs_storage_path=temp_storage,
        max_retries=2,
        retry_delay_minutes=1,
        check_interval_seconds=1
    )


@pytest.fixture
def executor_config():
    """Executor configuration"""
    return ExecutorConfig(
        max_concurrent_jobs=2,
        max_retries=2,
        base_retry_delay_seconds=1
    )


@pytest.fixture
def recurring_config():
    """Recurring scheduler configuration"""
    return RecurringConfig()


@pytest.fixture
def calendar_config():
    """Calendar configuration"""
    return CalendarConfig(
        min_gap_hours=2,
        max_videos_per_day=3,
        preferred_hours=[8, 12, 16, 20]  # Spaced 4 hours apart
    )


@pytest.fixture
def mock_script_generator():
    """Mock script generator"""
    generator = AsyncMock()
    generator.generate = AsyncMock(return_value=Mock(
        content="Test script content",
        title="Test Video",
        description="Test description",
        tags=["test", "python"]
    ))
    return generator


@pytest.fixture
def mock_video_assembler():
    """Mock video assembler"""
    assembler = AsyncMock()
    assembler.assemble = AsyncMock(return_value=Mock(
        output_path="test_video.mp4",
        thumbnail_path="test_thumb.jpg",
        duration=300
    ))
    return assembler


@pytest.fixture
def mock_youtube_uploader():
    """Mock YouTube uploader"""
    uploader = AsyncMock()
    uploader.upload = AsyncMock(return_value=Mock(
        video_id="test123",
        url="https://youtube.com/watch?v=test123"
    ))
    return uploader


# ===================================================================
# ContentScheduler Tests
# ===================================================================

class TestContentScheduler:
    """Test ContentScheduler"""
    
    @pytest.mark.asyncio
    async def test_schedule_video(
        self,
        schedule_config,
        mock_script_generator,
        mock_video_assembler
    ):
        """Test scheduling single video"""
        scheduler = ContentScheduler(
            config=schedule_config,
            script_generator=mock_script_generator,
            video_assembler=mock_video_assembler
        )
        
        scheduled_at = datetime.utcnow() + timedelta(hours=1)
        
        job_id = await scheduler.schedule_video(
            topic="Test Video",
            scheduled_at=scheduled_at,
            style="educational",
            duration_minutes=5
        )
        
        assert job_id is not None
        assert len(job_id) > 0
        
        # Verify job created
        job = await scheduler.get_job_status(job_id)
        assert job is not None
        assert job.topic == "Test Video"
        assert job.status == JobStatus.PENDING
        assert job.scheduled_at == scheduled_at
    
    @pytest.mark.asyncio
    async def test_schedule_batch(
        self,
        schedule_config,
        mock_script_generator,
        mock_video_assembler
    ):
        """Test batch scheduling"""
        scheduler = ContentScheduler(
            config=schedule_config,
            script_generator=mock_script_generator,
            video_assembler=mock_video_assembler
        )
        
        videos = [
            {
                "topic": "Video 1",
                "scheduled_at": datetime.utcnow() + timedelta(hours=i),
                "style": "educational"
            }
            for i in range(1, 4)
        ]
        
        job_ids = await scheduler.schedule_batch(videos)
        
        assert len(job_ids) == 3
        assert all(len(jid) > 0 for jid in job_ids)
    
    @pytest.mark.asyncio
    async def test_job_execution_workflow(
        self,
        schedule_config,
        mock_script_generator,
        mock_video_assembler,
        mock_youtube_uploader
    ):
        """Test complete job execution workflow"""
        scheduler = ContentScheduler(
            config=schedule_config,
            script_generator=mock_script_generator,
            video_assembler=mock_video_assembler,
            youtube_uploader=mock_youtube_uploader
        )
        
        # Schedule for immediate execution
        scheduled_at = datetime.utcnow()
        
        job_id = await scheduler.schedule_video(
            topic="Test Video",
            scheduled_at=scheduled_at,
            style="educational"
        )
        
        # Execute job directly
        job = await scheduler.get_job_status(job_id)
        await scheduler._execute_job(job)
        
        # Verify workflow stages completed
        assert job.status == JobStatus.COMPLETED
        assert job.script_path is not None
        assert job.video_path is not None
        assert job.youtube_video_id is not None
        assert job.progress_percent == 100
        
        # Verify all services called
        mock_script_generator.generate.assert_called_once()
        mock_video_assembler.assemble.assert_called_once()
        mock_youtube_uploader.upload.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_job_retry_logic(
        self,
        schedule_config,
        mock_script_generator,
        mock_video_assembler
    ):
        """Test job retry on failure"""
        # Make script generation fail first time
        mock_script_generator.generate = AsyncMock(
            side_effect=[Exception("Test failure"), Mock(
                content="Test script",
                title="Test",
                description="Test",
                tags=[]
            )]
        )
        
        scheduler = ContentScheduler(
            config=schedule_config,
            script_generator=mock_script_generator,
            video_assembler=mock_video_assembler
        )
        
        job_id = await scheduler.schedule_video(
            topic="Test Video",
            scheduled_at=datetime.utcnow()
        )
        
        job = await scheduler.get_job_status(job_id)
        
        # First attempt - should fail
        await scheduler._execute_job(job)
        
        assert job.retry_count == 1
        assert job.status == JobStatus.PENDING
        assert job.error_message is not None
        
        # Second attempt - should succeed
        await scheduler._execute_job(job)
        
        assert job.status == JobStatus.COMPLETED
        assert job.retry_count == 1
    
    @pytest.mark.asyncio
    async def test_job_cancellation(
        self,
        schedule_config,
        mock_script_generator,
        mock_video_assembler
    ):
        """Test job cancellation"""
        scheduler = ContentScheduler(
            config=schedule_config,
            script_generator=mock_script_generator,
            video_assembler=mock_video_assembler
        )
        
        job_id = await scheduler.schedule_video(
            topic="Test Video",
            scheduled_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        await scheduler.cancel_job(job_id)
        
        job = await scheduler.get_job_status(job_id)
        assert job.status == JobStatus.CANCELLED
    
    @pytest.mark.asyncio
    async def test_get_statistics(
        self,
        schedule_config,
        mock_script_generator,
        mock_video_assembler
    ):
        """Test statistics tracking"""
        scheduler = ContentScheduler(
            config=schedule_config,
            script_generator=mock_script_generator,
            video_assembler=mock_video_assembler
        )
        
        # Schedule multiple jobs
        for i in range(3):
            await scheduler.schedule_video(
                topic=f"Video {i}",
                scheduled_at=datetime.utcnow() + timedelta(hours=i)
            )
        
        stats = scheduler.get_statistics()
        
        assert stats["total_jobs"] == 3
        assert stats["status_counts"][JobStatus.PENDING.value] == 3
        assert stats["statistics"]["total_scheduled"] == 3


# ===================================================================
# JobExecutor Tests
# ===================================================================

class TestJobExecutor:
    """Test JobExecutor"""
    
    @pytest.mark.asyncio
    async def test_execute_success(self, executor_config):
        """Test successful job execution"""
        executor = JobExecutor(config=executor_config)
        
        async def test_job(value: int):
            await asyncio.sleep(0.1)
            return value * 2
        
        result = await executor.execute(
            job_func=test_job,
            job_args={"value": 5},
            job_id="test-job"
        )
        
        assert result.status == ExecutionStatus.COMPLETED
        assert result.result_data == 10
        assert result.duration_seconds is not None
        assert result.error_message is None
    
    @pytest.mark.asyncio
    async def test_execute_with_retry(self, executor_config):
        """Test execution with retry"""
        executor = JobExecutor(config=executor_config)
        
        attempt = [0]
        
        async def test_job():
            attempt[0] += 1
            if attempt[0] < 3:
                raise Exception("Not ready")
            return "success"
        
        result = await executor.execute(
            job_func=test_job,
            job_id="test-retry",
            max_retries=3
        )
        
        assert result.status == ExecutionStatus.COMPLETED
        assert result.result_data == "success"
        assert result.retry_count == 2
    
    @pytest.mark.asyncio
    async def test_execute_max_retries_reached(self, executor_config):
        """Test max retries failure"""
        executor = JobExecutor(config=executor_config)
        
        async def failing_job():
            raise Exception("Always fails")
        
        result = await executor.execute(
            job_func=failing_job,
            job_id="test-fail",
            max_retries=2
        )
        
        assert result.status == ExecutionStatus.FAILED
        assert result.error_message is not None
        assert result.retry_count == 2
    
    @pytest.mark.asyncio
    async def test_execute_timeout(self, executor_config):
        """Test execution timeout"""
        executor = JobExecutor(config=executor_config)
        
        async def slow_job():
            await asyncio.sleep(10)
            return "done"
        
        result = await executor.execute(
            job_func=slow_job,
            job_id="test-timeout",
            timeout=1
        )
        
        assert result.status == ExecutionStatus.FAILED
        assert "timeout" in result.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_concurrent_execution_limit(self, executor_config):
        """Test concurrent job limit"""
        executor = JobExecutor(config=executor_config)
        
        execution_times = []
        
        async def test_job(job_id: int):
            start = asyncio.get_event_loop().time()
            await asyncio.sleep(0.2)
            execution_times.append((job_id, start))
            return job_id
        
        # Execute 4 jobs with limit of 2
        tasks = [
            executor.execute(
                job_func=test_job,
                job_args={"job_id": i},
                job_id=f"job-{i}"
            )
            for i in range(4)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert all(r.status == ExecutionStatus.COMPLETED for r in results)
        assert len(execution_times) == 4
    
    @pytest.mark.asyncio
    async def test_execute_batch(self, executor_config):
        """Test batch execution"""
        executor = JobExecutor(config=executor_config)
        
        async def test_job(value: int):
            await asyncio.sleep(0.05)
            return value * 2
        
        jobs = [
            {"func": test_job, "args": {"value": i}, "id": f"job-{i}"}
            for i in range(5)
        ]
        
        results = await executor.execute_batch(jobs)
        
        assert len(results) == 5
        assert all(r.status == ExecutionStatus.COMPLETED for r in results)
        assert [r.result_data for r in results] == [0, 2, 4, 6, 8]


# ===================================================================
# RecurringScheduler Tests
# ===================================================================

class TestRecurringScheduler:
    """Test RecurringScheduler"""
    
    @pytest.mark.asyncio
    async def test_create_daily_schedule(
        self,
        recurring_config,
        schedule_config,
        mock_script_generator,
        mock_video_assembler
    ):
        """Test daily schedule creation"""
        content_scheduler = ContentScheduler(
            config=schedule_config,
            script_generator=mock_script_generator,
            video_assembler=mock_video_assembler
        )
        
        scheduler = RecurringScheduler(
            content_scheduler=content_scheduler,
            config=recurring_config
        )
        
        job_id = await scheduler.create_daily_schedule(
            name="Daily Python Tips",
            topic_template="Python Tip - {date}",
            hour=10,
            minute=0
        )
        
        assert job_id is not None
        
        job = scheduler.get_job(job_id)
        assert job is not None
        assert job.name == "Daily Python Tips"
        assert job.schedule_rule.pattern == RecurringPattern.DAILY
        assert job.schedule_rule.hour == 10
    
    @pytest.mark.asyncio
    async def test_create_weekly_schedule(
        self,
        recurring_config,
        schedule_config,
        mock_script_generator,
        mock_video_assembler
    ):
        """Test weekly schedule creation"""
        content_scheduler = ContentScheduler(
            config=schedule_config,
            script_generator=mock_script_generator,
            video_assembler=mock_video_assembler
        )
        
        scheduler = RecurringScheduler(
            content_scheduler=content_scheduler,
            config=recurring_config
        )
        
        job_id = await scheduler.create_weekly_schedule(
            name="Weekly Tutorials",
            topic_template="Tutorial - Week {week}",
            days=[DayOfWeek.MONDAY, DayOfWeek.WEDNESDAY, DayOfWeek.FRIDAY],
            hour=14,
            minute=30
        )
        
        assert job_id is not None
        
        job = scheduler.get_job(job_id)
        assert job is not None
        assert job.schedule_rule.pattern == RecurringPattern.WEEKLY
        assert len(job.schedule_rule.days_of_week) == 3
    
    @pytest.mark.asyncio
    async def test_format_topic_template(
        self,
        recurring_config,
        schedule_config,
        mock_script_generator,
        mock_video_assembler
    ):
        """Test topic template formatting"""
        content_scheduler = ContentScheduler(
            config=schedule_config,
            script_generator=mock_script_generator,
            video_assembler=mock_video_assembler
        )
        
        scheduler = RecurringScheduler(
            content_scheduler=content_scheduler,
            config=recurring_config
        )
        
        dt = datetime(2024, 6, 15, 14, 30)
        
        template = "Video {date} at {time} - Week {week}"
        result = scheduler._format_topic(template, dt)
        
        assert "2024-06-15" in result
        assert "14:30" in result
        assert "Week" in result
    
    @pytest.mark.asyncio
    async def test_pause_resume_job(
        self,
        recurring_config,
        schedule_config,
        mock_script_generator,
        mock_video_assembler
    ):
        """Test pausing and resuming jobs"""
        content_scheduler = ContentScheduler(
            config=schedule_config,
            script_generator=mock_script_generator,
            video_assembler=mock_video_assembler
        )
        
        scheduler = RecurringScheduler(
            content_scheduler=content_scheduler,
            config=recurring_config
        )
        
        job_id = await scheduler.create_daily_schedule(
            name="Test Daily",
            topic_template="Daily {date}",
            hour=10
        )
        
        # Pause
        await scheduler.pause_job(job_id)
        
        job = scheduler.get_job(job_id)
        assert not job.enabled
        
        # Resume
        await scheduler.resume_job(job_id)
        
        job = scheduler.get_job(job_id)
        assert job.enabled


# ===================================================================
# CalendarManager Tests
# ===================================================================

class TestCalendarManager:
    """Test CalendarManager"""
    
    @pytest.mark.asyncio
    async def test_reserve_slot(self, calendar_config):
        """Test reserving calendar slot"""
        manager = CalendarManager(config=calendar_config)
        
        scheduled_at = datetime.now() + timedelta(days=1)
        
        slot = await manager.reserve_slot(
            scheduled_at=scheduled_at,
            topic="Test Video",
            duration_minutes=5,
            style="educational"
        )
        
        assert slot is not None
        assert slot.topic == "Test Video"
        assert slot.status == ContentSlotStatus.RESERVED
        assert slot.scheduled_at == scheduled_at
    
    @pytest.mark.asyncio
    async def test_time_conflict_detection(self, calendar_config):
        """Test time conflict detection"""
        manager = CalendarManager(config=calendar_config)
        
        base_time = datetime.now() + timedelta(days=1)
        
        # Reserve first slot
        await manager.reserve_slot(
            scheduled_at=base_time,
            topic="Video 1",
            duration_minutes=5
        )
        
        # Try to reserve conflicting slot (within min gap)
        conflicting_time = base_time + timedelta(hours=1)
        
        slot2 = await manager.reserve_slot(
            scheduled_at=conflicting_time,
            topic="Video 2",
            duration_minutes=5
        )
        
        # Should be marked as conflict
        assert slot2.status == ContentSlotStatus.CONFLICT
    
    @pytest.mark.asyncio
    async def test_get_day_view(self, calendar_config):
        """Test day view generation"""
        manager = CalendarManager(config=calendar_config)
        
        target_date = date.today() + timedelta(days=1)
        base_time = datetime.combine(target_date, time(10, 0))
        
        # Add multiple slots
        for i in range(3):
            await manager.reserve_slot(
                scheduled_at=base_time + timedelta(hours=i*4),
                topic=f"Video {i}",
                duration_minutes=5
            )
        
        entry = await manager.get_day_view(target_date)
        
        assert entry.date == target_date
        assert entry.total_slots == 3
        assert len(entry.slots) == 3
    
    @pytest.mark.asyncio
    async def test_get_week_view(self, calendar_config):
        """Test week view generation"""
        manager = CalendarManager(config=calendar_config)
        
        start_date = date.today()
        
        week_view = await manager.get_week_view(start_date)
        
        assert len(week_view) == 7
        assert week_view[0].date == start_date
        assert week_view[6].date == start_date + timedelta(days=6)
    
    @pytest.mark.asyncio
    async def test_suggest_optimal_slots(self, calendar_config):
        """Test optimal slot suggestions"""
        manager = CalendarManager(config=calendar_config)
        
        suggestions = await manager.suggest_optimal_slots(
            count=5,
            start_date=date.today() + timedelta(days=1),
            days=30
        )
        
        assert len(suggestions) <= 5
        
        # Verify suggestions don't conflict
        for i, slot_time in enumerate(suggestions):
            for other_time in suggestions[i+1:]:
                gap_hours = abs((slot_time - other_time).total_seconds() / 3600)
                assert gap_hours >= calendar_config.min_gap_hours
    
    @pytest.mark.asyncio
    async def test_detect_conflicts(self, calendar_config):
        """Test conflict detection"""
        manager = CalendarManager(config=calendar_config)
        
        base_time = datetime.now() + timedelta(days=1)
        
        # Create intentional conflict
        await manager.reserve_slot(
            scheduled_at=base_time,
            topic="Video 1",
            duration_minutes=5
        )
        
        await manager.reserve_slot(
            scheduled_at=base_time + timedelta(minutes=30),
            topic="Video 2",
            duration_minutes=5
        )
        
        conflicts = await manager.detect_conflicts()
        
        assert len(conflicts) > 0
        assert any(c["conflict_type"] == "time" for c in conflicts)
    
    @pytest.mark.asyncio
    async def test_get_content_gaps(self, calendar_config):
        """Test content gap detection"""
        manager = CalendarManager(config=calendar_config)
        
        start_date = date.today()
        end_date = start_date + timedelta(days=10)
        
        # Add content on specific days only
        for day_offset in [1, 2, 5, 6]:
            target_date = start_date + timedelta(days=day_offset)
            await manager.reserve_slot(
                scheduled_at=datetime.combine(target_date, time(10, 0)),
                topic=f"Video {day_offset}",
                duration_minutes=5
            )
        
        gaps = await manager.get_content_gaps(start_date, end_date)
        
        # Should have gaps between days 2-5 and 6-10
        assert len(gaps) >= 2


# ===================================================================
# Integration Tests
# ===================================================================

class TestIntegration:
    """Integration tests for complete workflows"""
    
    @pytest.mark.asyncio
    async def test_complete_scheduling_workflow(
        self,
        schedule_config,
        mock_script_generator,
        mock_video_assembler,
        mock_youtube_uploader
    ):
        """Test complete end-to-end workflow"""
        # Create scheduler
        scheduler = ContentScheduler(
            config=schedule_config,
            script_generator=mock_script_generator,
            video_assembler=mock_video_assembler,
            youtube_uploader=mock_youtube_uploader
        )
        
        # Schedule video
        scheduled_at = datetime.utcnow()
        
        job_id = await scheduler.schedule_video(
            topic="Integration Test Video",
            scheduled_at=scheduled_at,
            style="educational",
            duration_minutes=5,
            tags=["test", "integration"]
        )
        
        # Execute job
        job = await scheduler.get_job_status(job_id)
        await scheduler._execute_job(job)
        
        # Verify complete workflow
        assert job.status == JobStatus.COMPLETED
        assert job.progress_percent == 100
        assert job.script_path is not None
        assert job.video_path is not None
        assert job.youtube_video_id is not None
        
        # Verify all stages completed
        assert WorkflowStage.SCRIPT_GENERATION.value in job.stage_progress
        assert WorkflowStage.VIDEO_ASSEMBLY.value in job.stage_progress
        assert WorkflowStage.YOUTUBE_UPLOAD.value in job.stage_progress


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
