"""
Calendar Manager

Content calendar and planning system:
- Visual calendar representation
- Content slot management
- Conflict detection
- Schedule optimization
- Calendar views (day/week/month)
"""

import logging
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass
from datetime import datetime, timedelta, date
from enum import Enum
from uuid import uuid4
from collections import defaultdict

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class CalendarView(str, Enum):
    """Calendar view types"""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class ContentSlotStatus(str, Enum):
    """Content slot status"""
    AVAILABLE = "available"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    CONFLICT = "conflict"
    RESERVED = "reserved"


@dataclass
class CalendarConfig:
    """Calendar configuration"""
    default_view: CalendarView = CalendarView.WEEK
    timezone: str = "UTC"
    
    # Slot settings
    slot_duration_minutes: int = 5  # Default video duration
    min_gap_hours: int = 6  # Minimum gap between videos
    max_videos_per_day: int = 3
    
    # Publishing windows
    preferred_hours: List[int] = None  # e.g., [10, 14, 18] for 10AM, 2PM, 6PM
    blackout_days: List[date] = None  # Days to avoid
    
    # Conflict detection
    detect_topic_conflicts: bool = True
    topic_similarity_threshold: float = 0.7


class ContentSlot(BaseModel):
    """Content slot in calendar"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    scheduled_at: datetime
    duration_minutes: int = 5
    
    # Status
    status: ContentSlotStatus = ContentSlotStatus.AVAILABLE
    
    # Content
    job_id: Optional[str] = None
    topic: Optional[str] = None
    style: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    
    # Publishing
    publish_at: Optional[datetime] = None
    video_id: Optional[str] = None
    youtube_url: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None


class CalendarEntry(BaseModel):
    """Calendar entry for display"""
    date: date
    slots: List[ContentSlot]
    total_slots: int
    available_slots: int
    scheduled_slots: int
    published_slots: int
    conflict_slots: int
    
    # Statistics
    total_duration_minutes: int = 0
    utilization_percent: float = 0.0


class CalendarManager:
    """
    Content calendar and planning manager
    
    Features:
    - Visual calendar with content slots
    - Conflict detection (time, topic similarity)
    - Optimal scheduling suggestions
    - Multi-view support (day/week/month/year)
    - Content gap analysis
    - Publishing window enforcement
    - Batch scheduling optimization
    
    Example:
        manager = CalendarManager(config=CalendarConfig())
        
        # Reserve slot for video
        slot = await manager.reserve_slot(
            scheduled_at=tomorrow_10am,
            topic="Python Functions",
            duration_minutes=5
        )
        
        # Get week view
        week_view = await manager.get_week_view(start_date=today)
        
        # Find optimal slots
        suggestions = await manager.suggest_optimal_slots(
            count=3,
            preferred_days=[DayOfWeek.MONDAY, DayOfWeek.WEDNESDAY]
        )
        
        # Detect conflicts
        conflicts = await manager.detect_conflicts()
    """
    
    def __init__(self, config: Optional[CalendarConfig] = None):
        self.config = config or CalendarConfig()
        
        # Set defaults if not provided
        if self.config.preferred_hours is None:
            self.config.preferred_hours = [10, 14, 18]  # 10AM, 2PM, 6PM
        
        if self.config.blackout_days is None:
            self.config.blackout_days = []
        
        # Slot storage
        self._slots: Dict[str, ContentSlot] = {}
        self._slots_by_date: Dict[date, List[ContentSlot]] = defaultdict(list)
        
        # Statistics
        self._stats = {
            "total_slots": 0,
            "reserved_slots": 0,
            "conflicts_detected": 0,
            "suggestions_generated": 0
        }
    
    async def reserve_slot(
        self,
        scheduled_at: datetime,
        topic: str,
        duration_minutes: Optional[int] = None,
        style: str = "educational",
        tags: Optional[List[str]] = None,
        job_id: Optional[str] = None,
        publish_at: Optional[datetime] = None,
        notes: Optional[str] = None
    ) -> ContentSlot:
        """
        Reserve calendar slot
        
        Args:
            scheduled_at: When to schedule
            topic: Video topic
            duration_minutes: Video duration
            style: Content style
            tags: Video tags
            job_id: Associated job ID
            publish_at: When to publish
            notes: Additional notes
        
        Returns:
            Created content slot
        """
        duration = duration_minutes or self.config.slot_duration_minutes
        
        # Check conflicts
        conflicts = await self._check_time_conflicts(scheduled_at, duration)
        
        slot = ContentSlot(
            scheduled_at=scheduled_at,
            duration_minutes=duration,
            status=ContentSlotStatus.CONFLICT if conflicts else ContentSlotStatus.RESERVED,
            job_id=job_id,
            topic=topic,
            style=style,
            tags=tags or [],
            publish_at=publish_at,
            notes=notes
        )
        
        # Store slot
        self._slots[slot.id] = slot
        self._slots_by_date[scheduled_at.date()].append(slot)
        
        self._stats["total_slots"] += 1
        self._stats["reserved_slots"] += 1
        
        if conflicts:
            self._stats["conflicts_detected"] += 1
            logger.warning(
                f"Slot has conflicts: {slot.id} at {scheduled_at} - {conflicts}"
            )
        else:
            logger.info(f"Reserved slot: {slot.id} - {topic} at {scheduled_at}")
        
        return slot
    
    async def _check_time_conflicts(
        self,
        scheduled_at: datetime,
        duration_minutes: int
    ) -> List[str]:
        """Check for time-based conflicts"""
        conflicts = []
        slot_date = scheduled_at.date()
        
        # Check slots on same day
        existing_slots = self._slots_by_date.get(slot_date, [])
        
        for existing in existing_slots:
            # Calculate time gap
            time_diff = abs((scheduled_at - existing.scheduled_at).total_seconds() / 3600)
            
            if time_diff < self.config.min_gap_hours:
                conflicts.append(
                    f"Too close to slot {existing.id} ({time_diff:.1f}h gap)"
                )
        
        # Check daily limit
        if len(existing_slots) >= self.config.max_videos_per_day:
            conflicts.append(
                f"Max videos per day reached ({self.config.max_videos_per_day})"
            )
        
        # Check blackout days
        if slot_date in self.config.blackout_days:
            conflicts.append(f"Date is in blackout list")
        
        # Check preferred hours
        if self.config.preferred_hours:
            if scheduled_at.hour not in self.config.preferred_hours:
                conflicts.append(
                    f"Not in preferred hours: {self.config.preferred_hours}"
                )
        
        return conflicts
    
    async def update_slot_status(
        self,
        slot_id: str,
        status: ContentSlotStatus,
        video_id: Optional[str] = None,
        youtube_url: Optional[str] = None
    ):
        """Update slot status"""
        slot = self._slots.get(slot_id)
        
        if not slot:
            raise ValueError(f"Slot not found: {slot_id}")
        
        old_status = slot.status
        slot.status = status
        
        if video_id:
            slot.video_id = video_id
        
        if youtube_url:
            slot.youtube_url = youtube_url
        
        logger.info(
            f"Updated slot {slot_id}: {old_status} -> {status}"
        )
    
    async def get_day_view(
        self,
        target_date: date
    ) -> CalendarEntry:
        """Get calendar view for single day"""
        slots = self._slots_by_date.get(target_date, [])
        
        return self._build_calendar_entry(target_date, slots)
    
    async def get_week_view(
        self,
        start_date: date
    ) -> List[CalendarEntry]:
        """Get calendar view for week"""
        entries = []
        
        for i in range(7):
            day = start_date + timedelta(days=i)
            entry = await self.get_day_view(day)
            entries.append(entry)
        
        return entries
    
    async def get_month_view(
        self,
        year: int,
        month: int
    ) -> List[CalendarEntry]:
        """Get calendar view for month"""
        entries = []
        
        # Get first day of month
        first_day = date(year, month, 1)
        
        # Get last day of month
        if month == 12:
            last_day = date(year, 12, 31)
        else:
            last_day = date(year, month + 1, 1) - timedelta(days=1)
        
        # Generate entries
        current = first_day
        while current <= last_day:
            entry = await self.get_day_view(current)
            entries.append(entry)
            current += timedelta(days=1)
        
        return entries
    
    def _build_calendar_entry(
        self,
        target_date: date,
        slots: List[ContentSlot]
    ) -> CalendarEntry:
        """Build calendar entry from slots"""
        # Count by status
        status_counts = defaultdict(int)
        for slot in slots:
            status_counts[slot.status] += 1
        
        # Calculate statistics
        total_duration = sum(s.duration_minutes for s in slots)
        
        # Utilization (assuming 8 hours workday = 480 minutes)
        max_capacity = 480  # minutes
        utilization = (total_duration / max_capacity * 100) if total_duration else 0
        
        return CalendarEntry(
            date=target_date,
            slots=sorted(slots, key=lambda s: s.scheduled_at),
            total_slots=len(slots),
            available_slots=status_counts[ContentSlotStatus.AVAILABLE],
            scheduled_slots=status_counts[ContentSlotStatus.SCHEDULED],
            published_slots=status_counts[ContentSlotStatus.PUBLISHED],
            conflict_slots=status_counts[ContentSlotStatus.CONFLICT],
            total_duration_minutes=total_duration,
            utilization_percent=round(utilization, 2)
        )
    
    async def suggest_optimal_slots(
        self,
        count: int,
        start_date: Optional[date] = None,
        days: int = 30,
        preferred_hours: Optional[List[int]] = None
    ) -> List[datetime]:
        """
        Suggest optimal time slots
        
        Args:
            count: Number of slots to suggest
            start_date: Start searching from this date
            days: Search window in days
            preferred_hours: Override preferred hours
        
        Returns:
            List of suggested datetimes
        """
        start = start_date or date.today()
        hours = preferred_hours or self.config.preferred_hours
        suggestions = []
        
        # Search for available slots
        for day_offset in range(days):
            current_date = start + timedelta(days=day_offset)
            
            # Skip blackout days
            if current_date in self.config.blackout_days:
                continue
            
            # Check existing slots
            existing = self._slots_by_date.get(current_date, [])
            
            # Skip if at capacity
            if len(existing) >= self.config.max_videos_per_day:
                continue
            
            # Try preferred hours
            for hour in hours:
                candidate = datetime.combine(current_date, datetime.min.time()).replace(hour=hour)
                
                # Check conflicts
                conflicts = await self._check_time_conflicts(
                    candidate,
                    self.config.slot_duration_minutes
                )
                
                if not conflicts:
                    suggestions.append(candidate)
                    
                    if len(suggestions) >= count:
                        self._stats["suggestions_generated"] += count
                        return suggestions
        
        logger.warning(
            f"Only found {len(suggestions)}/{count} optimal slots in {days} days"
        )
        
        return suggestions
    
    async def detect_conflicts(self) -> List[Dict[str, Any]]:
        """Detect all conflicts in calendar"""
        conflicts = []
        
        for slot in self._slots.values():
            # Time conflicts
            time_conflicts = await self._check_time_conflicts(
                slot.scheduled_at,
                slot.duration_minutes
            )
            
            if time_conflicts:
                conflicts.append({
                    "slot_id": slot.id,
                    "topic": slot.topic,
                    "scheduled_at": slot.scheduled_at,
                    "conflict_type": "time",
                    "details": time_conflicts
                })
            
            # Topic conflicts (if enabled)
            if self.config.detect_topic_conflicts and slot.topic:
                topic_conflicts = await self._check_topic_conflicts(slot)
                
                if topic_conflicts:
                    conflicts.append({
                        "slot_id": slot.id,
                        "topic": slot.topic,
                        "scheduled_at": slot.scheduled_at,
                        "conflict_type": "topic",
                        "details": topic_conflicts
                    })
        
        return conflicts
    
    async def _check_topic_conflicts(self, slot: ContentSlot) -> List[str]:
        """Check for similar topics (basic implementation)"""
        conflicts = []
        
        # Get slots within 7 days
        week_start = slot.scheduled_at.date() - timedelta(days=7)
        week_end = slot.scheduled_at.date() + timedelta(days=7)
        
        for other in self._slots.values():
            if other.id == slot.id:
                continue
            
            if week_start <= other.scheduled_at.date() <= week_end:
                # Simple similarity check (shared words)
                if slot.topic and other.topic:
                    slot_words = set(slot.topic.lower().split())
                    other_words = set(other.topic.lower().split())
                    
                    common = slot_words & other_words
                    total = slot_words | other_words
                    
                    if total:
                        similarity = len(common) / len(total)
                        
                        if similarity >= self.config.topic_similarity_threshold:
                            conflicts.append(
                                f"Similar to '{other.topic}' on {other.scheduled_at.date()} "
                                f"({similarity:.0%} similar)"
                            )
        
        return conflicts
    
    async def get_content_gaps(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Find gaps in content schedule"""
        gaps = []
        current = start_date
        
        while current <= end_date:
            slots = self._slots_by_date.get(current, [])
            
            if not slots and current not in self.config.blackout_days:
                # Gap found
                gap_start = current
                gap_end = current
                
                # Find end of gap
                while gap_end <= end_date:
                    next_day = gap_end + timedelta(days=1)
                    if next_day in self._slots_by_date or next_day in self.config.blackout_days:
                        break
                    gap_end = next_day
                
                gaps.append({
                    "start_date": gap_start,
                    "end_date": gap_end,
                    "days": (gap_end - gap_start).days + 1
                })
                
                current = gap_end + timedelta(days=1)
            else:
                current += timedelta(days=1)
        
        return gaps
    
    def get_slot(self, slot_id: str) -> Optional[ContentSlot]:
        """Get slot by ID"""
        return self._slots.get(slot_id)
    
    def get_all_slots(
        self,
        status_filter: Optional[ContentSlotStatus] = None
    ) -> List[ContentSlot]:
        """Get all slots with optional filter"""
        slots = list(self._slots.values())
        
        if status_filter:
            slots = [s for s in slots if s.status == status_filter]
        
        return sorted(slots, key=lambda s: s.scheduled_at)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get calendar statistics"""
        status_counts = defaultdict(int)
        for slot in self._slots.values():
            status_counts[slot.status.value] += 1
        
        return {
            "total_slots": len(self._slots),
            "status_counts": dict(status_counts),
            "days_with_content": len(self._slots_by_date),
            "statistics": self._stats
        }
    
    async def remove_slot(self, slot_id: str):
        """Remove slot from calendar"""
        slot = self._slots.get(slot_id)
        
        if not slot:
            raise ValueError(f"Slot not found: {slot_id}")
        
        # Remove from date index
        slot_date = slot.scheduled_at.date()
        if slot_date in self._slots_by_date:
            self._slots_by_date[slot_date].remove(slot)
            if not self._slots_by_date[slot_date]:
                del self._slots_by_date[slot_date]
        
        # Remove from main storage
        del self._slots[slot_id]
        
        logger.info(f"Removed slot: {slot_id}")
