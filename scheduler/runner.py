import asyncio
from uuid import UUID

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from core.models.post import Post, PostStatus
from config.logging import get_logger

logger = get_logger(__name__)

POLL_INTERVAL_SECONDS = 300  # 5 minutes


class SchedulerRunner:
    def __init__(
        self,
        post_repository,
        publishers: dict,  # {"reddit": AbstractPublisher, "discord": AbstractPublisher}
        scheduler: AsyncIOScheduler | None = None,
    ) -> None:
        self._repo = post_repository
        self._publishers = publishers
        self._scheduler = scheduler or AsyncIOScheduler()

    async def start(self) -> None:
        await self._load_existing_jobs()
        self._scheduler.add_job(
            self._poll_for_approved,
            "interval",
            seconds=POLL_INTERVAL_SECONDS,
            id="poll_approvals",
            replace_existing=True,
        )
        self._scheduler.start()
        logger.info("SchedulerRunner started")

    def stop(self) -> None:
        self._scheduler.shutdown()
        logger.info("SchedulerRunner stopped")

    async def _load_existing_jobs(self) -> None:
        approved_posts = await self._repo.get_by_status(PostStatus.APPROVED)
        for post in approved_posts:
            if post.scheduled_at:
                self._schedule_job(post)
        logger.info("Loaded %d existing approved+scheduled jobs", len(approved_posts))

    async def _poll_for_approved(self) -> None:
        approved_posts = await self._repo.get_by_status(PostStatus.APPROVED)
        for post in approved_posts:
            if post.scheduled_at and not self._scheduler.get_job(f"post_{post.id}"):
                self._schedule_job(post)

    def _schedule_job(self, post: Post) -> None:
        if not post.scheduled_at:
            return
        job_id = f"post_{post.id}"
        if self._scheduler.get_job(job_id):
            return
        self._scheduler.add_job(
            self._publish_post,
            DateTrigger(run_date=post.scheduled_at),
            args=[post.id],
            id=job_id,
            replace_existing=True,
        )
        logger.info("Registered job %s for %s", job_id, post.scheduled_at)

    async def _publish_post(self, post_id: UUID) -> None:
        post = await self._repo.get_by_id(post_id)
        if not post:
            logger.error("Publish job: post %s not found", post_id)
            return

        success = True
        for platform in post.target_platforms:
            publisher = self._publishers.get(platform)
            if not publisher:
                logger.warning("No publisher for platform '%s'", platform)
                continue
            try:
                ok = await publisher.publish(post)
                if not ok:
                    success = False
                    logger.error("Publisher '%s' returned False for post %s", platform, post_id)
            except Exception as exc:
                success = False
                logger.error("Publisher '%s' raised for post %s: %s", platform, post_id, exc)

        new_status = PostStatus.PUBLISHED if success else PostStatus.FAILED
        await self._repo.update_status(post_id, new_status)
        logger.info("Post %s → %s", post_id, new_status.value)
