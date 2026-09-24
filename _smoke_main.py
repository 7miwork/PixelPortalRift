"""Watchdog smoke-test: launches main.py, waits, reports crash or survival."""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WAIT_SECONDS = 25

proc = subprocess.Popen(
    [sys.executable, str(ROOT / "main.py")],
    cwd=str(ROOT),
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding="utf-8",
    errors="replace",
)

deadline = time.time() + WAIT_SECONDS
crashed = None
while time.time() < deadline:
    if proc.poll() is not None:
        crashed = proc.returncode
        break
    time.sleep(0.5)

output = ""
if crashed is not None:
    try:
        output = proc.communicate(timeout=5)[0] or ""
    except Exception:
        output = ""
else:
    proc.kill()
    try:
        output = proc.communicate(timeout=5)[0] or ""
    except Exception:
        output = ""

print("--- process output (last 4000 chars) ---")
print(output[-4000:])

if crashed is not None:
    print(f"SMOKE_FAIL: main.py exited early with code {crashed}")
    sys.exit(1)

print(f"SMOKE_OK: main.py still running after {WAIT_SECONDS}s (killed by watchdog)")
