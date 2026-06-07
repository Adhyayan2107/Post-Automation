from __future__ import annotations

import os
from typing import List

from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from core.models.post import Post
from core.models.schedule_slot import ScheduleSlot
from config.settings import settings
from config.logging import get_logger

logger = get_logger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar"]
TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "credentials.json"

# Calendar event colours (Google Calendar colour IDs)
PLATFORM_COLOURS = {"reddit": "2", "discord": "7"}  # 2=Sage(green), 7=Blueberry


class GoogleCalendarScheduler:
    def __init__(self, service=None) -> None:
        self._service = service  # injected in tests; built lazily in prod

    def _get_service(self):
        if self._service:
            return self._service
        creds = self._load_credentials()
        self._service = build("calendar", "v3", credentials=creds)
        return self._service

    def _load_credentials(self) -> Credentials:
        creds: Credentials | None = None
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=int(settings.google.redirect_uri.split(":")[-1]))
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())
        return creds

    def create_event(self, slot: ScheduleSlot, post: Post) -> str:
        service = self._get_service()
        start = slot.scheduled_at.isoformat()
        end = (slot.scheduled_at.replace(second=0, microsecond=0)).isoformat()

        body = {
            "summary": f"[EDUBOT] {post.title}",
            "description": f"{post.body[:200]}\n\nPost ID: {post.id}",
            "start": {"dateTime": start, "timeZone": "UTC"},
            "end": {"dateTime": end, "timeZone": "UTC"},
            "colorId": PLATFORM_COLOURS.get(slot.platform, "1"),
        }

        event = service.events().insert(
            calendarId=settings.google.calendar_id, body=body
        ).execute()

        event_id: str = event["id"]
        logger.info("Created calendar event %s for post %s", event_id, post.id)
        return event_id

    def list_upcoming_events(self, days: int = 7) -> List[ScheduleSlot]:
        from datetime import datetime, timezone, timedelta
        from uuid import UUID

        service = self._get_service()
        now = datetime.now(timezone.utc)
        time_max = now + timedelta(days=days)

        events_result = service.events().list(
            calendarId=settings.google.calendar_id,
            timeMin=now.isoformat(),
            timeMax=time_max.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        slots: List[ScheduleSlot] = []
        for event in events_result.get("items", []):
            summary: str = event.get("summary", "")
            description: str = event.get("description", "")
            if not summary.startswith("[EDUBOT]"):
                continue
            post_id_line = next(
                (line for line in description.splitlines() if line.startswith("Post ID:")), ""
            )
            post_id_str = post_id_line.replace("Post ID:", "").strip()
            if not post_id_str:
                continue
            start_str = event["start"].get("dateTime", "")
            platform = "reddit" if event.get("colorId") == "2" else "discord"
            slots.append(ScheduleSlot(
                post_id=UUID(post_id_str),
                platform=platform,
                scheduled_at=datetime.fromisoformat(start_str),
                calendar_event_id=event["id"],
            ))
        return slots

    def update_event(self, event_id: str, new_scheduled_at: "datetime") -> None:
        from datetime import timedelta
        service = self._get_service()
        start = new_scheduled_at.isoformat()
        end = (new_scheduled_at + timedelta(hours=1)).isoformat()
        service.events().patch(
            calendarId=settings.google.calendar_id,
            eventId=event_id,
            body={
                "start": {"dateTime": start, "timeZone": "UTC"},
                "end":   {"dateTime": end,   "timeZone": "UTC"},
            },
        ).execute()
        logger.info("Updated calendar event %s to %s", event_id, new_scheduled_at)

    def delete_event(self, event_id: str) -> None:
        service = self._get_service()
        service.events().delete(
            calendarId=settings.google.calendar_id, eventId=event_id
        ).execute()
        logger.info("Deleted calendar event %s", event_id)
