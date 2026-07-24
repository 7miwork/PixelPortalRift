"""
tools/export_block_textures.py – Exportiert Block-Texturen als PNG-Dateien
============================================================================

Dieses Skript erzeugt für jeden Block in BLOCK_PROPERTIES (utils/constants.py)
eine echte PNG-Datei unter assets/blocks/<block_name>.png.

Die Texturen werden mit exakt der gleichen Zeichenlogik erstellt, die auch
AssetLoader.create_block_texture() im Spiel verwendet. Dadurch sehen die
exportierten Bilder 1:1 so aus wie die bisher prozedural generierten Texturen.

Anschließend können die PNG-Dateien einzeln durch eigene Pixel-Art ersetzt
werden. Der bereits vorhandene Fallback-Mechanismus in asset_loader.py
(load_block_textures()) sorgt automatisch dafür, dass bei fehlender oder
fehlerhafter Datei weiterhin die generierte Textur verwendet wird.

Ausführung:
    python tools/export_block_textures.py

Das Skript muss aus dem Projekt-Root-Verzeichnis ausgeführt werden.
Hinweis: Dieses Skript ist NUR für die einmalige manuelle Ausführung gedacht.
Es wird NICHT automatisch beim Spielstart aufgerufen.
"""

import os
import sys

# ----- Projekt-Root zum sys.path hinzufügen -----
# Damit die Imports aus dem utils/-Package funktionieren,
# ermitteln wir den übergeordneten Ordner von tools/ (= Projekt-Root)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# ----- Dummy-Video-Treiber setzen (bevor pygame importiert wird) -----
# Dadurch läuft das Skript auch ohne Bildschirm/Display,
# z.B. auf einem Server oder in einer Replit-Umgebung.
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
from utils.constants import BLOCK_PROPERTIES
from utils.asset_loader import AssetLoader


def main():
    """
    Hauptfunktion des Export-Skripts.
    
    Ablauf:
    1. pygame initialisieren (mit Dummy-Display)
    2. assets/blocks/-Ordner anlegen, falls nicht vorhanden
    3. Für jeden Block in BLOCK_PROPERTIES:
       - Wenn color=None (z.B. "air") → überspringen
       - Wenn PNG bereits existiert → überspringen (nicht überschreiben)
       - Sonst: Textur via AssetLoader.create_block_texture() erzeugen und speichern
    4. Zusammenfassung in der Konsole ausgeben
    """
    
    # ----- pygame initialisieren -----
    # Ein minimales Display wird benötigt, damit Surface-Operationen
    # und pygame.image.save() zuverlässig funktionieren.
    pygame.init()
    pygame.display.set_mode((1, 1))
    
    # ----- AssetLoader-Instanz erzeugen -----
    # Wir nutzen die bereits vorhandene create_block_texture()-Methode,
    # damit die exportierten Bilder exakt so aussehen wie im Spiel.
    # Wichtig: load_all_assets() rufen wir NICHT auf, da wir nur die
    # create_block_texture()-Methode brauchen und keine Texturen laden wollen.
    asset_loader = AssetLoader()
    
    # ----- Zielverzeichnis festlegen und anlegen -----
    blocks_dir = os.path.join(_PROJECT_ROOT, "assets", "blocks")
    os.makedirs(blocks_dir, exist_ok=True)
    
    # ----- Zähler für die Zusammenfassung -----
    count_exported = 0          # Anzahl neu erzeugter Dateien
    count_skipped_existing = 0  # Anzahl übersprungener (weil bereits vorhanden)
    count_skipped_nocolor = 0   # Anzahl übersprungener (weil color=None)
    
    # ----- Alle Blöcke durchgehen -----
    for block_name, props in BLOCK_PROPERTIES.items():
        # Block ohne Farbe (z.B. "air") überspringen – kein Bild nötig
        if props["color"] is None:
            count_skipped_nocolor += 1
            continue
        
        # Ziel-Pfad für die PNG-Datei
        png_path = os.path.join(blocks_dir, f"{block_name}.png")
        
        # Bereits vorhandene Datei nicht überschreiben
        # (falls Nic schon von Hand eigene Pixel-Art eingefügt hat)
        if os.path.exists(png_path):
            count_skipped_existing += 1
            continue
        
        # Textur mit der exakt gleichen Logik wie im Spiel erzeugen
        texture_surface = asset_loader.create_block_texture(block_name, props["color"])
        
        # Als PNG speichern
        pygame.image.save(texture_surface, png_path)
        count_exported += 1
        
        print(f"  [EXPORT] {block_name}.png")
    
    # ----- Zusammenfassung ausgeben -----
    print("\n" + "=" * 50)
    print("  EXPORT ZUSAMMENFASSUNG")
    print("=" * 50)
    print(f"  Neu erzeugte Dateien:     {count_exported}")
    print(f"  Übersprungen (vorhanden): {count_skipped_existing}")
    print(f"  Übersprungen (kein Bild): {count_skipped_nocolor}")
    print(f"  Gesamt Blöcke:            {len(BLOCK_PROPERTIES)}")
    print("=" * 50)
    print(f"\nZielverzeichnis: {blocks_dir}")
    print("Die exportierten PNGs können jetzt einzeln bearbeitet werden.")
    print("Der Fallback-Mechanismus in asset_loader.py bleibt aktiv.")
    
    # pygame beenden
    pygame.quit()


if __name__ == "__main__":
    main()