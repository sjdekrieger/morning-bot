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
    import tasks_service

    today_events = calendar_service.get_today_events()
    tasks = storage.get_tasks()
    goals_str = "\n".join(f"{g['id']}. {g['title']}" for g in GOALS_2026)
    memories_str = storage.get_memories_as_text()
    google_tasks_str = tasks_service.get_tasks_as_text()

    events_str = calendar_service.format_events_for_message(today_events) if today_events else "Geen events vandaag."
    tasks_str = "\n".join(f"- {t}" for t in tasks) if tasks else "Nog geen taken ingepland."

    context = f"""[CONTEXT — nu beschikbaar voor dit gesprek]
Datum: {datetime.now().strftime('%A %d %B %Y, %H:%M')}

Agenda vandaag:
{events_str}

Taken voor vandaag (avondlijst):
{tasks_str}

Google Tasks (openstaande to-do's):
{google_tasks_str}

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
- "Stef slaat regelmatig college over — dit is een bewuste keuze, niet becommentariëren."
- "Stef wil geen opmerkingen over [X] — hij heeft dit meerdere keren aangegeven."

Let op: als Stef iets meerdere keren heeft gezegd of een voorkeur/keuze heeft aangegeven, sla dat dan op als gedragsregel zodat de bot er niet meer op terugkomt.

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

BELANGRIJK — prioriteitsregels:
1. Als het bericht expliciet woorden bevat zoals "task", "taak", "to-do", "todo", "reminder" → altijd task_add, ook als er een tijdstip in staat.
2. Als het bericht expliciet woorden bevat zoals "agenda", "event", "afspraak", "meeting", "planning" → calendar_add.
3. Als er een tijdstip staat maar geen expliciete voorkeur → calendar_add.
4. Geen tijdstip, geen expliciete voorkeur → task_add.

Geef een JSON-antwoord (ALLEEN JSON, geen uitleg):
- Als het een gewoon gesprek/vraag is:
  {{"type": "chat"}}
- Als hij een agenda-event wil toevoegen:
  {{"type": "calendar_add", "title": "naam van het event", "date_description": "datum/tijd beschrijving", "duration_hours": 1.0}}
- Als hij zijn agenda wil bekijken:
  {{"type": "calendar_view", "period": "today" of "week"}}
- Als hij een event wil verwijderen:
  {{"type": "calendar_delete", "title": "naam van het event"}}
- Als hij een taak of to-do noemt:
  {{"type": "task_add", "title": "naam van de taak"}}
- Als hij zijn Google Tasks wil zien:
  {{"type": "tasks_view"}}
- Als hij een taak wil afvinken als gedaan:
  {{"type": "task_complete", "title": "naam van de taak"}}
- Als hij een taak wil verwijderen uit Google Tasks:
  {{"type": "task_delete", "title": "naam van de taak"}}

Voorbeelden:
- "voeg gym toe morgen om 18:00" → calendar_add
- "voeg de task gym toe morgen om 18:00" → task_add (expliciet "task")
- "wat staat er vandaag in mijn agenda?" → calendar_view
- "verwijder de meeting van donderdag" → calendar_delete
- "ik moet nog mijn portfolio afmaken" → task_add
- "voeg de task wijn halen om 12 uur toe" → task_add (expliciet "task")
- "wat zijn mijn taken?" of "toon mijn to-do lijst" → tasks_view
- "ik heb mijn portfolio afgemaakt" of "vink portfolio af" → task_complete
- "verwijder taak gym" → task_delete
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


def parse_deadline(deadline_text: str) -> str | None:
    now = datetime.now()
    prompt = f"""Vandaag is {now.strftime('%A %d %B %Y')}, het is nu {now.strftime('%H:%M')}.

Zet deze deadline-beschrijving om naar een ISO 8601 datetime (tijdzone +02:00):
"{deadline_text}"

Geef ALLEEN een JSON-antwoord:
{{"deadline": "2025-01-15T17:00:00+02:00"}}"""

    response = _client.messages.create(
        model=MODEL,
        max_tokens=64,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text.strip()
    try:
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())["deadline"]
    except Exception:
        return None


def chat_image(image_bytes: bytes, caption: str = "") -> str:
    import base64
    prompt = caption.strip() if caption.strip() else "Wat zie je op deze foto?"
    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    if not _history:
        context = _build_context_prompt()
        _history.append({"role": "user", "content": context})
        _history.append({"role": "assistant", "content": "Begrepen, ik heb je agenda, taken, doelen en eerdere gesprekken in beeld."})

    message_content = [
        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_b64}},
        {"type": "text", "text": prompt},
    ]
    _history.append({"role": "user", "content": message_content})

    response = _client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=list(_history),
    )
    reply = response.content[0].text
    _history.append({"role": "assistant", "content": reply})
    return reply


def chat_with_location(user_message: str, lat: float, lon: float) -> str:
    import storage
    location_context = f"\n\n[Stef's huidige locatie: {lat:.4f}, {lon:.4f} — gebruik dit als het relevant is voor reistijd of afspraken]"
    full_message = user_message + location_context
    return chat(full_message)


def get_morning_greeting(weekday: str, num_events: int, event_titles: list[str], tasks: list[str], recent_memories: str) -> str:
    events_str = ", ".join(event_titles) if event_titles else "geen events"
    tasks_str = ", ".join(tasks[:2]) if tasks else "geen taken ingepland"
    drukte = "druk" if num_events >= 4 else ("rustig" if num_events == 0 else "normaal")

    prompt = f"""Het is {weekday}. Stef's dag is {drukte} ({num_events} events: {events_str}).
Zijn eerste taken: {tasks_str}.

Recente herinneringen over Stef:
{recent_memories or "Geen recente info."}

Schrijf een persoonlijke openingszin (max 20 woorden) voor zijn ochtendberichtje.
- Stem af op de dag (maandag = week starten, vrijdag = weekend in zicht, weekend = relaxed)
- Stem af op drukte (veel events = kort en direct, rustige dag = iets uitnodigender)
- Koppel eventueel aan iets uit zijn recente herinneringen als dat relevant is
- Geen neppe enthousiasme, geen "Geweldig!" of "Super!"
- Geen groet als "Goedemorgen" — die staat er al boven
- Gewoon één directe, persoonlijke zin

Geef ALLEEN de zin, niks anders."""

    response = _client.messages.create(
        model=MODEL,
        max_tokens=60,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def get_week_analysis(goals: list[dict], week_memories: str) -> str:
    goals_str = "\n".join(f"{g['id']}. {g['title']}" for g in goals)

    prompt = f"""Je bent de interne analyselaag van Stefs persoonlijke agent.
Je schrijft nooit direct aan Stef — je analyseert alleen.

Stefs doelen voor 2026:
{goals_str}

Wat er deze week over hem is onthouden:
{week_memories or "Geen specifieke info uit deze week."}

Analyseer in max 100 woorden:
1. Wat valt op in het patroon van deze week?
2. Wat heeft Stef nu nodig: erkenning, scherpere vraag, tijdsdruk of rust?
3. Welke 1-2 doelen verdienen aandacht op basis van patroon?
4. Is er iets wat hij zelf niet benoemt maar wat wel opvalt?

Schrijf alleen observaties en een aanbeveling. Geen aanspreking, geen berichtje."""

    response = _client.messages.create(
        model=MODEL,
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def get_weekly_goal_check(goals: list[dict], week_memories: str, week_type: str, analysis: str = "", past_observations: str = "") -> str:
    goals_str = "\n".join(f"{g['id']}. {g['title']}" for g in goals)

    week_type_instructions = {
        "A": (
            "Invalshoek deze week: WERK & VOORUITGANG\n"
            "Focus op 1-2 doelen rond design, school of portfolio.\n"
            "Centrale vraag: heeft hij iets gedaan dat telt — iets meetbaars?"
        ),
        "B": (
            "Invalshoek deze week: CONSISTENTIE\n"
            "Focus op 1-2 doelen rond sport, schermtijd, concentratie of routine.\n"
            "Centrale vraag: heeft hij gedaan wat hij zichzelf beloofde?"
        ),
        "C": (
            "Invalshoek deze week: TERUGKIJKEN\n"
            "Focus op 1-2 doelen naar keuze — maar kijk achteruit, niet vooruit.\n"
            "Centrale vraag: wat heeft hij dit jaar al bereikt richting dit doel?"
        ),
    }

    vuistregels = (
        "Zijn vuistregels:\n"
        "- Nooit werken zonder meetlat\n"
        "- Motivatie zit in terugkijken, niet in het einddoel\n"
        "- Tijdsdruk werkt voor hem"
    )

    analysis_block = f"\nInterne analyse deze week (niet letterlijk citeren):\n{analysis}\n" if analysis else ""
    past_block = f"\nPatronen uit eerdere weken (gebruik voor continuïteit, niet voor herhaling):\n{past_observations}\n" if past_observations else ""

    prompt = f"""Je bent de persoonlijke assistent van Stef (19, CMD-student Amsterdam).

{week_type_instructions.get(week_type, week_type_instructions["A"])}

Zijn 9 doelen voor 2026:
{goals_str}

{vuistregels}

Wat ik deze week over hem heb onthouden:
{week_memories or "Geen specifieke info uit deze week."}
{analysis_block}{past_block}
Schrijf nu een weekcheck-berichtje. Regels:
- Max 100 woorden
- Kies 1-2 doelen om op te focussen — noem NIET alle doelen
- Stel maximaal 2 vragen
- Sluit af met één van zijn vuistregels, passend bij deze week (niet letterlijk herhalen — verwerk het)
- Toon: direct, warm, kort — geen opsommingen, geen neppe motivatie
- In het Nederlands"""

    response = _client.messages.create(
        model=MODEL,
        max_tokens=250,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def get_week_overview_comment(week_events: list[dict], goals: list[dict]) -> str:
    titles = [e.get("summary", "") for e in week_events[:10]]
    events_str = ", ".join(titles) if titles else "geen events"
    goals_str = "\n".join(f"- {g['title']}" for g in goals)

    prompt = f"""Het is maandag. Stef's week heeft {len(week_events)} events: {events_str}.

Zijn doelen:
{goals_str}

Schrijf één zin (max 20 woorden) die:
- de toon zet voor zijn hele week
- iets noemt wat deze week haalbaar is richting zijn doelen
- direct en realistisch is

Geef ALLEEN de zin."""

    response = _client.messages.create(
        model=MODEL,
        max_tokens=60,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


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
