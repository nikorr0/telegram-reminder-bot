from __future__ import annotations

import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from bot.config import SCHEDULER_INTERVAL_SEC
from bot.keyboards import event_action_kb
from bot.i18n import DEFAULT_LANG
from bot.services.chats import get_chat_lang
from bot.services.events import (
    claim_due_events,
    claim_due_reminders,
    create_occurrence,
    deactivate_chat,
    format_notification,
    update_occurrence_message,
)

logger = logging.getLogger(__name__)


def _is_chat_unavailable(exc: BaseException) -> bool:
    text = str(exc).lower()
    markers = (
        "chat not found",
        "bot was kicked",
        "bot was blocked",
        "forbidden",
        "have no rights to send",
        "group chat was upgraded",
        "need administrator rights",
        "not enough rights",
    )
    return any(marker in text for marker in markers)


async def _send(bot: Bot, chat_id: int, text: str, reply_markup) -> int | None:
    try:
        message = await bot.send_message(chat_id, text, reply_markup=reply_markup)
        return message.message_id
    except TelegramForbiddenError:
        logger.warning("No access to chat %s, deactivating events", chat_id)
        await deactivate_chat(chat_id)
        return None
    except TelegramBadRequest as exc:
        if _is_chat_unavailable(exc):
            logger.warning("Chat %s unavailable (%s), deactivating events", chat_id, exc)
            await deactivate_chat(chat_id)
            return None
        logger.exception("Failed to send message to chat %s", chat_id)
        return None
    except Exception:
        logger.exception("Failed to send message to chat %s", chat_id)
        return None


async def _chat_lang(chat_id: int) -> str:
    return await get_chat_lang(chat_id) or DEFAULT_LANG


async def process_due_events(bot: Bot) -> None:
    events = await claim_due_events()
    for event in events:
        lang = await _chat_lang(event.chat_id)
        occ = await create_occurrence(event, message_id=None)
        markup = event_action_kb(occ.id, lang)
        message_id = await _send(
            bot, event.chat_id, format_notification(event, lang=lang), markup
        )
        if message_id is not None:
            await update_occurrence_message(occ.id, message_id)


async def process_due_reminders(bot: Bot) -> None:
    reminders = await claim_due_reminders()
    for _reminder, occ, event in reminders:
        lang = await _chat_lang(occ.chat_id)
        markup = event_action_kb(
            occ.id,
            lang,
            is_completed=occ.is_completed,
            is_not_completed=occ.is_not_completed,
        )
        await _send(
            bot,
            occ.chat_id,
            format_notification(
                event,
                lang=lang,
                is_reminder=True,
                is_completed=occ.is_completed,
                is_not_completed=occ.is_not_completed,
            ),
            markup,
        )


async def run_scheduler(bot: Bot) -> None:
    logger.info("Scheduler started, interval=%ss", SCHEDULER_INTERVAL_SEC)
    while True:
        try:
            await process_due_events(bot)
            await process_due_reminders(bot)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Scheduler tick failed")
        await asyncio.sleep(SCHEDULER_INTERVAL_SEC)
