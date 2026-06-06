import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from core.models.post import Post, PostStatus


def _make_post(title: str = "IB Chemistry exam tips for Paper 2") -> Post:
    return Post(
        title=title,
        body="Body text",
        post_type="educational",
        run_id=uuid4(),
    )


def _mock_provider(name: str, return_url: str | None) -> MagicMock:
    p = MagicMock()
    p.provider_name = name
    p.find_image = AsyncMock(return_value=return_url)
    return p


# ── PexelsImageProvider ─────────────────────────────────────────────────────

class TestPexelsImageProvider:
    @pytest.mark.asyncio
    async def test_returns_landscape_image_url(self):
        mock_data = {
            "photos": [
                {"width": 1920, "height": 1080, "src": {"medium": "https://pexels.com/img1.jpg"}},
            ]
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_data
        mock_resp.raise_for_status = MagicMock()

        with patch("image_providers.pexels.httpx.AsyncClient") as mock_cls, \
             patch("image_providers.pexels.settings") as mock_settings:
            mock_settings.pexels.api_key = "test-key"
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            from image_providers.pexels import PexelsImageProvider
            provider = PexelsImageProvider()
            url = await provider.find_image(["chemistry", "exam"])

        assert url == "https://pexels.com/img1.jpg"

    @pytest.mark.asyncio
    async def test_returns_none_on_rate_limit(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 429

        with patch("image_providers.pexels.httpx.AsyncClient") as mock_cls, \
             patch("image_providers.pexels.settings") as mock_settings:
            mock_settings.pexels.api_key = "test-key"
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            from image_providers.pexels import PexelsImageProvider
            provider = PexelsImageProvider()
            url = await provider.find_image(["chemistry"])

        assert url is None

    @pytest.mark.asyncio
    async def test_returns_none_when_no_photos(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"photos": []}
        mock_resp.raise_for_status = MagicMock()

        with patch("image_providers.pexels.httpx.AsyncClient") as mock_cls, \
             patch("image_providers.pexels.settings") as mock_settings:
            mock_settings.pexels.api_key = "test-key"
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            from image_providers.pexels import PexelsImageProvider
            provider = PexelsImageProvider()
            url = await provider.find_image(["noresults"])

        assert url is None


# ── UnsplashImageProvider ───────────────────────────────────────────────────

class TestUnsplashImageProvider:
    @pytest.mark.asyncio
    async def test_returns_image_url(self):
        mock_data = {"results": [{"urls": {"regular": "https://unsplash.com/img1.jpg"}}]}
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_data
        mock_resp.raise_for_status = MagicMock()

        with patch("image_providers.unsplash.httpx.AsyncClient") as mock_cls, \
             patch("image_providers.unsplash.settings") as mock_settings:
            mock_settings.unsplash.access_key = "test-key"
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            from image_providers.unsplash import UnsplashImageProvider
            provider = UnsplashImageProvider()
            url = await provider.find_image(["biology", "cell"])

        assert url == "https://unsplash.com/img1.jpg"

    @pytest.mark.asyncio
    async def test_returns_none_on_403(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 403

        with patch("image_providers.unsplash.httpx.AsyncClient") as mock_cls, \
             patch("image_providers.unsplash.settings") as mock_settings:
            mock_settings.unsplash.access_key = "test-key"
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            from image_providers.unsplash import UnsplashImageProvider
            provider = UnsplashImageProvider()
            url = await provider.find_image(["test"])

        assert url is None


# ── ImageAgent ──────────────────────────────────────────────────────────────

class TestImageAgent:
    @pytest.mark.asyncio
    async def test_returns_first_provider_result(self):
        from agents.image_agent import ImageAgent
        pexels = _mock_provider("pexels", "https://pexels.com/img.jpg")
        unsplash = _mock_provider("unsplash", "https://unsplash.com/img.jpg")

        agent = ImageAgent([pexels, unsplash])
        url = await agent.find_image(_make_post())

        assert url == "https://pexels.com/img.jpg"
        pexels.find_image.assert_called_once()
        unsplash.find_image.assert_not_called()

    @pytest.mark.asyncio
    async def test_falls_back_to_unsplash_when_pexels_returns_none(self):
        from agents.image_agent import ImageAgent
        pexels = _mock_provider("pexels", None)
        unsplash = _mock_provider("unsplash", "https://unsplash.com/img.jpg")

        agent = ImageAgent([pexels, unsplash])
        url = await agent.find_image(_make_post())

        assert url == "https://unsplash.com/img.jpg"
        pexels.find_image.assert_called_once()
        unsplash.find_image.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_none_when_all_providers_fail(self):
        from agents.image_agent import ImageAgent
        agent = ImageAgent([
            _mock_provider("pexels", None),
            _mock_provider("unsplash", None),
        ])
        url = await agent.find_image(_make_post())
        assert url is None

    @pytest.mark.asyncio
    async def test_enrich_posts_sets_image_url(self):
        from agents.image_agent import ImageAgent
        posts = [_make_post("IB Biology"), _make_post("IGCSE Chemistry")]
        provider = _mock_provider("pexels", "https://pexels.com/img.jpg")

        agent = ImageAgent([provider])
        enriched = await agent.enrich_posts(posts)

        assert all(p.image_url == "https://pexels.com/img.jpg" for p in enriched)
        assert provider.find_image.call_count == 2

    @pytest.mark.asyncio
    async def test_enrich_posts_handles_provider_exception(self):
        from agents.image_agent import ImageAgent
        posts = [_make_post("IB History")]
        provider = _mock_provider("pexels", None)
        provider.find_image = AsyncMock(side_effect=Exception("Network error"))

        agent = ImageAgent([provider])
        enriched = await agent.enrich_posts(posts)

        assert enriched[0].image_url is None


# ── Keyword extraction ──────────────────────────────────────────────────────

class TestKeywordExtraction:
    def test_strips_stopwords(self):
        from agents.image_agent import ImageAgent
        agent = ImageAgent([])
        kw = agent._extract_keywords("What are the best tips for IB Chemistry exam")
        assert "what" not in kw
        assert "are" not in kw
        assert "the" not in kw
        assert "for" not in kw

    def test_returns_at_most_five_keywords(self):
        from agents.image_agent import ImageAgent
        agent = ImageAgent([])
        kw = agent._extract_keywords("IB Chemistry Biology Physics History Mathematics Economics")
        assert len(kw) <= 5

    def test_strips_punctuation(self):
        from agents.image_agent import ImageAgent
        agent = ImageAgent([])
        kw = agent._extract_keywords("Chemistry: acids, bases, and pH!")
        assert "chemistry:" not in kw
        assert "acids," not in kw
        assert "ph!" not in kw

    def test_handles_empty_title(self):
        from agents.image_agent import ImageAgent
        agent = ImageAgent([])
        kw = agent._extract_keywords("")
        assert kw == []
