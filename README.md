# telegram-reminder-bot

Telegram bot that queues one-time and recurring reminders and sends them to the chat where they were created. Built with Python, aiogram, and SQLite.

## Features

- **One-time and repeating events** with a required title and optional description
- **Private chats and groups** — add the bot to a group; reminders go to that same chat
- **Inline actions** when a reminder fires: Done, Remind later, Not done
- **Pause and resume** repeating events without deleting them
- **History** of past reminders (/history)
- **Russian and English** UI, stored per chat (/lang)
- **Long polling**; event schedule survives restarts (SQLite)

## Commands

| Command | Description |
| --- | --- |
| /start | Welcome message and short intro |
| /help | Full help text |
| /add | Create an event (step-by-step wizard) |
| /list | Repeating events in this chat (enable / disable / delete) |
| /history | Past reminders that already fired |
| /lang | Change language for this chat |
| /cancel | Abort the current /add wizard |

## Creating an event (/add)

The wizard asks for:

1. **Title** (required, up to 200 characters)
2. **Description** (optional; skip with the button, -, or skip)
3. **Schedule type**
   - One-time — today, tomorrow, or a date DD.MM.YYYY
   - Every day
   - Every week — pick a weekday
   - Every month — day of month 1-31 (if the month is shorter, the last day is used)
4. **Time** as HH:MM (24-hour)
5. Confirmation

The event is bound to the chat where /add was used. In groups, reply to the bot (or disable privacy mode in BotFather) so it can read the title and description.

## When a reminder is sent

The bot posts the title (and description, if any) with three buttons:

- **Done** — marks the occurrence completed, appends Done, hides Done, shows Not done again
- **Not done** — marks it not completed, appends Not done, hides Not done, shows Done again
- **Remind later** — 15 minutes, 1 hour, 3 hours, or tomorrow at 09:00 (bot timezone). A new message is sent for the snooze; Done / Not done flags are kept

Statuses are mutually exclusive: choosing one replaces the other.

Repeating events stay scheduled after each send. A one-time event is sent once and then deactivated.

## Managing events (/list)

/list shows **repeating** events only (one-time events are not listed).

For each item:

- **Off** — stop sending; the button becomes **On**
- **On** — resume from the next future run
- **Delete** — remove the event (history of past sends is kept)

Anyone can create an event. **Off / On / Delete** are allowed for the event author or a chat administrator.

## History (/history)

Lists reminders that have already been sent, newest first:

- Title
- Date and time it was sent
- One-time or repeating
- In groups: who created the event (@username or display name)

History is stored independently, so deleting an event from /list does not wipe past entries. Long lists are paginated.

## Language (/lang)

Supported: **Russian** and **English**.

- Language is stored **per chat** (private or group)
- On first use, the bot infers it from the Telegram client language (`en*` → English, otherwise Russian)
- /lang — buttons to switch
- /lang en or /lang ru — set directly

In a group, only an administrator can change the language. Reminders and buttons use that chat language.

## Configuration

Copy `.env.example` to `.env`:

```env
BOT_TOKEN=123456789:ABC-your-token-here
TZ=Europe/London
```

- `BOT_TOKEN` — token from [@BotFather](https://t.me/BotFather)
- `TZ` — IANA timezone for schedules and tomorrow-at-09:00 (default `Europe/London`)

SQLite file: `data/bot.db` (created automatically).

### BotFather

1. Create a bot and copy the token into .env.
2. For groups, turn **Group Privacy** off so the wizard can see replies. With privacy on, users should reply to the bot prompt (Force Reply).

## Run locally

Python 3.12+ recommended.

```bash
python -m pip install -r requirements.txt
python -m bot.main
```

## Run with Docker

```bash
docker compose up -d --build
docker compose logs -f bot
docker compose down
```

The compose file mounts ./data so the database persists across rebuilds.

## Tech stack

- Python, aiogram, aiosqlite
- Background scheduler (~15s) driven by `next_run_at` in SQLite
- Long polling (no webhook)

## License

[MIT](LICENSE)
