from typing import List
import httpx
from core.interfaces.image_provider import AbstractImageProvider
from config.settings import settings
from config.logging import get_logger

logger = get_logger(__name__)

SEARCH_URL = "https://api.unsplash.com/search/photos"


class UnsplashImageProvider(AbstractImageProvider):
    @property
    def provider_name(self) -> str:
        return "unsplash"

    async def find_image(self, keywords: List[str]) -> str | None:
        query = " ".join(keywords)
        headers = {"Authorization": f"Client-ID {settings.unsplash.access_key}"}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    SEARCH_URL,
                    headers=headers,
                    params={"query": query, "per_page": 5},
                )
                if response.status_code == 403:
                    logger.warning("UnsplashImageProvider: rate limited (403)")
                    return None
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            logger.error("UnsplashImageProvider: HTTP error %s", exc)
            return None
        except Exception as exc:
            logger.error("UnsplashImageProvider: request failed: %s", exc)
            return None

        results = data.get("results", [])
        if not results:
            logger.info("UnsplashImageProvider: no results for '%s'", query)
            return None

        url = results[0].get("urls", {}).get("regular")
        if url:
            logger.info("UnsplashImageProvider: found image for '%s'", query)
        return url
