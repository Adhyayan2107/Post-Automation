import pytest
from uuid import uuid4
from unittest.mock import MagicMock, patch
from core.models.raw_content import RawContent


def _make_mock_post(title: str, permalink: str, selftext: str = "") -> MagicMock:
    post = MagicMock()
    post.title = title
    post.permalink = permalink
    post.selftext = selftext
    return post


@pytest.mark.asyncio
async def test_reddit_scraper_returns_raw_content():
    run_id = uuid4()

    mock_posts = [
        _make_mock_post("IB Chemistry tips", "/r/IBO/comments/abc", "Here are some tips..."),
        _make_mock_post("IGCSE Math question", "/r/igcse/comments/def", ""),
    ]

    mock_subreddit = MagicMock()
    mock_subreddit.top.return_value = mock_posts

    mock_reddit = MagicMock()
    mock_reddit.subreddit.return_value = mock_subreddit

    with patch("scrapers.reddit_scraper.praw.Reddit", return_value=mock_reddit):
        from scrapers.reddit_scraper import RedditScraper
        scraper = RedditScraper()
        results = await scraper.scrape_with_run_id(run_id)

    assert len(results) > 0
    for item in results:
        assert isinstance(item, RawContent)
        assert item.url.startswith("https://www.reddit.com")
        assert item.source == "reddit"
        assert item.run_id == run_id


@pytest.mark.asyncio
async def test_reddit_scraper_handles_subreddit_failure():
    run_id = uuid4()

    mock_reddit = MagicMock()
    mock_reddit.subreddit.side_effect = Exception("API error")

    with patch("scrapers.reddit_scraper.praw.Reddit", return_value=mock_reddit):
        from scrapers.reddit_scraper import RedditScraper
        scraper = RedditScraper()
        results = await scraper.scrape_with_run_id(run_id)

    assert results == []


@pytest.mark.asyncio
async def test_reddit_scraper_includes_selftext_in_body():
    run_id = uuid4()
    selftext = "Detailed question about the IB extended essay..."

    mock_post = _make_mock_post("EE Help", "/r/IBO/comments/xyz", selftext)
    mock_subreddit = MagicMock()
    mock_subreddit.top.return_value = [mock_post]
    mock_reddit = MagicMock()
    mock_reddit.subreddit.return_value = mock_subreddit

    with patch("scrapers.reddit_scraper.praw.Reddit", return_value=mock_reddit):
        from scrapers.reddit_scraper import RedditScraper
        scraper = RedditScraper()
        results = await scraper.scrape_with_run_id(run_id)

    assert any(r.body == selftext for r in results)
