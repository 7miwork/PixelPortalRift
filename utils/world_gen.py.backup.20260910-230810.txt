"""
utils/world_gen.py – Welten-Generierung
=========================================

Dieses Modul ist für die Erzeugung der Spielwelt zuständig.
Die Klasse World repräsentiert eine einzelne Dimension (Welt) als
2D-Raster aus Blöcken. Jeder Block ist ein String wie "grass", "stone", "air".

Die Welt wird mit einem Zufalls-Seed generiert, sodass jede Welt anders aussieht.
Das Gelände wird mit Sinus-Wellen (sanfte Hügel) plus zufälligem Rauschen erzeugt.
Anschließend werden Bäume, Erze und andere Besonderheiten platziert.

Außerdem enthält die Welt eine Respawn-Logik für Ressourcen:
Wenn ein abbaubarer Ressourcen-Block (Erz, Holz, Koralle, etc.) abgebaut wird,
wird er nach einer bestimmten Zeit (respawn_time) automatisch wiederhergestellt.
Terrain-Blöcke (Gras, Erde, Stein, etc.) respawnen NICHT, damit sich
gegrabene Tunnel nicht selbstständig zuschütten.

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
        respawn_queue:  Liste von Ressourcen, die nach einer Zeit wieder erscheinen
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

        # Respawn-Warteschlange: speichert abgebaute Ressourcen, die nach einer
        # bestimmten Zeit wieder erscheinen sollen. Eintrag: {"x", "y", "block", "time_left"}
        self.respawn_queue = []

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
        
        # Schritt 3b: Höhlen generieren mit dem "Drunkard's Walk"-Algorithmus.
        # Das ist ein einfaches Verfahren, bei dem man einen zufälligen Weg durch
        # den Untergrund gräbt. Es eignet sich gut für natürliche, verzweigte Gänge.
        # Wichtig: Höhlen werden VOR den Erzen generiert, damit Erze auch an
        # Höhlenwänden erscheinen können.
        self.generate_caves(heights)
        
        # Schritt 4: Erze verteilen (können jetzt auch an Höhlenwänden liegen)
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

    def generate_caves(self, heights):
        """
        Generiert Höhlen im Untergrund mit dem "Drunkard's Walk"-Algorithmus.
        
        Was ist "Drunkard's Walk"?
        Ein einfaches Verfahren, um zufällige, natürliche Pfade zu erstellen:
        Man startet an einem Punkt und läuft in eine zufällige Richtung.
        Bei jedem Schritt ändert sich die Richtung nur leicht, sodass der Weg
        keine scharfen Kurven macht, sondern eher einem natürlichen Gang ähnelt.
        
        Ablauf:
        1. Anzahl Wanderwege berechnen (abhängig von Weltbreite)
        2. Für jeden Weg:
           - Zufälligen Startpunkt tief im Untergrund wählen
           - Zufällige Richtung wählen
           - 80-200 Schritte laufen, wobei sich die Richtung bei jedem Schritt
             nur leicht verändert
           - Bei jedem Schritt einen kleinen Bereich (Radius 1-2) um die
             aktuelle Position auf "air" setzen
        
        Wichtig: Höhlen werden VOR den Erzen generiert, damit Erze auch an
        Höhlenwänden erscheinen können. Die Height-Grenze sorgt dafür, dass
        keine Löcher an der Oberfläche entstehen.
        
        :param heights: Die Boden-Höhen für jede x-Position
        """
        # Anzahl der Wanderwege: mindestens 3, sonst ein Weg pro 40 Blöcke Breite
        num_walks = max(3, self.width // 40)
        
        for _ in range(num_walks):
            # Zufälligen Startpunkt wählen: x = beliebig, y = mindestens 15 Blöcke unter der Oberfläche
            start_x = random.randint(10, self.width - 10)
            surface_y = heights[start_x]
            min_cave_y = surface_y + 15  # Höhlen beginnen mindestens 15 Blöcke unter der Oberfläche
            
            if min_cave_y >= self.height - 5:
                continue  # Zu wenig Platz für Höhlen in diesem Bereich
            
            start_y = random.randint(min_cave_y, self.height - 10)
            
            # Zufällige Start-Richtung (als dx/dy)
            # Wir verwenden kleine Werte, weil wir bei jedem Schritt nur leicht
            # die Richtung ändern wollen
            dx = random.uniform(-1.0, 1.0)
            dy = random.uniform(0.3, 1.0)  # Tendenz: eher nach unten
            
            # Anzahl Schritte für diesen Wanderweg (80-200)
            steps = random.randint(80, 200)
            
            # Aktuelle Position
            cx = start_x
            cy = start_y
            
            for step in range(steps):
                # Radius 1-2 Blöcke um die aktuelle Position auf "air" setzen
                radius = random.randint(1, 2)
                for ry in range(-radius, radius + 1):
                    for rx in range(-radius, radius + 1):
                        px = int(cx) + rx
                        py = int(cy) + ry
                        
                        # Nur innerhalb der Weltgrenzen setzen
                        if 0 <= px < self.width and 0 <= py < self.height:
                            # Height-Grenze beachten: Cave soll nicht zu nah an die Oberfläche kommen
                            # Prüfe an der jeweiligen x-Position, wie hoch die Oberfläche ist
                            surface_at_x = heights[px] if 0 <= px < len(heights) else surface_y
                            min_y = surface_at_x + 10  # Mindestens 10 Blöcke Abstand zur Oberfläche
                            
                            if py >= min_y:
                                # Block auf "air" setzen (Höhle graben)
                                self.blocks[px][py] = "air"
                
                # Richtung nur leicht verändern (Drunkard's Walk Prinzip)
                # Jede Komponente um maximal -0.3 bis +0.3 ändern
                dx += random.uniform(-0.3, 0.3)
                dy += random.uniform(-0.3, 0.3)
                
                # Richtung begrenzen, damit der Gang nicht zu steil wird
                # dy zwischen 0.2 und 1.5 halten (meistens nach unten, selten nach oben)
                dy = max(0.2, min(1.5, dy))
                # dx zwischen -1.5 und 1.5 begrenzen
                dx = max(-1.5, min(1.5, dx))
                
                # Nächste Position berechnen (aufrunden für Integer-Koordinaten)
                cx += dx
                cy += dy
                
                # Umwandeln in Integer für den Zugriff auf das Block-Array
                ix = int(cx)
                iy = int(cy)
                
                # Sicherstellen, dass wir innerhalb der Welt bleiben
                if ix < 0:
                    ix = 0
                    dx = abs(dx)  # Nach rechts umlenken
                elif ix >= self.width:
                    ix = self.width - 1
                    dx = -abs(dx)  # Nach links umlenken
                
                if iy < 0:
                    iy = 0
                    dy = abs(dy)  # Nach unten umlenken
                elif iy >= self.height:
                    iy = self.height - 1
                    dy = -abs(dy)  # Nach oben umlenken
                
                # Aktualisierte Position für den nächsten Schritt
                cx = ix
                cy = iy

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
        
        Wenn der Block als "respawnable" markiert ist, wird er in die
        Respawn-Warteschlange eingetragen und erscheint nach Ablauf der
        respawn_time automatisch wieder.
        
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
            
            # Wenn der Block respawn-fähig ist, in die Warteschlange einfügen
            if props.get("respawnable", False):
                respawn_time = props.get("respawn_time", 60000)
                self.respawn_queue.append({
                    "x": x,
                    "y": y,
                    "block": block,
                    "time_left": respawn_time
                })
            
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

    def update(self, dt):
        """
        Aktualisiert die Respawn-Warteschlange.
        
        Wird jeden Frame aufgerufen. Geht alle wartenden Respawns durch,
        zieht die vergangene Zeit ab und stellt den Block wieder her,
        wenn die Zeit abgelaufen ist.
        
        :param dt: Zeit seit dem letzten Frame in Millisekunden
        """
        # Liste von hinten durchgehen, weil wir Einträge entfernen
        for entry in self.respawn_queue[:]:
            entry["time_left"] -= dt
            
            if entry["time_left"] <= 0:
                # Prüfen, ob an der Position noch immer "air" ist
                current_block = self.get_block(entry["x"], entry["y"])
                if current_block == "air":
                    # Block wiederherstellen
                    self.set_block(entry["x"], entry["y"], entry["block"])
                
                # Eintrag aus der Warteschlange entfernen
                self.respawn_queue.remove(entry)

    # =========================================================
    # SPEICHERN / LADEN
    # =========================================================
    def get_save_data(self):
        """
        Gibt den gesamten Welt-Zustand als Dictionary zurück.
        
        Dieses Dictionary kann in einer JSON-Datei gespeichert werden.
        Enthält: Dimension, Seed, alle Blöcke, Spawn-Punkt, Portale,
        sowie die Respawn-Warteschlange.
        """
        return {
            "dimension": self.dimension,
            "seed": self.seed,
            "blocks": self.blocks,        # Das komplette 2D-Array
            "spawn_point": self.spawn_point,
            "portals": self.portals,
            "respawn_queue": self.respawn_queue
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
        # Respawn-Warteschlange wiederherstellen (oder leer starten)
        self.respawn_queue = data.get("respawn_queue", [])
        self.dimension_data = DIMENSIONS.get(self.dimension, DIMENSIONS["grassland"])