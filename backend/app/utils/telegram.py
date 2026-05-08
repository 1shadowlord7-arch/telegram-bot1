from __future__ import annotations
from aiogram.types import User, ChatMember, Chat, Message
from .text import safe_html

def display_name(user: User | None) -> str:
    if not user:
        return "Unknown"
    name = (user.first_name or "").strip()
    if user.last_name:
        name = f"{name} {user.last_name}".strip()
    return name or user.username or str(user.id)

def mention(user_id: int, name: str) -> str:
    return f'<a href="tg://user?id={user_id}">{safe_html(name)}</a>'

def username_handle(username: str | None) -> str:
    return f"@{username}" if username else "no_username"

def is_admin_status(status: str) -> bool:
    return status in {"administrator", "creator"}

def is_privileged(chat_member: ChatMember) -> bool:
    return is_admin_status(chat_member.status)

def chat_label(chat: Chat | Message | None) -> str:
    if chat is None:
        return "unknown"
    c = chat.chat if isinstance(chat, Message) else chat
    return c.title or c.username or str(c.id)
