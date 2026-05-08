from __future__ import annotations
from fastapi import APIRouter, Request, Header, HTTPException
from aiogram.types import Update
from app.bot.app import create_dispatcher, create_bot
from app.core.config import get_settings

router = APIRouter(tags=["telegram"])
settings = get_settings()
bot = create_bot()
dp = create_dispatcher()

@router.post("/telegram/webhook")
async def telegram_webhook(request: Request, x_telegram_bot_api_secret_token: str | None = Header(default=None)):
    if x_telegram_bot_api_secret_token != settings.bot_webhook_secret:
        raise HTTPException(401, "Invalid webhook secret")
    data = await request.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot, update)
    return {"ok": True}
