import json
import os
from pathlib import Path

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
TASKS_FILE = DATA_DIR / "tasks.json"
STATE_FILE = DATA_DIR / "state.json"


def init() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not TASKS_FILE.exists():
        TASKS_FILE.write_text(json.dumps([]))
    if not STATE_FILE.exists():
        STATE_FILE.write_text(json.dumps({"awaiting_tasks": False, "goal_index": 0}))


def _read_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {"awaiting_tasks": False, "goal_index": 0}


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
