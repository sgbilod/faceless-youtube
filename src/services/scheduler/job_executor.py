"""
Job Executor

Background task execution engine with:
- Async job execution
- Retry logic with exponential backoff
- Concurrent job limits
- Progress tracking
- Error recovery
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ExecutionStatus(str, Enum):
    """Execution status"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class RetryStrategy(str, Enum):
    """Retry strategies"""
    NONE = "none"
    FIXED_DELAY = "fixed_delay"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"


@dataclass
class ExecutorConfig:
    """Executor configuration"""
    max_concurrent_jobs: int = 3
    max_retries: int = 3
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    base_retry_delay_seconds: int = 60
    max_retry_delay_seconds: int = 3600
    execution_timeout_seconds: int = 3600  # 1 hour
    enable_progress_tracking: bool = True
    store_execution_history: bool = True
    history_retention_days: int = 30


class ExecutionResult(BaseModel):
    """Execution result"""
    execution_id: str
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Results
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    
    # Retry info
    retry_count: int = 0
    max_retries: int = 0
    
    # Progress
    progress_percent: float = 0.0
    progress_message: Optional[str] = None


class JobExecutor:
    """
    Background job execution engine
    
    Features:
    - Async job execution with concurrent limits
    - Automatic retry with configurable strategies
    - Progress tracking with callbacks
    - Timeout handling
    - Execution history
    - Resource management
    
    Example:
        executor = JobExecutor(config=ExecutorConfig())
        
        # Execute job
        result = await executor.execute(
            job_func=create_video,
            job_args={"topic": "Python Tutorial"},
            job_id="job-123",
            progress_callback=lambda p: print(f"Progress: {p}%")
        )
        
        if result.status == ExecutionStatus.COMPLETED:
            print(f"Success! Result: {result.result_data}")
    """
    
    def __init__(self, config: ExecutorConfig):
        self.config = config
        
        # Execution tracking
        self._active_executions: Dict[str, asyncio.Task] = {}
        self._execution_history: Dict[str, ExecutionResult] = {}
        
        # Semaphore for concurrent limit
        self._semaphore = asyncio.Semaphore(config.max_concurrent_jobs)
        
        # Statistics
        self._stats = {
            "total_executed": 0,
            "total_completed": 0,
            "total_failed": 0,
            "total_cancelled": 0,
            "total_retries": 0
        }
    
    async def execute(
        self,
        job_func: Callable,
        job_args: Optional[Dict[str, Any]] = None,
        job_id: Optional[str] = None,
        max_retries: Optional[int] = None,
        retry_strategy: Optional[RetryStrategy] = None,
        timeout: Optional[int] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> ExecutionResult:
        """
        Execute job with retry logic
        
        Args:
            job_func: Async function to execute
            job_args: Function arguments
            job_id: Unique job ID
            max_retries: Override default max retries
            retry_strategy: Override default retry strategy
            timeout: Override default timeout
            progress_callback: Progress callback(percent, message)
        
        Returns:
            ExecutionResult with status and data
        """
        execution_id = job_id or str(uuid4())
        job_args = job_args or {}
        max_retries = max_retries if max_retries is not None else self.config.max_retries
        retry_strategy = retry_strategy or self.config.retry_strategy
        timeout = timeout or self.config.execution_timeout_seconds
        
        # Create result
        result = ExecutionResult(
            execution_id=execution_id,
            status=ExecutionStatus.QUEUED,
            started_at=datetime.utcnow(),
            max_retries=max_retries
        )
        
        # Track execution
        self._stats["total_executed"] += 1
        
        # Execute with retries
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                # Wait for slot
                async with self._semaphore:
                    result.status = ExecutionStatus.RUNNING
                    
                    # Create task with timeout
                    task = asyncio.create_task(
                        self._execute_with_progress(
                            job_func,
                            job_args,
                            progress_callback
                        )
                    )
                    
                    self._active_executions[execution_id] = task
                    
                    try:
                        # Wait with timeout
                        job_result = await asyncio.wait_for(task, timeout=timeout)
                        
                        # Success
                        result.status = ExecutionStatus.COMPLETED
                        result.completed_at = datetime.utcnow()
                        result.duration_seconds = (
                            result.completed_at - result.started_at
                        ).total_seconds()
                        result.result_data = job_result
                        result.progress_percent = 100
                        
                        self._stats["total_completed"] += 1
                        
                        logger.info(
                            f"[{execution_id}] Completed in {result.duration_seconds:.1f}s"
                        )
                        
                        break
                    
                    except asyncio.TimeoutError:
                        # Timeout
                        logger.error(f"[{execution_id}] Timeout after {timeout}s")
                        raise TimeoutError(f"Job execution timeout after {timeout}s")
                    
                    finally:
                        # Cleanup
                        if execution_id in self._active_executions:
                            del self._active_executions[execution_id]
            
            except asyncio.CancelledError:
                # Cancellation
                result.status = ExecutionStatus.CANCELLED
                result.completed_at = datetime.utcnow()
                self._stats["total_cancelled"] += 1
                
                logger.warning(f"[{execution_id}] Cancelled")
                break
            
            except Exception as e:
                # Execution error
                logger.error(f"[{execution_id}] Error: {e}", exc_info=True)
                
                result.retry_count = retry_count
                result.error_message = str(e)
                
                # Check if should retry
                if retry_count < max_retries:
                    retry_count += 1
                    self._stats["total_retries"] += 1
                    
                    # Calculate retry delay
                    delay = self._calculate_retry_delay(
                        retry_count,
                        retry_strategy
                    )
                    
                    result.status = ExecutionStatus.RETRYING
                    
                    logger.info(
                        f"[{execution_id}] Retry {retry_count}/{max_retries} "
                        f"in {delay}s"
                    )
                    
                    # Wait before retry
                    await asyncio.sleep(delay)
                else:
                    # Max retries reached
                    result.status = ExecutionStatus.FAILED
                    result.completed_at = datetime.utcnow()
                    result.duration_seconds = (
                        result.completed_at - result.started_at
                    ).total_seconds()
                    
                    self._stats["total_failed"] += 1
                    
                    logger.error(
                        f"[{execution_id}] Failed permanently after "
                        f"{retry_count} retries"
                    )
                    
                    break
        
        # Store history
        if self.config.store_execution_history:
            self._execution_history[execution_id] = result
        
        return result
    
    async def _execute_with_progress(
        self,
        job_func: Callable,
        job_args: Dict[str, Any],
        progress_callback: Optional[Callable]
    ) -> Any:
        """Execute job with progress tracking"""
        # Add progress callback to args if enabled
        if self.config.enable_progress_tracking and progress_callback:
            job_args = {
                **job_args,
                "_progress_callback": progress_callback
            }
        
        # Execute
        if asyncio.iscoroutinefunction(job_func):
            return await job_func(**job_args)
        else:
            # Run sync function in executor
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: job_func(**job_args))
    
    def _calculate_retry_delay(
        self,
        retry_count: int,
        strategy: RetryStrategy
    ) -> float:
        """Calculate retry delay based on strategy"""
        base_delay = self.config.base_retry_delay_seconds
        max_delay = self.config.max_retry_delay_seconds
        
        if strategy == RetryStrategy.NONE:
            return 0
        
        elif strategy == RetryStrategy.FIXED_DELAY:
            return min(base_delay, max_delay)
        
        elif strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            # 2^retry_count * base_delay
            delay = base_delay * (2 ** (retry_count - 1))
            return min(delay, max_delay)
        
        elif strategy == RetryStrategy.LINEAR_BACKOFF:
            # retry_count * base_delay
            delay = base_delay * retry_count
            return min(delay, max_delay)
        
        return base_delay
    
    async def execute_batch(
        self,
        jobs: List[Dict[str, Any]],
        fail_fast: bool = False
    ) -> List[ExecutionResult]:
        """
        Execute multiple jobs
        
        Args:
            jobs: List of job definitions with func, args, etc.
            fail_fast: Stop on first failure
        
        Returns:
            List of execution results
        """
        tasks = []
        
        for job in jobs:
            task = asyncio.create_task(
                self.execute(
                    job_func=job["func"],
                    job_args=job.get("args"),
                    job_id=job.get("id"),
                    max_retries=job.get("max_retries"),
                    timeout=job.get("timeout"),
                    progress_callback=job.get("progress_callback")
                )
            )
            tasks.append(task)
        
        # Wait for all or first failure
        if fail_fast:
            # Stop on first exception
            results = []
            for task in asyncio.as_completed(tasks):
                result = await task
                results.append(result)
                
                if result.status == ExecutionStatus.FAILED:
                    # Cancel remaining
                    for t in tasks:
                        if not t.done():
                            t.cancel()
                    break
            
            return results
        else:
            # Wait for all
            return await asyncio.gather(*tasks, return_exceptions=False)
    
    async def cancel_execution(self, execution_id: str):
        """Cancel active execution"""
        task = self._active_executions.get(execution_id)
        
        if not task:
            raise ValueError(f"No active execution: {execution_id}")
        
        task.cancel()
        
        logger.info(f"Cancelled execution: {execution_id}")
    
    def get_active_executions(self) -> List[str]:
        """Get list of active execution IDs"""
        return list(self._active_executions.keys())
    
    def get_execution_result(
        self,
        execution_id: str
    ) -> Optional[ExecutionResult]:
        """Get execution result from history"""
        return self._execution_history.get(execution_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get executor statistics"""
        return {
            "active_executions": len(self._active_executions),
            "history_size": len(self._execution_history),
            "statistics": self._stats,
            "concurrent_limit": self.config.max_concurrent_jobs
        }
    
    async def clean_history(self):
        """Clean old execution history"""
        if not self.config.store_execution_history:
            return
        
        cutoff = datetime.utcnow() - timedelta(
            days=self.config.history_retention_days
        )
        
        removed = 0
        for exec_id, result in list(self._execution_history.items()):
            if result.completed_at and result.completed_at < cutoff:
                del self._execution_history[exec_id]
                removed += 1
        
        logger.info(f"Cleaned {removed} old execution records")
        return removed
    
    async def wait_all(self):
        """Wait for all active executions to complete"""
        if not self._active_executions:
            return
        
        logger.info(f"Waiting for {len(self._active_executions)} executions...")
        
        await asyncio.gather(
            *self._active_executions.values(),
            return_exceptions=True
        )
        
        logger.info("All executions completed")
