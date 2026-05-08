from __future__ import annotations
from datetime import datetime
from aiogram import Bot
from app.db.mongo import get_db
from app.utils.telegram import display_name

async def upsert_user_profile(user):
    db = get_db()
    await db.users.update_one(
        {"user_id": user.id},
        {"$set": {
            "user_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "photo_url": None,
            "language_code": user.language_code,
            "last_active_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }, "$setOnInsert": {"created_at": datetime.utcnow()}},
        upsert=True,
    )

async def fetch_user_profile(bot: Bot, user_id: int) -> dict:
    db = get_db()
    profile = await db.users.find_one({"user_id": user_id})
    if profile:
        return profile
    chat = await bot.get_chat(user_id)
    photo_url = None
    try:
        photos = await bot.get_user_profile_photos(user_id, limit=1)
        if photos.total_count:
            file = await bot.get_file(photos.photos[0][-1].file_id)
            photo_url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"
    except Exception:
        pass
    profile = {
        "user_id": user_id,
        "username": chat.username,
        "first_name": chat.first_name or "",
        "last_name": chat.last_name,
        "photo_url": photo_url,
        "last_active_at": datetime.utcnow(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    await db.users.update_one({"user_id": user_id}, {"$set": profile}, upsert=True)
    return profile

async def create_friend_request(requester_id: int, friend_id: int):
    db = get_db()
    if requester_id == friend_id:
        return {"status": "invalid"}
    existing = await db.friendships.find_one({"$or": [
        {"user_id": requester_id, "friend_id": friend_id},
        {"user_id": friend_id, "friend_id": requester_id},
    ]})
    if existing:
        return {"status": "exists", "friendship": existing}
    doc = {"user_id": requester_id, "friend_id": friend_id, "status": "pending", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow(), "blocked_by": None}
    await db.friendships.insert_one(doc)
    return {"status": "created", "friendship": doc}

async def accept_friend_request(user_id: int, friend_id: int):
    db = get_db()
    await db.friendships.update_one({"user_id": friend_id, "friend_id": user_id, "status": "pending"}, {"$set": {"status": "accepted", "updated_at": datetime.utcnow()}})
    await db.friendships.update_one({"user_id": user_id, "friend_id": friend_id, "status": "pending"}, {"$set": {"status": "accepted", "updated_at": datetime.utcnow()}})
    return True

async def remove_friend(user_id: int, friend_id: int):
    db = get_db()
    await db.friendships.delete_many({"$or": [{"user_id": user_id, "friend_id": friend_id}, {"user_id": friend_id, "friend_id": user_id}]})

async def block_friend(user_id: int, friend_id: int):
    db = get_db()
    await db.friendships.update_many({"$or": [{"user_id": user_id, "friend_id": friend_id}, {"user_id": friend_id, "friend_id": user_id}]}, {"$set": {"status": "blocked", "blocked_by": user_id, "updated_at": datetime.utcnow()}})

async def list_friends(user_id: int):
    db = get_db()
    cursor = db.friendships.find({"$or": [{"user_id": user_id, "status": "accepted"}, {"friend_id": user_id, "status": "accepted"}]})
    return await cursor.to_list(length=100)
