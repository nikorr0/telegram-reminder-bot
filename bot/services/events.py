from __future__ import annotations

import html
import re
from datetime import datetime, time, timedelta

from bot.config import TZ
from bot.db import connect
from bot.i18n import t, status_labels
from bot.models import Event, HistoryItem, Occurrence, Reminder
from bot.services.schedule import compute_next_run, format_dt, now_ts, schedule_label, ts_to_local


def _event_from_row(row) -> Event:
    return Event(
        id=row["id"],
        chat_id=row["chat_id"],
        created_by=row["created_by"],
        title=row["title"],
        description=row["description"],
        kind=row["kind"],
        run_time=row["run_time"],
        once_date=row["once_date"],
        weekday=row["weekday"],
        month_day=row["month_day"],
        next_run_at=row["next_run_at"],
        is_active=bool(row["is_active"]),
        created_at=row["created_at"],
        created_by_name=row["created_by_name"] if "created_by_name" in row.keys() else None,
    )


def _occurrence_from_row(row) -> Occurrence:
    return Occurrence(
        id=row["id"],
        event_id=row["event_id"],
        chat_id=row["chat_id"],
        message_id=row["message_id"],
        sent_at=row["sent_at"],
        is_completed=bool(row["is_completed"]),
        is_not_completed=bool(row["is_not_completed"]),
    )


async def create_event(
    *,
    chat_id: int,
    created_by: int,
    created_by_name: str | None = None,
    title: str,
    description: str | None,
    kind: str,
    run_time: str,
    once_date: str | None = None,
    weekday: int | None = None,
    month_day: int | None = None,
) -> Event:
    next_dt = compute_next_run(
        kind,
        run_time,
        once_date=once_date,
        weekday=weekday,
        month_day=month_day,
    )
    next_run_at = int(next_dt.timestamp()) if next_dt else None
    created_at = now_ts()
    is_active = 1 if next_run_at else 0
    async with connect() as db:
        cursor = await db.execute(
            """
            INSERT INTO events (
                chat_id, created_by, created_by_name, title, description, kind, run_time,
                once_date, weekday, month_day, next_run_at, is_active, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                chat_id,
                created_by,
                created_by_name,
                title,
                description,
                kind,
                run_time,
                once_date,
                weekday,
                month_day,
                next_run_at,
                is_active,
                created_at,
            ),
        )
        event_id = cursor.lastrowid
    event = await get_event(event_id)
    assert event is not None
    return event


async def get_event(event_id: int) -> Event | None:
    async with connect() as db:
        cur = await db.execute("SELECT * FROM events WHERE id = ?", (event_id,))
        row = await cur.fetchone()
    return _event_from_row(row) if row else None


async def list_chat_events(chat_id: int) -> list[Event]:
    async with connect() as db:
        cur = await db.execute(
            """
            SELECT * FROM events
            WHERE chat_id = ? AND kind != 'once'
            ORDER BY is_active DESC, next_run_at IS NULL, next_run_at, id
            """,
            (chat_id,),
        )
        rows = await cur.fetchall()
    return [_event_from_row(row) for row in rows]


async def deactivate_event(event_id: int) -> None:
    async with connect() as db:
        await db.execute(
            "UPDATE events SET is_active = 0, next_run_at = NULL WHERE id = ?",
            (event_id,),
        )


async def activate_event(event_id: int) -> Event | None:
    event = await get_event(event_id)
    if event is None:
        return None
    nxt = compute_next_run(
        event.kind,
        event.run_time,
        once_date=event.once_date,
        weekday=event.weekday,
        month_day=event.month_day,
    )
    if nxt is None:
        return None
    async with connect() as db:
        await db.execute(
            "UPDATE events SET is_active = 1, next_run_at = ? WHERE id = ?",
            (int(nxt.timestamp()), event_id),
        )
    return await get_event(event_id)


async def delete_event(event_id: int) -> None:
    async with connect() as db:
        await db.execute("DELETE FROM events WHERE id = ?", (event_id,))


async def deactivate_chat(chat_id: int) -> None:
    async with connect() as db:
        await db.execute(
            "UPDATE events SET is_active = 0, next_run_at = NULL WHERE chat_id = ?",
            (chat_id,),
        )


async def claim_due_events(limit: int = 50) -> list[Event]:
    now = now_ts()
    claimed: list[Event] = []
    async with connect() as db:
        cur = await db.execute(
            """
            SELECT * FROM events
            WHERE is_active = 1 AND next_run_at IS NOT NULL AND next_run_at <= ?
            ORDER BY next_run_at, id
            LIMIT ?
            """,
            (now, limit),
        )
        rows = await cur.fetchall()
        for row in rows:
            event = _event_from_row(row)
            if event.kind == "once":
                new_next: int | None = None
                is_active = 0
            else:
                nxt = compute_next_run(
                    event.kind,
                    event.run_time,
                    once_date=event.once_date,
                    weekday=event.weekday,
                    month_day=event.month_day,
                    after=datetime.now(TZ),
                )
                new_next = int(nxt.timestamp()) if nxt else None
                is_active = 1 if new_next else 0
            upd = await db.execute(
                """
                UPDATE events
                SET next_run_at = ?, is_active = ?
                WHERE id = ? AND is_active = 1 AND next_run_at = ?
                """,
                (new_next, is_active, event.id, event.next_run_at),
            )
            if upd.rowcount:
                claimed.append(event)
    return claimed


async def create_occurrence(event: Event, message_id: int | None) -> Occurrence:
    sent_at = now_ts()
    async with connect() as db:
        cur = await db.execute(
            """
            INSERT INTO occurrences (event_id, chat_id, message_id, sent_at)
            VALUES (?, ?, ?, ?)
            """,
            (event.id, event.chat_id, message_id, sent_at),
        )
        occ_id = cur.lastrowid
        await db.execute(
            """
            INSERT OR IGNORE INTO history (
                chat_id, event_id, occurrence_id, title, kind,
                created_by, created_by_name, sent_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.chat_id,
                event.id,
                occ_id,
                event.title,
                event.kind,
                event.created_by,
                event.created_by_name,
                sent_at,
            ),
        )
    occ = await get_occurrence(occ_id)
    assert occ is not None
    return occ


async def update_occurrence_message(occurrence_id: int, message_id: int) -> None:
    async with connect() as db:
        await db.execute(
            "UPDATE occurrences SET message_id = ? WHERE id = ?",
            (message_id, occurrence_id),
        )


async def get_occurrence(occurrence_id: int) -> Occurrence | None:
    async with connect() as db:
        cur = await db.execute(
            "SELECT * FROM occurrences WHERE id = ?", (occurrence_id,)
        )
        row = await cur.fetchone()
    return _occurrence_from_row(row) if row else None


async def set_completed(occurrence_id: int) -> Occurrence | None:
    async with connect() as db:
        await db.execute(
            """
            UPDATE occurrences
            SET is_completed = 1, is_not_completed = 0
            WHERE id = ?
            """,
            (occurrence_id,),
        )
    return await get_occurrence(occurrence_id)


async def set_not_completed(occurrence_id: int) -> Occurrence | None:
    async with connect() as db:
        await db.execute(
            """
            UPDATE occurrences
            SET is_completed = 0, is_not_completed = 1
            WHERE id = ?
            """,
            (occurrence_id,),
        )
    return await get_occurrence(occurrence_id)


async def add_reminder(occurrence_id: int, remind_at: int) -> Reminder:
    async with connect() as db:
        cur = await db.execute(
            """
            INSERT INTO reminders (occurrence_id, remind_at, sent)
            VALUES (?, ?, 0)
            """,
            (occurrence_id, remind_at),
        )
        reminder_id = cur.lastrowid
        cur = await db.execute("SELECT * FROM reminders WHERE id = ?", (reminder_id,))
        row = await cur.fetchone()
    assert row is not None
    return Reminder(
        id=row["id"],
        occurrence_id=row["occurrence_id"],
        remind_at=row["remind_at"],
        sent=bool(row["sent"]),
    )


def snooze_timestamp(code: str) -> int:
    now = datetime.now(TZ)
    if code == "tmr":
        day = now.date() + timedelta(days=1)
        dt = datetime.combine(day, time(9, 0), tzinfo=TZ)
        return int(dt.timestamp())
    minutes = int(code)
    return int((now + timedelta(minutes=minutes)).timestamp())


async def claim_due_reminders(limit: int = 50) -> list[tuple[Reminder, Occurrence, Event]]:
    now = now_ts()
    result: list[tuple[Reminder, Occurrence, Event]] = []
    async with connect() as db:
        cur = await db.execute(
            """
            SELECT
                r.id AS r_id, r.occurrence_id, r.remind_at, r.sent,
                o.id AS o_id, o.event_id, o.chat_id, o.message_id, o.sent_at,
                o.is_completed, o.is_not_completed,
                e.id AS e_id, e.created_by, e.created_by_name, e.title, e.description, e.kind,
                e.run_time, e.once_date, e.weekday, e.month_day,
                e.next_run_at, e.is_active, e.created_at
            FROM reminders r
            JOIN occurrences o ON o.id = r.occurrence_id
            JOIN events e ON e.id = o.event_id
            WHERE r.sent = 0 AND r.remind_at <= ?
            ORDER BY r.remind_at, r.id
            LIMIT ?
            """,
            (now, limit),
        )
        rows = await cur.fetchall()
        for row in rows:
            upd = await db.execute(
                "UPDATE reminders SET sent = 1 WHERE id = ? AND sent = 0",
                (row["r_id"],),
            )
            if not upd.rowcount:
                continue
            reminder = Reminder(
                id=row["r_id"],
                occurrence_id=row["occurrence_id"],
                remind_at=row["remind_at"],
                sent=True,
            )
            occurrence = Occurrence(
                id=row["o_id"],
                event_id=row["event_id"],
                chat_id=row["chat_id"],
                message_id=row["message_id"],
                sent_at=row["sent_at"],
                is_completed=bool(row["is_completed"]),
                is_not_completed=bool(row["is_not_completed"]),
            )
            event = Event(
                id=row["e_id"],
                chat_id=row["chat_id"],
                created_by=row["created_by"],
                title=row["title"],
                description=row["description"],
                kind=row["kind"],
                run_time=row["run_time"],
                once_date=row["once_date"],
                weekday=row["weekday"],
                month_day=row["month_day"],
                next_run_at=row["next_run_at"],
                is_active=bool(row["is_active"]),
                created_at=row["created_at"],
                created_by_name=row["created_by_name"] if "created_by_name" in row.keys() else None,
            )
            result.append((reminder, occurrence, event))
    return result


_STATUS_SUFFIX_RE = re.compile(
    r"(?:\n)+(" + "|".join(re.escape(label) for label in status_labels()) + r")\s*$"
)


def status_suffix(
    lang: str | None = None,
    *,
    is_completed: bool = False,
    is_not_completed: bool = False,
) -> str:
    if is_completed:
        return t(lang, "status_done")
    if is_not_completed:
        return t(lang, "status_not_done")
    return ""


def apply_status_suffix(
    text: str,
    lang: str | None = None,
    *,
    is_completed: bool = False,
    is_not_completed: bool = False,
) -> str:
    base = _STATUS_SUFFIX_RE.sub("", text).rstrip()
    label = status_suffix(
        lang, is_completed=is_completed, is_not_completed=is_not_completed
    )
    if not label:
        return base
    return f"{base}\n\n{label}"


def format_notification(
    event: Event,
    *,
    lang: str | None = None,
    is_reminder: bool = False,
    is_completed: bool = False,
    is_not_completed: bool = False,
) -> str:
    prefix = t(lang, "reminder_prefix") if is_reminder else ""
    lines = [f"{prefix}<b>{html.escape(event.title)}</b>"]
    if event.description:
        lines.append(html.escape(event.description))
    text = "\n\n".join(lines)
    return apply_status_suffix(
        text,
        lang,
        is_completed=is_completed,
        is_not_completed=is_not_completed,
    )


def format_event_card(index: int, event: Event, lang: str | None = None) -> str:
    when = schedule_label(
        event.kind,
        event.run_time,
        once_date=event.once_date,
        weekday=event.weekday,
        month_day=event.month_day,
        lang=lang,
    )
    nxt = t(lang, "next_label", when=format_dt(event.next_run_at)) if event.next_run_at else ""
    paused = t(lang, "paused") if not event.is_active else ""
    return f"<b>{index}.</b> {html.escape(event.title)}\n{when}{nxt}{paused}"


def format_event_list(events: list[Event], lang: str | None = None) -> str:
    if not events:
        return t(lang, "list_empty")
    body = "\n\n".join(
        format_event_card(i, event, lang) for i, event in enumerate(events, start=1)
    )
    return t(lang, "list_header", body=body)


HISTORY_PAGE_SIZE = 8


def _history_from_row(row) -> HistoryItem:
    return HistoryItem(
        id=row["id"],
        chat_id=row["chat_id"],
        event_id=row["event_id"],
        occurrence_id=row["occurrence_id"],
        title=row["title"],
        kind=row["kind"],
        created_by=row["created_by"],
        created_by_name=row["created_by_name"],
        sent_at=row["sent_at"],
    )


async def list_history(
    chat_id: int,
    *,
    page: int = 0,
    page_size: int = HISTORY_PAGE_SIZE,
) -> tuple[list[HistoryItem], int]:
    async with connect() as db:
        cur = await db.execute(
            "SELECT COUNT(*) AS n FROM history WHERE chat_id = ?",
            (chat_id,),
        )
        total = int((await cur.fetchone())["n"])
        pages = max(1, (total + page_size - 1) // page_size) if total else 1
        page = min(max(0, page), pages - 1)
        cur = await db.execute(
            """
            SELECT * FROM history
            WHERE chat_id = ?
            ORDER BY sent_at DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            (chat_id, page_size, page * page_size),
        )
        rows = await cur.fetchall()
    return [_history_from_row(row) for row in rows], total


def _author_label(item: HistoryItem) -> str:
    name = (item.created_by_name or "").strip()
    if name:
        return html.escape(name)
    return f"id {item.created_by}"


def format_history_text(
    items: list[HistoryItem],
    lang: str | None,
    *,
    show_author: bool,
    page: int,
    total: int,
    page_size: int = HISTORY_PAGE_SIZE,
) -> str:
    if not items:
        return t(lang, "history_empty")
    pages = max(1, (total + page_size - 1) // page_size)
    cards = []
    start = page * page_size
    for offset, item in enumerate(items, start=1):
        local = ts_to_local(item.sent_at)
        kind = t(lang, "history_kind_once" if item.kind == "once" else "history_kind_repeat")
        lines = [
            f"<b>{start + offset}.</b> {html.escape(item.title)}",
            t(
                lang,
                "history_when",
                date=local.strftime("%d.%m.%Y"),
                time=local.strftime("%H:%M"),
            ),
            t(lang, "history_kind", kind=kind),
        ]
        if show_author:
            lines.append(t(lang, "history_author", name=_author_label(item)))
        cards.append("\n".join(lines))
    body = "\n\n".join(cards)
    header = t(lang, "history_header", page=page + 1, pages=pages)
    return f"{header}\n\n{body}"
