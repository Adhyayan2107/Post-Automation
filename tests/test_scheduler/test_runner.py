import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from core.models.post import Post, PostStatus


def _make_post(status: PostStatus = PostStatus.SCHEDULED, platforms: list[str] | None = None) -> Post:
    post = Post(
        title="Test",
        body="Body",
        post_type="educational",
        run_id=uuid4(),
        status=status,
        target_platforms=platforms or ["reddit", "discord"],
        scheduled_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    return post


def _make_repo(posts: list[Post]) -> MagicMock:
    repo = MagicMock()
    repo.get_by_status = AsyncMock(return_value=posts)
    repo.get_by_id = AsyncMock(side_effect=lambda id: next((p for p in posts if p.id == id), None))
    repo.update_status = AsyncMock()
    return repo


def _make_publisher(success: bool = True) -> MagicMock:
    pub = MagicMock()
    pub.publish = AsyncMock(return_value=success)
    return pub


def _make_mock_scheduler() -> MagicMock:
    sched = MagicMock()
    sched.get_job = MagicMock(return_value=None)
    sched.add_job = MagicMock()
    sched.start = MagicMock()
    sched.shutdown = MagicMock()
    return sched


class TestSchedulerRunner:
    @pytest.mark.asyncio
    async def test_start_loads_scheduled_posts(self):
        from scheduler.runner import SchedulerRunner
        post = _make_post(PostStatus.SCHEDULED)
        repo = _make_repo([post])
        sched = _make_mock_scheduler()

        runner = SchedulerRunner(
            post_repository=repo,
            publishers={},
            scheduler=sched,
        )
        await runner.start()

        repo.get_by_status.assert_awaited_with(PostStatus.SCHEDULED)
        sched.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_registers_job_for_each_scheduled_post(self):
        from scheduler.runner import SchedulerRunner
        posts = [_make_post(PostStatus.SCHEDULED) for _ in range(3)]
        repo = _make_repo(posts)
        sched = _make_mock_scheduler()

        runner = SchedulerRunner(post_repository=repo, publishers={}, scheduler=sched)
        await runner.start()

        assert sched.add_job.call_count >= 3  # 3 post jobs + 1 poll job

    @pytest.mark.asyncio
    async def test_publish_post_calls_all_publishers(self):
        from scheduler.runner import SchedulerRunner
        post = _make_post(PostStatus.SCHEDULED, ["reddit", "discord"])
        repo = _make_repo([post])
        reddit_pub = _make_publisher(True)
        discord_pub = _make_publisher(True)
        sched = _make_mock_scheduler()

        runner = SchedulerRunner(
            post_repository=repo,
            publishers={"reddit": reddit_pub, "discord": discord_pub},
            scheduler=sched,
        )
        await runner._publish_post(post.id)

        reddit_pub.publish.assert_awaited_once_with(post)
        discord_pub.publish.assert_awaited_once_with(post)

    @pytest.mark.asyncio
    async def test_publish_post_marks_published_on_success(self):
        from scheduler.runner import SchedulerRunner
        post = _make_post(PostStatus.SCHEDULED, ["reddit"])
        repo = _make_repo([post])
        sched = _make_mock_scheduler()

        runner = SchedulerRunner(
            post_repository=repo,
            publishers={"reddit": _make_publisher(True)},
            scheduler=sched,
        )
        await runner._publish_post(post.id)

        repo.update_status.assert_awaited_with(post.id, PostStatus.PUBLISHED)

    @pytest.mark.asyncio
    async def test_publish_post_marks_failed_on_publisher_false(self):
        from scheduler.runner import SchedulerRunner
        post = _make_post(PostStatus.SCHEDULED, ["reddit"])
        repo = _make_repo([post])
        sched = _make_mock_scheduler()

        runner = SchedulerRunner(
            post_repository=repo,
            publishers={"reddit": _make_publisher(False)},
            scheduler=sched,
        )
        await runner._publish_post(post.id)

        repo.update_status.assert_awaited_with(post.id, PostStatus.FAILED)

    @pytest.mark.asyncio
    async def test_publish_post_marks_failed_on_exception(self):
        from scheduler.runner import SchedulerRunner
        post = _make_post(PostStatus.SCHEDULED, ["reddit"])
        repo = _make_repo([post])
        sched = _make_mock_scheduler()

        failing_pub = MagicMock()
        failing_pub.publish = AsyncMock(side_effect=Exception("Network error"))

        runner = SchedulerRunner(
            post_repository=repo,
            publishers={"reddit": failing_pub},
            scheduler=sched,
        )
        await runner._publish_post(post.id)

        repo.update_status.assert_awaited_with(post.id, PostStatus.FAILED)

    @pytest.mark.asyncio
    async def test_publish_post_handles_missing_post(self):
        from scheduler.runner import SchedulerRunner
        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=None)
        repo.update_status = AsyncMock()
        sched = _make_mock_scheduler()

        runner = SchedulerRunner(post_repository=repo, publishers={}, scheduler=sched)
        # Should not raise
        await runner._publish_post(uuid4())
        repo.update_status.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_poll_schedules_approved_posts(self):
        from scheduler.runner import SchedulerRunner
        post = _make_post(PostStatus.APPROVED)
        repo = _make_repo([post])
        sched = _make_mock_scheduler()

        mock_optimizer = MagicMock()
        mock_optimizer.get_slots_for_week = MagicMock(return_value=[])
        mock_calendar = MagicMock()

        runner = SchedulerRunner(
            post_repository=repo,
            publishers={},
            calendar_scheduler=mock_calendar,
            time_optimizer=mock_optimizer,
            scheduler=sched,
        )
        await runner._poll_for_new_approvals()

        repo.get_by_status.assert_awaited_with(PostStatus.APPROVED)
