import pygame
from utils.constants import TILE_SIZE, ITEM_PROPERTIES, SCREEN_WIDTH

class InventorySlot:
    def __init__(self):
        self.item = None
        self.count = 0
        self.durability = None
    
    def is_empty(self):
        return self.item is None or self.count <= 0
    
    def can_add(self, item_name, count=1):
        if self.is_empty():
            return True
        if self.item != item_name:
            return False
        props = ITEM_PROPERTIES.get(item_name, {"stackable": True, "max_stack": 64})
        if not props.get("stackable", True):
            return False
        return self.count + count <= props.get("max_stack", 64)
    
    def add(self, item_name, count=1, durability=None):
        if self.is_empty():
            self.item = item_name
            self.count = count
            props = ITEM_PROPERTIES.get(item_name, {})
            if durability is not None:
                self.durability = durability
            elif props.get("durability"):
                self.durability = props["durability"]
            return 0
        
        if self.item != item_name:
            return count
        
        props = ITEM_PROPERTIES.get(item_name, {"stackable": True, "max_stack": 64})
        if not props.get("stackable", True):
            return count
        
        max_stack = props.get("max_stack", 64)
        space = max_stack - self.count
        to_add = min(count, space)
        self.count += to_add
        return count - to_add
    
    def remove(self, count=1):
        if self.is_empty():
            return None, 0
        
        to_remove = min(count, self.count)
        self.count -= to_remove
        item = self.item
        
        if self.count <= 0:
            self.item = None
            self.count = 0
            self.durability = None
        
        return item, to_remove
    
    def use_durability(self, amount=1):
        if self.durability is not None:
            self.durability -= amount
            if self.durability <= 0:
                self.remove(1)
                return True
        return False


class Inventory:
    def __init__(self, size=36, hotbar_size=9):
        self.size = size
        self.hotbar_size = hotbar_size
        self.slots = [InventorySlot() for _ in range(size)]
        self.selected_slot = 0
        self.is_open = False

        # Drag-and-drop state
        self.held_item = None
        self.held_count = 0
        self.held_durability = None
        self.held_origin_slot = None
        self.mouse_pos = (0, 0)
        
    def add_item(self, item_name, count=1, durability=None):
        remaining = count
        
        for slot in self.slots:
            if not slot.is_empty() and slot.item == item_name and slot.can_add(item_name, remaining):
                remaining = slot.add(item_name, remaining, durability)
                if remaining <= 0:
                    return 0
        
        for slot in self.slots:
            if slot.is_empty():
                remaining = slot.add(item_name, remaining, durability)
                if remaining <= 0:
                    return 0
        
        return remaining
    
    def remove_item(self, item_name, count=1):
        remaining = count
        removed_total = 0
        
        for slot in self.slots:
            if slot.item == item_name:
                _, removed = slot.remove(remaining)
                removed_total += removed
                remaining -= removed
                if remaining <= 0:
                    break
        
        return removed_total
    
    def has_item(self, item_name, count=1):
        total = 0
        for slot in self.slots:
            if slot.item == item_name:
                total += slot.count
        return total >= count
    
    def count_item(self, item_name):
        total = 0
        for slot in self.slots:
            if slot.item == item_name:
                total += slot.count
        return total
    
    def get_selected_item(self):
        slot = self.slots[self.selected_slot]
        if slot.is_empty():
            return None
        return slot.item
    
    def get_selected_slot(self):
        return self.slots[self.selected_slot]
    
    def use_selected_item(self):
        slot = self.slots[self.selected_slot]
        if slot.is_empty():
            return None
        
        item = slot.item
        props = ITEM_PROPERTIES.get(item, {})
        
        if props.get("type") == "tool" or props.get("type") == "weapon":
            if slot.use_durability():
                return "broken"
            return item
        elif props.get("type") in ["food", "healing"]:
            slot.remove(1)
            return item
        elif props.get("type") == "block":
            slot.remove(1)
            return item
        
        return item
    
    def select_slot(self, slot_index):
        if 0 <= slot_index < self.hotbar_size:
            self.selected_slot = slot_index
    
    def scroll_selection(self, direction):
        self.selected_slot = (self.selected_slot + direction) % self.hotbar_size
    
    def toggle_open(self):
        self.is_open = not self.is_open
    
    def get_slot_at_pos(self, mouse_pos, screen):
        slot_size = 50
        padding = 4
        cols = 9
        rows = self.size // cols
        total_width = cols * (slot_size + padding) - padding
        total_height = rows * (slot_size + padding) - padding
        start_x = (screen.get_width() - total_width) // 2
        start_y = (screen.get_height() - total_height) // 2

        mx, my = mouse_pos
        for i in range(self.size):
            row = i // cols
            col = i % cols
            x = start_x + col * (slot_size + padding)
            y = start_y + row * (slot_size + padding)
            if x <= mx <= x + slot_size and y <= my <= y + slot_size:
                return i
        return None

    def handle_mouse_click(self, mouse_pos, screen):
        self.mouse_pos = mouse_pos
        slot_index = self.get_slot_at_pos(mouse_pos, screen)
        if slot_index is None:
            return

        target_slot = self.slots[slot_index]

        if self.held_item is None:
            # Pick up item from clicked slot
            if not target_slot.is_empty():
                self.held_item = target_slot.item
                self.held_count = target_slot.count
                self.held_durability = target_slot.durability
                self.held_origin_slot = slot_index
                target_slot.item = None
                target_slot.count = 0
                target_slot.durability = None
        else:
            # Place held item into clicked slot
            if target_slot.is_empty():
                target_slot.item = self.held_item
                target_slot.count = self.held_count
                target_slot.durability = self.held_durability
                self.held_item = None
                self.held_count = 0
                self.held_durability = None
                self.held_origin_slot = None
            elif target_slot.item == self.held_item:
                # Same item — stack as much as possible
                props = ITEM_PROPERTIES.get(self.held_item, {"stackable": True, "max_stack": 64})
                max_stack = props.get("max_stack", 64)
                space = max_stack - target_slot.count
                to_move = min(self.held_count, space)
                target_slot.count += to_move
                self.held_count -= to_move
                if self.held_count <= 0:
                    self.held_item = None
                    self.held_count = 0
                    self.held_durability = None
                    self.held_origin_slot = None
            else:
                # Different item — swap
                origin_slot = self.slots[self.held_origin_slot]
                (origin_slot.item, target_slot.item) = (target_slot.item, self.held_item)
                (origin_slot.count, target_slot.count) = (target_slot.count, self.held_count)
                (origin_slot.durability, target_slot.durability) = (target_slot.durability, self.held_durability)
                self.held_item = None
                self.held_count = 0
                self.held_durability = None
                self.held_origin_slot = None

    def swap_slots(self, slot1, slot2):
        if 0 <= slot1 < self.size and 0 <= slot2 < self.size:
            self.slots[slot1], self.slots[slot2] = self.slots[slot2], self.slots[slot1]
    
    def draw_hotbar(self, screen, asset_loader):
        slot_size = 50
        padding = 4
        total_width = self.hotbar_size * (slot_size + padding) - padding
        start_x = (SCREEN_WIDTH - total_width) // 2
        start_y = screen.get_height() - slot_size - 10
        
        for i in range(self.hotbar_size):
            x = start_x + i * (slot_size + padding)
            slot = self.slots[i]
            
            if i == self.selected_slot:
                pygame.draw.rect(screen, (255, 255, 255), (x - 2, start_y - 2, slot_size + 4, slot_size + 4), 3)
            
            pygame.draw.rect(screen, (50, 50, 50), (x, start_y, slot_size, slot_size))
            pygame.draw.rect(screen, (100, 100, 100), (x, start_y, slot_size, slot_size), 2)
            
            if not slot.is_empty():
                texture = asset_loader.get_item_texture(slot.item)
                if texture:
                    scaled = pygame.transform.scale(texture, (slot_size - 8, slot_size - 8))
                    screen.blit(scaled, (x + 4, start_y + 4))
                
                if slot.count > 1:
                    font = pygame.font.Font(None, 20)
                    count_text = font.render(str(slot.count), True, (255, 255, 255))
                    screen.blit(count_text, (x + slot_size - 15, start_y + slot_size - 18))
                
                if slot.durability is not None and slot.item is not None:
                    props = ITEM_PROPERTIES.get(slot.item, {})
                    max_dur = props.get("durability", 100) or 100
                    dur_percent = slot.durability / max_dur
                    dur_color = (255, int(255 * dur_percent), 0)
                    dur_width = int((slot_size - 8) * dur_percent)
                    pygame.draw.rect(screen, dur_color, (x + 4, start_y + slot_size - 6, dur_width, 3))
    
    def draw_full_inventory(self, screen, asset_loader):
        if not self.is_open:
            return

        overlay = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        slot_size = 50
        padding = 4
        cols = 9
        rows = self.size // cols

        total_width = cols * (slot_size + padding) - padding
        total_height = rows * (slot_size + padding) - padding
        start_x = (screen.get_width() - total_width) // 2
        start_y = (screen.get_height() - total_height) // 2

        bg_rect = pygame.Rect(start_x - 20, start_y - 60, total_width + 40, total_height + 100)
        pygame.draw.rect(screen, (60, 60, 60), bg_rect)
        pygame.draw.rect(screen, (100, 100, 100), bg_rect, 3)

        font = pygame.font.Font(None, 36)
        title = font.render("Inventory", True, (255, 255, 255))
        screen.blit(title, (start_x, start_y - 45))

        for i in range(self.size):
            row = i // cols
            col = i % cols
            x = start_x + col * (slot_size + padding)
            y = start_y + row * (slot_size + padding)
            slot = self.slots[i]

            pygame.draw.rect(screen, (40, 40, 40), (x, y, slot_size, slot_size))
            pygame.draw.rect(screen, (80, 80, 80), (x, y, slot_size, slot_size), 2)

            if not slot.is_empty():
                texture = asset_loader.get_item_texture(slot.item)
                if texture:
                    scaled = pygame.transform.scale(texture, (slot_size - 8, slot_size - 8))
                    screen.blit(scaled, (x + 4, y + 4))

                if slot.count > 1:
                    count_font = pygame.font.Font(None, 20)
                    count_text = count_font.render(str(slot.count), True, (255, 255, 255))
                    screen.blit(count_text, (x + slot_size - 15, y + slot_size - 18))

        # Draw held item following the cursor
        if self.held_item is not None:
            texture = asset_loader.get_item_texture(self.held_item)
            if texture:
                scaled = pygame.transform.scale(texture, (40, 40))
                mx, my = self.mouse_pos
                screen.blit(scaled, (mx - 20, my - 20))
    
    def get_save_data(self):
        data = []
        for slot in self.slots:
            if slot.is_empty():
                data.append(None)
            else:
                data.append({
                    "item": slot.item,
                    "count": slot.count,
                    "durability": slot.durability
                })
        return data
    
    def load_save_data(self, data):
        for i, slot_data in enumerate(data):
            if i >= self.size:
                break
            if slot_data is None:
                self.slots[i] = InventorySlot()
            else:
                self.slots[i].item = slot_data["item"]
                self.slots[i].count = slot_data["count"]
                self.slots[i].durability = slot_data.get("durability")
