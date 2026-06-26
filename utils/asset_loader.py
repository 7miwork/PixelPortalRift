import pygame
import os
from PIL import Image
from utils.constants import TILE_SIZE, BLOCK_PROPERTIES, ITEM_PROPERTIES, MOB_PROPERTIES

class AssetLoader:
    def __init__(self):
        self.block_textures = {}
        self.item_textures = {}
        self.mob_textures = {}
        self.player_texture = None
        self.assets_path = "assets"
        
    def load_all_assets(self):
        self.load_block_textures()
        self.load_item_textures()
        self.load_mob_textures()
        self.load_player_texture()
        
    def resize_image(self, image_path, target_size):
        try:
            img = Image.open(image_path)
            img = img.convert("RGBA")
            img = img.resize(target_size, Image.Resampling.LANCZOS)
            mode = img.mode
            size = img.size
            data = img.tobytes()
            return pygame.image.fromstring(data, size, mode)
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            return None
    
    def create_colored_surface(self, color, size=(TILE_SIZE, TILE_SIZE)):
        surface = pygame.Surface(size, pygame.SRCALPHA)
        if len(color) == 4:
            surface.fill(color)
        else:
            surface.fill((*color, 255))
        return surface
    
    def create_block_texture(self, block_name, color):
        surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        if len(color) == 4:
            surface.fill(color)
        else:
            surface.fill((*color, 255))
        
        border_color = tuple(max(0, c - 30) for c in color[:3])
        pygame.draw.rect(surface, border_color, (0, 0, TILE_SIZE, TILE_SIZE), 1)
        
        if block_name == "crystal":
            pygame.draw.line(surface, (255, 255, 255), (8, 0), (16, TILE_SIZE), 2)
            pygame.draw.line(surface, (255, 255, 255), (24, 0), (16, TILE_SIZE), 2)
            pygame.draw.line(surface, (200, 200, 255), (16, 8), (8, 24), 2)
        elif block_name == "uranium":
            pygame.draw.circle(surface, (0, 100, 0), (TILE_SIZE//2, TILE_SIZE//2), 6)
            pygame.draw.circle(surface, (0, 255, 0), (TILE_SIZE//2, TILE_SIZE//2), 3)
        elif block_name == "plutonium":
            pygame.draw.circle(surface, (100, 50, 150), (TILE_SIZE//2, TILE_SIZE//2), 7)
            pygame.draw.circle(surface, (200, 150, 255), (TILE_SIZE//2, TILE_SIZE//2), 4)
        elif block_name == "reactor_core":
            pygame.draw.circle(surface, (255, 255, 200), (TILE_SIZE//2, TILE_SIZE//2), 10)
            pygame.draw.circle(surface, (255, 255, 100), (TILE_SIZE//2, TILE_SIZE//2), 6)
            pygame.draw.circle(surface, (255, 255, 0), (TILE_SIZE//2, TILE_SIZE//2), 3)
        elif block_name == "contaminated_stone":
            pygame.draw.circle(surface, (50, 100, 50), (8, 8), 2)
            pygame.draw.circle(surface, (50, 100, 50), (24, 16), 2)
            pygame.draw.circle(surface, (50, 150, 50), (16, 24), 2)
        elif block_name == "obsidian":
            pygame.draw.circle(surface, (100, 50, 200), (TILE_SIZE//2, TILE_SIZE//2), 5)
        elif block_name == "pearl_ore":
            pygame.draw.circle(surface, (255, 220, 240), (TILE_SIZE//2, TILE_SIZE//2), 4)
        elif block_name == "amethyst":
            pygame.draw.polygon(surface, (200, 150, 255), [(16, 4), (24, 16), (16, 28), (8, 16)])
        elif block_name == "ruby_ore":
            pygame.draw.polygon(surface, (255, 50, 100), [(16, 4), (24, 16), (16, 28), (8, 16)])
        elif block_name == "emerald_ore":
            pygame.draw.polygon(surface, (50, 255, 100), [(16, 4), (24, 16), (16, 28), (8, 16)])
        elif block_name == "diamond_ore":
            pygame.draw.polygon(surface, (200, 240, 255), [(16, 4), (28, 16), (16, 28), (4, 16)])
        elif block_name == "coral":
            pygame.draw.line(surface, (255, 100, 50), (8, TILE_SIZE), (8, 8), 3)
            pygame.draw.line(surface, (255, 100, 50), (16, TILE_SIZE), (16, 12), 4)
            pygame.draw.line(surface, (255, 100, 50), (24, TILE_SIZE), (24, 10), 3)
        elif block_name == "clay":
            pygame.draw.circle(surface, (100, 80, 60), (12, 12), 2)
            pygame.draw.circle(surface, (100, 80, 60), (24, 20), 2)
        elif block_name == "gravel":
            for i in range(5):
                x = 4 + (i * 7)
                y = 8 + ((i * 11) % 16)
                pygame.draw.circle(surface, (120, 120, 120), (x, y), 2)
        elif block_name == "driftwood":
            pygame.draw.line(surface, (100, 60, 20), (4, 16), (28, 16), 4)
            pygame.draw.line(surface, (80, 50, 15), (12, 12), (12, 20), 2)
        elif block_name == "shell":
            pygame.draw.arc(surface, (255, 250, 240), (8, 8, 16, 16), 0, 3.14, 2)
            pygame.draw.line(surface, (200, 200, 200), (16, 8), (16, 24), 1)
        elif block_name == "anchor_piece":
            pygame.draw.circle(surface, (150, 150, 150), (16, 8), 4)
            pygame.draw.line(surface, (150, 150, 150), (16, 12), (16, 28), 3)
        elif block_name == "ship_plank":
            pygame.draw.line(surface, (120, 80, 40), (0, 8), (TILE_SIZE, 8), 1)
            pygame.draw.line(surface, (120, 80, 40), (0, 16), (TILE_SIZE, 16), 1)
            pygame.draw.line(surface, (80, 50, 20), (8, 0), (8, TILE_SIZE), 1)
        elif block_name == "rope":
            for i in range(0, TILE_SIZE, 4):
                pygame.draw.line(surface, (200, 180, 150), (i % 8 + 8, i), (i % 8 + 12, i + 2), 2)
        elif block_name == "leaves":
            for x in range(4, TILE_SIZE - 4, 6):
                for y in range(4, TILE_SIZE - 4, 6):
                    pygame.draw.circle(surface, (0, 100, 0), (x, y), 2)
        elif block_name == "seaweed":
            for i in range(4, TILE_SIZE - 4, 6):
                pygame.draw.line(surface, (0, 120, 0), (i, TILE_SIZE), (i + 2, 8), 2)
        elif block_name == "torch":
            pygame.draw.rect(surface, (139, 90, 43), (14, 16, 4, 12))
            pygame.draw.circle(surface, (255, 200, 0), (16, 12), 4)
            pygame.draw.circle(surface, (255, 100, 0), (16, 12), 2)
        elif block_name == "nuclear_waste":
            pygame.draw.circle(surface, (150, 255, 0), (TILE_SIZE//2, TILE_SIZE//2), 5)
            pygame.draw.circle(surface, (100, 200, 0), (TILE_SIZE//2, TILE_SIZE//2), 3)
        elif block_name == "thorium":
            pygame.draw.circle(surface, (100, 100, 200), (TILE_SIZE//2, TILE_SIZE//2), 6)
            pygame.draw.circle(surface, (150, 150, 255), (TILE_SIZE//2, TILE_SIZE//2), 3)
        elif block_name == "radium":
            pygame.draw.circle(surface, (200, 50, 50), (TILE_SIZE//2, TILE_SIZE//2), 6)
            pygame.draw.circle(surface, (255, 100, 100), (TILE_SIZE//2, TILE_SIZE//2), 3)
        elif block_name == "radioactive_crystal":
            pygame.draw.polygon(surface, (150, 255, 150), [(16, 2), (28, 16), (16, 30), (4, 16)])
            pygame.draw.polygon(surface, (200, 255, 200), [(16, 6), (24, 16), (16, 26), (8, 16)])
        elif block_name == "coal_ore":
            for i in range(3):
                x = 8 + (i * 8)
                y = 8 + ((i * 7) % 16)
                pygame.draw.circle(surface, (30, 30, 30), (x, y), 3)
        elif block_name == "iron_ore":
            for i in range(3):
                x = 8 + (i * 8)
                y = 8 + ((i * 7) % 16)
                pygame.draw.circle(surface, (180, 140, 100), (x, y), 3)
        elif block_name == "gold_ore":
            for i in range(3):
                x = 8 + (i * 8)
                y = 8 + ((i * 7) % 16)
                pygame.draw.circle(surface, (255, 215, 0), (x, y), 3)
        elif block_name == "gem":
            pygame.draw.polygon(surface, color, [(16, 4), (24, 16), (16, 28), (8, 16)])
        elif "ore" in block_name and block_name not in ["coal_ore", "iron_ore", "gold_ore", "pearl_ore", "ruby_ore", "emerald_ore", "diamond_ore"]:
            for i in range(3):
                x = 8 + (i * 8)
                y = 8 + ((i * 7) % 16)
                pygame.draw.circle(surface, (200, 200, 200), (x, y), 3)
        elif block_name == "grass":
            for i in range(0, TILE_SIZE, 4):
                pygame.draw.line(surface, (0, 100, 0), (i, 0), (i + 2, 4), 1)
        elif block_name == "leaves":
            for x in range(4, TILE_SIZE - 4, 8):
                for y in range(4, TILE_SIZE - 4, 8):
                    pygame.draw.circle(surface, (0, 100, 0), (x, y), 2)
        elif "ore" in block_name:
            ore_color = (200, 200, 200) if "coal" in block_name else color
            for i in range(3):
                x = 8 + (i * 8)
                y = 8 + ((i * 7) % 16)
                pygame.draw.circle(surface, ore_color, (x, y), 3)
        elif block_name == "wood":
            for i in range(4, TILE_SIZE, 8):
                pygame.draw.line(surface, (100, 60, 20), (0, i), (TILE_SIZE, i), 1)
        elif block_name == "portal":
            for i in range(0, TILE_SIZE, 4):
                alpha = 100 + (i * 4) % 100
                pygame.draw.rect(surface, (*color[:3], alpha), (i, 0, 2, TILE_SIZE))
        elif block_name.startswith("portal_frame"):
            props = BLOCK_PROPERTIES.get(block_name, {})
            color = props.get("color", (100, 0, 150))
            border = tuple(max(0, c - 40) for c in color[:3])
            pygame.draw.rect(surface, color, (2, 2, TILE_SIZE-4, TILE_SIZE-4))
            pygame.draw.rect(surface, border, (4, 4, TILE_SIZE-8, TILE_SIZE-8))
        elif block_name == "water":
            for i in range(0, TILE_SIZE, 6):
                wave_offset = (i % 12) - 6
                pygame.draw.arc(surface, (100, 150, 255), (wave_offset, i, 20, 8), 0, 3.14, 1)
        
        return surface
    
    def create_item_texture(self, item_name):
        surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        
        if item_name == "sapphire":
            pygame.draw.polygon(surface, (30, 100, 255), [(16, 2), (28, 16), (16, 30), (4, 16)])
            pygame.draw.polygon(surface, (100, 150, 255), [(16, 6), (24, 16), (16, 26), (8, 16)])
        elif item_name == "topaz":
            pygame.draw.polygon(surface, (255, 150, 0), [(16, 2), (28, 16), (16, 30), (4, 16)])
            pygame.draw.polygon(surface, (255, 200, 50), [(16, 6), (24, 16), (16, 26), (8, 16)])
        elif item_name == "opal":
            pygame.draw.polygon(surface, (200, 200, 255), [(16, 2), (28, 16), (16, 30), (4, 16)])
            pygame.draw.polygon(surface, (255, 255, 255), [(16, 6), (24, 16), (16, 26), (8, 16)])
        elif item_name == "thorium":
            pygame.draw.circle(surface, (100, 100, 200), (TILE_SIZE//2, TILE_SIZE//2), 8)
            pygame.draw.circle(surface, (150, 150, 255), (TILE_SIZE//2, TILE_SIZE//2), 4)
        elif item_name == "radium":
            pygame.draw.circle(surface, (200, 50, 50), (TILE_SIZE//2, TILE_SIZE//2), 8)
            pygame.draw.circle(surface, (255, 100, 100), (TILE_SIZE//2, TILE_SIZE//2), 4)
            pygame.draw.circle(surface, (255, 200, 200), (TILE_SIZE//2 - 2, TILE_SIZE//2 - 2), 2)
        elif item_name == "enriched_uranium":
            pygame.draw.circle(surface, (0, 150, 0), (TILE_SIZE//2, TILE_SIZE//2), 8)
            pygame.draw.circle(surface, (0, 255, 0), (TILE_SIZE//2, TILE_SIZE//2), 4)
            pygame.draw.circle(surface, (150, 255, 150), (TILE_SIZE//2, TILE_SIZE//2), 2)
        elif item_name == "radioactive_crystal":
            pygame.draw.polygon(surface, (100, 200, 100), [(16, 2), (28, 16), (16, 30), (4, 16)])
            pygame.draw.polygon(surface, (150, 255, 150), [(16, 6), (24, 16), (16, 26), (8, 16)])
        elif item_name == "driftwood":
            pygame.draw.line(surface, (100, 60, 20), (4, 16), (28, 16), 5)
        elif item_name == "shell":
            pygame.draw.arc(surface, (255, 250, 240), (4, 4, 24, 24), 0, 3.14, 3)
        elif item_name == "anchor_piece":
            pygame.draw.circle(surface, (150, 150, 150), (16, 8), 5)
            pygame.draw.line(surface, (150, 150, 150), (16, 13), (16, 28), 4)
        elif item_name == "ship_plank":
            pygame.draw.rect(surface, (140, 100, 60), (4, 4, 24, 24))
            pygame.draw.line(surface, (100, 60, 30), (4, 12), (28, 12), 1)
            pygame.draw.line(surface, (100, 60, 30), (4, 20), (28, 20), 1)
        elif item_name == "rope":
            for i in range(0, TILE_SIZE, 4):
                pygame.draw.line(surface, (200, 180, 150), (i % 8 + 6, i), (i % 8 + 14, i), 3)
        elif item_name == "raw_fish":
            pygame.draw.ellipse(surface, (200, 150, 50), (4, 12, 24, 10))
            pygame.draw.polygon(surface, (200, 150, 50), [(28, 17), (32, 12), (32, 22)])
        elif "pickaxe" in item_name:
            color = (139, 90, 43) if "wooden" in item_name else (128, 128, 128) if "stone" in item_name else (200, 200, 200)
            pygame.draw.line(surface, (100, 60, 20), (16, 28), (16, 12), 3)
            pygame.draw.polygon(surface, color, [(8, 4), (24, 4), (24, 12), (8, 12)])
        elif "axe" in item_name:
            color = (139, 90, 43) if "wooden" in item_name else (128, 128, 128) if "stone" in item_name else (200, 200, 200)
            pygame.draw.line(surface, (100, 60, 20), (16, 28), (16, 12), 3)
            pygame.draw.polygon(surface, color, [(10, 4), (22, 4), (26, 12), (6, 12)])
        elif "shovel" in item_name:
            color = (139, 90, 43) if "wooden" in item_name else (128, 128, 128) if "stone" in item_name else (200, 200, 200)
            pygame.draw.line(surface, (100, 60, 20), (16, 28), (16, 10), 3)
            pygame.draw.ellipse(surface, color, (10, 2, 12, 12))
        elif "sword" in item_name:
            color = (139, 90, 43) if "wooden" in item_name else (128, 128, 128) if "stone" in item_name else (200, 200, 200)
            pygame.draw.line(surface, (100, 60, 20), (16, 28), (16, 20), 4)
            pygame.draw.polygon(surface, color, [(14, 20), (18, 20), (18, 4), (16, 2), (14, 4)])
        elif "key" in item_name:
            key_color = (128, 128, 128) if "stone" in item_name else (0, 100, 200) if "water" in item_name else (200, 0, 200) if "gem" in item_name else (0, 255, 0)
            pygame.draw.circle(surface, key_color, (16, 10), 8)
            pygame.draw.circle(surface, (0, 0, 0), (16, 10), 4)
            pygame.draw.rect(surface, key_color, (14, 16, 4, 12))
            pygame.draw.rect(surface, key_color, (18, 22, 6, 3))
        elif item_name == "apple":
            pygame.draw.circle(surface, (255, 0, 0), (16, 18), 10)
            pygame.draw.line(surface, (100, 60, 20), (16, 8), (16, 4), 2)
            pygame.draw.ellipse(surface, (0, 150, 0), (17, 4, 6, 4))
        elif item_name == "healing_potion":
            pygame.draw.rect(surface, (200, 0, 0), (10, 12, 12, 16))
            pygame.draw.rect(surface, (150, 150, 150), (12, 6, 8, 8))
            pygame.draw.rect(surface, (100, 0, 0), (12, 14, 8, 4))
        elif item_name == "bread":
            pygame.draw.ellipse(surface, (210, 180, 140), (4, 12, 24, 12))
            pygame.draw.arc(surface, (180, 150, 100), (4, 12, 24, 12), 0, 3.14, 2)
        else:
            if item_name in BLOCK_PROPERTIES and BLOCK_PROPERTIES[item_name]["color"]:
                pygame.draw.rect(surface, BLOCK_PROPERTIES[item_name]["color"], (4, 4, 24, 24))
            else:
                pygame.draw.rect(surface, (150, 150, 150), (4, 4, 24, 24))
        
        return surface
    
    def create_mob_texture(self, mob_name, properties):
        size = properties.get("size", (24, 24))
        color = properties.get("color", (255, 0, 0))
        surface = pygame.Surface(size, pygame.SRCALPHA)
        
        if "slime" in mob_name:
            pygame.draw.ellipse(surface, color, (0, 0, size[0], size[1]))
            pygame.draw.ellipse(surface, (255, 255, 255), (size[0]//4, size[1]//4, 4, 4))
            pygame.draw.ellipse(surface, (255, 255, 255), (size[0]//2, size[1]//4, 4, 4))
        elif "zombie" in mob_name or "mutant" in mob_name:
            pygame.draw.rect(surface, color, (size[0]//4, 0, size[0]//2, size[1]//3))
            pygame.draw.rect(surface, color, (size[0]//4, size[1]//3, size[0]//2, size[1]//2))
            pygame.draw.rect(surface, color, (size[0]//4 - 4, size[1]//3, 4, size[1]//3))
            pygame.draw.rect(surface, color, (size[0]//4 + size[0]//2, size[1]//3, 4, size[1]//3))
            pygame.draw.rect(surface, (0, 0, 0), (size[0]//3, size[1]//8, 3, 3))
            pygame.draw.rect(surface, (0, 0, 0), (size[0]//2, size[1]//8, 3, 3))
        elif "golem" in mob_name:
            pygame.draw.rect(surface, color, (size[0]//4, 0, size[0]//2, size[1]//2))
            pygame.draw.rect(surface, color, (0, size[1]//4, size[0], size[1]//2))
            pygame.draw.rect(surface, (50, 50, 50), (size[0]//3, size[1]//6, 4, 4))
            pygame.draw.rect(surface, (50, 50, 50), (size[0]//2, size[1]//6, 4, 4))
        elif "bat" in mob_name:
            pygame.draw.ellipse(surface, color, (size[0]//4, size[1]//4, size[0]//2, size[1]//2))
            pygame.draw.polygon(surface, color, [(0, size[1]//2), (size[0]//4, 0), (size[0]//4, size[1])])
            pygame.draw.polygon(surface, color, [(size[0], size[1]//2), (size[0]*3//4, 0), (size[0]*3//4, size[1])])
        elif "fish" in mob_name:
            pygame.draw.ellipse(surface, color, (0, size[1]//4, size[0]*3//4, size[1]//2))
            pygame.draw.polygon(surface, color, [(size[0]*3//4, size[1]//2), (size[0], 0), (size[0], size[1])])
            pygame.draw.circle(surface, (0, 0, 0), (size[0]//4, size[1]//2), 2)
        elif "shark" in mob_name:
            pygame.draw.ellipse(surface, color, (0, size[1]//4, size[0]*4//5, size[1]//2))
            pygame.draw.polygon(surface, color, [(size[0]*3//4, size[1]//2), (size[0], size[1]//4), (size[0], size[1]*3//4)])
            pygame.draw.polygon(surface, color, [(size[0]//2, size[1]//4), (size[0]//2 + 4, 0), (size[0]//2 + 8, size[1]//4)])
            pygame.draw.circle(surface, (0, 0, 0), (size[0]//5, size[1]//2), 2)
        elif "spider" in mob_name:
            pygame.draw.ellipse(surface, color, (size[0]//4, size[1]//4, size[0]//2, size[1]//2))
            for i in range(4):
                y = size[1]//2
                pygame.draw.line(surface, color, (size[0]//2, y), (0, i * 4), 2)
                pygame.draw.line(surface, color, (size[0]//2, y), (size[0], i * 4), 2)
            pygame.draw.circle(surface, (0, 0, 0), (size[0]//3, size[1]//2), 2)
            pygame.draw.circle(surface, (0, 0, 0), (size[0]*2//3, size[1]//2), 2)
        else:
            pygame.draw.rect(surface, color, (0, 0, size[0], size[1]))
        
        return surface
    
    def create_player_texture(self):
        surface = pygame.Surface((24, 32), pygame.SRCALPHA)
        pygame.draw.rect(surface, (255, 200, 150), (6, 0, 12, 10))
        pygame.draw.rect(surface, (0, 0, 255), (4, 10, 16, 14))
        pygame.draw.rect(surface, (0, 0, 200), (0, 12, 4, 10))
        pygame.draw.rect(surface, (0, 0, 200), (20, 12, 4, 10))
        pygame.draw.rect(surface, (50, 50, 150), (6, 24, 5, 8))
        pygame.draw.rect(surface, (50, 50, 150), (13, 24, 5, 8))
        pygame.draw.rect(surface, (0, 0, 0), (8, 3, 2, 2))
        pygame.draw.rect(surface, (0, 0, 0), (14, 3, 2, 2))
        pygame.draw.rect(surface, (139, 90, 43), (4, 0, 16, 3))
        return surface
    
    def load_block_textures(self):
        blocks_path = os.path.join(self.assets_path, "blocks")
        
        for block_name, props in BLOCK_PROPERTIES.items():
            image_path = os.path.join(blocks_path, f"{block_name}.png")
            
            if os.path.exists(image_path):
                texture = self.resize_image(image_path, (TILE_SIZE, TILE_SIZE))
                if texture:
                    self.block_textures[block_name] = texture
                    continue
            
            if props["color"]:
                self.block_textures[block_name] = self.create_block_texture(block_name, props["color"])
    
    def load_item_textures(self):
        items_path = os.path.join(self.assets_path, "items")
        
        for item_name in ITEM_PROPERTIES.keys():
            image_path = os.path.join(items_path, f"{item_name}.png")
            
            if os.path.exists(image_path):
                texture = self.resize_image(image_path, (TILE_SIZE, TILE_SIZE))
                if texture:
                    self.item_textures[item_name] = texture
                    continue
            
            self.item_textures[item_name] = self.create_item_texture(item_name)
    
    def load_mob_textures(self):
        mobs_path = os.path.join(self.assets_path, "mobs")
        
        for mob_name, props in MOB_PROPERTIES.items():
            image_path = os.path.join(mobs_path, f"{mob_name}.png")
            
            if os.path.exists(image_path):
                texture = self.resize_image(image_path, props["size"])
                if texture:
                    self.mob_textures[mob_name] = texture
                    continue
            
            self.mob_textures[mob_name] = self.create_mob_texture(mob_name, props)
    
    def load_player_texture(self):
        player_path = os.path.join(self.assets_path, "player.png")
        
        if os.path.exists(player_path):
            texture = self.resize_image(player_path, (24, 32))
            if texture:
                self.player_texture = texture
                return
        
        self.player_texture = self.create_player_texture()
    
    def get_block_texture(self, block_name):
        return self.block_textures.get(block_name)
    
    def get_item_texture(self, item_name):
        if item_name in self.item_textures:
            return self.item_textures[item_name]
        if item_name in self.block_textures:
            return self.block_textures[item_name]
        return self.create_item_texture(item_name)
    
    def get_mob_texture(self, mob_name):
        return self.mob_textures.get(mob_name)
    
    def get_player_texture(self):
        return self.player_texture
