"""
utils/asset_loader.py – Lädt Bilder und erstellt Texturen
============================================================

Dieses Modul ist für ALLES rund um Grafiken zuständig:
- Es lädt echte PNG-Bilddateien aus dem assets/-Ordner, falls vorhanden.
- Falls keine PNG-Datei existiert, wird die Textur selbst gezeichnet
  (mit pygame-Befehlen wie draw.rect, draw.circle, draw.line usw.).
- Das betrifft: Block-Texturen, Item-Texturen, Gegner-Texturen und die Spieler-Grafik.

WICHTIG: Der Fallback-Mechanismus (keine PNG = selbst zeichnen) ist absichtlich so
entworfen. Wenn du eigene Pixel-Art für einen Block erstellen willst, legst du einfach
eine PNG-Datei unter assets/blocks/<block_name>.png an. Der Loader erkennt das
automatisch und verwendet deine Datei statt der gezeichneten Version.
"""

import pygame
import os
from PIL import Image
from utils.constants import TILE_SIZE, BLOCK_PROPERTIES, ITEM_PROPERTIES, MOB_PROPERTIES


class AssetLoader:
    """
    Der AssetLoader lädt alle Grafiken für das Spiel.
    
    Wichtige Attribute:
        block_textures: Dictionary mit Block-Name → pygame-Surface (Textur)
        item_textures:  Dictionary mit Item-Name → pygame-Surface
        mob_textures:   Dictionary mit Gegner-Name → pygame-Surface
        player_texture: Einzelne Surface für den Spieler
        assets_path:    Pfad zum assets/-Ordner (standardmäßig "assets")
    """
    
    def __init__(self):
        """Initialisiert den AssetLoader mit leeren Textur-Dictionaries."""
        self.block_textures = {}
        self.item_textures = {}
        self.mob_textures = {}
        self.player_texture = None
        self.assets_path = "assets"
        
    def load_all_assets(self):
        """
        Lädt ALLE Grafiken auf einmal.
        Diese Methode wird einmal beim Spielstart aufgerufen.
        """
        self.load_block_textures()
        self.load_item_textures()
        self.load_mob_textures()
        self.load_player_texture()
        
    def resize_image(self, image_path, target_size):
        """
        Lädt eine Bilddatei und skaliert sie auf die gewünschte Größe.
        
        Verwendet die PIL-Bibliothek (Pillow) für hochwertige Skalierung.
        
        :param image_path: Pfad zur PNG-Datei
        :param target_size: (Breite, Höhe) in Pixeln
        :return: pygame-Surface oder None bei Fehler
        """
        try:
            # PIL öffnet die Datei und skaliert sie
            img = Image.open(image_path)
            img = img.convert("RGBA")  # Stelle sicher, dass das Bild Alpha-Kanal hat
            img = img.resize(target_size, Image.Resampling.LANCZOS)  # LANCZOS = beste Qualität
            # Umwandlung von PIL → pygame
            mode = img.mode
            size = img.size
            data = img.tobytes()
            return pygame.image.fromstring(data, size, mode)
        except Exception as e:
            print(f"Fehler beim Laden von {image_path}: {e}")
            return None
    
    def create_colored_surface(self, color, size=(TILE_SIZE, TILE_SIZE)):
        """
        Erstellt eine einfarbige pygame-Oberfläche.
        
        :param color: RGB- oder RGBA-Farbe
        :param size: (Breite, Höhe) – standardmäßig ein Block
        :return: pygame-Surface
        """
        surface = pygame.Surface(size, pygame.SRCALPHA)
        if len(color) == 4:
            surface.fill(color)          # RGBA (mit Durchsichtigkeit)
        else:
            surface.fill((*color, 255))  # RGB → Alpha = 255 (undurchsichtig)
        return surface
    
    def create_block_texture(self, block_name, color):
        """
        Erzeugt eine Block-Textur durch Zeichnen mit pygame-Befehlen.
        
        Jeder Block-Typ hat sein eigenes Aussehen:
        - Die Grundfläche wird mit der Block-Farbe gefüllt.
        - Ein dünner Rand macht die Blöcke voneinander unterscheidbar.
        - Spezielle Blöcke (Erze, Kristalle, Wasser, etc.) bekommen
          zusätzliche Details (Kreise, Linien, Polygone).
        
        :param block_name: Name des Blocks (z.B. "grass", "stone")
        :param color: RGB- oder RGBA-Farbe aus BLOCK_PROPERTIES
        :return: pygame-Surface (32x32 Pixel)
        """
        surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        # Grundfläche mit der Block-Farbe füllen
        if len(color) == 4:
            surface.fill(color)
        else:
            surface.fill((*color, 255))
        
        # Dunklerer Rand um den Block (30 dunkler als die Grundfarbe)
        border_color = tuple(max(0, c - 30) for c in color[:3])
        pygame.draw.rect(surface, border_color, (0, 0, TILE_SIZE, TILE_SIZE), 1)
        
        # ---- Spezielle Details für bestimmte Blöcke ----
        if block_name == "crystal":
            # Kristall: weiße Linien, die wie Facetten aussehen
            pygame.draw.line(surface, (255, 255, 255), (8, 0), (16, TILE_SIZE), 2)
            pygame.draw.line(surface, (255, 255, 255), (24, 0), (16, TILE_SIZE), 2)
            pygame.draw.line(surface, (200, 200, 255), (16, 8), (8, 24), 2)
        elif block_name == "uranium":
            # Uran: grüne Kreise (leuchtend)
            pygame.draw.circle(surface, (0, 100, 0), (TILE_SIZE//2, TILE_SIZE//2), 6)
            pygame.draw.circle(surface, (0, 255, 0), (TILE_SIZE//2, TILE_SIZE//2), 3)
        elif block_name == "plutonium":
            # Plutonium: violette Kreise
            pygame.draw.circle(surface, (100, 50, 150), (TILE_SIZE//2, TILE_SIZE//2), 7)
            pygame.draw.circle(surface, (200, 150, 255), (TILE_SIZE//2, TILE_SIZE//2), 4)
        elif block_name == "reactor_core":
            # Reaktor-Kern: konzentrische gelbe Kreise (wie ein Ziel)
            pygame.draw.circle(surface, (255, 255, 200), (TILE_SIZE//2, TILE_SIZE//2), 10)
            pygame.draw.circle(surface, (255, 255, 100), (TILE_SIZE//2, TILE_SIZE//2), 6)
            pygame.draw.circle(surface, (255, 255, 0), (TILE_SIZE//2, TILE_SIZE//2), 3)
        elif block_name == "contaminated_stone":
            # Verseuchter Stein: grüne Punkte (Kontamination)
            pygame.draw.circle(surface, (50, 100, 50), (8, 8), 2)
            pygame.draw.circle(surface, (50, 100, 50), (24, 16), 2)
            pygame.draw.circle(surface, (50, 150, 50), (16, 24), 2)
        elif block_name == "obsidian":
            # Obsidian: dunkler Kreis in der Mitte
            pygame.draw.circle(surface, (100, 50, 200), (TILE_SIZE//2, TILE_SIZE//2), 5)
        elif block_name == "pearl_ore":
            # Perlen-Erz: heller rosa Kreis
            pygame.draw.circle(surface, (255, 220, 240), (TILE_SIZE//2, TILE_SIZE//2), 4)
        elif block_name == "amethyst":
            # Amethyst: Raute (Polygon mit 4 Ecken)
            pygame.draw.polygon(surface, (200, 150, 255), [(16, 4), (24, 16), (16, 28), (8, 16)])
        elif block_name == "ruby_ore":
            # Rubin-Erz: rote Raute
            pygame.draw.polygon(surface, (255, 50, 100), [(16, 4), (24, 16), (16, 28), (8, 16)])
        elif block_name == "emerald_ore":
            # Smaragd-Erz: grüne Raute
            pygame.draw.polygon(surface, (50, 255, 100), [(16, 4), (24, 16), (16, 28), (8, 16)])
        elif block_name == "diamond_ore":
            # Diamant-Erz: hellblaue Raute (etwas breiter)
            pygame.draw.polygon(surface, (200, 240, 255), [(16, 4), (28, 16), (16, 28), (4, 16)])
        elif block_name == "coral":
            # Koralle: orangefarbene Linien (wie Äste)
            pygame.draw.line(surface, (255, 100, 50), (8, TILE_SIZE), (8, 8), 3)
            pygame.draw.line(surface, (255, 100, 50), (16, TILE_SIZE), (16, 12), 4)
            pygame.draw.line(surface, (255, 100, 50), (24, TILE_SIZE), (24, 10), 3)
        elif block_name == "clay":
            # Ton: braune Punkte
            pygame.draw.circle(surface, (100, 80, 60), (12, 12), 2)
            pygame.draw.circle(surface, (100, 80, 60), (24, 20), 2)
        elif block_name == "gravel":
            # Kies: mehrere graue Punkte (Kieselsteine)
            for i in range(5):
                x = 4 + (i * 7)
                y = 8 + ((i * 11) % 16)
                pygame.draw.circle(surface, (120, 120, 120), (x, y), 2)
        elif block_name == "driftwood":
            # Treibholz: braune horizontale Linie
            pygame.draw.line(surface, (100, 60, 20), (4, 16), (28, 16), 4)
            pygame.draw.line(surface, (80, 50, 15), (12, 12), (12, 20), 2)
        elif block_name == "shell":
            # Muschel: weißer Bogen (arc = Kreisbogen)
            pygame.draw.arc(surface, (255, 250, 240), (8, 8, 16, 16), 0, 3.14, 2)
            pygame.draw.line(surface, (200, 200, 200), (16, 8), (16, 24), 1)
        elif block_name == "anchor_piece":
            # Ankerstück: Kreis mit Strich (wie ein kleiner Anker)
            pygame.draw.circle(surface, (150, 150, 150), (16, 8), 4)
            pygame.draw.line(surface, (150, 150, 150), (16, 12), (16, 28), 3)
        elif block_name == "ship_plank":
            # Schiffsplanke: Holzmaserung (horizontale und vertikale Linien)
            pygame.draw.line(surface, (120, 80, 40), (0, 8), (TILE_SIZE, 8), 1)
            pygame.draw.line(surface, (120, 80, 40), (0, 16), (TILE_SIZE, 16), 1)
            pygame.draw.line(surface, (80, 50, 20), (8, 0), (8, TILE_SIZE), 1)
        elif block_name == "rope":
            # Seil: diagonale Linien (wie geflochtenes Seil)
            for i in range(0, TILE_SIZE, 4):
                pygame.draw.line(surface, (200, 180, 150), (i % 8 + 8, i), (i % 8 + 12, i + 2), 2)
        elif block_name == "leaves":
            # Laub: mehrere grüne Punkte (Blattwerk)
            for x in range(4, TILE_SIZE - 4, 6):
                for y in range(4, TILE_SIZE - 4, 6):
                    pygame.draw.circle(surface, (0, 100, 0), (x, y), 2)
        elif block_name == "seaweed":
            # Seetang: grüne vertikale Linien
            for i in range(4, TILE_SIZE - 4, 6):
                pygame.draw.line(surface, (0, 120, 0), (i, TILE_SIZE), (i + 2, 8), 2)
        elif block_name == "torch":
            # Fackel: brauner Stiel + gelb-orange Flamme
            pygame.draw.rect(surface, (139, 90, 43), (14, 16, 4, 12))  # Stiel
            pygame.draw.circle(surface, (255, 200, 0), (16, 12), 4)    # Äußere Flamme
            pygame.draw.circle(surface, (255, 100, 0), (16, 12), 2)    # Innere Flamme
        elif block_name == "nuclear_waste":
            # Atommüll: hellgrüne Kreise (giftig)
            pygame.draw.circle(surface, (150, 255, 0), (TILE_SIZE//2, TILE_SIZE//2), 5)
            pygame.draw.circle(surface, (100, 200, 0), (TILE_SIZE//2, TILE_SIZE//2), 3)
        elif block_name == "thorium":
            # Thorium: blaue Kreise
            pygame.draw.circle(surface, (100, 100, 200), (TILE_SIZE//2, TILE_SIZE//2), 6)
            pygame.draw.circle(surface, (150, 150, 255), (TILE_SIZE//2, TILE_SIZE//2), 3)
        elif block_name == "radium":
            # Radium: rote Kreise
            pygame.draw.circle(surface, (200, 50, 50), (TILE_SIZE//2, TILE_SIZE//2), 6)
            pygame.draw.circle(surface, (255, 100, 100), (TILE_SIZE//2, TILE_SIZE//2), 3)
        elif block_name == "radioactive_crystal":
            # Radioaktiver Kristall: grüne Rauten (ineinander)
            pygame.draw.polygon(surface, (150, 255, 150), [(16, 2), (28, 16), (16, 30), (4, 16)])
            pygame.draw.polygon(surface, (200, 255, 200), [(16, 6), (24, 16), (16, 26), (8, 16)])
        elif block_name == "coal_ore":
            # Kohle-Erz: drei dunkle Kreise
            for i in range(3):
                x = 8 + (i * 8)
                y = 8 + ((i * 7) % 16)
                pygame.draw.circle(surface, (30, 30, 30), (x, y), 3)
        elif block_name == "iron_ore":
            # Eisen-Erz: drei braune Kreise
            for i in range(3):
                x = 8 + (i * 8)
                y = 8 + ((i * 7) % 16)
                pygame.draw.circle(surface, (180, 140, 100), (x, y), 3)
        elif block_name == "gold_ore":
            # Gold-Erz: drei gelbe Kreise
            for i in range(3):
                x = 8 + (i * 8)
                y = 8 + ((i * 7) % 16)
                pygame.draw.circle(surface, (255, 215, 0), (x, y), 3)
        elif block_name == "gem":
            # Allgemeiner Edelstein: Raute in Block-Farbe
            pygame.draw.polygon(surface, color, [(16, 4), (24, 16), (16, 28), (8, 16)])
        elif "ore" in block_name and block_name not in ["coal_ore", "iron_ore", "gold_ore", "pearl_ore", "ruby_ore", "emerald_ore", "diamond_ore"]:
            # Allgemeines Erz (Fallback für unbekannte Erze): graue Kreise
            for i in range(3):
                x = 8 + (i * 8)
                y = 8 + ((i * 7) % 16)
                pygame.draw.circle(surface, (200, 200, 200), (x, y), 3)
        elif block_name == "grass":
            # Gras: grüne Striche oben (Gras-Halme)
            for i in range(0, TILE_SIZE, 4):
                pygame.draw.line(surface, (0, 100, 0), (i, 0), (i + 2, 4), 1)
        elif block_name == "leaves":
            # Laub (zweite Definition – wird durch die erste oben abgefangen)
            for x in range(4, TILE_SIZE - 4, 8):
                for y in range(4, TILE_SIZE - 4, 8):
                    pygame.draw.circle(surface, (0, 100, 0), (x, y), 2)
        elif "ore" in block_name:
            # Allgemeines Erz (Fallback): farbige Kreise
            ore_color = (200, 200, 200) if "coal" in block_name else color
            for i in range(3):
                x = 8 + (i * 8)
                y = 8 + ((i * 7) % 16)
                pygame.draw.circle(surface, ore_color, (x, y), 3)
        elif block_name == "wood":
            # Holz: horizontale Linien (Jahresringe)
            for i in range(4, TILE_SIZE, 8):
                pygame.draw.line(surface, (100, 60, 20), (0, i), (TILE_SIZE, i), 1)
        elif block_name == "portal":
            # Portal: vertikale Streifen mit wechselnder Durchsichtigkeit
            for i in range(0, TILE_SIZE, 4):
                alpha = 100 + (i * 4) % 100
                pygame.draw.rect(surface, (*color[:3], alpha), (i, 0, 2, TILE_SIZE))
        elif block_name.startswith("portal_frame"):
            # Portal-Rahmen: gefülltes Rechteck mit dunklerem Innenrand
            props = BLOCK_PROPERTIES.get(block_name, {})
            color = props.get("color", (100, 0, 150))
            border = tuple(max(0, c - 40) for c in color[:3])
            pygame.draw.rect(surface, color, (2, 2, TILE_SIZE-4, TILE_SIZE-4))
            pygame.draw.rect(surface, border, (4, 4, TILE_SIZE-8, TILE_SIZE-8))
        elif block_name == "water":
            # Wasser: wellenförmige Linien (Kreisbögen)
            for i in range(0, TILE_SIZE, 6):
                wave_offset = (i % 12) - 6
                pygame.draw.arc(surface, (100, 150, 255), (wave_offset, i, 20, 8), 0, 3.14, 1)
        
        return surface
    
    def create_item_texture(self, item_name):
        """
        Erzeugt eine Item-Textur durch Zeichnen mit pygame-Befehlen.
        
        Ähnlich wie create_block_texture(), aber für Gegenstände im Inventar.
        Jeder Item-Typ hat sein eigenes Aussehen (Werkzeuge, Schlüssel, Essen, etc.).
        
        :param item_name: Name des Items (z.B. "wooden_pickaxe", "apple")
        :return: pygame-Surface (32x32 Pixel)
        """
        surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        
        if item_name == "sapphire":
            pygame.draw.polygon(surface, (30, 100, 255), [(16, 2), (28, 16), (16, 30), (4, 16)])
            pygame.draw.polygon(surface, (100, 150, 255), [(16, 6), (24, 16), (16, 26), (8, 16)])
        elif item_name == "topaz":
            pygame.draw.polygon(surface, (255, 150, 0), [(16, 2), (28, 16), (16, 30), (4, 16)])
            pygame.draw.polygon(surface, (255, 200, 50), [(16, 6), (24, 16), (16, 26), (8, 16)])
        elif item_name == "opal":
            pygame.draw.polygon(surface, (200, 200, 255), [(16, 2), (28, 16), (16, 30), (4, 16)])
            pygame.draw.polygon(surface, (255, 255, 255), [(16, 6), (24, 16), (16, 26), (8, 16)])
        elif item_name == "thorium":
            pygame.draw.circle(surface, (100, 100, 200), (TILE_SIZE//2, TILE_SIZE//2), 8)
            pygame.draw.circle(surface, (150, 150, 255), (TILE_SIZE//2, TILE_SIZE//2), 4)
        elif item_name == "radium":
            pygame.draw.circle(surface, (200, 50, 50), (TILE_SIZE//2, TILE_SIZE//2), 8)
            pygame.draw.circle(surface, (255, 100, 100), (TILE_SIZE//2, TILE_SIZE//2), 4)
            pygame.draw.circle(surface, (255, 200, 200), (TILE_SIZE//2 - 2, TILE_SIZE//2 - 2), 2)
        elif item_name == "enriched_uranium":
            pygame.draw.circle(surface, (0, 150, 0), (TILE_SIZE//2, TILE_SIZE//2), 8)
            pygame.draw.circle(surface, (0, 255, 0), (TILE_SIZE//2, TILE_SIZE//2), 4)
            pygame.draw.circle(surface, (150, 255, 150), (TILE_SIZE//2, TILE_SIZE//2), 2)
        elif item_name == "radioactive_crystal":
            pygame.draw.polygon(surface, (100, 200, 100), [(16, 2), (28, 16), (16, 30), (4, 16)])
            pygame.draw.polygon(surface, (150, 255, 150), [(16, 6), (24, 16), (16, 26), (8, 16)])
        elif item_name == "driftwood":
            pygame.draw.line(surface, (100, 60, 20), (4, 16), (28, 16), 5)
        elif item_name == "shell":
            pygame.draw.arc(surface, (255, 250, 240), (4, 4, 24, 24), 0, 3.14, 3)
        elif item_name == "anchor_piece":
            pygame.draw.circle(surface, (150, 150, 150), (16, 8), 5)
            pygame.draw.line(surface, (150, 150, 150), (16, 13), (16, 28), 4)
        elif item_name == "ship_plank":
            pygame.draw.rect(surface, (140, 100, 60), (4, 4, 24, 24))
            pygame.draw.line(surface, (100, 60, 30), (4, 12), (28, 12), 1)
            pygame.draw.line(surface, (100, 60, 30), (4, 20), (28, 20), 1)
        elif item_name == "rope":
            for i in range(0, TILE_SIZE, 4):
                pygame.draw.line(surface, (200, 180, 150), (i % 8 + 6, i), (i % 8 + 14, i), 3)
        elif item_name == "raw_fish":
            pygame.draw.ellipse(surface, (200, 150, 50), (4, 12, 24, 10))
            pygame.draw.polygon(surface, (200, 150, 50), [(28, 17), (32, 12), (32, 22)])
        elif "pickaxe" in item_name:
            # Spitzhacke: Stiel + Kopf (Farbe je nach Material)
            color = (139, 90, 43) if "wooden" in item_name else (128, 128, 128) if "stone" in item_name else (200, 200, 200)
            pygame.draw.line(surface, (100, 60, 20), (16, 28), (16, 12), 3)  # Stiel
            pygame.draw.polygon(surface, color, [(8, 4), (24, 4), (24, 12), (8, 12)])  # Kopf
        elif "axe" in item_name:
            # Axt: Stiel + Klinge
            color = (139, 90, 43) if "wooden" in item_name else (128, 128, 128) if "stone" in item_name else (200, 200, 200)
            pygame.draw.line(surface, (100, 60, 20), (16, 28), (16, 12), 3)  # Stiel
            pygame.draw.polygon(surface, color, [(10, 4), (22, 4), (26, 12), (6, 12)])  # Klinge
        elif "shovel" in item_name:
            # Schaufel: Stiel + ovaler Kopf
            color = (139, 90, 43) if "wooden" in item_name else (128, 128, 128) if "stone" in item_name else (200, 200, 200)
            pygame.draw.line(surface, (100, 60, 20), (16, 28), (16, 10), 3)  # Stiel
            pygame.draw.ellipse(surface, color, (10, 2, 12, 12))  # Schaufelblatt
        elif "sword" in item_name:
            # Schwert: Griff + Klinge
            color = (139, 90, 43) if "wooden" in item_name else (128, 128, 128) if "stone" in item_name else (200, 200, 200)
            pygame.draw.line(surface, (100, 60, 20), (16, 28), (16, 20), 4)  # Griff
            pygame.draw.polygon(surface, color, [(14, 20), (18, 20), (18, 4), (16, 2), (14, 4)])  # Klinge
        elif "key" in item_name:
            # Schlüssel: Kreis (Kopf) + rechteckiger Schaft + Bart
            key_color = (128, 128, 128) if "stone" in item_name else (0, 100, 200) if "water" in item_name else (200, 0, 200) if "gem" in item_name else (0, 255, 0)
            pygame.draw.circle(surface, key_color, (16, 10), 8)  # Kopf
            pygame.draw.circle(surface, (0, 0, 0), (16, 10), 4)  # Loch im Kopf
            pygame.draw.rect(surface, key_color, (14, 16, 4, 12))  # Schaft
            pygame.draw.rect(surface, key_color, (18, 22, 6, 3))  # Bart
        elif item_name == "apple":
            # Apfel: roter Kreis + Stiel + Blatt
            pygame.draw.circle(surface, (255, 0, 0), (16, 18), 10)
            pygame.draw.line(surface, (100, 60, 20), (16, 8), (16, 4), 2)  # Stiel
            pygame.draw.ellipse(surface, (0, 150, 0), (17, 4, 6, 4))  # Blatt
        elif item_name == "healing_potion":
            # Heiltrank: Flasche (rechteckig) + Hals + rote Flüssigkeit
            pygame.draw.rect(surface, (200, 0, 0), (10, 12, 12, 16))  # Flasche
            pygame.draw.rect(surface, (150, 150, 150), (12, 6, 8, 8))  # Hals
            pygame.draw.rect(surface, (100, 0, 0), (12, 14, 8, 4))  # Flüssigkeit
        elif item_name == "bread":
            # Brot: ovaler Laib
            pygame.draw.ellipse(surface, (210, 180, 140), (4, 12, 24, 12))
            pygame.draw.arc(surface, (180, 150, 100), (4, 12, 24, 12), 0, 3.14, 2)
        else:
            # Fallback: Wenn das Item ein Block ist, zeige die Block-Farbe
            if item_name in BLOCK_PROPERTIES and BLOCK_PROPERTIES[item_name]["color"]:
                pygame.draw.rect(surface, BLOCK_PROPERTIES[item_name]["color"], (4, 4, 24, 24))
            else:
                pygame.draw.rect(surface, (150, 150, 150), (4, 4, 24, 24))
        
        return surface
    
    def create_mob_texture(self, mob_name, properties):
        """
        Erzeugt eine Gegner-Textur durch Zeichnen mit pygame-Befehlen.
        
        Jeder Gegner-Typ sieht anders aus:
        - Schleime: ovale Form
        - Zombies/Mutanten: rechteckige Körper mit Armen
        - Golems: große, breite Kästen
        - Fledermäuse: ovaler Körper + Flügel
        - Fische/Haie: ovale Körper mit Schwanzflosse
        - Spinnen: ovaler Körper + Beine
        
        :param mob_name: Name des Gegners (z.B. "slime", "zombie")
        :param properties: Dictionary mit Eigenschaften (size, color, etc.)
        :return: pygame-Surface
        """
        size = properties.get("size", (24, 24))
        color = properties.get("color", (255, 0, 0))
        surface = pygame.Surface(size, pygame.SRCALPHA)
        
        if "slime" in mob_name:
            # Schleim: ovaler Körper + weiße Augen
            pygame.draw.ellipse(surface, color, (0, 0, size[0], size[1]))
            pygame.draw.ellipse(surface, (255, 255, 255), (size[0]//4, size[1]//4, 4, 4))
            pygame.draw.ellipse(surface, (255, 255, 255), (size[0]//2, size[1]//4, 4, 4))
        elif "zombie" in mob_name or "mutant" in mob_name:
            # Zombie/Mutant: Kopf + Körper + Arme + Augen
            pygame.draw.rect(surface, color, (size[0]//4, 0, size[0]//2, size[1]//3))  # Kopf
            pygame.draw.rect(surface, color, (size[0]//4, size[1]//3, size[0]//2, size[1]//2))  # Körper
            pygame.draw.rect(surface, color, (size[0]//4 - 4, size[1]//3, 4, size[1]//3))  # Linker Arm
            pygame.draw.rect(surface, color, (size[0]//4 + size[0]//2, size[1]//3, 4, size[1]//3))  # Rechter Arm
            pygame.draw.rect(surface, (0, 0, 0), (size[0]//3, size[1]//8, 3, 3))  # Linkes Auge
            pygame.draw.rect(surface, (0, 0, 0), (size[0]//2, size[1]//8, 3, 3))  # Rechtes Auge
        elif "golem" in mob_name:
            # Golem: großer, breiter Körper + Augen
            pygame.draw.rect(surface, color, (size[0]//4, 0, size[0]//2, size[1]//2))  # Kopf
            pygame.draw.rect(surface, color, (0, size[1]//4, size[0], size[1]//2))  # Körper
            pygame.draw.rect(surface, (50, 50, 50), (size[0]//3, size[1]//6, 4, 4))  # Linkes Auge
            pygame.draw.rect(surface, (50, 50, 50), (size[0]//2, size[1]//6, 4, 4))  # Rechtes Auge
        elif "bat" in mob_name:
            # Fledermaus: ovaler Körper + dreieckige Flügel
            pygame.draw.ellipse(surface, color, (size[0]//4, size[1]//4, size[0]//2, size[1]//2))
            pygame.draw.polygon(surface, color, [(0, size[1]//2), (size[0]//4, 0), (size[0]//4, size[1])])  # Linker Flügel
            pygame.draw.polygon(surface, color, [(size[0], size[1]//2), (size[0]*3//4, 0), (size[0]*3//4, size[1])])  # Rechter Flügel
        elif "fish" in mob_name:
            # Fisch: ovaler Körper + Schwanzflosse + Auge
            pygame.draw.ellipse(surface, color, (0, size[1]//4, size[0]*3//4, size[1]//2))
            pygame.draw.polygon(surface, color, [(size[0]*3//4, size[1]//2), (size[0], 0), (size[0], size[1])])  # Schwanz
            pygame.draw.circle(surface, (0, 0, 0), (size[0]//4, size[1]//2), 2)  # Auge
        elif "shark" in mob_name:
            # Hai: länglicher Körper + Rückenflosse + Schwanz + Auge
            pygame.draw.ellipse(surface, color, (0, size[1]//4, size[0]*4//5, size[1]//2))
            pygame.draw.polygon(surface, color, [(size[0]*3//4, size[1]//2), (size[0], size[1]//4), (size[0], size[1]*3//4)])  # Schwanz
            pygame.draw.polygon(surface, color, [(size[0]//2, size[1]//4), (size[0]//2 + 4, 0), (size[0]//2 + 8, size[1]//4)])  # Rückenflosse
            pygame.draw.circle(surface, (0, 0, 0), (size[0]//5, size[1]//2), 2)  # Auge
        elif "spider" in mob_name:
            # Spinne: ovaler Körper + 8 Beine + 2 Augen
            pygame.draw.ellipse(surface, color, (size[0]//4, size[1]//4, size[0]//2, size[1]//2))
            for i in range(4):
                y = size[1]//2
                pygame.draw.line(surface, color, (size[0]//2, y), (0, i * 4), 2)  # Linke Beine
                pygame.draw.line(surface, color, (size[0]//2, y), (size[0], i * 4), 2)  # Rechte Beine
            pygame.draw.circle(surface, (0, 0, 0), (size[0]//3, size[1]//2), 2)  # Linkes Auge
            pygame.draw.circle(surface, (0, 0, 0), (size[0]*2//3, size[1]//2), 2)  # Rechtes Auge
        else:
            # Fallback: einfarbiges Rechteck
            pygame.draw.rect(surface, color, (0, 0, size[0], size[1]))
        
        return surface
    
    def create_player_texture(self):
        """
        Erzeugt die Spieler-Textur (einfache Minecraft-artige Figur).
        
        Der Spieler besteht aus:
        - Kopf (hautfarben)
        - Körper (blau)
        - Arme (dunkelblau)
        - Beine (dunkelblau)
        - Augen (schwarz)
        - Haare (braun)
        
        :return: pygame-Surface (24x32 Pixel)
        """
        surface = pygame.Surface((24, 32), pygame.SRCALPHA)
        pygame.draw.rect(surface, (255, 200, 150), (6, 0, 12, 10))  # Kopf
        pygame.draw.rect(surface, (0, 0, 255), (4, 10, 16, 14))     # Körper
        pygame.draw.rect(surface, (0, 0, 200), (0, 12, 4, 10))      # Linker Arm
        pygame.draw.rect(surface, (0, 0, 200), (20, 12, 4, 10))     # Rechter Arm
        pygame.draw.rect(surface, (50, 50, 150), (6, 24, 5, 8))     # Linkes Bein
        pygame.draw.rect(surface, (50, 50, 150), (13, 24, 5, 8))    # Rechtes Bein
        pygame.draw.rect(surface, (0, 0, 0), (8, 3, 2, 2))          # Linkes Auge
        pygame.draw.rect(surface, (0, 0, 0), (14, 3, 2, 2))         # Rechtes Auge
        pygame.draw.rect(surface, (139, 90, 43), (4, 0, 16, 3))     # Haare
        return surface
    
    def load_block_textures(self):
        """
        Lädt alle Block-Texturen.
        
        Für jeden Block in BLOCK_PROPERTIES:
        1. Prüfen, ob unter assets/blocks/<block_name>.png eine Datei existiert.
        2. Wenn ja: Datei laden und skalieren.
        3. Wenn nein: Textur mit create_block_texture() selbst zeichnen.
        
        WICHTIG: Blöcke mit color=None (z.B. "air") werden übersprungen.
        """
        blocks_path = os.path.join(self.assets_path, "blocks")
        
        for block_name, props in BLOCK_PROPERTIES.items():
            image_path = os.path.join(blocks_path, f"{block_name}.png")
            
            # Versuche zuerst, eine echte PNG-Datei zu laden
            if os.path.exists(image_path):
                texture = self.resize_image(image_path, (TILE_SIZE, TILE_SIZE))
                if texture:
                    self.block_textures[block_name] = texture
                    continue  # PNG erfolgreich geladen → nächster Block
            
            # Fallback: selbst zeichnen (nur wenn der Block eine Farbe hat)
            if props["color"]:
                self.block_textures[block_name] = self.create_block_texture(block_name, props["color"])
    
    def load_item_textures(self):
        """
        Lädt alle Item-Texturen.
        
        Gleiches Prinzip wie bei Block-Texturen:
        Zuerst nach PNG suchen, dann selbst zeichnen.
        """
        items_path = os.path.join(self.assets_path, "items")
        
        for item_name in ITEM_PROPERTIES.keys():
            image_path = os.path.join(items_path, f"{item_name}.png")
            
            # Versuche zuerst, eine echte PNG-Datei zu laden
            if os.path.exists(image_path):
                texture = self.resize_image(image_path, (TILE_SIZE, TILE_SIZE))
                if texture:
                    self.item_textures[item_name] = texture
                    continue
            
            # Fallback: selbst zeichnen
            self.item_textures[item_name] = self.create_item_texture(item_name)
    
    def load_mob_textures(self):
        """
        Lädt alle Gegner-Texturen.
        
        Gleiches Prinzip wie bei Block-Texturen:
        Zuerst nach PNG suchen, dann selbst zeichnen.
        Die Größe der Textur wird aus MOB_PROPERTIES genommen.
        """
        mobs_path = os.path.join(self.assets_path, "mobs")
        
        for mob_name, props in MOB_PROPERTIES.items():
            image_path = os.path.join(mobs_path, f"{mob_name}.png")
            
            # Versuche zuerst, eine echte PNG-Datei zu laden
            if os.path.exists(image_path):
                texture = self.resize_image(image_path, props["size"])
                if texture:
                    self.mob_textures[mob_name] = texture
                    continue
            
            # Fallback: selbst zeichnen
            self.mob_textures[mob_name] = self.create_mob_texture(mob_name, props)
    
    def load_player_texture(self):
        """
        Lädt die Spieler-Textur.
        
        Zuerst nach assets/player.png suchen, dann selbst zeichnen.
        """
        player_path = os.path.join(self.assets_path, "player.png")
        
        if os.path.exists(player_path):
            texture = self.resize_image(player_path, (24, 32))
            if texture:
                self.player_texture = texture
                return
        
        # Fallback: selbst zeichnen
        self.player_texture = self.create_player_texture()
    
    # =========================================================
    # GETTER-METHODEN
    # =========================================================
    def get_block_texture(self, block_name):
        """Gibt die Textur für einen Block zurück (oder None, wenn nicht gefunden)."""
        return self.block_textures.get(block_name)
    
    def get_item_texture(self, item_name):
        """
        Gibt die Textur für ein Item zurück.
        
        Wenn das Item keine eigene Textur hat, wird geprüft, ob es
        eine Block-Textur mit demselben Namen gibt (z.B. für Blöcke
        im Inventar). Als letzte Möglichkeit wird eine neue Item-Textur
        gezeichnet.
        """
        if item_name in self.item_textures:
            return self.item_textures[item_name]
        if item_name in self.block_textures:
            return self.block_textures[item_name]
        return self.create_item_texture(item_name)
    
    def get_mob_texture(self, mob_name):
        """Gibt die Textur für einen Gegner zurück (oder None, wenn nicht gefunden)."""
        return self.mob_textures.get(mob_name)
    
    def get_player_texture(self):
        """Gibt die Spieler-Textur zurück."""
        return self.player_texture