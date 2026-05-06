import json
import os
from datetime import datetime, timezone

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/tasks",
]


def _get_service():
    token_json = os.getenv("GOOGLE_TOKEN_JSON")
    if not token_json:
        raise ValueError("GOOGLE_TOKEN_JSON not set")
    creds = Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build("tasks", "v1", credentials=creds)


def _get_default_list_id() -> str:
    service = _get_service()
    result = service.tasklists().list().execute()
    lists = result.get("items", [])
    return lists[0]["id"] if lists else "@default"


def get_tasks() -> list[dict]:
    try:
        service = _get_service()
        list_id = _get_default_list_id()
        result = service.tasks().list(
            tasklist=list_id,
            showCompleted=False,
            showHidden=False,
        ).execute()
        return result.get("items", [])
    except Exception:
        return []


def get_tasks_as_text() -> str:
    tasks = get_tasks()
    if not tasks:
        return "Geen openstaande taken in Google Tasks."
    lines = []
    for t in tasks:
        title = t.get("title", "")
        due = t.get("due", "")
        if due:
            due_dt = datetime.fromisoformat(due.replace("Z", "+00:00"))
            due_str = due_dt.strftime("%a %d %b")
            lines.append(f"• {title} (voor {due_str})")
        else:
            lines.append(f"• {title}")
    return "\n".join(lines)


def add_task(title: str, due_iso: str = "") -> bool:
    try:
        service = _get_service()
        list_id = _get_default_list_id()
        task = {"title": title}
        if due_iso:
            task["due"] = due_iso
        service.tasks().insert(tasklist=list_id, body=task).execute()
        return True
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("add_task failed: %s", e)
        return False


def complete_task_by_title(title: str) -> bool:
    try:
        service = _get_service()
        list_id = _get_default_list_id()
        result = service.tasks().list(tasklist=list_id, showCompleted=False).execute()
        tasks = result.get("items", [])
        match = next((t for t in tasks if title.lower() in t.get("title", "").lower()), None)
        if not match:
            return False
        match["status"] = "completed"
        service.tasks().update(tasklist=list_id, task=match["id"], body=match).execute()
        return True
    except Exception:
        return False


def delete_task_by_title(title: str) -> bool:
    try:
        service = _get_service()
        list_id = _get_default_list_id()
        result = service.tasks().list(tasklist=list_id, showCompleted=False).execute()
        tasks = result.get("items", [])
        match = next((t for t in tasks if title.lower() in t.get("title", "").lower()), None)
        if not match:
            return False
        service.tasks().delete(tasklist=list_id, task=match["id"]).execute()
        return True
    except Exception:
        return False
