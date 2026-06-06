from typing import List
from uuid import UUID
import praw
from core.interfaces.scraper import AbstractScraper
from core.models.raw_content import RawContent
from config.settings import settings
from config.logging import get_logger

logger = get_logger(__name__)

SUBREDDITS = ["IBO", "igcse", "6thForm", "alevel"]
POSTS_PER_SUB = 15


class RedditScraper(AbstractScraper):
    def __init__(self) -> None:
        self._reddit = praw.Reddit(
            client_id=settings.reddit.client_id,
            client_secret=settings.reddit.client_secret,
            user_agent=settings.reddit.user_agent,
            username=settings.reddit.username,
            password=settings.reddit.password,
        )

    @property
    def name(self) -> str:
        return "reddit"

    async def scrape(self) -> List[RawContent]:
        return await self.scrape_with_run_id(UUID(int=0))

    async def scrape_with_run_id(self, run_id: UUID) -> List[RawContent]:
        results: List[RawContent] = []
        for sub_name in SUBREDDITS:
            try:
                subreddit = self._reddit.subreddit(sub_name)
                for post in subreddit.top(time_filter="week", limit=POSTS_PER_SUB):
                    body = post.selftext or ""
                    results.append(RawContent(
                        url=f"https://www.reddit.com{post.permalink}",
                        title=post.title,
                        body=body,
                        source=self.name,
                        run_id=run_id,
                    ))
                logger.info("RedditScraper: scraped r/%s", sub_name)
            except Exception as exc:
                logger.error("RedditScraper: failed r/%s: %s", sub_name, exc)
        return results
