
import uuid
from typing import Dict, Optional, Tuple

ACTIVE_RPS: Dict[str, dict] = {}
VALID_CHOICES = {"rock", "paper", "scissors"}


def new_game(challenger_id: int, target_id: int, group_id: int | None = None) -> str:
    game_id = uuid.uuid4().hex[:10]
    ACTIVE_RPS[game_id] = {
        "id": game_id,
        "type": "rps",
        "group_id": group_id,
        "players": [challenger_id, target_id],
        "choices": {},
        "winner": None,
        "ended": False,
        "result": "",
    }
    return game_id


def get(game_id: str) -> Optional[dict]:
    return ACTIVE_RPS.get(game_id)


def _resolve(game: dict) -> str:
    a, b = game["players"]
    ca = game["choices"].get(a)
    cb = game["choices"].get(b)
    if not ca or not cb:
        return "Waiting for both players to choose."
    if ca == cb:
        game["ended"] = True
        game["winner"] = "draw"
        game["result"] = f"Draw: both chose {ca}."
        return game["result"]

    beats = {"rock": "scissors", "scissors": "paper", "paper": "rock"}
    if beats[ca] == cb:
        game["winner"] = a
        game["result"] = f"Player 1 wins: {ca} beats {cb}."
    else:
        game["winner"] = b
        game["result"] = f"Player 2 wins: {cb} beats {ca}."
    game["ended"] = True
    return game["result"]


def make_move(game_id: str, user_id: int, choice: str) -> Tuple[Optional[dict], str]:
    game = ACTIVE_RPS.get(game_id)
    if not game or game["ended"]:
        return None, "Game not active."
    if user_id not in game["players"]:
        return None, "You are not part of this game."
    choice = (choice or "").strip().lower()
    if choice not in VALID_CHOICES:
        return None, "Choose rock, paper, or scissors."

    game["choices"][user_id] = choice
    note = _resolve(game)
    return game, note


def result_text(game_id: str) -> str:
    game = ACTIVE_RPS.get(game_id)
    if not game:
        return "Game not found."
    a, b = game["players"]
    ca = game["choices"].get(a, "—")
    cb = game["choices"].get(b, "—")
    if game["ended"]:
        status = "Draw" if game["winner"] == "draw" else f"Winner: {game['winner']}"
    else:
        status = "Waiting for choices"
    return f"<b>Rock Paper Scissors</b>\n\nPlayer 1: {ca}\nPlayer 2: {cb}\n\n{status}"


def room_state(game_id: str) -> Optional[dict]:
    game = ACTIVE_RPS.get(game_id)
    if not game:
        return None
    return {
        "game_id": game_id,
        "type": "rps",
        "players": game["players"],
        "choices": game["choices"],
        "ended": game["ended"],
        "winner": game["winner"],
        "result": game["result"],
    }
