import json
import random
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
POSTS_PER_RUN = 3
MODEL = "claude-sonnet-4-6"

ANIME_LIST = [
    "Naruto", "One Piece", "Attack on Titan", "Death Note",
    "Fullmetal Alchemist", "Demon Slayer", "Hunter x Hunter",
    "Code Geass", "Steins;Gate", "Vinland Saga",
]

SUBJECTS = [
    "History", "Biology", "Chemistry", "Physics", "Economics",
    "Mathematics", "English Literature", "Psychology", "Geography",
]

CREATIVE_ANGLES = ["anime", "movie"]


class CreativePostGenerator(AbstractContentGenerator):
    def __init__(self) -> None:
        self._client = anthropic.Anthropic(api_key=settings.claude.api_key)
        self._env = Environment(loader=FileSystemLoader(str(PROMPTS_DIR)))

    @property
    def post_type(self) -> str:
        return "creative"

    async def generate(self, raw_contents: List[RawContent]) -> List[Post]:
        posts: List[Post] = []
        sample = raw_contents[:10]  # take first 10 items as context

        for _ in range(POSTS_PER_RUN):
            angle = random.choice(CREATIVE_ANGLES)
            try:
                post = await self._generate_one(sample, angle)
                if post:
                    posts.append(post)
            except Exception as exc:
                logger.error("CreativePostGenerator: failed angle '%s': %s", angle, exc)

        logger.info("CreativePostGenerator: generated %d posts", len(posts))
        return posts

    async def _generate_one(self, source: List[RawContent], angle: str) -> Post | None:
        summaries = self._format_summaries(source)
        subject = random.choice(SUBJECTS)

        if angle == "anime":
            template = self._env.get_template("creative_anime.jinja2")
            prompt = template.render(
                raw_content_summaries=summaries,
                target_subreddits=TARGET_SUBREDDITS,
                anime_list=ANIME_LIST,
                subject=subject,
                post_count=1,
            )
        else:
            template = self._env.get_template("creative_movies.jinja2")
            prompt = template.render(
                raw_content_summaries=summaries,
                target_subreddits=TARGET_SUBREDDITS,
                post_count=1,
            )

        response = self._client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=[
                {
                    "type": "text",
                    "text": "You are a creative IB/IGCSE/A-Level education content creator.",
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": prompt}],
        )

        raw_text = response.content[0].text.strip()
        items = self._parse_response(raw_text)
        if not items:
            return None

        item = items[0]
        run_id = source[0].run_id if source else uuid4()
        return Post(
            title=item["title"],
            body=item["body"],
            post_type=self.post_type,
            creative_angle=angle,
            source_urls=item.get("source_urls") or [rc.url for rc in source[:3]],
            target_subreddits=item.get("target_subreddits") or TARGET_SUBREDDITS,
            target_platforms=item.get("target_platforms") or ["reddit", "discord"],
            status=PostStatus.PENDING,
            run_id=run_id,
        )

    def _parse_response(self, raw_text: str) -> list:
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1]
            raw_text = raw_text.rsplit("```", 1)[0].strip()
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            # Last-resort: extract the first JSON array with regex
            import re
            match = re.search(r"\[.*\]", raw_text, re.DOTALL)
            if match:
                return json.loads(match.group())
            raise

    def _format_summaries(self, batch: List[RawContent]) -> str:
        parts = []
        for i, rc in enumerate(batch, 1):
            parts.append(f"{i}. [{rc.source}] {rc.title}\n   URL: {rc.url}\n   {rc.body[:200]}")
        return "\n\n".join(parts)
