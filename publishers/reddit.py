import asyncio
import praw
import praw.exceptions
from core.interfaces.publisher import AbstractPublisher
from core.models.post import Post
from config.settings import settings
from config.logging import get_logger

logger = get_logger(__name__)

POST_DELAY_SECONDS = 10


class RedditPublisher(AbstractPublisher):
    def __init__(self, reddit_instance: praw.Reddit | None = None) -> None:
        self._reddit = reddit_instance or praw.Reddit(
            client_id=settings.reddit.client_id,
            client_secret=settings.reddit.client_secret,
            username=settings.reddit.username,
            password=settings.reddit.password,
            user_agent=settings.reddit.user_agent,
        )

    @property
    def platform_name(self) -> str:
        return "reddit"

    async def publish(self, post: Post) -> bool:
        if settings.app.dry_run:
            for sub in post.target_subreddits:
                logger.info(
                    "[DRY RUN] Would post to %s — title: %r",
                    sub,
                    post.title[:80],
                )
            return True

        success = True
        for i, sub_name in enumerate(post.target_subreddits):
            if i > 0:
                await asyncio.sleep(POST_DELAY_SECONDS)
            try:
                subreddit = self._reddit.subreddit(sub_name.lstrip("r/"))
                if post.image_url:
                    submission = subreddit.submit(
                        title=post.title,
                        url=post.image_url,
                    )
                    submission.reply(post.body[:10000])
                else:
                    subreddit.submit(
                        title=post.title,
                        selftext=post.body[:40000],
                    )
                logger.info("Posted to %s — post id: %s", sub_name, post.id)
            except praw.exceptions.APIException as exc:
                logger.error("Reddit API error for %s: %s", sub_name, exc)
                success = False
            except Exception as exc:
                logger.error("Reddit unexpected error for %s: %s", sub_name, exc)
                success = False

        return success
