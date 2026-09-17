"""Build script: writes clean utils/world_gen.py"""
from pathlib import Path

OUT = Path("utils") / "world_gen.py"
assert OUT.parent == Path("utils")

# ------------------------------------------------------------------
# Complete file content as a single triple-quoted string
# ------------------------------------------------------------------
content = r"""
""" + r"""
3D-Voxelwelt-Generierung fuer PixelPortalRift.
==============================================

Die Klasse World repraesentiert eine einzelne Dimension als echtes
3D-Voxel-Gitter: X/Z = horizontale Grundflaeche, Y = Hoehe (nach oben).
Bloecke liegen in einem Dict {(x, y, z): block_name}. Fehlende Eintraege
bedeuten Luft.

Die Generierung ist chunkweise organisiert (CHUNK_SIZE x CHUNK_SIZE).
Eine vollstaendige Generierung berechnet zuerst eine 2D-Hoehenkarte mit
numpy (sin/cos + Rauschen) und erzeugt dann alle Chunks der Reihe nach.
Später koennen weitere Chunks beim Erkunden nachgeladen werden.

Block-Eigenschaften (solid, hardness, tool, drop, color) kommen aus
BLOCK_PROPERTIES in utils/constants.py — keine hartkodierten Werte.
""" + r"""

import math
import random

import numpy as np

from utils.constants import (
    BLOCK_PROPERTIES,
    CHUNK_HEIGHT,
    CHUNK_SIZE,

class World:
    """Erzeugt und verwaltet eine einzelne Dimension im 3D-Voxel-Grid."""

    def __init__(self, dimension="grassland", seed=None, skip_generation=False):
        if dimension not in DIMENSIONS:
            raise ValueError(f"Unbekannte Dimension: {dimension}")
        self.dimension = dimension
        self.seed = seed if seed is not None else random.randrange(1_000_000)
        self.width = WORLD_WIDTH
        self.depth = WORLD_DEPTH
        self.height = min(CHUNK_HEIGHT, WORLD_HEIGHT)
        self.dimension_data = DIMENSIONS[dimension]
        self.blocks = {}
        self.generated_chunks = set()
        self.portals = []
        self.respawn_queue = []
        self.spawn_point = None
        self._heightmap = None
        random.seed(self.seed)
        if not skip_generation:
            self.generate()

    # ------------------------------------------------------------
    # Chunk-Hilfsfunktionen
    # ------------------------------------------------------------
    @staticmethod
    def chunk_coords(x, z):
        """Welt-Koordinaten (x, z) -> Chunk-Koordinaten (cx, cz)."""
        return int(x) // CHUNK_SIZE, int(z) // CHUNK_SIZE

    def chunk_range_for_player(self, px, pz, radius=2):
        """Alle Chunk-Koordinaten im Umkreis `radius` um den Spieler."""
        cx, cz = self.chunk_coords(px, pz)
        out = []
        max_cx = math.ceil(self.width / CHUNK_SIZE)
        max_cz = math.ceil(self.depth / CHUNK_SIZE)
        for dx in range(-radius, radius + 1):
            for dz in range(-radius, radius + 1):
                nx, nz = cx + dx, cz + dz
                if 0 <= nx < max_cx and 0 <= nz < max_cz:
                    out.append((nx, nz))
        return out

    # ------------------------------------------------------------
    # Blockzugriff (weltweit 3D, bounds-geprüft)
    # ------------------------------------------------------------
    def get_block(self, x, y, z):
        """Block-Name an (x,y,z) oder None (Luft / ausserhalb)."""
        return self.blocks.get((int(x), int(y), int(z)))

    def set_block(self, x, y, z, block_name):
        """Setzt oder entfernt (air) einen Block."""
        position = (int(x), int(y), int(z))
        if not (0 <= position[0] < self.width
                and 0 <= position[2] < self.depth
                and 0 <= position[1] < self.height):
            return False
        if block_name in (None, "air"):
            self.blocks.pop(position, None)
        else:
            self.blocks[position] = block_name
        return True

    def is_solid(self, x, y=None, z=None):
        """True, falls ein fester Block an (x,y,z) liegt."""
        block = x if y is None else self.get_block(x, y, z)
        return bool(block and BLOCK_PROPERTIES.get(block, {}).get("solid", True))

    def get_height_at(self, x, z):
        """Hoechste feste Block-Y-Position bei (x,z) oder -1."""
        for y in range(self.height - 1, VOID_Y - 1, -1):
            if self.is_solid(x, y, z):
                return y
        return -1

    DIMENSIONS,
    TILE_SIZE,
    VOID_Y,
    WORLD_DEPTH,
    WORLD_HEIGHT,
    WORLD_WIDTH,
)