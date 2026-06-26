import pygame
from utils.constants import CRAFTING_RECIPES, SCREEN_WIDTH, SCREEN_HEIGHT

class CraftingSystem:
    def __init__(self):
        self.recipes = CRAFTING_RECIPES
        self.is_open = False
        self.selected_recipe = 0
        self.scroll_offset = 0
        self.craftable_recipes = []
    
    def update_craftable(self, inventory):
        self.craftable_recipes = []
        for recipe_name, recipe_data in self.recipes.items():
            if self.can_craft(recipe_name, inventory):
                self.craftable_recipes.append((recipe_name, recipe_data, True))
            else:
                self.craftable_recipes.append((recipe_name, recipe_data, False))
    
    def can_craft(self, recipe_name, inventory):
        if recipe_name not in self.recipes:
            return False
        
        recipe = self.recipes[recipe_name]
        for ingredient, count in recipe["ingredients"].items():
            if not inventory.has_item(ingredient, count):
                return False
        return True
    
    def craft(self, recipe_name, inventory):
        if not self.can_craft(recipe_name, inventory):
            return False
        
        recipe = self.recipes[recipe_name]
        
        for ingredient, count in recipe["ingredients"].items():
            inventory.remove_item(ingredient, count)
        
        result_count = recipe.get("result_count", 1)
        remaining = inventory.add_item(recipe_name, result_count)
        
        return remaining == 0
    
    def toggle_open(self, inventory):
        self.is_open = not self.is_open
        if self.is_open:
            self.update_craftable(inventory)
    
    def scroll(self, direction):
        max_visible = 8
        max_scroll = max(0, len(self.craftable_recipes) - max_visible)
        self.scroll_offset = max(0, min(max_scroll, self.scroll_offset + direction))
    
    def select_recipe(self, index):
        actual_index = index + self.scroll_offset
        if 0 <= actual_index < len(self.craftable_recipes):
            self.selected_recipe = actual_index
    
    def craft_selected(self, inventory):
        if 0 <= self.selected_recipe < len(self.craftable_recipes):
            recipe_name = self.craftable_recipes[self.selected_recipe][0]
            if self.craft(recipe_name, inventory):
                self.update_craftable(inventory)
                return True
        return False
    
    def draw(self, screen, asset_loader, inventory):
        if not self.is_open:
            return
        
        overlay = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        panel_width = 400
        panel_height = 500
        panel_x = (SCREEN_WIDTH - panel_width) // 2
        panel_y = (SCREEN_HEIGHT - panel_height) // 2
        
        pygame.draw.rect(screen, (60, 60, 60), (panel_x, panel_y, panel_width, panel_height))
        pygame.draw.rect(screen, (100, 100, 100), (panel_x, panel_y, panel_width, panel_height), 3)
        
        font = pygame.font.Font(None, 36)
        title = font.render("Crafting", True, (255, 255, 255))
        screen.blit(title, (panel_x + 20, panel_y + 15))
        
        recipe_height = 55
        max_visible = 8
        start_y = panel_y + 60
        
        for i in range(max_visible):
            recipe_index = i + self.scroll_offset
            if recipe_index >= len(self.craftable_recipes):
                break
            
            recipe_name, recipe_data, can_craft = self.craftable_recipes[recipe_index]
            y = start_y + i * recipe_height
            
            bg_color = (80, 80, 80) if can_craft else (50, 50, 50)
            if recipe_index == self.selected_recipe:
                bg_color = (100, 100, 150) if can_craft else (70, 70, 90)
            
            pygame.draw.rect(screen, bg_color, (panel_x + 10, y, panel_width - 20, recipe_height - 5))
            
            texture = asset_loader.get_item_texture(recipe_name)
            if texture:
                scaled = pygame.transform.scale(texture, (40, 40))
                screen.blit(scaled, (panel_x + 15, y + 5))
            
            name_color = (255, 255, 255) if can_craft else (150, 150, 150)
            small_font = pygame.font.Font(None, 24)
            name_text = small_font.render(recipe_name.replace("_", " ").title(), True, name_color)
            screen.blit(name_text, (panel_x + 60, y + 5))
            
            result_count = recipe_data.get("result_count", 1)
            if result_count > 1:
                count_text = small_font.render(f"x{result_count}", True, (200, 200, 200))
                screen.blit(count_text, (panel_x + 60, y + 25))
            
            ing_x = panel_x + 150
            tiny_font = pygame.font.Font(None, 18)
            for idx, (ingredient, count) in enumerate(recipe_data["ingredients"].items()):
                has_count = inventory.count_item(ingredient)
                ing_color = (100, 255, 100) if has_count >= count else (255, 100, 100)
                ing_text = tiny_font.render(f"{ingredient}: {has_count}/{count}", True, ing_color)
                line_y = y + 8 + idx * 22
                screen.blit(ing_text, (ing_x, line_y))
        
        if len(self.craftable_recipes) > max_visible:
            scrollbar_height = int((max_visible / len(self.craftable_recipes)) * (panel_height - 100))
            scrollbar_y = panel_y + 60 + int((self.scroll_offset / len(self.craftable_recipes)) * (panel_height - 100))
            pygame.draw.rect(screen, (150, 150, 150), (panel_x + panel_width - 15, scrollbar_y, 10, scrollbar_height))
        
        help_font = pygame.font.Font(None, 24)
        instructions = help_font.render("Click to craft | Scroll to browse | C to close", True, (200, 200, 200))
        screen.blit(instructions, (panel_x + 20, panel_y + panel_height - 30))
    
    def handle_click(self, mouse_pos, inventory):
        if not self.is_open:
            return False
        
        panel_width = 400
        panel_height = 500
        panel_x = (SCREEN_WIDTH - panel_width) // 2
        panel_y = (SCREEN_HEIGHT - panel_height) // 2
        
        recipe_height = 55
        start_y = panel_y + 60
        
        for i in range(8):
            recipe_index = i + self.scroll_offset
            if recipe_index >= len(self.craftable_recipes):
                break
            
            y = start_y + i * recipe_height
            rect = pygame.Rect(panel_x + 10, y, panel_width - 20, recipe_height - 5)
            
            if rect.collidepoint(mouse_pos):
                self.selected_recipe = recipe_index
                return self.craft_selected(inventory)
        
        return False
