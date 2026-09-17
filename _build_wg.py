"""Build script for clean utils/world_gen.py"""
from pathlib import Path

lines = []
lines.append('"""3D-Voxelwelt-Generierung fuer PixelPortalRift."""')
lines.append('')
lines.append('import math')
lines.append('import random')
lines.append('')
lines.append('from utils.constants import (')
lines.append('    BLOCK_PROPERTIES,')
lines.append('    CHUNK_HEIGHT,')
lines.append('    CHUNK_SIZE,')
lines.append('    DIMENSIONS,')
lines.append('    TILE_SIZE,')
lines.append('    VOID_Y,')
lines.append('    WORLD_DEPTH,')
lines.append('    WORLD_HEIGHT,')
lines.append('    WORLD_WIDTH,')
lines.append(')')

OUT = Path("utils/world_gen.py")
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Part 1 done: {len(lines)} lines written")
