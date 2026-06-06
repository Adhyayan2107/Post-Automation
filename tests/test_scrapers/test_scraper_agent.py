import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from agents.scraper_agent import ScraperAgent
from core.models.raw_content import RawContent


def _make_scraper(name: str, items: list[RawContent]) -> MagicMock:
    scraper = MagicMock()
    scraper.name = name
    scraper.scrape_with_run_id = AsyncMock(return_value=items)
    return scraper


def _make_content(url: str, run_id, source: str = "test") -> RawContent:
    return RawContent(url=url, title=f"Title {url}", source=source, run_id=run_id)


@pytest.mark.asyncio
async def test_scraper_agent_aggregates_results():
    run_id = uuid4()
    a = _make_scraper("a", [_make_content("https://a.com/1", run_id), _make_content("https://a.com/2", run_id)])
    b = _make_scraper("b", [_make_content("https://b.com/1", run_id)])

    agent = ScraperAgent([a, b])
    results = await agent.run(run_id)

    assert len(results) == 3


@pytest.mark.asyncio
async def test_scraper_agent_deduplicates_by_url():
    run_id = uuid4()
    shared = _make_content("https://shared.com/article", run_id)

    a = _make_scraper("a", [shared, _make_content("https://a.com/unique", run_id)])
    b = _make_scraper("b", [shared, _make_content("https://b.com/unique", run_id)])

    agent = ScraperAgent([a, b])
    results = await agent.run(run_id)

    urls = [r.url for r in results]
    assert len(urls) == len(set(urls)), "Duplicate URLs present"
    assert len(results) == 3  # shared deduped + 2 uniques


@pytest.mark.asyncio
async def test_scraper_agent_continues_if_one_fails():
    run_id = uuid4()

    failing = MagicMock()
    failing.name = "failing"
    failing.scrape_with_run_id = AsyncMock(side_effect=Exception("Boom"))

    working = _make_scraper("working", [_make_content("https://ok.com/1", run_id)])

    agent = ScraperAgent([failing, working])
    results = await agent.run(run_id)

    assert len(results) == 1
    assert results[0].url == "https://ok.com/1"


@pytest.mark.asyncio
async def test_scraper_agent_empty_scrapers():
    run_id = uuid4()
    agent = ScraperAgent([])
    results = await agent.run(run_id)
    assert results == []


@pytest.mark.asyncio
async def test_scraper_agent_runs_in_parallel():
    """Verify all scrapers are called with the correct run_id."""
    run_id = uuid4()
    scrapers = [_make_scraper(f"s{i}", []) for i in range(5)]

    agent = ScraperAgent(scrapers)
    await agent.run(run_id)

    for s in scrapers:
        s.scrape_with_run_id.assert_called_once_with(run_id)
