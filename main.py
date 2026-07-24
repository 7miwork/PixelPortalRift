"""
main.py – Hauptprogramm von PixelPortalRift

Dies ist die Hauptdatei des Spiels. Sie enthält die Klasse Game,
die das gesamte Spiel steuert:
- Initialisierung (Fenster, Grafik, Spieler, Welt, etc.)
- Die Game-Loop (Hauptschleife: Events → Update → Zeichnen)
- Steuerung (Tastatur, Maus)
- Dimensions-Wechsel (Reisen zwischen Welten)
- Speichern und Laden

Die Game-Loop läuft 60 Mal pro Sekunde (FPS = 60) und macht immer
dasselbe:
1. Events verarbeiten (Tastendrücke, Mausklicks)
2. Spiel-Zustand aktualisieren (Bewegung, Kollision, Gegner)
3. Alles auf den Bildschirm zeichnen

Starte das Spiel mit: python main.py
"""

import pygame
import sys
import os
import random

# Audio-Treiber auf "dummy" setzen, damit keine Sound-Fehler auftreten,
# falls keine Soundkarte vorhanden ist.
os.environ['SDL_AUDIODRIVER'] = 'dummy'

from utils.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TILE_SIZE,
    DIMENSIONS, BLOCK_PROPERTIES, ITEM_PROPERTIES, MAX_INTERACTION_RANGE,
    VOID_Y, VOID_DAMAGE_INTERVAL
)
from utils.asset_loader import AssetLoader
from utils.player import Player
from utils.inventory import Inventory
from utils.world_gen import World
from utils.crafting import CraftingSystem
from utils.portal import PortalSystem, DimensionalRift
from utils.mob import MobManager
from utils.save_system import SaveSystem
from utils.item_spawner import ItemSpawnerMenu


class Game:
    """
    Die Hauptklasse des Spiels. Steuert alles.
    
    Wichtige Attribute:
        screen:             Das pygame-Fenster (1200x800 Pixel)
        clock:              Die Spiel-Uhr (für konstante FPS)
        asset_loader:       Lädt alle Grafiken
        save_system:        Speichert und lädt Spielstände
        world:              Die aktuelle Welt (World-Objekt)
        player:             Der Spieler (Player-Objekt)
        inventory:          Das Inventar (Inventory-Objekt)
        crafting:           Das Crafting-System
        portal_system:      Die Portal-Verwaltung
        dimensional_rift:   Der Dimensions-Riss (Ende-Szene)
        mob_manager:        Die Gegner-Verwaltung
        current_dimension:  Name der aktuellen Dimension (z.B. "grassland")
        visited_dimensions: Set aller bereits besuchten Dimensionen
        dimension_cache:    Dictionary mit allen besuchten Welten (für schnellen Wechsel)
        game_state:         "playing" oder "game_over"
        paused:             Ist das Spiel pausiert?
    """
    
    def __init__(self):
        """
        Initialisiert das gesamte Spiel.
        
        Erzeugt:
        - Das pygame-Fenster
        - Die Grafik-Ladestation (AssetLoader)
        - Die Startwelt (Grassland)
        - Den Spieler, das Inventar, das Crafting-System
        - Die Portal-Verwaltung und die Gegner
        - Starter-Gegenstände (Holz-Spitzhacke, Axt, Schwert, Äpfel, Holz)
        """
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
        
        # Cache für vollständige Welten-Persistenz: speichert besuchte, aber aktuell nicht aktive Welten
        self.dimension_cache = {}
        
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
        self.item_spawner_menu = ItemSpawnerMenu()
        
        self.give_starter_items()
        
        self.game_state = "playing"
        self.paused = False
        self.show_help = False
        self.show_coords = False
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
        
        # Rare visual event state
        self.rare_event_active = False
        self.rare_event_timer = 0
        self.rare_event_duration = 0
    
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
            # ESC-Priorität: Zuerst das Item-Spawner-Menü schließen, dann Crafting,
            # dann Inventar, dann Pause. So werden sich nicht überlappende Menüs
            # nacheinander sauber geschlossen.
            if self.item_spawner_menu.is_open:
                self.item_spawner_menu.close()
            elif self.crafting.is_open:
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
        
        elif event.key == pygame.K_g:
            self.player.creative_mode = not self.player.creative_mode
            mode = "ON" if self.player.creative_mode else "OFF"
            self.show_message(f"Creative Mode: {mode}")
        
        elif event.key == pygame.K_F5:
            success, msg = self.save_system.save_game(self.get_game_state())
            self.show_message(msg)
        
        elif event.key == pygame.K_F9:
            self.load_game()
        
        elif event.key == pygame.K_F3:
            self.show_coords = not self.show_coords
        
        elif event.key == pygame.K_k:
            # Geheime Tastenkombination: Strg + Umschalt + K öffnet das Item-Spawner-Menü.
            # Ein einzelnes "k" ohne Modifikatoren tut nichts.
            mods = pygame.key.get_mods()
            if mods & pygame.KMOD_CTRL and mods & pygame.KMOD_SHIFT:
                self.item_spawner_menu.toggle_open(self.inventory)
                # Andere Menüs automatisch schließen, damit sie sich nicht überlappen
                self.inventory.is_open = False
                self.crafting.is_open = False
        
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
        # Höchste Priorität: Item-Spawner-Menü
        if self.item_spawner_menu.is_open:
            if self.item_spawner_menu.handle_click(event.pos, self.inventory, self.show_message):
                pass  # Nachricht wird bereits in handle_click angezeigt
            return
        
        if self.crafting.is_open:
            if self.crafting.handle_click(event.pos, self.inventory):
                self.show_message("Item crafted!")
            return
        
        if self.inventory.is_open:
            self.inventory.handle_mouse_click(event.pos, self.screen)
            return
        
        mouse_x, mouse_y = event.pos
        camera_x, camera_y = self.player.get_camera_offset()
        # Explizit zu int casten, damit keine Floats in range()-Aufrufe gelangen.
        # Hinweis: camera_x/camera_y sind Floats, deswegen muss das Ergebnis
        # von // TILE_SIZE zusätzlich mit int() in einen ganzen Zahlwert
        # umgewandelt werden.
        world_x = int((mouse_x + camera_x) // TILE_SIZE)
        world_y = int((mouse_y + camera_y) // TILE_SIZE)
        
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
                        
                        # Trigger rare visual event with 0.1% probability
                        if random.random() < 0.1:
                            self.rare_event_active = True
                            self.rare_event_timer = 1200
        
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
                                    if not self.player.creative_mode:
                                        self.inventory.use_selected_item()
                            else:
                                block_name = selected_item
                                if self.world.set_block(world_x, world_y, block_name):
                                    if not self.player.creative_mode:
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
        # Auch die Respawn-Warteschlange der aktuellen Welt weiter verarbeiten,
        # damit abgebaute Ressourcen nach Ablauf der respawn_time automatisch zurückkehren.
        self.world.update(dt)
        self.portal_system.update(dt)
        self.mob_manager.update(self.world, self.player, self.inventory, dt)
        
        target = self.portal_system.check_player_portal(self.player.get_rect(), self.world)
        if target and target != self.current_dimension:
            self.travel_to_dimension(target)
        
        if self.message_timer > 0:
            self.message_timer -= dt
        
        # Void-Schaden: Wenn der Spieler zu tief unter der Welt ist, nimmt er Schaden.
        if self.player.y // TILE_SIZE < VOID_Y:
            self.player.take_damage(1)
        
        if not self.player.is_alive():
            self.game_state = "game_over"
        
        if self.dimensional_rift.check_all_dimensions_complete(self.visited_dimensions):
            if self.dimensional_rift.trigger_rift():
                self.show_message("All dimensions explored! Dimensional Rift approaching!")
        
        result = self.dimensional_rift.update(dt)
        if result == "3D_WORLD":
            self.show_message("Welcome to the 3D world! (Coming soon...)")
            self.dimensional_rift.is_active = False
        
        # Update rare visual event timer
        if self.rare_event_active:
            self.rare_event_timer -= dt
            if self.rare_event_timer <= 0:
                self.rare_event_active = False
    
    def travel_to_dimension(self, target_dimension):
        if target_dimension == "dimensional_rift":
            if self.dimensional_rift.trigger_rift():
                self.show_message("DIMENSIONAL RIFT ACTIVATED!")
            return
        
        if target_dimension in DIMENSIONS:
            # Zuerst den aktuellen Weltzustand im Cache sichern, bevor gewechselt wird
            # Inklusive der letzten Spieler-Position in dieser Welt
            self.dimension_cache[self.current_dimension] = {
                "world": self.world.get_save_data(),
                "portals": self.portal_system.get_save_data(),
                "mobs": self.mob_manager.get_save_data(),
                "player_x": self.player.x,
                "player_y": self.player.y
            }
            
            self.current_dimension = target_dimension
            self.visited_dimensions.add(target_dimension)
            
            # Wenn die Zielwelt bereits im Cache vorhanden ist, aus dem Cache wiederherstellen
            if target_dimension in self.dimension_cache:
                cached = self.dimension_cache[target_dimension]
                # skip_generation=True, da load_save_data() direkt danach alles überschreibt
                self.world = World(target_dimension, skip_generation=True)
                self.world.load_save_data(cached.get("world", {}))
                self.portal_system.load_save_data(cached.get("portals", {}))
                self.mob_manager.load_save_data(cached.get("mobs", []))
                
                # Spieler an die letzte Position in dieser Welt setzen (statt Spawn-Punkt)
                self.player.x = cached.get("player_x", self.world.spawn_point[0])
                self.player.y = cached.get("player_y", self.world.spawn_point[1])
            else:
                # Erster Besuch: Welt komplett frisch generieren
                self.world = World(target_dimension)
                self.mob_manager.clear_mobs()
                self.portal_system.active_portals.clear()
                
                # Erster Besuch: Spieler an den Spawn-Punkt setzen
                self.player.x = self.world.spawn_point[0]
                self.player.y = self.world.spawn_point[1]
            
            self.player.velocity_x = 0
            self.player.velocity_y = 0
            self.show_message(f"Welcome to {DIMENSIONS[target_dimension]['name']}!")
    
    def get_game_state(self):
        """Sammelt den aktuellen Spielzustand für die Speicherfunktion."""
        return {
            "player": self.player,
            "inventory": self.inventory,
            "world": self.world,
            "current_dimension": self.current_dimension,
            "visited_dimensions": self.visited_dimensions,
            "portal_system": self.portal_system,
            "mob_manager": self.mob_manager,
            "dimension_cache": self.dimension_cache
        }
    
    def load_game(self):
        """Lädt einen gespeicherten Spielstand und stellt auch den dimension_cache wieder her."""
        save_data, msg = self.save_system.load_game()
        if save_data:
            self.current_dimension = save_data["current_dimension"]
            self.visited_dimensions = set(save_data["visited_dimensions"])
            
            # dimension_cache mit Abwärtskompatibilität: alte Spielstände ohne dieses Feld crashen nicht
            self.dimension_cache = save_data.get("dimension_cache", {})
            
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
    
    def draw_coords(self):
        """
        Zeichnet die aktuellen Koordinaten des Spielers oben links auf den Bildschirm.
        
        Zeigt Block-Koordinaten (x, y) und Pixel-Koordinaten an.
        """
        font = pygame.font.Font(None, 24)
        block_x = int(self.player.x // TILE_SIZE)
        block_y = int(self.player.y // TILE_SIZE)
        pixel_x = int(self.player.x)
        pixel_y = int(self.player.y)
        
        text = f"X: {block_x} Y: {block_y} | PX: {pixel_x} PY: {pixel_y}"
        rendered = font.render(text, True, (255, 255, 255))
        shadow = font.render(text, True, (0, 0, 0))
        
        self.screen.blit(shadow, (11, 11))
        self.screen.blit(rendered, (10, 10))
    
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
        
        # Verstecktes Item-Spawner-Menü zuletzt zeichnen, damit es über allem liegt
        self.item_spawner_menu.draw(self.screen, self.asset_loader)
        
        if self.paused:
            self.draw_pause_menu()
        
        if self.show_help:
            self.draw_help()
        
        if self.show_coords:
            self.draw_coords()
        
        if self.game_state == "game_over":
            self.draw_game_over()
        
        self.dimensional_rift.draw(self.screen)
        
        # Rare visual event overlay
        if self.rare_event_active:
            progress = 1.0 - (self.rare_event_timer / 1200.0)
            hue = (progress * 360) % 360
            color = pygame.Color(0, 0, 0)
            color.hsva = (hue, 80, 100, 25)
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill(color)
            self.screen.blit(overlay, (0, 0))
    
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
        
        # Dynamischer Hinweis auf den aktuell benötigten Portal-Schlüssel
        dimension_data = DIMENSIONS.get(self.current_dimension, {})
        next_dim = dimension_data.get("next_dimension")
        required_key = None
        if next_dim and next_dim != "dimensional_rift":
            next_dim_data = DIMENSIONS.get(next_dim, {})
            required_key = next_dim_data.get("portal_activator")
        
        key_hint = "None"
        if required_key:
            key_hint = required_key.replace("_", " ").title()
        
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
            "F3 - Show/Hide coordinates",
            "",
            "BUILD PORTAL: Place portal_frame blocks in a 3x4 frame",
            f"ACTIVATE PORTAL: Click the frame with the required key ({key_hint})",
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