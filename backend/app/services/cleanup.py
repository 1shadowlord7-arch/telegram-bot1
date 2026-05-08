from __future__ import annotations
from datetime import datetime, timedelta
from app.db.mongo import get_db
from app.db.redis import get_redis

async def cleanup_expired_documents():
    db = get_db()
    now = datetime.utcnow()

    await db.games.delete_many({"expires_at": {"$lte": now}})
    await db.cache.delete_many({"expires_at": {"$lte": now}})
    await db.requests.delete_many({"status": {"$in": ["fulfilled", "rejected"]}, "updated_at": {"$lte": now - timedelta(days=30)}})
    await db.logs.delete_many({"created_at": {"$lte": now - timedelta(days=180)}})

    redis = get_redis()
    async for key in redis.scan_iter(match="temp:*"):
        ttl = await redis.ttl(key)
        if ttl is not None and ttl <= 0:
            await redis.delete(key)
