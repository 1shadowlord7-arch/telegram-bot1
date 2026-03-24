import asyncio
import uuid
import time
import random
import os
import threading

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import aiosqlite

from fastapi import FastAPI
import uvicorn

# ---------------- CONFIG ---------------- #

BOT_TOKEN = os.getenv("8364493634:AAFMKkwVtKeenFpOW4cWlu7jiSNhgQ9qZRc")
BOT_USERNAME = os.getenv("@CreatorSuiteBot")

DB_NAME = "bot.db"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ---------------- WEB SERVER (KEEP ALIVE) ---------------- #

app = FastAPI()

@app.get("/")
async def home():
    return {"status": "alive"}

def run_web():
    uvicorn.run(app, host="0.0.0.0", port=10000)

threading.Thread(target=run_web).start()

# ---------------- DATABASE ---------------- #

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS pickers (
            id TEXT PRIMARY KEY,
            owner_id INTEGER,
            message TEXT,
            created_at INTEGER,
            ended INTEGER DEFAULT 0,
            winner TEXT
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS participants (
            picker_id TEXT,
            user_id INTEGER,
            username TEXT
        )
        """)
        await db.commit()

# ---------------- STATE (simple memory) ---------------- #

user_state = {}

# ---------------- START ---------------- #

@dp.message(Command("start"))
async def start(message: types.Message):
    args = message.text.split()

    if len(args) > 1 and args[1].startswith("join_"):
        picker_id = args[1].split("_")[1]
        await join_picker(message, picker_id)
        return

    await message.answer("Use /create_picker")

# ---------------- CREATE PICKER ---------------- #

@dp.message(Command("create_picker"))
async def create_picker(message: types.Message):
    user_state[message.from_user.id] = "waiting_picker"
    await message.answer("Send your picker message:")

@dp.message(F.text)
async def handle_text(message: types.Message):
    if user_state.get(message.from_user.id) == "waiting_picker":
        await save_picker(message)
        user_state.pop(message.from_user.id)

async def save_picker(msg: types.Message):
    picker_id = str(uuid.uuid4())[:8]
    now = int(time.time())

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO pickers VALUES (?, ?, ?, ?, 0, NULL)",
            (picker_id, msg.from_user.id, msg.text, now)
        )
        await db.commit()

    link = f"https://t.me/{BOT_USERNAME}?start=join_{picker_id}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Pick Winner 🎯", callback_data=f"pick_{picker_id}")]
    ])

    await msg.answer(f"✅ Picker created\n\n{link}", reply_markup=kb)

# ---------------- JOIN ---------------- #

async def join_picker(message, picker_id):
    user = message.from_user
    username = user.username or user.full_name

    async with aiosqlite.connect(DB_NAME) as db:
        cur = await db.execute(
            "SELECT * FROM participants WHERE picker_id=? AND user_id=?",
            (picker_id, user.id)
        )
        if await cur.fetchone():
            await message.answer("Already joined!")
            return

        await db.execute(
            "INSERT INTO participants VALUES (?, ?, ?)",
            (picker_id, user.id, username)
        )
        await db.commit()

    count = await get_count(picker_id)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"👥 {count}", callback_data="ignore")],
        [InlineKeyboardButton(text="Leave ❌", callback_data=f"leave_{picker_id}")]
    ])

    await message.answer("✅ Joined!", reply_markup=kb)

# ---------------- COUNT ---------------- #

async def get_count(picker_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cur = await db.execute(
            "SELECT COUNT(*) FROM participants WHERE picker_id=?",
            (picker_id,)
        )
        return (await cur.fetchone())[0]

# ---------------- LEAVE ---------------- #

@dp.callback_query(F.data.startswith("leave_"))
async def leave(call: types.CallbackQuery):
    picker_id = call.data.split("_")[1]

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "DELETE FROM participants WHERE picker_id=? AND user_id=?",
            (picker_id, call.from_user.id)
        )
        await db.commit()

    await call.answer("You left!")

# ---------------- PICK WINNER ---------------- #

@dp.callback_query(F.data.startswith("pick_"))
async def pick(call: types.CallbackQuery):
    picker_id = call.data.split("_")[1]

    async with aiosqlite.connect(DB_NAME) as db:
        cur = await db.execute(
            "SELECT owner_id, created_at, ended FROM pickers WHERE id=?",
            (picker_id,)
        )
        data = await cur.fetchone()

        if not data:
            await call.answer("Not found")
            return

        owner_id, created, ended = data

        if call.from_user.id != owner_id:
            await call.answer("Not yours")
            return

        if ended:
            await call.answer("Already ended")
            return

        if time.time() - created > 48 * 3600:
            await call.answer("Expired")
            return

        cur = await db.execute(
            "SELECT username FROM participants WHERE picker_id=?",
            (picker_id,)
        )
        users = await cur.fetchall()

        if not users:
            await call.message.answer("No participants")
            return

        winner = random.choice(users)[0]

        await db.execute(
            "UPDATE pickers SET ended=1, winner=? WHERE id=?",
            (winner, picker_id)
        )
        await db.commit()

    await call.message.answer(f"🎉 Winner: @{winner}")

# ---------------- AUTO END ---------------- #

async def auto_end():
    while True:
        now = int(time.time())

        async with aiosqlite.connect(DB_NAME) as db:
            cur = await db.execute(
                "SELECT id FROM pickers WHERE ended=0 AND created_at<?",
                (now - 48*3600,)
            )
            expired = await cur.fetchall()

            for (pid,) in expired:
                await db.execute(
                    "UPDATE pickers SET ended=1 WHERE id=?",
                    (pid,)
                )

            await db.commit()

        await asyncio.sleep(60)

# ---------------- MAIN ---------------- #

async def main():
    await init_db()
    asyncio.create_task(auto_end())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
