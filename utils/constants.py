"""
utils/constants.py – Zentrale Konstanten und Daten
====================================================

Dieses Modul ist das "Gedächtnis" des Spiels. Hier stehen ALLE festen Werte,
die das Spielverhalten bestimmen:

- Bildschirmgröße, Blockgröße, FPS
- Farben (als RGB-Tupel)
- Welt-Größe
- Dimensionen (welche Welten gibt es, wie sehen sie aus)
- Block-Eigenschaften (ist ein Block fest? Wie hart ist er? Welche Farbe?)
- Item-Eigenschaften (ist es stapelbar? Ist es ein Werkzeug? Wie viel Schaden?)
- Mob-Eigenschaften (wie viel Leben hat ein Gegner? Wie schnell?)
- Crafting-Rezepte (was kann man herstellen und welche Zutaten braucht man?)
- Welt-Item-Pools (welche Gegenstände kommen in welcher Welt vor)

Wenn du einen neuen Block, ein neues Item, einen neuen Gegner oder ein neues
Rezept hinzufügen willst, musst du hier die entsprechenden Einträge ergänzen.
"""

import math

# =========================================================
# BILDSCHIRM-EINSTELLUNGEN
# =========================================================
SCREEN_WIDTH = 1200   # Breite des Spielfensters in Pixeln
SCREEN_HEIGHT = 800   # Höhe des Spielfensters in Pixeln
TILE_SIZE = 32         # Jeder Block ist 32x32 Pixel groß
FPS = 60               # Das Spiel läuft mit 60 Bildern pro Sekunde (Frames Per Second)

# Maximale Interaktions-Reichweite in Blöcken (Abbauen/Platzieren)
# Der Spieler kann nur Blöcke erreichen, die maximal 3 Blöcke entfernt sind
MAX_INTERACTION_RANGE = 3

# =========================================================
# VOID / TODESGRENZE
# =========================================================
# Ab welcher y-Koordinate (Block-Koordinate) der Spieler Schaden durch den Void nimmt.
# In Minecraft ist das typischerweise y = -64 oder niedriger. Hier verwenden wir einen
# Wert, der unterhalb der normalen Welt liegt, damit Spieler in tiefen Höhlen nicht
# sofort sterben. Der Standardwert -64 ist sicher unter WORLD_HEIGHT=100.
VOID_Y = -64  # Unterhalb von y=-64: 1 Herz Schaden pro Sekunde
VOID_DAMAGE_INTERVAL = 1000  # Wie oft Schaden genommen wird (in Millisekunden)

# =========================================================
# FARBEN (als RGB-Tupel: Rot, Grün, Blau)
# Jede Farbe ist ein Wert zwischen 0 und 255.
# =========================================================
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 255, 255)          # Türkis (Cyan)
DARK_GREEN = (0, 100, 0)
LIGHT_BLUE = (135, 206, 235)  # Himmelblau
DARK_GRAY = (64, 64, 64)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)
PINK = (255, 192, 203)

# =========================================================
# WELT-GRÖSSE
# =========================================================
WORLD_WIDTH = 200   # Die Welt ist 200 Blöcke breit
WORLD_HEIGHT = 100  # Die Welt ist 100 Blöcke hoch

# =========================================================
# 3D-WELT-EINSTELLUNGEN (Ursina-Voxelwelt)
# =========================================================
# Seit der 3D-Migration ist die Welt ein echtes Voxel-Gitter:
#   X und Z sind die horizontale Grundfläche (wie Minecraft),
#   Y ist die Höhe (Y wächst nach oben).
# Die alten 2D-Werte WORLD_WIDTH/WORLD_HEIGHT bleiben als
# horizontale Ausdehnung erhalten; WORLD_DEPTH gibt die Tiefe
# unter der Oberfläche an (Anzahl Blockschichten nach unten).
WORLD_DEPTH = 32                    # Wie viele Blockschichten gibt es unter dem höchsten Punkt?
CHUNK_SIZE = 16                     # Ein Chunk ist 16×16 Blöcke Grundfläche (X/Z)
RENDER_DISTANCE_CHUNKS = 3          # Wie viele Chunks um den Spieler herum gerendert werden
CHUNK_HEIGHT = WORLD_HEIGHT         # Maximale Höhe eines Chunks (in Blöcken)

# Höhe der flachen Oberfläche des Testchunks (Phase 1 – Grundgerüst):
# 3 Schichten: Stein (unten), Erde (Mitte), Gras (oben)
TEST_CHUNK_STONE_LAYERS = 2         # Anzahl Stein-Schichten im Testchunk
TEST_CHUNK_SURFACE_Y = 4            # Y-Höhe der obersten (Gras-)Schicht

# =========================================================
# 3D-SPIELER-EINSTELLUNGEN
# =========================================================
# Die alten 2D-Werte (speed=4, jump_power=12, gravity=0.5) waren auf
# Pixel pro Frame ausgelegt. Für die 3D-Welt gibt es eigene, auf
# Block-Einheiten basierende Werte (wie in Minecraft):
PLAYER_SPEED_3D = 6                 # Laufgeschwindigkeit (Blöcke pro Sekunde)
PLAYER_JUMP_HEIGHT_3D = 2           # Sprunghöhe in Blöcken (2 Blöcke hoch springen)
PLAYER_GRAVITY_3D = 30              # Schwerkraft (Blöcke pro Sekunde²)
PLAYER_SPRINT_FACTOR_3D = 1.6       # Sprint-Multiplikator (Shift halten)
PLAYER_HEIGHT_3D = 2                # Körpergröße des Spielers in Blöcken

# =========================================================
# DIMENSIONEN (Welten)
# =========================================================
# Jede Dimension ist ein Dictionary mit diesen Informationen:
#   name:           Anzeigename (für den Spieler)
#   color:          Farbe der Dimension (für Menüs)
#   sky_color:      Himmelsfarbe (Hintergrund)
#   ground_level:   Auf welcher Höhe (y) ist der Boden? (0 = ganz oben)
#   blocks:         Welche Blöcke kommen in dieser Welt natürlich vor?
#   mobs:           Welche Gegner leben hier?
#   portal_activator: Welcher Schlüssel wird benötigt, um das Portal zu aktivieren?
#   next_dimension:  In welche Welt führt das Portal?
DIMENSIONS = {
    "grassland": {
        "name": "Grassland",
        "color": DARK_GREEN,
        "sky_color": LIGHT_BLUE,
        "ground_level": 50,
        "blocks": ["grass", "dirt", "stone", "wood", "leaves", "coal_ore"],
        "mobs": ["slime", "zombie"],
        "portal_activator": None,          # Startwelt: kein Schlüssel nötig
        "next_dimension": "stone_world"    # Portal führt in die Steinwelt
    },
    "stone_world": {
        "name": "Stone World",
        "color": GRAY,
        "sky_color": DARK_GRAY,
        "ground_level": 40,
        "blocks": ["stone", "cobblestone", "iron_ore", "gold_ore", "gravel"],
        "mobs": ["golem", "bat"],
        "portal_activator": "stone_key",   # Man braucht den Steinschlüssel
        "next_dimension": "water_world"
    },
    "water_world": {
        "name": "Water World",
        "color": BLUE,
        "sky_color": CYAN,
        "ground_level": 70,
        "blocks": ["water", "sand", "clay", "coral", "seaweed", "pearl_ore"],
        "mobs": ["fish", "shark"],
        "portal_activator": "water_key",
        "next_dimension": "gem_world"
    },
    "gem_world": {
        "name": "Gem World",
        "color": PURPLE,
        "sky_color": PINK,
        "ground_level": 45,
        "blocks": ["crystal", "amethyst", "ruby_ore", "emerald_ore", "diamond_ore", "obsidian"],
        "mobs": ["crystal_golem", "gem_spider"],
        "portal_activator": "gem_key",
        "next_dimension": "nuclear_world"
    },
    "nuclear_world": {
        "name": "Nuclear World",
        "color": YELLOW,
        "sky_color": (50, 50, 0),
        "ground_level": 55,
        "blocks": ["uranium", "plutonium", "nuclear_waste", "lead", "reactor_core", "contaminated_stone"],
        "mobs": ["mutant", "radioactive_slime"],
        "portal_activator": "nuclear_key",
        "next_dimension": "dimensional_rift"  # Letzte Welt: führt zum Dimensions-Riss
    }
}

# =========================================================
# BLOCK-EIGENSCHAFTEN (BLOCK_PROPERTIES)
# =========================================================
# Jeder Block hat diese Eigenschaften:
#   solid:    Kann der Spieler durch den Block laufen? (True = fest, False = durchlässig)
#   hardness: Wie schwer ist der Block abzubauen? (höher = länger)
#   tool:     Welches Werkzeug braucht man? (None = jedes Werkzeug)
#   drop:     Was fällt heraus, wenn man den Block abbaut?
#   color:    Welche Farbe hat der Block? (RGB oder RGBA mit Alpha für Durchsichtigkeit)
#             Achtung: color=None bedeutet, dass dieser Block kein Bild bekommt (z.B. "air")
BLOCK_PROPERTIES = {
    # ---- Basis-Blöcke ----
    "air": {"solid": False, "hardness": 0, "tool": None, "drop": None, "color": None},
    "grass": {"solid": True, "hardness": 1, "tool": "shovel", "drop": "dirt", "color": (34, 139, 34)},
    "dirt": {"solid": True, "hardness": 1, "tool": "shovel", "drop": "dirt", "color": (139, 90, 43)},
    "stone": {"solid": True, "hardness": 3, "tool": "pickaxe", "drop": "cobblestone", "color": (128, 128, 128)},
    "cobblestone": {"solid": True, "hardness": 3, "tool": "pickaxe", "drop": "cobblestone", "color": (100, 100, 100)},
    "wood": {"solid": True, "hardness": 2, "tool": "axe", "drop": "wood", "color": (139, 90, 43), "respawnable": True, "respawn_time": 90000},
    "leaves": {"solid": True, "hardness": 0.5, "tool": None, "drop": "stick", "color": (0, 128, 0)},

    # ---- Erze (Ores) ----
    "coal_ore": {"solid": True, "hardness": 3, "tool": "pickaxe", "drop": "coal", "color": (50, 50, 50), "respawnable": True, "respawn_time": 60000},
    "iron_ore": {"solid": True, "hardness": 4, "tool": "pickaxe", "drop": "iron_ore", "color": (180, 140, 100), "respawnable": True, "respawn_time": 60000},
    "gold_ore": {"solid": True, "hardness": 4, "tool": "pickaxe", "drop": "gold_ore", "color": (255, 215, 0), "respawnable": True, "respawn_time": 60000},
    "gravel": {"solid": True, "hardness": 1, "tool": "shovel", "drop": "gravel", "color": (150, 150, 150), "respawnable": True, "respawn_time": 60000},

    # ---- Wasserwelt-Blöcke ----
    "water": {"solid": False, "hardness": 0, "tool": None, "drop": None, "color": (0, 100, 200, 180)},  # Alpha=180 = durchsichtig
    "sand": {"solid": True, "hardness": 1, "tool": "shovel", "drop": "sand", "color": (238, 214, 175)},
    "clay": {"solid": True, "hardness": 1, "tool": "shovel", "drop": "clay", "color": (160, 140, 120)},
    "coral": {"solid": True, "hardness": 1, "tool": None, "drop": "coral", "color": (255, 127, 80), "respawnable": True, "respawn_time": 60000},
    "seaweed": {"solid": False, "hardness": 0, "tool": None, "drop": "seaweed", "color": (0, 100, 0), "respawnable": True, "respawn_time": 60000},
    "pearl_ore": {"solid": True, "hardness": 3, "tool": "pickaxe", "drop": "pearl", "color": (255, 240, 245), "respawnable": True, "respawn_time": 120000},

    # ---- Edelsteinwelt-Blöcke ----
    "crystal": {"solid": True, "hardness": 4, "tool": "pickaxe", "drop": "crystal_shard", "color": (200, 200, 255), "respawnable": True, "respawn_time": 120000},
    "amethyst": {"solid": True, "hardness": 4, "tool": "pickaxe", "drop": "amethyst", "color": (153, 102, 204), "respawnable": True, "respawn_time": 120000},
    "ruby_ore": {"solid": True, "hardness": 5, "tool": "pickaxe", "drop": "ruby", "color": (224, 17, 95), "respawnable": True, "respawn_time": 120000},
    "emerald_ore": {"solid": True, "hardness": 5, "tool": "pickaxe", "drop": "emerald", "color": (0, 201, 87), "respawnable": True, "respawn_time": 120000},
    "diamond_ore": {"solid": True, "hardness": 6, "tool": "pickaxe", "drop": "diamond", "color": (185, 242, 255), "respawnable": True, "respawn_time": 120000},
    "obsidian": {"solid": True, "hardness": 10, "tool": "pickaxe", "drop": "obsidian", "color": (20, 20, 30), "respawnable": True, "respawn_time": 120000},

    # ---- Atomwelt-Blöcke ----
    "uranium": {"solid": True, "hardness": 5, "tool": "pickaxe", "drop": "uranium", "color": (0, 255, 0), "respawnable": True, "respawn_time": 120000},
    "plutonium": {"solid": True, "hardness": 6, "tool": "pickaxe", "drop": "plutonium", "color": (150, 255, 150), "respawnable": True, "respawn_time": 120000},
    "nuclear_waste": {"solid": True, "hardness": 2, "tool": "pickaxe", "drop": "nuclear_waste", "color": (100, 200, 0)},
    "lead": {"solid": True, "hardness": 4, "tool": "pickaxe", "drop": "lead", "color": (80, 80, 90)},
    "reactor_core": {"solid": True, "hardness": 8, "tool": "pickaxe", "drop": "reactor_core", "color": (255, 255, 0), "respawnable": True, "respawn_time": 120000},
    "contaminated_stone": {"solid": True, "hardness": 3, "tool": "pickaxe", "drop": "contaminated_stone", "color": (100, 128, 100)},

    # ---- Portal-Blöcke ----
    # portal_frame_* sind die Rahmen-Blöcke, aus denen man ein Portal baut
    # Jede Dimension hat ihre eigene Portal-Frame-Art
    "portal_frame_grassland": {"solid": True, "hardness": 6, "tool": "pickaxe", "drop": "portal_frame_grassland", "color": (34, 139, 34)},
    "portal_frame_stone_world": {"solid": True, "hardness": 8, "tool": "pickaxe", "drop": "portal_frame_stone_world", "color": (128, 128, 128)},
    "portal_frame_water_world": {"solid": True, "hardness": 7, "tool": "pickaxe", "drop": "portal_frame_water_world", "color": (0, 100, 200)},
    "portal_frame_gem_world": {"solid": True, "hardness": 10, "tool": "pickaxe", "drop": "portal_frame_gem_world", "color": (75, 0, 130)},
    "portal_frame_nuclear_world": {"solid": True, "hardness": 12, "tool": "pickaxe", "drop": "portal_frame_nuclear_world", "color": (50, 50, 0)},

    # ---- Schlüssel-Adern (key_vein) ----
    # Diese speziellen Erz-Blöcke droppen beim Abbauen den Schlüssel für die nächste Welt.
    # Sie sind in der Welt versteckt und müssen gefunden werden.
    "ancient_key_vein": {"solid": True, "hardness": 5, "tool": "pickaxe", "drop": "stone_key", "color": (120, 110, 100), "respawnable": True, "respawn_time": 300000},
    "frozen_key_vein": {"solid": True, "hardness": 7, "tool": "pickaxe", "drop": "water_key", "color": (180, 200, 220), "respawnable": True, "respawn_time": 300000},
    "pearl_key_vein": {"solid": True, "hardness": 6, "tool": "pickaxe", "drop": "gem_key", "color": (220, 200, 240), "respawnable": True, "respawn_time": 300000},
    "crystal_key_vein": {"solid": True, "hardness": 8, "tool": "pickaxe", "drop": "nuclear_key", "color": (160, 100, 200), "respawnable": True, "respawn_time": 300000},

    # ---- Portal-Mitte (wird automatisch gesetzt, wenn ein Portal aktiviert wird) ----
    "portal": {"solid": False, "hardness": 0, "tool": None, "drop": None, "color": (138, 43, 226)}
}

# =========================================================
# ITEM-EIGENSCHAFTEN (ITEM_PROPERTIES)
# =========================================================
# Jedes Item hat diese Eigenschaften:
#   stackable:  Kann man mehrere davon in einem Slot stapeln? (True/False)
#   max_stack:  Wie viele passen maximal in einen Slot?
#   type:       Welche Art von Item ist das?
#               - "material":   Ein Rohstoff (z.B. Holz, Stein)
#               - "block":      Ein Block, den man platzieren kann
#               - "tool":       Ein Werkzeug (Spitzhacke, Axt, Schaufel)
#               - "weapon":     Eine Waffe (Schwert)
#               - "food":       Essen (stellt Hunger und/oder Leben wieder her)
#               - "healing":    Heiltrank
#               - "portal_activator": Ein Schlüssel zum Aktivieren von Portalen
#               - "armor":      Rüstung
#   durability: Haltbarkeit (wie oft kann man es benutzen, bevor es kaputt geht)
#   power:      Stärke des Werkzeugs (höher = schneller abbauen)
#   damage:     Schaden der Waffe
#   heal:       Wie viel Leben wird wiederhergestellt?
#   hunger:     Wie viel Hunger wird gestillt?
ITEM_PROPERTIES = {
    # ---- Grundressourcen ----
    "wood": {"stackable": True, "max_stack": 64, "type": "material"},
    "dirt": {"stackable": True, "max_stack": 64, "type": "block"},
    "cobblestone": {"stackable": True, "max_stack": 64, "type": "block"},
    "coal": {"stackable": True, "max_stack": 64, "type": "material"},
    "iron_ore": {"stackable": True, "max_stack": 64, "type": "material"},
    "gold_ore": {"stackable": True, "max_stack": 64, "type": "material"},
    "iron_ingot": {"stackable": True, "max_stack": 64, "type": "material"},
    "gold_ingot": {"stackable": True, "max_stack": 64, "type": "material"},
    "stick": {"stackable": True, "max_stack": 64, "type": "material"},

    # ---- Portal-Schlüssel (nicht stapelbar, da jeder Schlüssel einzeln ist) ----
    "stone_key": {"stackable": False, "max_stack": 1, "type": "portal_activator"},
    "water_key": {"stackable": False, "max_stack": 1, "type": "portal_activator"},
    "gem_key": {"stackable": False, "max_stack": 1, "type": "portal_activator"},
    "nuclear_key": {"stackable": False, "max_stack": 1, "type": "portal_activator"},

    # ---- Werkzeuge ----
    # Jedes Werkzeug hat einen Typ (tool_type), eine Haltbarkeit (durability) und eine Stärke (power)
    "wooden_pickaxe": {"stackable": False, "max_stack": 1, "type": "tool", "tool_type": "pickaxe", "durability": 60, "power": 1},
    "stone_pickaxe": {"stackable": False, "max_stack": 1, "type": "tool", "tool_type": "pickaxe", "durability": 132, "power": 2},
    "iron_pickaxe": {"stackable": False, "max_stack": 1, "type": "tool", "tool_type": "pickaxe", "durability": 251, "power": 3},
    "diamond_pickaxe": {"stackable": False, "max_stack": 1, "type": "tool", "tool_type": "pickaxe", "durability": 1000, "power": 5},

    "wooden_axe": {"stackable": False, "max_stack": 1, "type": "tool", "tool_type": "axe", "durability": 60, "power": 1},
    "stone_axe": {"stackable": False, "max_stack": 1, "type": "tool", "tool_type": "axe", "durability": 132, "power": 2},
    "iron_axe": {"stackable": False, "max_stack": 1, "type": "tool", "tool_type": "axe", "durability": 251, "power": 3},

    "wooden_shovel": {"stackable": False, "max_stack": 1, "type": "tool", "tool_type": "shovel", "durability": 60, "power": 1},
    "stone_shovel": {"stackable": False, "max_stack": 1, "type": "tool", "tool_type": "shovel", "durability": 132, "power": 2},
    "iron_shovel": {"stackable": False, "max_stack": 1, "type": "tool", "tool_type": "shovel", "durability": 251, "power": 3},

    # ---- Waffen ----
    "wooden_sword": {"stackable": False, "max_stack": 1, "type": "weapon", "damage": 4, "durability": 60},
    "stone_sword": {"stackable": False, "max_stack": 1, "type": "weapon", "damage": 5, "durability": 132},
    "iron_sword": {"stackable": False, "max_stack": 1, "type": "weapon", "damage": 6, "durability": 251},
    "diamond_sword": {"stackable": False, "max_stack": 1, "type": "weapon", "damage": 8, "durability": 1000},
    "overpowered_sword": {"stackable": False, "max_stack": 1, "type": "weapon", "damage": 50, "durability": 2500},  # Extrem starkes Schwert (nur von Bossen)

    # ---- Essen ----
    "apple": {"stackable": True, "max_stack": 64, "type": "food", "heal": 4, "hunger": 4},
    "bread": {"stackable": True, "max_stack": 64, "type": "food", "heal": 0, "hunger": 5},
    "cooked_fish": {"stackable": True, "max_stack": 64, "type": "food", "heal": 2, "hunger": 6},
    "raw_fish": {"stackable": True, "max_stack": 64, "type": "material"},

    # ---- Heilen ----
    "healing_potion": {"stackable": True, "max_stack": 16, "type": "healing", "heal": 10},

    # ---- Blöcke (die man platzieren kann) ----
    "portal_frame_grassland": {"stackable": True, "max_stack": 64, "type": "block"},
    "portal_frame_stone_world": {"stackable": True, "max_stack": 64, "type": "block"},
    "portal_frame_water_world": {"stackable": True, "max_stack": 64, "type": "block"},
    "portal_frame_gem_world": {"stackable": True, "max_stack": 64, "type": "block"},
    "portal_frame_nuclear_world": {"stackable": True, "max_stack": 64, "type": "block"},
    "obsidian": {"stackable": True, "max_stack": 64, "type": "block"},
    "sand": {"stackable": True, "max_stack": 64, "type": "block"},
    "gravel": {"stackable": True, "max_stack": 64, "type": "block"},
    "torch": {"stackable": True, "max_stack": 64, "type": "block"},

    # ---- Edelsteine ----
    "pearl": {"stackable": True, "max_stack": 64, "type": "material"},
    "crystal_shard": {"stackable": True, "max_stack": 64, "type": "material"},
    "amethyst": {"stackable": True, "max_stack": 64, "type": "material"},
    "ruby": {"stackable": True, "max_stack": 64, "type": "material"},
    "emerald": {"stackable": True, "max_stack": 64, "type": "material"},
    "diamond": {"stackable": True, "max_stack": 64, "type": "material"},
    "sapphire": {"stackable": True, "max_stack": 64, "type": "material"},
    "topaz": {"stackable": True, "max_stack": 64, "type": "material"},
    "opal": {"stackable": True, "max_stack": 64, "type": "material"},

    # ---- Nukleare Materialien ----
    "uranium": {"stackable": True, "max_stack": 64, "type": "material"},
    "plutonium": {"stackable": True, "max_stack": 64, "type": "material"},
    "nuclear_waste": {"stackable": True, "max_stack": 64, "type": "material"},
    "lead": {"stackable": True, "max_stack": 64, "type": "material"},
    "reactor_core": {"stackable": True, "max_stack": 16, "type": "material"},
    "thorium": {"stackable": True, "max_stack": 64, "type": "material"},
    "radium": {"stackable": True, "max_stack": 64, "type": "material"},
    "enriched_uranium": {"stackable": True, "max_stack": 64, "type": "material"},
    "radioactive_crystal": {"stackable": True, "max_stack": 64, "type": "material"},

    # ---- Wasserwelt-Materialien ----
    "driftwood": {"stackable": True, "max_stack": 64, "type": "material"},
    "shell": {"stackable": True, "max_stack": 64, "type": "material"},
    "anchor_piece": {"stackable": True, "max_stack": 64, "type": "material"},
    "ship_plank": {"stackable": True, "max_stack": 64, "type": "material"},
    "rope": {"stackable": True, "max_stack": 64, "type": "material"},

    # ---- Andere Materialien ----
    "clay": {"stackable": True, "max_stack": 64, "type": "material"},
    "coral": {"stackable": True, "max_stack": 64, "type": "material"},
    "seaweed": {"stackable": True, "max_stack": 64, "type": "material"},
    "slime_ball": {"stackable": True, "max_stack": 64, "type": "material"},
    "rotten_flesh": {"stackable": True, "max_stack": 64, "type": "material"},
    "shark_tooth": {"stackable": True, "max_stack": 64, "type": "material"},

    # ---- Rüstungen ----
    "radiation_suit": {"stackable": False, "max_stack": 1, "type": "armor"},
}

# =========================================================
# GEGNER-EIGENSCHAFTEN (MOB_PROPERTIES)
# =========================================================
# Jeder Gegner (Mob) hat:
#   health:  Wie viel Leben hat er?
#   damage:  Wie viel Schaden macht er pro Treffer?
#   speed:   Wie schnell bewegt er sich?
#   drop:    Was lässt er fallen, wenn er stirbt?
#   color:   Welche Farbe hat er?
#   size:    Wie groß ist er? (Breite, Höhe) in Pixeln
#   is_boss: Ist er ein Endgegner? (True/False)
MOB_PROPERTIES = {
    "slime": {"health": 10, "damage": 2, "speed": 1, "drop": "slime_ball", "color": GREEN, "size": (24, 24)},
    "zombie": {"health": 20, "damage": 3, "speed": 0.8, "drop": "rotten_flesh", "color": DARK_GREEN, "size": (24, 32)},
    "golem": {"health": 50, "damage": 5, "speed": 0.5, "drop": "iron_ingot", "color": GRAY, "size": (32, 40)},
    "bat": {"health": 5, "damage": 1, "speed": 2, "drop": None, "color": DARK_GRAY, "size": (16, 16)},
    "fish": {"health": 5, "damage": 0, "speed": 1.5, "drop": "raw_fish", "color": ORANGE, "size": (16, 12)},
    "shark": {"health": 30, "damage": 6, "speed": 1.2, "drop": "shark_tooth", "color": GRAY, "size": (40, 20)},
    "crystal_golem": {"health": 60, "damage": 6, "speed": 0.4, "drop": "crystal_shard", "color": PURPLE, "size": (32, 40), "is_boss": True},
    "gem_spider": {"health": 15, "damage": 4, "speed": 1.5, "drop": "ruby", "color": RED, "size": (24, 16)},
    "mutant": {"health": 40, "damage": 8, "speed": 1.0, "drop": "uranium", "color": (150, 255, 0), "size": (28, 36)},
    "radioactive_slime": {"health": 25, "damage": 5, "speed": 0.8, "drop": "nuclear_waste", "color": (100, 255, 100), "size": (28, 28)}
}

# =========================================================
# WELT-ITEM-POOLS
# =========================================================
# Diese Pools legen fest, welche Gegenstände in welcher Welt
# als Beute von Gegnern oder als seltene Funde vorkommen.
#   common:   Häufige Gegenstände
#   uncommon: Seltenere Gegenstände
#   rare:     Seltene Gegenstände (oft Schlüssel-Adern)
#   mob_drops: Beute, die Gegner fallen lassen können
WORLD_ITEM_POOLS = {
    "grassland": {
        "common": ["dirt", "cobblestone", "coal", "wood"],
        "uncommon": ["stick", "apple", "leaves"],
        "rare": ["iron_ore", "gold_ore", "ancient_key_vein"],
        "mob_drops": ["slime_ball", "rotten_flesh"]
    },
    "stone_world": {
        "common": ["stone", "cobblestone", "coal", "gravel", "iron_ore"],
        "uncommon": ["gold_ore", "stick"],
        "rare": ["diamond", "emerald", "ruby", "frozen_key_vein"],
        "mob_drops": ["iron_ingot", "rotten_flesh"]
    },
    "water_world": {
        "common": ["sand", "clay", "coral", "seaweed", "water"],
        "uncommon": ["pearl", "driftwood", "shell", "rope"],
        "rare": ["anchor_piece", "ship_plank", "cooked_fish", "pearl_key_vein"],
        "mob_drops": ["raw_fish", "shark_tooth", "cooked_fish"]
    },
    "gem_world": {
        "common": ["crystal", "amethyst", "obsidian"],
        "uncommon": ["ruby", "emerald", "diamond"],
        "rare": ["sapphire", "topaz", "opal", "crystal_key_vein"],
        "mob_drops": ["crystal_shard", "ruby", "emerald"]
    },
    "nuclear_world": {
        "common": ["contaminated_stone", "lead", "uranium", "nuclear_waste"],
        "uncommon": ["plutonium", "reactor_core", "radioactive_crystal"],
        "rare": ["thorium", "radium", "enriched_uranium"],
        "mob_drops": ["uranium", "nuclear_waste", "plutonium"]
    }
}

# =========================================================
# CRAFTING-REZEPTE (CRAFTING_RECIPES)
# =========================================================
# Jedes Rezept hat:
#   ingredients:  Ein Dictionary mit den benötigten Zutaten (Name: Anzahl)
#   result_count: Wie viele Stücke des Ergebnisses erhält man?
#
# Die Rezepte sind nach Themen gruppiert:
#   - Basis-Werkzeuge (Holz)
#   - Stein-Werkzeuge
#   - Eisen-Werkzeuge
#   - Diamant-Werkzeuge
#   - Portal-Frames (für jede Welt)
#   - Portal-Schlüssel
#   - Verbrauchsmaterialien (Essen, Heiltränke, Fackeln)
CRAFTING_RECIPES = {
    # ---- Basis-Werkzeuge (Holz) ----
    "stick": {"ingredients": {"wood": 2}, "result_count": 4},
    "wooden_pickaxe": {"ingredients": {"wood": 3, "stick": 2}, "result_count": 1},
    "wooden_axe": {"ingredients": {"wood": 3, "stick": 2}, "result_count": 1},
    "wooden_shovel": {"ingredients": {"wood": 1, "stick": 2}, "result_count": 1},
    "wooden_sword": {"ingredients": {"wood": 2, "stick": 1}, "result_count": 1},

    # ---- Stein-Werkzeuge ----
    "stone_pickaxe": {"ingredients": {"cobblestone": 3, "stick": 2}, "result_count": 1},
    "stone_axe": {"ingredients": {"cobblestone": 3, "stick": 2}, "result_count": 1},
    "stone_shovel": {"ingredients": {"cobblestone": 1, "stick": 2}, "result_count": 1},
    "stone_sword": {"ingredients": {"cobblestone": 2, "stick": 1}, "result_count": 1},

    # ---- Eisen-Werkzeuge ----
    "iron_ingot": {"ingredients": {"iron_ore": 1, "coal": 1}, "result_count": 1},
    "gold_ingot": {"ingredients": {"gold_ore": 1, "coal": 1}, "result_count": 1},
    "iron_pickaxe": {"ingredients": {"iron_ingot": 3, "stick": 2}, "result_count": 1},
    "iron_axe": {"ingredients": {"iron_ingot": 3, "stick": 2}, "result_count": 1},
    "iron_shovel": {"ingredients": {"iron_ingot": 1, "stick": 2}, "result_count": 1},
    "iron_sword": {"ingredients": {"iron_ingot": 2, "stick": 1}, "result_count": 1},

    # ---- Diamant-Werkzeuge ----
    "diamond_pickaxe": {"ingredients": {"diamond": 3, "stick": 2}, "result_count": 1},
    "diamond_sword": {"ingredients": {"diamond": 2, "stick": 1}, "result_count": 1},

    # ---- Portal-Frames (für jede Welt) ----
    # Die Zutaten sind so gewählt, dass sie in der jeweiligen Welt verfügbar sind
    "portal_frame_grassland": {"ingredients": {"cobblestone": 10, "coal": 4, "iron_ore": 2}, "result_count": 1},
    "portal_frame_stone_world": {"ingredients": {"cobblestone": 10, "coal": 4, "iron_ore": 2}, "result_count": 1},
    "portal_frame_water_world": {"ingredients": {"pearl": 4, "coral": 6, "anchor_piece": 1}, "result_count": 1},
    "portal_frame_gem_world": {"ingredients": {"obsidian": 6, "diamond": 2, "sapphire": 1}, "result_count": 1},
    "portal_frame_nuclear_world": {"ingredients": {"lead": 8, "reactor_core": 2, "thorium": 1}, "result_count": 1},

    # ---- Portal-Schlüssel ----
    "stone_key": {"ingredients": {"cobblestone": 12, "iron_ore": 1, "gold_ore": 1}, "result_count": 1},
    "water_key": {"ingredients": {"pearl": 6, "coral": 4, "ship_plank": 1}, "result_count": 1},
    "gem_key": {"ingredients": {"ruby": 3, "emerald": 3, "amethyst": 3, "opal": 1}, "result_count": 1},
    "nuclear_key": {"ingredients": {"uranium": 6, "lead": 6, "reactor_core": 2, "radium": 1}, "result_count": 1},

    # ---- Spezielle Gegenstände ----
    "radiation_suit": {"ingredients": {"lead": 8, "uranium": 2, "radioactive_crystal": 1}, "result_count": 1},

    # ---- Verbrauchsmaterialien ----
    "healing_potion": {"ingredients": {"apple": 2, "coal": 1}, "result_count": 1},
    "bread": {"ingredients": {"seaweed": 3}, "result_count": 2},
    "cooked_fish": {"ingredients": {"raw_fish": 1, "coal": 1}, "result_count": 1},
    "torch": {"ingredients": {"stick": 1, "coal": 1}, "result_count": 4},
}