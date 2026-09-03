"""
main.py – Hauptprogramm von PixelPortalRift (3D-Version)
=========================================================

Seit der Migration von Pygame (2D) auf Ursina (3D) steuert diese Datei
die gesamte 3D-Voxelwelt:

- Ursina-Fenster (statt pygame-Fenster)
- Sky + FirstPersonController (WASD + Maus, Springen mit Space)
- Die Voxel-Welt aus Chunks (siehe utils/voxel_world.py)

PHASE 1 (Grundgerüst): Es gibt noch einen flachen Testchunk
(Gras/Erde/Stein). Die weiteren Systeme (Inventar, Mobs, Portale,
Crafting, Speichern) werden in den folgenden Phasen migriert.

Starte das Spiel mit: python main.py
"""

from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

from utils.constants import (
    DIMENSIONS,
    TEST_CHUNK_SURFACE_Y,
    PLAYER_SPEED_3D,
    PLAYER_JUMP_HEIGHT_3D,
    PLAYER_GRAVITY_3D,
)
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


class Game:
    """
    Die Hauptklasse des 3D-Spiels. Steuert alles.

    Wichtige Attribute:
        world:             Die aktuelle Voxel-Welt (VoxelWorld-Objekt)
        player:            Der FirstPersonController (Ursina-Prefab)
        current_dimension: Name der aktuellen Dimension (z.B. "grassland")
        hud_text:          Text-Overlay mit Position/FPS (F3-Debug vorbereitet)
    """

    def __init__(self):
        """Erzeugt das Ursina-Fenster, den Himmel, die Testwelt und den Spieler."""
        self.app = Ursina(title="PixelPortalRift 3D - Dimensional Adventure")

        # ---- Himmel in der Farbe der aktuellen Dimension ----
        sky_color = rgb_to_ursina_color(DIMENSIONS["grassland"]["sky_color"])
        self.sky = Sky(color=sky_color)

        # ---- Beleuchtung (damit die Block-Flächen Plastizität bekommen) ----
        DirectionalLight(y=10, z=-10, shadows=False, rotation=(45, -45, 0))
        AmbientLight(color=color.rgba(0.6, 0.6, 0.6, 1))

        # ---- Welt: PHASE 1 = flacher Testchunk ----
        self.world = VoxelWorld(BlockTextureLibrary())
        self.world.generate_flat_test_chunk(cx=0, cz=0)

        # ---- Spieler: FirstPersonController aus dem Ursina-Prefab ----
        # Spawn in der Mitte des Testchunks, oberhalb der Oberfläche.
        spawn_x, spawn_z = 8, 8
        spawn_y = TEST_CHUNK_SURFACE_Y + 3
        self.player = FirstPersonController(
            position=(spawn_x, spawn_y, spawn_z),
            speed=PLAYER_SPEED_3D,
            jump_height=PLAYER_JUMP_HEIGHT_3D,
        )
        # Schwerkraft aus constants.py (statt Ursina-Standard)
        self.player.gravity = PLAYER_GRAVITY_3D

        # ---- HUD: Positions-Anzeige (Vorstufe des späteren F3-Debug) ----
        self.hud_text = Text(
            parent=camera.ui,
            position=(-0.85, 0.47),
            origin=(-0.5, 0.5),
            text="",
            scale=0.8,
        )

        self.current_dimension = "grassland"

    # =========================================================
    # UPDATE (wird jeden Frame von Ursina aufgerufen)
    # =========================================================
    def update(self):
        """Aktualisiert das HUD (Position + FPS). Spiel-Logik folgt in Phase 2+."""
        p = self.player.position
        self.hud_text.text = (
            f"Position: ({p.x:.1f}, {p.y:.1f}, {p.z:.1f})  |  "
            f"Dimension: {self.current_dimension}  |  FPS: {int(1 / time.dt) if time.dt > 0 else 0}"
        )

    # =========================================================
    # INPUT (Tastatur-Events von Ursina)
    # =========================================================
    def input(self, key):
        """Tastatureingaben (aktuell nur Vorbereitung für F3-Debug-Toggle)."""
        if key == "f3":
            self.hud_text.enabled = not self.hud_text.enabled

    # =========================================================
    # RUN (startet die Ursina-Hauptschleife)
    # =========================================================
    def run(self):
        """Startet die Ursina-Game-Loop (blockiert bis zum Fenster-Schließen)."""
        self.app.run()


if __name__ == "__main__":
    game = Game()
    game.run()
