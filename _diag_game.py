"""Diagnose: startet das Spiel, sammelt Render-Stats + Screenshot, beendet sich."""
import sys
import time as pytime
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

t0 = pytime.time()
from main import Game  # noqa: E402
t_import = pytime.time() - t0

t0 = pytime.time()
game = Game()
t_build = pytime.time() - t0
print(f"TIMING import={t_import:.2f}s game_init={t_build:.2f}s", flush=True)

from ursina import (  # noqa: E402
    application,
    camera,
    Entity,
    invoke,
    scene,
    time as ursina_time,
    window,
)

# ---- Frame-Zeit-Sonde: sammelt (zeit, dt) pro Frame fuer Segment-Auswertung
probe = Entity(name="frame_probe", eternal=True, add_to_scene_entities=True)
probe.t0 = pytime.time()
probe.samples = []
def _probe_update():
    probe.samples.append((pytime.time() - probe.t0, ursina_time.dt_unscaled))
probe.update = _probe_update


def avg_fps(t_a, t_b):
    ds = [dt for t, dt in probe.samples if t_a <= t <= t_b and dt > 0]
    if not ds:
        return None
    return round(len(ds) / sum(ds), 1)


def freeze_player():
    """Stoppt FPC-Update inkl. der 7 Raycasts pro Frame (A/B-Messung)."""
    game.player.update = lambda: None
    print(f"SEGMARK player_frozen t={probe.t0 and pytime.time() - probe.t0:.2f}s",
          flush=True)


invoke(freeze_player, delay=4.0)


def dump():
    try:
        chunk_meshes = [e for e in scene.entities
                        if getattr(e, "is_voxel_chunk", False)]
        from panda3d.core import ClockObject
        clock = ClockObject.getGlobalClock()
        for method_name in ("get_average_frame_rate", "getFramerate",
                            "get_frame_rate"):
            try:
                fps = round(getattr(clock, method_name)(), 1)
                break
            except AttributeError:
                continue
        else:
            fps = -1
        print("---- DIAGNOSE ----", flush=True)
        print("fps:", fps, flush=True)
        print("fps_segment_baseline_2_3.8s:", avg_fps(2.0, 3.8), flush=True)
        print("fps_segment_player_frozen_5_7.8s:", avg_fps(5.0, 7.8), flush=True)
        print("frame_samples:", len(probe.samples), flush=True)
        print("scene_entities:", len(scene.entities), flush=True)
        print("chunk_meshes:", len(chunk_meshes), flush=True)
        print("chunks:", len(game.world.chunks), flush=True)
        print("data_blocks:", game.world.data.block_count(), flush=True)
        print("player_pos:", tuple(round(v, 1) for v in game.player.position), flush=True)
        print("player_grounded:", game.player.grounded, flush=True)
        print("camera_wp:", tuple(round(v, 1) for v in camera.world_position), flush=True)
        print("window_color:", getattr(window, "color", "n/a"), flush=True)
        print("sky_enabled:", game.sky.enabled, flush=True)
        print("hud_text:", repr(game.hud_text.text[:90]), flush=True)
    except Exception:
        traceback.print_exc()

    try:
        from panda3d.core import Filename
        game.app.win.saveScreenshot(
            Filename.fromOsSpecific(str(ROOT / "diag_shot.png")))
        print("screenshot_ok: diag_shot.png", flush=True)
    except Exception as exc:
        print("screenshot_fail:", exc, flush=True)

    # Kurz warten, damit das Screenshot-Request-Frame noch gerendert wird
    invoke(application.quit, delay=0.5)


invoke(dump, delay=8)
game.run()
print("game.run() returned", flush=True)
