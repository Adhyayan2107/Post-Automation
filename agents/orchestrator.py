"""
FatherAgent — weekly entry point for the full EduBot pipeline.

Run directly:
    python -m agents.orchestrator
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone

from agents.scraper_agent import ScraperAgent
from agents.content_agent import ContentAgent
from agents.creative_agent import CreativeAgent
from agents.image_agent import ImageAgent
from generators.educational_post import EducationalPostGenerator
from generators.creative_post import CreativePostGenerator
from image_providers.pexels import PexelsImageProvider
from image_providers.unsplash import UnsplashImageProvider
from scrapers.news_scraper import NewsScraper
from scrapers.reddit_scraper import RedditScraper
from scrapers.ib_official import IBOfficialScraper
from scrapers.cambridge_scraper import CambridgeScraper
from scrapers.youtube_scraper import YouTubeScraper
from scheduler.gmail_notifier import GmailNotifier
from storage.database import get_supabase_service_client
from storage.repositories.post_repository import PostRepository
from storage.repositories.run_log_repository import RunLogRepository
from config.settings import settings
from config.logging import setup_logging, get_logger

logger = get_logger(__name__)

DASHBOARD_URL = "https://your-dashboard.vercel.app/posts"


class FatherAgent:
    def __init__(
        self,
        scraper_agent: ScraperAgent | None = None,
        content_agent: ContentAgent | None = None,
        creative_agent: CreativeAgent | None = None,
        image_agent: ImageAgent | None = None,
        post_repository: PostRepository | None = None,
        run_log_repository: RunLogRepository | None = None,
        gmail_notifier: GmailNotifier | None = None,
    ) -> None:
        if post_repository is None:
            client = get_supabase_service_client()
            post_repository = PostRepository(client)
            run_log_repository = RunLogRepository(client)

        self._post_repo = post_repository
        self._run_log_repo = run_log_repository or RunLogRepository(get_supabase_service_client())
        self._gmail = gmail_notifier or GmailNotifier()

        self._scraper_agent = scraper_agent or ScraperAgent([
            NewsScraper(),
            RedditScraper(),
            IBOfficialScraper(),
            CambridgeScraper(),
            YouTubeScraper(),
        ])

        self._content_agent = content_agent or ContentAgent(
            generator=EducationalPostGenerator(),
            post_repository=self._post_repo,
        )

        self._creative_agent = creative_agent or CreativeAgent(
            generator=CreativePostGenerator(),
            post_repository=self._post_repo,
        )

        self._image_agent = image_agent or ImageAgent([
            PexelsImageProvider(),
            UnsplashImageProvider(),
        ])

    async def run(self) -> None:
        setup_logging(settings.app.log_level)
        start = time.monotonic()
        logger.info("FatherAgent: starting weekly run — dry_run=%s", settings.app.dry_run)

        run_id = await self._run_log_repo.start_run()

        try:
            # 1. Scrape
            raw_contents = await self._scraper_agent.run(run_id)
            logger.info("Scraped %d unique items", len(raw_contents))

            if not raw_contents:
                logger.warning("No raw content scraped — ending run early")
                await self._run_log_repo.finish_run(run_id, 0)
                return

            # 2 & 3. Generate posts (educational + creative) concurrently
            edu_posts, creative_posts = await asyncio.gather(
                self._content_agent.run(raw_contents, run_id),
                self._creative_agent.run(raw_contents, run_id),
            )

            all_posts = edu_posts + creative_posts
            logger.info("Generated %d posts (%d edu, %d creative)",
                        len(all_posts), len(edu_posts), len(creative_posts))

            # 4. Enrich with images
            all_posts = await self._image_agent.enrich_posts(all_posts)

            # 5. Persist any posts that weren't already saved by their agents
            # (agents save individually; this is a safety net)
            for post in all_posts:
                if not post.id:
                    await self._post_repo.save(post)

            # 6. Gmail summary
            self._gmail.send_summary(
                post_titles=[p.title for p in all_posts],
                dashboard_url=DASHBOARD_URL,
            )

            elapsed = time.monotonic() - start
            logger.info(
                "FatherAgent: run complete — %d posts in %.1fs",
                len(all_posts),
                elapsed,
            )
            await self._run_log_repo.finish_run(run_id, len(all_posts))

        except Exception as exc:
            logger.error("FatherAgent: run failed: %s", exc, exc_info=True)
            await self._run_log_repo.fail_run(run_id)
            raise


if __name__ == "__main__":
    asyncio.run(FatherAgent().run())
