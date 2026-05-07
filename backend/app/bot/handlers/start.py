from __future__ import annotations
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from app.bot.keyboards import main_menu_keyboard, start_menu_inline
from app.core.config import get_settings

router = Router()
settings = get_settings()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "✨ Premium Telegram bot + Mini App is ready.",
        reply_markup=main_menu_keyboard(),
    )

@router.message(F.text == "➕ Add to Group")
async def add_to_group(message: Message):
    await message.answer(
        "Use the button below to add the bot to a group.",
        reply_markup=start_menu_inline(settings.bot_username, settings.updates_channel),
    )

@router.message(F.text == "👑 Owner")
async def owner(message: Message):
    await message.answer(
        f"Owner DM: https://t.me/{settings.owner_username}",
        disable_web_page_preview=True,
    )

@router.message(F.text == "📢 Join Updates Channel")
async def updates(message: Message):
    await message.answer(
        f"Updates channel: https://t.me/{settings.updates_channel.lstrip('@')}",
        disable_web_page_preview=True,
    )

@router.callback_query(F.data.startswith("ui:"))
async def ui_router(call: CallbackQuery):
    choice = call.data.split(":", 1)[1]
    await call.answer()
    labels = {
        "group_settings": "Open Group Settings from the Mini App menu.",
        "games": "Open Games from the Mini App menu.",
        "friends": "Open Friends from the Mini App menu.",
        "files": "Linked Files is coming soon.",
        "market": "Market is under construction.",
    }
    await call.message.answer(labels.get(choice, "Ready."))
