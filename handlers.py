import re

from telegram import Update
from telegram.ext import ContextTypes

import storage
import claude_service
import calendar_service
from goals import GOALS_2026


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hey Stef! Ik ben je persoonlijke assistent.\n\n"
        "Ik stuur je elke ochtend om 7:00 je dagplanning en elke avond om 23:00 vraag ik "
        "je om je 4 taken voor morgen.\n\n"
        "Je kunt me ook gewoon berichten sturen — ik help met je agenda, plannen, vragen, noem maar op.\n\n"
        "Commando's:\n"
        "/agenda — Agenda van vandaag\n"
        "/taken — Jouw taken voor morgen\n"
        "/doelen — Jouw doelen voor 2026\n"
        "/help — Dit bericht"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Wat ik voor je kan doen:\n\n"
        "• Agenda bekijken: 'wat staat er vandaag?' of /agenda\n"
        "• Event toevoegen: 'voeg gym toe morgen om 18:00'\n"
        "• Event verwijderen: 'verwijder de meeting van donderdag'\n"
        "• Taken bekijken: /taken\n"
        "• Doelen bekijken: /doelen\n"
        "• Gewoon praten: stel een vraag of vertel wat je bezighoudt\n\n"
        "Elke ochtend om 7:00 stuur ik je een dagstart.\n"
        "Elke avond om 23:00 vraag ik je om je 4 taken voor morgen."
    )


async def agenda_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    events = calendar_service.get_today_events()
    if events:
        text = "*📅 Agenda vandaag:*\n" + calendar_service.format_events_for_message(events)
    else:
        text = "Geen events vandaag."
    await update.message.reply_text(text, parse_mode="Markdown")


async def tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tasks = storage.get_tasks()
    if tasks:
        lines = ["*✅ Jouw taken voor morgen:*"]
        for i, task in enumerate(tasks, 1):
            lines.append(f"{i}. {task}")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    else:
        await update.message.reply_text("Nog geen taken opgeslagen. Ik vraag je er vanavond om 23:00 naar.")


async def goals_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lines = ["*🎯 Jouw doelen voor 2026:*\n"]
    for goal in GOALS_2026:
        lines.append(f"{goal['id']}. {goal['title']}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message.text.strip()

    if storage.is_awaiting_tasks():
        await _handle_task_input(update, message)
        return

    intent = claude_service.classify_intent(message)
    intent_type = intent.get("type", "chat")

    if intent_type == "calendar_add":
        await _handle_calendar_add(update, intent)
    elif intent_type == "calendar_view":
        period = intent.get("period", "today")
        await _handle_calendar_view(update, period)
    elif intent_type == "calendar_delete":
        await _handle_calendar_delete(update, intent)
    else:
        reply = claude_service.chat(message)
        await _send_long_message(update, reply)


async def _handle_task_input(update: Update, message: str) -> None:
    tasks = _parse_tasks(message)
    if not tasks:
        await update.message.reply_text("Ik kon geen taken herkennen. Stuur ze als lijst, bijvoorbeeld:\n1. Portfolio afmaken\n2. Sporten\n3. Hoofdstuk lezen")
        return

    storage.save_tasks(tasks)
    storage.set_awaiting_tasks(False)

    lines = ["Opgeslagen! Morgenochtend krijg je ze terug.\n\n*Jouw 4 taken voor morgen:*"]
    for i, task in enumerate(tasks[:4], 1):
        lines.append(f"{i}. {task}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


def _parse_tasks(message: str) -> list[str]:
    lines = [line.strip() for line in message.strip().splitlines() if line.strip()]
    tasks = []
    for line in lines:
        # Strip common list prefixes: "1.", "1)", "-", "•", "*"
        cleaned = re.sub(r"^(\d+[.)]\s*|[-•*]\s*)", "", line).strip()
        if cleaned:
            tasks.append(cleaned)
    return tasks[:4]


async def _handle_calendar_add(update: Update, intent: dict) -> None:
    title = intent.get("title", "Nieuw event")
    date_description = intent.get("date_description", "")
    duration_hours = float(intent.get("duration_hours", 1.0))

    if not date_description:
        await update.message.reply_text("Wanneer moet het event plaatsvinden? Geef een datum en tijd.")
        return

    await update.message.reply_text(f"Event toevoegen: _{title}_...", parse_mode="Markdown")

    result = claude_service.parse_date_with_claude(date_description, duration_hours)
    if not result:
        await update.message.reply_text("Ik kon de datum niet verwerken. Probeer het opnieuw met een duidelijkere datum, bijvoorbeeld 'morgen om 14:00'.")
        return

    start_iso, end_iso = result
    success = calendar_service.add_event(title, start_iso, end_iso)

    if success:
        await update.message.reply_text(f"✓ _{title}_ toegevoegd aan je agenda.", parse_mode="Markdown")
    else:
        await update.message.reply_text("Het lukte niet om het event toe te voegen. Controleer de Google Calendar instellingen.")


async def _handle_calendar_view(update: Update, period: str) -> None:
    if period == "week":
        events = calendar_service.get_upcoming_events(days=7)
        header = "*📅 Agenda komende week:*"
    else:
        events = calendar_service.get_today_events()
        header = "*📅 Agenda vandaag:*"

    if events:
        text = header + "\n" + calendar_service.format_events_for_message(events)
    else:
        text = "Geen events gevonden."
    await update.message.reply_text(text, parse_mode="Markdown")


async def _handle_calendar_delete(update: Update, intent: dict) -> None:
    title = intent.get("title", "")
    if not title:
        await update.message.reply_text("Welk event wil je verwijderen?")
        return

    success = calendar_service.delete_event_by_title(title)
    if success:
        await update.message.reply_text(f"✓ _{title}_ verwijderd uit je agenda.", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"Geen event gevonden met de naam '{title}' in de komende 30 dagen.")


async def _send_long_message(update: Update, text: str) -> None:
    if len(text) <= 4000:
        await update.message.reply_text(text)
        return
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    for chunk in chunks:
        await update.message.reply_text(chunk)
