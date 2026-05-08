from __future__ import annotations
import hashlib, hmac, json
from urllib.parse import parse_qsl
from datetime import datetime, timedelta, timezone
import jwt
from aiogram.types import WebAppInitData, User
from app.core.config import get_settings
from app.db.redis import get_redis

settings = get_settings()

def verify_telegram_init_data(init_data: str) -> dict:
    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    if "hash" not in parsed:
        raise ValueError("Missing hash")
    received_hash = parsed.pop("hash")
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret_key = hashlib.sha256(settings.bot_token.encode()).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated_hash, received_hash):
        raise ValueError("Invalid Telegram init data hash")
    auth_date = int(parsed.get("auth_date", "0"))
    if datetime.now(timezone.utc).timestamp() - auth_date > 86400:
        raise ValueError("Expired Telegram init data")
    user = json.loads(parsed.get("user", "{}"))
    return user

def issue_jwt(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": datetime.now(timezone.utc) + timedelta(seconds=settings.access_token_ttl_seconds),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def decode_jwt(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])

async def store_session(user_id: int, token: str):
    redis = get_redis()
    await redis.set(f"session:{token}", str(user_id), ex=settings.access_token_ttl_seconds)

async def session_user(token: str) -> int | None:
    redis = get_redis()
    value = await redis.get(f"session:{token}")
    return int(value) if value else None
