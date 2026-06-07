# EduBot — Full Project Context

Use this file to restore a Claude Code session to full context. Paste it at the start of a new conversation.

---

## What This Is

A fully automated weekly content pipeline for IB, IGCSE, A-Level, and AS-Level education communities.

**Full loop:**
1. Scrape the internet for relevant education news
2. Generate posts via Claude API (educational + creative/anime/movie/history angles)
3. Source images (Pexels → Unsplash → Jikan → TMDb depending on post type)
4. Save all posts to Supabase as `pending`
5. Human reviews in the dashboard → approve or reject
6. Approved posts get a time slot (written to `scheduled_at` in DB)
7. `runner.py` polls the DB and fires publishers at the right time
8. Posts go live on Reddit (PRAW) and Discord (webhook)
9. Status updated to `published` in DB

---

## Tech Stack

### Python Backend
- **Runtime**: Python 3.12, managed by `uv`
- **HTTP**: `httpx` (async only — never `requests`)
- **Claude API**: `anthropic`
- **Reddit**: `praw`
- **Discord**: `discord-webhook`
- **DB ORM**: `sqlmodel` + `supabase-py`
- **Scheduling**: `apscheduler`
- **Images**: `pexels-api`, custom Unsplash/Jikan/TMDb wrappers
- **Config**: `pydantic-settings`
- **Tests**: `pytest` + `pytest-asyncio`

### Next.js Dashboard
- **Framework**: Next.js App Router (NOT Pages Router), deployed to Vercel
- **DB client**: `@supabase/supabase-js`
- **Styling**: Tailwind CSS
- **Date handling**: `date-fns`
- **Icons**: `lucide-react` (note: `Github` icon not available in installed version — use `GitBranch`)
- **State**: React Server Components + `useState` / `useTransition`

### Infrastructure
| Service | Purpose |
|---------|---------|
| Supabase | Postgres database |
| Vercel | Dashboard hosting |
| Pexels | Stock images (primary) |
| Unsplash | Stock images (fallback) |
| Jikan API | Anime images (MAL, free, no key needed) |
| TMDb | Movie images |
| Reddit API | Publishing via PRAW |
| Discord | Publishing via webhook |
| GitHub Actions | Trigger pipeline runs (`workflow_dispatch`) |
| Claude API | Content generation (pay-per-use, ~$0.10-0.30/run) |

**Removed (intentionally):** Google Calendar — was a middleman between DB and scheduler. Dashboard's WeekCalendar does the same job. Runner polls `scheduled_at` from DB directly.

---

## Repository Layout

```
edu-automation-bot/
├── agents/
│   ├── orchestrator.py        # FatherAgent — full weekly pipeline entry point
│   ├── scraper_agent.py       # Fans out to all scrapers, deduplicates
│   ├── content_agent.py       # Generates educational posts via Claude
│   ├── creative_agent.py      # Generates anime/movie/history posts via Claude
│   └── image_agent.py         # Routes each post to the right image provider
│
├── core/
│   ├── interfaces/
│   │   ├── scraper.py         # AbstractScraper (ABC)
│   │   ├── content_generator.py
│   │   ├── image_provider.py
│   │   └── publisher.py
│   └── models/
│       ├── post.py            # Post SQLModel + PostStatus enum
│       ├── raw_content.py     # RawContent dataclass
│       └── schedule_slot.py   # ScheduleSlot dataclass
│
├── scrapers/
│   ├── news_scraper.py        # Google News RSS
│   ├── ib_official.py         # ibo.org
│   ├── cambridge_scraper.py   # Cambridge Assessment feed
│   ├── reddit_scraper.py      # r/IBO, r/IGCSE etc (read-only PRAW)
│   └── youtube_scraper.py     # YouTube Data API
│
├── generators/
│   ├── educational_post.py    # "Here's what changed in IB Chemistry HL"
│   ├── creative_post.py       # "Luffy's freedom = French Revolution concept"
│   └── prompts/
│       ├── educational.jinja2
│       ├── creative_anime.jinja2
│       ├── creative_movies.jinja2
│       └── creative_history.jinja2
│
├── image_providers/
│   ├── pexels.py              # Primary stock images
│   ├── unsplash.py            # Fallback stock images
│   ├── jikan.py               # Anime character images (no API key, free)
│   └── tmdb.py                # Movie poster images
│
├── publishers/
│   ├── reddit.py              # Posts via PRAW
│   └── discord.py             # Posts via webhook
│
├── scheduler/
│   ├── time_optimizer.py      # Best UTC posting times, avoids slot collisions
│   └── runner.py              # APScheduler: polls DB for approved posts, fires publishers
│
├── storage/
│   ├── database.py            # Supabase client factory
│   ├── repositories/
│   │   ├── post_repository.py
│   │   ├── raw_content_repository.py
│   │   └── run_log_repository.py
│   └── migrations/
│       ├── 001_initial_schema.sql
│       ├── 002_image_subject.sql     # Added image_subject column
│       ├── 003_gcal_event_id.sql     # Added gcal_event_id (now dropped by 004)
│       └── 004_drop_gcal_event_id.sql  # DROP COLUMN gcal_event_id — run this in Supabase
│
├── config/
│   ├── settings.py            # Pydantic BaseSettings — all env vars
│   └── logging.py             # Structured logging
│
├── scripts/
│   ├── mini_run.py            # Lightweight pipeline: scrape (or use cache) → generate → slot
│   └── dry_run.py             # Test run without saving to DB
│
├── tests/                     # pytest + pytest-asyncio
│
├── dashboard/                 # Next.js App Router — deployed to Vercel
│   └── src/
│       ├── app/
│       │   ├── layout.tsx             # Sidebar nav: Posts | Schedule | Run
│       │   ├── page.tsx               # Redirects to /posts
│       │   ├── posts/
│       │   │   ├── page.tsx           # Post list with tab bar + filter pills
│       │   │   └── [id]/page.tsx      # Post detail: preview + approve/reject/edit
│       │   ├── schedule/
│       │   │   └── page.tsx           # Week navigator + WeekCalendar
│       │   ├── run/
│       │   │   ├── page.tsx           # Server component, fetches cache status
│       │   │   └── RunClient.tsx      # Run locally (SSE) or via GitHub Actions
│       │   └── api/
│       │       ├── run/route.ts       # SSE: spawns mini_run.py locally
│       │       ├── run-status/route.ts  # Returns cache status from raw_content table
│       │       └── github-dispatch/route.ts  # Triggers + polls GitHub Actions workflow
│       ├── components/
│       │   ├── WeekCalendar.tsx       # Drag-drop calendar (same-week + cross-week)
│       │   ├── PostCard.tsx           # Card used in /posts grid
│       │   ├── ApprovalButtons.tsx    # Approve / Reject buttons
│       │   ├── StatusBadge.tsx        # Coloured status pill
│       │   └── NavLink.tsx            # Active-state sidebar link
│       ├── lib/
│       │   ├── supabase.ts            # Browser + server Supabase clients
│       │   └── types.ts               # Post, PostStatus TypeScript types
│       └── actions/
│           └── posts.ts               # Server Actions: approve, reject, reschedule, editPost
│
└── .github/workflows/
    └── dashboard_run.yml      # workflow_dispatch: checkout → uv → mini_run.py
```

---

## Data Model

### `posts` table (Supabase)
```sql
id                UUID PK
title             TEXT
body              TEXT          -- full markdown post
post_type         TEXT          -- 'educational' | 'creative'
creative_angle    TEXT          -- 'anime' | 'movie' | 'history' | NULL
image_url         TEXT
image_subject     TEXT          -- keyword used to find the image
source_urls       TEXT[]
target_platforms  TEXT[]        -- ['reddit', 'discord']
target_subreddits TEXT[]        -- ['r/IBO', 'r/IGCSE']
status            TEXT          -- see PostStatus below
scheduled_at      TIMESTAMPTZ
published_at      TIMESTAMPTZ
created_at        TIMESTAMPTZ
run_id            UUID FK → weekly_runs
```

### PostStatus flow
```
pending → approved → (runner fires at scheduled_at) → published
       → rejected
                                                     → failed
```
There is no "scheduled" status in practice — posts go `approved` and stay approved until the runner fires. The `scheduled` status exists in the enum but is unused.

### `raw_content` table
Scraped items cached for 7 days. `mini_run.py` checks this before scraping fresh. Deduped by `(url, run_id)`.

### `weekly_runs` table
Tracks each pipeline run. `run_log_repository.py` handles start/finish/fail.

---

## Post Type → Image Provider Routing

| post_type | creative_angle | Image provider |
|-----------|---------------|----------------|
| educational | — | Pexels → Unsplash (fallback) |
| creative | anime | Jikan (anime character art) |
| creative | movie | TMDb (movie poster) |
| creative | history | Pexels → Unsplash (fallback) |

---

## Dashboard Features (as of current build)

### `/posts`
- Tab bar: **Pending | Approved | Published | Rejected** (counts shown per tab)
- Filter pills: **All | Educational | Creative | Anime | Movie | History**
  - Filters hit DB with `.eq("post_type", ...)` and `.eq("creative_angle", ...)`
  - URL params: `?tab=pending&filter=anime` — fully shareable/linkable
- Grid of PostCards — click to go to detail page

### `/posts/[id]`
- Full post preview with image
- Approve / Reject buttons (Server Actions → revalidates + redirects)
- Edit title/body inline

### `/schedule`
- Week navigator (prev/next arrows, URL param `?week=N` where N is offset from current week)
- **WeekCalendar** with drag-and-drop:
  - Same-week drag: drop on a different day column → keeps same time, changes date
  - Cross-week drag: while dragging, two zones appear below calendar ("← Prev week" / "Next week →") — drops navigate to target week
  - Click a post → modal with datetime-local input for manual rescheduling
- Legend: yellow=pending, emerald=approved, purple=published
- All rescheduling calls `reschedulePost()` Server Action → updates `scheduled_at` in DB

### `/run`
- **Run Locally**: SSE stream from `/api/run` — spawns `uv run python scripts/mini_run.py` with extended PATH
- **Run via GitHub**: dispatches `dashboard_run.yml`, polls `/api/github-status` every 4s for step checkpoints
- Status cards: cache status (age, item count), estimated cost ($0.10-0.12 cache hit / $0.25-0.30 with scraping), pipeline steps

---

## `mini_run.py` — Step by Step

```
Step 1: Check raw_content cache (7-day window) — scrape only if empty
Step 2: Generate 2 educational posts via Claude
Step 3: Generate 2 creative posts via Claude
Step 4: Source images for each post (routed by post_type/creative_angle)
Step 5: Save all posts to Supabase (status=pending)
Step 6: Assign time slots (TimeOptimizer → writes scheduled_at to DB)
        — loads existing future-scheduled posts first to avoid collisions
Done: print summary
```

---

## TimeOptimizer — Slot Assignment

- Best times: Reddit 09:00, 12:00, 19:00 UTC | Discord 10:00, 15:00, 20:00 UTC
- Spreads posts Mon–Fri, avoids weekends
- Accepts `already_used` dict — pre-populated from existing DB slots to prevent double-booking
- One slot per post (first platform in `target_platforms`)

---

## Key Env Vars

### Python backend (`.env`)
```
ANTHROPIC_API_KEY=
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USERNAME=
REDDIT_PASSWORD=
REDDIT_USER_AGENT=EduBot/1.0
DISCORD_WEBHOOK_URL=
PEXELS_API_KEY=
UNSPLASH_ACCESS_KEY=
TMDB_API_KEY=
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
LOG_LEVEL=INFO
DRY_RUN=false
```

### Dashboard (`dashboard/.env.local`)
```
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
```

### Dashboard (Vercel env vars, for GitHub dispatch feature)
```
GITHUB_PAT=          # personal access token with workflow scope
GITHUB_OWNER=Adhyayan2107
GITHUB_REPO=Post-Automation
```

### GitHub Actions secrets
```
ANTHROPIC_API_KEY
PEXELS_API_KEY
UNSPLASH_ACCESS_KEY
SUPABASE_URL
SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY
```

---

## Supabase Project

- URL: `https://ierbzgpdvgbvxqcbzxvj.supabase.co`
- Dashboard user email: `internsortmyprep@gmail.com`

**Pending DB migration** (run in Supabase SQL editor if not done yet):
```sql
ALTER TABLE posts DROP COLUMN IF EXISTS gcal_event_id;
```
(File: `storage/migrations/004_drop_gcal_event_id.sql`)

---

## GitHub / Vercel

- GitHub repo: `Adhyayan2107/Post-Automation` (main branch)
- Vercel project linked to this repo, auto-deploys on push to main
- GitHub Actions workflow: `.github/workflows/dashboard_run.yml` — triggered manually from dashboard Run page or GitHub UI

---

## Golden Rules (from CLAUDE.md)

1. **SOLID strictly** — one class, one job. New platforms = new classes, never edit existing ones.
2. **No secrets in code** — only in `.env` / Vercel env vars
3. **Async-first Python** — `httpx.AsyncClient`, `asyncio`. Never `requests`.
4. **Full type hints** — Python and TypeScript strict mode
5. **Dataclasses/Pydantic** for all data shapes — no raw dicts between layers
6. **One migration per schema change** — never edit existing migrations
7. **Next.js App Router** — no Pages Router, no class components
8. **Python and Next.js share only the DB** — agents write, dashboard reads/writes via Supabase client

---

## What's NOT Built Yet (future phases)

- `orchestrator.py` — full weekly pipeline wiring all agents together (currently `mini_run.py` is the lightweight version)
- `runner.py` deployed as a persistent process — currently only the code exists; needs a server/VM to run continuously and fire publishers at `scheduled_at` times
- Reddit/Discord actually posting (publishers exist but need Reddit/Discord credentials in `.env`)
- `youtube_scraper.py` — needs YouTube Data API key
- `reddit_scraper.py` — needs Reddit read credentials
- Weekly cron via GitHub Actions (`weekly_run.yml`) — only `dashboard_run.yml` (manual trigger) exists so far

---

## How to Run Locally

```bash
# Python backend
cd edu-automation-bot
uv run python scripts/mini_run.py

# Dashboard
cd dashboard
npm run dev   # http://localhost:3000
```

---

## Recent Commits (latest first)

```
51af187  chore: remove Google Calendar integration entirely
322f74f  fix: create Google Calendar event on reschedule when gcal_event_id is null
5c26fef  feat: cross-week drag, post filter pills, rename Posts nav
1da3a13  feat: drag-drop rescheduling, modal date editor, Google Calendar sync
19a6cf5  fix: always assign slots at creation, remove Scheduled tab, show pending on calendar
882527b  fix: local uv PATH + GitHub Actions uv persistence across steps
84f637a  feat: trigger mini_run via GitHub Actions with live step checkpoints
56e996c  feat: show cache status and cost estimate on Run page
49d34f2  feat: Run Pipeline page — trigger mini_run.py from dashboard with live logs
655e51c  fix: avoid re-scheduling already-taken slots on mini_run reruns
816db01  fix: calendar shows approved+slotted posts, status colours, click preview
aa6f709  redesign: complete dashboard UI overhaul
```
