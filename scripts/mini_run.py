"""
Mini run: check for cached raw content first (7-day window), generate 1 edu + 1 creative
post, save to Supabase, auto-approve, and (optionally) schedule to Google Calendar.

Usage:
    uv run python scripts/mini_run.py
"""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.logging import setup_logging
from config.settings import settings

setup_logging("INFO")

from agents.scraper_agent import ScraperAgent
from agents.image_agent import ImageAgent
from generators.educational_post import EducationalPostGenerator
from generators.creative_post import CreativePostGenerator
from image_providers.pexels import PexelsImageProvider
from image_providers.unsplash import UnsplashImageProvider
from image_providers.jikan import JikanAnimeImageProvider
from image_providers.tmdb import TMDbImageProvider
from scrapers.news_scraper import NewsScraper
from scrapers.ib_official import IBOfficialScraper
from core.models.post import PostStatus
from storage.database import get_supabase_service_client
from storage.repositories.post_repository import PostRepository
from storage.repositories.raw_content_repository import RawContentRepository
from storage.repositories.run_log_repository import RunLogRepository


async def mini_run() -> None:
    print("\n🚀 EduBot Mini Run\n")

    client = get_supabase_service_client()
    post_repo = PostRepository(client)
    run_log_repo = RunLogRepository(client)
    raw_content_repo = RawContentRepository(client)

    run_id = await run_log_repo.start_run()
    print(f"Run ID: {run_id}\n")

    # ── Step 1: Use cached raw content or scrape fresh ────────────────────
    print("Step 1: Checking raw content cache (7-day window)...")
    raw_contents = await raw_content_repo.get_recent(max_age_days=7)

    if raw_contents:
        print(f"  Using {len(raw_contents)} cached items (no scraping needed)\n")
    else:
        print("  Cache empty — scraping fresh...")
        scraper_agent = ScraperAgent([NewsScraper(), IBOfficialScraper()])
        raw_contents = await scraper_agent.run(run_id)
        print(f"  Got {len(raw_contents)} items")
        if not raw_contents:
            print("  No items scraped — check network / API keys")
            await run_log_repo.fail_run(run_id)
            return
        await raw_content_repo.save_batch(raw_contents)
        print(f"  Saved {len(raw_contents)} items to cache\n")

    # ── Step 2: Generate 2 educational posts ──────────────────────────────
    print("Step 2: Generating educational posts (Claude)...")
    edu_gen = EducationalPostGenerator()
    edu_posts = await edu_gen.generate(raw_contents[:5])
    edu_posts = edu_posts[:2]
    for p in edu_posts:
        p.run_id = run_id
        p.status = PostStatus.PENDING
    for p in edu_posts:
        print(f"  Generated: {p.title[:70]}")
    print()

    # ── Step 3: Generate 2 creative posts ─────────────────────────────────
    print("Step 3: Generating creative posts (Claude)...")
    creative_gen = CreativePostGenerator()
    creative_posts = await creative_gen.generate(raw_contents[:5])
    creative_posts = creative_posts[:2]
    for p in creative_posts:
        p.run_id = run_id
        p.status = PostStatus.PENDING
    for p in creative_posts:
        print(f"  Generated: {p.title[:70]}")
    print()

    all_posts = edu_posts + creative_posts

    # ── Step 4: Get images ─────────────────────────────────────────────────
    print("Step 4: Sourcing images...")
    image_agent = ImageAgent(
        providers=[PexelsImageProvider(), UnsplashImageProvider()],
        anime_provider=JikanAnimeImageProvider(),
        movie_provider=TMDbImageProvider(),
    )
    all_posts = await image_agent.enrich_posts(all_posts)
    for p in all_posts:
        print(f"  {'✓' if p.image_url else '✗'} image for: {p.title[:60]}")
    print()

    # ── Step 5: Save to Supabase ───────────────────────────────────────────
    print("Step 5: Saving to Supabase...")
    saved = []
    for post in all_posts:
        saved_post = await post_repo.save(post)
        saved.append(saved_post)
        print(f"  Saved [{post.post_type}] id={post.id}")
    print()

    # ── Step 6: Assign time slots ─────────────────────────────────────────
    print("Step 6: Assigning time slots...")
    from scheduler.time_optimizer import TimeOptimizer

    optimizer = TimeOptimizer()

    existing = await post_repo.get_future_scheduled()
    already_used: dict[str, list] = {"reddit": [], "discord": []}
    for ep in existing:
        if ep.scheduled_at is None:
            continue
        for platform in (ep.target_platforms or []):
            if platform in already_used:
                already_used[platform].append(ep.scheduled_at)

    all_slots = optimizer.get_slots_for_week(saved, already_used=already_used)
    post_map = {p.id: p for p in saved}

    for slot in all_slots:
        post = post_map[slot.post_id]
        await post_repo.set_slot(post.id, slot.scheduled_at)
        print(f"  📅 [{slot.platform:7}] {slot.scheduled_at.strftime('%a %d %b %H:%M UTC')}  {post.title[:45]}")
    print()

    await run_log_repo.finish_run(run_id, len(saved))

    # ── Summary ────────────────────────────────────────────────────────────
    print("\n=== Done ===")
    for post in saved:
        status = (await post_repo.get_by_id(post.id)).status
        print(f"  [{status.value:10}] {post.title[:65]}")
    print(f"\nView in dashboard: posts are saved with their status in Supabase.")
    print(f"Table: posts | Run ID: {run_id}\n")


if __name__ == "__main__":
    asyncio.run(mini_run())
