from typing import List
import httpx
from core.interfaces.image_provider import AbstractImageProvider
from config.settings import settings
from config.logging import get_logger

logger = get_logger(__name__)

TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/multi"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"


class TMDbImageProvider(AbstractImageProvider):
    """Fetch movie/TV show posters from TMDb (free API key required: TMDB_API_KEY)."""

    @property
    def provider_name(self) -> str:
        return "tmdb"

    async def find_image(self, keywords: List[str]) -> str | None:
        if not settings.tmdb.api_key:
            return None
        query = " ".join(keywords)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    TMDB_SEARCH_URL,
                    params={"api_key": settings.tmdb.api_key, "query": query, "include_adult": "false"},
                )
                response.raise_for_status()
                data = response.json()
        except Exception as exc:
            logger.error("TMDbImageProvider: request failed: %s", exc)
            return None

        for result in data.get("results", []):
            poster_path = result.get("poster_path")
            if poster_path:
                url = f"{TMDB_IMAGE_BASE}{poster_path}"
                logger.info("TMDbImageProvider: found poster for '%s'", query)
                return url

        logger.info("TMDbImageProvider: no poster for '%s'", query)
        return None
