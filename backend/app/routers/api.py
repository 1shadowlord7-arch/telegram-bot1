from __future__ import annotations
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from app.services.auth import verify_telegram_init_data, issue_jwt, store_session, decode_jwt
from app.db.mongo import get_db
from app.core.config import get_settings
from app.services.friends import list_friends, fetch_user_profile, create_friend_request
from app.services.search import search_channel_posts
from app.utils.telegram import display_name
from app.services.groups import get_group, set_group_setting, connect_channel, disconnect_channel, is_group_admin, is_bot_admin, add_filter_word, remove_filter_word
from app.db.redis import get_redis

router = APIRouter(prefix="/api", tags=["api"])
settings = get_settings()

class LoginPayload(BaseModel):
    initData: str

async def require_user(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing token")
    token = authorization.removeprefix("Bearer ").strip()
    data = decode_jwt(token)
    return int(data["sub"])

@router.post("/auth/login")
async def login(payload: LoginPayload):
    user = verify_telegram_init_data(payload.initData)
    token = issue_jwt(user["id"])
    await store_session(user["id"], token)
    db = get_db()
    await db.users.update_one({"user_id": user["id"]}, {"$set": {"user_id": user["id"], "username": user.get("username"), "first_name": user.get("first_name", ""), "last_name": user.get("last_name"), "language_code": user.get("language_code"), "last_active_at": datetime.utcnow(), "updated_at": datetime.utcnow()}, "$setOnInsert": {"created_at": datetime.utcnow()}}, upsert=True)
    return {"token": token, "user": user}

@router.get("/menu")
async def menu():
    return {
        "buttons": [
            {"label": "➕ Add to Group", "type": "invite"},
            {"label": "⚙️ Group Settings", "type": "page", "route": "/group-settings"},
            {"label": "🕹 Play Games", "type": "page", "route": "/games"},
            {"label": "👥 Friends", "type": "page", "route": "/friends"},
            {"label": "📂 Linked Files", "type": "page", "route": "/files"},
            {"label": "🛒 Market", "type": "page", "route": "/market"},
            {"label": "👑 Owner", "type": "external", "url": f"https://t.me/{settings.owner_username}"},
            {"label": "📢 Join Updates Channel", "type": "external", "url": f"https://t.me/{settings.updates_channel.lstrip('@')}"},
        ]
    }

@router.get("/friends")
async def friends(user_id: int = Depends(require_user)):
    db = get_db()
    friendships = await list_friends(user_id)
    ids = []
    for f in friendships:
        ids.append(f["friend_id"] if f["user_id"] == user_id else f["user_id"])
    profiles = []
    now = datetime.utcnow()
    for uid in ids:
        profile = await db.users.find_one({"user_id": uid}) or {"user_id": uid}
        last_active = profile.get("last_active_at")
        online = False
        if last_active:
            try:
                online = (now - last_active).total_seconds() <= 600
            except Exception:
                online = False
        profiles.append({
            "user_id": uid,
            "display_name": f"{profile.get('first_name','')} {profile.get('last_name','')}".strip() or profile.get("username") or str(uid),
            "username": profile.get("username"),
            "photo_url": profile.get("photo_url"),
            "online": online,
            "last_active_at": last_active,
        })
    return {"friends": profiles}

class SearchPayload(BaseModel):
    group_id: int
    query: str

@router.post("/search")
async def search(payload: SearchPayload, user_id: int = Depends(require_user)):
    group = await get_group(payload.group_id)
    if not group or not group.get("connected_channel_id"):
        return {"result": None, "message": "No connected channel"}
    result = await search_channel_posts(group["connected_channel_id"], payload.query)
    return {"result": result}

@router.get("/groups/{group_id}")
async def group_settings(group_id: int, user_id: int = Depends(require_user)):
    group = await get_group(group_id)
    if not group:
        raise HTTPException(404, "Group not found")
    return group

class GroupUpdatePayload(BaseModel):
    request_limit: int | None = Field(default=None, ge=1, le=10)
    warning_limit: int | None = Field(default=None, ge=1, le=5)
    spam_enabled: bool | None = None
    spam_limit: int | None = Field(default=None, ge=3, le=10)
    spam_action: str | None = None
    warn_action: str | None = None
    filter_words: list[str] | None = None
    connect_channel: str | None = None
    disconnect_channel: bool = False

@router.patch("/groups/{group_id}")
async def update_group(group_id: int, payload: GroupUpdatePayload, user_id: int = Depends(require_user)):
    group = await get_group(group_id)
    if not group:
        raise HTTPException(404, "Group not found")
    updates = {}
    if payload.request_limit is not None:
        updates["request_limit"] = payload.request_limit
    if payload.warning_limit is not None:
        updates["warning_limit"] = payload.warning_limit
    if payload.spam_enabled is not None:
        updates["spam_enabled"] = payload.spam_enabled
    if payload.spam_limit is not None:
        updates["spam_limit"] = payload.spam_limit
    if payload.spam_action in {"mute", "ban"}:
        updates["spam_action"] = payload.spam_action
    if payload.warn_action in {"mute", "ban"}:
        updates["warn_action"] = payload.warn_action
    if payload.filter_words is not None:
        updates["filter_words"] = payload.filter_words
    if updates:
        await set_group_setting(group_id, **updates)
    return {"ok": True, "group": await get_group(group_id)}

@router.get("/owner")
async def owner():
    return {"url": f"https://t.me/{settings.owner_username}"}


class FriendRequestPayload(BaseModel):
    friend_id: int

@router.post("/friends/request")
async def request_friend(payload: FriendRequestPayload, user_id: int = Depends(require_user)):
    result = await create_friend_request(user_id, payload.friend_id)
    return result

@router.get("/files")
async def files():
    return {"title": "Linked Files", "subtitle": "Coming Soon"}

@router.get("/market")
async def market():
    return {"title": "Market", "subtitle": "Under Construction"}
