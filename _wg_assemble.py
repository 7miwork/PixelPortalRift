"""Assemble utils/world_gen.py from _wg_part*.txt, compile, and run tests."""
from __future__ import annotations

import os
import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PARTS = [ROOT / f"_wg_part{i}.txt" for i in range(1, 5)]
OUT = ROOT / "utils" / "world_gen.py"

# Teil-Dateien sind geloescht – world_gen.py ist die kanonische Datei.
# Nur assemblieren, wenn alle Teile vorhanden sind; sonst nur testen.
if all(part.exists() for part in PARTS):
    chunks = []
    for part in PARTS:
        text = part.read_text(encoding="utf-8")
        if not text.endswith("\n"):
            text += "\n"
        chunks.append(text)

    OUT.write_text("\n".join(chunks), encoding="utf-8")
    print(f"assembled {OUT} ({OUT.stat().st_size} bytes)")
else:
    print("part files not present – skipping assembly, testing existing "
          f"{OUT}")

py_compile.compile(str(OUT), doraise=True)
print("py_compile OK")

sys.path.insert(0, str(ROOT))
from utils.world_gen import World  # noqa: E402

# 1) Fast path: skip full generation, then generate explicitly.
# Kleine Testwelt (64x64), damit der Voll-Lauf schnell bleibt – die echte
# Welt ist 1000x1000 und wird nur lazy (chunkweise) erzeugt.
TEST_W = 64
world = World("grassland", seed=42, skip_generation=True,
              width=TEST_W, depth=TEST_W)
assert world.spawn_point is None
world.generate()
assert world.spawn_point is not None, "spawn point missing"
assert world.block_count() > 0, "no blocks generated"
assert len(world.generated_chunks) > 0, "no chunks marked generated"
print(
    "generated:",
    world.block_count(),
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

# 4) Save / load round-trip (inkl. modified_chunks)
data = world.get_save_data()
world2 = World("grassland", seed=1, skip_generation=True,
               width=TEST_W, depth=TEST_W)
world2.load_save_data(data)
assert world2.block_count() == world.block_count()
assert world2.spawn_point == world.spawn_point
assert set(world2.generated_chunks) == set(world.generated_chunks)
assert world2.modified_chunks == world.modified_chunks
print("save/load OK,", world2.block_count(), "blocks restored,",
      len(world2.modified_chunks), "modified chunks")

# 5) Non-grassland dimension (cheap: skip full generation)
stone = World("stone_world", seed=7, skip_generation=True)
assert stone.dimension == "stone_world"
print("stone_world init OK")

# 6) Lazy-Pfad wie ihn VoxelWorld.generate_dimension() nutzt
# (echte Weltgrenzen 1000x1000, nur 3x3 Chunks um die Mitte erzeugt)
lazy = World("grassland", seed=99)
wanted = lazy.chunk_range_for_player(lazy.width // 2, lazy.depth // 2, 1)
lazy.generate_chunks(wanted)
lazy_sp = lazy.ensure_spawn_point()
assert lazy_sp is not None
assert lazy.block_count() > 0
lgx, lgz = int(lazy_sp[0]), int(lazy_sp[2])
lground = lazy.terrain_height(lgx, lgz)
assert lazy.is_solid(lgx, lground, lgz)
for dx in (-1, 0, 1):
    for dz in (-1, 0, 1):
        col_ground = lazy.terrain_height(lgx + dx, lgz + dz)
        for dy in range(1, 6):
            b = lazy.get_block(lgx + dx, col_ground + dy, lgz + dz)
            assert b is None, f"lazy spawn blocked at ({lgx+dx},{col_ground+dy},{lgz+dz}): {b}"
print("lazy path OK,", lazy.block_count(), "blocks,", len(wanted), "chunks, spawn:", lazy_sp)

# 7) Chunk-Entladen: unveraendert wird gedroppt und identisch regeneriert,
#    Spieler-aenderte Chunks bleiben erhalten.
far = World("grassland", seed=5, skip_generation=True,
            width=TEST_W, depth=TEST_W)
far.generate_chunks(far.chunk_range_for_player(TEST_W // 2, TEST_W // 2, 2))
victim = sorted(far.generated_chunks - far.modified_chunks)
assert victim, "expected at least one unmodified chunk"
cx, cz = victim[0]
before = sorted(far.get_chunk_blocks(cx, cz))
assert before, "victim chunk should have blocks"
assert far.drop_chunk(cx, cz), "unmodified chunk must be droppable"
assert (cx, cz) not in far.generated_chunks
assert far.get_chunk_blocks(cx, cz) == []
far.generate_chunk(cx, cz)
after = sorted(far.get_chunk_blocks(cx, cz))
assert after == before, "regenerated chunk differs from original"

# Spieler-Aenderung: drop muss abgelehnt werden
mx, mz = cx, cz
gy = far.terrain_height(mx * 16 + 8, mz * 16 + 8)
assert far.set_block(mx * 16 + 8, gy + 5, mz * 16 + 8, "stone")
assert (mx, mz) in far.modified_chunks
assert not far.drop_chunk(mx, mz), "modified chunk must not be dropped"
assert far.get_block(mx * 16 + 8, gy + 5, mz * 16 + 8) == "stone"
print("drop/regenerate OK,", len(before), "blocks in chunk", (cx, cz))

# 8) Mesh-Culling: der optimierte Chunk.render()-Pfad (lokale Solid-Menge)
#    muss exakt die Flaechen liefern, die die Referenz-Regel ergibt (Nachbar
#    weltweit ueber World.get_block statt ueber die Chunk-eigene Menge).
try:
    os.chdir(ROOT)  # Ursina laedt Modelle relativ zum cwd (asset_folder)
    import utils.voxel_world as vw
    from utils.constants import BLOCK_PROPERTIES

    class _FakeMesh:
        def __init__(self, vertices=None, triangles=None, uvs=None, **kw):
            self.vertices, self.triangles, self.uvs = vertices, triangles, uvs

    class _FakeEntity:
        def __init__(self, **kw):
            self.model = kw.get("model")
            for key, value in kw.items():
                setattr(self, key, value)

        def removeNode(self):
            pass

    class _FakeTextureLibrary:
        """Minimal-Ersatz: je Block ein eindeutiges UV-Rechteck (kein PIL)."""

        def __init__(self):
            names = sorted(b for b in BLOCK_PROPERTIES
                           if b != "air"
                           and BLOCK_PROPERTIES[b].get("solid", True))
            self.atlas_uv = {
                name: (i * 0.01, i * 0.02, i * 0.01 + 0.005, i * 0.02 + 0.01)
                for i, name in enumerate(names)
            }
            self.atlas_texture = None

        def build_atlas(self):
            pass

    vw.Mesh, vw.Entity = _FakeMesh, _FakeEntity
    directions = ((0, 1, 0), (0, -1, 0), (1, 0, 0),
                  (-1, 0, 0), (0, 0, 1), (0, 0, -1))

    def _solid(name):
        return (name is not None
                and BLOCK_PROPERTIES.get(name, {}).get("solid", True))

    def _reference_faces(world_obj, tcx, tcz):
        faces = set()
        for x, y, z, name in world_obj.get_chunk_blocks(tcx, tcz):
            if not BLOCK_PROPERTIES.get(name, {}).get("solid", True):
                continue
            for d in directions:
                if not _solid(world_obj.get_block(x + d[0], y + d[1], z + d[2])):
                    faces.add(((x, y, z), d))
        return faces

    def _rendered_faces(world_obj, chunk, lib):
        vertices = chunk.entity.model.vertices
        uvs = chunk.entity.model.uvs
        triangles = chunk.entity.model.triangles
        assert len(vertices) == len(uvs) == len(triangles) * 2, \
            "Vertex/UV/Triangle-Verhaeltnis falsch"
        faces = set()
        for i in range(0, len(vertices), 4):
            quad = vertices[i:i + 4]
            centers, axis, plane = {}, None, None
            for k in range(3):
                values = {v[k] for v in quad}
                if len(values) == 1:
                    axis, plane = k, values.pop()
                else:
                    centers[k] = round(sum(v[k] for v in quad) / 4)
            assert axis is not None, "Quad nicht planar/achsparallel"
            # Flaeche liegt zwischen solidem Block und Luft (round() wuerde
            # bei x±0.5 bankmaessig runden) -> Blockseite eindeutig.
            candidates = [int(plane - 0.5), int(plane + 0.5)]
            solid_side = [
                c for c in candidates
                if _solid(world_obj.get_block(
                    *[c if k == axis else centers[k] for k in range(3)]))
            ]
            assert len(solid_side) == 1, f"Flaechenlage unklar: {candidates}"
            centers[axis] = solid_side[0]
            center = tuple(centers[k] for k in range(3))
            normal = [0, 0, 0]
            normal[axis] = 1 if plane > centers[axis] else -1
            key = (center, tuple(normal))
            assert key not in faces, f"doppelte Flaeche: {key}"
            faces.add(key)
            u0, v0, u1, v1 = lib.atlas_uv[world_obj.get_block(*center)]
            assert uvs[i:i + 4] == [(u0, v0), (u0, v1), (u1, v1), (u1, v0)], \
                "UV-Reihenfolge falsch"
            assert triangles[i // 2:i // 2 + 2] == \
                [(i, i + 1, i + 2), (i, i + 2, i + 3)], "Indizes falsch"
        return faces

    lib = _FakeTextureLibrary()
    face_total = 0
    for tcx, tcz in sorted(far.generated_chunks):
        chunk = vw.Chunk(tcx, tcz, lib, None, world_data=far)
        for x, y, z, name in far.get_chunk_blocks(tcx, tcz):
            chunk.set_block(x, y, z, name)
        chunk.render()
        rendered = _rendered_faces(far, chunk, lib)
        expected = _reference_faces(far, tcx, tcz)
        assert rendered == expected, (
            f"Chunk {(tcx, tcz)}: {len(rendered)} statt {len(expected)} Faces; "
            f"fehlend={sorted(expected - rendered)[:3]}, "
            f"zusaetzlich={sorted(rendered - expected)[:3]}"
        )
        face_total += len(rendered)
    print("mesh culling OK,", face_total, "faces in",
          len(far.generated_chunks), "chunks (identisch zur Referenzregel)")
except ImportError as exc:  # Ursina/Panda3D nicht verfuegbar -> ueberspringen
    print("mesh culling test skipped:", exc)

print("ALL TESTS PASSED")
