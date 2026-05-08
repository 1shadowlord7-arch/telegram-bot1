from __future__ import annotations
from datetime import datetime, timedelta
from app.db.redis import get_redis

async def allow_action(key: str, limit: int, window_seconds: int) -> bool:
    redis = get_redis()
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, window_seconds)
    return count <= limit

async def get_or_set_json(key: str, default, ttl: int | None = None):
    redis = get_redis()
    existing = await redis.get(key)
    if existing is None:
        import json
        value = json.dumps(default)
        if ttl:
            await redis.set(key, value, ex=ttl)
        else:
            await redis.set(key, value)
        return default
    import json
    return json.loads(existing)
