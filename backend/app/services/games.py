from __future__ import annotations
from datetime import datetime, timedelta
from uuid import uuid4
from app.db.mongo import get_db

def new_session_id() -> str:
    return uuid4().hex

async def create_challenge(chat_id: int, challenger_id: int, opponent_id: int, game_type: str):
    db = get_db()
    session = {
        "session_id": new_session_id(),
        "game_type": game_type,
        "chat_id": chat_id,
        "challenger_id": challenger_id,
        "opponent_id": opponent_id,
        "status": "pending",
        "board": [""] * 9,
        "turn_user_id": challenger_id if game_type == "tictactoe" else None,
        "rps_moves": {},
        "winner_id": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=2),
    }
    await db.games.insert_one(session)
    return session

async def get_session(session_id: str):
    return await get_db().games.find_one({"session_id": session_id})

async def set_session(session_id: str, **kwargs):
    kwargs["updated_at"] = datetime.utcnow()
    await get_db().games.update_one({"session_id": session_id}, {"$set": kwargs})

async def finish_ttt(session: dict, winner_id: int | None):
    await set_session(session["session_id"], status="finished", winner_id=winner_id)

def ttt_winner(board: list[str]) -> str | None:
    wins = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
    for a,b,c in wins:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    return None
