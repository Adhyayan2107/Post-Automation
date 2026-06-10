"""
One-time setup: import Reddit session cookies exported from your browser.

Steps:
1. Install Cookie-Editor extension (Chrome/Firefox)
2. Log in to reddit.com as your bot account in your real browser
3. Open Cookie-Editor → Export → "Export as JSON" → copy the JSON
4. Run: uv run python scripts/import_reddit_cookies.py
5. Paste the JSON when prompted

The session is saved to reddit_session.json and used by the publisher.
Reddit sessions last months — re-run this only if posts start failing.
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SESSION_FILE = "reddit_session.json"


def main() -> None:
    print("Paste the Cookie-Editor JSON export (then press Enter twice):\n")
    lines = []
    while True:
        line = input()
        if line == "" and lines:
            break
        lines.append(line)

    raw = "\n".join(lines).strip()

    try:
        cookies = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}")
        sys.exit(1)

    # Normalize to Playwright storage_state format
    playwright_cookies = []
    for c in cookies:
        domain = c.get("domain", ".reddit.com")
        if not domain.startswith("."):
            domain = "." + domain
        playwright_cookies.append({
            "name":     c["name"],
            "value":    c["value"],
            "domain":   domain,
            "path":     c.get("path", "/"),
            "secure":   c.get("secure", True),
            "httpOnly": c.get("httpOnly", False),
            "sameSite": c.get("sameSite", "Lax"),
        })

    state = {"cookies": playwright_cookies, "origins": []}
    with open(SESSION_FILE, "w") as f:
        json.dump(state, f, indent=2)

    print(f"\n✓ Saved {len(playwright_cookies)} cookies to {SESSION_FILE}")
    print("Reddit publisher will now use this session — no login needed.")


if __name__ == "__main__":
    main()
