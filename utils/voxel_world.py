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

PHASE 1 (Grundgerüst): Diese Datei erzeugt zunächst nur einen flachen
Testchunk (Gras/Erde/Stein), um Ursina, FirstPersonController und die
Kollisions-Logik zu testen. Ab Phase 2 wird hier die echte 3D-Terrain-
generierung (Heightmap, Bäume, Höhlen, Erze) angebaut.

Block-Eigenschaften (solid, hardness, tool, drop, color) kommen weiterhin
aus BLOCK_PROPERTIES in utils/constants.py — keine hartkodierten Werte.
"""

import math
import os
from ursina import Entity, Texture, color
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

    def __init__(self, chunk_x, chunk_z, texture_library, world_group):
        self.chunk_x = chunk_x
        self.chunk_z = chunk_z
        self.texture_library = texture_library
        self.world_group = world_group
        self.blocks = {}
        self.entities = []

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
    def _is_exposed(self, x, y, z):
        """
        Prüft, ob der Block an (x, y, z) mindestens eine sichtbare Fläche hat.
        Ein Block ist sichtbar, wenn einer seiner 6 Nachbarn fehlt (Luft)
        oder durchlässig ist (z.B. Wasser).
        Hinweis (Phase 2): Nachbarn außerhalb des Chunks liegen in anderen
        Chunks; die VoxelWorld stellt deren Blöcke dann global bereit.
        """
        for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            neighbor = self.get_block(x + dx, y + dy, z + dz)
            if neighbor is None:
                return True  # Nachbar fehlt → Fläche ist sichtbar
            if not BLOCK_PROPERTIES.get(neighbor, {}).get("solid", True):
                return True  # Durchlässiger Nachbar (z.B. Wasser) → auch sichtbar
        return False

    def render(self):
        """
        Erzeugt die Ursina-Entities für alle sichtbaren Blöcke dieses Chunks.

        Vorher werden alte Entities zerstört (wichtig für Rebuild nach
        Block-Änderungen, z.B. beim Abbauen in Phase 3).
        """
        self.clear()
        for (x, y, z), block in self.blocks.items():
            # Nur sichtbare Blöcke rendern — spart massiv Entities
            if not self._is_exposed(x, y, z):
                continue

            props = BLOCK_PROPERTIES.get(block, {})
            if not props.get("solid", True):
                continue  # Luft/durchlässige Blöcke werden nicht als Würfel gerendert

            texture = self.texture_library.get_texture(block)
            entity = Entity(
                parent=self.world_group,
                model="cube",
                texture=texture,
                color=self.texture_library.get_color(block),
                position=(x, y, z),
                collider="box",
                enabled=True,
            )
            # Merken, welcher Block hinter dem Entity steckt (fürs Abbauen/Platzieren)
            entity.block_name = block
            entity.block_coords = (x, y, z)
            self.entities.append(entity)

    def clear(self):
        """Entfernt alle Entities dieses Chunks aus der Szene."""
        for entity in self.entities:
            entity.removeNode()
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

        # Die Welt wird lokal erzeugt, damit beim Spielstart ein sichtbares Terrain
        # entsteht, statt die komplette Welt erst im Hintergrund aufzubauen.
        self.data.generate_chunks(wanted)

        for chunk_coords in wanted:
            if chunk_coords in self.chunks:
                continue
            chunk = Chunk(*chunk_coords, self.texture_library, self.world_group)
            for x, y, z, block in self.data.get_chunk_blocks(*chunk_coords):
                chunk.set_block(x, y, z, block)
            self.add_chunk(chunk)

        if self.data.spawn_point is None:
            surface_y = self.data.terrain_height(center_x, center_z)
            self.data.spawn_point = (center_x + 0.5, surface_y + 2, center_z + 0.5)
        return self.data.spawn_point

    # =========================================================
    # BLOCK-ZUGRIFF (weltweit, über Chunk-Grenzen hinweg)
    # =========================================================
    def get_block(self, x, y, z):
        """Gibt den Block an Welt-Position (x, y, z) zurück (oder None = Luft)."""
        return self.data.get_block(x, y, z)

    def set_block(self, x, y, z, block):
        """Setzt einen Block an Welt-Position (x, y, z)."""
        self.data.set_block(x, y, z, block)
        cx, cz = self.get_chunk_coords(x, z)
        chunk = self.get_chunk(cx, cz)
        if chunk is not None:
            chunk.set_block(x, y, z, block)

    def is_solid(self, x, y, z):
        """Prüft, ob an Welt-Position (x, y, z) ein fester Block ist."""
        return self.data.is_solid(x, y, z)

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

