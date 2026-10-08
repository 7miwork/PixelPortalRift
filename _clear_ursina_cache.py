"""Delete stale compiled caches for ursina so the latest source is used."""
import os
import shutil
from pathlib import Path

targets = [
    Path("C:/Users/user/AppData/Local/Programs/Python/Python311"
         "/Lib/site-packages/ursina/__pycache__"),
]
removed = []
for d in targets:
    if not d.exists():
        print("skip:", d)
        continue
    for p in d.iterdir():
        if p.suffix == ".pyc":
            try:
                p.unlink()
                removed.append(str(p))
            except Exception as exc:
                print("fail:", p, exc)

print("removed:", removed)
