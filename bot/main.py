from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from bot.config import BOT_TOKEN
from bot.db import init_db
from bot.handlers.callbacks import router as callbacks_router
from bot.handlers.commands import router as commands_router
from bot.i18n import t
from bot.middlewares import LangMiddleware
from bot.services.scheduler import run_scheduler

logger = logging.getLogger(__name__)


def _commands(lang: str) -> list[BotCommand]:
    return [
        BotCommand(command="start", description=t(lang, "cmd_start")),
        BotCommand(command="help", description=t(lang, "cmd_help")),
        BotCommand(command="add", description=t(lang, "cmd_add")),
        BotCommand(command="list", description=t(lang, "cmd_list")),
        BotCommand(command="history", description=t(lang, "cmd_history")),
        BotCommand(command="lang", description=t(lang, "cmd_lang")),
        BotCommand(command="cancel", description=t(lang, "cmd_cancel")),
    ]


async def _set_commands(bot: Bot) -> None:
    await bot.set_my_commands(_commands("ru"))
    await bot.set_my_commands(_commands("en"), language_code="en")


async def main() -> None:
    if not BOT_TOKEN:
        raise SystemExit("Не задан BOT_TOKEN. Скопируйте .env.example в .env и укажите токен.")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stdout,
    )

    await init_db()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.middleware(LangMiddleware())
    dp.callback_query.middleware(LangMiddleware())
    dp.include_routers(commands_router, callbacks_router)

    await _set_commands(bot)

    scheduler_task = asyncio.create_task(run_scheduler(bot), name="scheduler")
    logger.info("Bot polling started")
    try:
        await dp.start_polling(bot)
    finally:
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
