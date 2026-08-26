import os
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
TZ_NAME = os.getenv("TZ", "Europe/London").strip() or "Europe/London"
TZ = ZoneInfo(TZ_NAME)

DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "bot.db"

SCHEDULER_INTERVAL_SEC = 15
TITLE_MAX_LEN = 200
DESCRIPTION_MAX_LEN = 1000
