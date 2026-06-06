from typing import List
from uuid import UUID
import feedparser
import httpx
from core.interfaces.scraper import AbstractScraper
from core.models.raw_content import RawContent
from config.logging import get_logger

logger = get_logger(__name__)

QUERIES = [
    "IB diploma",
    "IGCSE 2025",
    "A level exam",
    "Cambridge assessment",
]
RESULTS_PER_QUERY = 10


class NewsScraper(AbstractScraper):
    @property
    def name(self) -> str:
        return "google_news"

    async def scrape(self) -> List[RawContent]:
        # run_id set externally by ScraperAgent
        return await self._fetch_all(UUID(int=0))

    async def scrape_with_run_id(self, run_id: UUID) -> List[RawContent]:
        return await self._fetch_all(run_id)

    async def _fetch_all(self, run_id: UUID) -> List[RawContent]:
        results: List[RawContent] = []
        seen_urls: set[str] = set()

        async with httpx.AsyncClient(timeout=15.0) as client:
            for query in QUERIES:
                try:
                    url = f"https://news.google.com/rss/search?q={httpx.QueryParams({'q': query})}&hl=en-US&gl=US&ceid=US:en"
                    response = await client.get(url)
                    response.raise_for_status()
                    feed = feedparser.parse(response.text)
                    count = 0
                    for entry in feed.entries[:RESULTS_PER_QUERY]:
                        link = entry.get("link", "")
                        if not link or link in seen_urls:
                            continue
                        seen_urls.add(link)
                        results.append(RawContent(
                            url=link,
                            title=entry.get("title", ""),
                            body=entry.get("summary", ""),
                            source=self.name,
                            run_id=run_id,
                        ))
                        count += 1
                    logger.info("NewsScraper: %d results for query '%s'", count, query)
                except Exception as exc:
                    logger.error("NewsScraper: failed query '%s': %s", query, exc)

        return results
