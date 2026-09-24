"""3D-Voxelwelt-Generierung fuer PixelPortalRift.
================================================

Die Klasse ``World`` repraesentiert eine einzelne Dimension als echtes
3D-Voxel-Gitter:

* X und Z sind die horizontale Grundflaeche (wie Minecraft).
* Y ist die Hoehe (Y waechst nach oben).

Bloecke liegen in einem Dict ``{(x, y, z): block_name}``. Fehlende
Eintraege bedeuten Luft. Die Generierung ist chunkweise organisiert
(``CHUNK_SIZE`` x ``CHUNK_SIZE`` Bloecke Grundflaeche).

Block-Eigenschaften (solid, drop, respawnable, ...) kommen ausschliesslich
aus ``BLOCK_PROPERTIES`` in ``utils/constants.py``.
"""

import math
import random

import numpy as np

from utils.constants import (
    BLOCK_PROPERTIES,
    CHUNK_HEIGHT,
    CHUNK_SIZE,
    DIMENSIONS,
    TILE_SIZE,
    VOID_Y,
    WORLD_DEPTH,
    WORLD_HEIGHT,
    WORLD_WIDTH,
)


class World:
    """Eine Dimension als 3D-Voxelwelt (X/Z Grundflaeche, Y Hoehe)."""

    def __init__(self, dimension="grassland", seed=None, skip_generation=True,
                 width=None, depth=None):
        """Erzeugt eine neue 3D-Welt. Standardmaessig wird NICHT sofort generiert
        (lazy): VoxelWorld baut nur die sichtbaren Chunks ueber generate_chunks().
        ``width``/``depth`` ueberschreiben die Weltgroesse (fuer Tests)."""
        if dimension not in DIMENSIONS:
            raise ValueError(f"Unbekannte Dimension: {dimension}")

        self.dimension = dimension
        self.seed = seed if seed is not None else random.randrange(1_000_000)
        self.width = WORLD_WIDTH if width is None else int(width)
        self.depth = WORLD_DEPTH if depth is None else int(depth)
        self.height = min(CHUNK_HEIGHT, WORLD_HEIGHT)
        self.dimension_data = DIMENSIONS[dimension]

        # Zwei-Ebenen-Dict: {chunk_key: {(x, y, z): block_name}}.
        # Ermöglicht O(Chunk)-Zugriff (get_chunk_blocks) und O(1)-Entladen.
        self.blocks = {}
        self.generated_chunks = set()
        # Chunks mit Spieler-/Spawn-/Respawn-Aenderungen: duerfen beim
        # Entladen NICHT geloescht werden (Aenderungen muessten sonst
        # verloren gehen).
        self.modified_chunks = set()
        # True waehrend _generate_chunk: interne Writes markieren nicht.
        self._generating = False
        self.portals = []
        self.respawn_queue = []
        self.spawn_point = None
        self._heightmap = None

        random.seed(self.seed)
        if not skip_generation:
            self.generate()

    # ------------------------------------------------------------------
    # Chunk-Koordinaten
    # ------------------------------------------------------------------
    @staticmethod
    def chunk_coords(x, z):
        """Welt-Koordinaten (x, z) -> Chunk-Koordinaten (cx, cz)."""
        return int(x) // CHUNK_SIZE, int(z) // CHUNK_SIZE

    def chunk_range_for_player(self, px, pz, radius=2):
        """Alle Chunk-Koordinaten im Umkreis ``radius`` um den Spieler."""
        pcx, pcz = self.chunk_coords(px, pz)
        max_cx = int(math.ceil(self.width / CHUNK_SIZE))
        max_cz = int(math.ceil(self.depth / CHUNK_SIZE))

        chunks = []
        for cx in range(pcx - radius, pcx + radius + 1):
            for cz in range(pcz - radius, pcz + radius + 1):
                if 0 <= cx < max_cx and 0 <= cz < max_cz:
                    chunks.append((cx, cz))
        return chunks

    # ------------------------------------------------------------------
    # Blockzugriff (weltweit 3D, bounds-geprüft)
    # ------------------------------------------------------------------
    def get_block(self, x, y, z):
        """Block-Name an ``(x, y, z)`` oder ``None`` (Luft bzw. ausserhalb)."""
        x, y, z = int(x), int(y), int(z)
        if not (0 <= x < self.width and 0 <= z < self.depth):
            return None
        if y < VOID_Y or y >= self.height:
            return None
        sub = self.blocks.get((x // CHUNK_SIZE, z // CHUNK_SIZE))
        if sub is None:
            return None
        return sub.get((x, y, z))

    def set_block(self, x, y, z, block_name):
        """Setzt einen Block; ``None`` oder ``'air'`` entfernt den Block."""
        x, y, z = int(x), int(y), int(z)
        if not (0 <= x < self.width and 0 <= z < self.depth):
            return False
        if y < VOID_Y or y >= self.height:
            return False

        chunk_key = (x // CHUNK_SIZE, z // CHUNK_SIZE)
        key = (x, y, z)
        if block_name in (None, "air"):
            sub = self.blocks.get(chunk_key)
            if sub is not None:
                sub.pop(key, None)
        else:
            self.blocks.setdefault(chunk_key, {})[key] = block_name

        # Ausserhalb der Generierung = Spieler-/Spawn-/Respawn-Zugriff:
        # Chunk vor dem Entladen schuetzen.
        if not self._generating:
            self.modified_chunks.add(chunk_key)
        return True

    def is_solid(self, x, y=None, z=None):
        """True, falls an ``(x, y, z)`` ein fester Block liegt."""
        if y is None or z is None:
            if not isinstance(x, str):
                return False
            block = x
        else:
            block = self.get_block(x, y, z)

        if not block:
            return False
        return bool(BLOCK_PROPERTIES.get(block, {}).get("solid", True))

    def get_height_at(self, x, z):
        """Hoechste feste Block-Y-Position bei ``(x, z)`` oder ``-1``."""
        for y in range(self.height - 1, VOID_Y - 1, -1):
            if self.is_solid(x, y, z):
                return y
        return -1

    # ------------------------------------------------------------------
    # Hoehenkarte und vollstaendige Generierung
    # ------------------------------------------------------------------
    def _build_heightmap(self):
        """Berechnet die 2D-Hoehenkarte der ganzen Welt (numpy-Array)."""
        width, depth, height = self.width, self.depth, self.height
        base = float(self.dimension_data.get("ground_level", height // 2))

        xs = np.arange(width, dtype=np.float64)
        zs = np.arange(depth, dtype=np.float64)
        xx, zz = np.meshgrid(xs, zs, indexing="ij")

        wave = (
            np.sin(xx * 0.05 + self.seed * 0.01) * 5.0
            + np.cos(zz * 0.04 + self.seed * 0.01) * 5.0
        )
        broad = np.sin((xx + zz) * 0.018 + self.seed * 0.007) * 6.0

        rng = np.random.RandomState(self.seed)
        noise = rng.normal(0.0, 1.5, size=(width, depth))
        noise += rng.normal(0.0, 0.6, size=(width, depth)) * 0.5

        heights = np.clip(base + wave + broad + noise, 3, height - 4)
        return heights.astype(np.int32)

    def generate(self):
        """Erzeugt die gesamte Welt chunkweise anhand der Hoehenkarte."""
        heights = self._build_heightmap()
        self._heightmap = heights

        self.blocks.clear()
        self.generated_chunks.clear()
        self.modified_chunks.clear()
        self.respawn_queue.clear()
        self.portals.clear()

        cx_max = int(math.ceil(self.width / CHUNK_SIZE))
        cz_max = int(math.ceil(self.depth / CHUNK_SIZE))
        for cx in range(cx_max):
            for cz in range(cz_max):
                self._generate_chunk(cx, cz, heights)

        self.ensure_spawn_point()

    def ensure_spawn_point(self):
        """Legt den Spawn-Point fest und raeumt die Spawn-Area frei.

        Verhindert, dass der Spieler beim Spawnen in einem Baumstamm oder
        Blaettern stecken bleibt. Idempotent – mehrfacher Aufruf ist erlaubt.
        Gibt den Spawn-Punkt (x, y, z) zurueck.
        """
        if self._heightmap is None:
            self._heightmap = self._build_heightmap()

        if self.spawn_point is None:
            spawn_x = self.width // 2
            spawn_z = self.depth // 2
            surface_y = self.terrain_height(spawn_x, spawn_z)
            self.spawn_point = (spawn_x + 0.5, surface_y + 2, spawn_z + 0.5)

        sx = int(self.spawn_point[0])
        sz = int(self.spawn_point[2])

        # 5x5-Saeule bis 12 Bl ueber dem jeweiligen Grund freiraeumen:
        # Baumkronen reichen bis ~ground+10 und ragen 2 Bl ueber den Stamm
        # hinaus – ein kleinerer Radius liess die Kamera in Blaettern stecken.
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                col_x, col_z = sx + dx, sz + dz
                ground_y = self.terrain_height(col_x, col_z)
                for dy in range(1, 13):
                    if self.get_block(col_x, ground_y + dy, col_z) is not None:
                        self.set_block(col_x, ground_y + dy, col_z, None)
        return self.spawn_point

    def _generate_chunk(self, cx, cz, heightmap=None):
        """Erzeugt einen Chunk unter dem Generierungs-Flag ``_generating``.

        Das Flag verhindert, dass interne Schreibzugriffe (Erze, Baeume)
        den Chunk als Spieler-aendert markieren – sonst waere nach dem
        Entladen jede Regeneration "modified" und nichts wuerde freigegeben.
        """
        if (cx, cz) in self.generated_chunks:
            return  # bereits generiert – keine Aenderungen ueberschreiben
        self._generating = True
        try:
            self._generate_chunk_impl(cx, cz, heightmap)
        finally:
            self._generating = False

    def _generate_chunk_impl(self, cx, cz, heightmap=None):
        """Fuellt den Chunk (cx, cz) mit Bloecken anhand der Hoehenkarte."""
        if heightmap is None:
            if self._heightmap is None:
                self._heightmap = self._build_heightmap()
            heightmap = self._heightmap

        x_start = cx * CHUNK_SIZE
        z_start = cz * CHUNK_SIZE
        x_end = min(x_start + CHUNK_SIZE, self.width)
        z_end = min(z_start + CHUNK_SIZE, self.depth)
        chunk_datum = self.dimension_data
        # Deterministische Zufallswerte NUR fuer diesen Chunk: Erze und
        # Baeume haengen nicht von der Chunk-Erreichfolge ab – Voraussetzung
        # dafuer, dass entladene Chunks identisch neu erzeugt werden koennen.
        rng = random.Random(f"{self.seed}:{cx}:{cz}")

        for x in range(x_start, x_end):
            for z in range(z_start, z_end):
                surface_y = int(heightmap[x, z])
                surface_y = max(3, min(self.height - 4, surface_y))

                # Stein von der Untergrund-Grenze bis surface_y - 3.
                stone_end = max(0, surface_y - 2)  # y = 0 .. surface_y - 3
                for y in range(stone_end):
                    self.set_block(x, y, z, "stone")

                # Subsurface-Schichten direkt unter der Oberflaeche.
                for y in range(max(0, surface_y - 2), surface_y):
                    self.set_block(
                        x, y, z,
                        self._surface_block_below(chunk_datum, x, z),
                    )

                # Oberflaechenblock.
                self.set_block(
                    x, surface_y, z,
                    self._surface_block(chunk_datum, x, z, surface_y),
                )

                # Erze im Untergrund.
                self._place_ores(x, z, surface_y, chunk_datum, rng)

        # Baeume, sofern Holz und Blaetter generell existieren.
        if "wood" in BLOCK_PROPERTIES and "leaves" in BLOCK_PROPERTIES:
            self._place_trees_in_chunk(
                cx, cz, heightmap, x_start, x_end, z_start, z_end, rng,
            )

        self.generated_chunks.add((cx, cz))

    def generate_chunk(self, cx, cz):
        """Erzeugt genau einen Chunk (auch nach dem anfaenglichen Laden)."""
        self._generate_chunk(cx, cz, self._heightmap)

    def generate_chunks(self, chunks):
        """Erzeugt eine Liste von Chunks ``[(cx, cz), ...]``."""
        for cx, cz in chunks:
            self.generate_chunk(cx, cz)

    def get_chunk_blocks(self, cx, cz):
        """Alle Bloecke eines Chunks als Liste von ``(x, y, z, block_name)``.

        Liest nur den einen Chunk-Eintrag – O(Chunk) unabhaengig von der
        Weltgroesse (ein Scan ueber alle Bloecke wuerde beim Laden jedes
        Chunks bei 1000x1000 die ganze Welt abarbeiten).
        """
        sub = self.blocks.get((cx, cz))
        if not sub:
            return []
        return [(x, y, z, name) for (x, y, z), name in sub.items()]

    def block_count(self):
        """Anzahl aller gespeicherten Bloecke (fuer Diagnose/Tests)."""
        return sum(len(sub) for sub in self.blocks.values())

    def drop_chunk(self, cx, cz):
        """Entlaedt die Daten eines unveraenderten Chunks (RAM-Sparen).

        Spieler-/Spawn-/Respawn-aenderte Chunks (``modified_chunks``)
        bleiben erhalten. Beim naechsten Besuch wird der Chunk ueber die
        pro-Chunk-RNG identisch neu erzeugt. Gibt True zurueck, wenn
        der Chunk entladen wurde.
        """
        key = (cx, cz)
        if key in self.modified_chunks:
            return False
        self.blocks.pop(key, None)
        self.generated_chunks.discard(key)
        return True

    def _height_at(self, x, z):
        """Naeherungs-Hoehe einer Spalte ohne numpy-Hoehenkarte."""
        base = float(self.dimension_data.get("ground_level", self.height // 2))
        wave = (
            math.sin(x * 0.05 + self.seed * 0.01) * 5.0
            + math.cos(z * 0.04 + self.seed * 0.01) * 5.0
        )
        broad = math.sin((x + z) * 0.018 + self.seed * 0.007) * 6.0

        # Deterministisches Rauschen im Bereich [0, 1).
        noise = math.sin(x * 12.9898 + z * 78.233 + self.seed) * 43758.5453
        noise -= math.floor(noise)

        value = base + wave + broad + (noise - 0.5) * 3.0
        return int(max(3, min(self.height - 4, value)))

    def terrain_height(self, x, z):
        """Oberflaechen-Y an (x, z) – nutzt die Hoehenkarte, falls vorhanden.

        Wird von VoxelWorld.generate_dimension() als Fallback fuer den
        Spawn-Point aufgerufen, wenn noch kein voller generate()-Lauf stattfand.
        """
        if self._heightmap is not None:
            xi = max(0, min(self.width - 1, int(x)))
            zi = max(0, min(self.depth - 1, int(z)))
            return int(self._heightmap[xi, zi])
        return self._height_at(x, z)

    # ------------------------------------------------------------------
    # Oberflaeche, Untergrund und Erze
    # ------------------------------------------------------------------
    def _surface_block_below(self, chunk_datum, x, z):
        """Subsurface-Block direkt unter der Oberflaeche."""
        data = chunk_datum or self.dimension_data
        blocks = data.get("blocks", [])

        if "dirt" in blocks:
            return "dirt"
        if "sand" in blocks:
            return "sand"
        if "cobblestone" in blocks:
            return "cobblestone"
        if "gravel" in blocks:
            return "gravel"
        if blocks and blocks[0] in BLOCK_PROPERTIES:
            return blocks[0]
        return "stone"

    def _surface_block(self, chunk_datum, x, z, surface_y):
        """Oberflaechenblock der Dimension."""
        data = chunk_datum or self.dimension_data
        blocks = data.get("blocks", [])

        if self.dimension == "water_world" and "water" in blocks:
            return "water"
        if "grass" in blocks:
            return "grass"
        if "sand" in blocks:
            return "sand"
        if "crystal" in blocks:
            return "crystal"
        if self.dimension == "nuclear_world" or "contaminated_stone" in blocks:
            if "contaminated_stone" in BLOCK_PROPERTIES:
                return "contaminated_stone"
        if blocks and blocks[0] in BLOCK_PROPERTIES:
            return blocks[0]
        return "stone"

    def _place_ores(self, x, z, surface_y, chunk_datum, rng):
        """Verteilt flachennahe und tiefe Erze unter der Oberflaeche."""
        data = chunk_datum or self.dimension_data
        blocks = data.get("blocks", [])
        shallow = [b for b in blocks if "ore" in b and b in BLOCK_PROPERTIES]

        if shallow:
            for _ in range(rng.randint(1, 2)):
                depth = rng.randint(2, 8)
                y = surface_y - depth
                if y >= 1:
                    self.set_block(x, y, z, rng.choice(shallow))

        if rng.random() < 0.15:
            deep = [
                b for b in ("diamond_ore", "gold_ore", "iron_ore")
                if b in BLOCK_PROPERTIES
            ]
            if deep:
                depth = rng.randint(12, 25)
                y = surface_y - depth
                if y >= 1:
                    self.set_block(x, y, z, rng.choice(deep))

    # ------------------------------------------------------------------
    # Baeume
    # ------------------------------------------------------------------
    def _place_trees_in_chunk(
        self, cx, cz, heightmap, x_start, x_end, z_start, z_end, rng,
    ):
        """Setzt etwa 0.8 Prozent der geeigneten Spalten mit einem Baum.

        Baeume werden nur mit mindestens 2 Bl Randabstand zur Chunk-Grenze
        gepflanzt, damit die Blaetterwolke (Reichweite +-2) komplett im
        eigenen Chunk landet: Chunks bleiben dadurch vollstaendig
        eigenstaendig und koennen deterministisch entladen und neu erzeugt
        werden, ohne Nachbar-Chunks anzufassen.
        """
        for x in range(x_start, x_end):
            for z in range(z_start, z_end):
                if not (x_start + 2 <= x < x_end - 2 and
                        z_start + 2 <= z < z_end - 2):
                    continue  # Baum wuerde ueber den Chunk-Rand ragen
                if heightmap is None:
                    surface_y = self._height_at(x, z)
                else:
                    surface_y = int(heightmap[x, z])

                ground = self.get_block(x, surface_y - 1, z)
                surface = self.get_block(x, surface_y, z)
                on_soil = ground in ("dirt", "grass") or surface in ("dirt", "grass")
                if not on_soil:
                    continue
                if rng.random() >= 0.008:
                    continue
                self._grow_tree(x, surface_y + 1, z, rng)

    def _grow_tree(self, x, y, z, rng):
        """Erzeugt einen Baum mit Stamm und Blaetterwolke."""
        trunk_height = rng.randint(4, 6)
        for offset in range(trunk_height):
            self.set_block(x, y + offset, z, "wood")

        top_y = y + trunk_height - 1
        for dy in (0, 1, 2):
            for dx in range(-2, 3):
                for dz in range(-2, 3):
                    if abs(dx) + abs(dz) > 3:
                        continue
                    if dx == 0 and dz == 0 and dy == 0:
                        continue
                    bx, by, bz = x + dx, top_y + dy, z + dz
                    if self.get_block(bx, by, bz) in (None, "air"):
                        self.set_block(bx, by, bz, "leaves")

    # ------------------------------------------------------------------
    # Block-Interaktion (Abbauen / Respawn)
    # ------------------------------------------------------------------
    def break_block(self, x, y, z):
        """Zerbricht den Block an (x, y, z) und gibt den Drop-Item zurueck."""
        block = self.get_block(x, y, z)
        if not block:
            return None

        properties = BLOCK_PROPERTIES.get(block, {})
        drop = properties.get("drop")
        self.set_block(x, y, z, None)

        if properties.get("respawnable"):
            self.respawn_queue.append({
                "x": int(x),
                "y": int(y),
                "z": int(z),
                "block": block,
                "time_left": int(properties.get("respawn_time", 60000)),
            })
        return drop

    def update(self, dt):
        """Vermindert die Respawn-Zeiten; ``dt`` ist die Frame-Zeit in Sekunden."""
        milliseconds = dt * 1000.0
        for entry in self.respawn_queue[:]:
            entry["time_left"] -= milliseconds
            if entry["time_left"] > 0:
                continue

            x, y, z = entry["x"], entry["y"], entry["z"]
            if self.get_block(x, y, z) is None:
                self.set_block(x, y, z, entry["block"])
            self.respawn_queue.remove(entry)

    # ------------------------------------------------------------------
    # Speichern / Laden
    # ------------------------------------------------------------------
    def get_save_data(self):
        """Kompletten Weltzustand als JSON-kompatibles Dict."""
        return {
            "dimension": self.dimension,
            "seed": self.seed,
            "blocks": {
                f"{x},{y},{z}": name
                for sub in self.blocks.values()
                for (x, y, z), name in sub.items()
            },
            "generated_chunks": [
                list(chunk) for chunk in self.generated_chunks
            ],
            "modified_chunks": [
                list(chunk) for chunk in sorted(self.modified_chunks)
            ],
            "spawn_point": list(self.spawn_point) if self.spawn_point else None,
            "portals": self.portals,
            "respawn_queue": self.respawn_queue,
        }

    def load_save_data(self, data):
        """Stellt den Weltzustand aus ``get_save_data()`` wieder her."""
        self.dimension = data.get("dimension", self.dimension)
        if self.dimension not in DIMENSIONS:
            self.dimension = "grassland"
        self.seed = data.get("seed", self.seed)
        self.dimension_data = DIMENSIONS[self.dimension]

        self.blocks = {}
        for key, block_name in data.get("blocks", {}).items():
            parts = str(key).split(",")
            if len(parts) != 3:
                continue
            try:
                x, y, z = (int(part) for part in parts)
            except (TypeError, ValueError):
                continue
            chunk_key = (x // CHUNK_SIZE, z // CHUNK_SIZE)
            self.blocks.setdefault(chunk_key, {})[(x, y, z)] = block_name

        self.generated_chunks = {
            tuple(chunk)
            for chunk in data.get("generated_chunks", [])
            if len(chunk) == 2
        }
        raw_modified = data.get("modified_chunks")
        if raw_modified is None:
            # Altes Save-Format ohne diese Angabe: konservativ alles als
            # geaendert behandeln, damit keine Spieleraenderungen durch
            # Entladen verloren gehen.
            self.modified_chunks = set(self.blocks.keys())
        else:
            self.modified_chunks = {
                tuple(chunk) for chunk in raw_modified if len(chunk) == 2
            }
        spawn = data.get("spawn_point")
        self.spawn_point = tuple(spawn) if spawn else None
        self.portals = data.get("portals", [])
        self.respawn_queue = data.get("respawn_queue", [])
        self._heightmap = None
        random.seed(self.seed)
