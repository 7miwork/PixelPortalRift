# 2D Minecraft - Dimensional Adventure

## Overview
A 2D Minecraft-like game built with Python and Pygame featuring multiple dimensions, portal travel, crafting, and mobs. Players start in the Grassland and must explore through different dimensions by building and activating portals.

## Project Structure
```
├── main.py                 # Main game loop and initialization
├── utils/
│   ├── __init__.py        # Package init
│   ├── constants.py       # Game constants, dimensions, blocks, items, mobs
│   ├── asset_loader.py    # Automatic image loading and resizing
│   ├── player.py          # Player class with movement and stats
│   ├── inventory.py       # Inventory and item management
│   ├── world_gen.py       # World/terrain generation
│   ├── crafting.py        # Crafting system
│   ├── portal.py          # Portal mechanics and dimension switching
│   ├── mob.py             # Mob AI and spawning
│   └── save_system.py     # Save/load functionality
├── assets/
│   ├── blocks/            # Block textures (auto-processed)
│   ├── items/             # Item sprites (auto-processed)
│   └── mobs/              # Mob sprites (auto-processed)
└── data/
    └── saves/             # Save files
```

## How to Add Custom Images

### For Students - Easy Asset Management
1. Create your image file (PNG format recommended)
2. Drop it in the appropriate folder:
   - `assets/blocks/` for block textures (e.g., `grass.png`, `stone.png`)
   - `assets/items/` for item sprites (e.g., `sword.png`, `apple.png`)
   - `assets/mobs/` for mob sprites (e.g., `slime.png`, `zombie.png`)
3. Name the file exactly as the block/item/mob is defined in `constants.py`
4. The game automatically resizes images to the correct pixel size!

Example: To add a custom grass texture, save your image as `assets/blocks/grass.png`

## Game Features

### Dimensions (5 worlds to explore)
1. **Grassland** - Starting world with trees, grass, and basic ores
2. **Stone World** - Underground caves with iron and gold
3. **Water World** - Underwater environment with coral and pearls
4. **Gem World** - Crystal caves with diamonds and rubies
5. **Nuclear World** - Dangerous radioactive zone

### Portal System
- Build a portal frame (3 blocks wide, 4 blocks tall) using `portal_frame` blocks
- Craft the required key for the next dimension
- Click on the portal frame to activate it
- Walk into the activated portal to travel

### Portal Keys Required
- Stone World: `stone_key` (8 cobblestone + 1 iron ingot)
- Water World: `water_key` (4 pearls + 2 crystal shards)
- Gem World: `gem_key` (2 ruby + 2 emerald + 2 amethyst)
- Nuclear World: `nuclear_key` (4 uranium + 4 lead + 1 reactor core)

### Controls
- **A/D** or **Arrow Keys** - Move left/right
- **Space/W/Up** - Jump
- **Left Click** - Break blocks / Interact
- **Right Click** - Place blocks / Use items / Attack
- **E** - Open/Close inventory
- **C** - Open/Close crafting menu
- **1-9** - Select hotbar slot
- **Mouse Wheel** - Scroll selection
- **F5** - Save game
- **F9** - Load game
- **ESC** - Pause/Close menus
- **H** - Show help

## Extending the Game

### Adding New Blocks
1. Open `utils/constants.py`
2. Add to `BLOCK_PROPERTIES`:
```python
"my_block": {"solid": True, "hardness": 3, "tool": "pickaxe", "drop": "my_block", "color": (R, G, B)}
```
3. Optionally add an image to `assets/blocks/my_block.png`

### Adding New Items
1. Open `utils/constants.py`
2. Add to `ITEM_PROPERTIES`:
```python
"my_item": {"stackable": True, "max_stack": 64, "type": "material"}
```

### Adding New Mobs
1. Open `utils/constants.py`
2. Add to `MOB_PROPERTIES`:
```python
"my_mob": {"health": 20, "damage": 3, "speed": 1, "drop": "item_name", "color": (R, G, B), "size": (24, 32)}
```
3. Add the mob type to a dimension's "mobs" list

### Adding New Dimensions
1. Open `utils/constants.py`
2. Add to `DIMENSIONS`:
```python
"my_dimension": {
    "name": "My Dimension",
    "color": (R, G, B),
    "sky_color": (R, G, B),
    "ground_level": 50,
    "blocks": ["block1", "block2"],
    "mobs": ["mob1", "mob2"],
    "portal_activator": "my_key",
    "next_dimension": "next_dim_name"
}
```

## Dimensional Rift (3D Transition)
When all 5 dimensions are explored, a Dimensional Rift event triggers, preparing for the transition to 3D mode (coming in future update).

## Recent Changes
- Initial game creation with all core systems
- 5 dimensions with unique blocks, mobs, and atmospheres
- Portal system with key-based activation
- Crafting system with 25+ recipes
- Save/load system
- Automatic asset loading with image resizing

## Dependencies
- pygame
- pillow (PIL)
