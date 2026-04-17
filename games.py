
from typing import Optional

import rps_game
import ttt_game

GAME_MODULES = {
    "ttt": ttt_game,
    "rps": rps_game,
}

GAME_TITLES = {
    "ttt": "Tic Tac Toe",
    "rps": "Rock Paper Scissors",
}


def list_games():
    return list(GAME_MODULES.keys())


def game_title(game_type: str) -> str:
    return GAME_TITLES.get(game_type, game_type.upper())


def new_game(game_type: str, challenger_id: int, target_id: int, group_id: int | None = None) -> str:
    module = GAME_MODULES[game_type]
    return module.new_game(challenger_id, target_id, group_id)


def get_game(game_type: str, game_id: str) -> Optional[dict]:
    module = GAME_MODULES.get(game_type)
    if not module:
        return None
    return module.get(game_id)


def handle_move(game_type: str, game_id: str, user_id: int, value):
    module = GAME_MODULES.get(game_type)
    if not module:
        return None, "Unknown game type."
    return module.make_move(game_id, user_id, value)


def result_text(game_type: str, game_id: str) -> str:
    module = GAME_MODULES.get(game_type)
    if not module:
        return "Unknown game type."
    return module.result_text(game_id)


def room_state(game_type: str, game_id: str):
    module = GAME_MODULES.get(game_type)
    if not module or not hasattr(module, "room_state"):
        return None
    return module.room_state(game_id)
