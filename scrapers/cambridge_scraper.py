from typing import List
from uuid import UUID
import feedparser
import httpx
from core.interfaces.scraper import AbstractScraper
from core.models.raw_content import RawContent
from config.logging import get_logger

logger = get_logger(__name__)

FEED_URL = "https://www.cambridgeassessment.org.uk/rss/news.xml"
MAX_ITEMS = 10


class CambridgeScraper(AbstractScraper):
    @property
    def name(self) -> str:
        return "cambridge"

    async def scrape(self) -> List[RawContent]:
        return await self.scrape_with_run_id(UUID(int=0))

    async def scrape_with_run_id(self, run_id: UUID) -> List[RawContent]:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(FEED_URL, headers={"User-Agent": "EduBot/1.0"})
                response.raise_for_status()
            feed = feedparser.parse(response.text)
        except Exception as exc:
            logger.error("CambridgeScraper: failed to fetch feed: %s", exc)
            return []

        results: List[RawContent] = []
        for entry in feed.entries[:MAX_ITEMS]:
            link = entry.get("link", "")
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            if not link or not title:
                continue
            results.append(RawContent(
                url=link,
                title=title,
                body=summary,
                source=self.name,
                run_id=run_id,
            ))

        logger.info("CambridgeScraper: found %d items", len(results))
        return results
