"""
Mini run: scrape news only, generate 1 edu + 1 creative post, save to Supabase,
then auto-approve and (optionally) schedule to Google Calendar.

Usage:
    uv run python scripts/mini_run.py
"""

from __future__ import annotations

import asyncio
import os
import sys

# ensure project root is on the path
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
from scrapers.news_scraper import NewsScraper
from scrapers.ib_official import IBOfficialScraper
from core.models.post import PostStatus
from storage.database import get_supabase_service_client
from storage.repositories.post_repository import PostRepository
from storage.repositories.run_log_repository import RunLogRepository


async def mini_run() -> None:
    print("\n🚀 EduBot Mini Run\n")

    client = get_supabase_service_client()
    post_repo = PostRepository(client)
    run_log_repo = RunLogRepository(client)

    run_id = await run_log_repo.start_run()
    print(f"Run ID: {run_id}\n")

    # ── Step 1: Scrape (news + IB official — no auth needed) ──────────────
    print("Step 1: Scraping news...")
    scraper_agent = ScraperAgent([NewsScraper(), IBOfficialScraper()])
    raw_contents = await scraper_agent.run(run_id)
    print(f"  Got {len(raw_contents)} items\n")

    if not raw_contents:
        print("  No items scraped — check network / API keys")
        await run_log_repo.fail_run(run_id)
        return

    # ── Step 2: Generate 1 educational post ───────────────────────────────
    print("Step 2: Generating educational post (Claude)...")
    edu_gen = EducationalPostGenerator()
    edu_gen.__class__.__dict__  # avoid module-level import issues
    # Patch to return exactly 1 post
    original_limit = edu_gen.__class__.__dict__.get("generate")
    edu_posts = await edu_gen.generate(raw_contents[:5])
    edu_posts = edu_posts[:1]
    for p in edu_posts:
        p.run_id = run_id
        p.status = PostStatus.PENDING
    print(f"  Generated: {edu_posts[0].title[:70] if edu_posts else 'none'}\n")

    # ── Step 3: Generate 1 creative post ──────────────────────────────────
    print("Step 3: Generating creative post (Claude)...")
    creative_gen = CreativePostGenerator()
    creative_posts = await creative_gen.generate(raw_contents[:5])
    creative_posts = creative_posts[:1]
    for p in creative_posts:
        p.run_id = run_id
        p.status = PostStatus.PENDING
    print(f"  Generated: {creative_posts[0].title[:70] if creative_posts else 'none'}\n")

    all_posts = edu_posts + creative_posts

    # ── Step 4: Get images ─────────────────────────────────────────────────
    print("Step 4: Sourcing images...")
    image_agent = ImageAgent([PexelsImageProvider(), UnsplashImageProvider()])
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

    # ── Step 6: Auto-approve ──────────────────────────────────────────────
    print("Step 6: Auto-approving posts...")
    for post in saved:
        await post_repo.update_status(post.id, PostStatus.APPROVED)
        print(f"  Approved: {post.id}")
    print()

    # ── Step 7: Schedule to Google Calendar ───────────────────────────────
    creds_exist = os.path.exists("credentials.json") or os.path.exists("token.json")
    if creds_exist:
        print("Step 7: Scheduling to Google Calendar...")
        from scheduler.google_calendar import GoogleCalendarScheduler
        from scheduler.time_optimizer import TimeOptimizer

        optimizer = TimeOptimizer()
        calendar = GoogleCalendarScheduler()

        for post in saved:
            post.status = PostStatus.APPROVED
            slots = optimizer.get_slots_for_week([post])
            for slot in slots:
                try:
                    event_id = calendar.create_event(slot, post)
                    print(f"  📅 Calendar event: {event_id} on {slot.scheduled_at.strftime('%a %d %b %H:%M UTC')}")
                    await post_repo.update_status(post.id, PostStatus.SCHEDULED)
                except Exception as exc:
                    print(f"  ✗ Calendar failed: {exc}")
    else:
        print("Step 7: Skipping Google Calendar (no credentials.json / token.json found)")
        print("  → To enable: download credentials.json from Google Cloud Console")
        print("    and put it in the project root, then re-run this script\n")

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
