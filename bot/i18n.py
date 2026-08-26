from __future__ import annotations

from typing import Any, Literal

Lang = Literal["ru", "en"]
DEFAULT_LANG = "ru"
SUPPORTED = ("ru", "en")

SKIP_DESCRIPTION = frozenset(
    {
        "-",
        "—",
        "пропустить",
        "skip",
        "none",
    }
)

TEXTS: dict[str, dict[str, Any]] = {
    "ru": {
        "start": "Привет! Я бот очереди событий.",
        "help": (
            "Я ставлю события в очередь и напоминаю о них в этом чате.\n\n"
            "<b>Команды</b>\n"
            "/add — создать разовое или повторяющееся событие\n"
            "/list — список событий этого чата\n"
            "/history — история прошедших задач\n"
            "/lang — язык бота (русский / English)\n"
            "/cancel — отменить текущий ввод\n"
            "/help — эта справка\n\n"
            "У события есть название и необязательное описание. "
            "Когда придёт напоминание, можно отметить «Выполнено» или «Невыполнено», "
            "либо попросить напомнить позже.\n\n"
            "Создать событие может любой участник чата. "
            "Выключить, включить или удалить — автор события или администратор.\n\n"
            "Бота можно добавить в группу: события будут приходить в тот чат, где их создали."
        ),
        "cmd_start": "Начало работы",
        "cmd_help": "Справка",
        "cmd_add": "Добавить событие",
        "cmd_list": "Список событий",
        "cmd_history": "История задач",
        "cmd_lang": "Язык бота",
        "cmd_cancel": "Отменить ввод",
        "ask_title": "Введите название события.",
        "ph_title": "Название",
        "ask_description": "Введите описание или нажмите «Пропустить».",
        "ask_description_group": "Если пишете текстом — ответьте на это сообщение (или отправьте «-»).",
        "ph_description": "Описание",
        "ask_kind": "Как повторять событие?",
        "ask_time": "Введите время в формате ЧЧ:ММ, например 09:30.",
        "ph_time": "ЧЧ:ММ",
        "no_description": "<i>без описания</i>",
        "preview": (
            "Проверьте событие:\n\n"
            "<b>{title}</b>\n"
            "{description}\n\n"
            "{when}\n"
            "ближайший запуск: {next_run}"
        ),
        "time_passed": "Это время уже прошло. Укажите будущее время.",
        "nothing_to_cancel": "Сейчас нечего отменять.",
        "cancelled": "Ввод отменён.",
        "unknown_user": "Не удалось определить пользователя.",
        "list_truncated": "\n\nПоказаны первые 40 из {total}.",
        "title_empty": "Название не может быть пустым. Введите название.",
        "title_too_long": "Слишком длинное название (макс. {max} символов).",
        "desc_too_long": "Слишком длинное описание (макс. {max} символов).",
        "desc_skipped": "Описание пропущено.",
        "choose_date": "Выберите дату:",
        "choose_weekday": "Выберите день недели:",
        "ask_month_day": "Введите число месяца (1–31).",
        "ph_month_day": "Число 1–31",
        "ask_custom_date": "Введите дату в формате ДД.ММ.ГГГГ, например 26.08.2026.",
        "ph_date": "ДД.ММ.ГГГГ",
        "bad_date": "Не понял дату. Пример: 26.08.2026",
        "date_passed": "Дата уже прошла. Укажите сегодня или будущий день.",
        "bad_month_day": "Введите число от 1 до 31.",
        "bad_time": "Не понял время. Пример: 09:30",
        "aborted": "Создание события отменено.",
        "time_passed_alert": "Время уже прошло, укажите другое.",
        "event_added": "Событие добавлено в очередь.\n<b>{title}</b>\n{when}{next_line}",
        "next_line": "\nближайший запуск: {when}",
        "need_button": "Сейчас нужен выбор кнопкой или /cancel для выхода.",
        "need_text_or_button": "Отправьте текст или нажмите кнопку. /cancel — выход.",
        "stale_step": "Этот шаг уже неактуален. Начните с /add",
        "btn_skip": "Пропустить",
        "btn_once": "Разовое",
        "btn_daily": "Каждый день",
        "btn_weekly": "Каждую неделю",
        "btn_monthly": "Каждый месяц",
        "btn_today": "Сегодня",
        "btn_tomorrow": "Завтра",
        "btn_custom_date": "Ввести дату",
        "btn_create": "Создать",
        "btn_abort": "Отмена",
        "btn_done": "Выполнено",
        "btn_later": "Напомнить позже",
        "btn_not_done": "Невыполнено",
        "btn_15m": "15 мин",
        "btn_1h": "1 час",
        "btn_3h": "3 часа",
        "btn_tomorrow_short": "Завтра",
        "btn_back": "Назад",
        "btn_off": "Выкл. {n}",
        "btn_on": "Вкл. {n}",
        "btn_delete": "Удалить {n}",
        "weekday_short": ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"),
        "weekday_acc": (
            "понедельник",
            "вторник",
            "среду",
            "четверг",
            "пятницу",
            "субботу",
            "воскресенье",
        ),
        "schedule_once": "разово, {date} в {time}",
        "schedule_daily": "каждый день в {time}",
        "schedule_weekly": "каждый {weekday} в {time}",
        "schedule_monthly": "каждое {day}-е число в {time}",
        "schedule_time": "в {time}",
        "status_done": "Выполнено ✅",
        "status_not_done": "Невыполнено ❌",
        "reminder_prefix": "🔔 Напоминание\n\n",
        "next_label": "\nследующее: {when}",
        "paused": "\n⏸ выключено",
        "list_empty": "Нет событий в этом чате.\nСоздайте новое командой /add",
        "list_header": "📋 <b>События этого чата</b>\n\n{body}",
        "snooze_15": "через 15 минут",
        "snooze_60": "через 1 час",
        "snooze_180": "через 3 часа",
        "snooze_tmr": "завтра в 09:00",
        "occ_gone": "Событие уже недоступно.",
        "marked_done": "Отмечено как выполненное",
        "marked_not_done": "Отмечено как невыполненное",
        "snooze_toast": "Напомню {when}",
        "snooze_chat": "Напоминание поставлено {when} ({at}).",
        "not_found": "Событие не найдено.",
        "off_denied": "Выключить может автор или администратор.",
        "already_off": "Событие уже выключено",
        "turned_off": "Событие выключено — отправка остановлена",
        "on_denied": "Включить может автор или администратор.",
        "already_on": "Событие уже включено",
        "cannot_enable": "Нельзя включить: ближайшее время уже прошло.",
        "turned_on": "Событие включено",
        "del_denied": "Удалить может автор или администратор.",
        "deleted": "Событие удалено",
        "lang_choose": "Язык этого чата: <b>{current}</b>\nВыберите язык:",
        "lang_name": "русский",
        "lang_set": "Язык переключён на русский.",
        "lang_denied": "Язык чата может сменить только администратор.",
        "btn_lang_ru": "Русский",
        "btn_lang_en": "English",
        "history_empty": "Пока нет прошедших задач в этом чате.",
        "history_header": "📜 <b>История задач</b> · {page}/{pages}",
        "history_when": "{date}  {time}",
        "history_kind": "тип: {kind}",
        "history_kind_once": "разовое",
        "history_kind_repeat": "повторяющееся",
        "history_author": "поставил: {name}",
        "history_page": "{page}/{pages}",
    },
    "en": {
        "start": "Hi! I am an event queue bot.",
        "help": (
            "I queue events and remind this chat when they are due.\n\n"
            "<b>Commands</b>\n"
            "/add — create a one-time or repeating event\n"
            "/list — events in this chat\n"
            "/history — history of past tasks\n"
            "/lang — bot language (Russian / English)\n"
            "/cancel — cancel the current input\n"
            "/help — this help\n\n"
            "An event has a title and an optional description. "
            "When a reminder arrives, you can mark it Done or Not done, "
            "or snooze it.\n\n"
            "Anyone in the chat can create an event. "
            "Disable, enable, or delete — the author or a chat admin.\n\n"
            "Add the bot to a group to keep that chat’s events there."
        ),
        "cmd_start": "Get started",
        "cmd_help": "Help",
        "cmd_add": "Add an event",
        "cmd_list": "Event list",
        "cmd_history": "Task history",
        "cmd_lang": "Bot language",
        "cmd_cancel": "Cancel input",
        "ask_title": "Enter the event title.",
        "ph_title": "Title",
        "ask_description": "Enter a description or tap Skip.",
        "ask_description_group": "If you type a description, reply to this message (or send “-”).",
        "ph_description": "Description",
        "ask_kind": "How should this event repeat?",
        "ask_time": "Enter the time as HH:MM, for example 09:30.",
        "ph_time": "HH:MM",
        "no_description": "<i>no description</i>",
        "preview": (
            "Check the event:\n\n"
            "<b>{title}</b>\n"
            "{description}\n\n"
            "{when}\n"
            "next run: {next_run}"
        ),
        "time_passed": "That time has already passed. Enter a future time.",
        "nothing_to_cancel": "Nothing to cancel right now.",
        "cancelled": "Input cancelled.",
        "unknown_user": "Could not identify the user.",
        "list_truncated": "\n\nShowing the first 40 of {total}.",
        "title_empty": "Title cannot be empty. Enter a title.",
        "title_too_long": "Title is too long (max. {max} characters).",
        "desc_too_long": "Description is too long (max. {max} characters).",
        "desc_skipped": "Description skipped.",
        "choose_date": "Choose a date:",
        "choose_weekday": "Choose a weekday:",
        "ask_month_day": "Enter the day of the month (1–31).",
        "ph_month_day": "Day 1–31",
        "ask_custom_date": "Enter the date as DD.MM.YYYY, for example 26.08.2026.",
        "ph_date": "DD.MM.YYYY",
        "bad_date": "Could not parse the date. Example: 26.08.2026",
        "date_passed": "That date has already passed. Use today or a future day.",
        "bad_month_day": "Enter a number from 1 to 31.",
        "bad_time": "Could not parse the time. Example: 09:30",
        "aborted": "Event creation cancelled.",
        "time_passed_alert": "That time has already passed. Enter another one.",
        "event_added": "Event added to the queue.\n<b>{title}</b>\n{when}{next_line}",
        "next_line": "\nnext run: {when}",
        "need_button": "Please use a button, or /cancel to exit.",
        "need_text_or_button": "Send text or tap a button. /cancel to exit.",
        "stale_step": "This step is no longer valid. Start over with /add",
        "btn_skip": "Skip",
        "btn_once": "One-time",
        "btn_daily": "Every day",
        "btn_weekly": "Every week",
        "btn_monthly": "Every month",
        "btn_today": "Today",
        "btn_tomorrow": "Tomorrow",
        "btn_custom_date": "Enter a date",
        "btn_create": "Create",
        "btn_abort": "Cancel",
        "btn_done": "Done",
        "btn_later": "Remind later",
        "btn_not_done": "Not done",
        "btn_15m": "15 min",
        "btn_1h": "1 hour",
        "btn_3h": "3 hours",
        "btn_tomorrow_short": "Tomorrow",
        "btn_back": "Back",
        "btn_off": "Off {n}",
        "btn_on": "On {n}",
        "btn_delete": "Delete {n}",
        "weekday_short": ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"),
        "weekday_acc": (
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ),
        "schedule_once": "once, {date} at {time}",
        "schedule_daily": "every day at {time}",
        "schedule_weekly": "every {weekday} at {time}",
        "schedule_monthly": "on day {day} of each month at {time}",
        "schedule_time": "at {time}",
        "status_done": "Done ✅",
        "status_not_done": "Not done ❌",
        "reminder_prefix": "🔔 Reminder\n\n",
        "next_label": "\nnext: {when}",
        "paused": "\n⏸ disabled",
        "list_empty": "No events in this chat.\nCreate one with /add",
        "list_header": "📋 <b>Events in this chat</b>\n\n{body}",
        "snooze_15": "in 15 minutes",
        "snooze_60": "in 1 hour",
        "snooze_180": "in 3 hours",
        "snooze_tmr": "tomorrow at 09:00",
        "occ_gone": "This event is no longer available.",
        "marked_done": "Marked as done",
        "marked_not_done": "Marked as not done",
        "snooze_toast": "I will remind you {when}",
        "snooze_chat": "Reminder set {when} ({at}).",
        "not_found": "Event not found.",
        "off_denied": "Only the author or an admin can disable this.",
        "already_off": "Event is already disabled",
        "turned_off": "Event disabled — sending stopped",
        "on_denied": "Only the author or an admin can enable this.",
        "already_on": "Event is already enabled",
        "cannot_enable": "Cannot enable: the next time has already passed.",
        "turned_on": "Event enabled",
        "del_denied": "Only the author or an admin can delete this.",
        "deleted": "Event deleted",
        "lang_choose": "Language for this chat: <b>{current}</b>\nChoose a language:",
        "lang_name": "English",
        "lang_set": "Language switched to English.",
        "lang_denied": "Only an admin can change the chat language.",
        "btn_lang_ru": "Русский",
        "btn_lang_en": "English",
        "history_empty": "No past tasks in this chat yet.",
        "history_header": "📜 <b>Task history</b> · {page}/{pages}",
        "history_when": "📅 {date}  {time}",
        "history_kind": "type: {kind}",
        "history_kind_once": "one-time",
        "history_kind_repeat": "repeating",
        "history_author": "created by: {name}",
        "history_page": "{page}/{pages}",
    },
}


def normalize_lang(lang: str | None) -> str:
    if lang in SUPPORTED:
        return lang
    return DEFAULT_LANG


def lang_from_code(language_code: str | None) -> str:
    if language_code and language_code.lower().startswith("en"):
        return "en"
    return DEFAULT_LANG


def t(lang: str | None, key: str, **kwargs: Any) -> str:
    pack = TEXTS[normalize_lang(lang)]
    fallback = TEXTS[DEFAULT_LANG]
    text = pack.get(key, fallback[key])
    if not isinstance(text, str):
        raise TypeError(f"i18n key {key!r} is not a string")
    return text.format(**kwargs) if kwargs else text


def t_tuple(lang: str | None, key: str) -> tuple[str, ...]:
    pack = TEXTS[normalize_lang(lang)]
    fallback = TEXTS[DEFAULT_LANG]
    value = pack.get(key, fallback[key])
    return tuple(value)


def status_labels() -> tuple[str, ...]:
    labels: list[str] = []
    for pack in TEXTS.values():
        labels.append(pack["status_done"])
        labels.append(pack["status_not_done"])
        # older Russian wording, so existing messages still parse
    labels.extend(("✅ Выполнено", "❌ Невыполнено", "Выполнено ✅", "Невыполнено ❌"))
    return tuple(dict.fromkeys(labels))
