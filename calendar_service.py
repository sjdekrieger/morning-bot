import json
import os
from datetime import datetime, date, timedelta, timezone

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]
CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")
EXTRA_CALENDARS = [c.strip() for c in os.getenv("EXTRA_CALENDAR_IDS", "").split(",") if c.strip()]
ALL_CALENDAR_IDS = [CALENDAR_ID] + EXTRA_CALENDARS

DAYS_NL = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"]
MONTHS_NL = [
    "januari", "februari", "maart", "april", "mei", "juni",
    "juli", "augustus", "september", "oktober", "november", "december",
]


def _format_date_nl(dt: datetime) -> str:
    day = DAYS_NL[dt.weekday()]
    return f"{day} {dt.day} {MONTHS_NL[dt.month - 1]}"


def _format_date_nl_date(d: date) -> str:
    day = DAYS_NL[d.weekday()]
    return f"{day} {d.day} {MONTHS_NL[d.month - 1]}"


def _get_service():
    token_json = os.getenv("GOOGLE_TOKEN_JSON")
    if not token_json:
        raise ValueError("GOOGLE_TOKEN_JSON environment variable not set")

    token_data = json.loads(token_json)
    creds = Credentials.from_authorized_user_info(token_data, SCOPES)

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    return build("calendar", "v3", credentials=creds)


def _parse_event_time(event: dict) -> tuple[datetime | None, bool]:
    """Returns (datetime, is_all_day)."""
    start = event.get("start", {})
    if "dateTime" in start:
        dt = datetime.fromisoformat(start["dateTime"])
        return dt, False
    elif "date" in start:
        d = date.fromisoformat(start["date"])
        dt = datetime(d.year, d.month, d.day)
        return dt, True
    return None, False


def _format_event(event: dict) -> str:
    start = event.get("start", {})
    end = event.get("end", {})
    title = event.get("summary", "Naamloos event")

    if "dateTime" in start:
        start_dt = datetime.fromisoformat(start["dateTime"])
        end_dt = datetime.fromisoformat(end["dateTime"])
        return f"• {start_dt.strftime('%H:%M')}–{end_dt.strftime('%H:%M')} — {title}"
    else:
        return f"• Hele dag — {title}"


def _fetch_events(calendar_id: str, time_min: str, time_max: str) -> list[dict]:
    try:
        service = _get_service()
        result = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return result.get("items", [])
    except Exception:
        return []


def _sort_events(events: list[dict]) -> list[dict]:
    def sort_key(e):
        start = e.get("start", {})
        if "dateTime" in start:
            return start["dateTime"]
        return start.get("date", "")
    return sorted(events, key=sort_key)


def get_today_events() -> list[dict]:
    now = datetime.now().astimezone()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0).isoformat()

    all_events = []
    for cal_id in ALL_CALENDAR_IDS:
        all_events.extend(_fetch_events(cal_id, start_of_day, end_of_day))
    return _sort_events(all_events)


def get_upcoming_events(days: int = 7) -> list[dict]:
    now = datetime.now().astimezone()
    future = now + timedelta(days=days)

    all_events = []
    for cal_id in ALL_CALENDAR_IDS:
        all_events.extend(_fetch_events(cal_id, now.isoformat(), future.isoformat()))
    return _sort_events(all_events)


def format_events_for_message(events: list[dict]) -> str:
    if not events:
        return "Geen events gevonden."
    return "\n".join(_format_event(e) for e in events)


def detect_free_blocks_today(events: list[dict], min_hours: float = 2.0) -> list[tuple[int, int, int]]:
    """Find free time blocks (start_min, end_min, duration_min) between 08:00 and 22:00."""
    day_start = 8 * 60   # 08:00 in minutes from midnight
    day_end = 22 * 60    # 22:00

    busy: list[tuple[int, int]] = []
    today = date.today()

    for event in events:
        start_raw = event.get("start", {})
        end_raw = event.get("end", {})
        if "dateTime" not in start_raw:
            continue
        start_dt = datetime.fromisoformat(start_raw["dateTime"])
        end_dt = datetime.fromisoformat(end_raw["dateTime"])
        if start_dt.date() != today:
            continue
        s = start_dt.hour * 60 + start_dt.minute
        e = end_dt.hour * 60 + end_dt.minute
        busy.append((max(s, day_start), min(e, day_end)))

    busy.sort()

    free_blocks: list[tuple[int, int, int]] = []
    cursor = day_start
    for s, e in busy:
        if s > cursor:
            duration = s - cursor
            if duration >= min_hours * 60:
                free_blocks.append((cursor, s, duration))
        cursor = max(cursor, e)

    if cursor < day_end:
        duration = day_end - cursor
        if duration >= min_hours * 60:
            free_blocks.append((cursor, day_end, duration))

    return free_blocks


def add_event(title: str, start_iso: str, end_iso: str, description: str = "") -> bool:
    try:
        service = _get_service()
        event = {
            "summary": title,
            "start": {"dateTime": start_iso, "timeZone": "Europe/Amsterdam"},
            "end": {"dateTime": end_iso, "timeZone": "Europe/Amsterdam"},
        }
        if description:
            event["description"] = description
        service.events().insert(calendarId="sjdekrieger@gmail.com", body=event).execute()
        return True
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("add_event failed: %s", e)
        return False


def delete_event_by_title(title: str) -> bool:
    try:
        service = _get_service()
        now = datetime.now().astimezone()
        future = now + timedelta(days=30)

        result = (
            service.events()
            .list(
                calendarId="sjdekrieger@gmail.com",
                timeMin=now.isoformat(),
                timeMax=future.isoformat(),
                singleEvents=True,
                orderBy="startTime",
                q=title,
            )
            .execute()
        )
        items = result.get("items", [])
        if not items:
            return False

        service.events().delete(calendarId="sjdekrieger@gmail.com", eventId=items[0]["id"]).execute()
        return True
    except Exception:
        return False
