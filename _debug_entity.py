"""Inspect the running Entity parent mechanism + test construction."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import ursina.entity as eu
import inspect

print("parent_setter source:\n", inspect.getsource(eu.Entity.parent_setter), flush=True)
print("-------", flush=True)

from ursina import Ursina, camera, color, invoke  # noqa: E402
from utils.inventory import Inventory  # noqa: E402
from utils.crafting import CraftingSystem  # noqa: E402
from utils.game_ui import GameUI  # noqa: E402

app = Ursina()
print("camera.ui type:", type(camera.ui), flush=True)

# reproduce step by step
ent = eu.Entity()
print("plain entity parent:", ent.parent, flush=True)
try:
    ent2 = eu.Entity(parent=camera.ui, name="probe")
    print("Entity(parent=camera.ui) OK:", ent2.parent, flush=True)
except Exception as exc:
    print("Entity(parent=camera.ui) FAILED:", type(exc).__name__, exc, flush=True)

from ursina import Entity as UEntity

try:
    ui = UEntity(parent=camera.ui, name="game_ui")
    print("UEntity(parent=camera.ui) OK", flush=True)
except Exception as exc:
    print("UEntity(parent=camera.ui) FAILED:", type(exc).__name__, exc, flush=True)

try:
    e2 = eu.Entity(parent=camera, name="probe2")
    print("Entity(parent=camera) OK:", e2.parent, flush=True)
except Exception as exc:
    print("Entity(parent=camera) FAILED:", type(exc).__name__, exc, flush=True)

from ursina import application

application.quit()
