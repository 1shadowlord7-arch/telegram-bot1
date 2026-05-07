from __future__ import annotations
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from app.services.friends import upsert_user_profile, create_friend_request, accept_friend_request, remove_friend, block_friend, list_friends, fetch_user_profile
from app.utils.telegram import display_name, username_handle
from app.db.mongo import get_db

router = Router()

@router.message(Command("addfriend"))
async def addfriend(message: Message, bot):
    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user
    else:
        parts = (message.text or "").split(maxsplit=1)
        if len(parts) < 2:
            await message.reply("Reply to a user or send /addfriend @username")
            return
        username = parts[1].lstrip("@")
        try:
            target = await bot.get_chat(username)
        except Exception:
            await message.reply("Couldn't find that user. Ask them to message the bot first.")
            return
    await upsert_user_profile(message.from_user)
    result = await create_friend_request(message.from_user.id, target.id)
    if result["status"] == "exists":
        await message.reply("Friendship already exists.")
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Accept", callback_data=f"friend:accept:{message.from_user.id}:{target.id}"), InlineKeyboardButton(text="Decline", callback_data=f"friend:decline:{message.from_user.id}:{target.id}")]])
    await bot.send_message(target.id, f"👥 Friend request from {display_name(message.from_user)}", reply_markup=kb)
    await message.reply("✅ Friend request sent.")

@router.callback_query(F.data.startswith("friend:"))
async def friend_actions(call: CallbackQuery, bot):
    _, action, a, b = call.data.split(":")
    requester_id, target_id = int(a), int(b)
    if call.from_user.id != target_id and call.from_user.id != requester_id:
        await call.answer("Not allowed", show_alert=True)
        return
    if action == "accept":
        await accept_friend_request(target_id, requester_id)
        await call.answer("Accepted")
        await call.message.edit_text("✅ Friend request accepted.")
    elif action == "decline":
        await call.answer("Declined")
        await call.message.edit_text("❌ Friend request declined.")
    elif action == "remove":
        await remove_friend(call.from_user.id, requester_id if call.from_user.id == target_id else target_id)
        await call.answer("Removed")
    elif action == "block":
        await block_friend(call.from_user.id, requester_id if call.from_user.id == target_id else target_id)
        await call.answer("Blocked")

@router.message(F.text == "👥 Friends")
async def friends_menu(message: Message):
    await message.answer("Open the Friends page in the Mini App.")
