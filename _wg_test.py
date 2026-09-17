import sys
from pathlib import Path
p = Path(r"Z:\Codes\Unterricht\Nic Dragomir\Spiele\PixelPortalRift-main")
sys.path.insert(0, str(p))
from utils.world_gen import World
w = World("grassland", seed=42, skip_generation=True)
print("World created")
print("Spawn point", w.spawn_point)
print("Blocks count", len(w.blocks))
print("Generated chunks", len(w.generated_chunks))
print("Width", w.width, "Depth", w.depth, "Height", w.height)
