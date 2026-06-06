import pytest
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import MagicMock
from core.models.post import Post
from core.models.schedule_slot import ScheduleSlot


def _make_post() -> Post:
    return Post(
        title="IB Chemistry Tips",
        body="Here are some tips for HL Chemistry paper 2.",
        post_type="educational",
        run_id=uuid4(),
    )


def _make_slot(platform: str = "reddit") -> ScheduleSlot:
    return ScheduleSlot(
        post_id=uuid4(),
        platform=platform,
        scheduled_at=datetime(2026, 6, 9, 8, 0, tzinfo=timezone.utc),
    )


def _make_mock_service(event_id: str = "evt_abc123") -> MagicMock:
    mock_event = {"id": event_id}
    mock_insert = MagicMock()
    mock_insert.execute.return_value = mock_event
    mock_events = MagicMock()
    mock_events.insert.return_value = mock_insert
    mock_delete = MagicMock()
    mock_delete.execute.return_value = None
    mock_events.delete.return_value = mock_delete
    service = MagicMock()
    service.events.return_value = mock_events
    return service


class TestGoogleCalendarScheduler:
    def test_create_event_returns_event_id(self):
        from scheduler.google_calendar import GoogleCalendarScheduler
        service = _make_mock_service("evt_123")
        scheduler = GoogleCalendarScheduler(service=service)
        post = _make_post()
        slot = _make_slot("reddit")

        event_id = scheduler.create_event(slot, post)
        assert event_id == "evt_123"

    def test_create_event_title_format(self):
        from scheduler.google_calendar import GoogleCalendarScheduler
        service = _make_mock_service()
        scheduler = GoogleCalendarScheduler(service=service)
        post = _make_post()
        slot = _make_slot()

        scheduler.create_event(slot, post)

        call_kwargs = service.events().insert.call_args
        body = call_kwargs.kwargs["body"] if call_kwargs.kwargs else call_kwargs[1]["body"]
        assert body["summary"] == f"[EDUBOT] {post.title}"

    def test_create_event_description_contains_post_id(self):
        from scheduler.google_calendar import GoogleCalendarScheduler
        service = _make_mock_service()
        scheduler = GoogleCalendarScheduler(service=service)
        post = _make_post()
        slot = _make_slot()

        scheduler.create_event(slot, post)

        call_kwargs = service.events().insert.call_args
        body = call_kwargs.kwargs["body"] if call_kwargs.kwargs else call_kwargs[1]["body"]
        assert str(post.id) in body["description"]

    def test_reddit_event_uses_green_colour(self):
        from scheduler.google_calendar import GoogleCalendarScheduler, PLATFORM_COLOURS
        service = _make_mock_service()
        scheduler = GoogleCalendarScheduler(service=service)
        post = _make_post()
        slot = _make_slot("reddit")

        scheduler.create_event(slot, post)

        call_kwargs = service.events().insert.call_args
        body = call_kwargs.kwargs["body"] if call_kwargs.kwargs else call_kwargs[1]["body"]
        assert body["colorId"] == PLATFORM_COLOURS["reddit"]

    def test_discord_event_uses_blue_colour(self):
        from scheduler.google_calendar import GoogleCalendarScheduler, PLATFORM_COLOURS
        service = _make_mock_service()
        scheduler = GoogleCalendarScheduler(service=service)
        post = _make_post()
        slot = _make_slot("discord")

        scheduler.create_event(slot, post)

        call_kwargs = service.events().insert.call_args
        body = call_kwargs.kwargs["body"] if call_kwargs.kwargs else call_kwargs[1]["body"]
        assert body["colorId"] == PLATFORM_COLOURS["discord"]

    def test_delete_event_calls_api(self):
        from scheduler.google_calendar import GoogleCalendarScheduler
        service = _make_mock_service()
        scheduler = GoogleCalendarScheduler(service=service)

        scheduler.delete_event("evt_to_delete")

        service.events().delete.assert_called_once()
