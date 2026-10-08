"""Instrument the real GameUI construction without changing game_ui.py."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import ursina.entity as eu
import ursina.ursinastuff as us

# capture the original parent setter
orig = eu.Entity.parent_setter


def traced(self, value):
    print("parent_setter CALLED: value =", type(value), getattr(value, "name", "?"),
          "has _children:", hasattr(value, "_children"), flush=True)
    return orig(self, value)


eu.Entity.parent_setter = traced

from utils.inventory import Inventory  # noqa: E402
from utils.crafting import CraftingSystem  # noqa: E402
from utils.game_ui import GameUI  # noqa: E402

from ursina import Ursina, camera, application  # noqa: E402

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
finally:
    application.quit()
