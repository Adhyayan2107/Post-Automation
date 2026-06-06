-- EduBot initial schema
-- Run this in Supabase SQL editor

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Weekly pipeline runs
CREATE TABLE IF NOT EXISTS weekly_runs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    started_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    status      TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed')),
    post_count  INTEGER NOT NULL DEFAULT 0
);

-- Raw scraped content (deduplicated by URL per run)
CREATE TABLE IF NOT EXISTS raw_content (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url         TEXT NOT NULL,
    title       TEXT NOT NULL,
    body        TEXT NOT NULL DEFAULT '',
    source      TEXT NOT NULL,
    scraped_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    run_id      UUID NOT NULL REFERENCES weekly_runs(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS raw_content_url_run_idx ON raw_content(url, run_id);

-- Generated posts pending approval
CREATE TABLE IF NOT EXISTS posts (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title             TEXT NOT NULL,
    body              TEXT NOT NULL,
    post_type         TEXT NOT NULL CHECK (post_type IN ('educational', 'creative')),
    creative_angle    TEXT CHECK (creative_angle IN ('anime', 'movie', 'history')),
    image_url         TEXT,
    source_urls       TEXT[] NOT NULL DEFAULT '{}',
    target_platforms  TEXT[] NOT NULL DEFAULT '{}',
    target_subreddits TEXT[] NOT NULL DEFAULT '{}',
    status            TEXT NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'approved', 'rejected', 'scheduled', 'published', 'failed')),
    scheduled_at      TIMESTAMPTZ,
    published_at      TIMESTAMPTZ,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    run_id            UUID NOT NULL REFERENCES weekly_runs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS posts_status_idx ON posts(status);
CREATE INDEX IF NOT EXISTS posts_run_id_idx ON posts(run_id);

-- Scheduling slots linking posts to calendar events
CREATE TABLE IF NOT EXISTS post_schedule (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id             UUID NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    platform            TEXT NOT NULL CHECK (platform IN ('reddit', 'discord')),
    scheduled_at        TIMESTAMPTZ NOT NULL,
    calendar_event_id   TEXT
);

CREATE INDEX IF NOT EXISTS post_schedule_post_id_idx ON post_schedule(post_id);
CREATE INDEX IF NOT EXISTS post_schedule_scheduled_at_idx ON post_schedule(scheduled_at);
