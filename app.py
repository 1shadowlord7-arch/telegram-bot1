import asyncio
import html
import json
import logging
import threading
import traceback
from typing import Optional

from flask import Flask, abort, jsonify, redirect, request

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from config import ADMIN_USERNAME, BASE_URL, BOT_TOKEN, BOT_USERNAME, PORT
from games import GAME_REGISTRY, load_games

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("telegram-bot")

app = Flask(__name__)

load_games()

BOT_APP: Optional[Application] = None
BOT_READY = False
LAST_ERROR = None
STARTUP_DONE = False
STARTUP_LOCK = threading.Lock()


def build_home_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ add to group", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
        [InlineKeyboardButton("play", callback_data="play_menu")],
        [InlineKeyboardButton("contact admin", url=f"https://t.me/{ADMIN_USERNAME}")],
    ])


def build_game_keyboard():
    rows = []
    for key, module in GAME_REGISTRY.items():
        rows.append([InlineKeyboardButton(module.GAME_NAME, callback_data=f"game:{key}")])
    return InlineKeyboardMarkup(rows)


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = html.escape(user.full_name if user else "there")
    text = (
        f"Hello {name} 👋\n\n"
        "Use the buttons below.\n"
        "You can add me to a group, open games, or contact admin."
    )
    await update.message.reply_text(text, reply_markup=build_home_keyboard(), parse_mode="HTML")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "/start - open menu\n"
        "/help - show commands\n"
        "/info - show your user info\n"
        "/play - open game list\n"
        "/challenge <game> <@username|user_id> - send a challenge card\n"
        "/ping - test if the bot is alive"
    )
    await update.message.reply_text(text)


async def info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    username = f"@{user.username}" if user.username else "not set"
    text = (
        "Your info:\n"
        f"User ID: {user.id}\n"
        f"Username: {username}\n"
        f"Name: {user.full_name}\n"
        f"Chat ID: {chat.id}\n"
        f"Chat type: {chat.type}"
    )
    await update.message.reply_text(text)


async def play_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Choose a game:", reply_markup=build_game_keyboard())


async def ping_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot is alive ✅")


async def challenge_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Use: /challenge <game> <@username|user_id>")
        return

    game_key = context.args[0].lower().strip()
    target = " ".join(context.args[1:]).strip()

    module = GAME_REGISTRY.get(game_key)
    if not module:
        names = ", ".join(m.GAME_NAME for m in GAME_REGISTRY.values())
        await update.message.reply_text(f"Unknown game.\nAvailable: {names}")
        return

    text = (
        f"🎮 Challenge created!\n"
        f"Game: {module.GAME_NAME}\n"
        f"Target: {target}\n\n"
        f"Open the game page with the button below."
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Open {module.GAME_NAME}", url=f"{BASE_URL}/game/{game_key}")],
        [InlineKeyboardButton("Back to games", url=f"{BASE_URL}/play")],
    ])
    await update.message.reply_text(text, reply_markup=keyboard)


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data or ""

    if data == "play_menu":
        await query.edit_message_text("Choose a game:", reply_markup=build_game_keyboard())
        return

    if data.startswith("game:"):
        game_key = data.split(":", 1)[1]
        module = GAME_REGISTRY.get(game_key)
        if not module:
            await query.edit_message_text("Game not found.")
            return

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"Open {module.GAME_NAME}", url=f"{BASE_URL}/game/{game_key}")],
            [InlineKeyboardButton("Back to games", callback_data="play_menu")],
        ])
        await query.edit_message_text(
            f"{module.GAME_NAME}\n\nOpen the web page to play.",
            reply_markup=keyboard,
        )


async def debug_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        logger.info(
            "Message received | chat_id=%s | user_id=%s | text=%s",
            update.effective_chat.id if update.effective_chat else None,
            update.effective_user.id if update.effective_user else None,
            update.message.text,
        )


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    global LAST_ERROR
    err_text = "".join(traceback.format_exception(context.error))
    LAST_ERROR = err_text
    logger.error("Unhandled error:\n%s", err_text)


def build_bot_app():
    app_ = Application.builder().token(BOT_TOKEN).build()

    app_.add_handler(CommandHandler("start", start_cmd))
    app_.add_handler(CommandHandler("help", help_cmd))
    app_.add_handler(CommandHandler("info", info_cmd))
    app_.add_handler(CommandHandler("play", play_cmd))
    app_.add_handler(CommandHandler("challenge", challenge_cmd))
    app_.add_handler(CommandHandler("ping", ping_cmd))
    app_.add_handler(CallbackQueryHandler(callback_handler))
    app_.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, debug_text))
    app_.add_error_handler(on_error)

    return app_



def start_bot():
    import asyncio
    import traceback

    global BOT_READY, LAST_ERROR, BOT_APP

    try:
        # 🔥 CREATE EVENT LOOP (FIX)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        BOT_APP = build_bot_app()

        print("✅ Bot starting polling...")

        BOT_APP.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            stop_signals=None,
        )

        BOT_READY = True

    except Exception:
        LAST_ERROR = traceback.format_exc()
        print("❌ BOT ERROR:\n", LAST_ERROR)

def ensure_bot_started():
    global STARTUP_DONE
    with STARTUP_LOCK:
        if STARTUP_DONE:
            return
        STARTUP_DONE = True
        thread = threading.Thread(target=start_bot, name="telegram-bot-thread", daemon=True)
        thread.start()
        logger.info("Bot thread started")


@app.before_request
def lazy_start_bot():
    ensure_bot_started()


@app.route("/")
def home():
    return redirect("/play")


@app.route("/play")
def play_page():
    cards = []
    for key, module in GAME_REGISTRY.items():
        cards.append(
            f"""
            <div style="background:#111827;border:1px solid #334155;border-radius:16px;padding:16px;margin:12px 0;">
                <h2 style="margin:0 0 6px 0;color:#fff;">{module.GAME_NAME}</h2>
                <p style="margin:0 0 12px 0;color:#cbd5e1;">Open this game in your browser.</p>
                <a href="/game/{key}" style="display:inline-block;padding:10px 14px;border-radius:12px;background:#2563eb;color:#fff;text-decoration:none;font-weight:700;">Open</a>
            </div>
            """
        )

    page = f"""
    <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Game Hub</title>
      <style>
        body {{ margin:0; font-family:Arial,sans-serif; background:#0b1220; color:#e5e7eb; }}
        .wrap {{ max-width:900px; margin:0 auto; padding:18px; }}
        .hero {{ background:#111827; border:1px solid #334155; border-radius:18px; padding:18px; }}
        .status {{ margin-top:12px; padding:12px; border-radius:12px; background:#0f172a; border:1px solid #334155; }}
        a.btn {{ display:inline-block; margin-right:8px; margin-top:8px; padding:10px 14px; border-radius:12px; background:#2563eb; color:#fff; text-decoration:none; font-weight:700; }}
        code {{ word-break: break-all; }}
      </style>
    </head>
    <body>
      <div class="wrap">
        <div class="hero">
          <h1>Game Hub</h1>
          <p>Open a game here or go back to Telegram.</p>
          <a class="btn" href="https://t.me/{BOT_USERNAME}">Open bot</a>
          <a class="btn" href="https://t.me/{BOT_USERNAME}?startgroup=true">Add to group</a>
          <a class="btn" href="https://t.me/{ADMIN_USERNAME}">Contact admin</a>

          <div class="status">
            <div><b>Bot ready:</b> {BOT_READY}</div>
            <div><b>Loaded games:</b> {", ".join(GAME_REGISTRY.keys()) if GAME_REGISTRY else "none"}</div>
            <div><b>Health:</b> <a href="/health">/health</a></div>
            <div><b>Status:</b> <a href="/status">/status</a></div>
          </div>
        </div>
        {''.join(cards)}
      </div>
    </body>
    </html>
    """
    return page


@app.route("/game/<game_key>")
def game_page(game_key: str):
    module = GAME_REGISTRY.get(game_key)
    if not module:
        abort(404)
    return module.render_page(BASE_URL)


@app.route("/health")
def health():
    return jsonify({
        "ok": True,
        "bot_ready": BOT_READY,
        "loaded_games": list(GAME_REGISTRY.keys()),
    })


@app.route("/status")
def status():
    return jsonify({
        "bot_ready": BOT_READY,
        "loaded_games": list(GAME_REGISTRY.keys()),
        "last_error": LAST_ERROR,
        "base_url": BASE_URL,
    })


@app.route("/bot-check")
def bot_check():
    return f"Bot ready: {BOT_READY}\nLoaded games: {', '.join(GAME_REGISTRY.keys())}\n"


if __name__ == "__main__":
    ensure_bot_started()
    app.run(host="0.0.0.0", port=PORT, use_reloader=False)
