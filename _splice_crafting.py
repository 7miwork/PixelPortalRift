"""Temporäres Splice-Skript: entfernt pygame-Methoden aus crafting.py."""
from pathlib import Path

p = Path(__file__).parent / "utils" / "crafting.py"
text = p.read_text(encoding="utf-8")

# 1) Imports: pygame + Bildschirmgrößen raus
text = text.replace(
    "import pygame\nfrom utils.constants import CRAFTING_RECIPES, SCREEN_WIDTH, SCREEN_HEIGHT\n",
    "from utils.constants import CRAFTING_RECIPES\n",
)

# 2) Docstring-Hinweis an die 3D-UI anpassen
text = text.replace(
    "WICHTIG: Die Darstellung (3-Zeilen-Boxen) ist bereits fertig und darf nicht\n"
    "verändert werden.",
    "WICHTIG: Dieses Modul ist reine Spiellogik – KEIN pygame. Die Darstellung\n"
    "(Rezeptliste, Klick-Behandlung) übernimmt die Ursina-UI in\n"
    "utils/game_ui.py; das Layout (3-Zeilen-Boxen) bleibt dabei gleich.",
)

lines = text.splitlines(keepends=True)


def find(prefix, start=0):
    for i in range(start, len(lines)):
        if lines[i].startswith(prefix):
            return i
    raise SystemExit(f"nicht gefunden: {prefix!r}")


# 3) draw() und handle_click() komplett entfernen
a = find("    def draw(self, screen, asset_loader, inventory):")
# handle_click folgt direkt auf draw; Datei-Ende danach
lines[a:] = ["\n"]

p.write_text("".join(lines), encoding="utf-8")
print("OK: crafting.py gespliced")