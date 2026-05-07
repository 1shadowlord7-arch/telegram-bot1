from __future__ import annotations
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from app.services.games import create_challenge, get_session, set_session, ttt_winner
from app.services.logging import log_action
from app.utils.telegram import display_name
from app.db.mongo import get_db

router = Router()

@router.message(Command("challenge"))
async def challenge_cmd(message: Message, bot):
    if not message.from_user:
        return
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.reply("Reply to a user or send /challenge @username")
        return
    username = parts[1].lstrip("@")
    try:
        target = await bot.get_chat(username)
    except Exception:
        await message.reply("User not found.")
        return
    game = await create_challenge(message.chat.id, message.from_user.id, target.id, "rps")
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Accept", callback_data=f"game:accept:{game['session_id']}"), InlineKeyboardButton(text="Decline", callback_data=f"game:decline:{game['session_id']}")]])
    await bot.send_message(target.id, f"🕹 {display_name(message.from_user)} challenged you to Rock Paper Scissors", reply_markup=kb)
    await message.reply("Challenge sent.")

@router.callback_query(F.data.startswith("game:"))
async def game_cb(call: CallbackQuery, bot):
    parts = call.data.split(":")
    action = parts[1]
    session_id = parts[2]
    session = await get_session(session_id)
    if not session:
        await call.answer("Game expired", show_alert=True)
        return
    if action == "accept":
        await set_session(session_id, status="active")
        await call.answer("Accepted")
        await call.message.edit_text("Game accepted.")
    elif action == "decline":
        await set_session(session_id, status="declined")
        await call.answer("Declined")
        await call.message.edit_text("Game declined.")
