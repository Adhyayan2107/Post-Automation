# EduBot — Claude Code Master Instructions

## What This Project Is

A fully automated weekly content pipeline for IB, IGCSE, A-Level and AS-Level education communities.
It scrapes the internet, generates posts (educational + creative/anime-angle), sources images, routes
drafts through a human approval dashboard, schedules approved posts on Google Calendar, and auto-publishes
to Reddit and Discord at the right times.

---

## Golden Rules — Read Before Every Task

1. **Follow SOLID strictly.** Every class has one job. New platforms/sources are added by writing new
   classes, never by editing existing ones. All agents depend on abstractions (interfaces), never on
   concrete implementations.

2. **Never put secrets in code.** All keys, tokens, and credentials live in `.env` only. Use
   `config/settings.py` (Pydantic `BaseSettings`) to load them.

3. **Async-first Python.** Use `httpx.AsyncClient`, `asyncio`, and `async/await` throughout the
   Python backend. No `requests` library.

4. **Type everything.** All Python functions have full type hints. All TypeScript is strict mode.

5. **Dataclasses/Pydantic for all data shapes.** No raw dicts passed between layers.

6. **One migration per schema change.** Never edit existing migrations. Always add a new one.

7. **Test the interface contract, not the implementation.** Unit tests mock at the interface boundary.

8. **Dashboard is Next.js App Router on Vercel.** No Pages Router. No class components.

9. **Keep Python agents and Next.js dashboard completely separate.** They share only the database
   (Supabase). The agents write to the DB; the dashboard reads/writes to the DB via Supabase client.

10. **When in doubt, ask before implementing.** This project has external API costs and rate limits.
    Pause and confirm before adding any paid API calls.

---

## Tech Stack

### Python Backend (Agents + Scheduler)
| Purpose          | Library              |
|------------------|----------------------|
| HTTP client      | `httpx` (async)      |
| HTML parsing     | `BeautifulSoup4`     |
| RSS/Atom feeds   | `feedparser`         |
| Claude API       | `anthropic`          |
| Reddit posting   | `praw`               |
| Discord posting  | `discord-webhook`    |
| Google APIs      | `google-api-python-client` + `google-auth` |
| Database ORM     | `sqlmodel` + `supabase-py` |
| Job scheduling   | `apscheduler`        |
| Image sourcing   | `pexels-api` (free)  |
| Templating       | `jinja2`             |
| Config           | `pydantic-settings`  |
| Testing          | `pytest` + `pytest-asyncio` |

### Next.js Dashboard (Vercel)
| Purpose          | Library              |
|------------------|----------------------|
| Framework        | Next.js 14 App Router|
| Database client  | `@supabase/supabase-js` |
| UI components    | `shadcn/ui`          |
| Styling          | Tailwind CSS         |
| State            | React Server Components + `useState` |
| Date handling    | `date-fns`           |
| Deployment       | Vercel               |

### Infrastructure
| Service          | Purpose              | Cost    |
|------------------|----------------------|---------|
| Supabase         | Postgres database    | Free    |
| Vercel           | Dashboard hosting    | Free    |
| Pexels API       | Stock images         | Free    |
| Google Cloud     | Calendar + Gmail API | Free    |
| Reddit API       | PRAW posting         | Free    |
| Discord Webhook  | Discord posting      | Free    |
| Claude API       | Content generation   | Pay-per-use |
| GitHub Actions   | Weekly cron trigger  | Free    |

---

## Repository Layout

```
edu-automation-bot/
│
├── CLAUDE.md                      ← you are here
├── PROJECT_SPEC.md                ← detailed spec per phase
├── .env.example
├── .gitignore
├── README.md
│
├── agents/                        # Python: AI orchestration layer
│   ├── __init__.py
│   ├── orchestrator.py            # FatherAgent — weekly entry point
│   ├── scraper_agent.py           # Coordinates all scrapers, deduplicates
│   ├── content_agent.py           # Generates straight educational posts
│   ├── creative_agent.py          # Generates anime/pop-culture angle posts
│   └── image_agent.py             # Sources images per post
│
├── core/                          # Pure abstractions — no implementations here
│   ├── interfaces/
│   │   ├── scraper.py             # AbstractScraper (ABC)
│   │   ├── content_generator.py   # AbstractContentGenerator (ABC)
│   │   ├── image_provider.py      # AbstractImageProvider (ABC)
│   │   └── publisher.py           # AbstractPublisher (ABC)
│   └── models/
│       ├── raw_content.py         # RawContent dataclass
│       ├── post.py                # Post dataclass + PostStatus enum
│       └── schedule_slot.py       # ScheduleSlot dataclass
│
├── scrapers/                      # One class per source, all extend AbstractScraper
│   ├── __init__.py
│   ├── ib_official.py             # ibo.org, subject guides, exam updates
│   ├── reddit_scraper.py          # r/IBO, r/IGCSE, r/6thForm, r/alevel
│   ├── news_scraper.py            # Google News RSS for IB/IGCSE keywords
│   ├── youtube_scraper.py         # Edu channel titles via YouTube Data API
│   └── cambrige_scraper.py        # Cambridge Assessment news feed
│
├── generators/                    # One class per post type, all extend AbstractContentGenerator
│   ├── __init__.py
│   ├── educational_post.py        # "Here's what changed in IB Chemistry HL"
│   ├── creative_post.py           # "Luffy's freedom = French Revolution concept"
│   └── prompts/
│       ├── educational.jinja2
│       ├── creative_anime.jinja2
│       ├── creative_movies.jinja2
│       └── creative_history.jinja2
│
├── image_providers/               # All extend AbstractImageProvider
│   ├── __init__.py
│   ├── pexels.py                  # Primary — free API
│   └── unsplash.py                # Fallback — free API
│
├── publishers/                    # All extend AbstractPublisher
│   ├── __init__.py
│   ├── reddit.py                  # Posts to target subreddits via PRAW
│   └── discord.py                 # Posts via webhook
│
├── scheduler/
│   ├── __init__.py
│   ├── google_calendar.py         # Creates/reads calendar events for approved posts
│   ├── time_optimizer.py          # Returns best UTC posting times per platform/day
│   └── runner.py                  # APScheduler: polls calendar, fires publishers
│
├── storage/
│   ├── __init__.py
│   ├── database.py                # Supabase client + SQLModel session factory
│   ├── repositories/
│   │   ├── post_repository.py     # CRUD for Post model
│   │   └── run_log_repository.py  # CRUD for weekly run logs
│   └── migrations/
│       └── 001_initial_schema.sql
│
├── config/
│   ├── __init__.py
│   ├── settings.py                # Pydantic BaseSettings — all env vars typed here
│   └── logging.py                 # Structured logging setup
│
├── tests/
│   ├── conftest.py
│   ├── test_scrapers/
│   ├── test_generators/
│   ├── test_publishers/
│   └── test_scheduler/
│
├── dashboard/                     # Next.js App Router — deployed to Vercel
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── .env.local.example
│   └── src/
│       ├── app/
│       │   ├── layout.tsx
│       │   ├── page.tsx                  # Redirect to /posts
│       │   ├── posts/
│       │   │   ├── page.tsx              # Post queue: pending approval
│       │   │   └── [id]/
│       │   │       └── page.tsx          # Single post detail + approve/reject
│       │   └── schedule/
│       │       └── page.tsx              # Weekly calendar view of approved posts
│       ├── components/
│       │   ├── PostCard.tsx
│       │   ├── ApprovalButtons.tsx
│       │   ├── WeekCalendar.tsx
│       │   └── StatusBadge.tsx
│       ├── lib/
│       │   ├── supabase.ts               # Supabase client (browser + server)
│       │   └── types.ts                  # Shared TypeScript types
│       └── actions/
│           └── posts.ts                  # Server Actions for approve/reject/edit
│
└── .github/
    └── workflows/
        └── weekly_run.yml             # Triggers orchestrator every Monday 6AM UTC
```

---

## Data Flow (Step by Step)

```
1. GitHub Actions cron → runs orchestrator.py
2. orchestrator.py → calls scraper_agent.py
3. scraper_agent.py → fans out to all scrapers in parallel (asyncio.gather)
4. Each scraper → returns List[RawContent]
5. scraper_agent.py → deduplicates by URL + semantic similarity, saves to DB
6. orchestrator.py → calls content_agent.py and creative_agent.py with raw content
7. content_agent.py → generates 3-5 educational posts via Claude API
8. creative_agent.py → generates 2-3 anime/pop-culture angle posts via Claude API
9. Each generator → calls image_agent.py for a matching image
10. image_agent.py → queries Pexels API with keywords, returns image URL
11. All posts saved to DB with status = "pending"
12. Dashboard reads pending posts from Supabase
13. You approve / reject / edit each post in the dashboard
14. Approved posts → scheduler reads them, creates Google Calendar events
15. time_optimizer.py → slots posts at optimal times (Reddit: 9AM/12PM/7PM local)
16. runner.py APScheduler → at event time, calls appropriate publisher
17. reddit.py → posts via PRAW to target subreddits
18. discord.py → posts via webhook to configured channel
19. Post status updated to "published" in DB
```

---

## Post Data Model

```python
class PostStatus(str, Enum):
    PENDING   = "pending"     # Generated, awaiting your review
    APPROVED  = "approved"    # You approved it, awaiting scheduling
    REJECTED  = "rejected"    # You rejected it
    SCHEDULED = "scheduled"   # On Google Calendar
    PUBLISHED = "published"   # Live on Reddit/Discord
    FAILED    = "failed"      # Publishing failed — check logs

class Post(SQLModel, table=True):
    id: UUID
    title: str
    body: str                 # Full post text (markdown)
    post_type: str            # "educational" | "creative"
    creative_angle: str | None  # "anime" | "movie" | "history" | None
    image_url: str | None
    source_urls: list[str]    # Where the content came from
    target_platforms: list[str]  # ["reddit", "discord"]
    target_subreddits: list[str] # ["r/IBO", "r/IGCSE"]
    status: PostStatus
    scheduled_at: datetime | None
    published_at: datetime | None
    created_at: datetime
    run_id: UUID              # Which weekly run generated this
```

---

## Reddit Strategy (My Recommendation)

**Post to existing subreddits** — don't create your own yet. Existing audiences are already there.

Target subreddits:
- `r/IBO` — 50k+ members, IB-focused
- `r/igcse` — active IGCSE community
- `r/6thForm` — UK A-Level students
- `r/alevel` — A/AS Level focused

Rules per sub: each post checks subreddit rules before posting (scrape sidebar rules once at setup).
Educational / creative posts alternate to avoid spam flags.

---

## SOLID Implementation Guide

| Principle | How It Applies Here |
|-----------|---------------------|
| **S** — Single Responsibility | `pexels.py` only fetches images. `time_optimizer.py` only calculates times. `post_repository.py` only does DB operations. |
| **O** — Open/Closed | To add a new scraper (e.g. `CollegeBoard`), create `scrapers/collegeboard.py`, extend `AbstractScraper`, register in `scraper_agent.py`. Zero existing files change. |
| **L** — Liskov Substitution | `Pexels`, `Unsplash` both extend `AbstractImageProvider`. `image_agent.py` accepts `AbstractImageProvider` — swap freely. |
| **I** — Interface Segregation | `AbstractPublisher` has only `publish(post: Post)`. It does not have `schedule()` or `login()`. Scheduling is `AbstractScheduler`'s job. |
| **D** — Dependency Inversion | `content_agent.py` depends on `AbstractContentGenerator`, not `EducationalPostGenerator`. Injected at runtime via `config/settings.py`. |

---

## Environment Variables (`.env`)

```bash
# Claude API
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

# Pexels
PEXELS_API_KEY=

# Unsplash
UNSPLASH_ACCESS_KEY=

# Supabase
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# App
LOG_LEVEL=INFO
DRY_RUN=false          # If true, skip actual publishing — log only
WEEKLY_RUN_DAY=monday
```

---

## Build Order for Claude Code

Follow these phases in order. **Do not start a phase until the previous one passes its tests.**

### Phase 0 — Project Bootstrap
- Init Python project with `pyproject.toml` (uv or poetry)
- Init Next.js dashboard with `create-next-app` (TypeScript, Tailwind, App Router)
- Set up `.env.example`, `.gitignore`, `config/settings.py`
- Set up Supabase project + run `001_initial_schema.sql`
- Confirm Supabase connection from Python

### Phase 1 — Core Abstractions
- Write all interfaces in `core/interfaces/`
- Write all dataclasses in `core/models/`
- Write `storage/database.py` and `storage/repositories/`
- No implementations yet — just contracts

### Phase 2 — Scrapers
- Implement `news_scraper.py` first (RSS, simplest)
- Then `reddit_scraper.py` (PRAW read-only)
- Then `ib_official.py` and `cambridge_scraper.py`
- Then `youtube_scraper.py`
- Write tests for each
- Build `scraper_agent.py` to fan-out + deduplicate

### Phase 3 — Content Generators
- Write Jinja2 prompt templates first
- Implement `educational_post.py`
- Implement `creative_post.py` (anime/movie angles)
- Build `content_agent.py` and `creative_agent.py`
- Write tests with mocked Claude responses

### Phase 4 — Image Agent
- Implement `pexels.py`
- Implement `unsplash.py` as fallback
- Build `image_agent.py` with fallback chain
- Write tests

### Phase 5 — Approval Dashboard
- Scaffold Next.js with shadcn/ui
- Build `/posts` page — list of pending posts, sortable
- Build `/posts/[id]` page — full preview, approve/reject/edit buttons
- Build `/schedule` page — weekly calendar of approved posts
- Wire Server Actions for status mutations
- Deploy to Vercel + connect Supabase env vars

### Phase 6 — Scheduler
- Implement `time_optimizer.py`
- Implement `google_calendar.py`
- Implement `runner.py` with APScheduler

### Phase 7 — Publishers
- Implement `reddit.py` with PRAW
- Implement `discord.py` with webhook
- Write dry-run tests

### Phase 8 — Orchestrator + GitHub Actions
- Implement `orchestrator.py` — full weekly pipeline
- Write `weekly_run.yml` GitHub Actions workflow
- End-to-end test with `DRY_RUN=true`

---

## Prompt to Start Each Phase

Use this prefix when starting any phase:

> "We are building `edu-automation-bot`. Read `CLAUDE.md` and `PROJECT_SPEC.md` first.
> We are on **Phase N — [Name]**. Follow the SOLID rules in CLAUDE.md.
> Implement only what is listed for this phase. Do not implement future phases.
> Start with the interfaces/contracts before any implementations.
> All async, all typed, no secrets in code."
