from __future__ import annotations
from datetime import datetime
from aiogram import Bot
from aiogram.types import ChatPermissions
from app.services.logging import log_action
from app.db.mongo import get_db

async def apply_ban(bot: Bot, chat_id: int, user_id: int, reason: str | None, admin_user_id: int | None):
    await bot.ban_chat_member(chat_id, user_id)
    await log_action(chat_id, "ban", user_id, admin_user_id, reason)

async def apply_unban(bot: Bot, chat_id: int, user_id: int, admin_user_id: int | None):
    await bot.unban_chat_member(chat_id, user_id, only_if_banned=True)
    await log_action(chat_id, "unban", user_id, admin_user_id)

async def apply_mute(bot: Bot, chat_id: int, user_id: int, admin_user_id: int | None, until_date: datetime | None = None, reason: str | None = None):
    perms = ChatPermissions(can_send_messages=False, can_send_audios=False, can_send_documents=False, can_send_photos=False, can_send_videos=False, can_send_video_notes=False, can_send_voice_notes=False, can_send_polls=False, can_send_other_messages=False, can_add_web_page_previews=False, can_change_info=False, can_invite_users=False, can_pin_messages=False)
    await bot.restrict_chat_member(chat_id, user_id, permissions=perms, until_date=until_date)
    await log_action(chat_id, "mute", user_id, admin_user_id, reason)

async def apply_unmute(bot: Bot, chat_id: int, user_id: int, admin_user_id: int | None):
    perms = ChatPermissions(can_send_messages=True, can_send_audios=True, can_send_documents=True, can_send_photos=True, can_send_videos=True, can_send_video_notes=True, can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True, can_add_web_page_previews=True)
    await bot.restrict_chat_member(chat_id, user_id, permissions=perms)
    await log_action(chat_id, "unmute", user_id, admin_user_id)

async def add_warning(group_id: int, user_id: int, admin_user_id: int | None, reason: str | None):
    db = get_db()
    doc = await db.warnings.find_one({"group_id": group_id, "user_id": user_id})
    count = (doc or {}).get("warning_count", 0) + 1
    await db.warnings.update_one(
        {"group_id": group_id, "user_id": user_id},
        {"$set": {"warning_count": count, "reason": reason, "updated_at": datetime.utcnow()}, "$setOnInsert": {"created_at": datetime.utcnow()}},
        upsert=True,
    )
    await log_action(group_id, "warn", user_id, admin_user_id, reason, {"warning_count": count})
    return count

async def remove_warning(group_id: int, user_id: int, admin_user_id: int | None):
    db = get_db()
    await db.warnings.delete_one({"group_id": group_id, "user_id": user_id})
    await log_action(group_id, "unwarn", user_id, admin_user_id)
