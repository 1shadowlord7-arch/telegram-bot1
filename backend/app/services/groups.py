from __future__ import annotations
from datetime import datetime
from typing import Any
from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from app.db.mongo import get_db
from app.utils.text import normalize_text, similarity
from app.utils.telegram import is_privileged
from app.services.logging import log_action

async def ensure_group(group_id: int, title: str | None = None, owner_id: int | None = None):
    db = get_db()
    await db.groups.update_one(
        {"group_id": group_id},
        {"$setOnInsert": {"group_id": group_id, "created_at": datetime.utcnow()},
         "$set": {"title": title, "owner_id": owner_id, "updated_at": datetime.utcnow()}},
        upsert=True,
    )

async def get_group(group_id: int) -> dict[str, Any] | None:
    return await get_db().groups.find_one({"group_id": group_id})

async def is_group_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return is_privileged(member)
    except Exception:
        return False

async def is_bot_admin(bot: Bot, chat_id: int) -> bool:
    me = await bot.get_me()
    try:
        member = await bot.get_chat_member(chat_id, me.id)
        return member.status in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER, ChatMemberStatus.CREATOR}
    except Exception:
        return False

async def set_group_setting(group_id: int, **kwargs):
    kwargs["updated_at"] = datetime.utcnow()
    await get_db().groups.update_one({"group_id": group_id}, {"$set": kwargs}, upsert=True)

async def connect_channel(group_id: int, channel_id: int, username: str | None, title: str | None):
    await get_db().channels.update_one(
        {"channel_id": channel_id},
        {"$set": {"channel_id": channel_id, "group_id": group_id, "username": username, "title": title, "indexed_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
         "$setOnInsert": {"created_at": datetime.utcnow()}},
        upsert=True,
    )
    await set_group_setting(group_id, connected_channel_id=channel_id, connected_channel_username=username, connected_channel_title=title)

async def disconnect_channel(group_id: int):
    group = await get_group(group_id)
    if group and group.get("connected_channel_id"):
        await get_db().channels.update_one({"channel_id": group["connected_channel_id"]}, {"$set": {"group_id": None, "updated_at": datetime.utcnow()}})
    await set_group_setting(group_id, connected_channel_id=None, connected_channel_username=None, connected_channel_title=None)

def allowed_limit(value: int, allowed: set[int], default: int) -> int:
    return value if value in allowed else default

async def set_filter_words(group_id: int, words: list[str]):
    await set_group_setting(group_id, filter_words=words)

async def add_filter_word(group_id: int, word: str):
    word = normalize_text(word).strip()
    if not word:
        return
    group = await get_group(group_id) or {}
    words = group.get("filter_words", [])
    if word not in words:
        words.append(word)
    await set_filter_words(group_id, words)

async def remove_filter_word(group_id: int, word: str):
    word = normalize_text(word).strip()
    group = await get_group(group_id) or {}
    words = [w for w in group.get("filter_words", []) if w != word]
    await set_filter_words(group_id, words)
