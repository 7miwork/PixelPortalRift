"""Focused: print the running parent_setter + test exact GameUI construction."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import ursina.entity as eu
import inspect

src = inspect.getsource(eu.Entity.parent_setter)
print("===== RUNNING parent_setter =====", flush=True)
print(src, flush=True)
print("===== END source =====", flush=True)

from ursina import Ursina, camera, color, invoke  # noqa: E402
from utils.inventory import Inventory  # noqa: E402
from utils.crafting import CraftingSystem  # noqa: E402
from utils.game_ui import GameUI  # noqa: E402

app = Ursina()
print("camera.ui is Entity:", isinstance(camera.ui, eu.Entity), flush=True)

try:
    ui = GameUI(Inventory(), CraftingSystem())
    print("GameUI OK:", ui.name, flush=True)
except Exception:
    import traceback
    traceback.print_exc()
    print("REPRO_FAILED", flush=True)
finally:
    from ursina import application  # noqa: E402
    application.quit()
