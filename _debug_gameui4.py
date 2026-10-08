"""Read the exact GameUI init + print MRO and parent setter identity."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import ursina.entity as eu
import ursina.ursinastuff as us
import utils.game_ui as gui

print("=== game_ui.py GameUI region (450-470) ===")
with open(ROOT / "utils/game_ui.py", encoding="utf-8") as fh:
    lines = fh.readlines()
for n in range(450, 476):
    print("%4d: %s" % (n + 1, lines[n]), end="")

print("\n=== MRO ===")
for c in gui.GameUI.__mro__:
    print(" ", c)

print("\nparent_setter id:", id(eu.Entity.parent_setter))
print("GameUI.__init__ globals 'Entity':", gui.GameUI.__init__.__globals__.get("Entity") is eu.Entity)

from ursina import Ursina, camera, color, invoke  # noqa: E402
from utils.inventory import Inventory  # noqa: E402
from utils.crafting import CraftingSystem  # noqa: E402

app = Ursina()
inv = Inventory()
craft = CraftingSystem()

# monkeypatched trace back at the real parent_setter used by GameUI
real = eu.Entity.parent_setter


def traced(self, value):
    print("TRACE parent_setter: value =", type(value).__name__,
          "has _children:", hasattr(value, "_children"), flush=True)
    return real(self, value)


eu.Entity.parent_setter = traced

try:
    ui = gui.GameUI(inv, craft)
    print("GameUI OK:", ui.name, flush=True)
except Exception:
    import traceback
    traceback.print_exc()
    print("REPRO_FAILED", flush=True)
finally:
    from ursina import application  # noqa: E402
    application.quit()
