from __future__ import annotations

import json, datetime as dt
from fastapi import HTTPException
from google.oauth2 import service_account
from googleapiclient.discovery import build, Resource
from dateutil import parser

from .config import get_settings
import traceback


settings = get_settings()

_SCOPES = ["https://www.googleapis.com/auth/calendar"]
_credentials = service_account.Credentials.from_service_account_info(
    json.loads(settings.google_credentials), scopes=_SCOPES
)
_service: Resource = build("calendar", "v3", credentials=_credentials, cache_discovery=False)

CAL_ID = settings.calendar_id
TZ = settings.time_zone

ISO = "%Y-%m-%dT%H:%M:%S%z"  # helper

def _iso(dt_obj: dt.datetime) -> str:
    return dt_obj.strftime(ISO)

# ──────────────────────────────────────────────────────────────────────────────

def list_events(start_iso: str, end_iso: str) -> list[dict]:
    """Return events overlapping [start, end)."""
    return (
        _service.events()
        .list(
            calendarId=CAL_ID,
            timeMin=start_iso,
            timeMax=end_iso,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
        .get("items", [])
    )

def is_free(start_iso: str, end_iso: str) -> bool:
    return len(list_events(start_iso, end_iso)) == 0


def create_event(summary: str, start_iso: str, end_iso: str, description: str = "") -> str:
    try:
        body = {
            "summary": summary,
            "description": description,
            "start": {"dateTime": start_iso, "timeZone": TZ},
            "end": {"dateTime": end_iso, "timeZone": TZ},
        }
        created = _service.events().insert(calendarId=CAL_ID, body=body).execute()
        return created.get("htmlLink", "<no‑link>")
    except Exception as exc:
        # 🔴 Print *full* traceback so we can see the real cause
        print("❌ Unhandled error in /chat route --------------------------------")
        traceback.print_exc()
        print("------------------------------------------------------------------")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

# Convenience helpers for naive ISO date parsing/formatting

def to_iso(dt_or_str: str | dt.datetime) -> str:
    if isinstance(dt_or_str, str):
        dt_obj = parser.isoparse(dt_or_str)
    else:
        dt_obj = dt_or_str
    if dt_obj.tzinfo is None:
        dt_obj = dt_obj.replace(tzinfo=dt.timezone.utc)
    return dt_obj.isoformat()