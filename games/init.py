from importlib import import_module
from pathlib import Path

GAME_REGISTRY = {}

def load_games():
    GAME_REGISTRY.clear()
    folder = Path(__file__).parent

    for file in folder.glob("*.py"):
        if file.stem == "__init__":
            continue

        module = import_module(f"games.{file.stem}")
        if hasattr(module, "GAME_KEY") and hasattr(module, "GAME_NAME") and hasattr(module, "render_page"):
            GAME_REGISTRY[module.GAME_KEY] = module

    return GAME_REGISTRY
