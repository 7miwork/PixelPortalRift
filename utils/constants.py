import pygame

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
TILE_SIZE = 32
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BROWN = (139, 69, 19)
DARK_GREEN = (0, 100, 0)
LIGHT_BLUE = (135, 206, 235)
DARK_GRAY = (64, 64, 64)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)
PINK = (255, 192, 203)

WORLD_WIDTH = 200
WORLD_HEIGHT = 100

DIMENSIONS = {
    "grassland": {
        "name": "Grassland",
        "color": DARK_GREEN,
        "sky_color": LIGHT_BLUE,
        "ground_level": 50,
        "blocks": ["grass", "dirt", "stone", "wood", "leaves", "coal_ore"],
        "mobs": ["slime", "zombie"],
        "portal_activator": None,
        "next_dimension": "stone_world"
    },
    "stone_world": {
        "name": "Stone World",
        "color": GRAY,
        "sky_color": DARK_GRAY,
        "ground_level": 40,
        "blocks": ["stone", "cobblestone", "iron_ore", "gold_ore", "gravel"],
        "mobs": ["golem", "bat"],
        "portal_activator": "stone_key",
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
        "next_dimension": "dimensional_rift"
    }
}

BLOCK_PROPERTIES = {
    "air": {"solid": False, "hardness": 0, "tool": None, "drop": None, "color": None},
    "grass": {"solid": True, "hardness": 1, "tool": "shovel", "drop": "dirt", "color": (34, 139, 34)},
    "dirt": {"solid": True, "hardness": 1, "tool": "shovel", "drop": "dirt", "color": (139, 90, 43)},
    "stone": {"solid": True, "hardness": 3, "tool": "pickaxe", "drop": "cobblestone", "color": (128, 128, 128)},
    "cobblestone": {"solid": True, "hardness": 3, "tool": "pickaxe", "drop": "cobblestone", "color": (100, 100, 100)},
    "wood": {"solid": True, "hardness": 2, "tool": "axe", "drop": "wood", "color": (139, 90, 43)},
    "leaves": {"solid": True, "hardness": 0.5, "tool": None, "drop": "stick", "color": (0, 128, 0)},
    "coal_ore": {"solid": True, "hardness": 3, "tool": "pickaxe", "drop": "coal", "color": (50, 50, 50)},
    "iron_ore": {"solid": True, "hardness": 4, "tool": "pickaxe", "drop": "iron_ore", "color": (180, 140, 100)},
    "gold_ore": {"solid": True, "hardness": 4, "tool": "pickaxe", "drop": "gold_ore", "color": (255, 215, 0)},
    "gravel": {"solid": True, "hardness": 1, "tool": "shovel", "drop": "gravel", "color": (150, 150, 150)},
    "water": {"solid": False, "hardness": 0, "tool": None, "drop": None, "color": (0, 100, 200, 180)},
    "sand": {"solid": True, "hardness": 1, "tool": "shovel", "drop": "sand", "color": (238, 214, 175)},
    "clay": {"solid": True, "hardness": 1, "tool": "shovel", "drop": "clay", "color": (160, 140, 120)},
    "coral": {"solid": True, "hardness": 1, "tool": None, "drop": "coral", "color": (255, 127, 80)},
    "seaweed": {"solid": False, "hardness": 0, "tool": None, "drop": "seaweed", "color": (0, 100, 0)},
    "pearl_ore": {"solid": True, "hardness": 3, "tool": "pickaxe", "drop": "pearl", "color": (255, 240, 245)},
    "crystal": {"solid": True, "hardness": 4, "tool": "pickaxe", "drop": "crystal_shard", "color": (200, 200, 255)},
    "amethyst": {"solid": True, "hardness": 4, "tool": "pickaxe", "drop": "amethyst", "color": (153, 102, 204)},
    "ruby_ore": {"solid": True, "hardness": 5, "tool": "pickaxe", "drop": "ruby", "color": (224, 17, 95)},
    "emerald_ore": {"solid": True, "hardness": 5, "tool": "pickaxe", "drop": "emerald", "color": (0, 201, 87)},
    "diamond_ore": {"solid": True, "hardness": 6, "tool": "pickaxe", "drop": "diamond", "color": (185, 242, 255)},
    "obsidian": {"solid": True, "hardness": 10, "tool": "pickaxe", "drop": "obsidian", "color": (20, 20, 30)},
    "uranium": {"solid": True, "hardness": 5, "tool": "pickaxe", "drop": "uranium", "color": (0, 255, 0)},
    "plutonium": {"solid": True, "hardness": 6, "tool": "pickaxe", "drop": "plutonium", "color": (150, 255, 150)},
    "nuclear_waste": {"solid": True, "hardness": 2, "tool": "pickaxe", "drop": "nuclear_waste", "color": (100, 200, 0)},
    "lead": {"solid": True, "hardness": 4, "tool": "pickaxe", "drop": "lead", "color": (80, 80, 90)},
    "reactor_core": {"solid": True, "hardness": 8, "tool": "pickaxe", "drop": "reactor_core", "color": (255, 255, 0)},
    "contaminated_stone": {"solid": True, "hardness": 3, "tool": "pickaxe", "drop": "contaminated_stone", "color": (100, 128, 100)},
    "portal_frame": {"solid": True, "hardness": 10, "tool": "pickaxe", "drop": "portal_frame", "color": (75, 0, 130)},
    "portal": {"solid": False, "hardness": 0, "tool": None, "drop": None, "color": (138, 43, 226)}
}

ITEM_PROPERTIES = {
    # Grundressourcen
    "wood": {"stackable": True, "max_stack": 64, "type": "material"},
    "dirt": {"stackable": True, "max_stack": 64, "type": "block"},
    "cobblestone": {"stackable": True, "max_stack": 64, "type": "block"},
    "coal": {"stackable": True, "max_stack": 64, "type": "material"},
    "iron_ore": {"stackable": True, "max_stack": 64, "type": "material"},
    "gold_ore": {"stackable": True, "max_stack": 64, "type": "material"},
    "iron_ingot": {"stackable": True, "max_stack": 64, "type": "material"},
    "gold_ingot": {"stackable": True, "max_stack": 64, "type": "material"},
    "stick": {"stackable": True, "max_stack": 64, "type": "material"},
    
    # Portal-Schlüssel
    "stone_key": {"stackable": False, "max_stack": 1, "type": "portal_activator"},
    "water_key": {"stackable": False, "max_stack": 1, "type": "portal_activator"},
    "gem_key": {"stackable": False, "max_stack": 1, "type": "portal_activator"},
    "nuclear_key": {"stackable": False, "max_stack": 1, "type": "portal_activator"},
    
    # Werkzeuge
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
    
    # Waffen
    "wooden_sword": {"stackable": False, "max_stack": 1, "type": "weapon", "damage": 4, "durability": 60},
    "stone_sword": {"stackable": False, "max_stack": 1, "type": "weapon", "damage": 5, "durability": 132},
    "iron_sword": {"stackable": False, "max_stack": 1, "type": "weapon", "damage": 6, "durability": 251},
    "diamond_sword": {"stackable": False, "max_stack": 1, "type": "weapon", "damage": 8, "durability": 1000},
    
    # Essen
    "apple": {"stackable": True, "max_stack": 64, "type": "food", "heal": 4, "hunger": 4},
    "bread": {"stackable": True, "max_stack": 64, "type": "food", "heal": 0, "hunger": 5},
    "cooked_fish": {"stackable": True, "max_stack": 64, "type": "food", "heal": 2, "hunger": 6},
    "raw_fish": {"stackable": True, "max_stack": 64, "type": "material"},
    
    # Heilen
    "healing_potion": {"stackable": True, "max_stack": 16, "type": "healing", "heal": 10},
    
    # Blöcke
    "portal_frame": {"stackable": True, "max_stack": 64, "type": "block"},
    "obsidian": {"stackable": True, "max_stack": 64, "type": "block"},
    "sand": {"stackable": True, "max_stack": 64, "type": "block"},
    "gravel": {"stackable": True, "max_stack": 64, "type": "block"},
    "torch": {"stackable": True, "max_stack": 64, "type": "block"},
    
    # Edelsteine
    "pearl": {"stackable": True, "max_stack": 64, "type": "material"},
    "crystal_shard": {"stackable": True, "max_stack": 64, "type": "material"},
    "amethyst": {"stackable": True, "max_stack": 64, "type": "material"},
    "ruby": {"stackable": True, "max_stack": 64, "type": "material"},
    "emerald": {"stackable": True, "max_stack": 64, "type": "material"},
    "diamond": {"stackable": True, "max_stack": 64, "type": "material"},
    "sapphire": {"stackable": True, "max_stack": 64, "type": "material"},
    "topaz": {"stackable": True, "max_stack": 64, "type": "material"},
    "opal": {"stackable": True, "max_stack": 64, "type": "material"},
    
    # Nuklear
    "uranium": {"stackable": True, "max_stack": 64, "type": "material"},
    "plutonium": {"stackable": True, "max_stack": 64, "type": "material"},
    "nuclear_waste": {"stackable": True, "max_stack": 64, "type": "material"},
    "lead": {"stackable": True, "max_stack": 64, "type": "material"},
    "reactor_core": {"stackable": True, "max_stack": 16, "type": "material"},
    "thorium": {"stackable": True, "max_stack": 64, "type": "material"},
    "radium": {"stackable": True, "max_stack": 64, "type": "material"},
    "enriched_uranium": {"stackable": True, "max_stack": 64, "type": "material"},
    "radioactive_crystal": {"stackable": True, "max_stack": 64, "type": "material"},
    
    # Wasserwelt
    "driftwood": {"stackable": True, "max_stack": 64, "type": "material"},
    "shell": {"stackable": True, "max_stack": 64, "type": "material"},
    "anchor_piece": {"stackable": True, "max_stack": 64, "type": "material"},
    "ship_plank": {"stackable": True, "max_stack": 64, "type": "material"},
    "rope": {"stackable": True, "max_stack": 64, "type": "material"},
    
    # Andere Materialien
    "clay": {"stackable": True, "max_stack": 64, "type": "material"},
    "coral": {"stackable": True, "max_stack": 64, "type": "material"},
    "seaweed": {"stackable": True, "max_stack": 64, "type": "material"},
    "slime_ball": {"stackable": True, "max_stack": 64, "type": "material"},
    "rotten_flesh": {"stackable": True, "max_stack": 64, "type": "material"},
    "shark_tooth": {"stackable": True, "max_stack": 64, "type": "material"},
    
    # Rüstungen
    "radiation_suit": {"stackable": False, "max_stack": 1, "type": "armor"},
}

MOB_PROPERTIES = {
    "slime": {"health": 10, "damage": 2, "speed": 1, "drop": "slime_ball", "color": GREEN, "size": (24, 24)},
    "zombie": {"health": 20, "damage": 3, "speed": 0.8, "drop": "rotten_flesh", "color": DARK_GREEN, "size": (24, 32)},
    "golem": {"health": 50, "damage": 5, "speed": 0.5, "drop": "iron_ingot", "color": GRAY, "size": (32, 40)},
    "bat": {"health": 5, "damage": 1, "speed": 2, "drop": None, "color": DARK_GRAY, "size": (16, 16)},
    "fish": {"health": 5, "damage": 0, "speed": 1.5, "drop": "raw_fish", "color": ORANGE, "size": (16, 12)},
    "shark": {"health": 30, "damage": 6, "speed": 1.2, "drop": "shark_tooth", "color": GRAY, "size": (40, 20)},
    "crystal_golem": {"health": 60, "damage": 6, "speed": 0.4, "drop": "crystal_shard", "color": PURPLE, "size": (32, 40)},
    "gem_spider": {"health": 15, "damage": 4, "speed": 1.5, "drop": "ruby", "color": RED, "size": (24, 16)},
    "mutant": {"health": 40, "damage": 8, "speed": 1.0, "drop": "uranium", "color": (150, 255, 0), "size": (28, 36)},
    "radioactive_slime": {"health": 25, "damage": 5, "speed": 0.8, "drop": "nuclear_waste", "color": (100, 255, 100), "size": (28, 28)}
}

# Welt-spezifische Item-Pools für Loot und Generation
WORLD_ITEM_POOLS = {
    "grassland": {
        "common": ["dirt", "cobblestone", "coal", "wood"],
        "uncommon": ["stick", "apple", "leaves"],
        "rare": ["iron_ore", "gold_ore"],
        "mob_drops": ["slime_ball", "rotten_flesh"]
    },
    "stone_world": {
        "common": ["stone", "cobblestone", "coal", "gravel", "iron_ore"],
        "uncommon": ["gold_ore", "stick"],
        "rare": ["diamond", "emerald", "ruby"],
        "mob_drops": ["iron_ingot", "rotten_flesh"]
    },
    "water_world": {
        "common": ["sand", "clay", "coral", "seaweed", "water"],
        "uncommon": ["pearl", "driftwood", "shell", "rope"],
        "rare": ["anchor_piece", "ship_plank", "cooked_fish"],
        "mob_drops": ["raw_fish", "shark_tooth", "cooked_fish"]
    },
    "gem_world": {
        "common": ["crystal", "amethyst", "obsidian"],
        "uncommon": ["ruby", "emerald", "diamond"],
        "rare": ["sapphire", "topaz", "opal"],
        "mob_drops": ["crystal_shard", "ruby", "emerald"]
    },
    "nuclear_world": {
        "common": ["contaminated_stone", "lead", "uranium", "nuclear_waste"],
        "uncommon": ["plutonium", "reactor_core", "radioactive_crystal"],
        "rare": ["thorium", "radium", "enriched_uranium"],
        "mob_drops": ["uranium", "nuclear_waste", "plutonium"]
    }
}

CRAFTING_RECIPES = {
    # Basis-Werkzeuge
    "stick": {"ingredients": {"wood": 2}, "result_count": 4},
    "wooden_pickaxe": {"ingredients": {"wood": 3, "stick": 2}, "result_count": 1},
    "wooden_axe": {"ingredients": {"wood": 3, "stick": 2}, "result_count": 1},
    "wooden_shovel": {"ingredients": {"wood": 1, "stick": 2}, "result_count": 1},
    "wooden_sword": {"ingredients": {"wood": 2, "stick": 1}, "result_count": 1},
    
    # Stein-Werkzeuge
    "stone_pickaxe": {"ingredients": {"cobblestone": 3, "stick": 2}, "result_count": 1},
    "stone_axe": {"ingredients": {"cobblestone": 3, "stick": 2}, "result_count": 1},
    "stone_shovel": {"ingredients": {"cobblestone": 1, "stick": 2}, "result_count": 1},
    "stone_sword": {"ingredients": {"cobblestone": 2, "stick": 1}, "result_count": 1},
    
    # Eisen-Werkzeuge
    "iron_ingot": {"ingredients": {"iron_ore": 1, "coal": 1}, "result_count": 1},
    "gold_ingot": {"ingredients": {"gold_ore": 1, "coal": 1}, "result_count": 1},
    "iron_pickaxe": {"ingredients": {"iron_ingot": 3, "stick": 2}, "result_count": 1},
    "iron_axe": {"ingredients": {"iron_ingot": 3, "stick": 2}, "result_count": 1},
    "iron_shovel": {"ingredients": {"iron_ingot": 1, "stick": 2}, "result_count": 1},
    "iron_sword": {"ingredients": {"iron_ingot": 2, "stick": 1}, "result_count": 1},
    
    # Diamant-Werkzeuge
    "diamond_pickaxe": {"ingredients": {"diamond": 3, "stick": 2}, "result_count": 1},
    "diamond_sword": {"ingredients": {"diamond": 2, "stick": 1}, "result_count": 1},
    
    # Portal-Materialien
    "portal_frame": {"ingredients": {"obsidian": 4, "diamond": 1}, "result_count": 1},
    "stone_key": {"ingredients": {"cobblestone": 8, "iron_ingot": 1}, "result_count": 1},
    "water_key": {"ingredients": {"pearl": 4, "crystal_shard": 2}, "result_count": 1},
    "gem_key": {"ingredients": {"ruby": 2, "emerald": 2, "amethyst": 2}, "result_count": 1},
    
    # Nuklearer Schlüssel
    "nuclear_key": {"ingredients": {"uranium": 4, "lead": 4, "reactor_core": 1}, "result_count": 1},
    
    # Radioaktiver Schutzanzug (nur mit Nuclear-World-Materialien)
    "radiation_suit": {"ingredients": {"lead": 8, "uranium": 2, "radioactive_crystal": 1}, "result_count": 1},
    
    # Verbrauchsmaterialien
    "healing_potion": {"ingredients": {"apple": 2, "crystal_shard": 1}, "result_count": 1},
    "bread": {"ingredients": {"seaweed": 3}, "result_count": 2},
    "cooked_fish": {"ingredients": {"raw_fish": 1, "coal": 1}, "result_count": 1},
    "torch": {"ingredients": {"stick": 1, "coal": 1}, "result_count": 4},
}