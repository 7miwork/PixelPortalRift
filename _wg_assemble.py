"""Assemble utils/world_gen.py from _wg_part*.txt, compile, and run tests."""
from __future__ import annotations

import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PARTS = [ROOT / f"_wg_part{i}.txt" for i in range(1, 5)]
OUT = ROOT / "utils" / "world_gen.py"

chunks = []
for part in PARTS:
    text = part.read_text(encoding="utf-8")
    if not text.endswith("\n"):
        text += "\n"
    chunks.append(text)

OUT.write_text("\n".join(chunks), encoding="utf-8")
print(f"assembled {OUT} ({OUT.stat().st_size} bytes)")

py_compile.compile(str(OUT), doraise=True)
print("py_compile OK")

sys.path.insert(0, str(ROOT))
from utils.world_gen import World  # noqa: E402

# 1) Fast path: skip full generation, then generate explicitly.
world = World("grassland", seed=42, skip_generation=True)
assert world.spawn_point is None
world.generate()
assert world.spawn_point is not None, "spawn point missing"
assert len(world.blocks) > 0, "no blocks generated"
assert len(world.generated_chunks) > 0, "no chunks marked generated"
print(
    "generated:",
    len(world.blocks),
    "blocks,",
    len(world.generated_chunks),
    "chunks, spawn:",
    world.spawn_point,
)

# 2) Accessors + Spawn pruefen
sx, sy, sz = (int(v) for v in world.spawn_point)
ground = world.terrain_height(sx, sz)
print("ground below spawn:", world.get_block(sx, ground, sz), "| spawn y:", sy)
assert world.is_solid(sx, ground, sz), "ground below spawn must be solid"

# Spawn-Area (3x3 x 5 hoehe ueber JEDEM Spaltengrund) muss frei sein
for dx in (-1, 0, 1):
    for dz in (-1, 0, 1):
        col_ground = world.terrain_height(sx + dx, sz + dz)
        for dy in range(1, 6):
            b = world.get_block(sx + dx, col_ground + dy, sz + dz)
            assert b is None, f"spawn blocked at ({sx+dx},{col_ground+dy},{sz+dz}): {b}"
print("spawn area clear OK (ground y =", ground, ")")

assert world.set_block(sx, sy + 5, sz, "stone")
assert world.get_block(sx, sy + 5, sz) == "stone"
assert world.is_solid(sx, sy + 5, sz)
assert world.get_height_at(sx, sz) >= sy + 5
print("height_at spawn column:", world.get_height_at(sx, sz))

# 3) break_block + respawn queue
world.set_block(sx, sy + 5, sz, "coal_ore")
drop = world.break_block(sx, sy + 5, sz)
assert world.get_block(sx, sy + 5, sz) is None
assert drop is not None, "coal_ore should drop something"
assert any(e["block"] == "coal_ore" for e in world.respawn_queue)
world.update(100000.0)  # advance far enough for respawn
assert world.get_block(sx, sy + 5, sz) == "coal_ore", "respawn failed"
print("break/respawn OK, drop:", drop)

# 4) Save / load round-trip
data = world.get_save_data()
world2 = World("grassland", seed=1, skip_generation=True)
world2.load_save_data(data)
assert len(world2.blocks) == len(world.blocks)
assert world2.spawn_point == world.spawn_point
assert set(world2.generated_chunks) == set(world.generated_chunks)
print("save/load OK,", len(world2.blocks), "blocks restored")

# 5) Non-grassland dimension (cheap: skip full generation)
stone = World("stone_world", seed=7, skip_generation=True)
assert stone.dimension == "stone_world"
print("stone_world init OK")

# 6) Lazy-Pfad wie ihn VoxelWorld.generate_dimension() nutzt
lazy = World("grassland", seed=99)
wanted = lazy.chunk_range_for_player(lazy.width // 2, lazy.depth // 2, 1)
lazy.generate_chunks(wanted)
lazy_sp = lazy.ensure_spawn_point()
assert lazy_sp is not None
assert len(lazy.blocks) > 0
lgx, lgz = int(lazy_sp[0]), int(lazy_sp[2])
lground = lazy.terrain_height(lgx, lgz)
assert lazy.is_solid(lgx, lground, lgz)
for dx in (-1, 0, 1):
    for dz in (-1, 0, 1):
        col_ground = lazy.terrain_height(lgx + dx, lgz + dz)
        for dy in range(1, 6):
            b = lazy.get_block(lgx + dx, col_ground + dy, lgz + dz)
            assert b is None, f"lazy spawn blocked at ({lgx+dx},{col_ground+dy},{lgz+dz}): {b}"
print("lazy path OK,", len(lazy.blocks), "blocks,", len(wanted), "chunks, spawn:", lazy_sp)

print("ALL TESTS PASSED")
