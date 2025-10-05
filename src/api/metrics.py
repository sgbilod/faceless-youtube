"""
Custom Prometheus metrics for application monitoring

Tracks:
- Video generation requests and durations
- Script generation performance
- Active job counts
- Error rates
- API performance

Metrics are exposed at /metrics endpoint and can be scraped by Prometheus.
"""

from prometheus_client import Counter, Histogram, Gauge, Info
import time
from functools import wraps
from typing import Callable, Any
import asyncio

# ============================================================================
# REQUEST COUNTERS
# ============================================================================

video_generation_requests = Counter(
    'video_generation_requests_total',
    'Total video generation requests',
    ['status', 'niche']  # Labels: success/failure, meditation/affirmation/etc
)

script_generation_requests = Counter(
    'script_generation_requests_total',
    'Total script generation requests',
    ['status', 'niche']
)

api_requests_total = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status_code']
)

# ============================================================================
# DURATION HISTOGRAMS
# ============================================================================

video_generation_duration = Histogram(
    'video_generation_duration_seconds',
    'Time spent generating videos (end-to-end)',
    buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1200]  # 1s to 20min
)

script_generation_duration = Histogram(
    'script_generation_duration_seconds',
    'Time spent generating scripts with AI',
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60]  # 100ms to 1min
)

asset_download_duration = Histogram(
    'asset_download_duration_seconds',
    'Time spent downloading video/audio assets',
    buckets=[0.5, 1, 2, 5, 10, 30, 60, 120]  # 500ms to 2min
)

video_rendering_duration = Histogram(
    'video_rendering_duration_seconds',
    'Time spent rendering final video',
    buckets=[5, 10, 30, 60, 120, 300, 600]  # 5s to 10min
)

youtube_upload_duration = Histogram(
    'youtube_upload_duration_seconds',
    'Time spent uploading to YouTube',
    buckets=[10, 30, 60, 120, 300, 600, 1200]  # 10s to 20min
)

# ============================================================================
# GAUGES (CURRENT STATE)
# ============================================================================

active_video_jobs = Gauge(
    'active_video_jobs',
    'Number of currently active video generation jobs'
)

active_script_generations = Gauge(
    'active_script_generations',
    'Number of currently active script generation tasks'
)

queue_depth = Gauge(
    'queue_depth',
    'Number of jobs waiting in queue',
    ['queue_type']  # video_generation, upload, etc.
)

cache_hit_rate = Gauge(
    'cache_hit_rate',
    'Cache hit rate (0-1)',
    ['cache_type']  # redis, local, etc.
)

# ============================================================================
# INFO METRICS
# ============================================================================

app_info = Info(
    'faceless_youtube_app',
    'Application information'
)

# Set application info (call once at startup)
app_info.info({
    'version': '2.0.0',
    'python_version': '3.13',
    'environment': 'production'
})

# ============================================================================
# DECORATOR UTILITIES
# ============================================================================


def track_video_generation(func: Callable) -> Callable:
    """
    Decorator to track video generation metrics
    
    Usage:
        @track_video_generation
        async def generate_video(script, niche):
            ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        active_video_jobs.inc()
        start_time = time.time()
        
        # Extract niche from kwargs or args
        niche = kwargs.get('niche', 'unknown')
        
        try:
            result = await func(*args, **kwargs)
            
            # Track success
            video_generation_requests.labels(
                status='success',
                niche=niche
            ).inc()
            
            return result
            
        except Exception as e:
            # Track failure
            video_generation_requests.labels(
                status='failure',
                niche=niche
            ).inc()
            raise
            
        finally:
            duration = time.time() - start_time
            video_generation_duration.observe(duration)
            active_video_jobs.dec()
    
    return wrapper


def track_script_generation(func: Callable) -> Callable:
    """
    Decorator to track script generation metrics
    
    Usage:
        @track_script_generation
        async def generate_script(prompt, niche):
            ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        active_script_generations.inc()
        start_time = time.time()
        
        niche = kwargs.get('niche', 'unknown')
        
        try:
            result = await func(*args, **kwargs)
            
            script_generation_requests.labels(
                status='success',
                niche=niche
            ).inc()
            
            return result
            
        except Exception as e:
            script_generation_requests.labels(
                status='failure',
                niche=niche
            ).inc()
            raise
            
        finally:
            duration = time.time() - start_time
            script_generation_duration.observe(duration)
            active_script_generations.dec()
    
    return wrapper


def track_duration(histogram: Histogram) -> Callable:
    """
    Generic decorator to track function duration
    
    Args:
        histogram: Prometheus Histogram to record duration
        
    Usage:
        @track_duration(asset_download_duration)
        async def download_asset(url):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = time.time() - start_time
                histogram.observe(duration)
        return wrapper
    return decorator


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def update_queue_depth(queue_type: str, depth: int) -> None:
    """
    Update queue depth gauge
    
    Args:
        queue_type: Type of queue (video_generation, upload, etc.)
        depth: Current depth
    """
    queue_depth.labels(queue_type=queue_type).set(depth)


def update_cache_hit_rate(cache_type: str, hit_rate: float) -> None:
    """
    Update cache hit rate gauge
    
    Args:
        cache_type: Type of cache (redis, local, etc.)
        hit_rate: Hit rate between 0 and 1
    """
    cache_hit_rate.labels(cache_type=cache_type).set(hit_rate)
