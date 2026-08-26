from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, InlineKeyboardMarkup

from bot.i18n import t
from bot.keyboards import event_action_kb, history_kb, list_events_kb, snooze_kb
from bot.models import Event
from bot.services.events import (
    HISTORY_PAGE_SIZE,
    add_reminder,
    apply_status_suffix,
    activate_event,
    deactivate_event,
    delete_event,
    format_event_list,
    format_history_text,
    get_event,
    get_occurrence,
    list_chat_events,
    list_history,
    set_completed,
    set_not_completed,
    snooze_timestamp,
)
from bot.services.schedule import format_dt as format_ts

router = Router()

SNOOZE_KEYS = {
    "15": "snooze_15",
    "60": "snooze_60",
    "180": "snooze_180",
    "tmr": "snooze_tmr",
}


async def can_manage(bot: Bot, event: Event, user_id: int) -> bool:
    if event.created_by == user_id:
        return True
    try:
        member = await bot.get_chat_member(event.chat_id, user_id)
    except TelegramBadRequest:
        return False
    return member.status in {"creator", "administrator"}


def _occ_markup(occ, lang: str) -> InlineKeyboardMarkup:
    return event_action_kb(
        occ.id,
        lang,
        is_completed=occ.is_completed,
        is_not_completed=occ.is_not_completed,
    )


async def _apply_occurrence_view(callback: CallbackQuery, occ, lang: str) -> None:
    message = callback.message
    if message is None or not hasattr(message, "edit_text"):
        return
    current = getattr(message, "html_text", None) or getattr(message, "text", None) or ""
    new_text = apply_status_suffix(
        current,
        lang,
        is_completed=occ.is_completed,
        is_not_completed=occ.is_not_completed,
    )
    markup = _occ_markup(occ, lang)
    try:
        await message.edit_text(new_text, reply_markup=markup)
    except TelegramBadRequest:
        try:
            await message.edit_reply_markup(reply_markup=markup)
        except TelegramBadRequest:
            pass


def _suffix_id(data: str | None, prefix: str) -> int | None:
    if not data or not data.startswith(prefix):
        return None
    raw = data[len(prefix) :]
    if not raw.isdigit():
        return None
    return int(raw)


class IdCallback(BaseFilter):
    def __init__(self, prefix: str) -> None:
        self.prefix = prefix

    async def __call__(self, callback: CallbackQuery) -> bool:
        return _suffix_id(callback.data, self.prefix) is not None


@router.callback_query(IdCallback("d:"))
async def cb_done(callback: CallbackQuery, lang: str) -> None:
    occ_id = _suffix_id(callback.data, "d:")
    if occ_id is None:
        await callback.answer()
        return
    occ = await get_occurrence(occ_id)
    if occ is None:
        await callback.answer(t(lang, "occ_gone"), show_alert=True)
        return
    if occ.is_completed:
        await callback.answer()
        return
    occ = await set_completed(occ_id)
    if occ is None:
        await callback.answer(t(lang, "occ_gone"), show_alert=True)
        return
    await _apply_occurrence_view(callback, occ, lang)
    await callback.answer(t(lang, "marked_done"))


@router.callback_query(IdCallback("n:"))
async def cb_not_done(callback: CallbackQuery, lang: str) -> None:
    occ_id = _suffix_id(callback.data, "n:")
    if occ_id is None:
        await callback.answer()
        return
    occ = await get_occurrence(occ_id)
    if occ is None:
        await callback.answer(t(lang, "occ_gone"), show_alert=True)
        return
    if occ.is_not_completed:
        await callback.answer()
        return
    occ = await set_not_completed(occ_id)
    if occ is None:
        await callback.answer(t(lang, "occ_gone"), show_alert=True)
        return
    await _apply_occurrence_view(callback, occ, lang)
    await callback.answer(t(lang, "marked_not_done"))


@router.callback_query(IdCallback("l:"))
async def cb_later(callback: CallbackQuery, lang: str) -> None:
    occ_id = _suffix_id(callback.data, "l:")
    if occ_id is None:
        await callback.answer()
        return
    occ = await get_occurrence(occ_id)
    if occ is None:
        await callback.answer(t(lang, "occ_gone"), show_alert=True)
        return
    try:
        await callback.message.edit_reply_markup(reply_markup=snooze_kb(occ_id, lang))
    except TelegramBadRequest:
        pass
    await callback.answer()


@router.callback_query(IdCallback("b:"))
async def cb_later_back(callback: CallbackQuery, lang: str) -> None:
    occ_id = _suffix_id(callback.data, "b:")
    if occ_id is None:
        await callback.answer()
        return
    occ = await get_occurrence(occ_id)
    if occ is None:
        await callback.answer(t(lang, "occ_gone"), show_alert=True)
        return
    try:
        await callback.message.edit_reply_markup(reply_markup=_occ_markup(occ, lang))
    except TelegramBadRequest:
        pass
    await callback.answer()


@router.callback_query(F.data.startswith("s:"))
async def cb_snooze(callback: CallbackQuery, lang: str) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) != 3 or parts[1] not in SNOOZE_KEYS or not parts[2].isdigit():
        await callback.answer()
        return
    code = parts[1]
    occ_id = int(parts[2])
    occ = await get_occurrence(occ_id)
    if occ is None:
        await callback.answer(t(lang, "occ_gone"), show_alert=True)
        return
    remind_at = snooze_timestamp(code)
    await add_reminder(occ_id, remind_at)
    try:
        await callback.message.edit_reply_markup(reply_markup=_occ_markup(occ, lang))
    except TelegramBadRequest:
        pass
    when = t(lang, SNOOZE_KEYS[code])
    await callback.answer(t(lang, "snooze_toast", when=when))
    await callback.message.answer(
        t(lang, "snooze_chat", when=when, at=format_ts(remind_at))
    )


async def _refresh_list(callback: CallbackQuery, lang: str) -> None:
    events = await list_chat_events(callback.message.chat.id)
    extra = ""
    if len(events) > 40:
        extra = t(lang, "list_truncated", total=len(events))
        events = events[:40]
    try:
        await callback.message.edit_text(
            format_event_list(events, lang) + extra,
            reply_markup=list_events_kb(events, lang),
        )
    except TelegramBadRequest:
        pass


@router.callback_query(IdCallback("off:"))
async def cb_off(callback: CallbackQuery, bot: Bot, lang: str) -> None:
    event_id = _suffix_id(callback.data, "off:")
    if event_id is None:
        await callback.answer()
        return
    event = await get_event(event_id)
    if event is None or event.chat_id != callback.message.chat.id:
        await callback.answer(t(lang, "not_found"), show_alert=True)
        return
    if not await can_manage(bot, event, callback.from_user.id):
        await callback.answer(t(lang, "off_denied"), show_alert=True)
        return
    if not event.is_active:
        await callback.answer(t(lang, "already_off"))
        await _refresh_list(callback, lang)
        return
    await deactivate_event(event_id)
    await callback.answer(t(lang, "turned_off"))
    await _refresh_list(callback, lang)


@router.callback_query(IdCallback("on:"))
async def cb_on(callback: CallbackQuery, bot: Bot, lang: str) -> None:
    event_id = _suffix_id(callback.data, "on:")
    if event_id is None:
        await callback.answer()
        return
    event = await get_event(event_id)
    if event is None or event.chat_id != callback.message.chat.id:
        await callback.answer(t(lang, "not_found"), show_alert=True)
        return
    if not await can_manage(bot, event, callback.from_user.id):
        await callback.answer(t(lang, "on_denied"), show_alert=True)
        return
    if event.is_active:
        await callback.answer(t(lang, "already_on"))
        await _refresh_list(callback, lang)
        return
    enabled = await activate_event(event_id)
    if enabled is None:
        await callback.answer(t(lang, "cannot_enable"), show_alert=True)
        return
    await callback.answer(t(lang, "turned_on"))
    await _refresh_list(callback, lang)


@router.callback_query(IdCallback("del:"))
async def cb_del(callback: CallbackQuery, bot: Bot, lang: str) -> None:
    event_id = _suffix_id(callback.data, "del:")
    if event_id is None:
        await callback.answer()
        return
    event = await get_event(event_id)
    if event is None or event.chat_id != callback.message.chat.id:
        await callback.answer(t(lang, "not_found"), show_alert=True)
        return
    if not await can_manage(bot, event, callback.from_user.id):
        await callback.answer(t(lang, "del_denied"), show_alert=True)
        return
    await delete_event(event_id)
    await callback.answer(t(lang, "deleted"))
    await _refresh_list(callback, lang)


@router.callback_query(F.data.startswith("h:"))
async def cb_history(callback: CallbackQuery, lang: str) -> None:
    raw = (callback.data or "")[2:]
    if raw == "nop" or not raw.isdigit():
        await callback.answer()
        return
    page = int(raw)
    show_author = callback.message.chat.type != "private"
    items, total = await list_history(callback.message.chat.id, page=page)
    pages = max(1, (total + HISTORY_PAGE_SIZE - 1) // HISTORY_PAGE_SIZE) if total else 1
    clamped = min(page, pages - 1)
    if clamped != page:
        items, total = await list_history(callback.message.chat.id, page=clamped)
        page = clamped
    try:
        await callback.message.edit_text(
            format_history_text(
                items,
                lang,
                show_author=show_author,
                page=page,
                total=total,
            ),
            reply_markup=history_kb(page, pages, lang),
        )
    except TelegramBadRequest:
        pass
    await callback.answer()
