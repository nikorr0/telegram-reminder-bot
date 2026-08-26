from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, User

from bot.i18n import lang_from_code
from bot.services.chats import get_chat_lang, set_chat_lang


class LangMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        chat_id: int | None = None
        user: User | None = None
        if isinstance(event, Message):
            chat_id = event.chat.id
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            if event.message:
                chat_id = event.message.chat.id
        if chat_id is not None:
            data["lang"] = await _resolve(chat_id, user)
        else:
            data["lang"] = lang_from_code(user.language_code if user else None)
        return await handler(event, data)


async def _resolve(chat_id: int, user: User | None) -> str:
    stored = await get_chat_lang(chat_id)
    if stored:
        return stored
    lang = lang_from_code(user.language_code if user else None)
    await set_chat_lang(chat_id, lang)
    return lang
