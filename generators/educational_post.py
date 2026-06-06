import json
from pathlib import Path
from typing import List
from uuid import uuid4

import anthropic
from jinja2 import Environment, FileSystemLoader

from core.interfaces.content_generator import AbstractContentGenerator
from core.models.post import Post, PostStatus
from core.models.raw_content import RawContent
from config.settings import settings
from config.logging import get_logger

logger = get_logger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"
TARGET_SUBREDDITS = ["r/IBO", "r/igcse", "r/6thForm", "r/alevel"]
BATCH_SIZE = 5
POSTS_PER_RUN = 4  # aim for 3–5; Claude decides final count within that
MODEL = "claude-sonnet-4-6"


class EducationalPostGenerator(AbstractContentGenerator):
    def __init__(self) -> None:
        self._client = anthropic.Anthropic(api_key=settings.claude.api_key)
        self._env = Environment(loader=FileSystemLoader(str(PROMPTS_DIR)))

    @property
    def post_type(self) -> str:
        return "educational"

    async def generate(self, raw_contents: List[RawContent]) -> List[Post]:
        posts: List[Post] = []
        batches = [raw_contents[i:i + BATCH_SIZE] for i in range(0, len(raw_contents), BATCH_SIZE)]

        for batch in batches[:3]:  # cap at 3 batches to control API spend
            try:
                batch_posts = await self._generate_batch(batch)
                posts.extend(batch_posts)
                if len(posts) >= POSTS_PER_RUN:
                    break
            except Exception as exc:
                logger.error("EducationalPostGenerator: batch failed: %s", exc)

        logger.info("EducationalPostGenerator: generated %d posts", len(posts))
        return posts[:POSTS_PER_RUN]

    async def _generate_batch(self, batch: List[RawContent]) -> List[Post]:
        summaries = self._format_summaries(batch)
        template = self._env.get_template("educational.jinja2")
        prompt = template.render(
            raw_content_summaries=summaries,
            target_subreddits=TARGET_SUBREDDITS,
            post_count=min(POSTS_PER_RUN, 5),
        )

        response = self._client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=[
                {
                    "type": "text",
                    "text": "You are an expert IB/IGCSE/A-Level education content creator.",
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": prompt}],
        )

        raw_text = response.content[0].text.strip()
        return self._parse_response(raw_text, batch)

    def _parse_response(self, raw_text: str, source_batch: List[RawContent]) -> List[Post]:
        # Strip markdown code fences if Claude added them
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1]
            raw_text = raw_text.rsplit("```", 1)[0].strip()

        try:
            items = json.loads(raw_text)
        except json.JSONDecodeError:
            import re
            match = re.search(r"\[.*\]", raw_text, re.DOTALL)
            if match:
                items = json.loads(match.group())
            else:
                raise
        source_urls = [rc.url for rc in source_batch]
        run_id = source_batch[0].run_id if source_batch else uuid4()

        posts = []
        for item in items:
            posts.append(Post(
                title=item["title"],
                body=item["body"],
                post_type=self.post_type,
                source_urls=item.get("source_urls") or source_urls,
                target_subreddits=item.get("target_subreddits") or TARGET_SUBREDDITS,
                target_platforms=item.get("target_platforms") or ["reddit", "discord"],
                status=PostStatus.PENDING,
                run_id=run_id,
            ))
        return posts

    def _format_summaries(self, batch: List[RawContent]) -> str:
        parts = []
        for i, rc in enumerate(batch, 1):
            parts.append(f"{i}. [{rc.source}] {rc.title}\n   URL: {rc.url}\n   {rc.body[:300]}")
        return "\n\n".join(parts)
