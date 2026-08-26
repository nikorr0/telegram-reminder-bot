from __future__ import annotations

from aiogram.types import ForceReply, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.i18n import t, t_tuple
from bot.models import Event


def force_reply(placeholder: str, message: Message) -> ForceReply:
    return ForceReply(
        selective=message.chat.type != "private",
        input_field_placeholder=placeholder,
    )


def skip_description_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "btn_skip"), callback_data="add:skip_desc")]
        ]
    )


def kind_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t(lang, "btn_once"), callback_data="add:kind:once"),
                InlineKeyboardButton(text=t(lang, "btn_daily"), callback_data="add:kind:daily"),
            ],
            [
                InlineKeyboardButton(text=t(lang, "btn_weekly"), callback_data="add:kind:weekly"),
                InlineKeyboardButton(text=t(lang, "btn_monthly"), callback_data="add:kind:monthly"),
            ],
        ]
    )


def once_date_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t(lang, "btn_today"), callback_data="add:date:today"),
                InlineKeyboardButton(text=t(lang, "btn_tomorrow"), callback_data="add:date:tomorrow"),
            ],
            [InlineKeyboardButton(text=t(lang, "btn_custom_date"), callback_data="add:date:custom")],
        ]
    )


def weekday_kb(lang: str) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text=name, callback_data=f"add:wd:{i}")
        for i, name in enumerate(t_tuple(lang, "weekday_short"))
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons[:4], buttons[4:]])


def confirm_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t(lang, "btn_create"), callback_data="add:ok"),
                InlineKeyboardButton(text=t(lang, "btn_abort"), callback_data="add:abort"),
            ]
        ]
    )


def language_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Русский", callback_data="lang:ru"),
                InlineKeyboardButton(text="English", callback_data="lang:en"),
            ]
        ]
    )


def event_action_kb(
    occ_id: int,
    lang: str,
    *,
    is_completed: bool = False,
    is_not_completed: bool = False,
) -> InlineKeyboardMarkup:
    row: list[InlineKeyboardButton] = []
    if not is_completed:
        row.append(InlineKeyboardButton(text=t(lang, "btn_done"), callback_data=f"d:{occ_id}"))
    row.append(InlineKeyboardButton(text=t(lang, "btn_later"), callback_data=f"l:{occ_id}"))
    if not is_not_completed:
        row.append(
            InlineKeyboardButton(text=t(lang, "btn_not_done"), callback_data=f"n:{occ_id}")
        )
    return InlineKeyboardMarkup(inline_keyboard=[row])


def snooze_kb(occ_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t(lang, "btn_15m"), callback_data=f"s:15:{occ_id}"),
                InlineKeyboardButton(text=t(lang, "btn_1h"), callback_data=f"s:60:{occ_id}"),
            ],
            [
                InlineKeyboardButton(text=t(lang, "btn_3h"), callback_data=f"s:180:{occ_id}"),
                InlineKeyboardButton(text=t(lang, "btn_tomorrow_short"), callback_data=f"s:tmr:{occ_id}"),
            ],
            [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data=f"b:{occ_id}")],
        ]
    )


def list_events_kb(events: list[Event], lang: str) -> InlineKeyboardMarkup | None:
    if not events:
        return None
    rows = []
    for i, event in enumerate(events, start=1):
        if event.is_active:
            toggle = InlineKeyboardButton(
                text=t(lang, "btn_off", n=i), callback_data=f"off:{event.id}"
            )
        else:
            toggle = InlineKeyboardButton(
                text=t(lang, "btn_on", n=i), callback_data=f"on:{event.id}"
            )
        rows.append(
            [
                toggle,
                InlineKeyboardButton(
                    text=t(lang, "btn_delete", n=i), callback_data=f"del:{event.id}"
                ),
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def history_kb(page: int, pages: int, lang: str) -> InlineKeyboardMarkup | None:
    if pages <= 1:
        return None
    row: list[InlineKeyboardButton] = []
    if page > 0:
        row.append(InlineKeyboardButton(text="‹", callback_data=f"h:{page - 1}"))
    row.append(
        InlineKeyboardButton(
            text=t(lang, "history_page", page=page + 1, pages=pages),
            callback_data="h:nop",
        )
    )
    if page + 1 < pages:
        row.append(InlineKeyboardButton(text="›", callback_data=f"h:{page + 1}"))
    return InlineKeyboardMarkup(inline_keyboard=[row])
