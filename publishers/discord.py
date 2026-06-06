from discord_webhook import DiscordWebhook, DiscordEmbed
from core.interfaces.publisher import AbstractPublisher
from core.models.post import Post
from config.settings import settings
from config.logging import get_logger

logger = get_logger(__name__)

EMBED_COLOUR = 0x5865F2  # Discord blurple
MAX_TITLE = 256
MAX_DESCRIPTION = 4096


class DiscordPublisher(AbstractPublisher):
    def __init__(self, webhook_url: str | None = None) -> None:
        self._webhook_url = webhook_url or settings.discord.webhook_url

    @property
    def platform_name(self) -> str:
        return "discord"

    async def publish(self, post: Post) -> bool:
        embed = self._build_embed(post)

        if settings.app.dry_run:
            logger.info(
                "[DRY RUN] Would send Discord embed — title: %r, colour: %s",
                embed.title,
                embed.color,
            )
            return True

        try:
            webhook = DiscordWebhook(url=self._webhook_url)
            webhook.add_embed(embed)
            response = webhook.execute()
            if response and hasattr(response, "status_code") and response.status_code >= 400:
                logger.error("Discord webhook returned %s", response.status_code)
                return False
            logger.info("Posted to Discord — post id: %s", post.id)
            return True
        except Exception as exc:
            logger.error("Discord publish failed for post %s: %s", post.id, exc)
            return False

    def _build_embed(self, post: Post) -> DiscordEmbed:
        embed = DiscordEmbed(
            title=post.title[:MAX_TITLE],
            description=post.body[:MAX_DESCRIPTION],
            color=EMBED_COLOUR,
        )
        if post.image_url:
            embed.set_image(url=post.image_url)
        embed.set_footer(text=f"EduBot • {post.post_type}")
        return embed
