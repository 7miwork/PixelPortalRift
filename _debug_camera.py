"""Print the camera globals used for UI parenting."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ursina import Ursina, camera, color, invoke  # noqa: E402
from ursina import application  # noqa: E402

app = Ursina()
print("camera type:", type(camera), flush=True)
print("camera attrs:", [a for a in dir(camera) if not a.startswith("_")], flush=True)
print("hasattr ui:", hasattr(camera, "ui"), flush=True)
try:
    ui = camera.ui
    print("camera.ui type:", type(ui), flush=True)
except Exception as exc:
    print("camera.ui FAILED:", exc, flush=True)

from utils.game_ui import GameUI  # noqa: E402

ui = GameUI(Inventory(), CraftingSystem())