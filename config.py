import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
BOT_USERNAME = os.getenv("BOT_USERNAME", "").lstrip("@")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "").lstrip("@")
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:5000").rstrip("/")
PORT = int(os.getenv("PORT", "5000"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")

if not BOT_USERNAME:
    raise RuntimeError("BOT_USERNAME is missing")

if not ADMIN_USERNAME:
    raise RuntimeError("ADMIN_USERNAME is missing")
