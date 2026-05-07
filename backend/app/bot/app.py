from __future__ import annotations
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from app.core.config import get_settings
from app.bot.handlers.start import router as start_router
from app.bot.handlers.groups import router as groups_router
from app.bot.handlers.friends import router as friends_router
from app.bot.handlers.games import router as games_router

settings = get_settings()

def create_bot() -> Bot:
    return Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(start_router)
    dp.include_router(groups_router)
    dp.include_router(friends_router)
    dp.include_router(games_router)
    return dp
