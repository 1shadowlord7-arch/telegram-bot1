from __future__ import annotations
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Add to Group"), KeyboardButton(text="⚙️ Group Settings")],
            [KeyboardButton(text="🕹 Play Games")],
            [KeyboardButton(text="👥 Friends")],
            [KeyboardButton(text="📂 Linked Files")],
            [KeyboardButton(text="🛒 Market")],
            [KeyboardButton(text="👑 Owner"), KeyboardButton(text="📢 Join Updates Channel")],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )

def start_menu_inline(bot_username: str, updates_channel: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Add to Group", url=f"https://t.me/{bot_username}?startgroup=true")
    kb.button(text="⚙️ Group Settings", callback_data="ui:group_settings")
    kb.button(text="🕹 Play Games", callback_data="ui:games")
    kb.button(text="👥 Friends", callback_data="ui:friends")
    kb.button(text="📂 Linked Files", callback_data="ui:files")
    kb.button(text="🛒 Market", callback_data="ui:market")
    kb.button(text="👑 Owner", url=f"https://t.me/{bot_username}")
    kb.button(text="📢 Join Updates Channel", url=f"https://t.me/{updates_channel.lstrip('@')}")
    kb.adjust(2, 1, 1, 1, 2)
    return kb.as_markup()

def admin_permission_error() -> str:
    return "⚠️ You need to be an admin to access this section."

def bot_permission_error() -> str:
    return "⚠️ I need admin permissions in this group first."
