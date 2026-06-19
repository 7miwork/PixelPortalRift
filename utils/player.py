import pygame
from utils.constants import TILE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT

class Player:
    def __init__(self, x, y, asset_loader):
        self.x = x
        self.y = y
        self.width = 24
        self.height = 32

        self.velocity_x = 0
        self.velocity_y = 0

        self.speed = 4
        self.jump_power = 12
        self.gravity = 0.5
        self.on_ground = False
        self.is_jumping = False
        self.facing_right = True

        # ===== STATS =====
        self.max_health = 100
        self.health = self.max_health
        self.max_hunger = 100
        self.hunger = self.max_hunger
        self.hunger_timer = 0
        self.damage_cooldown = 0

        self.asset_loader = asset_loader
        self.texture = asset_loader.get_player_texture()

    # =========================================================
    # UPDATE
    # =========================================================
    def update(self, world, dt):
        # -------- HORIZONTAL --------
        new_x = self.x + self.velocity_x
        if not self.check_collision_x(world, new_x):
            self.x = new_x
        else:
            self.velocity_x = 0

        # -------- GRAVITY --------
        self.velocity_y += self.gravity
        if self.velocity_y > 15:
            self.velocity_y = 15

        # -------- VERTICAL --------
        new_y = self.y + self.velocity_y
        
        if not self.check_collision_y(world, new_y):
            self.y = new_y
            self.on_ground = False
        else:
            if self.velocity_y > 0:
                # Landed on ground - snap to exact tile position
                self.y = (int((self.y + self.height) // TILE_SIZE) * TILE_SIZE) - self.height
                self.on_ground = True
                self.is_jumping = False
            self.velocity_y = 0

        # -------- HUNGER / HEALTH --------
        self.hunger_timer += dt
        if self.hunger_timer >= 5000:
            self.hunger = max(0, self.hunger - 1)
            self.hunger_timer = 0
            if self.hunger <= 0:
                self.health = max(0, self.health - 1)

        if self.damage_cooldown > 0:
            self.damage_cooldown -= dt

    # =========================================================
    # COLLISION
    # =========================================================
    def check_collision_x(self, world, x):
        points = [
            (x + 2, self.y + 2),
            (x + self.width - 2, self.y + 2),
            (x + 2, self.y + self.height - 2),
            (x + self.width - 2, self.y + self.height - 2),
        ]

        for px, py in points:
            tile_x = int(px) // TILE_SIZE
            tile_y = int(py) // TILE_SIZE
            block = world.get_block(tile_x, tile_y)
            if block and world.is_solid(block):
                return True
        return False

    def check_collision_y(self, world, y):
        # Check TOP (ceiling) and BOTTOM (ground)
        points_top = [
            (self.x + 2, y),
            (self.x + self.width - 2, y),
        ]
        points_bottom = [
            (self.x + 2, y + self.height),
            (self.x + self.width - 2, y + self.height),
        ]

        for px, py in points_top:
            tile_x = int(px) // TILE_SIZE
            tile_y = int(py) // TILE_SIZE
            block = world.get_block(tile_x, tile_y)
            if block and world.is_solid(block):
                return True

        for px, py in points_bottom:
            tile_x = int(px) // TILE_SIZE
            tile_y = int(py) // TILE_SIZE
            block = world.get_block(tile_x, tile_y)
            if block and world.is_solid(block):
                return True

        return False

    # =========================================================
    # MOVEMENT
    # =========================================================
    def move(self, direction):
        if direction == "left":
            self.velocity_x = -self.speed
            self.facing_right = False
        elif direction == "right":
            self.velocity_x = self.speed
            self.facing_right = True
        elif direction == "stop":
            self.velocity_x = 0

    def jump(self):
        if self.on_ground and not self.is_jumping:
            self.velocity_y = -self.jump_power
            self.on_ground = False
            self.is_jumping = True

    # =========================================================
    # HEALTH
    # =========================================================
    def take_damage(self, amount):
        if self.damage_cooldown <= 0:
            self.health = max(0, self.health - amount)
            self.damage_cooldown = 1000
            return True
        return False

    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)

    def eat(self, hunger_restore, health_restore=0):
        self.hunger = min(self.max_hunger, self.hunger + hunger_restore)
        if health_restore > 0:
            self.heal(health_restore)

    def is_alive(self):
        return self.health > 0

    # =========================================================
    # RENDER
    # =========================================================
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def get_camera_offset(self):
        return (
            self.x - SCREEN_WIDTH // 2 + self.width // 2,
            self.y - SCREEN_HEIGHT // 2 + self.height // 2
        )

    def draw(self, screen, camera_x, camera_y):
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y

        if self.texture:
            img = self.texture
            if not self.facing_right:
                img = pygame.transform.flip(img, True, False)
            screen.blit(img, (draw_x, draw_y))
        else:
            pygame.draw.rect(
                screen,
                (255, 200, 150),
                (draw_x, draw_y, self.width, self.height)
            )

        # Damage flash
        if self.damage_cooldown > 0 and int(self.damage_cooldown / 100) % 2 == 0:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((255, 0, 0, 100))
            screen.blit(overlay, (draw_x, draw_y))

    def draw_stats(self, screen):
        bar_width = 200
        bar_height = 20
        x = 10
        y = 10

        # Health
        pygame.draw.rect(screen, (100, 100, 100), (x, y, bar_width, bar_height))
        hw = int((self.health / self.max_health) * bar_width)
        pygame.draw.rect(screen, (255, 0, 0), (x, y, hw, bar_height))
        pygame.draw.rect(screen, (255, 255, 255), (x, y, bar_width, bar_height), 2)

        font = pygame.font.Font(None, 20)
        screen.blit(
            font.render(f"HP: {int(self.health)}/{self.max_health}", True, (255, 255, 255)),
            (x + 5, y + 3)
        )

        # Hunger
        pygame.draw.rect(screen, (100, 100, 100), (x, y + 25, bar_width, bar_height))
        hw = int((self.hunger / self.max_hunger) * bar_width)
        pygame.draw.rect(screen, (139, 90, 43), (x, y + 25, hw, bar_height))
        pygame.draw.rect(screen, (255, 255, 255), (x, y + 25, bar_width, bar_height), 2)

        screen.blit(
            font.render(f"Hunger: {int(self.hunger)}/{self.max_hunger}", True, (255, 255, 255)),
            (x + 5, y + 28)
        )