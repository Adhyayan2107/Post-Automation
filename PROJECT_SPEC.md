# PROJECT_SPEC.md — EduBot Detailed Specification

## Phase 0 — Project Bootstrap

### Goal
Get a working repo skeleton with all tools connected and secrets loading correctly.

### Prompt for Claude Code
```
Read CLAUDE.md first.

Phase 0 — Bootstrap:

1. Create pyproject.toml using `uv` with these dependencies:
   httpx, beautifulsoup4, feedparser, anthropic, praw, discord-webhook,
   google-api-python-client, google-auth, google-auth-oauthlib,
   sqlmodel, supabase, apscheduler, jinja2, pydantic-settings,
   pytest, pytest-asyncio

2. Create config/settings.py using Pydantic BaseSettings.
   Load every variable from .env.example. Group them into nested models:
   ClaudeSettings, RedditSettings, DiscordSettings, GoogleSettings,
   PexelsSettings, SupabaseSettings, AppSettings.

3. Create config/logging.py with structured JSON logging using Python's
   built-in logging. Log level from settings.

4. Create .env.example with all variables listed in CLAUDE.md.

5. Create storage/migrations/001_initial_schema.sql with tables:
   - weekly_runs (id, started_at, finished_at, status, post_count)
   - raw_content (id, url, title, body, source, scraped_at, run_id)
   - posts (all fields from Post model in CLAUDE.md)
   - post_schedule (id, post_id, platform, scheduled_at, calendar_event_id)

6. Create storage/database.py that:
   - Creates a Supabase client using settings
   - Has a simple test_connection() async function

7. Create a smoke test: tests/test_config.py that asserts settings load
   without error (mock the env vars).

Do NOT create any agents, scrapers, or dashboard yet.
Follow SOLID. All typed. No secrets in code.
```

---

## Phase 1 — Core Abstractions

### Goal
Define all contracts. Zero implementations. Everything else in the project depends on these.

### Prompt for Claude Code
```
Read CLAUDE.md first.

Phase 1 — Core Abstractions:

Create these abstract base classes in core/interfaces/:

1. core/interfaces/scraper.py
   AbstractScraper(ABC):
   - async def scrape(self) -> List[RawContent]
   - property name: str  (e.g. "reddit", "ib_official")

2. core/interfaces/content_generator.py
   AbstractContentGenerator(ABC):
   - async def generate(self, raw_contents: List[RawContent]) -> List[Post]
   - property post_type: str  (e.g. "educational", "creative")

3. core/interfaces/image_provider.py
   AbstractImageProvider(ABC):
   - async def find_image(self, keywords: List[str]) -> str | None
     (returns image URL or None)
   - property provider_name: str

4. core/interfaces/publisher.py
   AbstractPublisher(ABC):
   - async def publish(self, post: Post) -> bool  (True = success)
   - property platform_name: str

Create these dataclasses in core/models/:

5. core/models/raw_content.py
   RawContent:
   - id: UUID (auto)
   - url: str
   - title: str
   - body: str
   - source: str  (scraper name)
   - scraped_at: datetime (auto utcnow)
   - run_id: UUID

6. core/models/post.py
   PostStatus(Enum): pending, approved, rejected, scheduled, published, failed
   Post (SQLModel, table=True): all fields from CLAUDE.md

7. core/models/schedule_slot.py
   ScheduleSlot:
   - post_id: UUID
   - platform: str
   - scheduled_at: datetime
   - calendar_event_id: str | None

8. storage/repositories/post_repository.py
   PostRepository:
   - async def save(post: Post) -> Post
   - async def get_by_id(id: UUID) -> Post | None
   - async def get_by_status(status: PostStatus) -> List[Post]
   - async def update_status(id: UUID, status: PostStatus) -> None

9. storage/repositories/run_log_repository.py
   RunLogRepository:
   - async def start_run() -> UUID  (creates run record, returns run_id)
   - async def finish_run(run_id: UUID, post_count: int) -> None

Write tests in tests/test_models/ that instantiate each model and verify
field defaults. No mocking needed here — just object construction tests.
```

---

## Phase 2 — Scrapers

### Goal
5 working scrapers that each return `List[RawContent]`. A `ScraperAgent` that runs them all in parallel.

### Prompt for Claude Code
```
Read CLAUDE.md first.

Phase 2 — Scrapers:

All scrapers must extend AbstractScraper from core/interfaces/scraper.py.
Use httpx.AsyncClient for all HTTP. BeautifulSoup4 for HTML. feedparser for RSS.

Implement in this order:

1. scrapers/news_scraper.py — NewsScraper
   - Use Google News RSS: https://news.google.com/rss/search?q={query}
   - Queries: ["IB diploma", "IGCSE 2025", "A level exam", "Cambridge assessment"]
   - Parse feed with feedparser, return top 10 results per query
   - Deduplicate by URL within this scraper

2. scrapers/reddit_scraper.py — RedditScraper
   - Use PRAW in read-only mode (no auth needed for public posts)
   - Scrape: r/IBO, r/igcse, r/6thForm, r/alevel
   - Get top 15 posts from "week" timeframe per subreddit
   - Include post title + selftext in RawContent.body

3. scrapers/ib_official.py — IBOfficialScraper
   - Scrape https://www.ibo.org/news/ (parse HTML, extract article titles + summaries)
   - Return last 10 news items

4. scrapers/cambridge_scraper.py — CambridgeScraper
   - Parse Cambridge Assessment RSS: https://www.cambridgeassessment.org.uk/rss/news.xml
   - Return last 10 items

5. scrapers/youtube_scraper.py — YouTubeScraper
   - Use YouTube Data API v3 search endpoint
   - Query: "IB study tips 2025", "IGCSE revision", "A level explained"
   - Return video title + description as RawContent (URL = watch link)
   - Max 10 results per query

6. agents/scraper_agent.py — ScraperAgent
   - Takes List[AbstractScraper] in __init__ (dependency injection)
   - async def run(run_id: UUID) -> List[RawContent]
   - Uses asyncio.gather to run all scrapers in parallel
   - Deduplicates results across scrapers by URL
   - Saves all unique RawContent to DB via a repository
   - Logs counts per scraper

Write tests:
- tests/test_scrapers/test_news_scraper.py — mock httpx, assert RawContent shape
- tests/test_scrapers/test_reddit_scraper.py — mock PRAW, assert RawContent shape
- tests/test_scrapers/test_scraper_agent.py — mock all scrapers, assert dedup logic

Error handling: if one scraper fails, log the error and continue with others.
Never raise from ScraperAgent.run().
```

---

## Phase 3 — Content Generators

### Goal
Two generators (educational + creative) that turn `List[RawContent]` into `List[Post]` via Claude API.

### Prompt for Claude Code
```
Read CLAUDE.md first.

Phase 3 — Content Generators:

All generators must extend AbstractContentGenerator.
Use the anthropic Python SDK with claude-sonnet-4-6.
Use Jinja2 for prompt templates stored in generators/prompts/.

1. Create generators/prompts/educational.jinja2
   System prompt instructs Claude to:
   - Act as an IB/IGCSE/A-Level education content creator
   - Write Reddit-style posts: punchy title, clear body, actionable takeaways
   - Always cite the source content
   - Tone: helpful, peer-to-peer, not corporate
   - Format: markdown with headers and bullet points
   - Length: 200-400 words
   Template variables: {{ raw_content_summaries }}, {{ target_subreddits }}

2. Create generators/prompts/creative_anime.jinja2
   System prompt instructs Claude to:
   - Draw a SPECIFIC parallel between an anime character/arc and an IB/IGCSE concept
   - Structure: Hook (the anime moment) → The concept → The connection → Why it helps
   - Must be accurate educationally — the anime is a hook, not the content
   - Examples style: "Luffy's 'I want to be free' = the Enlightenment ideal of liberty
     that directly caused the French Revolution. Here's why that matters for Paper 2..."
   - Tone: exciting, like a friend who loves both anime and studying
   Template variables: {{ raw_content_summaries }}, {{ subject }}, {{ anime_list }}

3. Create generators/prompts/creative_movies.jinja2
   Same structure as anime but using popular movies/series
   (Oppenheimer, Breaking Bad, The Crown, etc.)

4. generators/educational_post.py — EducationalPostGenerator
   - Implements AbstractContentGenerator
   - Batches raw_contents into groups of 5
   - Calls Claude with educational.jinja2 template
   - Parses Claude response into Post objects
   - Sets post_type = "educational"
   - Returns 3-5 posts per run

5. generators/creative_post.py — CreativePostGenerator
   - Implements AbstractContentGenerator
   - Picks a creative angle (anime or movie) randomly per post
   - Uses appropriate Jinja2 template
   - Anime list to draw from (hardcoded in config):
     Naruto, One Piece, Attack on Titan, Death Note, Fullmetal Alchemist,
     Demon Slayer, Hunter x Hunter, Code Geass, Steins;Gate, Vinland Saga
   - Sets post_type = "creative", creative_angle = "anime" | "movie"
   - Returns 2-3 posts per run

6. agents/content_agent.py — ContentAgent
   - Takes AbstractContentGenerator in __init__
   - async def run(raw_contents, run_id) -> List[Post]
   - Saves posts to DB with status = "pending"

7. agents/creative_agent.py — CreativeAgent
   - Same structure as ContentAgent but uses CreativePostGenerator
   - Separate agent so it can be tuned independently

Write tests:
- Mock the anthropic client — do NOT call the real API in tests
- Test that the Jinja2 templates render without error
- Test that Post objects are correctly constructed from Claude mock response
- Test that posts are saved with status = "pending"
```

---

## Phase 4 — Image Agent

### Goal
For each post, find a relevant free image. Pexels first, Unsplash as fallback.

### Prompt for Claude Code
```
Read CLAUDE.md first.

Phase 4 — Image Agent:

All image providers must extend AbstractImageProvider.

1. image_providers/pexels.py — PexelsImageProvider
   - Pexels API: GET https://api.pexels.com/v1/search?query={keywords}&per_page=5
   - Authorization: Bearer {PEXELS_API_KEY}
   - Pick the first landscape-oriented result (width > height)
   - Return the "medium" size URL from response
   - Handle 429 rate limit: log and return None

2. image_providers/unsplash.py — UnsplashImageProvider
   - Unsplash API: GET https://api.unsplash.com/search/photos?query={keywords}&per_page=5
   - Authorization: Client-ID {UNSPLASH_ACCESS_KEY}
   - Return regular size URL of first result
   - Handle 403 (rate limit): log and return None

3. agents/image_agent.py — ImageAgent
   - Takes List[AbstractImageProvider] in __init__ (ordered by priority)
   - async def find_image(post: Post) -> str | None
   - Extracts 3-5 keywords from post title using simple word extraction
     (no Claude call here — keep it cheap, just strip stopwords)
   - Tries providers in order, returns first non-None result
   - async def enrich_posts(posts: List[Post]) -> List[Post]
   - Calls find_image for each post, updates post.image_url
   - Runs concurrently with asyncio.gather, max 3 concurrent requests

Write tests:
- Mock httpx responses for both providers
- Test fallback: if Pexels returns None, Unsplash is tried
- Test keyword extraction from post title
```

---

## Phase 5 — Approval Dashboard

### Goal
A clean Next.js dashboard on Vercel where you review pending posts, approve or reject them, and see the weekly schedule.

### Prompt for Claude Code
```
Read CLAUDE.md first.

Phase 5 — Approval Dashboard:

Initialize Next.js inside the dashboard/ folder:
- TypeScript, Tailwind CSS, App Router, no src/ prefix
- Install: @supabase/supabase-js, @supabase/ssr, shadcn/ui, date-fns, lucide-react

Create dashboard/src/lib/types.ts:
- Mirror the Post SQLModel as a TypeScript interface
- Include PostStatus as a TypeScript enum

Create dashboard/src/lib/supabase.ts:
- Browser client (createBrowserClient)
- Server client (createServerClient) using cookies
- Service role client for Server Actions

Build these pages and components:

1. dashboard/src/app/posts/page.tsx — Post Queue
   - Server Component: fetches all posts with status = "pending" from Supabase
   - Shows a grid of PostCard components
   - Stats bar at top: X pending, Y approved this week, Z published
   - Empty state when no pending posts

2. dashboard/src/components/PostCard.tsx
   - Shows: title, first 150 chars of body, post_type badge, creative_angle badge
   - Shows image thumbnail if image_url exists
   - Shows source_urls count
   - Two buttons: "Review →" links to /posts/[id]

3. dashboard/src/app/posts/[id]/page.tsx — Post Detail
   - Server Component: fetches single post by id
   - Full post preview rendered as markdown (use a lightweight renderer)
   - Image preview if available
   - Source URLs listed as clickable links
   - Target platforms and subreddits shown
   - ApprovalButtons component at bottom

4. dashboard/src/components/ApprovalButtons.tsx
   - Client Component
   - "Approve" button (green) → calls approvePost server action
   - "Reject" button (red) → calls rejectPost server action
   - Optional: inline edit of title/body before approving
   - Shows loading state while action is running
   - Redirects to /posts after action completes

5. dashboard/src/app/schedule/page.tsx — Weekly Calendar
   - Server Component: fetches all posts with status = "scheduled" or "published"
   - Groups posts by day of week
   - Shows each post as a time-slotted card
   - Published posts shown with a checkmark
   - Scheduled posts shown with a clock icon

6. dashboard/src/actions/posts.ts — Server Actions
   - approvePost(id: string): update status to "approved" in Supabase
   - rejectPost(id: string): update status to "rejected" in Supabase
   - editPost(id: string, title: string, body: string): update post content

7. dashboard/src/app/layout.tsx
   - Simple sidebar nav: "Post Queue" | "Schedule"
   - Dark mode by default (Tailwind dark class on html element)

Styling rules:
- Dark background: bg-gray-950
- Cards: bg-gray-900, border border-gray-800
- Approve green: emerald-500, Reject red: red-500
- Typography: Inter font
- No animations — keep it fast

Create vercel.json at dashboard/ root with correct build settings.
Create dashboard/.env.local.example with NEXT_PUBLIC_SUPABASE_URL and
NEXT_PUBLIC_SUPABASE_ANON_KEY.

Do not add authentication — this dashboard is for personal use only.
```

---

## Phase 6 — Scheduler

### Goal
Turn approved posts into Google Calendar events. A runner that fires publishers at the right time.

### Prompt for Claude Code
```
Read CLAUDE.md first.

Phase 6 — Scheduler:

1. scheduler/time_optimizer.py — TimeOptimizer
   Best posting times (UTC, assuming audience in UK/Europe/Asia):
   Reddit:  Mon 08:00, Tue 12:00, Wed 18:00, Thu 08:00, Fri 12:00, Sat 10:00, Sun 16:00
   Discord: Mon 16:00, Tue 16:00, Wed 20:00, Thu 16:00, Fri 17:00, Sat 12:00, Sun 18:00

   TimeOptimizer:
   - get_slots_for_week(posts: List[Post]) -> List[ScheduleSlot]
   - Assigns each post to the next available time slot
   - Alternates between platforms
   - Ensures no two posts are within 4 hours of each other on the same platform
   - Returns list of ScheduleSlot objects

2. scheduler/google_calendar.py — GoogleCalendarScheduler
   - Auth via OAuth2 service account (credentials.json in project root, gitignored)
   - create_event(slot: ScheduleSlot, post: Post) -> str (returns event_id)
   - Event title: "[EDUBOT] {post.title}"
   - Event description: post body first 200 chars + "\n\nPost ID: {post.id}"
   - Event color: green for reddit, blue for discord
   - list_upcoming_events(days: int = 7) -> List[ScheduleSlot]
   - delete_event(event_id: str) -> None

3. scheduler/runner.py — SchedulerRunner
   - APScheduler with AsyncIOScheduler
   - On startup: reads all posts with status = "scheduled" from DB
   - Creates a job for each scheduled post at post.scheduled_at
   - Job calls the correct publisher based on target_platforms
   - After publish: updates post status to "published" or "failed"
   - Also schedules a recurring job: every 5 minutes, check for newly approved
     posts and create calendar events + jobs for them

Write tests:
- test_time_optimizer: assert no overlapping slots, assert correct day assignments
- test_google_calendar: mock the Google API client, assert event structure
- test_runner: mock APScheduler, assert jobs are created for scheduled posts
```

---

## Phase 7 — Publishers

### Goal
Two publishers: Reddit (via PRAW) and Discord (via webhook).

### Prompt for Claude Code
```
Read CLAUDE.md first.

Phase 7 — Publishers:

Both must extend AbstractPublisher from core/interfaces/publisher.py.

1. publishers/reddit.py — RedditPublisher
   - Auth via PRAW with credentials from settings
   - async def publish(post: Post) -> bool
   - Iterates over post.target_subreddits
   - For each subreddit: submit a text post (subreddit.submit())
   - If post.image_url exists: submit as link post to the image, body in comment
   - Rate limit: wait 10 seconds between subreddit posts
   - If DRY_RUN=true: log what would be posted, return True without posting
   - Catches praw.exceptions.APIException, logs, returns False on failure

2. publishers/discord.py — DiscordPublisher
   - Use discord_webhook.DiscordWebhook
   - async def publish(post: Post) -> bool
   - Build a Discord embed:
     - title: post.title (max 256 chars)
     - description: post.body (max 4096 chars)
     - color: 0x5865F2 (Discord blurple)
     - image: post.image_url if available
     - footer: "EduBot • {post.post_type}"
   - If DRY_RUN=true: log the embed dict, return True
   - Webhook URL from settings.discord.webhook_url

Write tests:
- Mock PRAW and discord_webhook
- Test dry run mode: assert no actual HTTP calls made
- Test that failed API calls return False, not raise
- Test embed structure for Discord
```

---

## Phase 8 — Orchestrator + GitHub Actions

### Goal
One entry point that runs the full pipeline. A GitHub Actions cron that triggers it weekly.

### Prompt for Claude Code
```
Read CLAUDE.md first.

Phase 8 — Orchestrator + GitHub Actions:

1. agents/orchestrator.py — FatherAgent
   This is the weekly entry point. It coordinates ALL other agents in sequence.

   async def run():
     a. run_log_repo.start_run() → run_id
     b. scraper_agent.run(run_id) → raw_contents
     c. content_agent.run(raw_contents, run_id) → edu_posts
     d. creative_agent.run(raw_contents, run_id) → creative_posts
     e. all_posts = edu_posts + creative_posts
     f. image_agent.enrich_posts(all_posts) → posts_with_images
     g. Save all posts to DB with status = "pending"
     h. Send summary email via Gmail API:
        Subject: "EduBot: {N} new posts ready for review"
        Body: list of post titles with link to dashboard
     i. run_log_repo.finish_run(run_id, len(posts_with_images))
     j. Log total time taken

   Add a __main__ block so it can be run directly:
   if __name__ == "__main__":
       asyncio.run(FatherAgent().run())

2. Create a Gmail notification helper in scheduler/gmail_notifier.py:
   - Uses Gmail API to send the summary email to GMAIL_NOTIFY_ADDRESS from settings
   - Simple HTML email listing post titles and a "Review now" button linking to dashboard

3. .github/workflows/weekly_run.yml
   Triggers: schedule (cron: '0 6 * * 1')  — every Monday at 6AM UTC
   Also: workflow_dispatch (so you can trigger manually)

   Steps:
   - Checkout repo
   - Set up Python 3.12
   - Install uv, then uv sync
   - Run: python -m agents.orchestrator
   - All secrets injected as environment variables from GitHub Secrets

   List every env var from .env.example as a GitHub secret reference.

4. Create a script scripts/dry_run.py:
   - Sets DRY_RUN=true, runs the full orchestrator
   - Prints a report: scraped N items, generated M posts, would post to X subreddits
   - Does not write to DB, does not call publishers

Write an end-to-end test: tests/test_e2e.py
   - Mocks ALL external services (Claude, Reddit, Pexels, Google, Discord)
   - Runs FatherAgent().run()
   - Asserts: posts created in DB with status pending, image_agent was called,
     Gmail notification was sent
   - Uses DRY_RUN=true
```

---

## API Keys Setup Guide

### 1. Reddit API
1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" → select "script"
3. Name: `EduBot`, redirect URI: `http://localhost:8080`
4. Note: `client_id` (under app name), `client_secret`

### 2. Discord Webhook
1. Server Settings → Integrations → Webhooks
2. New Webhook → assign to your channel → Copy URL
3. That's your `DISCORD_WEBHOOK_URL`

### 3. Google Calendar + Gmail API
1. Go to https://console.cloud.google.com
2. New project: `EduBot`
3. Enable: Google Calendar API, Gmail API
4. Create OAuth 2.0 credentials (Desktop app type)
5. Download `credentials.json` → put in project root (gitignored)
6. First run will open browser for OAuth consent

### 4. Pexels API
1. https://www.pexels.com/api/ → "Get Started"
2. Free tier: 200 req/hour, 20,000 req/month — plenty

### 5. Unsplash API
1. https://unsplash.com/developers → "New Application"
2. Free tier: 50 req/hour — backup only

### 6. Supabase
1. https://supabase.com → New Project
2. Go to Settings → API → copy URL and anon key
3. Run `storage/migrations/001_initial_schema.sql` in SQL editor
4. For Vercel: also save the service role key (for Server Actions)

### 7. Anthropic API
1. https://console.anthropic.com → API Keys → New Key
2. Set a spending limit to avoid surprise bills

---

## Subreddit Posting Rules Summary

| Subreddit | Type | Key Rule |
|-----------|------|----------|
| r/IBO | Community | No spam. Educational posts welcome. Flair required. |
| r/igcse | Community | Must be student-relevant. No self-promo. |
| r/6thForm | Community | UK-focused. Helpful content OK. No ads. |
| r/alevel | Community | Revision/tips posts are welcome. Cite sources. |

EduBot will: use appropriate flairs, space posts 48h+ apart per subreddit, vary post types.

---

## Weekly Content Mix Target

| Post Type | Count | Platforms |
|-----------|-------|-----------|
| Educational (news/updates) | 3 | Reddit + Discord |
| Educational (study tips) | 2 | Reddit + Discord |
| Creative (anime angle) | 2 | Reddit + Discord |
| Creative (movie/TV angle) | 1 | Discord only |

Total: ~8 posts per week, spread across 7 days.
