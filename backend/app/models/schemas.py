from __future__ import annotations
from datetime import datetime
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field

class TelegramUser(BaseModel):
    user_id: int
    username: Optional[str] = None
    first_name: str = ""
    last_name: Optional[str] = None
    photo_url: Optional[str] = None
    language_code: Optional[str] = None
    last_active_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class GroupConfig(BaseModel):
    group_id: int
    title: Optional[str] = None
    owner_id: Optional[int] = None
    admins_only: bool = True
    connected_channel_id: Optional[int] = None
    connected_channel_username: Optional[str] = None
    connected_channel_title: Optional[str] = None
    request_limit: int = 1
    warning_limit: int = 3
    spam_enabled: bool = False
    spam_limit: int = 3
    spam_action: Literal["mute", "ban"] = "mute"
    filter_words: list[str] = Field(default_factory=list)
    filter_action: Literal["mute", "ban"] = "mute"
    warn_action: Literal["mute", "ban"] = "mute"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ChannelConfig(BaseModel):
    channel_id: int
    group_id: Optional[int] = None
    username: Optional[str] = None
    title: Optional[str] = None
    indexed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Friendship(BaseModel):
    user_id: int
    friend_id: int
    status: Literal["pending", "accepted", "blocked"] = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    blocked_by: Optional[int] = None

class WarningItem(BaseModel):
    group_id: int
    user_id: int
    warning_count: int = 0
    reason: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class RequestItem(BaseModel):
    group_id: int
    requester_id: int
    text: str
    normalized_text: str
    status: Literal["open", "matched", "fulfilled", "rejected"] = "open"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class GameSession(BaseModel):
    session_id: str
    game_type: Literal["rps", "tictactoe"]
    chat_id: int
    challenger_id: int
    opponent_id: int
    status: Literal["pending", "active", "finished", "declined"] = "pending"
    board: list[str] = Field(default_factory=lambda: [""] * 9)
    turn_user_id: Optional[int] = None
    rps_moves: dict[str, str] = Field(default_factory=dict)
    winner_id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(default_factory=datetime.utcnow)

class LogEntry(BaseModel):
    group_id: int
    action: str
    target_user_id: Optional[int] = None
    admin_user_id: Optional[int] = None
    reason: Optional[str] = None
    meta: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
