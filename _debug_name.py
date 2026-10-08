"""Test the exact GameUI super().__init__ call."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import ursina.entity as eu
import inspect

from ursina import Ursina, camera, color, invoke  # noqa: E402
from ursina import Entity as UEntity  # noqa: E402
from utils.inventory import Inventory  # noqa: E402
from utils.crafting import CraftingSystem  # noqa: E402

app = Ursina()

try:
    ent = UEntity(parent=camera.ui, name="game_ui")
    print("UEntity(parent=camera.ui, name=...) OK:", ent.parent, ent.name, flush=True)
except Exception:
    import traceback
    traceback.print_exc()
    print("UEntity(...name) FAILED", flush=True)

try:
    ent = eu.Entity(parent=camera.ui, name="game_ui")
    print("eu.Entity(...) OK", flush=True)
except Exception:
    import traceback
    traceback.print_exc()
    print("eu.Entity(...name) FAILED", flush=True)

# variant: no name
try:
    ent = UEntity(parent=camera.ui)
    print("UEntity(parent=camera.ui) OK", flush=True)
except Exception:
    import traceback
    traceback.print_exc()
    print("UEntity(...no name) FAILED", flush=True)

from ursina import application  # noqa: E402
application.quit()
