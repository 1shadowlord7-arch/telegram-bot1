from __future__ import annotations
import json
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, ChatMemberUpdated
from app.db.mongo import get_db
from app.db.redis import get_redis
from app.services.groups import (
    ensure_group, is_bot_admin, is_group_admin, connect_channel, disconnect_channel,
    set_group_setting, get_group
)
from app.services.search import search_channel_posts, create_request, index_channel_post
from app.services.moderation import apply_mute, apply_ban, add_warning, remove_warning, apply_unmute, apply_unban
from app.services.logging import log_action
from app.utils.text import normalize_text
from app.utils.telegram import display_name
from app.utils.rate_limit import allow_action

router = Router()

@router.message(Command("menu"))
async def menu(message: Message):
    await message.answer("Main menu is available from the keyboard.")

@router.my_chat_member()
async def bot_member_update(event: ChatMemberUpdated):
    chat = event.chat
    if chat.type in {"group", "supergroup"}:
        await ensure_group(chat.id, chat.title, event.from_user.id if event.from_user else None)
        if event.new_chat_member.status in {"administrator", "member"}:
            await get_db().groups.update_one(
                {"group_id": chat.id},
                {"$set": {"title": chat.title, "updated_at": datetime.utcnow()}},
            )

@router.message(Command("connect_channel"))
async def connect_channel_cmd(message: Message, bot):
    if message.chat.type not in {"group", "supergroup"}:
        return
    if not message.from_user or not await is_group_admin(bot, message.chat.id, message.from_user.id):
        await message.reply("⚠️ Admins only.")
        return
    if not await is_bot_admin(bot, message.chat.id):
        await message.reply("⚠️ I need to be admin in this group.")
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("Send: /connect_channel @channelusername or channel_id")
        return
    target = parts[1].strip()
    channel = await bot.get_chat(target)
    bot_member = await bot.get_chat_member(channel.id, (await bot.get_me()).id)
    if bot_member.status not in {"administrator", "creator"}:
        await message.reply("⚠️ I need to be admin in the channel too.")
        return
    await connect_channel(message.chat.id, channel.id, channel.username, channel.title)
    await message.reply(f"✅ Connected to channel: {channel.title or channel.username or channel.id}")

@router.message(Command("disconnect_channel"))
async def disconnect_channel_cmd(message: Message, bot):
    if not message.from_user or not await is_group_admin(bot, message.chat.id, message.from_user.id):
        await message.reply("⚠️ Admins only.")
        return
    await disconnect_channel(message.chat.id)
    await message.reply("✅ Channel disconnected.")

@router.message(Command("search"))
async def search_cmd(message: Message, bot):
    group = await get_group(message.chat.id)
    if not group or not group.get("connected_channel_id"):
        await message.reply("No connected channel yet.")
        return
    if not await allow_action(f"rl:search:{message.chat.id}:{message.from_user.id if message.from_user else 0}", 20, 60):
        await message.reply("⚠️ Too many searches. Please slow down.")
        return
    query = (message.text or "").split(maxsplit=1)
    if len(query) < 2:
        await message.reply("Send: /search query")
        return
    result = await search_channel_posts(group["connected_channel_id"], query[1])
    if not result:
        await message.reply("No exact result found. Use /request text to ask admins.")
        return
    text = result.get("full_text") or result.get("text") or result.get("caption") or ""
    post_link = None
    if group.get("connected_channel_username"):
        post_link = f"https://t.me/{group['connected_channel_username'].lstrip('@')}/{result['message_id']}"
    reply = f"🔎 Best match:\n\n{text[:3000]}"
    if post_link:
        reply += f"\n\nLink: {post_link}"
    await message.reply(reply, disable_web_page_preview=True)

@router.message(Command("request"))
async def request_cmd(message: Message, bot):
    if message.chat.type not in {"group", "supergroup"}:
        return
    group = await get_group(message.chat.id) or {}
    if not await allow_action(f"rl:request:{message.chat.id}:{message.from_user.id if message.from_user else 0}", 10, 60):
        await message.reply("⚠️ Too many requests. Please slow down.")
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("Send: /request text")
        return
    text = parts[1].strip()
    connected_channel_id = group.get("connected_channel_id")
    indexed = []
    if connected_channel_id:
        cursor = get_db().channel_posts.find({"channel_id": connected_channel_id}).sort("post_date", -1).limit(50)
        indexed = [doc.get("full_text", "") for doc in await cursor.to_list(50)]
    result = await create_request(message.chat.id, message.from_user.id if message.from_user else 0, text, indexed)
    if result["status"] == "duplicate":
        await message.reply("⚠️ Similar content already exists or has already been requested.")
        return
    await message.reply("✅ Request created and shared with admins.")
    await log_action(message.chat.id, "request", message.from_user.id if message.from_user else None, None, text)

@router.message(Command("done"))
async def done_cmd(message: Message):
    await message.reply("Saved.")

@router.message(Command("filter"))
async def filter_cmd(message: Message, bot):
    if not message.from_user or not await is_group_admin(bot, message.chat.id, message.from_user.id):
        await message.reply("⚠️ Admins only.")
        return
    redis = get_redis()
    await redis.set(f"pending:filter:add:{message.chat.id}:{message.from_user.id}", "1", ex=900)
    await message.reply("Send filter words now, one per message. Use /done when finished.")

@router.message(Command("filter_remove"))
async def filter_remove_cmd(message: Message, bot):
    if not message.from_user or not await is_group_admin(bot, message.chat.id, message.from_user.id):
        await message.reply("⚠️ Admins only.")
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("Send: /filter_remove word")
        return
    group = await get_group(message.chat.id) or {}
    words = [w for w in group.get("filter_words", []) if w != normalize_text(parts[1])]
    await set_group_setting(message.chat.id, filter_words=words)
    await message.reply("✅ Removed.")

@router.message(Command("warn"))
async def warn_cmd(message: Message, bot):
    if not message.from_user or not await is_group_admin(bot, message.chat.id, message.from_user.id):
        await message.reply("⚠️ Admins only.")
        return
    if not await is_bot_admin(bot, message.chat.id):
        await message.reply("⚠️ I need admin permissions in this group.")
        return
    target = message.reply_to_message.from_user if message.reply_to_message else None
    if not target:
        await message.reply("Reply to a user with /warn.")
        return
    group = await get_group(message.chat.id) or {}
    count = await add_warning(message.chat.id, target.id, message.from_user.id, "warned by admin")
    limit = group.get("warning_limit", 3)
    warn_card = (
        f"⚠️ warnings: {count} / {limit}\n"
        f"ID: {target.id}\n"
        f"@{target.username or 'no_username'}\n"
        f"{display_name(target)}"
    )
    await message.reply(warn_card)
    if count >= limit:
        action = group.get("warn_action", "mute")
        if action == "ban":
            await apply_ban(bot, message.chat.id, target.id, "warning limit reached", message.from_user.id)
        else:
            await apply_mute(bot, message.chat.id, target.id, message.from_user.id, reason="warning limit reached")

@router.message(Command("unwarn"))
async def unwarn_cmd(message: Message, bot):
    if not message.from_user or not await is_group_admin(bot, message.chat.id, message.from_user.id):
        await message.reply("⚠️ Admins only.")
        return
    if not await is_bot_admin(bot, message.chat.id):
        await message.reply("⚠️ I need admin permissions in this group.")
        return
    target = message.reply_to_message.from_user if message.reply_to_message else None
    if not target:
        await message.reply("Reply to a user with /unwarn.")
        return
    await remove_warning(message.chat.id, target.id, message.from_user.id)
    await message.reply("✅ Warning removed.")

@router.message(Command("ban"))
async def ban_cmd(message: Message, bot):
    if not message.from_user or not await is_group_admin(bot, message.chat.id, message.from_user.id):
        await message.reply("⚠️ Admins only.")
        return
    if not await is_bot_admin(bot, message.chat.id):
        await message.reply("⚠️ I need admin permissions in this group.")
        return
    target = message.reply_to_message.from_user if message.reply_to_message else None
    if not target:
        await message.reply("Reply to a user with /ban.")
        return
    await apply_ban(bot, message.chat.id, target.id, "manual ban", message.from_user.id)
    await message.reply("✅ Banned.")

@router.message(Command("unban"))
async def unban_cmd(message: Message, bot):
    if not message.from_user or not await is_group_admin(bot, message.chat.id, message.from_user.id):
        await message.reply("⚠️ Admins only.")
        return
    if not await is_bot_admin(bot, message.chat.id):
        await message.reply("⚠️ I need admin permissions in this group.")
        return
    target = message.reply_to_message.from_user if message.reply_to_message else None
    if not target:
        await message.reply("Reply to a user with /unban.")
        return
    await apply_unban(bot, message.chat.id, target.id, message.from_user.id)
    await message.reply("✅ Unbanned.")

@router.message(Command("mute"))
async def mute_cmd(message: Message, bot):
    if not message.from_user or not await is_group_admin(bot, message.chat.id, message.from_user.id):
        await message.reply("⚠️ Admins only.")
        return
    if not await is_bot_admin(bot, message.chat.id):
        await message.reply("⚠️ I need admin permissions in this group.")
        return
    target = message.reply_to_message.from_user if message.reply_to_message else None
    if not target:
        await message.reply("Reply to a user with /mute.")
        return
    await apply_mute(bot, message.chat.id, target.id, message.from_user.id)
    await message.reply("✅ Muted.")

@router.message(Command("unmute"))
async def unmute_cmd(message: Message, bot):
    if not message.from_user or not await is_group_admin(bot, message.chat.id, message.from_user.id):
        await message.reply("⚠️ Admins only.")
        return
    if not await is_bot_admin(bot, message.chat.id):
        await message.reply("⚠️ I need admin permissions in this group.")
        return
    target = message.reply_to_message.from_user if message.reply_to_message else None
    if not target:
        await message.reply("Reply to a user with /unmute.")
        return
    await apply_unmute(bot, message.chat.id, target.id, message.from_user.id)
    await message.reply("✅ Unmuted.")

@router.message(F.text)
async def group_text_moderation(message: Message, bot):
    if message.chat.type not in {"group", "supergroup"} or not message.from_user:
        return
    if not await is_bot_admin(bot, message.chat.id):
        return
    await ensure_group(message.chat.id, message.chat.title, message.from_user.id)
    group = await get_group(message.chat.id) or {}
    text = normalize_text(message.text or message.caption or "")
    if not text:
        return

    redis = get_redis()
    pending_key = f"pending:filter:add:{message.chat.id}:{message.from_user.id}"
    if await redis.get(pending_key):
        incoming = normalize_text(message.text or "")
        if incoming and incoming != "/done":
            words = [w.strip() for w in incoming.split(",") if w.strip()]
            current = list(group.get("filter_words", []))
            for w in words:
                if w not in current:
                    current.append(w)
            await set_group_setting(message.chat.id, filter_words=current)
            await message.reply("✅ Filter word saved.")
            return

    for word in group.get("filter_words", []):
        if word and word in text:
            try:
                await message.delete()
            except Exception:
                pass
            await log_action(message.chat.id, "filter_action", message.from_user.id, None, f"matched={word}")
            if group.get("filter_action", "mute") == "ban":
                await apply_ban(bot, message.chat.id, message.from_user.id, "filter word", None)
            else:
                await apply_mute(bot, message.chat.id, message.from_user.id, None, reason="filter word")
            return

    if group.get("spam_enabled", False):
        key = f"spam:{message.chat.id}:{message.from_user.id}"
        raw = await redis.get(key)
        payload = [] if not raw else json.loads(raw)
        now = datetime.utcnow().timestamp()
        payload = [ts for ts in payload if now - ts <= 300]
        payload.append(now)
        await redis.set(key, json.dumps(payload), ex=330)
        limit = group.get("spam_limit", 3)
        if len(payload) >= limit:
            try:
                await message.delete()
            except Exception:
                pass
            if group.get("spam_action", "mute") == "ban":
                await apply_ban(bot, message.chat.id, message.from_user.id, "spam detection", None)
            else:
                await apply_mute(bot, message.chat.id, message.from_user.id, None, reason="spam detection")
            await log_action(message.chat.id, "spam_action", message.from_user.id, None, "spam detection", {"count": len(payload)})
            await redis.delete(key)
            return

@router.channel_post()
async def channel_post_index(message: Message):
    text = message.text
    caption = message.caption
    keywords = []
    if text:
        keywords.extend(text.split()[:20])
    if caption:
        keywords.extend(caption.split()[:20])
    await index_channel_post(message.chat.id, message.message_id, text, caption, keywords, message.date)

@router.message(Command("reindex"))
async def reindex_cmd(message: Message, bot):
    if not message.from_user or not await is_group_admin(bot, message.chat.id, message.from_user.id):
        await message.reply("⚠️ Admins only.")
        return
    group = await get_group(message.chat.id) or {}
    if not group.get("connected_channel_id"):
        await message.reply("No connected channel.")
        return
    await message.reply("✅ Reindex scheduled. Existing channel posts remain searchable.")
