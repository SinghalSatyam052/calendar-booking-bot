from __future__ import annotations

import datetime as dt
from typing import Optional, List

from dateutil import parser, tz
from pydantic import BaseModel, Field
from langchain.tools import tool

from .calendar_client import is_free, list_events, create_event, to_iso
from .config import get_settings

settings = get_settings()
TZ = tz.gettz(settings.time_zone)

# ──────────────────────────────────────────────────────────────────────────────
# 🗓 1. Availability checker
# ──────────────────────────────────────────────────────────────────────────────

class AvailabilityInput(BaseModel):
    start_iso: str = Field(..., description="ISO‑8601 start datetime, e.g. 2025-07-07T14:00:00+05:30")
    end_iso:   str = Field(..., description="ISO‑8601 end datetime (> start)")

@tool(
    args_schema=AvailabilityInput,
    description="Return whether the given [start, end) range is free on the calendar, plus any conflicting event titles.",
)
def availability_tool(start_iso: str, end_iso: str) -> dict:
    """LLM‑callable wrapper for `check_availability`."""
    events = list_events(start_iso, end_iso)
    return {
        "available": len(events) == 0,
        "conflicts": [e["summary"] for e in events],
    }

# ──────────────────────────────────────────────────────────────────────────────
# 🗓 2. Slot suggester
# ──────────────────────────────────────────────────────────────────────────────

class SlotsInput(BaseModel):
    date_iso: str = Field(..., description="ISO date (YYYY‑MM‑DD) to search on")
    duration_minutes: int = Field(30, description="Length of each slot in minutes")

@tool(
    args_schema=SlotsInput,
    description="Suggest up to three free slots between 10:00 and 17:00 local time on the given date.",
)
def suggest_slots_tool(date_iso: str, duration_minutes: int = 30) -> List[dict]:
    date_obj = parser.isoparse(date_iso).astimezone(TZ).date()
    start_of_day = dt.datetime.combine(date_obj, dt.time(10, 0), tzinfo=TZ)
    cur = start_of_day
    suggestions: list[dict] = []
    while cur.hour < 17 and len(suggestions) < 3:
        start_iso = to_iso(cur)
        end_iso = to_iso(cur + dt.timedelta(minutes=duration_minutes))
        if is_free(start_iso, end_iso):
            suggestions.append({"start": start_iso, "end": end_iso})
        cur += dt.timedelta(minutes=30)
    return suggestions

# ──────────────────────────────────────────────────────────────────────────────
# 🗓 3. Booking creator
# ──────────────────────────────────────────────────────────────────────────────

class BookingInput(BaseModel):
    title: str = Field(..., description="Event title/summary")
    start_iso: str = Field(..., description="Start datetime in ISO‑8601 format")
    end_iso: str   = Field(..., description="End   datetime in ISO‑8601 format")
    notes: Optional[str] = Field(None, description="Optional description/notes to include in the calendar event")

@tool(
    args_schema=BookingInput,
    description="Create a calendar event with the given title, start, end, and notes.",
)
def booking_tool(title: str, start_iso: str, end_iso: str, notes: Optional[str] = None) -> str:
    """Create an event via the Google Calendar API and return a human‑readable confirmation."""
    # Basic validation
    if parser.isoparse(end_iso) <= parser.isoparse(start_iso):
        raise ValueError("end_iso must be after start_iso")

    link = create_event(title, start_iso, end_iso, notes or "")
    return f"✅ Booked **{title}** from {start_iso[11:16]} to {end_iso[11:16]}. Calendar link: {link}"