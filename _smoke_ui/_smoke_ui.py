"""UI-only smoke test: builds the full UI tree (no world) and quits."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ursina import Ursina, application, color, invoke  # noqa: E402
from utils.inventory import Inventory  # noqa: E402
from utils.crafting import CraftingSystem  # noqa: E402
from utils.game_ui import GameUI, IconLibrary  # noqa: E402


def main():
    app = Ursina()
    inventory = Inventory()
    crafting = CraftingSystem()
    ui = GameUI(inventory, crafting)
    invoke(application.quit, delay=0.5)
    app.run()
    print("UI_SMOKE_OK", flush=True)


if __name__ == "__main__":
    main()
