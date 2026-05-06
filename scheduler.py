import os
from datetime import datetime

from telegram.ext import ContextTypes

import storage
import quotes_service
import calendar_service
import claude_service
from goals import GOALS_2026

CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))

DAYS_NL = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]
MONTHS_NL = [
    "januari", "februari", "maart", "april", "mei", "juni",
    "juli", "augustus", "september", "oktober", "november", "december",
]


def format_date_nl(dt: datetime) -> str:
    day = DAYS_NL[dt.weekday()]
    return f"{day} {dt.day} {MONTHS_NL[dt.month - 1]} {dt.year}"


async def send_morning_message(context: ContextTypes.DEFAULT_TYPE) -> None:
    now = datetime.now()
    date_str = format_date_nl(now)

    lines = [f"Goedemorgen! ☀️\n*{date_str}*\n"]

    # Agenda vandaag
    today_events = calendar_service.get_today_events()
    lines.append("*📅 Agenda vandaag:*")
    if today_events:
        lines.append(calendar_service.format_events_for_message(today_events))
    else:
        lines.append("Geen events vandaag.")

    # Deadlines komende 7 dagen
    upcoming = calendar_service.get_upcoming_events(days=7)
    deadlines = [e for e in upcoming if any(
        kw in e.get("summary", "").lower()
        for kw in ["deadline", "inlever", "opdracht", "presentatie", "tentamen", "toets", "examen"]
    )]
    if deadlines:
        lines.append("\n*⚠️ Deadlines komende week:*")
        lines.append(calendar_service.format_events_for_message(deadlines))

    # 4 taken van gisteren
    tasks = storage.get_tasks()
    lines.append("\n*✅ Jouw 4 taken voor vandaag:*")
    if tasks:
        for i, task in enumerate(tasks[:4], 1):
            lines.append(f"{i}. {task}")
    else:
        lines.append("Nog geen taken ingepland. Stuur me vanavond je 4 belangrijkste dingen voor morgen.")

    # Dag-opmerking op basis van drukte + doelen
    timed_events = [e for e in today_events if "dateTime" in e.get("start", {})]
    event_titles = [e.get("summary", "") for e in timed_events]
    day_comment = claude_service.get_day_comment(len(timed_events), event_titles, GOALS_2026)
    lines.append(f"\n_{day_comment}_")

    # Motiverende quote
    quote = quotes_service.get_quote()
    lines.append(f"\n*💬 Quote:*\n_{quote}_")

    # Vrije tijd suggestie
    free_blocks = calendar_service.detect_free_blocks_today(today_events, min_hours=2.0)
    if free_blocks:
        longest_block = max(free_blocks, key=lambda b: b[2])
        start_min, end_min, duration_min = longest_block
        start_h = start_min // 60
        start_m = start_min % 60
        end_h = end_min // 60
        end_m = end_min % 60

        goal_index = storage.get_goal_index()
        goal = GOALS_2026[goal_index % len(GOALS_2026)]
        storage.increment_goal_index(len(GOALS_2026))

        suggestion = claude_service.get_goal_suggestion(duration_min, goal)
        lines.append(
            f"\n*🎯 Vrij blok {start_h:02d}:{start_m:02d}–{end_h:02d}:{end_m:02d} "
            f"({duration_min // 60}u{duration_min % 60 or ''})*"
        )
        lines.append(f"Doel: _{goal['short']}_\n{suggestion}")

    message = "\n".join(lines)
    await context.bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")


async def send_evening_message(context: ContextTypes.DEFAULT_TYPE) -> None:
    storage.set_awaiting_tasks(True)
    message = (
        "Wat zijn je *4 belangrijkste dingen voor morgen*?\n\n"
        "Stuur ze één voor één, of als een genummerde lijst. "
        "Ik sla ze op en stuur ze morgenochtend terug."
    )
    await context.bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
