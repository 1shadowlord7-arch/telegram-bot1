import html
import threading

from flask import Flask, abort, redirect, render_template_string, request
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from config import ADMIN_USERNAME, BASE_URL, BOT_TOKEN, BOT_USERNAME, PORT
from games import GAME_REGISTRY, load_games

app = Flask(__name__)
load_games()


def build_game_keyboard():
    rows = []
    for key, module in GAME_REGISTRY.items():
        rows.append([InlineKeyboardButton(module.GAME_NAME, callback_data=f"game:{key}")])
    return InlineKeyboardMarkup(rows)


def build_home_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ add to group", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
        [InlineKeyboardButton("play", callback_data="play_menu")],
        [InlineKeyboardButton("contact admin", url=f"https://t.me/{ADMIN_USERNAME}")],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = html.escape(user.full_name if user else "there")
    text = (
        f"Hello {name} 👋\n\n"
        "Choose one button below.\n"
        "You can add the bot to a group, open games, or contact the admin."
    )
    await update.message.reply_text(text, reply_markup=build_home_keyboard(), parse_mode="HTML")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "/start - open bot menu\n"
        "/help - show commands\n"
        "/info - show your user info\n"
        "/play - open game list\n"
        "/challenge <game> <@username|user_id> - send a challenge card in a group"
    )
    await update.message.reply_text(text)


async def info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    text = (
        f"Your info:\n"
        f"User ID: {user.id}\n"
        f"Username: @{user.username}" if user.username else f"Your info:\nUser ID: {user.id}\nUsername: not set"
    )
    text += f"\nName: {user.full_name}\nChat ID: {chat.id}"
    await update.message.reply_text(text)


async def play_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Choose a game:", reply_markup=build_game_keyboard())


async def challenge_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Use: /challenge <game> <@username|user_id>")
        return

    game_key = context.args[0].lower().strip()
    target = " ".join(context.args[1:]).strip()

    if game_key not in GAME_REGISTRY:
        names = ", ".join(module.GAME_NAME for module in GAME_REGISTRY.values())
        await update.message.reply_text(f"Unknown game.\nAvailable: {names}")
        return

    module = GAME_REGISTRY[game_key]
    text = (
        f"🎮 Challenge created!\n"
        f"Game: {module.GAME_NAME}\n"
        f"Target: {target}\n\n"
        f"Open the game page from the button below."
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
            reply_markup=keyboard
        )


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
        a.btn {{ display:inline-block; margin-right:8px; margin-top:8px; padding:10px 14px; border-radius:12px; background:#2563eb; color:#fff; text-decoration:none; font-weight:700; }}
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
        </div>
        {"".join(cards)}
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
    return {"ok": True}


def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("info", info_cmd))
    application.add_handler(CommandHandler("play", play_cmd))
    application.add_handler(CommandHandler("challenge", challenge_cmd))
    application.add_handler(CallbackQueryHandler(callback_handler))

    application.run_polling(allowed_updates=Update.ALL_TYPES, stop_signals=None)


if __name__ == "__main__":
    import threading
    t = threading.Thread(target=run_bot)
    t.start()

    app.run(host="0.0.0.0", port=PORT, use_reloader=False)
