from typing import List
import httpx
from core.interfaces.image_provider import AbstractImageProvider
from config.settings import settings
from config.logging import get_logger

logger = get_logger(__name__)

SEARCH_URL = "https://api.pexels.com/v1/search"


class PexelsImageProvider(AbstractImageProvider):
    @property
    def provider_name(self) -> str:
        return "pexels"

    async def find_image(self, keywords: List[str]) -> str | None:
        query = " ".join(keywords)
        headers = {"Authorization": settings.pexels.api_key}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    SEARCH_URL,
                    headers=headers,
                    params={"query": query, "per_page": 5, "orientation": "landscape"},
                )
                if response.status_code == 429:
                    logger.warning("PexelsImageProvider: rate limited")
                    return None
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            logger.error("PexelsImageProvider: HTTP error %s", exc)
            return None
        except Exception as exc:
            logger.error("PexelsImageProvider: request failed: %s", exc)
            return None

        photos = data.get("photos", [])
        # prefer landscape (width > height)
        for photo in photos:
            if photo.get("width", 0) > photo.get("height", 0):
                url = photo.get("src", {}).get("medium")
                if url:
                    logger.info("PexelsImageProvider: found image for '%s'", query)
                    return url

        # fallback: first result regardless of orientation
        if photos:
            return photos[0].get("src", {}).get("medium")

        logger.info("PexelsImageProvider: no results for '%s'", query)
        return None
