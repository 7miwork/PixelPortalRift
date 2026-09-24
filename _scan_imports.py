"""Scannt alle Projekt-*.py nach externen Imports (fuer requirements.txt)."""
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STDLIB = set(sys.stdlib_module_names)
LOCAL = {"utils", "main"}

found = {}
for path in sorted(ROOT.rglob("*.py")):
    if path.name.startswith("_") or "__pycache__" in path.parts:
        continue
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError as exc:
        print(f"skip {path.name}: {exc}")
        continue
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module] if node.module else []
        else:
            continue
        for name in names:
            top = name.split(".")[0]
            if top in STDLIB or top in LOCAL or top == "__future__":
                continue
            found.setdefault(top, set()).add(path.name)

for mod in sorted(found):
    print(f"{mod} -> {', '.join(sorted(found[mod]))}")
