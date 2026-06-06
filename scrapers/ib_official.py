from typing import List
from uuid import UUID
import httpx
from bs4 import BeautifulSoup
from core.interfaces.scraper import AbstractScraper
from core.models.raw_content import RawContent
from config.logging import get_logger

logger = get_logger(__name__)

NEWS_URL = "https://www.ibo.org/news/"
MAX_ARTICLES = 10


class IBOfficialScraper(AbstractScraper):
    @property
    def name(self) -> str:
        return "ib_official"

    async def scrape(self) -> List[RawContent]:
        return await self.scrape_with_run_id(UUID(int=0))

    async def scrape_with_run_id(self, run_id: UUID) -> List[RawContent]:
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.get(NEWS_URL, headers={"User-Agent": "EduBot/1.0"})
                response.raise_for_status()
        except Exception as exc:
            logger.error("IBOfficialScraper: fetch failed: %s", exc)
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        results: List[RawContent] = []

        # IBO news page structure: articles in various card/list layouts
        articles = soup.find_all("article")[:MAX_ARTICLES]
        if not articles:
            # fallback: look for news list items
            articles = soup.select(".news-item, .article-card, li.news")[:MAX_ARTICLES]

        for article in articles:
            title_tag = article.find(["h2", "h3", "h4"])
            link_tag = article.find("a", href=True)
            summary_tag = article.find("p")

            title = title_tag.get_text(strip=True) if title_tag else ""
            href = link_tag["href"] if link_tag else ""
            summary = summary_tag.get_text(strip=True) if summary_tag else ""

            if not title or not href:
                continue

            url = href if href.startswith("http") else f"https://www.ibo.org{href}"
            results.append(RawContent(
                url=url,
                title=title,
                body=summary,
                source=self.name,
                run_id=run_id,
            ))

        logger.info("IBOfficialScraper: found %d articles", len(results))
        return results
