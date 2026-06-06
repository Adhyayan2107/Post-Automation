import asyncio
from typing import List
from core.interfaces.image_provider import AbstractImageProvider
from core.models.post import Post
from config.logging import get_logger

logger = get_logger(__name__)

MAX_CONCURRENT = 3

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "it", "its", "this", "that", "are",
    "was", "be", "as", "how", "what", "why", "when", "who", "which", "your",
    "my", "our", "their", "i", "you", "we", "they", "he", "she", "about",
    "into", "not", "can", "do", "if", "up", "out", "so", "just", "than",
    "more", "also", "will", "would", "could", "have", "has", "had",
    "ib", "igcse", "a-level", "alevel", "level",
}


class ImageAgent:
    def __init__(
        self,
        providers: List[AbstractImageProvider],
        anime_provider: AbstractImageProvider | None = None,
        movie_provider: AbstractImageProvider | None = None,
    ) -> None:
        self._providers = providers          # fallback providers (Pexels, Unsplash)
        self._anime_provider = anime_provider
        self._movie_provider = movie_provider

    async def find_image(self, post: Post) -> str | None:
        # For creative posts try the specialist provider first using the
        # explicit image_subject Claude returned (e.g. "Demon Slayer").
        if post.creative_angle == "anime" and self._anime_provider and post.image_subject:
            url = await self._try_provider(self._anime_provider, [post.image_subject])
            if url:
                return url

        if post.creative_angle == "movie" and self._movie_provider and post.image_subject:
            url = await self._try_provider(self._movie_provider, [post.image_subject])
            if url:
                return url

        # Fall back to concept-based search on Pexels / Unsplash.
        keywords = self._extract_keywords(post)
        for provider in self._providers:
            url = await self._try_provider(provider, keywords)
            if url:
                return url
        return None

    async def enrich_posts(self, posts: List[Post]) -> List[Post]:
        semaphore = asyncio.Semaphore(MAX_CONCURRENT)

        async def _enrich(post: Post) -> Post:
            async with semaphore:
                url = await self.find_image(post)
                if url:
                    post.image_url = url
            return post

        enriched = await asyncio.gather(*[_enrich(p) for p in posts])
        found = sum(1 for p in enriched if p.image_url)
        logger.info("ImageAgent: enriched %d/%d posts with images", found, len(posts))
        return list(enriched)

    async def _try_provider(
        self, provider: AbstractImageProvider, keywords: List[str]
    ) -> str | None:
        try:
            return await provider.find_image(keywords)
        except Exception as exc:
            logger.error(
                "ImageAgent: provider '%s' failed: %s", provider.provider_name, exc
            )
            return None

    def _extract_keywords(self, post: Post) -> List[str]:
        title = post.title

        # Creative posts: title is "[Hook] — [Concept]".
        # Pexels/Unsplash are stock sites — search the educational concept.
        if post.post_type == "creative" and " — " in title:
            _, concept_part = title.split(" — ", 1)
            search_text = concept_part
        else:
            search_text = title

        words = search_text.lower().split()
        keywords = [
            w.strip(".,!?;:\"'()[]—")
            for w in words
            if w.strip(".,!?;:\"'()[]—") and w.strip(".,!?;:\"'()[]—") not in STOPWORDS
        ]
        return keywords[:5]
