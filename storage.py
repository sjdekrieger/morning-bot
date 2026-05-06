import json
import os
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
TASKS_FILE = DATA_DIR / "tasks.json"
STATE_FILE = DATA_DIR / "state.json"
MEMORY_FILE = DATA_DIR / "memory.json"


def init() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not TASKS_FILE.exists():
        TASKS_FILE.write_text(json.dumps([]))
    if not STATE_FILE.exists():
        STATE_FILE.write_text(json.dumps({"awaiting_tasks": False, "goal_index": 0}))
    if not MEMORY_FILE.exists():
        MEMORY_FILE.write_text(json.dumps([]))


def _read_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {"awaiting_tasks": False, "goal_index": 0, "week_rotation": 0}


def _write_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


def save_tasks(tasks: list[str]) -> None:
    TASKS_FILE.write_text(json.dumps(tasks, ensure_ascii=False, indent=2))


def get_tasks() -> list[str]:
    try:
        return json.loads(TASKS_FILE.read_text())
    except Exception:
        return []


def is_awaiting_tasks() -> bool:
    return _read_state().get("awaiting_tasks", False)


def set_awaiting_tasks(value: bool) -> None:
    state = _read_state()
    state["awaiting_tasks"] = value
    _write_state(state)


def get_goal_index() -> int:
    return _read_state().get("goal_index", 0)


def increment_goal_index(total: int) -> int:
    state = _read_state()
    new_index = (state.get("goal_index", 0) + 1) % total
    state["goal_index"] = new_index
    _write_state(state)
    return new_index


def get_pending_task() -> str | None:
    return _read_state().get("pending_task")


def set_pending_task(task: str) -> None:
    state = _read_state()
    state["pending_task"] = task
    _write_state(state)


def clear_pending_task() -> None:
    state = _read_state()
    state.pop("pending_task", None)
    _write_state(state)


def set_location(lat: float, lon: float) -> None:
    state = _read_state()
    state["location"] = {
        "lat": lat,
        "lon": lon,
        "timestamp": datetime.now().isoformat(),
    }
    _write_state(state)


def get_location() -> dict | None:
    return _read_state().get("location")


def is_location_fresh(max_minutes: int = 30) -> bool:
    loc = get_location()
    if not loc:
        return False
    ts = datetime.fromisoformat(loc["timestamp"])
    return (datetime.now() - ts).total_seconds() < max_minutes * 60


def get_and_advance_week_rotation() -> str:
    """Geeft de huidige weektype (A/B/C) en schuift door naar de volgende."""
    state = _read_state()
    index = state.get("week_rotation", 0)
    rotation = ["A", "B", "C"]
    current = rotation[index % 3]
    state["week_rotation"] = (index + 1) % 3
    _write_state(state)
    return current


def get_week_memories() -> str:
    """Geeft geheugen uit de afgelopen 7 dagen als tekst."""
    from datetime import timedelta
    memories = get_memories()
    cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    recent = [m for m in memories if m.get("date", "") >= cutoff]
    if not recent:
        return ""
    return "\n".join(f"[{m['date']}] {m['note']}" for m in recent)


def save_weekly_observation(week_type: str, observation: str) -> None:
    memories = get_memories()
    memories.append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "type": "observation",
        "week_type": week_type,
        "note": observation,
    })
    MEMORY_FILE.write_text(json.dumps(memories[-200:], ensure_ascii=False, indent=2))


def get_recent_observations(n: int = 4) -> str:
    memories = get_memories()
    observations = [m for m in memories if m.get("type") == "observation"]
    recent = observations[-n:]
    if not recent:
        return ""
    lines = [f"[{m['date']} week-{m['week_type']}] {m['note']}" for m in recent]
    return "\n".join(lines)


def add_memory(note: str) -> None:
    memories = get_memories()
    memories.append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "note": note,
    })
    # Bewaar maximaal 200 herinneringen
    MEMORY_FILE.write_text(json.dumps(memories[-200:], ensure_ascii=False, indent=2))


def get_memories() -> list[dict]:
    try:
        return json.loads(MEMORY_FILE.read_text())
    except Exception:
        return []


def get_memories_as_text() -> str:
    memories = get_memories()
    if not memories:
        return ""
    lines = [f"[{m['date']}] {m['note']}" for m in memories[-50:]]
    return "\n".join(lines)
