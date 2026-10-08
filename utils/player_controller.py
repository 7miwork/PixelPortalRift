"""
utils/player_controller.py – Robuster 3D-Spieler (Voxel-Kollision)
==================================================================

Warum gibt es diese Datei?
--------------------------
Der Ursina-Prefab ``FirstPersonController`` prüft Kollisionen nur mit
kurzen Raycasts ("Fühler") direkt am Spieler und teleportiert ihn dann
um ``speed * dt`` Blöcke. Beim Nachladen von Chunks ruckelt das Spiel
(dt bis über 1 Sekunde) – ein Frame schiebt den Spieler dann mehrere
Blöcke weit in einen Hang hinein:

1. Der Spieler steckt IM Block (die Fühler-Rays starten schon im Berg
   und treffen keine Fläche mehr),
2. der Kopf-Ray meldet trotzdem "Boden" (``grounded = True``),
3. läuft der Spieler weiter, steht er plötzlich in der Luft und fällt,
4. die Fall-Formel des Prefabs (``y -= min(air_time, dist) * dt * 100``)
   hängt von dt ab und tunnelt bei Rucklern durch den Boden → der
   Spieler fällt bis y = -800 ins Leere.

Deshalb macht ``VoxelPlayer`` die Steuerung selbst:

- Kollision gegen die VOXEL-DATEN (``World.is_solid``) statt gegen die
  sichtbaren Mesh-Flächen – im Berginneren gibt es keine Flächen!
- AABB-Hitbox: Höhe ``PLAYER_HEIGHT_3D``, halbe Breite
  ``PLAYER_HALF_WIDTH_3D``.
- Bewegung in kleinen Teilschritten (max. ``PLAYER_MAX_SUBSTEP`` Blöcke)
  → kein Tunneling, auch bei einem 1-Sekunden-Ruckler.
- Achsen-Auflösung (erst X, dann Z, dann Y) statt Teleport.
- Automatisches Hochsteigen von Stufen bis ``PLAYER_STEP_HEIGHT_3D`` und
  weiches Mitgehen beim Laufen bergab.
- dt-Begrenzung über ``PLAYER_MAX_PHYSICS_DT``.
- Sicherheitsnetz: aus Blöcken freisetzen (``_rescue_if_stuck``) und
  Void-Respawn (``_respawn``) unter ``VOID_Y``.

Die Maus-/Kamera-Steuerung ist 1:1 die des Prefabs, damit sich das Spiel
genau gleich anfühlt (Kamera schaut nach vorn, WASD bewegt, Leertaste
springt).
"""

import math

from ursina import Vec3, clamp, held_keys, mouse, time
from ursina.prefabs.first_person_controller import FirstPersonController

from utils.constants import (
    PLAYER_GRAVITY_3D,
    PLAYER_HALF_WIDTH_3D,
    PLAYER_HEIGHT_3D,
    PLAYER_JUMP_HEIGHT_3D,
    PLAYER_MAX_PHYSICS_DT,
    PLAYER_MAX_SUBSTEP,
    PLAYER_SPEED_3D,
    PLAYER_STEP_HEIGHT_3D,
    VOID_Y,
)

# Kleiner Abstand, damit der Spieler nie exakt in einer Blockgrenze
# steht (auf der Fläche kleben statt darin schweben).
EPS = 0.001


def _axis_min(cells, axis):
    """Kleinste Zell-Koordinate der blockierenden Zellen auf einer Achse.

    ``cells`` sind Voxel-Tripel (cx, cy, cz) – ``min(cells)`` würde die
    Tupel vergleichen und keine Zahl liefern, deshalb hier die Achse
    (0 = x, 1 = y, 2 = z) explizit auswählen.
    """
    return min(c[axis] for c in cells)


def _axis_max(cells, axis):
    """Grösste Zell-Koordinate der blockierenden Zellen auf einer Achse."""
    return max(c[axis] for c in cells)


class VoxelPlayer(FirstPersonController):
    """FirstPersonController mit echter Voxel-Kollision (siehe Modul-Doku).

    ``position`` ist – genau wie im Prefab – die Position der FÜSSE:
    die Hitbox reicht von ``y`` bis ``y + height``.
    """

    def __init__(self, world, **kwargs):
        """Erzeugt den Spieler. ``world`` ist die VoxelWorld (Kollisionsdaten)."""
        super().__init__(**kwargs)
        self.world = world

        # Physik-Werte aus utils/constants.py (statt Ursina-Standard)
        self.speed = kwargs.get("speed", PLAYER_SPEED_3D)
        self.gravity = kwargs.get("gravity", PLAYER_GRAVITY_3D)
        self.jump_height = kwargs.get("jump_height", PLAYER_JUMP_HEIGHT_3D)
        self.height = kwargs.get("height", PLAYER_HEIGHT_3D)
        self.half_width = PLAYER_HALF_WIDTH_3D

        self.velocity_x = 0.0     # eigene Geschwindigkeit in Block/Sekunde
        self.velocity_y = 0.0
        self.velocity_z = 0.0
        self.grounded = False
        self.air_time = 0.0
        self.jumping = False
        self.direction = Vec3(0, 0, 0)
        self.rescues = 0          # Zähler fürs F3-Debug (Befreiungen/Respawns)

        # False, solange ein Menü (Inventar/Crafting) offen ist:
        # Maus-Blick, WASD und Springen sind dann gesperrt – die Physik
        # (Schwerkraft, Sicherheitsnetz) läuft aber weiter, damit der
        # Spieler z. B. beim Öffnen nicht in der Luft schwebt.
        self.controls_enabled = True

        # Kamera-Pivot auf Augenhöhe des 2 Block großen Spielers
        self.camera_pivot.y = self.height

        # Falls der Startpunkt (Spawn) doch in einem Block liegt: befreien.
        self._rescue_if_stuck()
        self.grounded = self._ground_below()

    # =========================================================
    # VOXEL-ABFRAGEN (Kollisionsdaten)
    # =========================================================
    @staticmethod
    def _cell(value):
        """Blockzelle einer Weltkoordinate (Blockmitte = ganze Zahl).

        Blöcke sind um ihre ganzzahlige Mitte ±0.5 groß, deshalb gehört
        die Koordinate ``v`` zur Zelle ``floor(v + 0.5)``.
        """
        return int(math.floor(value + 0.5))

    def _solid_at(self, x, y, z):
        """Ist an der Weltposition (x, y, z) ein fester Block?"""
        return self.world.is_solid(self._cell(x), self._cell(y), self._cell(z))

    def _cells_of_box(self, x, y, z):
        """Alle Voxel-Zellen, die die Spieler-Hitbox an (x, y, z) berührt."""
        hw = self.half_width
        x0, x1 = self._cell(x - hw), self._cell(x + hw)
        z0, z1 = self._cell(z - hw), self._cell(z + hw)
        y0 = self._cell(y + EPS)
        y1 = self._cell(y + self.height - EPS)
        for cy in range(min(y0, y1), max(y0, y1) + 1):
            for cx in range(min(x0, x1), max(x0, x1) + 1):
                for cz in range(min(z0, z1), max(z0, z1) + 1):
                    yield cx, cy, cz

    def _collides(self, x, y, z):
        """Steckt die Hitbox an (x, y, z) in festen Blöcken?"""
        for cx, cy, cz in self._cells_of_box(x, y, z):
            if self.world.is_solid(cx, cy, cz):
                return True
        return False

    # =========================================================
    # BEWEGUNG MIT KOLLISION (Achsen + Teilschritte)
    # =========================================================
    def _ground_below(self, y_offset=-0.05):
        """Steht unter den Füßen (leicht versetzt) ein fester Block?"""
        hw = self.half_width
        feet_y = self.y + y_offset
        for x in (self.x - hw, self.x + hw):
            for z in (self.z - hw, self.z + hw):
                if self._solid_at(x, feet_y, z):
                    return True
        return False

    def _blocking_cells(self, x, y, z):
        """Menge der festen Zellen, die die Hitbox an (x, y, z) verletzt."""
        return {c for c in self._cells_of_box(x, y, z)
                if self.world.is_solid(*c)}

    def _step_height_for(self, x, z):
        """Nötige Steighöhe für eine Stufe an (x, z) oder ``None``.

        Wird beim Laufen gegen einen Block geprüft: liegt der höchste
        feste Block im Körperbereich höchstens ``PLAYER_STEP_HEIGHT_3D``
        über den Füßen UND ist darüber Platz, darf der Spieler
        automatisch hochsteigen (wie in Minecraft eine 1-Block-Stufe).
        """
        hw = self.half_width
        highest = None
        for cx in (self._cell(x - hw), self._cell(x + hw)):
            for cz in (self._cell(z - hw), self._cell(z + hw)):
                for cy in range(self._cell(self.y + EPS),
                                self._cell(self.y + self.height - EPS) + 1):
                    if self.world.is_solid(cx, cy, cz):
                        if highest is None or cy > highest:
                            highest = cy
        if highest is None:
            return None

        step = (highest + 0.5 + EPS) - self.y
        if not (0.0 < step <= PLAYER_STEP_HEIGHT_3D + EPS):
            return None
        if self._collides(x, self.y + step, z):
            return None  # oben ist kein Platz (Decke)
        return step

    def _move_axis_x(self, amount):
        """Verschiebt den Spieler auf der X-Achse und löst Kollisionen."""
        if not amount:
            return
        target = self.x + amount
        blocking = self._blocking_cells(target, self.y, self.z)
        if not blocking:
            self.x = target
            return

        # Stufe? (nur vom Boden aus, nicht im Sprung)
        if self.grounded and self.air_time <= 0.0:
            step = self._step_height_for(target, self.z)
            if step is not None:
                self.y += step
                self.x = target
                return

        if amount > 0:
            limit = _axis_min(blocking, 0) - 0.5 - self.half_width - EPS
            self.x = max(self.x, min(target, limit))
        else:
            limit = _axis_max(blocking, 0) + 0.5 + self.half_width + EPS
            self.x = min(self.x, max(target, limit))
        self.velocity_x = 0.0

    def _move_axis_z(self, amount):
        """Verschiebt den Spieler auf der Z-Achse und löst Kollisionen."""
        if not amount:
            return
        target = self.z + amount
        blocking = self._blocking_cells(self.x, self.y, target)
        if not blocking:
            self.z = target
            return

        if self.grounded and self.air_time <= 0.0:
            step = self._step_height_for(self.x, target)
            if step is not None:
                self.y += step
                self.z = target
                return

        if amount > 0:
            limit = _axis_min(blocking, 2) - 0.5 - self.half_width - EPS
            self.z = max(self.z, min(target, limit))
        else:
            limit = _axis_max(blocking, 2) + 0.5 + self.half_width + EPS
            self.z = min(self.z, max(target, limit))
        self.velocity_z = 0.0

    def _move_axis_y(self, amount):
        """Verschiebt den Spieler auf der Y-Achse (Springen/Fallen)."""
        if not amount:
            return
        target = self.y + amount
        blocking = self._blocking_cells(self.x, target, self.z)
        if not blocking:
            self.y = target
            return

        if amount < 0:                     # nach unten: auf dem Boden landen
            limit = _axis_max(blocking, 1) + 0.5 + EPS
            self.y = min(self.y, max(target, limit))
            self.velocity_y = 0.0
            self.land()
        else:                              # nach oben: an die Decke stoßen
            limit = _axis_min(blocking, 1) - 0.5 - self.height - EPS
            self.y = max(self.y, min(target, limit))
            self.velocity_y = 0.0
            self.jumping = False

    def _snap_down(self):
        """Kleine Stufen bergab automatisch mitgehen (weiches Laufen).

        Nur wenn der Spieler eben noch auf dem Boden stand und die
        nächste Fläche höchstens eine Stufe tiefer liegt – so bleibt er
        beim Laufen an Hängen auf dem Terrain kleben, statt bei jedem
        Hügel kurz zu "schweben".
        """
        if self.air_time > 0.0 or self.velocity_y > 0.0:
            return
        if self._ground_below():
            return

        hw = self.half_width
        for drop in (0.1, 0.35, 0.6, 0.85, PLAYER_STEP_HEIGHT_3D + EPS):
            new_y = self.y - drop
            if self._collides(self.x, new_y, self.z):
                return                     # irgendwo blockiert → nicht sinken
            for x in (self.x - hw, self.x + hw):
                for z in (self.z - hw, self.z + hw):
                    if not self._solid_at(x, new_y - 0.05, z):
                        continue
                    self.y = new_y
                    self.velocity_y = 0.0
                    return

    # =========================================================
    # UPDATE (wird jeden Frame von Ursina aufgerufen)
    # =========================================================
    def update(self):
        """Maus-Steuerung, Bewegung, Schwerkraft und Kollision pro Frame."""
        # --- Kamera/Maus genau wie im Ursina-Prefab (nur bei freien Controls,
        #     sonst dreht sich die Kamera mit, während die Maus über das
        #     offene Menü fährt) ---
        if self.controls_enabled:
            self.rotation_y += mouse.velocity[0] * self.mouse_sensitivity[1]
            self.camera_pivot.rotation_x -= mouse.velocity[1] * self.mouse_sensitivity[0]
            self.camera_pivot.rotation_x = clamp(
                self.camera_pivot.rotation_x, -90, 90)

        # --- dt begrenzen: ein Ruckler beim Chunk-Nachladen darf den
        #     Spieler nicht mehrere Blöcke weit teleportieren ---
        dt = min(time.dt, PLAYER_MAX_PHYSICS_DT)
        if dt <= 0:
            return

        # --- Richtung aus der Tastatur (WASD) – nur bei freien Controls;
        #     die Schwerkraft darunter läuft weiter ---
        if self.controls_enabled:
            direction = (self.forward * (held_keys["w"] - held_keys["s"])
                         + self.right * (held_keys["d"] - held_keys["a"]))
        else:
            direction = Vec3(0, 0, 0)
        if direction.length() > 0:
            direction = direction.normalized()
        self.direction = direction

        # --- Schwerkraft (echte Integration statt Prefab-Formel) ---
        if self.grounded and self.velocity_y <= 0:
            self.velocity_y = 0.0
        self.velocity_y -= self.gravity * dt

        horizontal = direction * self.speed * dt
        vertical = self.velocity_y * dt

        # --- in Teilschritten bewegen: kein Tunneling bei großem dt ---
        step_count = max(1, int(math.ceil(
            max(abs(horizontal.x), abs(vertical), abs(horizontal.z))
            / PLAYER_MAX_SUBSTEP)))
        for _ in range(step_count):
            self._move_with_collision(horizontal.x / step_count,
                                      vertical / step_count,
                                      horizontal.z / step_count,
                                      dt / step_count)

        # --- Sicherheitsnetz: nie im Block stecken, nie in den Void fallen ---
        self._rescue_if_stuck()

    def _move_with_collision(self, dx, dy, dz, dt):
        """Ein Physik-Teilschritt: erst horizontal (mit Stufen), dann vertikal."""
        if dx:
            self._move_axis_x(dx)
        if dz:
            self._move_axis_z(dz)
        if (dx or dz) and self.air_time <= 0.0:
            self._snap_down()

        if dy:
            self._move_axis_y(dy)

        on_ground = self._ground_below()
        if on_ground and self.velocity_y <= 0:
            self.land()                    # air_time/velocity_y zurücksetzen
        else:
            # Beim Aufsteigen (Sprung) ist man NICHT geerdet – auch wenn
            # die Füße in diesem Teilschritt noch fast am Boden sind.
            self.grounded = False
            self.air_time += dt

    # =========================================================
    # SPRINGEN
    # =========================================================
    def input(self, key):
        """Leertaste = springen (wie im Prefab) – nur bei freien Controls."""
        if key == "space" and self.controls_enabled:
            self.jump()

    def jump(self):
        """Springt, wenn der Spieler auf dem Boden steht."""
        if not self.grounded:
            return

        # v0 = sqrt(2 * g * h) ⇒ der Spieler erreicht genau PLAYER_JUMP_HEIGHT_3D
        self.grounded = False
        self.air_time = 0.001
        self.jumping = True
        self.velocity_y = math.sqrt(2.0 * self.gravity * self.jump_height)

    def land(self):
        """Setzt den Spieler bei einer Landung zurück."""
        self.air_time = 0.0
        self.grounded = True
        self.jumping = False
        self.velocity_y = 0.0

    # =========================================================
    # SICHERHEITSNETZ (Befreiung aus Blöcken, Void-Respawn)
    # =========================================================
    def _rescue_if_stuck(self):
        """Befreit den Spieler aus festen Blöcken und aus dem Void.

        Selbst wenn irgendetwas schiefgeht (Teleport, Dimensionswechsel,
        geladene Blockdaten einer unbegehbaren Stelle), hängt der Spieler
        höchstens einen Frame fest – er fällt nie ins Leere.
        """
        if self.y < VOID_Y:
            self._respawn()
            return

        if not self._collides(self.x, self.y, self.z):
            return

        # Höchsten festen Block im Körperbereich suchen und darüber setzen
        hw = self.half_width
        top = None
        for cx in (self._cell(self.x - hw), self._cell(self.x + hw)):
            for cz in (self._cell(self.z - hw), self._cell(self.z + hw)):
                for cy in range(self._cell(self.y + EPS),
                                self._cell(self.y + self.height - EPS) + 1):
                    if self.world.is_solid(cx, cy, cz):
                        if top is None or cy > top:
                            top = cy
        if top is None:
            return

        self.y = top + 0.5 + EPS
        self.velocity_y = 0.0
        self.grounded = True
        self.air_time = 0.0
        self.jumping = False
        self.rescues += 1

    def _respawn(self):
        """Setzt den Spieler zurück an den Spawn-Punkt der Welt."""
        spawn = self.world.data.spawn_point or (self.x, self.y, self.z)
        self.position = (spawn[0], spawn[1] + 1.8, spawn[2])
        self.velocity_x = self.velocity_y = self.velocity_z = 0.0
        self.grounded = False
        self.air_time = 0.0
        self.jumping = False
        self.rescues += 1
        self._rescue_if_stuck()


