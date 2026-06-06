# EduBot — Automated Education Content Pipeline

A fully automated weekly content pipeline for IB, IGCSE, A-Level and AS-Level education communities on Reddit and Discord.

EduBot scrapes the internet for education news, generates posts (educational + creative/anime-angle) via Claude AI, sources images, routes drafts through a human approval dashboard, schedules approved posts on Google Calendar, and auto-publishes at optimal times.

---

## What It Does

```
Monday 6AM UTC (GitHub Actions cron)
    ↓
Scrape 5 sources in parallel
(Google News, Reddit, IBO, Cambridge, YouTube)
    ↓
Generate posts via Claude API
• 3–5 educational posts ("Here's what changed in IB Chemistry HL")
• 2–3 creative posts ("Luffy's freedom = French Revolution concept")
    ↓
Source images from Pexels → Unsplash fallback
    ↓
Save to Supabase (status: pending)
Gmail summary → you
    ↓
You review in Next.js dashboard
Approve / Reject / Edit
    ↓
TimeOptimizer assigns slots → Google Calendar events created
    ↓
APScheduler fires at event time
→ Reddit (PRAW) + Discord (webhook)
    ↓
Status updated to "published" in DB
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Content generation | Claude API (`claude-sonnet-4-6`) |
| Scraping | `httpx`, `BeautifulSoup4`, `feedparser`, `PRAW` |
| Scheduling | `APScheduler`, Google Calendar API |
| Publishing | `PRAW` (Reddit), `discord-webhook` |
| Database | Supabase (Postgres) |
| Dashboard | Next.js 16 App Router, Tailwind CSS, shadcn/ui |
| Dashboard hosting | Vercel |
| Automation | GitHub Actions (weekly cron) |
| Images | Pexels API → Unsplash fallback |
| Notifications | Gmail API |
| Config | Pydantic Settings |

---

## Repository Structure

```
edu-automation-bot/
├── agents/              # Orchestration layer
│   ├── orchestrator.py  # FatherAgent — weekly entry point
│   ├── scraper_agent.py # Fans out to all scrapers, deduplicates
│   ├── content_agent.py # Generates educational posts
│   ├── creative_agent.py# Generates anime/pop-culture posts
│   └── image_agent.py   # Sources images per post
│
├── core/                # Pure abstractions — no implementations
│   ├── interfaces/      # AbstractScraper, AbstractPublisher, etc.
│   └── models/          # RawContent, Post, ScheduleSlot dataclasses
│
├── scrapers/            # One class per source
│   ├── news_scraper.py  # Google News RSS
│   ├── reddit_scraper.py# r/IBO, r/igcse, r/6thForm, r/alevel
│   ├── ib_official.py   # ibo.org news
│   ├── cambridge_scraper.py
│   └── youtube_scraper.py
│
├── generators/          # Claude-powered post generators
│   ├── educational_post.py
│   ├── creative_post.py # Anime + movie angle posts
│   └── prompts/         # Jinja2 prompt templates
│
├── image_providers/     # Pexels + Unsplash
├── publishers/          # Reddit + Discord
│
├── scheduler/
│   ├── time_optimizer.py   # Best UTC slots per platform/day
│   ├── google_calendar.py  # Calendar event management
│   ├── runner.py           # APScheduler — fires publishers
│   └── gmail_notifier.py   # Weekly summary email
│
├── storage/
│   ├── database.py          # Supabase client
│   ├── repositories/        # PostRepository, RunLogRepository
│   └── migrations/
│       └── 001_initial_schema.sql
│
├── config/
│   ├── settings.py     # Pydantic BaseSettings — all env vars
│   └── logging.py      # Structured JSON logging
│
├── dashboard/          # Next.js 16 App Router (deploy to Vercel)
│   └── src/
│       ├── app/
│       │   ├── posts/       # Pending post queue
│       │   ├── posts/[id]/  # Full preview + approve/reject
│       │   └── schedule/    # Weekly calendar view
│       ├── components/
│       └── actions/posts.ts # Server Actions
│
├── scripts/
│   ├── mini_run.py     # Quick 2-post test run
│   └── dry_run.py      # Full pipeline, no publishing
│
├── tests/              # 91 tests, all passing
└── .github/
    └── workflows/
        └── weekly_run.yml  # Monday 6AM UTC cron
```

---

## Setup

### 1. Clone & install

```bash
git clone https://github.com/Adhyayan2107/Post-Automation.git
cd Post-Automation

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies (Python 3.12)
uv sync
```

### 2. Environment variables

```bash
cp .env.example .env
# Fill in all values — see section below
```

### 3. Supabase

1. Create a project at [supabase.com](https://supabase.com)
2. Go to **SQL Editor → New query**
3. Paste and run `storage/migrations/001_initial_schema.sql`
4. Copy your **URL**, **anon key**, and **service role key** into `.env`

> Run without RLS — this is a personal-use tool with no end users.

### 4. Google Calendar + Gmail

1. [Google Cloud Console](https://console.cloud.google.com) → New project
2. Enable: **Google Calendar API** + **Gmail API**
3. Create **OAuth 2.0 credentials** (Desktop app) → download as `credentials.json` → put in project root
4. Add your email as a **test user** in OAuth consent screen
5. First run opens a browser for one-time consent, saves `token.json`

### 5. Other API keys

| Service | Where to get it |
|---|---|
| Claude API | [console.anthropic.com](https://console.anthropic.com) |
| Reddit | [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) → script app |
| Discord | Server Settings → Integrations → Webhooks |
| Pexels | [pexels.com/api](https://www.pexels.com/api/) |
| Unsplash | [unsplash.com/developers](https://unsplash.com/developers) |

### 6. Dashboard (Vercel)

```bash
cd dashboard
cp .env.local.example .env.local
# Fill in NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY

npx vercel --prod
```

### 7. GitHub Actions

Add all variables from `.env.example` as **GitHub Secrets** in your repo:  
`Settings → Secrets and variables → Actions → New repository secret`

---

## Environment Variables

```bash
# Claude
ANTHROPIC_API_KEY=

# Reddit
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USERNAME=
REDDIT_PASSWORD=
REDDIT_USER_AGENT=EduBot/1.0

# Discord
DISCORD_WEBHOOK_URL=

# Google
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_CALENDAR_ID=
GOOGLE_REDIRECT_URI=http://localhost:8080
GMAIL_NOTIFY_ADDRESS=

# Pexels / Unsplash
PEXELS_API_KEY=
UNSPLASH_ACCESS_KEY=

# Supabase
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# App
LOG_LEVEL=INFO
DRY_RUN=false
WEEKLY_RUN_DAY=monday
```

---

## Running Locally

```bash
# Quick 2-post test (scrape → generate → image → Supabase → Calendar)
uv run python scripts/mini_run.py

# Full dry run (no DB writes, no publishing)
uv run python scripts/dry_run.py

# Full weekly pipeline
uv run python -m agents.orchestrator

# Run tests
uv run pytest
```

---

## Post Types

| Type | Description | Platforms |
|---|---|---|
| Educational | News-based: "What changed in IB Chemistry HL" | Reddit + Discord |
| Creative (anime) | "Luffy's freedom = French Revolution — IB History" | Reddit + Discord |
| Creative (movie) | "Oppenheimer's moral crisis — IB Ethics" | Discord |

Target subreddits: `r/IBO`, `r/igcse`, `r/6thForm`, `r/alevel`

---

## Posting Schedule

Optimal UTC slots (audience in UK/Europe/Asia):

| Day | Reddit | Discord |
|---|---|---|
| Mon | 08:00 | 16:00 |
| Tue | 12:00 | 16:00 |
| Wed | 18:00 | 20:00 |
| Thu | 08:00 | 16:00 |
| Fri | 12:00 | 17:00 |
| Sat | 10:00 | 12:00 |
| Sun | 16:00 | 18:00 |

Minimum 4-hour gap enforced between posts on the same platform.

---

## Architecture Principles

Built strictly following **SOLID**:

- **S** — Every class has one job (`pexels.py` only fetches images)
- **O** — Add a new scraper by creating a new file, zero existing files change
- **L** — `Pexels` and `Unsplash` both extend `AbstractImageProvider`, swap freely
- **I** — `AbstractPublisher` only has `publish()`, nothing else
- **D** — Agents depend on abstractions, not concrete implementations

---

## Cost

| Service | Cost |
|---|---|
| Claude API | ~$0.10–0.30 per weekly run |
| Everything else | Free tier |

Set a spending limit in [Anthropic Console](https://console.anthropic.com) to avoid surprises.

---

## License

MIT
