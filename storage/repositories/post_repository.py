from datetime import datetime
from typing import List, Optional
from uuid import UUID
from supabase import Client
from core.models.post import Post, PostStatus
from config.logging import get_logger

logger = get_logger(__name__)


class PostRepository:
    def __init__(self, client: Client) -> None:
        self._client = client

    async def save(self, post: Post) -> Post:
        data = {
            "id": str(post.id),
            "title": post.title,
            "body": post.body,
            "post_type": post.post_type,
            "creative_angle": post.creative_angle,
            "image_url": post.image_url,
            "source_urls": post.source_urls,
            "target_platforms": post.target_platforms,
            "target_subreddits": post.target_subreddits,
            "status": post.status.value,
            "scheduled_at": post.scheduled_at.isoformat() if post.scheduled_at else None,
            "published_at": post.published_at.isoformat() if post.published_at else None,
            "created_at": post.created_at.isoformat(),
            "run_id": str(post.run_id),
        }
        self._client.table("posts").upsert(data).execute()
        logger.info("Saved post %s", post.id)
        return post

    async def get_by_id(self, id: UUID) -> Optional[Post]:
        response = self._client.table("posts").select("*").eq("id", str(id)).single().execute()
        if not response.data:
            return None
        return self._row_to_post(response.data)

    async def get_by_status(self, status: PostStatus) -> List[Post]:
        response = self._client.table("posts").select("*").eq("status", status.value).execute()
        return [self._row_to_post(row) for row in (response.data or [])]

    async def update_status(self, id: UUID, status: PostStatus) -> None:
        self._client.table("posts").update({"status": status.value}).eq("id", str(id)).execute()
        logger.info("Updated post %s status to %s", id, status.value)

    async def update_schedule(self, id: UUID, scheduled_at: datetime) -> None:
        self._client.table("posts").update({
            "status": PostStatus.SCHEDULED.value,
            "scheduled_at": scheduled_at.isoformat(),
        }).eq("id", str(id)).execute()
        logger.info("Scheduled post %s at %s", id, scheduled_at)

    def _row_to_post(self, row: dict) -> Post:
        from datetime import datetime
        from uuid import UUID as _UUID

        def _parse_dt(val: str | None) -> datetime | None:
            return datetime.fromisoformat(val) if val else None

        return Post(
            id=_UUID(row["id"]),
            title=row["title"],
            body=row["body"],
            post_type=row["post_type"],
            creative_angle=row.get("creative_angle"),
            image_url=row.get("image_url"),
            source_urls=row.get("source_urls") or [],
            target_platforms=row.get("target_platforms") or [],
            target_subreddits=row.get("target_subreddits") or [],
            status=PostStatus(row["status"]),
            scheduled_at=_parse_dt(row.get("scheduled_at")),
            published_at=_parse_dt(row.get("published_at")),
            created_at=datetime.fromisoformat(row["created_at"]),
            run_id=_UUID(row["run_id"]),
        )
