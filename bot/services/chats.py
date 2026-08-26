from __future__ import annotations

from bot.db import connect
from bot.i18n import SUPPORTED, normalize_lang


async def get_chat_lang(chat_id: int) -> str | None:
    async with connect() as db:
        cur = await db.execute(
            "SELECT lang FROM chats WHERE chat_id = ?", (chat_id,)
        )
        row = await cur.fetchone()
    if row is None:
        return None
    lang = row["lang"]
    return lang if lang in SUPPORTED else None


async def set_chat_lang(chat_id: int, lang: str) -> None:
    lang = normalize_lang(lang)
    async with connect() as db:
        await db.execute(
            """
            INSERT INTO chats (chat_id, lang) VALUES (?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET lang = excluded.lang
            """,
            (chat_id, lang),
        )
