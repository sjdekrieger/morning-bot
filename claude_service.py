import json
import os
from collections import deque
from datetime import datetime

import anthropic

from goals import SYSTEM_PROMPT, GOALS_2026

MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001")
_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
_history: deque = deque(maxlen=40)  # 20 turns = 40 messages (user + assistant)


def _build_context_prompt() -> str:
    import calendar_service
    import storage

    today_events = calendar_service.get_today_events()
    tasks = storage.get_tasks()
    goals_str = "\n".join(f"{g['id']}. {g['title']}" for g in GOALS_2026)
    memories_str = storage.get_memories_as_text()

    events_str = calendar_service.format_events_for_message(today_events) if today_events else "Geen events vandaag."
    tasks_str = "\n".join(f"- {t}" for t in tasks) if tasks else "Nog geen taken ingepland."

    context = f"""[CONTEXT — nu beschikbaar voor dit gesprek]
Datum: {datetime.now().strftime('%A %d %B %Y, %H:%M')}

Agenda vandaag:
{events_str}

Taken voor vandaag:
{tasks_str}

Stef's doelen 2026:
{goals_str}"""

    if memories_str:
        context += f"\n\nWat ik over Stef onthouden heb (gebruik dit om je stijl en advies op aan te passen):\n{memories_str}"

    context += "\n[EINDE CONTEXT]"
    return context


def _extract_memory(user_message: str, reply: str) -> str | None:
    prompt = f"""Stef zei: "{user_message}"
Jij antwoordde: "{reply}"

Is er iets in dit gesprek wat de moeite waard is om te onthouden voor toekomstige gesprekken?

Denk aan:
- Voortgang op doelen (boeken, sport, geld, school)
- Persoonlijke info of situaties
- Hoe Stef reageert op bepaalde dingen (wil hij korte antwoorden? houdt hij niet van X?)
- Patronen in zijn gedrag of gewoontes
- Dingen waar hij mee worstelt
- Voorkeuren in communicatie

Als ja: schrijf één korte zin (max 15 woorden) die de kern vastlegt. Begin met "Stef".
Als nee: antwoord alleen met "NEE".

Voorbeelden:
- "Stef heeft 2 boeken gelezen dit jaar."
- "Stef reageert beter op korte, directe berichten zonder uitleg."
- "Stef heeft moeite met consistent sporten, heeft een zetje nodig."
- "Stef werkt liever 's avonds dan 's ochtends."
- "Stef wordt gedemotiveerd als berichten te lang zijn."

Antwoord:"""

    response = _client.messages.create(
        model=MODEL,
        max_tokens=40,
        messages=[{"role": "user", "content": prompt}],
    )
    result = response.content[0].text.strip()
    if result.upper() == "NEE" or not result.startswith("Stef"):
        return None
    return result


def chat(user_message: str) -> str:
    import storage

    if not _history:
        context = _build_context_prompt()
        _history.append({"role": "user", "content": context})
        _history.append({"role": "assistant", "content": "Begrepen, ik heb je agenda, taken, doelen en eerdere gesprekken in beeld."})

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

    # Sla relevante info op in geheugen
    memory = _extract_memory(user_message, reply)
    if memory:
        storage.add_memory(memory)

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


def get_day_comment(num_events: int, event_titles: list[str], goals: list[dict]) -> str:
    goals_str = "\n".join(f"- {g['title']}" for g in goals)
    events_str = ", ".join(event_titles) if event_titles else "geen events"
    drukte = "druk" if num_events >= 4 else ("vrij" if num_events == 0 else "normaal")

    prompt = f"""Stef's agenda vandaag heeft {num_events} events: {events_str}.
Drukte: {drukte}.

Zijn doelen voor 2026:
{goals_str}

Schrijf één korte zin (max 15 woorden) die:
- past bij hoe druk zijn dag is
- een specifiek doel noemt dat relevant is voor vandaag
- direct en eerlijk is, geen neppe motivatie

Voorbeelden:
- "Drukke dag, maar 's avonds kun je nog 30 minuten aan je portfolio werken."
- "Rustige dag — ideaal om eindelijk die 3D render af te maken."
- "Weinig tijd vandaag, focus op school en laat de rest voor morgen."

Geef ALLEEN de zin, geen uitleg."""

    response = _client.messages.create(
        model=MODEL,
        max_tokens=80,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


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
