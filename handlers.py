import os
import re
from datetime import datetime, timedelta

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ContextTypes

import storage
import claude_service
import calendar_service
import tasks_service
from goals import GOALS_2026

CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))

LOCATION_KEYWORDS = ["meeting", "afspraak", "op tijd", "hoe laat vertrek", "onderweg", "kan ik halen", "reistijd", "halen"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hey Stef! Ik ben je persoonlijke assistent.\n\n"
        "Ik stuur je elke ochtend om 7:00 je dagplanning en elke avond om 23:00 vraag ik "
        "je om je 4 taken voor morgen.\n\n"
        "Commando's:\n"
        "/agenda — Agenda van vandaag\n"
        "/taken — Jouw taken voor morgen\n"
        "/doelen — Jouw doelen voor 2026\n"
        "/locatie — Deel je locatie\n"
        "/help — Dit bericht"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Wat ik voor je kan doen:\n\n"
        "• Agenda bekijken: 'wat staat er vandaag?' of /agenda\n"
        "• Event toevoegen: 'voeg gym toe morgen om 18:00'\n"
        "• Event verwijderen: 'verwijder de meeting van donderdag'\n"
        "• Taak toevoegen: 'ik moet nog mijn portfolio afmaken'\n"
        "• Taken bekijken: /taken\n"
        "• Doelen bekijken: /doelen\n"
        "• Locatie delen: /locatie\n"
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


async def locatie_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[KeyboardButton("📍 Deel locatie", request_location=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Druk op de knop om je locatie te delen.", reply_markup=reply_markup)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    photo = update.message.photo[-1]  # hoogste resolutie
    caption = update.message.caption or ""
    file = await context.bot.get_file(photo.file_id)
    image_bytes = await file.download_as_bytearray()
    reply = claude_service.chat_image(bytes(image_bytes), caption)
    await _send_long_message(update, reply)


async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    loc = update.message.location
    storage.set_location(loc.latitude, loc.longitude)
    await update.message.reply_text(
        "Locatie ontvangen. Ik gebruik hem de komende 30 minuten als het relevant is.",
        reply_markup=ReplyKeyboardRemove()
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message.text.strip()

    # Taak deadline flow
    if storage.get_pending_task():
        await _handle_deadline_input(update, context, message)
        return

    # Avond taken flow
    if storage.is_awaiting_tasks():
        await _handle_task_input(update, message)
        return

    # Proactief locatie vragen als relevant
    if any(kw in message.lower() for kw in LOCATION_KEYWORDS) and not storage.is_location_fresh():
        keyboard = [[KeyboardButton("📍 Deel locatie", request_location=True)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(
            "Deel je locatie zodat ik reistijd kan meenemen.",
            reply_markup=reply_markup
        )

    intent = claude_service.classify_intent(message)
    intent_type = intent.get("type", "chat")

    if intent_type == "calendar_add":
        await _handle_calendar_add(update, intent)
    elif intent_type == "calendar_view":
        period = intent.get("period", "today")
        await _handle_calendar_view(update, period)
    elif intent_type == "calendar_delete":
        await _handle_calendar_delete(update, intent)
    elif intent_type == "task_add":
        task_title = intent.get("title", message)
        storage.set_pending_task(task_title)
        await update.message.reply_text(f"Wanneer is de deadline voor *{task_title}*?", parse_mode="Markdown")
    elif intent_type == "tasks_view":
        text = "*📋 Google Tasks:*\n" + tasks_service.get_tasks_as_text()
        await update.message.reply_text(text, parse_mode="Markdown")
    elif intent_type == "task_complete":
        title = intent.get("title", "")
        success = tasks_service.complete_task_by_title(title)
        if success:
            await update.message.reply_text(f"✓ *{title}* afgevinkt.", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"Geen taak gevonden met de naam '{title}'.")
    elif intent_type == "task_delete":
        title = intent.get("title", "")
        success = tasks_service.delete_task_by_title(title)
        if success:
            await update.message.reply_text(f"✓ *{title}* verwijderd.", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"Geen taak gevonden met de naam '{title}'.")
    else:
        loc = storage.get_location()
        if storage.is_location_fresh() and loc:
            reply = claude_service.chat_with_location(message, loc["lat"], loc["lon"])
        else:
            reply = claude_service.chat(message)
        await _send_long_message(update, reply)


def _smart_reminder_delay(remaining_seconds: float, deadline_dt: datetime) -> float:
    """Berekent slimme reminder-timing op basis van hoe ver de deadline weg is."""
    now = datetime.now(deadline_dt.tzinfo)

    if remaining_seconds > 48 * 3600:
        # Meer dan 2 dagen: herinner de dag ervoor om 18:00
        day_before_18 = (deadline_dt - timedelta(days=1)).replace(hour=18, minute=0, second=0, microsecond=0)
        if day_before_18 > now:
            return (day_before_18 - now).total_seconds()
        # Als 18:00 gisteren al voorbij is, herinner 's ochtends om 9:00 op de dag zelf
        morning = deadline_dt.replace(hour=9, minute=0, second=0, microsecond=0)
        if morning > now:
            return (morning - now).total_seconds()

    if remaining_seconds > 6 * 3600:
        # 6-48 uur: herinner 3 uur van tevoren, maar minimaal om 9:00 's ochtends
        remind_at = deadline_dt - timedelta(hours=3)
        morning = remind_at.replace(hour=9, minute=0, second=0, microsecond=0)
        remind_at = max(remind_at, morning)
        if remind_at > now:
            return (remind_at - now).total_seconds()

    # Minder dan 6 uur: herinner 1 uur van tevoren (minimaal 20 minuten)
    return max(remaining_seconds - 3600, 1200)


async def _handle_deadline_input(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str) -> None:
    task = storage.get_pending_task()
    storage.clear_pending_task()

    deadline_iso = claude_service.parse_deadline(message)
    if not deadline_iso:
        await update.message.reply_text("Ik kon die datum niet begrijpen. Taak opgeslagen zonder deadline.")
        return

    deadline_dt = datetime.fromisoformat(deadline_iso)
    now = datetime.now(deadline_dt.tzinfo)
    remaining = (deadline_dt - now).total_seconds()

    if remaining <= 0:
        await update.message.reply_text("Die deadline is al voorbij. Taak niet opgeslagen.")
        return

    reminder_delay = _smart_reminder_delay(remaining, deadline_dt)
    deadline_str = deadline_dt.strftime("%a %d %b om %H:%M")

    context.job_queue.run_once(
        _send_reminder,
        when=reminder_delay,
        data={"task": task, "deadline_str": deadline_str},
        chat_id=CHAT_ID,
    )

    tasks_service.add_task(task, deadline_iso)

    reminder_at = datetime.now(deadline_dt.tzinfo) + timedelta(seconds=reminder_delay)
    reminder_str = reminder_at.strftime("%a %d %b om %H:%M")
    await update.message.reply_text(
        f"✓ *{task}* toegevoegd aan Google Tasks.\n"
        f"Deadline: {deadline_str}\n"
        f"Reminder: {reminder_str}",
        parse_mode="Markdown"
    )


async def _send_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    task = context.job.data["task"]
    deadline_str = context.job.data["deadline_str"]
    await context.bot.send_message(
        chat_id=context.job.chat_id,
        text=f"⏰ Reminder: *{task}* — deadline is {deadline_str}.",
        parse_mode="Markdown"
    )


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
        await update.message.reply_text("Het lukte niet om het event toe te voegen.")


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
