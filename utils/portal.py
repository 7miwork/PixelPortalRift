import pygame
from utils.constants import TILE_SIZE, DIMENSIONS, BLOCK_PROPERTIES

class PortalSystem:
    def __init__(self):
        self.portal_frames = []
        self.active_portals = []
        self.animation_frame = 0
        self.animation_timer = 0
        
    def check_portal_structure(self, world, x, y, dimension=None):
        required_height = 4
        required_width = 3
        portal_block = f"portal_frame_{dimension}" if dimension else "portal_frame"
        
        for check_y in range(y, y + required_height):
            if world.get_block(x, check_y) != portal_block:
                return None
            if world.get_block(x + required_width - 1, check_y) != portal_block:
                return None
        
        for check_x in range(x, x + required_width):
            if world.get_block(check_x, y) != portal_block:
                return None
            if world.get_block(check_x, y + required_height - 1) != portal_block:
                return None
        
        for check_x in range(x + 1, x + required_width - 1):
            for check_y in range(y + 1, y + required_height - 1):
                block = world.get_block(check_x, check_y)
                if block != "air" and block != "portal":
                    return None
        
        return (x, y, required_width, required_height)
    
    def find_portal_at(self, world, click_x, click_y, dimension=None):
        for dx in range(-3, 1):
            for dy in range(-4, 1):
                result = self.check_portal_structure(world, click_x + dx, click_y + dy, dimension)
                if result:
                    return result
        return None
    
    def activate_portal(self, world, x, y, width, height, current_dimension, inventory):
        dimension_data = DIMENSIONS.get(current_dimension, {})
        next_dim = dimension_data.get("next_dimension")
        
        if next_dim and next_dim != "dimensional_rift":
            next_dim_data = DIMENSIONS.get(next_dim, {})
            required_key = next_dim_data.get("portal_activator")
            
            if required_key:
                if not inventory.has_item(required_key, 1):
                    return False, f"Need {required_key.replace('_', ' ')} to activate!"
                inventory.remove_item(required_key, 1)
        
        for portal_x in range(x + 1, x + width - 1):
            for portal_y in range(y + 1, y + height - 1):
                world.set_block(portal_x, portal_y, "portal")
        
        portal_data = {
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "target": next_dim if next_dim else "grassland"
        }
        self.active_portals.append(portal_data)
        
        return True, f"Portal to {portal_data['target'].replace('_', ' ').title()} activated!"
    
    def deactivate_portal(self, world, portal_data):
        x, y, width, height = portal_data["x"], portal_data["y"], portal_data["width"], portal_data["height"]
        
        for portal_x in range(x + 1, x + width - 1):
            for portal_y in range(y + 1, y + height - 1):
                world.set_block(portal_x, portal_y, "air")
        
        self.active_portals.remove(portal_data)
    
    def check_player_portal(self, player_rect, world):
        player_center_x = player_rect.centerx // TILE_SIZE
        player_center_y = player_rect.centery // TILE_SIZE
        
        block = world.get_block(player_center_x, player_center_y)
        if block == "portal":
            for portal in self.active_portals:
                if (portal["x"] < player_center_x < portal["x"] + portal["width"] - 1 and
                    portal["y"] < player_center_y < portal["y"] + portal["height"] - 1):
                    return portal["target"]
        
        return None
    
    def update(self, dt):
        self.animation_timer += dt
        if self.animation_timer >= 100:
            self.animation_timer = 0
            self.animation_frame = (self.animation_frame + 1) % 8
    
    def draw_portal_effects(self, screen, world, camera_x, camera_y):
        for portal in self.active_portals:
            x, y, width, height = portal["x"], portal["y"], portal["width"], portal["height"]
            
            for px in range(x + 1, x + width - 1):
                for py in range(y + 1, y + height - 1):
                    screen_x = px * TILE_SIZE - camera_x
                    screen_y = py * TILE_SIZE - camera_y
                    
                    alpha = 150 + int(50 * ((self.animation_frame + px + py) % 8) / 8)
                    portal_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                    
                    color_shift = (self.animation_frame * 20) % 255
                    portal_color = (138 + color_shift // 4, 43, 226 - color_shift // 4, alpha)
                    portal_surface.fill(portal_color)
                    
                    for i in range(0, TILE_SIZE, 4):
                        wave_y = int(4 * ((self.animation_frame + i) % 4))
                        pygame.draw.line(portal_surface, (200, 100, 255, 100), 
                                       (0, i + wave_y), (TILE_SIZE, i + wave_y), 2)
                    
                    screen.blit(portal_surface, (screen_x, screen_y))
    
    def get_save_data(self):
        return {
            "active_portals": self.active_portals
        }
    
    def load_save_data(self, data):
        self.active_portals = data.get("active_portals", [])


class DimensionalRift:
    def __init__(self):
        self.is_active = False
        self.animation_progress = 0
        self.completed_dimensions = set()
        self.rift_triggered = False
    
    def check_all_dimensions_complete(self, visited_dimensions):
        required_dimensions = ["grassland", "stone_world", "water_world", "gem_world", "nuclear_world"]
        return all(dim in visited_dimensions for dim in required_dimensions)
    
    def trigger_rift(self):
        if not self.rift_triggered:
            self.rift_triggered = True
            self.is_active = True
            return True
        return False
    
    def update(self, dt):
        if self.is_active:
            self.animation_progress += dt / 1000
            if self.animation_progress >= 5.0:
                self.is_active = False
                return "3D_WORLD"
        return None
    
    def draw(self, screen):
        if not self.is_active:
            return
        
        overlay = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
        
        progress = min(1.0, self.animation_progress / 3.0)
        alpha = int(255 * progress)
        
        overlay.fill((0, 0, 0, alpha))
        
        center_x = screen.get_width() // 2
        center_y = screen.get_height() // 2
        max_radius = max(screen.get_width(), screen.get_height())
        
        for i in range(5):
            radius = int((max_radius * progress * (i + 1) / 5) % max_radius)
            color = (138 + i * 20, 43, 226 - i * 30, 200 - i * 30)
            pygame.draw.circle(overlay, color, (center_x, center_y), radius, 3)
        
        screen.blit(overlay, (0, 0))
        
        if self.animation_progress > 1.0:
            font = pygame.font.Font(None, 72)
            text = font.render("DIMENSIONAL RIFT!", True, (255, 255, 255))
            text_rect = text.get_rect(center=(center_x, center_y - 50))
            screen.blit(text, text_rect)
            
            small_font = pygame.font.Font(None, 36)
            sub_text = small_font.render("Entering 3D World...", True, (200, 200, 255))
            sub_rect = sub_text.get_rect(center=(center_x, center_y + 20))
            screen.blit(sub_text, sub_rect)
