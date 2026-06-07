"""
One-shot test: sends one real approved post to Discord immediately.
Does NOT check scheduled_at — purely for verifying webhook works.
Does NOT change the post's status in DB.

Usage: uv run python scripts/test_discord.py
"""

from __future__ import annotations
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.logging import setup_logging
setup_logging("INFO")

from core.models.post import PostStatus
from publishers.discord import DiscordPublisher
from storage.database import get_supabase_service_client
from storage.repositories.post_repository import PostRepository


async def test() -> None:
    client = get_supabase_service_client()
    repo   = PostRepository(client)

    posts = await repo.get_by_status(PostStatus.APPROVED)
    if not posts:
        posts = await repo.get_by_status(PostStatus.PENDING)
    if not posts:
        print("No approved or pending posts in DB to test with.")
        return

    post = posts[0]
    print(f"Sending test post to Discord:")
    print(f"  Title : {post.title}")
    print(f"  Type  : {post.post_type}" + (f" / {post.creative_angle}" if post.creative_angle else ""))
    channel = "fun-to-learn" if post.post_type == "creative" else "news-and-updates"
    print(f"  → #{channel}\n")

    publisher = DiscordPublisher()
    ok = await publisher.publish(post)
    print("✓ Sent successfully!" if ok else "✗ Failed — check webhook URL / secrets")


if __name__ == "__main__":
    asyncio.run(test())
