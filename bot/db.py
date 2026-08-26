from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import aiosqlite

from bot.config import DATA_DIR, DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    created_by INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    kind TEXT NOT NULL CHECK (kind IN ('once', 'daily', 'weekly', 'monthly')),
    run_time TEXT NOT NULL,
    once_date TEXT,
    weekday INTEGER,
    month_day INTEGER,
    next_run_at INTEGER,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS occurrences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    chat_id INTEGER NOT NULL,
    message_id INTEGER,
    sent_at INTEGER NOT NULL,
    is_completed INTEGER NOT NULL DEFAULT 0,
    is_not_completed INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    occurrence_id INTEGER NOT NULL,
    remind_at INTEGER NOT NULL,
    sent INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (occurrence_id) REFERENCES occurrences(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_events_due
    ON events (is_active, next_run_at);

CREATE INDEX IF NOT EXISTS idx_reminders_due
    ON reminders (sent, remind_at);

CREATE INDEX IF NOT EXISTS idx_events_chat
    ON events (chat_id, is_active);

CREATE TABLE IF NOT EXISTS chats (
    chat_id INTEGER PRIMARY KEY,
    lang TEXT NOT NULL DEFAULT 'ru'
);

CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    event_id INTEGER,
    occurrence_id INTEGER UNIQUE,
    title TEXT NOT NULL,
    kind TEXT NOT NULL,
    created_by INTEGER NOT NULL,
    created_by_name TEXT,
    sent_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_history_chat
    ON history (chat_id, sent_at DESC);
"""


async def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await _ensure_column(db, "events", "created_by_name", "TEXT")
        await _backfill_history(db)
        await db.commit()


async def _ensure_column(
    db: aiosqlite.Connection, table: str, column: str, col_type: str
) -> None:
    cur = await db.execute(f"PRAGMA table_info({table})")
    names = {row[1] for row in await cur.fetchall()}
    if column not in names:
        await db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")


async def _backfill_history(db: aiosqlite.Connection) -> None:
    await db.execute(
        """
        INSERT OR IGNORE INTO history (
            chat_id, event_id, occurrence_id, title, kind,
            created_by, created_by_name, sent_at
        )
        SELECT
            o.chat_id, o.event_id, o.id, e.title, e.kind,
            e.created_by, e.created_by_name, o.sent_at
        FROM occurrences o
        JOIN events e ON e.id = o.event_id
        """
    )


@asynccontextmanager
async def connect() -> AsyncIterator[aiosqlite.Connection]:
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys = ON")
    try:
        yield db
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    finally:
        await db.close()
