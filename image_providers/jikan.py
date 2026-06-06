from typing import List
import httpx
from core.interfaces.image_provider import AbstractImageProvider
from config.logging import get_logger

logger = get_logger(__name__)

JIKAN_SEARCH_URL = "https://api.jikan.moe/v4/anime"


class JikanAnimeImageProvider(AbstractImageProvider):
    """Fetch official anime cover art from MyAnimeList via the free Jikan v4 API."""

    @property
    def provider_name(self) -> str:
        return "jikan"

    async def find_image(self, keywords: List[str]) -> str | None:
        query = " ".join(keywords)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    JIKAN_SEARCH_URL,
                    params={"q": query, "limit": 1},
                )
                if response.status_code == 429:
                    logger.warning("JikanAnimeImageProvider: rate limited")
                    return None
                response.raise_for_status()
                data = response.json()
        except Exception as exc:
            logger.error("JikanAnimeImageProvider: request failed: %s", exc)
            return None

        results = data.get("data", [])
        if not results:
            logger.info("JikanAnimeImageProvider: no results for '%s'", query)
            return None

        images = results[0].get("images", {})
        jpg = images.get("jpg", {})
        url = jpg.get("large_image_url") or jpg.get("image_url")
        if url:
            logger.info("JikanAnimeImageProvider: found image for '%s'", query)
        return url
