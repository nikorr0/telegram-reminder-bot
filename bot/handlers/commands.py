from __future__ import annotations

import html
from datetime import datetime, timedelta

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.config import DESCRIPTION_MAX_LEN, TITLE_MAX_LEN, TZ
from bot.i18n import SKIP_DESCRIPTION, normalize_lang, t
from bot.keyboards import (
    confirm_kb,
    force_reply,
    history_kb,
    kind_kb,
    language_kb,
    list_events_kb,
    once_date_kb,
    skip_description_kb,
    weekday_kb,
)
from bot.services.chats import set_chat_lang
from bot.services.events import (
    HISTORY_PAGE_SIZE,
    create_event,
    format_event_list,
    format_history_text,
    list_chat_events,
    list_history,
)
from bot.services.schedule import compute_next_run, format_dt, parse_date, parse_time, schedule_label

router = Router()


class AddEvent(StatesGroup):
    title = State()
    description = State()
    kind = State()
    once_date = State()
    weekday = State()
    month_day = State()
    run_time = State()
    confirm = State()


def _user_label(user) -> str | None:
    if user is None:
        return None
    if user.username:
        return f"@{user.username}"
    return user.full_name


def _is_command(text: str | None) -> bool:
    return bool(text) and text.startswith("/")


def _parse_lang_arg(raw: str) -> str | None:
    value = raw.strip().lower()
    aliases = {
        "ru": "ru",
        "rus": "ru",
        "russian": "ru",
        "русский": "ru",
        "рус": "ru",
        "en": "en",
        "eng": "en",
        "english": "en",
        "английский": "en",
    }
    return aliases.get(value)


async def _can_change_lang(bot: Bot, message: Message) -> bool:
    if message.chat.type == "private":
        return True
    if message.from_user is None:
        return False
    try:
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    except TelegramBadRequest:
        return False
    return member.status in {"creator", "administrator"}


async def _ask_title(message: Message, state: FSMContext, lang: str) -> None:
    await state.set_state(AddEvent.title)
    await message.answer(
        t(lang, "ask_title"),
        reply_markup=force_reply(t(lang, "ph_title"), message),
    )


async def _ask_description(message: Message, lang: str) -> None:
    await message.answer(t(lang, "ask_description"), reply_markup=skip_description_kb(lang))
    if message.chat.type != "private":
        await message.answer(
            t(lang, "ask_description_group"),
            reply_markup=force_reply(t(lang, "ph_description"), message),
        )


async def _ask_kind(message: Message, state: FSMContext, lang: str) -> None:
    await state.set_state(AddEvent.kind)
    await message.answer(t(lang, "ask_kind"), reply_markup=kind_kb(lang))


async def _ask_time(message: Message, state: FSMContext, lang: str) -> None:
    await state.set_state(AddEvent.run_time)
    await message.answer(
        t(lang, "ask_time"),
        reply_markup=force_reply(t(lang, "ph_time"), message),
    )


async def _preview_text(data: dict, lang: str) -> str | None:
    kind = data["kind"]
    run_time = data["run_time"]
    once_date = data.get("once_date")
    weekday = data.get("weekday")
    month_day = data.get("month_day")
    nxt = compute_next_run(
        kind,
        run_time,
        once_date=once_date,
        weekday=weekday,
        month_day=month_day,
    )
    if nxt is None:
        return None
    when = schedule_label(
        kind,
        run_time,
        once_date=once_date,
        weekday=weekday,
        month_day=month_day,
        lang=lang,
    )
    description = data.get("description")
    desc_line = html.escape(description) if description else t(lang, "no_description")
    return t(
        lang,
        "preview",
        title=html.escape(data["title"]),
        description=desc_line,
        when=when,
        next_run=nxt.strftime("%d.%m.%Y %H:%M"),
    )


async def _ask_confirm(message: Message, state: FSMContext, lang: str) -> None:
    data = await state.get_data()
    text = await _preview_text(data, lang)
    if text is None:
        await message.answer(t(lang, "time_passed"))
        await _ask_time(message, state, lang)
        return
    await state.set_state(AddEvent.confirm)
    await message.answer(text, reply_markup=confirm_kb(lang))


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext, lang: str) -> None:
    current = await state.get_state()
    await state.clear()
    if current is None:
        await message.answer(t(lang, "nothing_to_cancel"))
        return
    await message.answer(t(lang, "cancelled"))


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, lang: str) -> None:
    await state.clear()
    await message.answer(f"{t(lang, 'start')}\n\n{t(lang, 'help')}")


@router.message(Command("help"))
async def cmd_help(message: Message, lang: str) -> None:
    await message.answer(t(lang, "help"))


@router.message(Command("lang", "language"))
async def cmd_lang(message: Message, bot: Bot, lang: str) -> None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) > 1:
        chosen = _parse_lang_arg(parts[1])
        if chosen is None:
            await message.answer(
                t(lang, "lang_choose", current=t(lang, "lang_name")),
                reply_markup=language_kb(),
            )
            return
        if not await _can_change_lang(bot, message):
            await message.answer(t(lang, "lang_denied"))
            return
        await set_chat_lang(message.chat.id, chosen)
        await message.answer(t(chosen, "lang_set"))
        return
    await message.answer(
        t(lang, "lang_choose", current=t(lang, "lang_name")),
        reply_markup=language_kb(),
    )


@router.callback_query(F.data.in_({"lang:ru", "lang:en"}))
async def cb_lang(callback: CallbackQuery, bot: Bot, lang: str) -> None:
    chosen = normalize_lang(callback.data.split(":")[-1])
    chat = callback.message.chat if callback.message else None
    if chat is None or callback.from_user is None:
        await callback.answer()
        return
    if chat.type != "private":
        try:
            member = await bot.get_chat_member(chat.id, callback.from_user.id)
        except TelegramBadRequest:
            await callback.answer(t(lang, "lang_denied"), show_alert=True)
            return
        if member.status not in {"creator", "administrator"}:
            await callback.answer(t(lang, "lang_denied"), show_alert=True)
            return
    await set_chat_lang(chat.id, chosen)
    await callback.answer()
    try:
        await callback.message.edit_text(t(chosen, "lang_set"), reply_markup=None)
    except TelegramBadRequest:
        await callback.message.answer(t(chosen, "lang_set"))


@router.message(Command("add"))
async def cmd_add(message: Message, state: FSMContext, lang: str) -> None:
    if message.from_user is None:
        await message.answer(t(lang, "unknown_user"))
        return
    await state.clear()
    await state.update_data(
        chat_id=message.chat.id,
        created_by=message.from_user.id,
        created_by_name=_user_label(message.from_user),
    )
    await _ask_title(message, state, lang)


@router.message(Command("list"))
async def cmd_list(message: Message, lang: str) -> None:
    events = await list_chat_events(message.chat.id)
    extra = ""
    if len(events) > 40:
        extra = t(lang, "list_truncated", total=len(events))
        events = events[:40]
    await message.answer(
        format_event_list(events, lang) + extra,
        reply_markup=list_events_kb(events, lang),
    )


@router.message(Command("history"))
async def cmd_history(message: Message, lang: str) -> None:
    show_author = message.chat.type != "private"
    items, total = await list_history(message.chat.id, page=0)
    pages = max(1, (total + HISTORY_PAGE_SIZE - 1) // HISTORY_PAGE_SIZE) if total else 1
    await message.answer(
        format_history_text(
            items,
            lang,
            show_author=show_author,
            page=0,
            total=total,
        ),
        reply_markup=history_kb(0, pages, lang),
    )


@router.message(AddEvent.title, F.text)
async def add_title(message: Message, state: FSMContext, lang: str) -> None:
    if _is_command(message.text):
        return
    title = (message.text or "").strip()
    if not title:
        await message.answer(t(lang, "title_empty"))
        return
    if len(title) > TITLE_MAX_LEN:
        await message.answer(t(lang, "title_too_long", max=TITLE_MAX_LEN))
        return
    await state.update_data(title=title)
    await state.set_state(AddEvent.description)
    await _ask_description(message, lang)


@router.message(AddEvent.description, F.text)
async def add_description(message: Message, state: FSMContext, lang: str) -> None:
    if _is_command(message.text):
        return
    raw = (message.text or "").strip()
    description = None if raw.lower() in SKIP_DESCRIPTION else raw
    if description and len(description) > DESCRIPTION_MAX_LEN:
        await message.answer(t(lang, "desc_too_long", max=DESCRIPTION_MAX_LEN))
        return
    await state.update_data(description=description)
    await _ask_kind(message, state, lang)


@router.callback_query(AddEvent.description, F.data == "add:skip_desc")
async def add_skip_description(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.update_data(description=None)
    await callback.answer()
    await callback.message.answer(t(lang, "desc_skipped"))
    await _ask_kind(callback.message, state, lang)


@router.callback_query(AddEvent.kind, F.data.startswith("add:kind:"))
async def add_kind(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    kind = callback.data.split(":")[-1]
    await state.update_data(kind=kind)
    await callback.answer()
    if kind == "once":
        await state.set_state(AddEvent.once_date)
        await callback.message.answer(t(lang, "choose_date"), reply_markup=once_date_kb(lang))
    elif kind == "weekly":
        await state.set_state(AddEvent.weekday)
        await callback.message.answer(t(lang, "choose_weekday"), reply_markup=weekday_kb(lang))
    elif kind == "monthly":
        await state.set_state(AddEvent.month_day)
        await callback.message.answer(
            t(lang, "ask_month_day"),
            reply_markup=force_reply(t(lang, "ph_month_day"), callback.message),
        )
    else:
        await _ask_time(callback.message, state, lang)


@router.callback_query(AddEvent.once_date, F.data.startswith("add:date:"))
async def add_once_date(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    choice = callback.data.split(":")[-1]
    await callback.answer()
    today = datetime.now(TZ).date()
    if choice == "today":
        await state.update_data(once_date=today.isoformat())
        await _ask_time(callback.message, state, lang)
    elif choice == "tomorrow":
        await state.update_data(once_date=(today + timedelta(days=1)).isoformat())
        await _ask_time(callback.message, state, lang)
    else:
        await callback.message.answer(
            t(lang, "ask_custom_date"),
            reply_markup=force_reply(t(lang, "ph_date"), callback.message),
        )


@router.message(AddEvent.once_date, F.text)
async def add_once_date_text(message: Message, state: FSMContext, lang: str) -> None:
    if _is_command(message.text):
        return
    parsed = parse_date(message.text or "")
    if parsed is None:
        await message.answer(t(lang, "bad_date"))
        return
    if parsed < datetime.now(TZ).date():
        await message.answer(t(lang, "date_passed"))
        return
    await state.update_data(once_date=parsed.isoformat())
    await _ask_time(message, state, lang)


@router.callback_query(AddEvent.weekday, F.data.startswith("add:wd:"))
async def add_weekday(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    weekday = int(callback.data.split(":")[-1])
    await state.update_data(weekday=weekday)
    await callback.answer()
    await _ask_time(callback.message, state, lang)


@router.message(AddEvent.month_day, F.text)
async def add_month_day(message: Message, state: FSMContext, lang: str) -> None:
    if _is_command(message.text):
        return
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer(t(lang, "bad_month_day"))
        return
    day = int(raw)
    if not 1 <= day <= 31:
        await message.answer(t(lang, "bad_month_day"))
        return
    await state.update_data(month_day=day)
    await _ask_time(message, state, lang)


@router.message(AddEvent.run_time, F.text)
async def add_run_time(message: Message, state: FSMContext, lang: str) -> None:
    if _is_command(message.text):
        return
    parsed = parse_time(message.text or "")
    if parsed is None:
        await message.answer(t(lang, "bad_time"))
        return
    await state.update_data(run_time=parsed.strftime("%H:%M"))
    await _ask_confirm(message, state, lang)


@router.callback_query(AddEvent.confirm, F.data == "add:abort")
async def add_abort(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.clear()
    await callback.answer()
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass
    await callback.message.answer(t(lang, "aborted"))


@router.callback_query(AddEvent.confirm, F.data == "add:ok")
async def add_ok(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    data = await state.get_data()
    if data.get("submitted"):
        await callback.answer()
        return
    preview = await _preview_text(data, lang)
    if preview is None:
        await callback.answer(t(lang, "time_passed_alert"), show_alert=True)
        await _ask_time(callback.message, state, lang)
        return
    await state.update_data(submitted=True)
    chat_id = data.get("chat_id") or callback.message.chat.id
    created_by = data.get("created_by") or callback.from_user.id
    created_by_name = data.get("created_by_name") or _user_label(callback.from_user)
    event = await create_event(
        chat_id=chat_id,
        created_by=created_by,
        created_by_name=created_by_name,
        title=data["title"],
        description=data.get("description"),
        kind=data["kind"],
        run_time=data["run_time"],
        once_date=data.get("once_date"),
        weekday=data.get("weekday"),
        month_day=data.get("month_day"),
    )
    await state.clear()
    await callback.answer()
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass
    when = schedule_label(
        event.kind,
        event.run_time,
        once_date=event.once_date,
        weekday=event.weekday,
        month_day=event.month_day,
        lang=lang,
    )
    next_line = (
        t(lang, "next_line", when=format_dt(event.next_run_at)) if event.next_run_at else ""
    )
    await callback.message.answer(
        t(lang, "event_added", title=html.escape(event.title), when=when, next_line=next_line)
    )


@router.message(StateFilter(AddEvent), F.text)
async def add_unexpected_text(message: Message, lang: str) -> None:
    if _is_command(message.text):
        return
    await message.answer(t(lang, "need_button"))


@router.message(StateFilter(AddEvent))
async def add_unexpected_any(message: Message, lang: str) -> None:
    await message.answer(t(lang, "need_text_or_button"))


@router.callback_query(F.data.startswith("add:"))
async def add_stale_callback(callback: CallbackQuery, lang: str) -> None:
    await callback.answer(t(lang, "stale_step"), show_alert=True)
