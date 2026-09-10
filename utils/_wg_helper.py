#!/usr/bin/env python3
"""Helper script to rewrite world_gen.py with 3D content."""
from pathlib import Path

WORLD_GEN_PATH = Path(__file__).parent / "world_gen.py"

NEW_CONTENT = r"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
utils/world_gen.py - 3D-Voxelwelt-Generierung
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Diese Datei enthalt die 3D-Weltgenerierung fur das Voxel-Spiel.
Die Klasse World erzeugt und verwaltet eine voxelbasierte 3D-Welt
mit Chunks (CHUNK_SIZE x CHUNK_SIZE x CHUNK_HEIGHT Blocke).

Block-Eigenschaften kommen aus BLOCK_PROPERTIES in constants.py.
"""

# We'll append to this in subsequent calls
print("Helper loaded")

