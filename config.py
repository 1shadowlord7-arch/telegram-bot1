import os
from dotenv import load_dotenv

load_dotenv()

def _clean_url(value: str | None, fallback: str) -> str:
    value = (value or '').strip()
    if not value:
        value = fallback
    return value.rstrip('/')

BOT_TOKEN = (os.getenv("BOT_TOKEN", "") or "").strip()
BOT_USERNAME = (os.getenv("BOT_USERNAME", "") or "").strip()
OWNER_URL = _clean_url(os.getenv("OWNER_URL"), "https://t.me/yourusername")
UPDATES_CHANNEL_URL = _clean_url(os.getenv("UPDATES_CHANNEL_URL"), "https://t.me/yourchannel")
BASE_URL = _clean_url(os.getenv("BASE_URL"), "http://127.0.0.1:10000")
FRONTEND_URL = _clean_url(os.getenv("FRONTEND_URL"), BASE_URL)
SECRET_KEY = (os.getenv("SECRET_KEY", "change-this-secret-key") or "change-this-secret-key").strip()
DB_FILE = (os.getenv("DB_FILE", "bot.db") or "bot.db").strip()
DEFAULT_WARN_LIMIT = int(os.getenv("DEFAULT_WARN_LIMIT", "3"))
DEFAULT_REQUEST_LIMIT = int(os.getenv("DEFAULT_REQUEST_LIMIT", "1"))
DEFAULT_SPAM_LIMIT = int(os.getenv("DEFAULT_SPAM_LIMIT", "5"))
MUTE_SECONDS = int(os.getenv("MUTE_SECONDS", "600"))

MONGO_URI = (os.getenv("MONGO_URI", "") or "").strip()
MONGO_DB_NAME = (os.getenv("MONGO_DB_NAME", "telegram_bot") or "telegram_bot").strip()
