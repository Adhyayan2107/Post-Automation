-- Google Calendar integration removed. The dashboard's built-in WeekCalendar
-- serves as the scheduling UI; the runner polls scheduled_at from the DB directly.
ALTER TABLE posts DROP COLUMN IF EXISTS gcal_event_id;
