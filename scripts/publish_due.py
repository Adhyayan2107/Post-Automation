"""
Publish all approved posts whose scheduled_at <= now.

Run manually:  uv run python scripts/publish_due.py
GitHub Actions cron runs this every hour automatically.

Platforms are published based on target_platforms on each post.
Unconfigured platforms (e.g. Reddit with no credentials) are skipped silently.
"""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.logging import setup_logging
from config.settings import settings

setup_logging("INFO")

from core.models.post import PostStatus
from publishers.discord import DiscordPublisher
from publishers.reddit_browser import RedditBrowserPublisher
from storage.database import get_supabase_service_client
from storage.repositories.post_repository import PostRepository


async def publish_due() -> None:
    print("\n📤 EduBot Publish Due Posts\n")

    client = get_supabase_service_client()
    repo   = PostRepository(client)

    due = await repo.get_due_for_publishing()
    if not due:
        print("Nothing due to publish right now.")
        return

    print(f"Found {len(due)} post(s) due for publishing:\n")

    # Build only the publishers that are configured
    publishers: dict = {}

    discord_configured = bool(
        settings.discord.webhook_educational or settings.discord.webhook_creative
    )
    if discord_configured:
        publishers["discord"] = DiscordPublisher()
        print("  ✓ Discord publisher ready")

    reddit_configured = bool(settings.reddit.username and settings.reddit.password)
    if reddit_configured:
        publishers["reddit"] = RedditBrowserPublisher()
        print("  ✓ Reddit publisher ready (browser mode)")
    else:
        print("  ⚠ Reddit credentials not set — skipping Reddit")

    print()

    for post in due:
        print(f"Publishing: [{post.post_type}] {post.title[:65]}")
        overall_success = False
        any_attempted   = False

        for platform in post.target_platforms:
            publisher = publishers.get(platform)
            if not publisher:
                continue
            any_attempted = True
            ok = await publisher.publish(post)
            status_icon = "✓" if ok else "✗"
            print(f"  {status_icon} {platform}")
            if ok:
                overall_success = True

        if not any_attempted:
            print("  ⚠ No configured publisher matched — skipping (won't mark failed)")
            continue

        new_status = PostStatus.PUBLISHED if overall_success else PostStatus.FAILED
        await repo.update_status(post.id, new_status)
        print(f"  → status: {new_status.value}\n")

    print("Done.")


if __name__ == "__main__":
    asyncio.run(publish_due())
