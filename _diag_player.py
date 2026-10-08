"""
Diagnose: Faellt oder klemmt der Spieler beim Bewegen aus der Welt?
=================================================================

Der Spieler laeuft wie im echten Spiel (gehaltene 'w'-Taste) und quert
dabei mehrere Chunk-Grenzen. Gemessen werdenInvarianten, die
unmissverstaendlich sind:

1. HITBOX-KOLLISION: ``player._collides(...)`` - die echte AABB der Spieler-
   Hitbox gegen die Voxel-Daten. True heisst "im Block stecken".
   (Nicht ``floor(y+0.5)``: das liegt bei aufrechtem Stand genau auf der
   Blockgrenze und meldet schon bei +-0.001 einen Fehler.)
2. OBERFLAECHEN-LUECKE: Fusshoehe minus Oberseite des obersten festen
   Blocks der Spalte. Geerdet: ~0.  Tief im Berg: < -1.
3. Y-VERLUST: nur waehrend des Geerdet-Seins - im Flug ist Fallen erlaubt.
4. VOID: y < VOID_Y heisst "durch die Welt gefallen".

Zusaetzlich Phase HITCH: der Spieler-Update wird mit ABSICHTlich riesigen
Frame-Zeiten (bis 2 s) gefuettert, weil genau solche Ausreisser beim
Nachladen der Chunks entstehen.

Start: py _diag_player.py   (Fenster oeffnet sich, beendet sich selbst)
"""
import math
import sys
import time as pytime
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from main import Game  # noqa: E402
from utils.constants import VOID_Y  # noqa: E402

from ursina import (  # noqa: E402
    Entity,
    application,
    held_keys,
    invoke,
    time as ursina_time,
)

WARMUP = 1.0         # s ohne Eingabe: Spieler auf dem Terrain einsettle(n)
WALK = 15.0          # s mit gehaltener 'w'-Taste
HITCH = 4.0          # s mit kuenstlich riesigen Frame-Zeiten

IN_GROUND_TOL = -1.0  # Fuss tiefer = wirklich im Berg (nicht Rundlauf)
STEP_TOL = 1.2        # erlaubter y-Sprung im Schritt (1 Block Stufe)

game = Game()
world = game.world
player = game.player


# =========================================================
# MESSHELFER
# =========================================================
def top_block(x, z):
    """Y des obersten FESTEN Blocks in der Spalte (oder None)."""
    return world.data.get_height_at(int(x), int(z))


def surface_gap(x, y, z):
    """Abstand der Fuesse zur Oberflaeche (0 = stehen, <0 = im Boden)."""
    top = top_block(x, z)
    return None if top is None else y - (top + 0.5)


def support_gap():
    """Abstand der Fuesse zum staetzenden Block darunter (0 = darauf).

    Wichtig: NICHT die Oberflaeche der SPALTE nehmen – unter einem
    Baumkronen-Ueberhang (oder in einer Mulde neben einer hohen Stufe)
    ist der oberste Block der Spalte hoeher als der Spieler, ohne dass
    irgendetwas kaputt waere. Geprueft wird deshalb nur der Block, auf
    dem der Spieler tatsaechlich steht.
    """
    hw = player.half_width
    feet = player.y
    best = None
    for sx in (player.x - hw, player.x + hw):
        for sz in (player.z - hw, player.z + hw):
            cy = player._cell(feet - 0.05)
            while cy > VOID_Y and not player._solid_at(sx, cy, sz):
                cy -= 1
            if cy <= VOID_Y:
                continue
            surf = cy + 0.5
            if best is None or surf > best:
                best = surf
    return None if best is None else feet - best


def in_solid():
    """Steckt die echte Spieler-Hitbox in einem festen Block?"""
    return player._collides(player.x, player.y, player.z)


# =========================================================
# ZUSTAND
# =========================================================
state = {
    "t0": pytime.time(),
    "phase": "warmup",
    "frames": 0,
    "dt_max": 0.0,
    "dt_sum": 0.0,
    "prev_y": None,
    "prev_xz": None,
    "clip_frames": 0,
    "clip_worst": None,       # (t, y, luecke)
    "min_gap_grounded": None,
    "max_gap_airborne": None,
    "loss_grounded": [],      # (t, dy) nur waehrend grounded
    "void_frames": 0,
    "y_min": None,
    "rescues0": player.rescues,
    "traveled": 0.0,
    "turns": 0,
    "stuck_since": None,
    "last_xz": None,
    "history": deque(maxlen=40),
    "sink": None,
    "void_test": None,
    "hitch_plan": [],
    "hitch_i": 0,
}
def watch():
    """Laeuft jeden Frame NACH dem Spieler-Update."""
    t = pytime.time() - state["t0"]
    dt = ursina_time.dt_unscaled
    x, y, z = player.x, player.y, player.z
    prev_y = state["prev_y"]
    dy = 0.0 if prev_y is None else y - prev_y

    state["frames"] += 1
    state["dt_sum"] += dt
    state["dt_max"] = max(state["dt_max"], dt)
    if state["y_min"] is None or y < state["y_min"]:
        state["y_min"] = y

    pxz = state["prev_xz"]
    if pxz is not None and state["phase"] == "walk":
        state["traveled"] += math.hypot(x - pxz[0], z - pxz[1])
    state["prev_xz"] = (x, z)
    state["prev_y"] = y

    if state["phase"] in ("walk", "hitch"):
        state["history"].append(
            (round(t, 2), round(dt, 3), round(x, 2), round(y, 2),
             round(z, 2), player.grounded, round(player.air_time, 2),
             top_block(x, z)))

        # 1) ECHTE HITBOX IM BLOCK?
        if in_solid():
            state["clip_frames"] += 1
            if state["clip_worst"] is None:
                state["clip_worst"] = (round(t, 2), round(y, 2),
                                       surface_gap(x, y, z))
                print(f"CLIP t={t:.2f}s pos=({x:.2f}, {y:.2f}, {z:.2f}) "
                      f"luecke={surface_gap(x, y, z)} "
                      f"grounded={player.grounded} "
                      f"luftzeit={player.air_time:.2f} "
                      f"rescues={player.rescues}", flush=True)

        # 2) LUECKE ZUM STUETZENDEN BLOCK (Baumkronen duerfen hoeher sein)
        gap = support_gap()
        if gap is not None:
            if player.grounded:
                if (state["min_gap_grounded"] is None
                        or gap < state["min_gap_grounded"]):
                    state["min_gap_grounded"] = gap
            elif (state["max_gap_airborne"] is None
                    or gap > state["max_gap_airborne"]):
                state["max_gap_airborne"] = gap

        # 3) Y-VERLUST NUR IM SCHRITT (im Flug ist Fallen erlaubt)
        if player.grounded and dy < -STEP_TOL:
            state["loss_grounded"].append((round(t, 2), round(dy, 2)))

        # 4) VOID
        if y < VOID_Y:
            state["void_frames"] += 1

    # --- steckt fest? dann drehen (wie ein echter Spieler) ---
    if state["phase"] in ("walk", "hitch"):
        lx, lz = state["last_xz"] or (x, z)
        if abs(x - lx) < 0.3 and abs(z - lz) < 0.3:
            if state["stuck_since"] is None:
                state["stuck_since"] = t
            elif t - state["stuck_since"] > 1.2:
                player.rotation_y += 35
                state["turns"] += 1
                state["stuck_since"] = t
        else:
            state["stuck_since"] = None
        state["last_xz"] = (x, z)


watcher = Entity(name="diag_watch", eternal=True)
watcher.update = watch


def start_walk():
    state["phase"] = "walk"
    held_keys["w"] = 1
    print(f"PHASE walk ab t={pytime.time() - state['t0']:.2f}s", flush=True)


def start_hitch():
    """Frame-Zeiten absichtlich aufblaehen (Chunk-Nachladen simulieren)."""
    state["phase"] = "hitch"
    state["hitch_plan"] = [
        2.0, 1.2, 0.5, 1.8, 0.3, 1.5, 0.05, 2.0, 0.9, 0.05,
        1.1, 0.4, 2.0, 0.05, 0.7, 1.6, 0.05, 0.3, 1.9, 0.05,
    ]
    state["hitch_i"] = 0
    print(f"PHASE hitch ab t={pytime.time() - state['t0']:.2f}s "
          f"(kuenstliche Frame-Zeiten bis 2 s)", flush=True)
    invoke(next_hitch, delay=0.05)


def next_hitch():
    """Setzt time.dt kuenstlich und ruft den Spieler-Update direkt auf."""
    i = state["hitch_i"]
    if i >= len(state["hitch_plan"]):
        state["phase"] = "settle"
        print(f"PHASE settle ab t={pytime.time() - state['t0']:.2f}s",
              flush=True)
        return
    fake_dt = state["hitch_plan"][i]
    state["hitch_i"] = i + 1
    ursina_time.dt = fake_dt
    player.update()
    invoke(next_hitch, delay=0.05)


def start_sink():
    """Spieler 6 Bloecke unter die Oberflaeche setzen (Klipping)."""
    state["phase"] = "sink"
    held_keys["w"] = 0
    y0 = player.y
    state["sink"] = {"y_vor": round(y0, 2)}
    player.y = y0 - 6
    player.grounded = False
    print(f"PHASE sink ab t={pytime.time() - state['t0']:.2f}s "
          f"y {y0:.2f} -> {player.y:.2f}", flush=True)


def check_sink():
    """Nach 1 s: steht der Spieler wieder sauber auf der Oberflaeche?"""
    s = state["sink"]
    s["y_nach"] = round(player.y, 2)
    s["luecke"] = round(support_gap(), 2)
    s["im_block"] = in_solid()
    s["gerettet"] = (not s["im_block"]) and abs(s["luecke"]) <= 0.2
    print(f"SINK y_vor={s['y_vor']} y_nach={s['y_nach']} "
          f"luecke={s['luecke']} im_block={s['im_block']} "
          f"gerettet={s['gerettet']} rescues={player.rescues}", flush=True)


def start_void():
    """Spieler unter VOID_Y setzen - muss am Spawn landen."""
    state["phase"] = "void"
    state["void_test"] = {"y_vor": round(player.y, 2)}
    player.y = VOID_Y - 10
    player.grounded = False
    print(f"PHASE void ab t={pytime.time() - state['t0']:.2f}s "
          f"y -> {player.y:.2f}", flush=True)


def check_void():
    v = state["void_test"]
    spawn = world.data.spawn_point
    v["y_nach"] = round(player.y, 2)
    v["pos"] = (round(player.x, 2), round(player.z, 2))
    v["luecke"] = round(support_gap(), 2)
    v["im_block"] = in_solid()
    v["am_spawn"] = (abs(player.x - spawn[0]) < 4
                     and abs(player.z - spawn[2]) < 4)
    v["ok"] = v["am_spawn"] and not v["im_block"] and v["y_nach"] > VOID_Y
    print(f"VOID y_vor={v['y_vor']} y_nach={v['y_nach']} "
          f"pos={v['pos']} spawn={tuple(round(c, 1) for c in spawn)} "
          f"luecke={v['luecke']} im_block={v['im_block']} "
          f"am_spawn={v['am_spawn']} ok={v['ok']} "
          f"rescues={player.rescues}", flush=True)


def finish():
    """Auswertung + Beenden."""
    s = state["sink"] or {}
    v = state["void_test"] or {}
    print("---- DIAG_PLAYER ----", flush=True)
    print(f"frames={state['frames']} dt_max={state['dt_max']:.3f}s "
          f"dt_mittel={round(state['dt_sum'] / max(1, state['frames']), 4)}s",
          flush=True)
    print(f"1) hitbox_im_block_frames={state['clip_frames']} "
          f"erster_fall={state['clip_worst']}", flush=True)
    print(f"2) luecke_geerdet_min={state['min_gap_grounded']} "
          f"luecke_in_der_luft_max={state['max_gap_airborne']}", flush=True)
    print(f"3) y_verlust_im_schritt={len(state['loss_grounded'])} "
          f"{sorted(state['loss_grounded'], key=lambda r: r[1])[:3]}",
          flush=True)
    print(f"4) void_frames={state['void_frames']} y_min={state['y_min']}",
          flush=True)
    print(f"strecke={round(state['traveled'], 1)} Bloecke "
          f"drehungen={state['turns']} "
          f"befreiungen={player.rescues - state['rescues0']} "
          f"chunks={len(world.chunks)}", flush=True)
    print(f"sink: gerettet={s.get('gerettet')} luecke={s.get('luecke')}",
          flush=True)
    print(f"void: ok={v.get('ok')} am_spawn={v.get('am_spawn')}", flush=True)

    fail = []
    if state["clip_frames"]:
        fail.append("Hitbox im Block")
    if state["min_gap_grounded"] is not None and \
            state["min_gap_grounded"] < IN_GROUND_TOL:
        fail.append("Fuss tief im Boden")
    if state["loss_grounded"]:
        fail.append("y-Verlust im Schritt")
    if state["void_frames"]:
        fail.append("im Void")
    if not s.get("gerettet"):
        fail.append("Befreiung aus dem Block fehlt")
    if not v.get("ok"):
        fail.append("Void-Respawn fehlt")

    if fail:
        print("PLAYER_FALL_REPRO: " + ", ".join(fail), flush=True)
    else:
        print("PLAYER_STABLE_OK", flush=True)
    invoke(application.quit, delay=0.3)


invoke(start_walk, delay=WARMUP)
invoke(start_hitch, delay=WARMUP + WALK)
invoke(start_sink, delay=WARMUP + WALK + HITCH)
invoke(check_sink, delay=WARMUP + WALK + HITCH + 1.0)
invoke(start_void, delay=WARMUP + WALK + HITCH + 1.3)
invoke(check_void, delay=WARMUP + WALK + HITCH + 2.3)
invoke(finish, delay=WARMUP + WALK + HITCH + 2.8)
game.run()
print("game.run() returned", flush=True)