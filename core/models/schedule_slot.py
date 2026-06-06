from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from typing import Optional


@dataclass
class ScheduleSlot:
    post_id: UUID
    platform: str
    scheduled_at: datetime
    calendar_event_id: Optional[str] = None
