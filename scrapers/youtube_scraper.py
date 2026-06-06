from typing import List
from uuid import UUID
import httpx
from core.interfaces.scraper import AbstractScraper
from core.models.raw_content import RawContent
from config.settings import settings
from config.logging import get_logger

logger = get_logger(__name__)

QUERIES = [
    "IB study tips 2025",
    "IGCSE revision",
    "A level explained",
]
MAX_PER_QUERY = 10
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


class YouTubeScraper(AbstractScraper):
    @property
    def name(self) -> str:
        return "youtube"

    async def scrape(self) -> List[RawContent]:
        return await self.scrape_with_run_id(UUID(int=0))

    async def scrape_with_run_id(self, run_id: UUID) -> List[RawContent]:
        results: List[RawContent] = []
        seen_ids: set[str] = set()

        async with httpx.AsyncClient(timeout=15.0) as client:
            for query in QUERIES:
                try:
                    response = await client.get(YOUTUBE_SEARCH_URL, params={
                        "part": "snippet",
                        "q": query,
                        "type": "video",
                        "maxResults": MAX_PER_QUERY,
                        "key": settings.google.client_id,  # YouTube uses API key, not OAuth
                    })
                    response.raise_for_status()
                    data = response.json()
                    count = 0
                    for item in data.get("items", []):
                        video_id = item.get("id", {}).get("videoId", "")
                        if not video_id or video_id in seen_ids:
                            continue
                        seen_ids.add(video_id)
                        snippet = item.get("snippet", {})
                        results.append(RawContent(
                            url=f"https://www.youtube.com/watch?v={video_id}",
                            title=snippet.get("title", ""),
                            body=snippet.get("description", ""),
                            source=self.name,
                            run_id=run_id,
                        ))
                        count += 1
                    logger.info("YouTubeScraper: %d results for '%s'", count, query)
                except Exception as exc:
                    logger.error("YouTubeScraper: failed query '%s': %s", query, exc)

        return results
