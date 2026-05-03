
import uuid
from typing import Dict, Optional, Tuple

ACTIVE_TTT: Dict[str, dict] = {}


def new_game(challenger_id: int, target_id: int, group_id: int | None = None) -> str:
    game_id = uuid.uuid4().hex[:10]
    ACTIVE_TTT[game_id] = {
        "id": game_id,
        "type": "ttt",
        "group_id": group_id,
        "players": [challenger_id, target_id],
        "symbols": {challenger_id: "X", target_id: "O"},
        "board": [" "] * 9,
        "turn": challenger_id,
        "winner": None,
        "ended": False,
    }
    return game_id


def get(game_id: str) -> Optional[dict]:
    return ACTIVE_TTT.get(game_id)


def winner(board):
    lines = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6),
    ]
    for a, b, c in lines:
        if board[a] != " " and board[a] == board[b] == board[c]:
            return board[a]
    if " " not in board:
        return "draw"
    return None


def symbol_for(game: dict, user_id: int) -> str:
    return game["symbols"][user_id]


def make_move(game_id: str, user_id: int, cell: int) -> Tuple[Optional[dict], str]:
    game = ACTIVE_TTT.get(game_id)
    if not game or game["ended"]:
        return None, "Game not active."
    if user_id not in game["players"]:
        return None, "You are not part of this game."
    if game["turn"] != user_id:
        return None, "Not your turn."
    if cell < 0 or cell > 8:
        return None, "Invalid cell."
    if game["board"][cell] != " ":
        return None, "Cell already used."

    game["board"][cell] = symbol_for(game, user_id)
    w = winner(game["board"])
    if w:
        game["ended"] = True
        game["winner"] = w
        if w == "draw":
            return game, "Draw."
        return game, f"Winner: {w}"

    game["turn"] = game["players"][1] if game["turn"] == game["players"][0] else game["players"][0]
    return game, "Move accepted."


def result_text(game_id: str) -> str:
    game = ACTIVE_TTT.get(game_id)
    if not game:
        return "Game not found."

    board = game["board"]
    rows = []
    for r in range(3):
        rows.append(" | ".join(board[r * 3:(r + 1) * 3]).replace(" ", "·"))
    board_txt = "\n---------\n".join(rows)
    if game["ended"]:
        status = "Draw" if game["winner"] == "draw" else f"Winner: {game['winner']}"
    else:
        status = f"Turn: {game['symbols'][game['turn']]}"
    return f"<b>Tic Tac Toe</b>\n\n<pre>{board_txt}</pre>\n{status}"


def room_state(game_id: str) -> Optional[dict]:
    game = ACTIVE_TTT.get(game_id)
    if not game:
        return None
    return {
        "game_id": game_id,
        "type": "ttt",
        "players": game["players"],
        "turn": game["turn"],
        "ended": game["ended"],
        "winner": game["winner"],
        "board": game["board"],
        "symbols": game["symbols"],
    }
