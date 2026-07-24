"""
utils/inventory.py – Inventar-Verwaltung
=========================================

Dieses Modul verwaltet das gesamte Inventar des Spielers.
Es enthält zwei Klassen:
- InventorySlot: Ein einzelner Slot im Inventar (kann einen Gegenstand halten)
- Inventory: Das gesamte Inventar (alle Slots + Hotbar + Drag-and-Drop)

Das Inventar hat 36 Slots, davon 9 in der Hotbar (schnell erreichbar).
Gegenstände können gestapelt werden (stackable), wenn sie denselben Typ haben.
"""

import pygame
from utils.constants import TILE_SIZE, ITEM_PROPERTIES, SCREEN_WIDTH


class InventorySlot:
    """
    Ein einzelner Slot im Inventar.
    
    Wichtige Attribute:
        item:       Name des Gegenstands (String) oder None (leer)
        count:      Anzahl der Gegenstände in diesem Slot
        durability: Haltbarkeit (für Werkzeuge/Waffen, None wenn nicht anwendbar)
    
    Ein Slot kann leer sein (item=None, count=0).
    Wenn stackable=True, können mehrere Gegenstände in einem Slot sein.
    """
    
    def __init__(self):
        """Erzeugt einen leeren Inventar-Slot."""
        self.item = None
        self.count = 0
        self.durability = None
    
    def is_empty(self):
        """Prüft, ob der Slot leer ist."""
        return self.item is None or self.count <= 0
    
    def can_add(self, item_name, count=1):
        """
        Prüft, ob man diesen Gegenstand in den Slot legen kann.
        
        Bedingungen:
        - Slot ist leer → ja
        - Gleicher Gegenstand + stackable + genug Platz → ja
        - Sonst → nein
        
        :param item_name: Name des Gegenstands
        :param count: Wie viele sollen hinzugefügt werden?
        :return: True wenn möglich
        """
        if self.is_empty():
            return True
        if self.item != item_name:
            return False  # Anderer Gegenstand → nicht legbar
        props = ITEM_PROPERTIES.get(item_name, {"stackable": True, "max_stack": 64})
        if not props.get("stackable", True):
            return False  # Nicht stapelbar → nur 1 pro Slot
        return self.count + count <= props.get("max_stack", 64)
    
    def add(self, item_name, count=1, durability=None):
        """
        Fügt Gegenstände zum Slot hinzu.
        
        :param item_name: Name des Gegenstands
        :param count: Wie viele?
        :param durability: Haltbarkeit (optional, für Werkzeuge)
        :return: Anzahl der Gegenstände, die NICHT hinzugefügt werden konnten
                 (0 = alles passte)
        """
        if self.is_empty():
            # Slot ist leer → neu befüllen
            self.item = item_name
            self.count = count
            props = ITEM_PROPERTIES.get(item_name, {})
            if durability is not None:
                self.durability = durability
            elif props.get("durability"):
                self.durability = props["durability"]
            return 0  # Alles hinzugefügt
        
        if self.item != item_name:
            return count  # Kann nicht hinzugefügt werden
        
        # Stapeln: wie viele passen noch?
        props = ITEM_PROPERTIES.get(item_name, {"stackable": True, "max_stack": 64})
        if not props.get("stackable", True):
            return count
        
        max_stack = props.get("max_stack", 64)
        space = max_stack - self.count          # Freier Platz
        to_add = min(count, space)              # Nicht mehr als Platz
        self.count += to_add
        return count - to_add                   # Rest (was nicht passte)
    
    def remove(self, count=1):
        """
        Entfernt Gegenstände aus dem Slot.
        
        :param count: Wie viele sollen entfernt werden?
        :return: (item_name, removed_count) – was wurde entfernt?
        """
        if self.is_empty():
            return None, 0
        
        to_remove = min(count, self.count)
        self.count -= to_remove
        item = self.item
        
        # Wenn leer: Slot zurücksetzen
        if self.count <= 0:
            self.item = None
            self.count = 0
            self.durability = None
        
        return item, to_remove
    
    def use_durability(self, amount=1):
        """
        Nutzt die Haltbarkeit eines Werkzeugs/Waffe.
        
        Wenn die Haltbarkeit auf 0 fällt, wird das Item entfernt.
        
        :param amount: Wie viel Haltbarkeit wird verbraucht?
        :return: True wenn das Item kaputt gegangen ist
        """
        if self.durability is not None:
            self.durability -= amount
            if self.durability <= 0:
                self.remove(1)  # Werkzeug ist kaputt
                return True
        return False


class Inventory:
    """
    Das gesamte Inventar des Spielers.
    
    Wichtige Attribute:
        size:         Anzahl der Slots (36)
        hotbar_size:  Anzahl der Hotbar-Slots (9)
        slots:        Liste von InventorySlot-Objekten
        selected_slot: Aktuell ausgewählter Slot (0-8)
        is_open:      Ist das Inventar-Fenster geöffnet?
        
    Drag-and-Drop (für das Inventar-Fenster):
        held_item:     Der aktuell "in der Hand" gehaltene Gegenstand
        held_count:    Wie viele?
        held_durability: Haltbarkeit
        held_origin_slot: Aus welchem Slot wurde er genommen?
    """
    
    def __init__(self, size=36, hotbar_size=9):
        """
        Erzeugt ein Inventar mit 36 Slots (davon 9 in der Hotbar).
        
        :param size: Gesamtanzahl der Slots
        :param hotbar_size: Anzahl der Hotbar-Slots
        """
        self.size = size
        self.hotbar_size = hotbar_size
        self.slots = [InventorySlot() for _ in range(size)]
        self.selected_slot = 0
        self.is_open = False

        # Drag-and-Drop Zustand
        self.held_item = None
        self.held_count = 0
        self.held_durability = None
        self.held_origin_slot = None
        self.mouse_pos = (0, 0)
        
    def add_item(self, item_name, count=1, durability=None):
        """
        Fügt einen Gegenstand zum Inventar hinzu.
        
        Zuerst wird versucht, zu vorhandenen Stapeln desselben Items hinzuzufügen.
        Wenn das nicht reicht, werden leere Slots gefüllt.
        
        :param item_name: Name des Gegenstands
        :param count: Wie viele?
        :param durability: Haltbarkeit (optional)
        :return: Anzahl der Gegenstände, die NICHT hinzugefügt werden konnten
                 (0 = alles hinzugefügt)
        """
        remaining = count
        
        # Schritt 1: Vorhandene Stapel auffüllen
        for slot in self.slots:
            if not slot.is_empty() and slot.item == item_name and slot.can_add(item_name, remaining):
                remaining = slot.add(item_name, remaining, durability)
                if remaining <= 0:
                    return 0
        
        # Schritt 2: Leere Slots füllen
        for slot in self.slots:
            if slot.is_empty():
                remaining = slot.add(item_name, remaining, durability)
                if remaining <= 0:
                    return 0
        
        return remaining
    
    def remove_item(self, item_name, count=1):
        """
        Entfernt einen Gegenstand aus dem Inventar.
        
        :param item_name: Name des Gegenstands
        :param count: Wie viele sollen entfernt werden?
        :return: Anzahl der tatsächlich entfernten Gegenstände
        """
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
        """
        Prüft, ob genug von einem Gegenstand im Inventar ist.
        
        :param item_name: Name des Gegenstands
        :param count: Wie viele werden benötigt?
        :return: True wenn genug vorhanden
        """
        total = 0
        for slot in self.slots:
            if slot.item == item_name:
                total += slot.count
        return total >= count
    
    def count_item(self, item_name):
        """
        Zählt, wie viele von einem Gegenstand im Inventar sind.
        
        :param item_name: Name des Gegenstands
        :return: Gesamtanzahl
        """
        total = 0
        for slot in self.slots:
            if slot.item == item_name:
                total += slot.count
        return total
    
    def get_selected_item(self):
        """Gibt den Namen des Gegenstands im ausgewählten Hotbar-Slot zurück."""
        slot = self.slots[self.selected_slot]
        if slot.is_empty():
            return None
        return slot.item
    
    def get_selected_slot(self):
        """Gibt den ausgewählten InventorySlot zurück."""
        return self.slots[self.selected_slot]
    
    def use_selected_item(self):
        """
        Benutzt den Gegenstand im ausgewählten Slot.
        
        - Werkzeuge/Waffen: Haltbarkeit wird verringert
        - Essen/Heilung: Ein Stück wird verbraucht
        - Blöcke: Ein Stück wird verbraucht
        
        :return: "broken" wenn das Werkzeug kaputt ging, sonst Item-Name oder None
        """
        slot = self.slots[self.selected_slot]
        if slot.is_empty():
            return None
        
        item = slot.item
        props = ITEM_PROPERTIES.get(item, {})
        
        if props.get("type") == "tool" or props.get("type") == "weapon":
            # Haltbarkeit verringern
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
        """
        Wählt einen Hotbar-Slot aus (Tasten 1-9).
        
        :param slot_index: Index 0-8
        """
        if 0 <= slot_index < self.hotbar_size:
            self.selected_slot = slot_index
    
    def scroll_selection(self, direction):
        """
        Scrollt durch die Hotbar (Mausrad).
        
        :param direction: +1 oder -1 (Richtung des Mausrads)
        """
        self.selected_slot = (self.selected_slot + direction) % self.hotbar_size
    
    def toggle_open(self):
        """Öffnet oder schließt das Inventar-Fenster."""
        self.is_open = not self.is_open
    
    def get_slot_at_pos(self, mouse_pos, screen):
        """
        Findet heraus, welcher Slot an einer Bildschirm-Position ist.
        
        Berechnet die Position jedes Slots im Inventar-Fenster.
        
        :param mouse_pos: (x, y) Mausposition
        :param screen: Die pygame-Oberfläche (für Bildschirmgröße)
        :return: Slot-Index oder None
        """
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
        """
        Verarbeitet Mausklicks im Inventar-Fenster (Drag-and-Drop).
        
        Wenn kein Gegenstand gehalten wird: Nimm den angeklickten Gegenstand auf.
        Wenn ein Gegenstand gehalten wird: Lege ihn ab (stapeln, tauschen, etc.).
        
        :param mouse_pos: (x, y) Mausposition
        :param screen: Die pygame-Oberfläche
        """
        self.mouse_pos = mouse_pos
        slot_index = self.get_slot_at_pos(mouse_pos, screen)
        if slot_index is None:
            return

        target_slot = self.slots[slot_index]

        if self.held_item is None:
            # ----- Gegenstand aufnehmen -----
            if not target_slot.is_empty():
                self.held_item = target_slot.item
                self.held_count = target_slot.count
                self.held_durability = target_slot.durability
                self.held_origin_slot = slot_index
                # Slot leeren
                target_slot.item = None
                target_slot.count = 0
                target_slot.durability = None
        else:
            # ----- Gegenstand ablegen -----
            if target_slot.is_empty():
                # Einfach in den leeren Slot legen
                target_slot.item = self.held_item
                target_slot.count = self.held_count
                target_slot.durability = self.held_durability
                self.held_item = None
                self.held_count = 0
                self.held_durability = None
                self.held_origin_slot = None
            elif target_slot.item == self.held_item:
                # Gleicher Gegenstand → stapeln (so viel wie möglich)
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
                # Unterschiedliche Gegenstände → tauschen
                origin_slot = self.slots[self.held_origin_slot]
                (origin_slot.item, target_slot.item) = (target_slot.item, self.held_item)
                (origin_slot.count, target_slot.count) = (target_slot.count, self.held_count)
                (origin_slot.durability, target_slot.durability) = (target_slot.durability, self.held_durability)
                self.held_item = None
                self.held_count = 0
                self.held_durability = None
                self.held_origin_slot = None

    def swap_slots(self, slot1, slot2):
        """
        Vertauscht zwei Slots.
        
        :param slot1: Index des ersten Slots
        :param slot2: Index des zweiten Slots
        """
        if 0 <= slot1 < self.size and 0 <= slot2 < self.size:
            self.slots[slot1], self.slots[slot2] = self.slots[slot2], self.slots[slot1]
    
    def draw_hotbar(self, screen, asset_loader):
        """
        Zeichnet die Hotbar (die 9 Schnellzugriff-Slots unten auf dem Bildschirm).
        
        :param screen: Die pygame-Oberfläche
        :param asset_loader: Für die Item-Texturen
        """
        slot_size = 50
        padding = 4
        total_width = self.hotbar_size * (slot_size + padding) - padding
        start_x = (SCREEN_WIDTH - total_width) // 2
        start_y = screen.get_height() - slot_size - 10
        
        for i in range(self.hotbar_size):
            x = start_x + i * (slot_size + padding)
            slot = self.slots[i]
            
            # Ausgewählten Slot hervorheben (weißer Rahmen)
            if i == self.selected_slot:
                pygame.draw.rect(screen, (255, 255, 255), (x - 2, start_y - 2, slot_size + 4, slot_size + 4), 3)
            
            # Slot-Hintergrund
            pygame.draw.rect(screen, (50, 50, 50), (x, start_y, slot_size, slot_size))
            pygame.draw.rect(screen, (100, 100, 100), (x, start_y, slot_size, slot_size), 2)
            
            # Item im Slot zeichnen
            if not slot.is_empty():
                texture = asset_loader.get_item_texture(slot.item)
                if texture:
                    scaled = pygame.transform.scale(texture, (slot_size - 8, slot_size - 8))
                    screen.blit(scaled, (x + 4, start_y + 4))
                
                # Anzahl anzeigen (wenn > 1)
                if slot.count > 1:
                    font = pygame.font.Font(None, 20)
                    count_text = font.render(str(slot.count), True, (255, 255, 255))
                    screen.blit(count_text, (x + slot_size - 15, start_y + slot_size - 18))
                
                # Haltbarkeitsbalken anzeigen (für Werkzeuge)
                if slot.durability is not None and slot.item is not None:
                    props = ITEM_PROPERTIES.get(slot.item, {})
                    max_dur = props.get("durability", 100) or 100
                    dur_percent = slot.durability / max_dur
                    # Farbe: grün → gelb → rot (je nach Haltbarkeit)
                    dur_color = (255, int(255 * dur_percent), 0)
                    dur_width = int((slot_size - 8) * dur_percent)
                    pygame.draw.rect(screen, dur_color, (x + 4, start_y + slot_size - 6, dur_width, 3))
    
    def draw_full_inventory(self, screen, asset_loader):
        """
        Zeichnet das vollständige Inventar-Fenster (wenn is_open=True).
        
        :param screen: Die pygame-Oberfläche
        :param asset_loader: Für die Item-Texturen
        """
        if not self.is_open:
            return

        # Halbtransparenter Hintergrund
        overlay = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        slot_size = 50
        padding = 4
        cols = 9
        rows = self.size // cols

        # Position des Inventar-Fensters (zentriert)
        total_width = cols * (slot_size + padding) - padding
        total_height = rows * (slot_size + padding) - padding
        start_x = (screen.get_width() - total_width) // 2
        start_y = (screen.get_height() - total_height) // 2

        # Hintergrund-Rechteck
        bg_rect = pygame.Rect(start_x - 20, start_y - 60, total_width + 40, total_height + 100)
        pygame.draw.rect(screen, (60, 60, 60), bg_rect)
        pygame.draw.rect(screen, (100, 100, 100), bg_rect, 3)

        # Titel
        font = pygame.font.Font(None, 36)
        title = font.render("Inventory", True, (255, 255, 255))
        screen.blit(title, (start_x, start_y - 45))

        # Slots zeichnen
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

        # Gehaltenen Gegenstand an Mausposition zeichnen
        if self.held_item is not None:
            texture = asset_loader.get_item_texture(self.held_item)
            if texture:
                scaled = pygame.transform.scale(texture, (40, 40))
                mx, my = self.mouse_pos
                screen.blit(scaled, (mx - 20, my - 20))
    
    def get_save_data(self):
        """
        Gibt den Inventar-Zustand als Liste zurück (zum Speichern).
        
        :return: Liste von Dictionaries oder None (für leere Slots)
        """
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
        """
        Stellt das Inventar aus gespeicherten Daten wieder her.
        
        :param data: Liste aus get_save_data()
        """
        for i, slot_data in enumerate(data):
            if i >= self.size:
                break
            if slot_data is None:
                self.slots[i] = InventorySlot()
            else:
                self.slots[i].item = slot_data["item"]
                self.slots[i].count = slot_data["count"]
                self.slots[i].durability = slot_data.get("durability")