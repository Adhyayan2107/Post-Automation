import pytest
from uuid import UUID, uuid4
from datetime import datetime, timezone
from core.models.raw_content import RawContent
from core.models.post import Post, PostStatus
from core.models.schedule_slot import ScheduleSlot


class TestRawContent:
    def test_defaults_populated(self):
        run_id = uuid4()
        rc = RawContent(url="https://example.com", title="Test", source="news", run_id=run_id)
        assert isinstance(rc.id, UUID)
        assert isinstance(rc.scraped_at, datetime)
        assert rc.scraped_at.tzinfo is not None
        assert rc.body == ""
        assert rc.run_id == run_id

    def test_fields_stored(self):
        run_id = uuid4()
        rc = RawContent(
            url="https://ibo.org/article",
            title="IB News",
            body="Some body text",
            source="ib_official",
            run_id=run_id,
        )
        assert rc.url == "https://ibo.org/article"
        assert rc.title == "IB News"
        assert rc.body == "Some body text"
        assert rc.source == "ib_official"


class TestPost:
    def test_defaults_populated(self):
        run_id = uuid4()
        post = Post(title="Test Post", body="Body text", post_type="educational", run_id=run_id)
        assert isinstance(post.id, UUID)
        assert isinstance(post.created_at, datetime)
        assert post.status == PostStatus.PENDING
        assert post.source_urls == []
        assert post.target_platforms == []
        assert post.target_subreddits == []
        assert post.creative_angle is None
        assert post.image_url is None
        assert post.scheduled_at is None
        assert post.published_at is None

    def test_post_status_enum_values(self):
        assert PostStatus.PENDING == "pending"
        assert PostStatus.APPROVED == "approved"
        assert PostStatus.REJECTED == "rejected"
        assert PostStatus.SCHEDULED == "scheduled"
        assert PostStatus.PUBLISHED == "published"
        assert PostStatus.FAILED == "failed"

    def test_creative_post_fields(self):
        run_id = uuid4()
        post = Post(
            title="Naruto and the French Revolution",
            body="Body",
            post_type="creative",
            creative_angle="anime",
            run_id=run_id,
            target_platforms=["reddit", "discord"],
            target_subreddits=["r/IBO", "r/igcse"],
        )
        assert post.post_type == "creative"
        assert post.creative_angle == "anime"
        assert "reddit" in post.target_platforms
        assert "r/IBO" in post.target_subreddits


class TestScheduleSlot:
    def test_fields_stored(self):
        post_id = uuid4()
        now = datetime.now(timezone.utc)
        slot = ScheduleSlot(post_id=post_id, platform="reddit", scheduled_at=now)
        assert slot.post_id == post_id
        assert slot.platform == "reddit"
        assert slot.scheduled_at == now
        assert slot.calendar_event_id is None

    def test_with_calendar_event(self):
        slot = ScheduleSlot(
            post_id=uuid4(),
            platform="discord",
            scheduled_at=datetime.now(timezone.utc),
            calendar_event_id="abc123",
        )
        assert slot.calendar_event_id == "abc123"
