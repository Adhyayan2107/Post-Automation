"""
One-time setup: import Reddit session cookies from a file.

Usage:
  1. Install Cookie-Editor extension (Chrome/Firefox)
  2. Log in to reddit.com in your real browser
  3. Open Cookie-Editor → Export → "Export as JSON" → save to a file (e.g. cookies.json)
  4. Run: uv run python scripts/import_reddit_cookies.py cookies.json
"""

import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SESSION_FILE = "reddit_session.json"

if len(sys.argv) < 2:
    print("Usage: uv run python scripts/import_reddit_cookies.py <cookies.json>")
    sys.exit(1)

cookie_file = sys.argv[1]
if not os.path.exists(cookie_file):
    print(f"File not found: {cookie_file}")
    sys.exit(1)

with open(cookie_file) as f:
    cookies = json.load(f)

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
        "sameSite": c.get("sameSite") or "Lax",
    })

state = {"cookies": playwright_cookies, "origins": []}
with open(SESSION_FILE, "w") as f:
    json.dump(state, f, indent=2)

print(f"✓ Saved {len(playwright_cookies)} cookies to {SESSION_FILE}")
print("Reddit publisher will now use this session — no login needed.")
