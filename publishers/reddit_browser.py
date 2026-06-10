"""
Reddit publisher using Playwright browser automation.
Uses old.reddit.com (plain HTML forms) — no API key required.
Saves session cookies locally so it only logs in once per machine.
"""

import asyncio
import json
from pathlib import Path

from playwright.async_api import async_playwright, BrowserContext, Page

from core.interfaces.publisher import AbstractPublisher
from core.models.post import Post
from config.settings import settings
from config.logging import get_logger

logger = get_logger(__name__)

SESSION_FILE   = Path("reddit_session.json")
LOGIN_URL      = "https://www.reddit.com/login"
POST_DELAY_SEC = 20   # between subreddits to avoid rate-limit flags


class RedditBrowserPublisher(AbstractPublisher):

    def __init__(self) -> None:
        self._username = settings.reddit.username
        self._password = settings.reddit.password

    @property
    def platform_name(self) -> str:
        return "reddit"

    async def publish(self, post: Post) -> bool:
        if not self._username or not self._password:
            logger.warning("Reddit credentials not set — skipping post %s", post.id)
            return False

        if settings.app.dry_run:
            for sub in post.target_subreddits:
                logger.info("[DRY RUN] Would post to %s: %r", sub, post.title[:80])
            return True

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
            )
            context = await self._get_authenticated_context(browser)

            overall = True
            for i, subreddit in enumerate(post.target_subreddits):
                if i > 0:
                    await asyncio.sleep(POST_DELAY_SEC)
                ok = await self._submit_post(context, post, subreddit)
                if not ok:
                    overall = False

            await self._save_session(context)
            await browser.close()

        return overall

    # ── Auth ──────────────────────────────────────────────────────────────────

    async def _get_authenticated_context(self, browser) -> BrowserContext:
        if SESSION_FILE.exists():
            try:
                state = json.loads(SESSION_FILE.read_text())
                ctx   = await browser.new_context(storage_state=state)
                if await self._is_logged_in(ctx):
                    logger.info("Reddit: reusing saved session")
                    return ctx
                await ctx.close()
            except Exception:
                pass

        ctx = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/124.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="America/New_York",
        )
        await ctx.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        await self._login(ctx)
        return ctx

    async def _is_logged_in(self, ctx: BrowserContext) -> bool:
        page = await ctx.new_page()
        try:
            await page.goto("https://www.reddit.com/", timeout=15000)
            await page.wait_for_load_state("domcontentloaded")
            html = await page.content()
            return self._username.lower() in html.lower()
        except Exception:
            return False
        finally:
            await page.close()

    async def _login(self, ctx: BrowserContext) -> None:
        page = await ctx.new_page()
        try:
            await page.goto(LOGIN_URL, timeout=30000)
            await page.wait_for_selector('input[name="username"]', state="visible", timeout=15000)

            await page.fill('input[name="username"]', self._username)
            await page.fill('input[name="password"]', self._password)
            await page.click('button:has-text("Log In")')

            # Wait for redirect away from login page
            try:
                await page.wait_for_url(
                    lambda url: "reddit.com/login" not in url,
                    timeout=15000,
                )
            except Exception:
                pass
            await page.wait_for_timeout(2000)

            html = await page.content()
            if self._username.lower() in html.lower():
                logger.info("Reddit: logged in as %s", self._username)
            else:
                logger.warning("Reddit: login may have failed — check credentials or 2FA")
        finally:
            await page.close()

    # ── Posting ───────────────────────────────────────────────────────────────

    async def _submit_post(self, ctx: BrowserContext, post: Post, subreddit: str) -> bool:
        sub  = subreddit.lstrip("r/")
        url  = f"https://www.reddit.com/r/{sub}/submit?type=text"
        page = await ctx.new_page()

        try:
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state("domcontentloaded")

            if "login" in page.url:
                logger.error("Reddit: session expired for r/%s", sub)
                return False

            # Wait for title input
            await page.wait_for_selector('textarea[name="title"], input[name="title"]',
                                         state="visible", timeout=10000)

            # Title
            await page.fill('textarea[name="title"], input[name="title"]', post.title[:300])

            # Body — new Reddit uses a contenteditable div
            body = _format_body(post)
            body_sel = 'div[contenteditable="true"][role="textbox"], div.public-DraftEditor-content'
            try:
                await page.wait_for_selector(body_sel, state="visible", timeout=8000)
                await page.click(body_sel)
                await page.keyboard.type(body[:5000], delay=5)
            except Exception:
                # Fallback: try plain textarea
                try:
                    await page.fill('textarea[placeholder*="text"]', body[:5000])
                except Exception:
                    pass

            # Submit — try multiple selectors
            for btn in ['button[type="submit"]:has-text("Post")',
                        'button:has-text("Post")',
                        'button[type="submit"]']:
                if await page.locator(btn).count() > 0:
                    await page.click(btn)
                    break

            await page.wait_for_load_state("networkidle", timeout=20000)

            if "/comments/" in page.url:
                logger.info("Posted to r/%s → %s", sub, page.url)
                return True
            else:
                logger.error("Post to r/%s may have failed — ended at %s", sub, page.url)
                return False

        except Exception as exc:
            logger.error("r/%s submission error: %s", sub, exc)
            return False
        finally:
            await page.close()

    # ── Helpers ───────────────────────────────────────────────────────────────

    async def _save_session(self, ctx: BrowserContext) -> None:
        try:
            state = await ctx.storage_state()
            SESSION_FILE.write_text(json.dumps(state))
        except Exception:
            pass


def _format_body(post: Post) -> str:
    """Append image and source links to the post body."""
    body = post.body[:39000]
    if post.image_url:
        body += f"\n\n[Image]({post.image_url})"
    if post.source_urls:
        sources = " | ".join(f"[source]({u})" for u in post.source_urls[:3])
        body += f"\n\n*Sources: {sources}*"
    return body
