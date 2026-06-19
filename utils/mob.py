import pygame
import random
import math
from utils.constants import TILE_SIZE, MOB_PROPERTIES, DIMENSIONS, WORLD_ITEM_POOLS

class Mob:
    def __init__(self, x, y, mob_type, asset_loader):
        self.x = x
        self.y = y
        self.mob_type = mob_type
        self.properties = MOB_PROPERTIES.get(mob_type, {})
        
        self.width, self.height = self.properties.get("size", (24, 24))
        self.health = self.properties.get("health", 10)
        self.max_health = self.health
        self.damage = self.properties.get("damage", 1)
        self.speed = self.properties.get("speed", 1)
        self.drop = self.properties.get("drop")
        
        self.velocity_x = 0
        self.velocity_y = 0
        self.gravity = 0.3
        self.on_ground = False
        self.facing_right = random.choice([True, False])
        
        self.ai_timer = 0
        self.ai_state = "idle"
        self.target = None
        self.attack_cooldown = 0
        self.damage_cooldown = 0
        
        self.texture = asset_loader.get_mob_texture(mob_type)
    
    def update(self, world, player, dt):
        self.ai_timer += dt
        self.attack_cooldown = max(0, self.attack_cooldown - dt)
        self.damage_cooldown = max(0, self.damage_cooldown - dt)
        
        player_dist = math.sqrt((player.x - self.x) ** 2 + (player.y - self.y) ** 2)
        
        if player_dist < 200:
            self.ai_state = "chase"
            self.target = player
        elif player_dist > 400:
            self.ai_state = "wander"
            self.target = None
        
        if self.ai_state == "idle":
            if self.ai_timer > 2000:
                self.ai_timer = 0
                if random.random() < 0.5:
                    self.ai_state = "wander"
        
        elif self.ai_state == "wander":
            if self.ai_timer > 3000:
                self.ai_timer = 0
                self.facing_right = random.choice([True, False])
                if random.random() < 0.3:
                    self.ai_state = "idle"
            
            self.velocity_x = self.speed if self.facing_right else -self.speed
            
            if random.random() < 0.02 and self.on_ground:
                self.velocity_y = -8
        
        elif self.ai_state == "chase":
            if self.target:
                if self.target.x > self.x:
                    self.velocity_x = self.speed * 1.5
                    self.facing_right = True
                else:
                    self.velocity_x = -self.speed * 1.5
                    self.facing_right = False
                
                if self.on_ground and random.random() < 0.05:
                    self.velocity_y = -10
                
                if player_dist < 40 and self.attack_cooldown <= 0:
                    self.attack(player)
        
        self.velocity_y += self.gravity
        if self.velocity_y > 10:
            self.velocity_y = 10
        
        new_x = self.x + self.velocity_x
        if not self.check_collision(world, new_x, self.y):
            self.x = new_x
        else:
            self.velocity_x = 0
            self.facing_right = not self.facing_right
        
        new_y = self.y + self.velocity_y
        if not self.check_collision(world, self.x, new_y):
            self.y = new_y
            self.on_ground = False
        else:
            if self.velocity_y > 0:
                self.on_ground = True
            self.velocity_y = 0
    
    def check_collision(self, world, x, y):
        points = [
            (x, y),
            (x + self.width, y),
            (x, y + self.height),
            (x + self.width, y + self.height)
        ]
        
        for px, py in points:
            tile_x = int(px) // TILE_SIZE
            tile_y = int(py) // TILE_SIZE
            block = world.get_block(tile_x, tile_y)
            if block and world.is_solid(block):
                return True
        return False
    
    def attack(self, player):
        if self.attack_cooldown <= 0:
            if player.take_damage(self.damage):
                self.attack_cooldown = 1000
    
    def take_damage(self, amount):
        if self.damage_cooldown <= 0:
            self.health -= amount
            self.damage_cooldown = 500
            
            knockback = 5 if self.facing_right else -5
            self.velocity_x = -knockback
            self.velocity_y = -3
            
            return True
        return False
    
    def is_alive(self):
        return self.health > 0
    
    def get_drop(self):
        if self.drop and random.random() < 0.8:
            return self.drop
        return None
    
    def get_world_drop(self, world_dimension):
        pool = WORLD_ITEM_POOLS.get(world_dimension, {})
        mob_drops = pool.get("mob_drops", [])
        if mob_drops and random.random() < 0.8:
            return random.choice(mob_drops)
        if self.drop:
            return self.drop
        return None
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def draw(self, screen, camera_x, camera_y):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        
        if self.texture:
            if not self.facing_right:
                flipped = pygame.transform.flip(self.texture, True, False)
                screen.blit(flipped, (draw_x, draw_y))
            else:
                screen.blit(self.texture, (draw_x, draw_y))
        else:
            color = self.properties.get("color", (255, 0, 0))
            pygame.draw.rect(screen, color, (draw_x, draw_y, self.width, self.height))
        
        if self.damage_cooldown > 0:
            damage_overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            damage_overlay.fill((255, 0, 0, 100))
            screen.blit(damage_overlay, (draw_x, draw_y))
        
        health_bar_width = self.width
        health_bar_height = 4
        health_percent = self.health / self.max_health
        
        pygame.draw.rect(screen, (100, 0, 0), (draw_x, draw_y - 8, health_bar_width, health_bar_height))
        pygame.draw.rect(screen, (0, 255, 0), (draw_x, draw_y - 8, int(health_bar_width * health_percent), health_bar_height))


class MobManager:
    def __init__(self, asset_loader):
        self.mobs = []
        self.asset_loader = asset_loader
        self.spawn_timer = 0
        self.max_mobs = 15
    
    def update(self, world, player, dt):
        self.spawn_timer += dt
        
        if self.spawn_timer >= 5000 and len(self.mobs) < self.max_mobs:
            self.spawn_timer = 0
            self.try_spawn_mob(world, player)
        
        for mob in self.mobs[:]:
            mob.update(world, player, dt)
            
            if not mob.is_alive():
                drop = mob.get_world_drop(world.dimension)
                if drop:
                    pass
                self.mobs.remove(mob)
    
    def try_spawn_mob(self, world, player):
        dimension_data = DIMENSIONS.get(world.dimension, {})
        available_mobs = dimension_data.get("mobs", [])
        
        if not available_mobs:
            return
        
        spawn_x = player.x + random.choice([-1, 1]) * random.randint(300, 500)
        
        spawn_y = None
        for y in range(10, world.height - 10):
            if world.is_solid(world.get_block(int(spawn_x // TILE_SIZE), y)):
                spawn_y = (y - 2) * TILE_SIZE
                break
        
        if spawn_y is None:
            return
        
        if 0 <= spawn_x < world.width * TILE_SIZE:
            mob_type = random.choice(available_mobs)
            new_mob = Mob(spawn_x, spawn_y, mob_type, self.asset_loader)
            self.mobs.append(new_mob)
    
    def spawn_mob_at(self, x, y, mob_type):
        new_mob = Mob(x, y, mob_type, self.asset_loader)
        self.mobs.append(new_mob)
    
    def clear_mobs(self):
        self.mobs.clear()
    
    def check_attack(self, player_rect, damage):
        hits = []
        for mob in self.mobs:
            if player_rect.colliderect(mob.get_rect()):
                if mob.take_damage(damage):
                    hits.append(mob)
        return hits
    
    def draw(self, screen, camera_x, camera_y):
        for mob in self.mobs:
            mob.draw(screen, camera_x, camera_y)
    
    def get_save_data(self):
        return [{
            "x": mob.x,
            "y": mob.y,
            "mob_type": mob.mob_type,
            "health": mob.health
        } for mob in self.mobs]
    
    def load_save_data(self, data):
        self.mobs.clear()
        for mob_data in data:
            mob = Mob(mob_data["x"], mob_data["y"], mob_data["mob_type"], self.asset_loader)
            mob.health = mob_data["health"]
            self.mobs.append(mob)
