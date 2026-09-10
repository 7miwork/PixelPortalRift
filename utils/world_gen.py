"""3D-Voxelwelt-Generierung fuer PixelPortalRift."""

import math
import random

from utils.constants import (
    BLOCK_PROPERTIES,
    CHUNK_HEIGHT,
    CHUNK_SIZE,
    DIMENSIONS,
    WORLD_HEIGHT,
    WORLD_WIDTH,
)


class World:
    """Erzeugt und verwaltet eine einzelne Dimension im 3D-Voxel-Grid."""

    def __init__(self, dimension="grassland", seed=None, skip_generation=False):
        if dimension not in DIMENSIONS:
            raise ValueError(f"Unbekannte Dimension: {dimension}")
        self.dimension = dimension
        self.seed = seed if seed is not None else random.randrange(1_000_000)
        self.width = WORLD_WIDTH
        self.depth = WORLD_WIDTH
        self.height = min(CHUNK_HEIGHT, WORLD_HEIGHT)
        self.dimension_data = DIMENSIONS[dimension]
        self.blocks = {}
        self.generated_chunks = set()
        self.portals = []
        self.respawn_queue = []
        self.spawn_point = None
        if not skip_generation:
            center = self.chunk_coords(self.width // 2, self.depth // 2)
            self.generate_chunk(*center)

    @staticmethod
    def chunk_coords(x, z):
        return int(x) // CHUNK_SIZE, int(z) // CHUNK_SIZE

    def chunk_range_for_player(self, px, pz, radius=2):
        center_x, center_z = self.chunk_coords(px, pz)
        return [
            (center_x + dx, center_z + dz)
            for dx in range(-radius, radius + 1)
            for dz in range(-radius, radius + 1)
            if 0 <= center_x + dx < math.ceil(self.width / CHUNK_SIZE)
            and 0 <= center_z + dz < math.ceil(self.depth / CHUNK_SIZE)
        ]

    def _hash(self, x, z, salt=0):
        value = x * 374761393 + z * 668265263 + self.seed * 1442695041 + salt * 1013904223
        value = (value ^ (value >> 13)) * 1274126177
        return ((value ^ (value >> 16)) & 0xFFFFFFFF) / 0xFFFFFFFF

    def terrain_height(self, x, z):
        base = self.dimension_data["ground_level"]
        wave = math.sin(x * 0.055) * 4 + math.sin(z * 0.047) * 4
        broad = math.sin((x + z) * 0.018) * 6
        noise = (self._hash(x, z) - 0.5) * 3
        return max(3, min(self.height - 5, int(base + wave + broad + noise)))

    def get_surface_block(self):
        return {
            "grassland": "grass", "stone_world": "stone", "water_world": "sand",
            "gem_world": "crystal", "nuclear_world": "contaminated_stone",
        }.get(self.dimension, "grass")

    def get_subsurface_block(self):
        return {
            "grassland": "dirt", "stone_world": "cobblestone", "water_world": "sand",
            "gem_world": "amethyst", "nuclear_world": "lead",
        }.get(self.dimension, "dirt")

    def _underground_block(self, x, y, z):
        available = self.dimension_data["blocks"]
        candidates = [block for block in available if "ore" not in block] or ["stone"]
        ores = [block for block in available if "ore" in block]
        if ores and self._hash(x, z, y) < 0.018:
            return ores[int(self._hash(x, z, y + 1) * len(ores))]
        return candidates[int(self._hash(x, z, y + 2) * len(candidates))]

    def _is_cave(self, x, y, z, surface):
        if y < surface + 6 or y >= self.height - 2:
            return False
        value = (
            math.sin(x * 0.19 + z * 0.11 + self.seed * 0.01)
            + math.sin(y * 0.23 + x * 0.07)
            + math.sin(z * 0.17 - y * 0.13)
        ) / 3
        return value > 0.67 and self._hash(x, z, y + 11) > 0.22

    def generate_chunk(self, cx, cz):
        """Generiert genau einen Chunk und gibt seine Blockdaten zurueck."""
        if (cx, cz) in self.generated_chunks:
            return self.get_chunk_blocks(cx, cz)
        x_start, z_start = max(0, cx * CHUNK_SIZE), max(0, cz * CHUNK_SIZE)
        x_end, z_end = min(self.width, x_start + CHUNK_SIZE), min(self.depth, z_start + CHUNK_SIZE)
        for x in range(x_start, x_end):
            for z in range(z_start, z_end):
                surface = self.terrain_height(x, z)
                for y in range(surface + 1):
                    if self._is_cave(x, y, z, surface):
                        continue
                    if y == surface:
                        block = self.get_surface_block()
                    elif y >= surface - 3:
                        block = self.get_subsurface_block()
                    else:
                        block = self._underground_block(x, y, z)
                    self.blocks[(x, y, z)] = block
                if self.dimension == "grassland" and self._hash(x, z, 20) > 0.985:
                    self._generate_tree(x, surface + 1, z)
        self.generated_chunks.add((cx, cz))
        if self.spawn_point is None:
            spawn_x, spawn_z = self.width // 2, self.depth // 2
            self.spawn_point = (spawn_x + 0.5, self.terrain_height(spawn_x, spawn_z) + 2, spawn_z + 0.5)
        return self.get_chunk_blocks(cx, cz)

    def _generate_tree(self, x, y, z):
        for offset in range(4):
            if y + offset < self.height:
                self.blocks[(x, y + offset, z)] = "wood"
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                for dy in range(2, 4):
                    if abs(dx) + abs(dz) < 4 and y + dy < self.height:
                        self.blocks[(x + dx, y + dy, z + dz)] = "leaves"

    def generate_chunks(self, chunks):
        for cx, cz in chunks:
            self.generate_chunk(cx, cz)

    def get_chunk_blocks(self, cx, cz):
        x_start, z_start = cx * CHUNK_SIZE, cz * CHUNK_SIZE
        x_end, z_end = x_start + CHUNK_SIZE, z_start + CHUNK_SIZE
        return [(x, y, z, block) for (x, y, z), block in self.blocks.items()
                if x_start <= x < x_end and z_start <= z < z_end]

    def get_block(self, x, y, z):
        return self.blocks.get((int(x), int(y), int(z)))

    def set_block(self, x, y, z, block_name):
        position = (int(x), int(y), int(z))
        if not (0 <= position[0] < self.width and 0 <= position[2] < self.depth
                and 0 <= position[1] < self.height):
            return False
        if block_name in (None, "air"):
            self.blocks.pop(position, None)
        else:
            self.blocks[position] = block_name
        return True

    def is_solid(self, x, y=None, z=None):
        block = x if y is None else self.get_block(x, y, z)
        return bool(block and BLOCK_PROPERTIES.get(block, {}).get("solid", True))

    def break_block(self, x, y, z):
        block = self.get_block(x, y, z)
        if not block:
            return None
        drop = BLOCK_PROPERTIES.get(block, {}).get("drop")
        self.set_block(x, y, z, None)
        properties = BLOCK_PROPERTIES.get(block, {})
        if properties.get("respawnable"):
            self.respawn_queue.append({"x": int(x), "y": int(y), "z": int(z),
                                       "block": block, "time_left": properties.get("respawn_time", 60000)})
        return drop

    def update(self, dt):
        for entry in self.respawn_queue[:]:
            entry["time_left"] -= dt * 1000
            if entry["time_left"] <= 0:
                if self.get_block(entry["x"], entry["y"], entry["z"]) is None:
                    self.set_block(entry["x"], entry["y"], entry["z"], entry["block"])
                self.respawn_queue.remove(entry)

    def get_save_data(self):
        return {
            "dimension": self.dimension,
            "seed": self.seed,
            "blocks": {f"{x},{y},{z}": block for (x, y, z), block in self.blocks.items()},
            "generated_chunks": [list(chunk) for chunk in self.generated_chunks],
            "spawn_point": list(self.spawn_point) if self.spawn_point else None,
            "portals": self.portals,
            "respawn_queue": self.respawn_queue,
        }

    def load_save_data(self, data):
        self.dimension = data.get("dimension", self.dimension)
        self.seed = data.get("seed", self.seed)
        self.dimension_data = DIMENSIONS.get(self.dimension, DIMENSIONS["grassland"])
        self.blocks = {}
        for key, block in data.get("blocks", {}).items():
            try:
                position = tuple(map(int, key.split(",")))
                if len(position) == 3:
                    self.blocks[position] = block
            except (TypeError, ValueError):
                continue
        self.generated_chunks = {tuple(chunk) for chunk in data.get("generated_chunks", []) if len(chunk) == 2}
        self.spawn_point = tuple(data["spawn_point"]) if data.get("spawn_point") else None
        self.portals = data.get("portals", [])
        self.respawn_queue = data.get("respawn_queue", [])