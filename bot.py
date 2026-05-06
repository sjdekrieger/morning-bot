import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from apscheduler.triggers.cron import CronTrigger

load_dotenv()

import storage
from telegram.ext import filters as tg_filters
from handlers import start, help_command, agenda_command, tasks_command, goals_command, locatie_command, handle_location, handle_photo, handle_message
from scheduler import send_morning_message, send_evening_message, send_weekly_goal_check

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))
TIMEZONE = os.getenv("TIMEZONE", "Europe/Amsterdam")


async def post_init(application: Application) -> None:
    storage.init()
    logger.info("Storage initialized")
    await application.bot.send_message(
        chat_id=CHAT_ID,
        text=(
            "🤖 *Bot is online!*\n\n"
            "Alles werkt. Ik stuur je elke ochtend om 7:00 je dagstart "
            "en elke avond om 23:00 vraag ik je om je 4 taken voor morgen.\n\n"
            "Stuur /help voor een overzicht van wat ik kan."
        ),
        parse_mode="Markdown",
    )
    logger.info("Startup message sent to chat_id=%s", CHAT_ID)


def main() -> None:
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN environment variable not set")
    if not CHAT_ID:
        raise ValueError("TELEGRAM_CHAT_ID environment variable not set")

    app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("agenda", agenda_command))
    app.add_handler(CommandHandler("taken", tasks_command))
    app.add_handler(CommandHandler("doelen", goals_command))
    app.add_handler(CommandHandler("locatie", locatie_command))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.job_queue.run_custom(
        send_morning_message,
        job_kwargs={"trigger": CronTrigger(hour=7, minute=0, timezone=TIMEZONE)},
    )
    app.job_queue.run_custom(
        send_evening_message,
        job_kwargs={"trigger": CronTrigger(hour=23, minute=0, timezone=TIMEZONE)},
    )
    app.job_queue.run_custom(
        send_weekly_goal_check,
        job_kwargs={"trigger": CronTrigger(day_of_week="sun", hour=20, minute=0, timezone=TIMEZONE)},
    )

    logger.info("Bot starting — morning 07:00, evening 23:00, weekly check sun 20:00 (%s)", TIMEZONE)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
