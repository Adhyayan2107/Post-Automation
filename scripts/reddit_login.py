"""
One-time setup: log in to Reddit via a visible browser window.
Playwright captures ALL cookies (including httpOnly) that Cookie-Editor cannot.

Usage:
  uv run python scripts/reddit_login.py

A browser window will open. Log in normally. The session is saved automatically
once Reddit detects you as logged in.
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.async_api import async_playwright

SESSION_FILE = "reddit_session.json"
USERNAME_ENV = os.getenv("REDDIT_USERNAME", "")


async def main() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        ctx = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="America/New_York",
        )
        await ctx.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        page = await ctx.new_page()
        await page.goto("https://www.reddit.com/login", timeout=30000)

        print("\n=== Reddit Login ===")
        print("A browser window has opened.")
        print("Log in to Reddit as normal (username, password, any CAPTCHA).")
        print("This script will detect when you're logged in and save the session.\n")

        username = USERNAME_ENV.strip()
        if not username:
            username = input("Enter your Reddit username (for detection): ").strip()

        # Poll until username appears in the page HTML (logged-in indicator)
        print(f"Waiting for login as '{username}'...")
        for _ in range(120):  # up to 4 minutes
            try:
                await page.wait_for_timeout(2000)
                current_url = page.url
                if "reddit.com/login" not in current_url:
                    html = await page.content()
                    if username.lower() in html.lower():
                        break
            except Exception:
                pass
        else:
            print("Timed out waiting for login. Saving whatever session exists.")

        # Let the page settle so all cookies are set
        await page.wait_for_timeout(2000)

        state = await ctx.storage_state()
        with open(SESSION_FILE, "w") as f:
            json.dump(state, f, indent=2)

        reddit_cookies = [
            c for c in state.get("cookies", [])
            if "reddit.com" in c.get("domain", "")
        ]
        print(f"\n✓ Session saved to {SESSION_FILE}")
        print(f"  {len(reddit_cookies)} Reddit cookies captured:")
        for c in reddit_cookies:
            tag = " (httpOnly)" if c.get("httpOnly") else ""
            print(f"    {c['name']}{tag}")

        await browser.close()
        print("\nDone. Reddit publisher will now use this session.")


if __name__ == "__main__":
    asyncio.run(main())
