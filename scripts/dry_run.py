"""
Dry run: executes the full pipeline with DRY_RUN=true.
No DB writes, no real API calls to publishers.

Usage:
    uv run python scripts/dry_run.py
"""

from __future__ import annotations

import asyncio
import os
import time
from uuid import uuid4

os.environ.setdefault("DRY_RUN", "true")

from config.logging import setup_logging
from config.settings import settings

setup_logging(settings.app.log_level)

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
from core.models.post import PostStatus


async def dry_run() -> None:
    print("\n=== EduBot Dry Run ===\n")
    run_id = uuid4()
    start = time.monotonic()

    # Scrape
    print("Step 1: Scraping...")
    scraper_agent = ScraperAgent([
        NewsScraper(),
        RedditScraper(),
        IBOfficialScraper(),
        CambridgeScraper(),
        YouTubeScraper(),
    ])
    raw_contents = await scraper_agent.run(run_id)
    print(f"  Scraped {len(raw_contents)} unique items\n")

    if not raw_contents:
        print("  No items scraped — check your API keys in .env")
        return

    # Generate
    print("Step 2: Generating content (Claude API)...")
    content_agent = ContentAgent(generator=EducationalPostGenerator())
    creative_agent = CreativeAgent(generator=CreativePostGenerator())

    edu_posts, creative_posts = await asyncio.gather(
        content_agent.run(raw_contents, run_id),
        creative_agent.run(raw_contents, run_id),
    )
    all_posts = edu_posts + creative_posts
    print(f"  Generated {len(edu_posts)} educational + {len(creative_posts)} creative posts\n")

    # Image enrichment
    print("Step 3: Sourcing images...")
    image_agent = ImageAgent([PexelsImageProvider(), UnsplashImageProvider()])
    all_posts = await image_agent.enrich_posts(all_posts)
    with_images = sum(1 for p in all_posts if p.image_url)
    print(f"  {with_images}/{len(all_posts)} posts have images\n")

    # Report
    elapsed = time.monotonic() - start
    all_subreddits = set(sub for p in all_posts for sub in p.target_subreddits)

    print("=== Dry Run Report ===")
    print(f"  Scraped items:    {len(raw_contents)}")
    print(f"  Posts generated:  {len(all_posts)}")
    print(f"  Posts with image: {with_images}")
    print(f"  Target subreddits: {', '.join(sorted(all_subreddits))}")
    print(f"  Time elapsed:     {elapsed:.1f}s")
    print(f"  DRY_RUN=true — nothing was published or saved to DB\n")

    print("Posts that would be created:")
    for i, post in enumerate(all_posts, 1):
        angle = f" [{post.creative_angle}]" if post.creative_angle else ""
        image = "✓ image" if post.image_url else "✗ no image"
        print(f"  {i}. [{post.post_type}{angle}] {post.title[:70]}  ({image})")
    print()


if __name__ == "__main__":
    asyncio.run(dry_run())
