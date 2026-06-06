import json
import pytest
from uuid import uuid4
from unittest.mock import MagicMock, patch
from core.models.raw_content import RawContent
from core.models.post import Post, PostStatus


def _make_raw_content(n: int = 3) -> list[RawContent]:
    run_id = uuid4()
    return [
        RawContent(
            url=f"https://example.com/article-{i}",
            title=f"IB News Article {i}",
            body=f"Summary of article {i} about IB diploma changes.",
            source="google_news",
            run_id=run_id,
        )
        for i in range(n)
    ]


def _mock_claude_response(posts_json: list[dict]) -> MagicMock:
    content_block = MagicMock()
    content_block.text = json.dumps(posts_json)
    response = MagicMock()
    response.content = [content_block]
    return response


EDU_POSTS_JSON = [
    {
        "title": "IB Chemistry HL changes for 2026 — what you need to know",
        "body": "## What changed\n\nThe IBO updated the HL chemistry syllabus...\n\n**Key takeaways:**\n- New organic chemistry section\n- Updated IA criteria",
        "source_urls": ["https://example.com/article-0"],
        "target_subreddits": ["r/IBO", "r/igcse"],
        "target_platforms": ["reddit", "discord"],
    },
    {
        "title": "IGCSE Math Paper 2 tips that actually work",
        "body": "## Quick wins\n\nBased on the latest examiner report...",
        "source_urls": ["https://example.com/article-1"],
        "target_subreddits": ["r/igcse", "r/alevel"],
        "target_platforms": ["reddit", "discord"],
    },
]

ANIME_POSTS_JSON = [
    {
        "title": "Light Yagami's notebook logic — IB Theory of Knowledge in action",
        "body": "## The Hook\n\nWhen Light first picks up the Death Note...",
        "source_urls": ["https://example.com/article-0"],
        "target_subreddits": ["r/IBO"],
        "target_platforms": ["reddit", "discord"],
        "creative_angle": "anime",
    }
]

MOVIE_POSTS_JSON = [
    {
        "title": "Oppenheimer's moral crisis — IB Ethics perfectly illustrated",
        "body": "## The Hook\n\nThe Trinity test scene in Oppenheimer...",
        "source_urls": ["https://example.com/article-0"],
        "target_subreddits": ["r/IBO"],
        "target_platforms": ["discord"],
        "creative_angle": "movie",
    }
]


# ── Template rendering ──────────────────────────────────────────────────────

class TestTemplateRendering:
    def test_educational_template_renders(self):
        from jinja2 import Environment, FileSystemLoader
        from pathlib import Path
        env = Environment(loader=FileSystemLoader(str(Path("generators/prompts"))))
        tmpl = env.get_template("educational.jinja2")
        result = tmpl.render(
            raw_content_summaries="1. [news] Some article\n   URL: https://x.com\n   Body text",
            target_subreddits=["r/IBO", "r/igcse"],
            post_count=3,
        )
        assert "IBO" in result or "post" in result.lower()
        assert "JSON" in result

    def test_creative_anime_template_renders(self):
        from jinja2 import Environment, FileSystemLoader
        from pathlib import Path
        env = Environment(loader=FileSystemLoader(str(Path("generators/prompts"))))
        tmpl = env.get_template("creative_anime.jinja2")
        result = tmpl.render(
            raw_content_summaries="1. [news] Some article\n   URL: https://x.com\n   Body",
            target_subreddits=["r/IBO"],
            anime_list=["Naruto", "One Piece"],
            subject="History",
            post_count=1,
        )
        assert "Naruto" in result or "One Piece" in result
        assert "JSON" in result

    def test_creative_movies_template_renders(self):
        from jinja2 import Environment, FileSystemLoader
        from pathlib import Path
        env = Environment(loader=FileSystemLoader(str(Path("generators/prompts"))))
        tmpl = env.get_template("creative_movies.jinja2")
        result = tmpl.render(
            raw_content_summaries="1. [news] Some article\n   URL: https://x.com\n   Body",
            target_subreddits=["r/IBO"],
            post_count=1,
        )
        assert "JSON" in result


# ── EducationalPostGenerator ────────────────────────────────────────────────

class TestEducationalPostGenerator:
    def test_returns_post_objects(self):
        raw = _make_raw_content(5)
        mock_response = _mock_claude_response(EDU_POSTS_JSON)

        with patch("generators.educational_post.anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_cls.return_value = mock_client

            from importlib import reload
            import generators.educational_post as mod
            reload(mod)
            gen = mod.EducationalPostGenerator()
            gen._client = mock_client

            import asyncio
            posts = asyncio.run(gen.generate(raw))

        assert len(posts) > 0
        for p in posts:
            assert isinstance(p, Post)
            assert p.post_type == "educational"
            assert p.title
            assert p.body

    def test_posts_have_pending_status(self):
        raw = _make_raw_content(3)
        mock_response = _mock_claude_response(EDU_POSTS_JSON)

        with patch("generators.educational_post.anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_cls.return_value = mock_client

            from importlib import reload
            import generators.educational_post as mod
            reload(mod)
            gen = mod.EducationalPostGenerator()
            gen._client = mock_client

            import asyncio
            posts = asyncio.run(gen.generate(raw))

        for p in posts:
            assert p.status == PostStatus.PENDING

    def test_parses_json_with_code_fences(self):
        raw = _make_raw_content(3)
        fenced = "```json\n" + json.dumps(EDU_POSTS_JSON) + "\n```"
        content_block = MagicMock()
        content_block.text = fenced
        mock_response = MagicMock()
        mock_response.content = [content_block]

        with patch("generators.educational_post.anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_cls.return_value = mock_client

            from importlib import reload
            import generators.educational_post as mod
            reload(mod)
            gen = mod.EducationalPostGenerator()
            gen._client = mock_client

            import asyncio
            posts = asyncio.run(gen.generate(raw))

        assert len(posts) > 0

    def test_handles_api_failure_gracefully(self):
        raw = _make_raw_content(3)

        with patch("generators.educational_post.anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = Exception("API down")
            mock_cls.return_value = mock_client

            from importlib import reload
            import generators.educational_post as mod
            reload(mod)
            gen = mod.EducationalPostGenerator()
            gen._client = mock_client

            import asyncio
            posts = asyncio.run(gen.generate(raw))

        assert posts == []


# ── CreativePostGenerator ───────────────────────────────────────────────────

class TestCreativePostGenerator:
    def _run_with_mock(self, angle: str, posts_json: list[dict]) -> list[Post]:
        import random
        raw = _make_raw_content(5)
        mock_response = _mock_claude_response(posts_json)

        with patch("generators.creative_post.anthropic.Anthropic") as mock_cls, \
             patch("generators.creative_post.random.choice", side_effect=[angle, "History"]):
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_cls.return_value = mock_client

            from importlib import reload
            import generators.creative_post as mod
            reload(mod)
            gen = mod.CreativePostGenerator()
            gen._client = mock_client

            import asyncio
            # Only generate 1 to keep test deterministic
            gen._client.messages.create.return_value = mock_response
            posts = asyncio.run(gen._generate_one(raw, angle))

        return [posts] if posts else []

    def test_anime_post_has_correct_fields(self):
        posts = self._run_with_mock("anime", ANIME_POSTS_JSON)
        assert len(posts) == 1
        p = posts[0]
        assert p.post_type == "creative"
        assert p.creative_angle == "anime"
        assert p.status == PostStatus.PENDING

    def test_movie_post_has_correct_fields(self):
        posts = self._run_with_mock("movie", MOVIE_POSTS_JSON)
        assert len(posts) == 1
        p = posts[0]
        assert p.post_type == "creative"
        assert p.creative_angle == "movie"


# ── ContentAgent ────────────────────────────────────────────────────────────

class TestContentAgent:
    @pytest.mark.asyncio
    async def test_agent_saves_posts_with_pending_status(self):
        from agents.content_agent import ContentAgent
        run_id = uuid4()
        raw = _make_raw_content(3)

        mock_gen = MagicMock()
        pending_posts = [
            Post(title="T1", body="B1", post_type="educational", run_id=run_id),
            Post(title="T2", body="B2", post_type="educational", run_id=run_id),
        ]
        mock_gen.post_type = "educational"
        mock_gen.generate = MagicMock(return_value=_async_return(pending_posts))

        mock_repo = MagicMock()
        mock_repo.save = MagicMock(side_effect=lambda p: _async_return(p))

        agent = ContentAgent(generator=mock_gen, post_repository=mock_repo)
        posts = await agent.run(raw, run_id)

        assert len(posts) == 2
        assert mock_repo.save.call_count == 2
        for p in posts:
            assert p.status == PostStatus.PENDING
            assert p.run_id == run_id

    @pytest.mark.asyncio
    async def test_agent_works_without_repo(self):
        from agents.content_agent import ContentAgent
        run_id = uuid4()
        raw = _make_raw_content(2)

        mock_gen = MagicMock()
        mock_gen.post_type = "educational"
        mock_gen.generate = MagicMock(return_value=_async_return([
            Post(title="T", body="B", post_type="educational", run_id=run_id)
        ]))

        agent = ContentAgent(generator=mock_gen)
        posts = await agent.run(raw, run_id)
        assert len(posts) == 1


# ── CreativeAgent ───────────────────────────────────────────────────────────

class TestCreativeAgent:
    @pytest.mark.asyncio
    async def test_creative_agent_saves_posts(self):
        from agents.creative_agent import CreativeAgent
        run_id = uuid4()
        raw = _make_raw_content(3)

        creative_posts = [
            Post(title="Naruto — ToK", body="B", post_type="creative", creative_angle="anime", run_id=run_id),
        ]
        mock_gen = MagicMock()
        mock_gen.post_type = "creative"
        mock_gen.generate = MagicMock(return_value=_async_return(creative_posts))

        mock_repo = MagicMock()
        mock_repo.save = MagicMock(side_effect=lambda p: _async_return(p))

        agent = CreativeAgent(generator=mock_gen, post_repository=mock_repo)
        posts = await agent.run(raw, run_id)

        assert len(posts) == 1
        assert posts[0].creative_angle == "anime"
        mock_repo.save.assert_called_once()


# ── helpers ─────────────────────────────────────────────────────────────────

async def _async_return(value):
    return value
