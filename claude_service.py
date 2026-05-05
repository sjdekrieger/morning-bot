import json
import os
from collections import deque
from datetime import datetime

import anthropic

from goals import SYSTEM_PROMPT

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
_history: deque = deque(maxlen=40)  # 20 turns = 40 messages (user + assistant)


def chat(user_message: str) -> str:
    _history.append({"role": "user", "content": user_message})
    messages = list(_history)

    response = _client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=messages,
    )
    reply = response.content[0].text
    _history.append({"role": "assistant", "content": reply})
    return reply


def classify_intent(message: str) -> dict:
    prompt = f"""Analyseer dit bericht van Stef en bepaal de intentie.

Bericht: "{message}"

Geef een JSON-antwoord (ALLEEN JSON, geen uitleg):
- Als het een gewoon gesprek/vraag is:
  {{"type": "chat"}}
- Als hij een agenda-event wil toevoegen:
  {{"type": "calendar_add", "title": "naam van het event", "date_description": "datum/tijd beschrijving", "duration_hours": 1.0}}
- Als hij zijn agenda wil bekijken:
  {{"type": "calendar_view", "period": "today" of "week"}}
- Als hij een event wil verwijderen:
  {{"type": "calendar_delete", "title": "naam van het event"}}

Voorbeelden:
- "voeg gym toe morgen om 18:00" → calendar_add
- "wat staat er vandaag in mijn agenda?" → calendar_view
- "verwijder de meeting van donderdag" → calendar_delete
- "hoe pak ik mijn portfolio aan?" → chat"""

    response = _client.messages.create(
        model=MODEL,
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text.strip()
    try:
        # Strip markdown code blocks if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception:
        return {"type": "chat"}


def parse_date_with_claude(date_description: str, duration_hours: float = 1.0) -> tuple[str, str] | None:
    now = datetime.now()
    prompt = f"""Vandaag is {now.strftime('%A %d %B %Y')}, het is nu {now.strftime('%H:%M')}.

Zet deze datum/tijdbeschrijving om naar ISO 8601 formaat (inclusief tijdzone +02:00 voor zomertijd of +01:00 voor wintertijd):
"{date_description}"

Duur: {duration_hours} uur

Geef ALLEEN een JSON-antwoord:
{{"start": "2025-01-15T14:00:00+01:00", "end": "2025-01-15T15:00:00+01:00"}}"""

    response = _client.messages.create(
        model=MODEL,
        max_tokens=128,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text.strip()
    try:
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text.strip())
        return data["start"], data["end"]
    except Exception:
        return None


def get_goal_suggestion(free_minutes: int, goal: dict) -> str:
    hours = free_minutes // 60
    minutes = free_minutes % 60
    time_str = f"{hours} uur" if minutes == 0 else f"{hours} uur {minutes} minuten"

    prompt = f"""Stef heeft vandaag een aaneengesloten blok van {time_str} vrije tijd.

Zijn doel: {goal['title']}

Geef een CONCRETE, specifieke suggestie wat hij in dit tijdblok kan doen voor dit doel.
Maximaal 2 zinnen. Direct en zonder neppe enthousiasme. In het Nederlands."""

    response = _client.messages.create(
        model=MODEL,
        max_tokens=150,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()
