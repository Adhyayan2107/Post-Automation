import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, patch, MagicMock
from scrapers.news_scraper import NewsScraper
from core.models.raw_content import RawContent

MOCK_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Google News</title>
    <item>
      <title>IB Diploma Results 2025</title>
      <link>https://example.com/ib-results</link>
      <description>Record pass rates for IB diploma candidates.</description>
    </item>
    <item>
      <title>New IB Subject Guide Released</title>
      <link>https://example.com/ib-guide</link>
      <description>IBO releases updated subject guides for 2026.</description>
    </item>
  </channel>
</rss>"""


@pytest.mark.asyncio
async def test_news_scraper_returns_raw_content():
    run_id = uuid4()
    mock_response = MagicMock()
    mock_response.text = MOCK_RSS
    mock_response.raise_for_status = MagicMock()

    with patch("scrapers.news_scraper.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        scraper = NewsScraper()
        results = await scraper.scrape_with_run_id(run_id)

    assert len(results) > 0
    for item in results:
        assert isinstance(item, RawContent)
        assert item.url.startswith("http")
        assert item.title
        assert item.source == "google_news"
        assert item.run_id == run_id


@pytest.mark.asyncio
async def test_news_scraper_deduplicates_urls():
    run_id = uuid4()
    # Same item returned by multiple queries
    dup_rss = """<?xml version="1.0"?>
    <rss version="2.0"><channel>
      <item><title>Same Article</title><link>https://example.com/same</link><description>Dup</description></item>
    </channel></rss>"""

    mock_response = MagicMock()
    mock_response.text = dup_rss
    mock_response.raise_for_status = MagicMock()

    with patch("scrapers.news_scraper.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        scraper = NewsScraper()
        results = await scraper.scrape_with_run_id(run_id)

    urls = [r.url for r in results]
    assert len(urls) == len(set(urls)), "Duplicate URLs found"


@pytest.mark.asyncio
async def test_news_scraper_handles_http_error():
    run_id = uuid4()
    with patch("scrapers.news_scraper.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("Network error"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_cls.return_value = mock_client

        scraper = NewsScraper()
        results = await scraper.scrape_with_run_id(run_id)

    assert results == []
