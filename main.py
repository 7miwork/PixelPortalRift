import pygame
import sys
import os

os.environ['SDL_AUDIODRIVER'] = 'dummy'

from utils.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TILE_SIZE,
    DIMENSIONS, BLOCK_PROPERTIES, ITEM_PROPERTIES, MAX_INTERACTION_RANGE
)
from utils.asset_loader import AssetLoader
from utils.player import Player
from utils.inventory import Inventory
from utils.world_gen import World
from utils.crafting import CraftingSystem
from utils.portal import PortalSystem, DimensionalRift
from utils.mob import MobManager
from utils.save_system import SaveSystem

class Game:
    def __init__(self):
        pygame.init()
        pygame.key.set_repeat(0)
        pygame.display.set_caption("2D Minecraft - Dimensional Adventure")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.asset_loader = AssetLoader()
        self.asset_loader.load_all_assets()
        
        self.save_system = SaveSystem()
        
        self.current_dimension = "grassland"
        self.visited_dimensions = {"grassland"}
        
        self.world = World(self.current_dimension)
        self.inventory = Inventory()
        self.player = Player(
            self.world.spawn_point[0],
            self.world.spawn_point[1],
            self.asset_loader
        )
        self.crafting = CraftingSystem()
        self.portal_system = PortalSystem()
        self.dimensional_rift = DimensionalRift()
        self.mob_manager = MobManager(self.asset_loader)
        
        self.give_starter_items()
        
        self.game_state = "playing"
        self.paused = False
        self.show_help = False
        self.message = ""
        self.message_timer = 0
        
        self.break_progress = 0
        self.breaking_block = None
        self.break_target = None
        
        self.keys_held = {
            "left": False,
            "right": False
        }
        self.jump_key_was_pressed = False
    
    def give_starter_items(self):
        self.inventory.add_item("wooden_pickaxe", 1)
        self.inventory.add_item("wooden_axe", 1)
        self.inventory.add_item("wooden_sword", 1)
        self.inventory.add_item("apple", 5)
        self.inventory.add_item("wood", 10)
    
    def show_message(self, text, duration=3000):
        self.message = text
        self.message_timer = duration
    
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS)
            
            self.handle_events()
            
            if not self.paused and self.game_state == "playing":
                self.update(dt)
            
            self.draw()
            
            pygame.display.flip()
        
        pygame.quit()
        sys.exit()
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                self.handle_keydown(event)
            
            elif event.type == pygame.KEYUP:
                self.handle_keyup(event)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_mouse_click(event)
            
            elif event.type == pygame.MOUSEWHEEL:
                if self.crafting.is_open:
                    self.crafting.scroll(-event.y)
                else:
                    self.inventory.scroll_selection(-event.y)
    
    def handle_keydown(self, event):
        if event.key == pygame.K_ESCAPE:
            if self.crafting.is_open:
                self.crafting.is_open = False
            elif self.inventory.is_open:
                self.inventory.is_open = False
            else:
                self.paused = not self.paused
        
        elif event.key == pygame.K_a or event.key == pygame.K_LEFT:
            self.keys_held["left"] = True
        elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
            self.keys_held["right"] = True
        
        elif event.key == pygame.K_e:
            self.inventory.toggle_open()
            if self.inventory.is_open:
                self.crafting.is_open = False
        
        elif event.key == pygame.K_c:
            self.crafting.toggle_open(self.inventory)
            if self.crafting.is_open:
                self.inventory.is_open = False
        
        elif event.key == pygame.K_h:
            self.show_help = not self.show_help
        
        elif event.key == pygame.K_F5:
            success, msg = self.save_system.save_game(self.get_game_state())
            self.show_message(msg)
        
        elif event.key == pygame.K_F9:
            self.load_game()
        
        elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5,
                          pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9]:
            slot = event.key - pygame.K_1
            self.inventory.select_slot(slot)
    
    def handle_keyup(self, event):
        if event.key == pygame.K_a or event.key == pygame.K_LEFT:
            self.keys_held["left"] = False
        elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
            self.keys_held["right"] = False
        if not self.keys_held["left"] and not self.keys_held["right"]:
            self.player.move("stop")
    
    def is_within_range(self, world_x, world_y):
        """Prueft, ob der Block innerhalb der maximalen Interaktions-Reichweite liegt."""
        player_tiles = [
            (int(self.player.x // TILE_SIZE), int(self.player.y // TILE_SIZE)),
            (int((self.player.x + self.player.width) // TILE_SIZE), int(self.player.y // TILE_SIZE)),
            (int(self.player.x // TILE_SIZE), int((self.player.y + self.player.height) // TILE_SIZE)),
            (int((self.player.x + self.player.width) // TILE_SIZE), int((self.player.y + self.player.height) // TILE_SIZE))
        ]
        
        min_dx = min(abs(world_x - px) for px, _ in player_tiles)
        min_dy = min(abs(world_y - py) for _, py in player_tiles)
        distance = (min_dx ** 2 + min_dy ** 2) ** 0.5
        return distance <= MAX_INTERACTION_RANGE
    
    def handle_mouse_click(self, event):
        if self.crafting.is_open:
            if self.crafting.handle_click(event.pos, self.inventory):
                self.show_message("Item crafted!")
            return
        
        if self.inventory.is_open:
            return
        
        mouse_x, mouse_y = event.pos
        camera_x, camera_y = self.player.get_camera_offset()
        world_x = (mouse_x + camera_x) // TILE_SIZE
        world_y = (mouse_y + camera_y) // TILE_SIZE
        
        if event.button == 1:
            if not self.is_within_range(world_x, world_y):
                self.show_message("Too far away!")
                return
            
            block = self.world.get_block(world_x, world_y)
            if block and block != "air":
                if block == "portal":
                    target = self.portal_system.check_player_portal(self.player.get_rect(), self.world)
                    if target:
                        self.travel_to_dimension(target)
                elif block.startswith("portal_frame"):
                    portal_struct = self.portal_system.find_portal_at(
                        self.world, world_x, world_y, self.current_dimension
                    )
                    if portal_struct:
                        x, y, w, h = portal_struct
                        success, msg = self.portal_system.activate_portal(
                            self.world, x, y, w, h,
                            self.current_dimension, self.inventory
                        )
                        self.show_message(msg)
                    else:
                        self.show_message("Portal structure incomplete!")
                else:
                    drop = self.world.break_block(world_x, world_y)
                    if drop:
                        remaining = self.inventory.add_item(drop)
                        if remaining == 0:
                            self.show_message(f"Got {drop}!")
                        else:
                            self.show_message("Inventory full!")
        
        elif event.button == 3:
            selected_item = self.inventory.get_selected_item()
            if selected_item:
                props = ITEM_PROPERTIES.get(selected_item, {})
                
                if props.get("type") == "block":
                    if not self.is_within_range(world_x, world_y):
                        self.show_message("Too far away!")
                        return
                    
                    current_block = self.world.get_block(world_x, world_y)
                    if current_block == "air" or current_block is None:
                        player_tiles = [
                            (int(self.player.x // TILE_SIZE), int(self.player.y // TILE_SIZE)),
                            (int((self.player.x + self.player.width) // TILE_SIZE), int(self.player.y // TILE_SIZE)),
                            (int(self.player.x // TILE_SIZE), int((self.player.y + self.player.height) // TILE_SIZE)),
                            (int((self.player.x + self.player.width) // TILE_SIZE), int((self.player.y + self.player.height) // TILE_SIZE))
                        ]
                        
                        if (world_x, world_y) not in player_tiles:
                            if selected_item in BLOCK_PROPERTIES:
                                if self.world.set_block(world_x, world_y, selected_item):
                                    self.inventory.use_selected_item()
                            else:
                                block_name = selected_item
                                if self.world.set_block(world_x, world_y, block_name):
                                    self.inventory.use_selected_item()
                
                elif props.get("type") == "food":
                    heal = props.get("heal", 0)
                    hunger = props.get("hunger", 0)
                    self.player.eat(hunger, heal)
                    self.inventory.use_selected_item()
                    self.show_message(f"Ate {selected_item}!")
                
                elif props.get("type") == "healing":
                    heal = props.get("heal", 0)
                    self.player.heal(heal)
                    self.inventory.use_selected_item()
                    self.show_message(f"Used {selected_item}!")
                
                elif props.get("type") == "weapon":
                    attack_rect = pygame.Rect(
                        self.player.x - 30 if not self.player.facing_right else self.player.x + self.player.width,
                        self.player.y,
                        40,
                        self.player.height
                    )
                    damage = props.get("damage", 1)
                    hits = self.mob_manager.check_attack(attack_rect, damage)
                    if hits:
                        self.inventory.use_selected_item()
                        for mob in hits:
                            if not mob.is_alive():
                                drop = mob.get_drop()
                                if drop:
                                    self.inventory.add_item(drop)
                                    self.show_message(f"Got {drop}!")
    
    def update(self, dt):
        if self.keys_held["left"]:
            self.player.move("left")
        elif self.keys_held["right"]:
            self.player.move("right")
        
        # -------- SPRUNG (Rising-Edge-Erkennung, entkoppelt vom Event-System) --------
        jump_now = (
            pygame.key.get_pressed()[pygame.K_SPACE] or
            pygame.key.get_pressed()[pygame.K_w] or
            pygame.key.get_pressed()[pygame.K_UP]
        )
        if jump_now and not self.jump_key_was_pressed:
            if self.player.on_ground and not self.player.is_jumping:
                self.player.jump()
        self.jump_key_was_pressed = jump_now
        
        self.player.update(self.world, dt)
        self.portal_system.update(dt)
        self.mob_manager.update(self.world, self.player, dt)
        
        target = self.portal_system.check_player_portal(self.player.get_rect(), self.world)
        if target and target != self.current_dimension:
            self.travel_to_dimension(target)
        
        if self.message_timer > 0:
            self.message_timer -= dt
        
        if not self.player.is_alive():
            self.game_state = "game_over"
        
        if self.dimensional_rift.check_all_dimensions_complete(self.visited_dimensions):
            if self.dimensional_rift.trigger_rift():
                self.show_message("All dimensions explored! Dimensional Rift approaching!")
        
        result = self.dimensional_rift.update(dt)
        if result == "3D_WORLD":
            self.show_message("Welcome to the 3D world! (Coming soon...)")
            self.dimensional_rift.is_active = False
    
    def travel_to_dimension(self, target_dimension):
        if target_dimension == "dimensional_rift":
            if self.dimensional_rift.trigger_rift():
                self.show_message("DIMENSIONAL RIFT ACTIVATED!")
            return
        
        if target_dimension in DIMENSIONS:
            self.current_dimension = target_dimension
            self.visited_dimensions.add(target_dimension)
            self.world = World(target_dimension)
            self.player.x = self.world.spawn_point[0]
            self.player.y = self.world.spawn_point[1]
            self.player.velocity_x = 0
            self.player.velocity_y = 0
            self.mob_manager.clear_mobs()
            self.portal_system.active_portals.clear()
            self.show_message(f"Welcome to {DIMENSIONS[target_dimension]['name']}!")
    
    def get_game_state(self):
        return {
            "player": self.player,
            "inventory": self.inventory,
            "world": self.world,
            "current_dimension": self.current_dimension,
            "visited_dimensions": self.visited_dimensions,
            "portal_system": self.portal_system,
            "mob_manager": self.mob_manager
        }
    
    def load_game(self):
        save_data, msg = self.save_system.load_game()
        if save_data:
            self.current_dimension = save_data["current_dimension"]
            self.visited_dimensions = set(save_data["visited_dimensions"])
            
            self.world = World(self.current_dimension)
            self.world.load_save_data(save_data["world"])
            
            self.player.x = save_data["player"]["x"]
            self.player.y = save_data["player"]["y"]
            self.player.health = save_data["player"]["health"]
            self.player.hunger = save_data["player"]["hunger"]
            self.player.facing_right = save_data["player"]["facing_right"]
            
            self.inventory.load_save_data(save_data["inventory"])
            self.portal_system.load_save_data(save_data["portals"])
            self.mob_manager.load_save_data(save_data["mobs"])
            
            self.show_message(msg)
        else:
            self.show_message(msg)
    
    def draw(self):
        dimension_data = DIMENSIONS.get(self.current_dimension, {})
        sky_color = dimension_data.get("sky_color", (135, 206, 235))
        self.screen.fill(sky_color)
        
        camera_x, camera_y = self.player.get_camera_offset()
        
        self.draw_world(camera_x, camera_y)
        self.portal_system.draw_portal_effects(self.screen, self.world, camera_x, camera_y)
        self.mob_manager.draw(self.screen, camera_x, camera_y)
        self.player.draw(self.screen, camera_x, camera_y)
        
        self.player.draw_stats(self.screen)
        self.inventory.draw_hotbar(self.screen, self.asset_loader)
        
        self.draw_dimension_info()
        
        if self.message_timer > 0:
            self.draw_message()
        
        if self.inventory.is_open:
            self.inventory.draw_full_inventory(self.screen, self.asset_loader)
        
        if self.crafting.is_open:
            self.crafting.draw(self.screen, self.asset_loader, self.inventory)
        
        if self.paused:
            self.draw_pause_menu()
        
        if self.show_help:
            self.draw_help()
        
        if self.game_state == "game_over":
            self.draw_game_over()
        
        self.dimensional_rift.draw(self.screen)
    
    def draw_world(self, camera_x, camera_y):
        start_x = max(0, int(camera_x // TILE_SIZE) - 1)
        end_x = min(self.world.width, int((camera_x + SCREEN_WIDTH) // TILE_SIZE) + 2)
        start_y = max(0, int(camera_y // TILE_SIZE) - 1)
        end_y = min(self.world.height, int((camera_y + SCREEN_HEIGHT) // TILE_SIZE) + 2)
        
        for x in range(start_x, end_x):
            for y in range(start_y, end_y):
                block = self.world.get_block(x, y)
                if block and block != "air":
                    screen_x = x * TILE_SIZE - camera_x
                    screen_y = y * TILE_SIZE - camera_y
                    
                    texture = self.asset_loader.get_block_texture(block)
                    if texture:
                        self.screen.blit(texture, (screen_x, screen_y))
                    else:
                        props = BLOCK_PROPERTIES.get(block, {})
                        color = props.get("color", (128, 128, 128))
                        pygame.draw.rect(self.screen, color, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
    
    def draw_dimension_info(self):
        font = pygame.font.Font(None, 28)
        dim_name = DIMENSIONS.get(self.current_dimension, {}).get("name", "Unknown")
        text = font.render(f"Dimension: {dim_name}", True, (255, 255, 255))
        shadow = font.render(f"Dimension: {dim_name}", True, (0, 0, 0))
        self.screen.blit(shadow, (SCREEN_WIDTH - text.get_width() - 9, 11))
        self.screen.blit(text, (SCREEN_WIDTH - text.get_width() - 10, 10))
        
        visited_text = font.render(f"Explored: {len(self.visited_dimensions)}/5", True, (255, 255, 255))
        self.screen.blit(visited_text, (SCREEN_WIDTH - visited_text.get_width() - 10, 35))
    
    def draw_message(self):
        font = pygame.font.Font(None, 36)
        text = font.render(self.message, True, (255, 255, 255))
        shadow = font.render(self.message, True, (0, 0, 0))
        
        x = (SCREEN_WIDTH - text.get_width()) // 2
        y = SCREEN_HEIGHT // 2 - 150
        
        self.screen.blit(shadow, (x + 2, y + 2))
        self.screen.blit(text, (x, y))
    
    def draw_pause_menu(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        font = pygame.font.Font(None, 72)
        title = font.render("PAUSED", True, (255, 255, 255))
        self.screen.blit(title, ((SCREEN_WIDTH - title.get_width()) // 2, SCREEN_HEIGHT // 3))
        
        small_font = pygame.font.Font(None, 36)
        instructions = [
            "Press ESC to resume",
            "Press H for help",
            "Press F5 to save",
            "Press F9 to load"
        ]
        
        for i, text in enumerate(instructions):
            rendered = small_font.render(text, True, (200, 200, 200))
            self.screen.blit(rendered, ((SCREEN_WIDTH - rendered.get_width()) // 2, SCREEN_HEIGHT // 2 + i * 40))
    
    def draw_help(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        font = pygame.font.Font(None, 48)
        title = font.render("CONTROLS", True, (255, 255, 255))
        self.screen.blit(title, ((SCREEN_WIDTH - title.get_width()) // 2, 50))
        
        small_font = pygame.font.Font(None, 28)
        controls = [
            "A/D or Arrow Keys - Move left/right",
            "Space/W/Up - Jump",
            "Left Click - Break blocks / Interact",
            "Right Click - Place blocks / Use items / Attack",
            "E - Open/Close inventory",
            "C - Open/Close crafting menu",
            "1-9 - Select hotbar slot",
            "Mouse Wheel - Scroll selection/crafting",
            "F5 - Save game",
            "F9 - Load game",
            "ESC - Pause/Close menus",
            "H - Show/Hide this help",
            "",
            "BUILD PORTAL: Place portal_frame blocks in a 3x4 frame",
            "ACTIVATE PORTAL: Click the frame with the required key",
            "EXPLORE: Visit all 5 dimensions to trigger the Dimensional Rift!"
        ]
        
        for i, text in enumerate(controls):
            color = (255, 200, 100) if text.startswith("BUILD") or text.startswith("ACTIVATE") or text.startswith("EXPLORE") else (200, 200, 200)
            rendered = small_font.render(text, True, color)
            self.screen.blit(rendered, (100, 120 + i * 32))
    
    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((100, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        font = pygame.font.Font(None, 96)
        title = font.render("GAME OVER", True, (255, 255, 255))
        self.screen.blit(title, ((SCREEN_WIDTH - title.get_width()) // 2, SCREEN_HEIGHT // 3))
        
        small_font = pygame.font.Font(None, 36)
        text = small_font.render("Press F9 to load your last save", True, (200, 200, 200))
        self.screen.blit(text, ((SCREEN_WIDTH - text.get_width()) // 2, SCREEN_HEIGHT // 2))


if __name__ == "__main__":
    game = Game()
    game.run()