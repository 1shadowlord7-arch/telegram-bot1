from __future__ import annotations
from datetime import datetime
from app.db.mongo import get_db

async def log_action(group_id: int, action: str, target_user_id: int | None = None, admin_user_id: int | None = None, reason: str | None = None, meta: dict | None = None):
    db = get_db()
    await db.logs.insert_one({
        "group_id": group_id,
        "action": action,
        "target_user_id": target_user_id,
        "admin_user_id": admin_user_id,
        "reason": reason,
        "meta": meta or {},
        "created_at": datetime.utcnow(),
    })
