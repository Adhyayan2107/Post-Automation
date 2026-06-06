import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from scheduler.time_optimizer import TimeOptimizer, MIN_GAP_HOURS
from core.models.post import Post
from core.models.schedule_slot import ScheduleSlot


def _make_post(platforms: list[str] | None = None) -> Post:
    return Post(
        title="Test Post",
        body="Body",
        post_type="educational",
        run_id=uuid4(),
        target_platforms=platforms or ["reddit", "discord"],
    )


def _monday_ref() -> datetime:
    """Return a Monday 00:00 UTC in the near future."""
    now = datetime.now(timezone.utc)
    days_until_monday = (7 - now.weekday()) % 7 or 7
    return (now + timedelta(days=days_until_monday)).replace(hour=0, minute=0, second=0, microsecond=0)


class TestTimeOptimizer:
    def test_returns_slots_for_each_platform(self):
        optimizer = TimeOptimizer()
        posts = [_make_post(["reddit", "discord"])]
        slots = optimizer.get_slots_for_week(posts)
        platforms = {s.platform for s in slots}
        assert "reddit" in platforms
        assert "discord" in platforms

    def test_no_two_reddit_slots_within_gap(self):
        optimizer = TimeOptimizer()
        posts = [_make_post(["reddit"]) for _ in range(5)]
        slots = optimizer.get_slots_for_week(posts)
        reddit_slots = sorted([s.scheduled_at for s in slots if s.platform == "reddit"])
        for a, b in zip(reddit_slots, reddit_slots[1:]):
            gap = (b - a).total_seconds() / 3600
            assert gap >= MIN_GAP_HOURS, f"Gap too small: {gap}h between {a} and {b}"

    def test_no_two_discord_slots_within_gap(self):
        optimizer = TimeOptimizer()
        posts = [_make_post(["discord"]) for _ in range(5)]
        slots = optimizer.get_slots_for_week(posts)
        discord_slots = sorted([s.scheduled_at for s in slots if s.platform == "discord"])
        for a, b in zip(discord_slots, discord_slots[1:]):
            gap = (b - a).total_seconds() / 3600
            assert gap >= MIN_GAP_HOURS

    def test_all_slots_are_in_future(self):
        optimizer = TimeOptimizer()
        posts = [_make_post() for _ in range(4)]
        slots = optimizer.get_slots_for_week(posts)
        now = datetime.now(timezone.utc)
        for slot in slots:
            assert slot.scheduled_at > now

    def test_slot_post_id_matches(self):
        optimizer = TimeOptimizer()
        post = _make_post(["reddit"])
        slots = optimizer.get_slots_for_week([post])
        reddit_slots = [s for s in slots if s.platform == "reddit"]
        assert len(reddit_slots) == 1
        assert reddit_slots[0].post_id == post.id

    def test_empty_posts_returns_empty(self):
        optimizer = TimeOptimizer()
        assert optimizer.get_slots_for_week([]) == []

    def test_single_platform_post_gets_one_slot(self):
        optimizer = TimeOptimizer()
        post = _make_post(["reddit"])
        slots = optimizer.get_slots_for_week([post])
        assert len(slots) == 1
        assert slots[0].platform == "reddit"

    def test_slots_on_correct_weekday_hours(self):
        from scheduler.time_optimizer import REDDIT_SLOTS
        optimizer = TimeOptimizer()
        post = _make_post(["reddit"])
        slots = optimizer.get_slots_for_week([post])
        for slot in slots:
            day = slot.scheduled_at.weekday()
            hour = slot.scheduled_at.hour
            assert hour in REDDIT_SLOTS[day], f"Hour {hour} not valid for Reddit on day {day}"
