from discord_webhook import DiscordWebhook, DiscordEmbed
from core.interfaces.publisher import AbstractPublisher
from core.models.post import Post
from config.settings import settings
from config.logging import get_logger

logger = get_logger(__name__)

EMBED_COLOUR_EDUCATIONAL = 0x3B82F6  # blue
EMBED_COLOUR_CREATIVE    = 0xA855F7  # purple
MAX_TITLE       = 256
MAX_DESCRIPTION = 4096


class DiscordPublisher(AbstractPublisher):
    def __init__(
        self,
        webhook_educational: str | None = None,
        webhook_creative: str | None = None,
    ) -> None:
        self._webhook_educational = webhook_educational or settings.discord.webhook_educational
        self._webhook_creative    = webhook_creative    or settings.discord.webhook_creative

    @property
    def platform_name(self) -> str:
        return "discord"

    def _get_webhook(self, post: Post) -> str:
        if post.post_type == "creative":
            return self._webhook_creative or self._webhook_educational
        return self._webhook_educational or self._webhook_creative

    async def publish(self, post: Post) -> bool:
        webhook_url = self._get_webhook(post)
        if not webhook_url:
            logger.warning("No Discord webhook configured — skipping post %s", post.id)
            return False

        embed = self._build_embed(post)

        if settings.app.dry_run:
            channel = "fun-to-learn" if post.post_type == "creative" else "news-and-updates"
            logger.info("[DRY RUN] Would send to #%s — title: %r", channel, post.title[:80])
            return True

        try:
            webhook = DiscordWebhook(url=webhook_url)
            webhook.add_embed(embed)
            response = webhook.execute()
            if response and hasattr(response, "status_code") and response.status_code >= 400:
                logger.error("Discord webhook returned %s for post %s", response.status_code, post.id)
                return False
            channel = "fun-to-learn" if post.post_type == "creative" else "news-and-updates"
            logger.info("Posted to #%s — post id: %s", channel, post.id)
            return True
        except Exception as exc:
            logger.error("Discord publish failed for post %s: %s", post.id, exc)
            return False

    def _build_embed(self, post: Post) -> DiscordEmbed:
        colour = EMBED_COLOUR_CREATIVE if post.post_type == "creative" else EMBED_COLOUR_EDUCATIONAL
        embed = DiscordEmbed(
            title=post.title[:MAX_TITLE],
            description=post.body[:MAX_DESCRIPTION],
            color=colour,
        )
        if post.image_url:
            embed.set_image(url=post.image_url)
        angle = f" • {post.creative_angle}" if post.creative_angle else ""
        embed.set_footer(text=f"EduBot • {post.post_type}{angle}")
        return embed
