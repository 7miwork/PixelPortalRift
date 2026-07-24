"""
utils/world_gen.py – Welten-Generierung
=========================================

Dieses Modul ist für die Erzeugung der Spielwelt zuständig.
Die Klasse World repräsentiert eine einzelne Dimension (Welt) als
2D-Raster aus Blöcken. Jeder Block ist ein String wie "grass", "stone", "air".

Die Welt wird mit einem Zufalls-Seed generiert, sodass jede Welt anders aussieht.
Das Gelände wird mit Sinus-Wellen (sanfte Hügel) plus zufälligem Rauschen erzeugt.
Anschließend werden Bäume, Erze und andere Besonderheiten platziert.

WICHTIG: Die Welt kann auch aus einem Savegame geladen werden (load_save_data()).
Dann wird die aufwändige generate()-Methode übersprungen (skip_generation=True),
um Rechenzeit zu sparen.
"""

import random
import math
import pygame
from utils.constants import (
    WORLD_WIDTH, WORLD_HEIGHT, TILE_SIZE, DIMENSIONS, BLOCK_PROPERTIES, WORLD_ITEM_POOLS
)


class World:
    """
    Repräsentiert eine einzelne Spielwelt (Dimension).
    
    Die Welt ist ein 2D-Array (Liste von Listen) mit der Größe WORLD_WIDTH × WORLD_HEIGHT.
    Jede Zelle enthält einen Block-Namen (String) oder None (noch nicht gesetzt).
    
    Wichtige Attribute:
        dimension:      Name der Dimension (z.B. "grassland", "stone_world")
        seed:           Zufalls-Seed für reproduzierbare Welten
        width, height:  Größe der Welt in Blöcken
        blocks:         Das 2D-Array: blocks[x][y] = Block-Name
        dimension_data: Die Daten aus DIMENSIONS für diese Dimension
        spawn_point:    Wo der Spieler beim Betreten spawnen soll (in Pixeln)
        portals:        Liste der Portal-Strukturen in dieser Welt
    """
    
    def __init__(self, dimension="grassland", seed=None, skip_generation=False):
        """
        Erzeugt eine neue Welt.
        
        :param dimension: Name der Dimension (z.B. "grassland")
        :param seed: Zufalls-Seed für die Generierung (optional)
        :param skip_generation: Wenn True, wird generate() übersprungen.
            Nützlich, wenn direkt danach load_save_data() aufgerufen wird
            (z.B. bei Wiederbesuch einer Welt aus dem dimension_cache),
            um unnötige Rechenzeit zu sparen.
        """
        self.dimension = dimension
        # Seed setzen: entweder übergeben oder zufällig
        self.seed = seed if seed else random.randint(0, 999999)
        self.width = WORLD_WIDTH
        self.height = WORLD_HEIGHT
        # 2D-Array initialisieren: alle Zellen sind erstmal None
        self.blocks = [[None for _ in range(self.height)] for _ in range(self.width)]
        self.dimension_data = DIMENSIONS[dimension]
        self.portals = []
        # Vorläufiger Spawn-Punkt (Mitte der Welt, ganz oben)
        self.spawn_point = (self.width // 2 * TILE_SIZE, 0)

        # Zufallsgenerator mit dem Seed initialisieren
        random.seed(self.seed)
        if not skip_generation:
            self.generate()

    # =========================================================
    # WELTEN-GENERIERUNG
    # =========================================================
    def generate(self):
        """
        Erzeugt das gesamte Gelände der Welt.
        
        Ablauf:
        1. Boden-Höhen mit Sinus-Wellen berechnen (sanfte Hügel)
        2. Für jede Spalte (x): Blöcke von oben nach unten setzen
           - Oben: Luft
           - Bodenoberfläche: spezieller Block (Gras, Sand, etc.)
           - Direkt unter der Oberfläche: zweite Schicht (Erde, etc.)
           - Tief unten: zufällige unterirdische Blöcke
        3. Besonderheiten generieren (Bäume in Grasland)
        4. Erze verteilen
        5. Spawn-Punkt auf die Mitte der Oberfläche setzen
        """
        ground_level = self.dimension_data["ground_level"]
        available_blocks = self.dimension_data["blocks"]

        # Schritt 1: Boden-Höhen berechnen
        heights = self.generate_terrain_heights(ground_level)

        # Schritt 2: Blöcke setzen
        for x in range(self.width):
            ground_y = heights[x]
            for y in range(self.height):
                if y < ground_y - 5:
                    # Weit über dem Boden: Luft
                    self.blocks[x][y] = "air"
                elif y == ground_y:
                    # Bodenoberfläche: spezieller Block (Gras, Sand, etc.)
                    self.blocks[x][y] = self.get_surface_block()
                elif y < ground_y + 4:
                    # Direkt unter der Oberfläche: zweite Schicht (Erde, etc.)
                    self.blocks[x][y] = self.get_subsurface_block()
                else:
                    # Tief unter der Erde: zufällige unterirdische Blöcke
                    self.blocks[x][y] = self.get_underground_block(y - ground_y, available_blocks)

        # Schritt 3: Besonderheiten (Bäume, etc.)
        self.generate_features(heights)
        
        # Schritt 4: Erze verteilen
        self.generate_ores(available_blocks)

        # Schritt 5: Spawn-Punkt auf die Mitte der Oberfläche setzen
        spawn_x = self.width // 2
        spawn_y = heights[spawn_x] - 3  # 3 Blöcke über dem Boden (Kopfhöhe)
        self.spawn_point = (spawn_x * TILE_SIZE, spawn_y * TILE_SIZE)

    def generate_terrain_heights(self, base_level):
        """
        Berechnet die Boden-Höhe für jede Spalte (x).
        
        Verwendet eine Mischung aus:
        - Sinus-Wellen (für sanfte Hügel)
        - Zufälligem Rauschen (für natürliche Unebenheiten)
        
        :param base_level: Die durchschnittliche Boden-Höhe
        :return: Liste mit Höhen (y-Wert) für jede x-Position
        """
        heights = []
        for x in range(self.width):
            # Sinus-Wellen mit zwei verschiedenen Frequenzen
            noise = (
                math.sin(x * 0.05) * 5 +   # Große, sanfte Hügel
                math.sin(x * 0.02) * 10 +  # Kleinere Wellen
                random.random() * 2 - 1     # Zufälliges Rauschen
            )
            heights.append(int(base_level + noise))
        return heights

    # =========================================================
    # BLOCK-TYPEN (je nach Dimension)
    # =========================================================
    def get_surface_block(self):
        """
        Gibt den Block-Typ für die Bodenoberfläche zurück.
        
        Jede Dimension hat einen anderen Oberflächen-Block:
        - Grasland: Gras
        - Steinwelt: Stein
        - Wasserwelt: Sand
        - Edelsteinwelt: Kristall
        - Atomwelt: Verseuchter Stein
        """
        return {
            "grassland": "grass",
            "stone_world": "stone",
            "water_world": "sand",
            "gem_world": "crystal",
            "nuclear_world": "contaminated_stone"
        }.get(self.dimension, "grass")

    def get_subsurface_block(self):
        """
        Gibt den Block-Typ für die Schicht direkt unter der Oberfläche zurück.
        
        Jede Dimension hat eine andere Unterschicht:
        - Grasland: Erde
        - Steinwelt: Bruchstein
        - Wasserwelt: Sand
        - Edelsteinwelt: Amethyst
        - Atomwelt: Blei
        """
        return {
            "grassland": "dirt",
            "stone_world": "cobblestone",
            "water_world": "sand",
            "gem_world": "amethyst",
            "nuclear_world": "lead"
        }.get(self.dimension, "dirt")

    def get_underground_block(self, depth, available_blocks):
        """
        Wählt einen zufälligen Block für den tiefen Untergrund.
        
        :param depth: Wie tief unter der Oberfläche (in Blöcken)
        :param available_blocks: Liste der verfügbaren Blöcke für diese Dimension
        :return: Zufälliger Block-Name
        """
        return random.choice(available_blocks)

    # =========================================================
    # BESONDERHEITEN / ERZE
    # =========================================================
    def generate_features(self, heights):
        """
        Generiert besondere Strukturen in der Welt.
        
        Aktuell: Bäume im Grasland.
        In Zukunft könnten hier Höhlen, Gebäude oder andere Strukturen hinzugefügt werden.
        
        :param heights: Die Boden-Höhen für jede x-Position
        """
        if self.dimension == "grassland":
            self.generate_trees(heights)

    def generate_trees(self, heights):
        """
        Generiert Bäume im Grasland.
        
        Ein Baum besteht aus einem Stamm (wood) und wird zufällig platziert.
        Die Bäume haben unterschiedliche Höhen (4-7 Blöcke).
        
        :param heights: Die Boden-Höhen für jede x-Position
        """
        x = 10  # Starte nicht ganz am Rand
        while x < self.width - 10:
            # 15% Wahrscheinlichkeit, dass hier ein Baum steht
            if random.random() < 0.15:
                ground_y = heights[x]
                # Stamm: 4-7 Blöcke hoch
                for ty in range(random.randint(4, 7)):
                    if ground_y - ty - 1 >= 0:
                        self.blocks[x][ground_y - ty - 1] = "wood"
                # Nach einem Baum etwas Abstand lassen
                x += random.randint(5, 12)
            else:
                x += 1

    def generate_ores(self, available_blocks):
        """
        Verteilt Erze in der Welt.
        
        Zwei Schritte:
        1. Für jedes Erz in available_blocks: 15-30 Vorkommen generieren
        2. Zusätzlich seltene Items aus WORLD_ITEM_POOLS verteilen
           (z.B. Schlüssel-Adern)
        
        :param available_blocks: Liste der verfügbaren Blöcke für diese Dimension
        """
        # Schritt 1: Erze aus der Block-Liste
        ore_blocks = [b for b in available_blocks if "ore" in b]
        for ore in ore_blocks:
            for _ in range(random.randint(15, 30)):
                x = random.randint(0, self.width - 1)
                y = random.randint(self.dimension_data["ground_level"] + 5, self.height - 5)
                self.blocks[x][y] = ore
        
        # Schritt 2: Seltene Items aus WORLD_ITEM_POOLS (z.B. Schlüssel-Adern)
        pool = WORLD_ITEM_POOLS.get(self.dimension, {})
        rare_items = pool.get("rare", [])
        for item in rare_items:
            # Nur Blöcke, die in BLOCK_PROPERTIES definiert sind
            if item not in ore_blocks and item in BLOCK_PROPERTIES:
                for _ in range(random.randint(3, 8)):
                    x = random.randint(0, self.width - 1)
                    y = random.randint(self.dimension_data["ground_level"] + 10, self.height - 5)
                    self.blocks[x][y] = item

    # =========================================================
    # BLOCK-ZUGRIFF (FLOAT-SICHER)
    # =========================================================
    def get_block(self, x, y):
        """
        Gibt den Block an Position (x, y) zurück.
        
        Die Koordinaten werden automatisch in Integer umgewandelt,
        damit man auch Float-Werte übergeben kann (z.B. Spieler-Position).
        
        :param x: x-Koordinate (kann Float sein)
        :param y: y-Koordinate (kann Float sein)
        :return: Block-Name (String) oder None (wenn außerhalb der Welt)
        """
        x = int(x)
        y = int(y)
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.blocks[x][y]
        return None

    def set_block(self, x, y, block):
        """
        Setzt einen Block an Position (x, y).
        
        :param x: x-Koordinate
        :param y: y-Koordinate
        :param block: Block-Name (String)
        :return: True bei Erfolg, False wenn außerhalb der Welt
        """
        x = int(x)
        y = int(y)
        if 0 <= x < self.width and 0 <= y < self.height:
            self.blocks[x][y] = block
            return True
        return False

    def break_block(self, x, y):
        """
        Baut einen Block ab (entfernt ihn) und gibt den Drop zurück.
        
        :param x: x-Koordinate
        :param y: y-Koordinate
        :return: Name des gedroppten Items (oder None, wenn nichts gedroppt wird)
        """
        x = int(x)
        y = int(y)
        block = self.get_block(x, y)
        if block and block != "air":
            props = BLOCK_PROPERTIES.get(block, {})
            drop = props.get("drop")  # Was fällt heraus?
            self.set_block(x, y, "air")  # Block entfernen
            return drop
        return None

    def is_solid(self, block):
        """
        Prüft, ob ein Block fest ist (der Spieler nicht durchlaufen kann).
        
        :param block: Block-Name (String) oder None
        :return: True wenn fest, False wenn Luft/Wasser/durchlässig
        """
        if block is None or block == "air":
            return False
        return BLOCK_PROPERTIES.get(block, {}).get("solid", True)

    # =========================================================
    # SPEICHERN / LADEN
    # =========================================================
    def get_save_data(self):
        """
        Gibt den gesamten Welt-Zustand als Dictionary zurück.
        
        Dieses Dictionary kann in einer JSON-Datei gespeichert werden.
        Enthält: Dimension, Seed, alle Blöcke, Spawn-Punkt, Portale.
        """
        return {
            "dimension": self.dimension,
            "seed": self.seed,
            "blocks": self.blocks,        # Das komplette 2D-Array
            "spawn_point": self.spawn_point,
            "portals": self.portals
        }

    def load_save_data(self, data):
        """
        Stellt den Welt-Zustand aus gespeicherten Daten wieder her.
        
        :param data: Dictionary aus get_save_data() (oder aus einer JSON-Datei)
        """
        self.dimension = data.get("dimension", self.dimension)
        self.seed = data.get("seed", self.seed)
        self.blocks = data.get("blocks", self.blocks)
        self.spawn_point = data.get("spawn_point", self.spawn_point)
        self.portals = data.get("portals", [])
        self.dimension_data = DIMENSIONS.get(self.dimension, DIMENSIONS["grassland"])