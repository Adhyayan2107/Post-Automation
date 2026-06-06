from datetime import datetime, timedelta, timezone
from typing import List
from uuid import UUID

from supabase import Client

from core.models.raw_content import RawContent
from config.logging import get_logger

logger = get_logger(__name__)


class RawContentRepository:
    def __init__(self, client: Client) -> None:
        self._client = client

    async def save_batch(self, items: List[RawContent]) -> None:
        for item in items:
            data = {
                "id": str(item.id),
                "url": item.url,
                "title": item.title,
                "body": item.body,
                "source": item.source,
                "scraped_at": item.scraped_at.isoformat(),
                "run_id": str(item.run_id),
            }
            try:
                self._client.table("raw_content").upsert(
                    data, on_conflict="url,run_id"
                ).execute()
            except Exception as exc:
                logger.warning("RawContentRepository: skipped duplicate %s: %s", item.url, exc)

    async def get_recent(self, max_age_days: int = 7) -> List[RawContent]:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=max_age_days)).isoformat()
        response = (
            self._client.table("raw_content")
            .select("*")
            .gte("scraped_at", cutoff)
            .order("scraped_at", desc=True)
            .execute()
        )
        return [self._row_to_raw_content(r) for r in (response.data or [])]

    def _row_to_raw_content(self, row: dict) -> RawContent:
        return RawContent(
            id=UUID(row["id"]),
            url=row["url"],
            title=row["title"],
            body=row.get("body", ""),
            source=row["source"],
            run_id=UUID(row["run_id"]),
            scraped_at=datetime.fromisoformat(row["scraped_at"]),
        )
