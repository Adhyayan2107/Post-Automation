"""
End-to-end test: runs FatherAgent with all external services mocked.
DRY_RUN=true — no real publishing or DB writes.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from core.models.post import Post, PostStatus
from core.models.raw_content import RawContent


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_raw(n: int = 5) -> list[RawContent]:
    run_id = uuid4()
    return [
        RawContent(url=f"https://example.com/{i}", title=f"Article {i}",
                   body=f"Body {i}", source="news", run_id=run_id)
        for i in range(n)
    ]


def _make_post(post_type: str = "educational") -> Post:
    return Post(
        title=f"Test {post_type} post",
        body="Some body text",
        post_type=post_type,
        run_id=uuid4(),
        status=PostStatus.PENDING,
        target_platforms=["reddit", "discord"],
        target_subreddits=["r/IBO"],
    )


def _make_scraper_agent(raw: list[RawContent]) -> MagicMock:
    agent = MagicMock()
    agent.run = AsyncMock(return_value=raw)
    return agent


def _make_content_agent(posts: list[Post]) -> MagicMock:
    agent = MagicMock()
    agent.run = AsyncMock(return_value=posts)
    return agent


def _make_image_agent(posts: list[Post]) -> MagicMock:
    agent = MagicMock()
    enriched = [Post(**{**p.model_dump(), "image_url": "https://pexels.com/img.jpg"}) for p in posts]
    agent.enrich_posts = AsyncMock(return_value=enriched)
    return agent


def _make_post_repo(run_id=None) -> MagicMock:
    repo = MagicMock()
    repo.save = AsyncMock(side_effect=lambda p: p)
    return repo


def _make_run_log_repo() -> MagicMock:
    repo = MagicMock()
    repo.start_run = AsyncMock(return_value=uuid4())
    repo.finish_run = AsyncMock()
    repo.fail_run = AsyncMock()
    return repo


def _make_gmail() -> MagicMock:
    gmail = MagicMock()
    gmail.send_summary = MagicMock(return_value=True)
    return gmail


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestFatherAgentE2E:
    @pytest.mark.asyncio
    async def test_full_pipeline_runs_without_error(self):
        from agents.orchestrator import FatherAgent

        raw = _make_raw(6)
        edu_posts = [_make_post("educational") for _ in range(3)]
        creative_posts = [_make_post("creative") for _ in range(2)]
        all_posts = edu_posts + creative_posts

        scraper_agent = _make_scraper_agent(raw)
        content_agent = _make_content_agent(edu_posts)
        creative_agent = _make_content_agent(creative_posts)
        image_agent = _make_image_agent(all_posts)
        post_repo = _make_post_repo()
        run_log_repo = _make_run_log_repo()
        gmail = _make_gmail()

        with patch("agents.orchestrator.settings") as mock_settings:
            mock_settings.app.dry_run = True
            mock_settings.app.log_level = "INFO"

            agent = FatherAgent(
                scraper_agent=scraper_agent,
                content_agent=content_agent,
                creative_agent=creative_agent,
                image_agent=image_agent,
                post_repository=post_repo,
                run_log_repository=run_log_repo,
                gmail_notifier=gmail,
            )
            await agent.run()

        # Run lifecycle
        run_log_repo.start_run.assert_awaited_once()
        run_log_repo.finish_run.assert_awaited_once()
        run_log_repo.fail_run.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_scraper_agent_called_with_run_id(self):
        from agents.orchestrator import FatherAgent

        raw = _make_raw(3)
        edu_posts = [_make_post("educational")]
        creative_posts = [_make_post("creative")]
        all_posts = edu_posts + creative_posts

        run_id = uuid4()
        run_log_repo = _make_run_log_repo()
        run_log_repo.start_run = AsyncMock(return_value=run_id)

        scraper_agent = _make_scraper_agent(raw)
        content_agent = _make_content_agent(edu_posts)
        creative_agent = _make_content_agent(creative_posts)
        image_agent = _make_image_agent(all_posts)

        with patch("agents.orchestrator.settings") as mock_settings:
            mock_settings.app.dry_run = True
            mock_settings.app.log_level = "INFO"

            agent = FatherAgent(
                scraper_agent=scraper_agent,
                content_agent=content_agent,
                creative_agent=creative_agent,
                image_agent=image_agent,
                post_repository=_make_post_repo(),
                run_log_repository=run_log_repo,
                gmail_notifier=_make_gmail(),
            )
            await agent.run()

        scraper_agent.run.assert_awaited_once_with(run_id)

    @pytest.mark.asyncio
    async def test_image_agent_called_with_all_posts(self):
        from agents.orchestrator import FatherAgent

        raw = _make_raw(3)
        edu_posts = [_make_post("educational") for _ in range(3)]
        creative_posts = [_make_post("creative") for _ in range(2)]
        all_posts = edu_posts + creative_posts

        image_agent = _make_image_agent(all_posts)

        with patch("agents.orchestrator.settings") as mock_settings:
            mock_settings.app.dry_run = True
            mock_settings.app.log_level = "INFO"

            agent = FatherAgent(
                scraper_agent=_make_scraper_agent(raw),
                content_agent=_make_content_agent(edu_posts),
                creative_agent=_make_content_agent(creative_posts),
                image_agent=image_agent,
                post_repository=_make_post_repo(),
                run_log_repository=_make_run_log_repo(),
                gmail_notifier=_make_gmail(),
            )
            await agent.run()

        image_agent.enrich_posts.assert_awaited_once()
        enriched_arg = image_agent.enrich_posts.call_args[0][0]
        assert len(enriched_arg) == len(edu_posts) + len(creative_posts)

    @pytest.mark.asyncio
    async def test_gmail_called_with_post_titles(self):
        from agents.orchestrator import FatherAgent

        raw = _make_raw(3)
        edu_posts = [_make_post("educational")]
        creative_posts = [_make_post("creative")]
        all_posts = edu_posts + creative_posts
        gmail = _make_gmail()

        with patch("agents.orchestrator.settings") as mock_settings:
            mock_settings.app.dry_run = True
            mock_settings.app.log_level = "INFO"

            agent = FatherAgent(
                scraper_agent=_make_scraper_agent(raw),
                content_agent=_make_content_agent(edu_posts),
                creative_agent=_make_content_agent(creative_posts),
                image_agent=_make_image_agent(all_posts),
                post_repository=_make_post_repo(),
                run_log_repository=_make_run_log_repo(),
                gmail_notifier=gmail,
            )
            await agent.run()

        gmail.send_summary.assert_called_once()
        call_kwargs = gmail.send_summary.call_args
        titles = call_kwargs.kwargs.get("post_titles") or call_kwargs[1].get("post_titles") or call_kwargs[0][0]
        assert len(titles) == len(all_posts)

    @pytest.mark.asyncio
    async def test_run_marked_failed_on_exception(self):
        from agents.orchestrator import FatherAgent

        run_log_repo = _make_run_log_repo()
        failing_scraper = MagicMock()
        failing_scraper.run = AsyncMock(side_effect=Exception("Scraper exploded"))

        with patch("agents.orchestrator.settings") as mock_settings:
            mock_settings.app.dry_run = True
            mock_settings.app.log_level = "INFO"

            agent = FatherAgent(
                scraper_agent=failing_scraper,
                content_agent=_make_content_agent([]),
                creative_agent=_make_content_agent([]),
                image_agent=_make_image_agent([]),
                post_repository=_make_post_repo(),
                run_log_repository=run_log_repo,
                gmail_notifier=_make_gmail(),
            )
            with pytest.raises(Exception, match="Scraper exploded"):
                await agent.run()

        run_log_repo.fail_run.assert_awaited_once()
        run_log_repo.finish_run.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_empty_scrape_finishes_early(self):
        from agents.orchestrator import FatherAgent

        run_log_repo = _make_run_log_repo()
        content_agent = _make_content_agent([])
        creative_agent = _make_content_agent([])

        with patch("agents.orchestrator.settings") as mock_settings:
            mock_settings.app.dry_run = True
            mock_settings.app.log_level = "INFO"

            agent = FatherAgent(
                scraper_agent=_make_scraper_agent([]),
                content_agent=content_agent,
                creative_agent=creative_agent,
                image_agent=_make_image_agent([]),
                post_repository=_make_post_repo(),
                run_log_repository=run_log_repo,
                gmail_notifier=_make_gmail(),
            )
            await agent.run()

        # Still finishes cleanly
        run_log_repo.finish_run.assert_awaited_once()
        # Generators never called because no raw content
        content_agent.run.assert_not_awaited()
        creative_agent.run.assert_not_awaited()
