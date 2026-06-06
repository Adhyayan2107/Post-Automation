import pytest
from uuid import uuid4
from unittest.mock import MagicMock, AsyncMock, patch
from core.models.post import Post, PostStatus


def _make_post(
    subreddits: list[str] | None = None,
    platforms: list[str] | None = None,
    image_url: str | None = None,
) -> Post:
    return Post(
        title="IB Chemistry Paper 2 Prep Guide",
        body="## Overview\n\nHere are the key topics you need to know...",
        post_type="educational",
        run_id=uuid4(),
        status=PostStatus.SCHEDULED,
        target_subreddits=subreddits or ["r/IBO", "r/igcse"],
        target_platforms=platforms or ["reddit", "discord"],
        image_url=image_url,
    )


# ── RedditPublisher ─────────────────────────────────────────────────────────

class TestRedditPublisher:
    @pytest.mark.asyncio
    async def test_dry_run_returns_true_without_posting(self):
        from publishers.reddit import RedditPublisher
        mock_reddit = MagicMock()
        post = _make_post()

        with patch("publishers.reddit.settings") as mock_settings:
            mock_settings.app.dry_run = True
            publisher = RedditPublisher(reddit_instance=mock_reddit)
            result = await publisher.publish(post)

        assert result is True
        mock_reddit.subreddit.assert_not_called()

    @pytest.mark.asyncio
    async def test_posts_text_to_each_subreddit(self):
        from publishers.reddit import RedditPublisher
        mock_subreddit = MagicMock()
        mock_reddit = MagicMock()
        mock_reddit.subreddit.return_value = mock_subreddit
        post = _make_post(subreddits=["r/IBO", "r/igcse"])

        with patch("publishers.reddit.settings") as mock_settings, \
             patch("publishers.reddit.asyncio.sleep", new_callable=AsyncMock):
            mock_settings.app.dry_run = False
            publisher = RedditPublisher(reddit_instance=mock_reddit)
            result = await publisher.publish(post)

        assert result is True
        assert mock_reddit.subreddit.call_count == 2
        assert mock_subreddit.submit.call_count == 2

    @pytest.mark.asyncio
    async def test_posts_image_as_link_with_body_in_comment(self):
        from publishers.reddit import RedditPublisher
        mock_submission = MagicMock()
        mock_subreddit = MagicMock()
        mock_subreddit.submit.return_value = mock_submission
        mock_reddit = MagicMock()
        mock_reddit.subreddit.return_value = mock_subreddit
        post = _make_post(subreddits=["r/IBO"], image_url="https://pexels.com/img.jpg")

        with patch("publishers.reddit.settings") as mock_settings:
            mock_settings.app.dry_run = False
            publisher = RedditPublisher(reddit_instance=mock_reddit)
            result = await publisher.publish(post)

        assert result is True
        call_kwargs = mock_subreddit.submit.call_args
        assert call_kwargs.kwargs.get("url") == "https://pexels.com/img.jpg"
        mock_submission.reply.assert_called_once()

    @pytest.mark.asyncio
    async def test_api_exception_returns_false(self):
        import praw.exceptions
        from publishers.reddit import RedditPublisher
        mock_subreddit = MagicMock()
        mock_subreddit.submit.side_effect = praw.exceptions.APIException(
            [["RATELIMIT", "Take a break", "ratelimit"]]
        )
        mock_reddit = MagicMock()
        mock_reddit.subreddit.return_value = mock_subreddit
        post = _make_post(subreddits=["r/IBO"])

        with patch("publishers.reddit.settings") as mock_settings:
            mock_settings.app.dry_run = False
            publisher = RedditPublisher(reddit_instance=mock_reddit)
            result = await publisher.publish(post)

        assert result is False

    @pytest.mark.asyncio
    async def test_unexpected_exception_returns_false(self):
        from publishers.reddit import RedditPublisher
        mock_subreddit = MagicMock()
        mock_subreddit.submit.side_effect = Exception("Connection reset")
        mock_reddit = MagicMock()
        mock_reddit.subreddit.return_value = mock_subreddit
        post = _make_post(subreddits=["r/IBO"])

        with patch("publishers.reddit.settings") as mock_settings:
            mock_settings.app.dry_run = False
            publisher = RedditPublisher(reddit_instance=mock_reddit)
            result = await publisher.publish(post)

        assert result is False

    @pytest.mark.asyncio
    async def test_partial_failure_returns_false(self):
        """One subreddit succeeds, one fails — overall result is False."""
        import praw.exceptions
        from publishers.reddit import RedditPublisher

        good_sub = MagicMock()
        bad_sub = MagicMock()
        bad_sub.submit.side_effect = praw.exceptions.APIException(
            [["SUBREDDIT_NOTALLOWED", "Not allowed", "subreddit"]]
        )

        mock_reddit = MagicMock()
        mock_reddit.subreddit.side_effect = lambda name: good_sub if name == "IBO" else bad_sub
        post = _make_post(subreddits=["r/IBO", "r/igcse"])

        with patch("publishers.reddit.settings") as mock_settings, \
             patch("publishers.reddit.asyncio.sleep", new_callable=AsyncMock):
            mock_settings.app.dry_run = False
            publisher = RedditPublisher(reddit_instance=mock_reddit)
            result = await publisher.publish(post)

        assert result is False

    def test_platform_name(self):
        from publishers.reddit import RedditPublisher
        mock_reddit = MagicMock()
        publisher = RedditPublisher(reddit_instance=mock_reddit)
        assert publisher.platform_name == "reddit"


# ── DiscordPublisher ────────────────────────────────────────────────────────

class TestDiscordPublisher:
    @pytest.mark.asyncio
    async def test_dry_run_returns_true_without_webhook(self):
        from publishers.discord import DiscordPublisher
        post = _make_post()

        with patch("publishers.discord.settings") as mock_settings, \
             patch("publishers.discord.DiscordWebhook") as mock_wh_cls:
            mock_settings.app.dry_run = True
            publisher = DiscordPublisher(webhook_url="https://discord.com/api/webhooks/test")
            result = await publisher.publish(post)

        assert result is True
        mock_wh_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_calls_webhook_execute(self):
        from publishers.discord import DiscordPublisher
        post = _make_post()
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_webhook = MagicMock()
        mock_webhook.execute.return_value = mock_response

        with patch("publishers.discord.settings") as mock_settings, \
             patch("publishers.discord.DiscordWebhook", return_value=mock_webhook):
            mock_settings.app.dry_run = False
            mock_settings.discord.webhook_url = "https://discord.com/api/webhooks/test"
            publisher = DiscordPublisher(webhook_url="https://discord.com/api/webhooks/test")
            result = await publisher.publish(post)

        assert result is True
        mock_webhook.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_exception_returns_false(self):
        from publishers.discord import DiscordPublisher
        post = _make_post()

        with patch("publishers.discord.settings") as mock_settings, \
             patch("publishers.discord.DiscordWebhook", side_effect=Exception("Network down")):
            mock_settings.app.dry_run = False
            publisher = DiscordPublisher(webhook_url="https://discord.com/api/webhooks/test")
            result = await publisher.publish(post)

        assert result is False

    def test_embed_title_truncated_to_256(self):
        from publishers.discord import DiscordPublisher, MAX_TITLE
        long_title = "A" * 300
        post = _make_post()
        post.title = long_title

        with patch("publishers.discord.settings"):
            publisher = DiscordPublisher(webhook_url="https://discord.com/api/webhooks/test")
            embed = publisher._build_embed(post)

        assert len(embed.title) <= MAX_TITLE

    def test_embed_description_truncated_to_4096(self):
        from publishers.discord import DiscordPublisher, MAX_DESCRIPTION
        post = _make_post()
        post.body = "B" * 5000

        with patch("publishers.discord.settings"):
            publisher = DiscordPublisher(webhook_url="https://discord.com/api/webhooks/test")
            embed = publisher._build_embed(post)

        assert len(embed.description) <= MAX_DESCRIPTION

    def test_embed_has_correct_colour(self):
        from publishers.discord import DiscordPublisher, EMBED_COLOUR
        post = _make_post()

        with patch("publishers.discord.settings"):
            publisher = DiscordPublisher(webhook_url="https://discord.com/api/webhooks/test")
            embed = publisher._build_embed(post)

        assert embed.color == EMBED_COLOUR

    def test_embed_sets_image_when_present(self):
        from publishers.discord import DiscordPublisher
        post = _make_post(image_url="https://pexels.com/img.jpg")

        with patch("publishers.discord.settings"):
            publisher = DiscordPublisher(webhook_url="https://discord.com/api/webhooks/test")
            embed = publisher._build_embed(post)

        assert embed.image and embed.image.get("url") == "https://pexels.com/img.jpg"

    def test_embed_footer_contains_post_type(self):
        from publishers.discord import DiscordPublisher
        post = _make_post()

        with patch("publishers.discord.settings"):
            publisher = DiscordPublisher(webhook_url="https://discord.com/api/webhooks/test")
            embed = publisher._build_embed(post)

        assert "educational" in embed.footer.get("text", "")

    def test_platform_name(self):
        from publishers.discord import DiscordPublisher
        with patch("publishers.discord.settings"):
            publisher = DiscordPublisher(webhook_url="https://discord.com/api/webhooks/test")
        assert publisher.platform_name == "discord"
