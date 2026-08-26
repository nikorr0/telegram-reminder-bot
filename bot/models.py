from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Event:
    id: int
    chat_id: int
    created_by: int
    title: str
    description: str | None
    kind: str
    run_time: str
    once_date: str | None
    weekday: int | None
    month_day: int | None
    next_run_at: int | None
    is_active: bool
    created_at: int
    created_by_name: str | None = None


@dataclass
class HistoryItem:
    id: int
    chat_id: int
    event_id: int | None
    occurrence_id: int | None
    title: str
    kind: str
    created_by: int
    created_by_name: str | None
    sent_at: int


@dataclass
class Occurrence:
    id: int
    event_id: int
    chat_id: int
    message_id: int | None
    sent_at: int
    is_completed: bool
    is_not_completed: bool


@dataclass
class Reminder:
    id: int
    occurrence_id: int
    remind_at: int
    sent: bool
