"""Minimal repro: instantiate the real GameUI and print the full traceback."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ursina import Ursina, camera, color, invoke  # noqa: E402
from utils.inventory import Inventory  # noqa: E402
from utils.crafting import CraftingSystem  # noqa: E402
from utils.game_ui import GameUI  # noqa: E402

app = Ursina()
inv = Inventory()
craft = CraftingSystem()

try:
    ui = GameUI(inv, craft)
    print("GameUI OK:", ui.name, flush=True)
except Exception:
    import traceback
    traceback.print_exc()
    print("REPRO_FAILED", flush=True)
    import application  # noqa: E402

    application.quit()
