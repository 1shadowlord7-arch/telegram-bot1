import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
BOT_USERNAME = os.getenv("BOT_USERNAME", "")
OWNER_URL = os.getenv("OWNER_URL", "https://t.me/yourusername")
UPDATES_CHANNEL_URL = os.getenv("UPDATES_CHANNEL_URL", "https://t.me/yourchannel")
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:10000")
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key")
DB_FILE = os.getenv("DB_FILE", "bot.db")
DEFAULT_WARN_LIMIT = int(os.getenv("DEFAULT_WARN_LIMIT", "3"))
DEFAULT_REQUEST_LIMIT = int(os.getenv("DEFAULT_REQUEST_LIMIT", "1"))
DEFAULT_SPAM_LIMIT = int(os.getenv("DEFAULT_SPAM_LIMIT", "5"))
MUTE_SECONDS = int(os.getenv("MUTE_SECONDS", "600"))

MONGO_URI = os.getenv("MONGO_URI", "")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "telegram_bot")
