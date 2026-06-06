from typing import List
from uuid import UUID

from core.interfaces.content_generator import AbstractContentGenerator
from core.models.post import Post, PostStatus
from core.models.raw_content import RawContent
from config.logging import get_logger

logger = get_logger(__name__)


class ContentAgent:
    def __init__(self, generator: AbstractContentGenerator, post_repository=None) -> None:
        self._generator = generator
        self._repo = post_repository

    async def run(self, raw_contents: List[RawContent], run_id: UUID) -> List[Post]:
        logger.info(
            "ContentAgent: generating %s posts from %d raw items",
            self._generator.post_type,
            len(raw_contents),
        )
        posts = await self._generator.generate(raw_contents)

        for post in posts:
            post.run_id = run_id
            post.status = PostStatus.PENDING

        if self._repo:
            for post in posts:
                await self._repo.save(post)

        logger.info("ContentAgent: saved %d posts with status=pending", len(posts))
        return posts
