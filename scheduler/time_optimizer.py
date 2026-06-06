from datetime import datetime, timedelta, timezone
from typing import List
from core.models.post import Post
from core.models.schedule_slot import ScheduleSlot
from config.logging import get_logger

logger = get_logger(__name__)

# Best UTC posting times per platform per weekday (0=Mon … 6=Sun)
REDDIT_SLOTS: dict[int, list[int]] = {
    0: [8],
    1: [12],
    2: [18],
    3: [8],
    4: [12],
    5: [10],
    6: [16],
}

DISCORD_SLOTS: dict[int, list[int]] = {
    0: [16],
    1: [16],
    2: [20],
    3: [16],
    4: [17],
    5: [12],
    6: [18],
}

MIN_GAP_HOURS = 4


def _candidate_slots(platform: str, reference: datetime) -> List[datetime]:
    """Return all weekly slots for a platform starting from reference week."""
    table = REDDIT_SLOTS if platform == "reddit" else DISCORD_SLOTS
    monday = reference - timedelta(days=reference.weekday())
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    slots = []
    for day_offset, hours in table.items():
        for hour in hours:
            dt = monday + timedelta(days=day_offset, hours=hour)
            slots.append(dt.replace(tzinfo=timezone.utc))
    slots.sort()
    return slots


class TimeOptimizer:
    def get_slots_for_week(self, posts: List[Post]) -> List[ScheduleSlot]:
        if not posts:
            return []

        now = datetime.now(timezone.utc)
        used: dict[str, List[datetime]] = {"reddit": [], "discord": []}
        result: List[ScheduleSlot] = []

        for post in posts:
            platforms = post.target_platforms or ["reddit", "discord"]
            for platform in platforms:
                slot_time = self._next_available(platform, now, used[platform])
                if slot_time is None:
                    logger.warning("No available slot for post %s on %s", post.id, platform)
                    continue
                used[platform].append(slot_time)
                result.append(ScheduleSlot(
                    post_id=post.id,
                    platform=platform,
                    scheduled_at=slot_time,
                ))
                logger.info("Assigned %s → %s @ %s", post.id, platform, slot_time.isoformat())

        return result

    def _next_available(
        self,
        platform: str,
        reference: datetime,
        used: List[datetime],
    ) -> datetime | None:
        candidates = _candidate_slots(platform, reference)
        # also check next week if this week is full
        next_week = reference + timedelta(weeks=1)
        candidates += _candidate_slots(platform, next_week)

        for candidate in candidates:
            if candidate <= reference:
                continue
            if self._conflicts(candidate, used):
                continue
            return candidate

        return None

    def _conflicts(self, candidate: datetime, used: List[datetime]) -> bool:
        for taken in used:
            if abs((candidate - taken).total_seconds()) < MIN_GAP_HOURS * 3600:
                return True
        return False
