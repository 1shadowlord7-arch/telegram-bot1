from __future__ import annotations
from datetime import datetime
from typing import Any
from app.db.mongo import get_db
from app.utils.text import normalize_text, compact_keywords, similarity

async def ensure_indexes():
    db = get_db()
    await db.channel_posts.create_index([("channel_id", 1), ("text", "text"), ("caption", "text"), ("keywords", "text"), ("message_id", 1)], name="channel_post_text")
    await db.requests.create_index([("group_id", 1), ("normalized_text", 1)], unique=True, name="unique_group_request")

async def index_channel_post(channel_id: int, message_id: int, text: str | None, caption: str | None, keywords: list[str] | None, post_date: datetime | None):
    db = get_db()
    full = " ".join([text or "", caption or "", " ".join(keywords or [])]).strip()
    if not full:
        return
    doc = {
        "channel_id": channel_id,
        "message_id": message_id,
        "text": text,
        "caption": caption,
        "keywords": keywords or [],
        "full_text": full,
        "normalized_text": normalize_text(full),
        "post_date": post_date or datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    await db.channel_posts.update_one({"channel_id": channel_id, "message_id": message_id}, {"$set": doc, "$setOnInsert": {"created_at": datetime.utcnow()}}, upsert=True)
    await db.channels.update_one({"channel_id": channel_id}, {"$set": {"indexed_at": datetime.utcnow(), "updated_at": datetime.utcnow()}}, upsert=True)

async def search_channel_posts(channel_id: int, query: str) -> dict[str, Any] | None:
    db = get_db()
    normalized = normalize_text(query)
    cursor = db.channel_posts.find({"channel_id": channel_id, "$or": [
        {"normalized_text": {"$regex": normalized.replace(" ", ".*"), "$options": "i"}},
        {"full_text": {"$regex": query, "$options": "i"}},
    ]}).sort("post_date", -1).limit(20)
    candidates = await cursor.to_list(length=20)
    if not candidates:
        return None
    ranked = sorted(candidates, key=lambda d: similarity(normalized, d.get("normalized_text", "")), reverse=True)
    best = ranked[0]
    best["score"] = similarity(normalized, best.get("normalized_text", ""))
    return best

async def create_request(group_id: int, requester_id: int, text: str, indexed_content: list[str]):
    db = get_db()
    normalized = normalize_text(text)
    for existing in indexed_content:
        if similarity(normalized, normalize_text(existing)) >= 88:
            return {"status": "duplicate", "matched": existing}
    existing_request = await db.requests.find_one({"group_id": group_id, "normalized_text": normalized})
    if existing_request:
        return {"status": "duplicate", "matched": existing_request.get("text")}
    doc = {
        "group_id": group_id,
        "requester_id": requester_id,
        "text": text,
        "normalized_text": normalized,
        "status": "open",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    await db.requests.insert_one(doc)
    return {"status": "created", "request": doc}
