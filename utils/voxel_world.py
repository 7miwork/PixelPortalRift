"""
utils/voxel_world.py – 3D-Voxelwelt (Ursina)
============================================

Seit der 3D-Migration ist die Welt kein 2D-Tile-Array mehr, sondern ein
echtes Voxel-Gitter aus (x, y, z)-Koordinaten:
    X und Z = horizontale Grundfläche (wie in Minecraft)
    Y       = Höhe (wächst nach oben)

Die Welt ist in Chunks eingeteilt (CHUNK_SIZE × CHUNK_SIZE Blöcke Grundfläche).
Jeder Chunk speichert seine Blöcke in einem Dictionary: {(x, y, z): Block-Name}.
Für die Performance gilt: Es werden nur Blöcke als Ursina-Entities erzeugt,
die mindestens eine sichtbare Fläche haben (komplett von Nachbarn umschlossene
Blöcke bleiben unsichtbar). Das hält die Entity-Anzahl klein, auch wenn die
Welt intern viel größer ist.

PHASE 2: Die Blöcke kommen aus utils/world_gen.py (World mit Heightmap,
Bäume, Erze). VoxelWorld rendert die sichtbaren Blöcke als Entities,
streamt Chunks um den Spieler herum (ensure_chunks_around) und hält
Darstellung und Daten bei Block-Interaktionen synchron.

Block-Eigenschaften (solid, hardness, tool, drop, color) kommen weiterhin
aus BLOCK_PROPERTIES in utils/constants.py — keine hartkodierten Werte.
"""

import math
import os
from ursina import Entity, Mesh, Texture, color
from utils.constants import (
    CHUNK_SIZE,
    RENDER_DISTANCE_CHUNKS,
    TEST_CHUNK_STONE_LAYERS,
    TEST_CHUNK_SURFACE_Y,
    BLOCK_PROPERTIES,
)
from utils.world_gen import World


class BlockTextureLibrary:
    """
    Lädt und cached die Block-Texturen für die 3D-Welt.

    Es werden die vorhandenen PNG-Dateien aus assets/blocks/ verwendet
    (z.B. grass.png, dirt.png, stone.png). Hat ein Block keine PNG,
    wird als Fallback die Farbe aus BLOCK_PROPERTIES["color"] benutzt.
    """

    def __init__(self):
        self.texture_cache = {}       # Block-Name → Ursina-Texture (oder None)
        self.color_cache = {}         # Block-Name → Ursina-Farbe (Fallback)
        self.assets_path = os.path.join("assets", "blocks")

    def get_texture(self, block_name):
        """
        Gibt die Ursina-Textur für einen Block zurück (oder None, wenn
        keine PNG-Datei existiert — dann wird die Fallback-Farbe genutzt).
        """
        if block_name in self.texture_cache:
            return self.texture_cache[block_name]

        texture = None
        image_path = os.path.join(self.assets_path, f"{block_name}.png")
        if os.path.exists(image_path):
            try:
                texture = Texture(image_path)
            except Exception as e:
                print(f"Fehler beim Laden von {image_path}: {e}")
                texture = None

        self.texture_cache[block_name] = texture
        return texture

    def get_color(self, block_name):
        """
        Gibt die Fallback-Farbe eines Blocks als Ursina-Farbe zurück.
        Wird verwendet, wenn keine Textur-PNG vorhanden ist.
        """
        if block_name in self.color_cache:
            return self.color_cache[block_name]

        rgb = BLOCK_PROPERTIES.get(block_name, {}).get("color")
        ursina_color = None
        if rgb is not None:
            # RGB-Tupel (0-255) → Ursina-Farbe (0-1); Alpha optional
            r, g, b = rgb[0] / 255, rgb[1] / 255, rgb[2] / 255
            alpha = rgb[3] / 255 if len(rgb) > 3 else 1.0
            ursina_color = color.rgba(r, g, b, alpha)

        self.color_cache[block_name] = ursina_color
        return ursina_color

    def build_atlas(self, cell=32, cols=8):
        """Erzeugt einmalig eine Textur-Atlas-Kachelkarte aus allen Block-PNGs.

        Füllt fehlende PNGs mit der BLOCK_PROPERTIES-Farbe und multipliziert
        Textur × Farbe (exakt wie früher die Entity-Einfärbung).
        Danach sind self.atlas_uv (Block → UV-Rechteck) und
        self.atlas_texture (eine einzige Ursina-Textur) verfügbar.
        """
        if getattr(self, "atlas_uv", None):
            return

        from math import ceil
        from PIL import Image, ImageChops

        blocks = sorted(
            b for b in BLOCK_PROPERTIES
            if b != "air" and BLOCK_PROPERTIES[b].get("solid", True)
        )
        rows = ceil(len(blocks) / cols)
        atlas = Image.new("RGBA", (cols * cell, rows * cell), (0, 0, 0, 0))
        self.atlas_uv = {}

        for i, block in enumerate(blocks):
            cx = (i % cols) * cell
            cy = (i // cols) * cell

            image_path = os.path.join(self.assets_path, f"{block}.png")
            if os.path.exists(image_path):
                img = Image.open(image_path).convert("RGBA").resize(
                    (cell, cell), Image.NEAREST)
            else:
                rgb = BLOCK_PROPERTIES[block].get("color") or (255, 0, 255)
                img = Image.new("RGBA", (cell, cell),
                                (rgb[0], rgb[1], rgb[2], 255))

            # Textur × Farbe wie bisher bei den Entity-Entities
            rgb = BLOCK_PROPERTIES[block].get("color")
            if rgb is not None:
                tint = Image.new("RGBA", img.size,
                                 (rgb[0], rgb[1], rgb[2], 255))
                img = ImageChops.multiply(img, tint)

            atlas.paste(img, (cx, cy))

            atlas_w = cols * cell
            atlas_h = rows * cell
            eps_u = 0.5 / atlas_w
            eps_v = 0.5 / atlas_h
            u0 = cx / atlas_w + eps_u
            u1 = (cx + cell) / atlas_w - eps_u
            # WICHTIG: Ursina/Panda3D lädt PIL-Bilder mit vertikalem Flip
            # (texture.py: FLIP_TOP_BOTTOM, speichert Bildzeile 0 an v=0) →
            # PIL-Y-Achse (0 = oben) entspricht der gespiegelten V-Achse.
            v0 = 1.0 - (cy + cell) / atlas_h + eps_v
            v1 = 1.0 - cy / atlas_h - eps_v
            self.atlas_uv[block] = (u0, v0, u1, v1)

        self.atlas_texture = Texture(atlas)
        try:  # Pixel-Look: keine weichen Kanten zwischen Atlas-Zellen
            from panda3d.core import Texture as PTexture
            self.atlas_texture.set_minfilter(PTexture.FT_nearest)
            self.atlas_texture.set_magfilter(PTexture.FT_nearest)
        except Exception:
            pass



class Chunk:
    """
    Ein Chunk ist ein CHUNK_SIZE×CHUNK_SIZE-Stück der Welt (Grundfläche X/Z).

    Die Blockdaten liegen in einem Dictionary: {(x, y, z): Block-Name}.
    Zur Darstellung erzeugt der Chunk Ursina-Entities — aber nur für
    Blöcke mit mindestens einer sichtbaren Fläche (Culling von
    komplett umschlossenen Blöcken).

    Wichtige Attribute:
        chunk_x, chunk_z: Chunk-Koordinaten (Chunk-(cx, cz) in Chunk-Einheiten)
        blocks:           Dictionary aller Blöcke dieses Chunks
        entities:         Liste der aktuell gerenderten Ursina-Entities
        world_group:      Parent-Entity, in dem alle Block-Entities liegen
    """

    def __init__(self, chunk_x, chunk_z, texture_library, world_group,
                 world_data=None):
        self.chunk_x = chunk_x
        self.chunk_z = chunk_z
        self.texture_library = texture_library
        self.world_group = world_group
        self.world_data = world_data   # globale World-Daten (fuer Nachbar-Checks)
        self.blocks = {}
        self.entities = []
        self.entity = None             # der eine verschmolzene Chunk-Entity

    # =========================================================
    # BLOCK-ZUGRIFF
    # =========================================================
    def get_block(self, x, y, z):
        """Gibt den Block-Namen an Position (x, y, z) zurück (oder None = Luft)."""
        return self.blocks.get((x, y, z))

    def set_block(self, x, y, z, block):
        """Setzt einen Block an Position (x, y, z) (None oder 'air' = Luft)."""
        if block is None or block == "air":
            self.blocks.pop((x, y, z), None)
        else:
            self.blocks[(x, y, z)] = block

    # =========================================================
    # RENDERING
    # =========================================================
    def _neighbor_solid(self, x, y, z):
        """True, wenn der Nachbar-Block die Fläche verdeckt (weltweit, chunkübergreifend)."""
        if self.world_data is not None:
            neighbor = self.world_data.get_block(x, y, z)
        else:
            neighbor = self.get_block(x, y, z)
        if neighbor is None:
            return False  # Luft oder außerhalb → Fläche sichtbar
        return bool(BLOCK_PROPERTIES.get(neighbor, {}).get("solid", True))

    def render(self):
        """Baut EINEN verschmolzenen Mesh pro Chunk (nur sichtbare Flächen).

        Ersetzt die alte Variante mit einem Entity pro Block: 14 Chunks statt
        ~57.000 Entities → Startzeit von ~100s auf ~2s und 60 FPS statt 2 FPS.

        Nachbar-Checks laufen gegen eine lokale Solid-Menge des Chunks
        (statt pro Fläche über world_data) — das spart bei der 1000×1000-Welt
        mit 49 geladenen Chunks rund die Hälfte der Startzeit.
        """
        self.clear()
        if not self.blocks:
            return

        # 6 Seiten: (Nachbar-Offset, 4 Ecken relativ zur Blockmitte ±0.5)
        # Winding: rechtshändig, Normale zeigt per Cross-Produkt nach AUSSEN.
        faces = (
            ((0, 1, 0), ((-.5, .5, .5), (.5, .5, .5), (.5, .5, -.5), (-.5, .5, -.5))),
            ((0, -1, 0), ((-.5, -.5, -.5), (.5, -.5, -.5), (.5, -.5, .5), (-.5, -.5, .5))),
            ((1, 0, 0), ((.5, -.5, -.5), (.5, .5, -.5), (.5, .5, .5), (.5, -.5, .5))),
            ((-1, 0, 0), ((-.5, -.5, .5), (-.5, .5, .5), (-.5, .5, -.5), (-.5, -.5, -.5))),
            ((0, 0, 1), ((.5, -.5, .5), (.5, .5, .5), (-.5, .5, .5), (-.5, -.5, .5))),
            ((0, 0, -1), ((-.5, -.5, -.5), (-.5, .5, -.5), (.5, .5, -.5), (.5, -.5, -.5))),
        )
        self.texture_library.build_atlas()
        atlas_uv = self.texture_library.atlas_uv
        props = BLOCK_PROPERTIES

        # Nachbar-Checks laufen über eine lokale Solid-Menge: über world_data
        # gingen sie pro Block 6 mal durch die Methodenkette (bei ~14.000
        # Blöcken/Chunk sind das ~83.000 Aufrufe, davon >97 % verdeckt).
        # world_data wird nur noch für Nachbarn ausserhalb des Chunks befragt.
        own = self.blocks
        solid_here = {
            pos for pos, name in own.items()
            if props.get(name, {}).get("solid", True)
        }
        x0, z0 = self.chunk_x * CHUNK_SIZE, self.chunk_z * CHUNK_SIZE
        x1, z1 = x0 + CHUNK_SIZE, z0 + CHUNK_SIZE

        # Quad-UVs: k0→k1 = horizontal (U), k0→k3 = vertikal (V, oben = v1).
        # Die vier Ecken sind pro Block identisch → einmal vorberechnen.
        vertices, uvs, triangles = [], [], []
        for (x, y, z), block in own.items():
            if (x, y, z) not in solid_here:
                continue
            uv = atlas_uv.get(block)
            if uv is None:
                continue
            u0, v0, u1, v1 = uv
            corner_uvs = ((u0, v0), (u0, v1), (u1, v1), (u1, v0))
            for (dx, dy, dz), corners in faces:
                nx, ny, nz = x + dx, y + dy, z + dz
                if x0 <= nx < x1 and z0 <= nz < z1:
                    if (nx, ny, nz) in solid_here:
                        continue  # vollständig verdeckt → nicht zeichnen
                elif self._neighbor_solid(nx, ny, nz):
                    continue  # Nachbar in anderem Chunk → weltweiter Check
                base = len(vertices)
                # Tupel statt Vec3/Vec2: Ursina ravelt Punkte/UVs intern in
                # float-Arrays (Mesh._ravel) und reicht die Objekte nur an den
                # MeshCollider weiter → spart ~780.000 Objekte pro Start.
                for fx, fy, fz in corners:
                    vertices.append((x + fx, y + fy, z + fz))
                uvs.extend(corner_uvs)
                triangles.append((base, base + 1, base + 2))
                triangles.append((base, base + 2, base + 3))

        if not vertices:
            return

        mesh = Mesh(vertices=vertices, triangles=triangles, uvs=uvs,
                    mode="triangle")
        self.entity = Entity(
            parent=self.world_group,
            model=mesh,
            texture=self.texture_library.atlas_texture,
            collider="mesh",
        )
        self.entity.is_voxel_chunk = True
        self.entity.chunk_x = self.chunk_x
        self.entity.chunk_z = self.chunk_z
        self.entities = [self.entity]

    def clear(self):
        """Entfernt den Chunk-Entity (Mesh) aus der Szene."""
        if self.entity is not None:
            self.entity.removeNode()
            self.entity = None
        self.entities = []

class VoxelWorld:
    """
    Verwaltet alle Chunks der aktuellen Welt (Dimension).

    Die Welt besteht aus Chunks à CHUNK_SIZE × CHUNK_SIZE Blöcken.
    Chunks werden per Koordinate (cx, cz) angesprochen und können
    einzeln geladen/entladen werden (wichtig für den Dimensionswechsel
    und die spätere dynamische Sichtweite).

    PHASE 1: Erzeugt einen flachen Testchunk (Gras/Erde/Stein).
    """

    def __init__(self, texture_library=None, dimension="grassland", seed=None):
        # Parent-Entity für alle Chunks (kann als Ganzes versteckt/entladen werden)
        self.world_group = Entity(name="VoxelWorld")
        self.texture_library = texture_library or BlockTextureLibrary()
        self.chunks = {}  # (cx, cz) → Chunk
        # Nur die sichtbare Startregion wird erzeugt; die komplette Welt wird nicht
        # beim Start mit Millionen Blöcken geladen, da das zu einem schwarzen oder
        # unbearbeitbaren Startbild führen kann.
        self.data = World(dimension=dimension, seed=seed, skip_generation=True)
        self._wanted_chunks = None
        # Weltweit sichtbare Flächen markieren, aber NICHT rückseitig beschneiden
        try:
            import builtins
            rnd = getattr(builtins, "render", None)
            if rnd is None:
                from ursina import render as rnd
            rnd.setTwoSided(True)
        except Exception:
            pass

    # =========================================================
    # CHUNK-VERWALTUNG
    # =========================================================
    def get_chunk_coords(self, x, z):
        """Rechnet Welt-Koordinaten (x, z) in Chunk-Koordinaten um."""
        return (x // CHUNK_SIZE, z // CHUNK_SIZE)

    def get_chunk(self, cx, cz):
        """Gibt den Chunk an (cx, cz) zurück (oder None, wenn nicht geladen)."""
        return self.chunks.get((cx, cz))

    def add_chunk(self, chunk):
        """Registriert einen Chunk in der Welt und rendert ihn."""
        self.chunks[(chunk.chunk_x, chunk.chunk_z)] = chunk
        chunk.render()

    def unload_all_chunks(self):
        """Entfernt alle Chunks (wird später beim Dimensionswechsel gebraucht)."""
        for chunk in self.chunks.values():
            chunk.clear()
        self.chunks = {}

    def generate_dimension(self, center_x=None, center_z=None, radius=RENDER_DISTANCE_CHUNKS):
        """Generiert und rendert nur die sichtbare Startregion der Dimension."""
        center_x = self.data.width // 2 if center_x is None else center_x
        center_z = self.data.depth // 2 if center_z is None else center_z
        wanted = set(self.data.chunk_range_for_player(center_x, center_z, radius))
        self._wanted_chunks = wanted

        # Die Welt wird lokal erzeugt, damit beim Spielstart ein sichtbares Terrain
        # entsteht, statt die komplette Welt erst im Hintergrund aufzubauen.
        self.data.generate_chunks(wanted)

        for chunk_coords in wanted:
            if chunk_coords in self.chunks:
                continue
            chunk = Chunk(*chunk_coords, self.texture_library, self.world_group,
                          world_data=self.data)
            for x, y, z, block in self.data.get_chunk_blocks(*chunk_coords):
                chunk.set_block(x, y, z, block)
            self.add_chunk(chunk)

        # Spawn-Point bestimmen und Spawn-Area freiraeumen (kein Baum im Weg).
        return self.data.ensure_spawn_point()

    # =========================================================
    # BLOCK-ZUGRIFF (weltweit, über Chunk-Grenzen hinweg)
    # =========================================================
    def get_block(self, x, y, z):
        """Gibt den Block an Welt-Position (x, y, z) zurück (oder None = Luft)."""
        return self.data.get_block(x, y, z)

    def set_block(self, x, y, z, block):
        """Setzt einen Block und synchronisiert die Darstellung (inkl. Nachbarn)."""
        self.data.set_block(x, y, z, block)
        self._refresh_blocks_around(x, y, z)

    def break_block(self, x, y, z):
        """Zerbricht den Block an (x, y, z) und gibt den Drop-Namen zurück."""
        if self.data.get_block(x, y, z) is None:
            return None
        drop = self.data.break_block(x, y, z)
        self._refresh_blocks_around(x, y, z)
        return drop

    def place_block(self, x, y, z, block):
        """Setzt einen Block (True bei Erfolg)."""
        if not self.data.set_block(x, y, z, block):
            return False
        self._refresh_blocks_around(x, y, z)
        return True

    def is_solid(self, x, y, z):
        """Prüft, ob an Welt-Position (x, y, z) ein fester Block ist."""
        return self.data.is_solid(x, y, z)

    def _refresh_blocks_around(self, x, y, z):
        """Synchronisiert alle betroffenen Chunks mit den World-Daten und rendert sie neu.

        Nach einer Aenderung (abbauen/platzieren) muessen nicht nur der
        eigene Chunk, sondern auch Nachbar-Chunks neu geprueft werden:
        dort koennen durch die Aenderung neue sichtbare Flaechen entstehen.
        """
        touched = set()
        for dx, dy, dz in (
            (0, 0, 0), (1, 0, 0), (-1, 0, 0),
            (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1),
        ):
            nx, ny, nz = x + dx, y + dy, z + dz
            cx, cz = self.get_chunk_coords(nx, nz)
            chunk = self.get_chunk(cx, cz)
            if chunk is None:
                continue
            chunk.set_block(nx, ny, nz, self.data.get_block(nx, ny, nz))
            touched.add((cx, cz))

        # Betroffene Chunks neu rendern (set_block aendert nur das Dict)
        for key in touched:
            self.chunks[key].render()

    def ensure_chunks_around(self, px, pz, radius=RENDER_DISTANCE_CHUNKS):
        """Lädt Chunks im Umkreis um (px, pz) und entfernt entfernte Chunks."""
        wanted = set(self.data.chunk_range_for_player(px, pz, radius))
        if wanted == self._wanted_chunks:
            return
        self._wanted_chunks = wanted

        # Fehlende Chunks erzeugen (Daten + sichtbare Blöcke als Entities)
        self.data.generate_chunks(wanted)
        for cx, cz in wanted:
            if (cx, cz) in self.chunks:
                continue
            chunk = Chunk(cx, cz, self.texture_library, self.world_group,
                          world_data=self.data)
            for x, y, z, block in self.data.get_chunk_blocks(cx, cz):
                chunk.set_block(x, y, z, block)
            self.add_chunk(chunk)

        # Chunks außerhalb des Radius + 1 Puffer entfernen: Render-Entity UND
        # Blockdaten (drop_chunk). Spieler-aenderte Chunks bleiben in den
        # Daten erhalten und werden beim Besuch nicht neu generiert.
        keep = set(self.data.chunk_range_for_player(px, pz, radius + 1))
        for chunk_key in list(self.chunks.keys()):
            if chunk_key not in keep:
                self.chunks[chunk_key].clear()
                del self.chunks[chunk_key]
                self.data.drop_chunk(*chunk_key)

    # =========================================================
    # PHASE 1: FLACHER TESTCHUNK
    # =========================================================
    def generate_flat_test_chunk(self, cx=0, cz=0):
        """
        Erzeugt einen flachen Testchunk (16×16): unten Stein, darüber
        Erde, oben Gras. Die Höhen kommen aus den Test-Konstanten.
        """
        chunk = Chunk(cx, cz, self.texture_library, self.world_group)
        base_x, base_z = cx * CHUNK_SIZE, cz * CHUNK_SIZE

        for lx in range(CHUNK_SIZE):
            for lz in range(CHUNK_SIZE):
                x, z = base_x + lx, base_z + lz
                # Stein-Schichten unten (unter der Erde)
                for y in range(TEST_CHUNK_SURFACE_Y - TEST_CHUNK_STONE_LAYERS - 1, TEST_CHUNK_SURFACE_Y - 1):
                    chunk.set_block(x, y, z, "stone")
                # Erde und Gras oben
                chunk.set_block(x, TEST_CHUNK_SURFACE_Y - 1, z, "dirt")
                chunk.set_block(x, TEST_CHUNK_SURFACE_Y, z, "grass")

        self.add_chunk(chunk)
        return chunk

