import random
import math
import pygame
from utils.constants import (
    WORLD_WIDTH, WORLD_HEIGHT, TILE_SIZE, DIMENSIONS, BLOCK_PROPERTIES, WORLD_ITEM_POOLS
)

class World:
    def __init__(self, dimension="grassland", seed=None):
        self.dimension = dimension
        self.seed = seed if seed else random.randint(0, 999999)
        self.width = WORLD_WIDTH
        self.height = WORLD_HEIGHT
        self.blocks = [[None for _ in range(self.height)] for _ in range(self.width)]
        self.dimension_data = DIMENSIONS[dimension]
        self.portals = []
        self.spawn_point = (self.width // 2 * TILE_SIZE, 0)

        random.seed(self.seed)
        self.generate()

    # =========================================================
    # WORLD GENERATION
    # =========================================================
    def generate(self):
        ground_level = self.dimension_data["ground_level"]
        available_blocks = self.dimension_data["blocks"]

        heights = self.generate_terrain_heights(ground_level)

        for x in range(self.width):
            ground_y = heights[x]
            for y in range(self.height):
                if y < ground_y - 5:
                    self.blocks[x][y] = "air"
                elif y == ground_y:
                    self.blocks[x][y] = self.get_surface_block()
                elif y < ground_y + 4:
                    self.blocks[x][y] = self.get_subsurface_block()
                else:
                    self.blocks[x][y] = self.get_underground_block(y - ground_y, available_blocks)

        self.generate_features(heights)
        self.generate_ores(available_blocks)

        spawn_x = self.width // 2
        spawn_y = heights[spawn_x] - 3
        self.spawn_point = (spawn_x * TILE_SIZE, spawn_y * TILE_SIZE)

    def generate_terrain_heights(self, base_level):
        heights = []
        for x in range(self.width):
            noise = (
                math.sin(x * 0.05) * 5 +
                math.sin(x * 0.02) * 10 +
                random.random() * 2 - 1
            )
            heights.append(int(base_level + noise))
        return heights

    # =========================================================
    # BLOCK TYPES
    # =========================================================
    def get_surface_block(self):
        return {
            "grassland": "grass",
            "stone_world": "stone",
            "water_world": "sand",
            "gem_world": "crystal",
            "nuclear_world": "contaminated_stone"
        }.get(self.dimension, "grass")

    def get_subsurface_block(self):
        return {
            "grassland": "dirt",
            "stone_world": "cobblestone",
            "water_world": "sand",
            "gem_world": "amethyst",
            "nuclear_world": "lead"
        }.get(self.dimension, "dirt")

    def get_underground_block(self, depth, available_blocks):
        return random.choice(available_blocks)

    # =========================================================
    # FEATURES / ORES
    # =========================================================
    def generate_features(self, heights):
        if self.dimension == "grassland":
            self.generate_trees(heights)

    def generate_trees(self, heights):
        x = 10
        while x < self.width - 10:
            if random.random() < 0.15:
                ground_y = heights[x]
                for ty in range(random.randint(4, 7)):
                    if ground_y - ty - 1 >= 0:
                        self.blocks[x][ground_y - ty - 1] = "wood"
                x += random.randint(5, 12)
            else:
                x += 1

    def generate_ores(self, available_blocks):
        ore_blocks = [b for b in available_blocks if "ore" in b]
        for ore in ore_blocks:
            for _ in range(random.randint(15, 30)):
                x = random.randint(0, self.width - 1)
                y = random.randint(self.dimension_data["ground_level"] + 5, self.height - 5)
                self.blocks[x][y] = ore
        
        # Zusätzliche generische Erzgenerierung basierend auf WORLD_ITEM_POOLS
        pool = WORLD_ITEM_POOLS.get(self.dimension, {})
        rare_items = pool.get("rare", [])
        for item in rare_items:
            if item not in ore_blocks and item in BLOCK_PROPERTIES:
                for _ in range(random.randint(3, 8)):
                    x = random.randint(0, self.width - 1)
                    y = random.randint(self.dimension_data["ground_level"] + 10, self.height - 5)
                    self.blocks[x][y] = item

    # =========================================================
    # BLOCK ACCESS (FLOAT-SAFE)
    # =========================================================
    def get_block(self, x, y):
        x = int(x)
        y = int(y)
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.blocks[x][y]
        return None

    def set_block(self, x, y, block):
        x = int(x)
        y = int(y)
        if 0 <= x < self.width and 0 <= y < self.height:
            self.blocks[x][y] = block
            return True
        return False

    def break_block(self, x, y):
        x = int(x)
        y = int(y)
        block = self.get_block(x, y)
        if block and block != "air":
            props = BLOCK_PROPERTIES.get(block, {})
            drop = props.get("drop")
            self.set_block(x, y, "air")
            return drop
        return None

    def is_solid(self, block):
        if block is None or block == "air":
            return False
        return BLOCK_PROPERTIES.get(block, {}).get("solid", True)

    # =========================================================
    # SAVE / LOAD
    # =========================================================
    def get_save_data(self):
        return {
            "dimension": self.dimension,
            "seed": self.seed,
            "blocks": self.blocks,
            "spawn_point": self.spawn_point,
            "portals": self.portals
        }

    def load_save_data(self, data):
        self.dimension = data.get("dimension", self.dimension)
        self.seed = data.get("seed", self.seed)
        self.blocks = data.get("blocks", self.blocks)
        self.spawn_point = data.get("spawn_point", self.spawn_point)
        self.portals = data.get("portals", [])
        self.dimension_data = DIMENSIONS.get(self.dimension, DIMENSIONS["grassland"])