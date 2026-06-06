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
    def __init__(self, providers: List[AbstractImageProvider]) -> None:
        self._providers = providers

    async def find_image(self, post: Post) -> str | None:
        keywords = self._extract_keywords(post)
        for provider in self._providers:
            try:
                url = await provider.find_image(keywords)
                if url:
                    return url
            except Exception as exc:
                logger.error("ImageAgent: provider '%s' failed: %s", provider.provider_name, exc)
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

    def _extract_keywords(self, post: Post) -> List[str]:
        title = post.title

        # For creative posts the title is "[Hook] — [Concept]".
        # Pexels is a stock photo site — it has concept/subject photos but not
        # anime stills or movie screenshots. Search the educational concept part.
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
