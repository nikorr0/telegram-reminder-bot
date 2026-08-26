from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, time, timedelta

from bot.config import TZ
from bot.i18n import t, t_tuple


def now_ts() -> int:
    return int(datetime.now(TZ).timestamp())


def ts_to_local(ts: int) -> datetime:
    return datetime.fromtimestamp(ts, TZ)


def format_dt(ts: int) -> str:
    return ts_to_local(ts).strftime("%d.%m.%Y %H:%M")


def parse_time(text: str) -> time | None:
    raw = text.strip()
    parts = raw.split(":")
    if len(parts) != 2:
        return None
    try:
        hour = int(parts[0])
        minute = int(parts[1])
    except ValueError:
        return None
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None
    return time(hour, minute)


def parse_date(text: str) -> date | None:
    raw = text.strip()
    for fmt in ("%d.%m.%Y", "%d.%m.%y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _combine_local(day: date, run_time: time) -> datetime:
    return datetime.combine(day, run_time, tzinfo=TZ)


def _month_day_date(year: int, month: int, month_day: int) -> date:
    last = monthrange(year, month)[1]
    return date(year, month, min(month_day, last))


def _add_month(day: date) -> date:
    if day.month == 12:
        return date(day.year + 1, 1, 1)
    return date(day.year, day.month + 1, 1)


def compute_next_run(
    kind: str,
    run_time_str: str,
    *,
    once_date: str | None = None,
    weekday: int | None = None,
    month_day: int | None = None,
    after: datetime | None = None,
) -> datetime | None:
    after = after or datetime.now(TZ)
    hour, minute = map(int, run_time_str.split(":"))
    run_time = time(hour, minute)

    if kind == "once":
        if not once_date:
            return None
        dt = _combine_local(date.fromisoformat(once_date), run_time)
        if dt <= after:
            return None
        return dt

    if kind == "daily":
        dt = _combine_local(after.date(), run_time)
        if dt <= after:
            dt = _combine_local(after.date() + timedelta(days=1), run_time)
        return dt

    if kind == "weekly":
        if weekday is None:
            return None
        days_ahead = (weekday - after.weekday()) % 7
        dt = _combine_local(after.date() + timedelta(days=days_ahead), run_time)
        if dt <= after:
            dt = _combine_local(after.date() + timedelta(days=days_ahead + 7), run_time)
        return dt

    if kind == "monthly":
        if month_day is None:
            return None
        candidate_day = _month_day_date(after.year, after.month, month_day)
        dt = _combine_local(candidate_day, run_time)
        if dt <= after:
            nxt = _add_month(candidate_day)
            candidate_day = _month_day_date(nxt.year, nxt.month, month_day)
            dt = _combine_local(candidate_day, run_time)
        return dt

    return None


def schedule_label(
    kind: str,
    run_time: str,
    *,
    once_date: str | None = None,
    weekday: int | None = None,
    month_day: int | None = None,
    lang: str | None = None,
) -> str:
    if kind == "once":
        day = date.fromisoformat(once_date) if once_date else None
        day_s = day.strftime("%d.%m.%Y") if day else "?"
        return t(lang, "schedule_once", date=day_s, time=run_time)
    if kind == "daily":
        return t(lang, "schedule_daily", time=run_time)
    if kind == "weekly" and weekday is not None:
        names = t_tuple(lang, "weekday_acc")
        return t(lang, "schedule_weekly", weekday=names[weekday], time=run_time)
    if kind == "monthly" and month_day is not None:
        return t(lang, "schedule_monthly", day=month_day, time=run_time)
    return t(lang, "schedule_time", time=run_time)
