"""
main.py – Hauptprogramm von PixelPortalRift (3D-Version)
=========================================================

Seit der Migration von Pygame (2D) auf Ursina (3D) steuert diese Datei
die gesamte 3D-Voxelwelt:

- Ursina-Fenster (statt pygame-Fenster)
- Sky + FirstPersonController (WASD + Maus, Springen mit Space)
- Die Voxel-Welt aus Chunks (siehe utils/voxel_world.py)

Die Welt wird chunkweise generiert und um den Spieler herum dynamisch
nachgeladen. Das Inventar öffnet mit E, das Crafting-Menü mit C.
Links klicken baut Blöcke ab; rechts klicken platziert einen Block aus
der Hotbar (Tasten 1-9, Mausrad).

Starte das Spiel mit: python main.py
"""

from ursina import (
    AmbientLight,
    DirectionalLight,
    Entity,
    Sky,
    Text,
    Ursina,
    camera,
    color,
    raycast,
    time,
    window,
)
from utils.player_controller import VoxelPlayer

from utils.constants import (
    BLOCK_PROPERTIES,
    DIMENSIONS,
    MAX_INTERACTION_RANGE,
    PLAYER_SPEED_3D,
    PLAYER_JUMP_HEIGHT_3D,
    PLAYER_GRAVITY_3D,
)
from utils.inventory import Inventory
from utils.crafting import CraftingSystem
from utils.game_ui import GameUI
from utils.voxel_world import VoxelWorld, BlockTextureLibrary


def rgb_to_ursina_color(rgb):
    """
    Wandelt ein RGB(A)-Tupel (Werte 0-255, aus constants.py) in eine
    Ursina-Farbe um (Werte 0-1).
    """
    if rgb is None:
        return None
    r, g, b = rgb[0] / 255, rgb[1] / 255, rgb[2] / 255
    alpha = rgb[3] / 255 if len(rgb) > 3 else 1.0
    return color.rgba(r, g, b, alpha)


class Game(Entity):
    """
    Die Hauptklasse des 3D-Spiels. Steuert alles.

    Erbt von Entity, damit Ursina update() und input() jeden Frame
    bzw. bei jedem Tastendruck automatisch aufruft.

    Wichtige Attribute:
        world:             Die aktuelle Voxel-Welt (VoxelWorld-Objekt)
        player:            Der FirstPersonController (Ursina-Prefab)
        current_dimension: Name der aktuellen Dimension (z.B. "grassland")
        hud_text:          Text-Overlay mit Position/FPS (F3-Debug vorbereitet)
    """

    def __init__(self):
        """Erzeugt das Ursina-Fenster, den Himmel, die Voxelwelt und den Spieler."""
        self.app = Ursina(title="PixelPortalRift 3D - Dimensional Adventure",
                          size=(1536, 960),   # ints verhindern win-size-Warnungen
                          borderless=False,   # normale Titelleiste mit Schliessen
                          editor_ui_enabled=False)  # Hinweis: wirkt bei ursina 7.0
        # nicht direkt (make_editor_gui() haengt die UI an development_mode),
        # daher explizit nach dem Init abschalten – versteckt rotes X,
        # FPS-/Entity-/Collider-Zaehler (F12 kann es zuruecktoggleaen).
        if getattr(window, "editor_ui", None) is not None:
            window.editor_ui.enabled = False
        super().__init__(name="game")  # registriert Game in scene (Update/Input-Loop)

        # ---- Himmel in der Farbe der aktuellen Dimension ----
        sky_color = rgb_to_ursina_color(DIMENSIONS["grassland"]["sky_color"])
        self.sky = Sky(color=sky_color)

        # ---- Beleuchtung (damit die Block-Flächen Plastizität bekommen) ----
        DirectionalLight(y=10, z=-10, shadows=False, rotation=(45, -45, 0))
        AmbientLight(color=color.rgba(0.6, 0.6, 0.6, 1))

        # ---- Welt: chunkweise 3D-Terrain-Generierung ----
        self.world = VoxelWorld(BlockTextureLibrary())
        spawn = self.world.generate_dimension()

        # ---- Spieler: eigener Controller mit Voxel-Kollision ----
        # (utils/player_controller.VoxelPlayer statt des Ursina-Prefabs:
        #  der Prefab fällt beim Bewegen durch die Welt, siehe Modul-Doku.)
        spawn_x, spawn_y, spawn_z = spawn
        self.player = VoxelPlayer(
            self.world,
            position=(spawn_x, spawn_y + 1.8, spawn_z),
            speed=PLAYER_SPEED_3D,
            jump_height=PLAYER_JUMP_HEIGHT_3D,
        )
        # Schwerkraft aus constants.py (statt Ursina-Standard)
        self.player.gravity = PLAYER_GRAVITY_3D

        # ---- HUD: Positions-Anzeige (Vorstufe des späteren F3-Debug) ----
        self.hud_text = Text(
            parent=camera.ui,
            position=(0, 0.47),
            origin=(0, 0.5),
            text="",
            scale=0.8,
        )

        self.current_dimension = "grassland"

        # ---- Phase 3: Inventar & Crafting (nicht: dict-Vorstufe) ----
        # 36 Slots (9 in der Hotbar) aus utils.inventory, CraftingSystem
        # nutzt die Rezepte aus utils/constants.py
        self.inventory = Inventory()
        self.crafting = CraftingSystem()

        # Crosshair in der Bildschirmmitte
        self.crosshair = Text(
            parent=camera.ui,
            text="+",
            origin=(0, 0),
            scale=1.2,
            color=color.white,
        )

        # Menüs blenden Spielersteuerung und Crosshair aus.
        self.ui = GameUI(
            self.inventory, self.crafting,
            player=self.player, crosshair=self.crosshair,
        )

    # =========================================================
    # UPDATE (wird jeden Frame von Ursina aufgerufen)
    # =========================================================
    def update(self):
        """HUD, dynamisches Chunk-Streaming und Welt-Respawn pro Frame."""
        p = self.player.position

        # Chunks um den Spieler herum nachladen bzw. entfernen
        self.world.ensure_chunks_around(p.x, p.z)

        # Respawn-Warteschlange der Welt ticken (dt in Sekunden)
        self.world.data.update(time.dt)

        selected = self.inventory.get_selected_item() or "-"
        inventory_counts = {}
        for slot in self.inventory.slots:
            if not slot.is_empty():
                inventory_counts[slot.item] = (
                    inventory_counts.get(slot.item, 0) + slot.count
                )
        inv_str = ", ".join(
            f"{k}:{v}" for k, v in sorted(inventory_counts.items())
        ) or "-"
        self.hud_text.text = (
            f"Position: ({p.x:.1f}, {p.y:.1f}, {p.z:.1f})  |  "
            f"Dimension: {self.current_dimension}  |  "
            f"FPS: {int(1 / time.dt) if time.dt > 0 else 0}\n"
            f"Hotbar [{self.inventory.selected_slot + 1}]: {selected}  |  "
            f"Links: abbauen, Rechts: platzieren\n"
            f"Drops: {inv_str}"
        )

    # =========================================================
    # INPUT (Tastatur- und Maus-Events von Ursina)
    # =========================================================
    def input(self, key):
        """Alle Tasten an die Oberflaeche (GameUI) weiterleiten.

        Das Inventar verwaltet Hotbar-Auswahl, Menüs und Welt-Interaktionen.
        """
        if self.ui.handle_key(key) or self.ui.any_open:
            return
        if key == "left mouse down":
            self._break_targeted_block()
            self.ui.refresh()
        elif key == "right mouse down":
            self._place_targeted_block()
            self.ui.refresh()

    # =========================================================
    # BLOCK-INTERAKTION (Raycast von der Kamera)
    # =========================================================
    def _raycast_block(self):
        """Raycast aus der Kamera; gibt (break_pos, place_pos) oder (None, None).

        Die Trefferflaeche liegt zwischen einem festen Block und einer
        Luftzelle. Blöcke sind um ihre ganzzahlige Mitte ±0.5 gross, daher
        sind die beiden Nachbarzellen round(p ± normal*0.5).
        """
        hit = raycast(
            camera.world_position,
            camera.forward,
            distance=MAX_INTERACTION_RANGE,
            ignore=[self.player, self.sky],
        )
        if not hit.hit or hit.entity is None:
            return None, None
        if not getattr(hit.entity, "is_voxel_chunk", False):
            return None, None

        p, n = hit.world_point, hit.normal
        if p is None or n is None:
            return None, None
        c1 = (
            round(p.x - n[0] * 0.5),
            round(p.y - n[1] * 0.5),
            round(p.z - n[2] * 0.5),
        )
        c2 = (
            round(p.x + n[0] * 0.5),
            round(p.y + n[1] * 0.5),
            round(p.z + n[2] * 0.5),
        )
        if self.world.get_block(*c1):
            return c1, c2
        if self.world.get_block(*c2):
            return c2, c1
        return None, None

    def _break_targeted_block(self):
        """Linksklick: Block abbauen und Drop ins Inventar legen."""
        break_pos, _ = self._raycast_block()
        if break_pos is None:
            return
        drop = self.world.break_block(*break_pos)
        if drop:
            self.inventory.add_item(drop)

    def _place_targeted_block(self):
        """Rechtsklick: ausgewähltes Inventar-Slot neben dem setzen."""
        _, place_pos = self._raycast_block()
        if place_pos is None:
            return
        slot = self.inventory.get_selected_slot()
        if slot.is_empty() or slot.item not in BLOCK_PROPERTIES:
            return
        block_name = slot.item
        if self.world.get_block(*place_pos) is not None:
            return  # Zielzelle bereits belegt
        # Nicht in den eigenen Koerper platzieren
        p = self.player.position
        px, py, pz = p.x, p.y, p.z
        if (
            abs(place_pos[0] + 0.5 - px) < 1.0
            and abs(place_pos[2] + 0.5 - pz) < 1.0
            and py - 1 <= place_pos[1] <= py + 2
        ):
            return
        if self.world.place_block(*place_pos, block_name):
            slot.remove(1)

    # =========================================================
    # RUN (startet die Ursina-Hauptschleife)
    # =========================================================
    def run(self):
        """Startet die Ursina-Game-Loop (blockiert bis zum Fenster-Schließen)."""
        self.app.run()


if __name__ == "__main__":
    game = Game()
    game.run()
