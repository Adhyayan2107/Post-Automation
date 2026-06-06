import asyncio
from typing import List
from uuid import UUID
from core.interfaces.scraper import AbstractScraper
from core.models.raw_content import RawContent
from storage.repositories.post_repository import PostRepository
from config.logging import get_logger

logger = get_logger(__name__)


class ScraperAgent:
    def __init__(self, scrapers: List[AbstractScraper], raw_content_repo=None) -> None:
        self._scrapers = scrapers
        self._raw_content_repo = raw_content_repo  # optional; used to persist raw content

    async def run(self, run_id: UUID) -> List[RawContent]:
        tasks = [self._run_scraper(s, run_id) for s in self._scrapers]
        results_per_scraper: List[List[RawContent]] = await asyncio.gather(*tasks)

        seen_urls: set[str] = set()
        unique: List[RawContent] = []
        for scraper_results in results_per_scraper:
            for item in scraper_results:
                if item.url not in seen_urls:
                    seen_urls.add(item.url)
                    unique.append(item)

        logger.info(
            "ScraperAgent: %d unique items from %d scrapers",
            len(unique),
            len(self._scrapers),
        )
        return unique

    async def _run_scraper(self, scraper: AbstractScraper, run_id: UUID) -> List[RawContent]:
        try:
            if hasattr(scraper, "scrape_with_run_id"):
                results = await scraper.scrape_with_run_id(run_id)
            else:
                results = await scraper.scrape()
                for r in results:
                    r.run_id = run_id
            logger.info("Scraper '%s': %d items", scraper.name, len(results))
            return results
        except Exception as exc:
            logger.error("Scraper '%s' failed: %s", scraper.name, exc)
            return []
