""" "Panoptibot Telegram bot"""

import datetime
import logging
import os

import dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes

from panoptibot.propel import Propel
from panoptibot.tools import format_table

logger = logging.getLogger("telegram_bot")

# Secrets
dotenv.load_dotenv(override=True)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


def run_panoptibot() -> None:
    """Run the bot"""

    propel = Propel()

    # Commands
    async def health_command(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Get health command"""

        table = []
        for service in propel.services.values():
            for agent in service.agents.values():
                is_agent_healthy, period = agent.healthcheck()
                if is_agent_healthy:
                    table.append([agent.name, "✅", f"P{period}"])
                else:
                    table.append([agent.name, "❌", f"P{period}"])

        await update.message.reply_text(
            text=f"```Healthcheck\n{format_table(table)}```",
            parse_mode=ParseMode.MARKDOWN_V2,
            disable_web_page_preview=True,
        )

    async def rounds_command(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Get rounds command"""

        table = []
        for service in propel.services.values():
            for agent in service.agents.values():
                round_ = agent.get_current_round()
                table.append([agent.name, round_])

        await update.message.reply_text(
            text=f"```Rounds\n{format_table(table)}```",
            parse_mode=ParseMode.MARKDOWN_V2,
            disable_web_page_preview=True,
        )

    async def state_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Get state command"""

        table = []
        for service in propel.services.values():
            for agent in service.agents.values():
                state = agent.get_agent_state()
                table.append([agent.name, state])

        await update.message.reply_text(
            text=f"```State\n{format_table(table)}```",
            parse_mode=ParseMode.MARKDOWN_V2,
            disable_web_page_preview=True,
        )

    async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Reset a service"""

        if len(context.args) != 1:
            await update.message.reply_text(
                text="Please provide a single valid service name",
                parse_mode=ParseMode.MARKDOWN_V2,
                disable_web_page_preview=True,
            )
            return

        service_name = context.args[0]
        service = propel.services.get(service_name, None)

        if service is None:
            await update.message.reply_text(
                text="Please provide a valid service name",
                parse_mode=ParseMode.MARKDOWN_V2,
                disable_web_page_preview=True,
            )
            return

        service.restart()

        await update.message.reply_text(
            text=f"Service {service_name} is being restarted",
            parse_mode=ParseMode.MARKDOWN_V2,
            disable_web_page_preview=True,
        )

    async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Stop a service"""

        if len(context.args) != 1:
            await update.message.reply_text(
                text="Please provide a single valid service name",
                parse_mode=ParseMode.MARKDOWN_V2,
                disable_web_page_preview=True,
            )
            return

        service_name = context.args[0]
        service = propel.services.get(service_name, None)

        if service is None:
            await update.message.reply_text(
                text="Please provide a valid service name",
                parse_mode=ParseMode.MARKDOWN_V2,
                disable_web_page_preview=True,
            )
            return

        service.stop()

        await update.message.reply_text(
            text=f"Service {service_name} is being stopped",
            parse_mode=ParseMode.MARKDOWN_V2,
            disable_web_page_preview=True,
        )

    # Tasks
    async def start(context: ContextTypes.DEFAULT_TYPE):
        """Start"""
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text="Panoptibot has started",
        )

    async def health_task(context: ContextTypes.DEFAULT_TYPE):
        logger.info("Running healthcheck task")

        message = ""
        for service in propel.services.values():
            service.healthcheck()
            now = datetime.datetime.now()
            if service.not_healthy_counter >= 30 and (
                service.last_notification is None
                or now - service.last_notification > datetime.timedelta(hours=1)
            ):
                message += f"Service {service.name} is not healthy\n"
                service.last_notification = now

            if service.not_healthy_counter >= 120:
                is_restarting = False
                for agent in service.agents.values():
                    agent_state = agent.get_agent_state()
                    if agent_state.lower() == "restarting":
                        is_restarting = True
                        break

                if (
                    not is_restarting
                    and now - service.last_restart > datetime.timedelta(minutes=30)
                ):
                    service.restart()
                    service.last_restart = now
                    message += f"Service {service.name} is being restarted\n"

        if message:
            await context.bot.send_message(chat_id=CHAT_ID, text=message)

    async def post_init(app):
        await app.bot.set_my_description("A bot to monitor Olas services")
        await app.bot.set_my_short_description("A bot to monitor Olas services")
        await app.bot.set_my_commands(
            [
                ("healthcheck", "Check the services health"),
                ("rounds", "Check the agent current rounds"),
                ("state", "Check the agent state on Propel"),
                ("reset", "Reset a service"),
                ("stop", "Stop a service"),
            ]
        )

    # Create bot
    app = Application.builder().token(TELEGRAM_TOKEN).post_init(post_init).build()
    job_queue = app.job_queue

    # Add commands
    app.add_handler(CommandHandler("healthcheck", health_command))
    app.add_handler(CommandHandler("rounds", rounds_command))
    app.add_handler(CommandHandler("state", state_command))
    app.add_handler(CommandHandler("reset", reset_command))
    app.add_handler(CommandHandler("stop", stop_command))

    # Add tasks
    job_queue.run_once(start, when=3)  # in 1 second
    job_queue.run_repeating(
        health_task,
        interval=datetime.timedelta(minutes=1),
        first=5,  # in 5 seconds
    )

    # Start
    logger.info("Starting bot")
    app.run_polling()
