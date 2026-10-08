"""
utils/inventory.py – Inventar-Verwaltung
=========================================

Dieses Modul verwaltet das gesamte Inventar des Spielers.
Es enthält zwei Klassen:
- InventorySlot: Ein einzelner Slot im Inventar (kann einen Gegenstand halten)
- Inventory: Das gesamte Inventar (alle Slots + Hotbar + Drag-and-Drop)

Das Inventar hat 36 Slots, davon 9 in der Hotbar (schnell erreichbar).
Gegenstände können gestapelt werden (stackable), wenn sie denselben Typ haben.

WICHTIG: Dieses Modul ist reine Spiellogik – KEIN pygame. Die Darstellung
(Hotbar, Inventar-Fenster, Mauszeiger) übernimmt die Ursina-UI in
utils/game_ui.py. Die Drag-and-Drop-Semantik bleibt hier (handle_slot_click),
damit sie ohne Fenster testbar ist.
"""

from utils.constants import ITEM_PROPERTIES


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
            props = ITEM_PROPERTIES.get(
                item_name, {"stackable": True, "max_stack": 64})
            capacity = props.get("max_stack", 64) if props.get(
                "stackable", True) else 1
            to_add = min(count, capacity)
            self.item = item_name
            self.count = to_add
            if durability is not None:
                self.durability = durability
            elif props.get("durability"):
                self.durability = props["durability"]
            return count - to_add
        
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
            if not slot.is_empty() and slot.item == item_name:
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
    
    def handle_slot_click(self, slot_index):
        """
        Verarbeitet einen Klick auf einen Slot (Drag-and-Drop).

        Die UI (utils/game_ui.py) liefert nur den Slot-Index; die Semantik
        bleibt exakt wie im 2D-Original:

        - Kein Gegenstand gehalten → Gegenstand aus dem Slot aufnehmen
        - Gegenstand gehalten + Slot leer → komplett ablegen
        - Gegenstand gehalten + gleicher Typ → stapeln (max. max_stack)
        - Gegenstand gehalten + anderer Typ → mit dem Herkunfts-Slot tauschen

        :param slot_index: Index des angeklickten Slots (0..size-1)
        """
        if not 0 <= slot_index < self.size:
            return
        target_slot = self.slots[slot_index]

        if self.held_item is None:
            # ----- Gegenstand aufnehmen -----
            if not target_slot.is_empty():
                self.held_item = target_slot.item
                self.held_count = target_slot.count
                self.held_durability = target_slot.durability
                self.held_origin_slot = slot_index
                target_slot.item = None
                target_slot.count = 0
                target_slot.durability = None
            return

        # ----- Gegenstand ablegen -----
        if target_slot.is_empty():
            # Einfach in den leeren Slot legen
            target_slot.item = self.held_item
            target_slot.count = self.held_count
            target_slot.durability = self.held_durability
            self._clear_held()
        elif target_slot.item == self.held_item:
            # Gleicher Gegenstand → stapeln (so viel wie möglich)
            props = ITEM_PROPERTIES.get(
                self.held_item, {"stackable": True, "max_stack": 64})
            max_stack = props.get("max_stack", 64)
            space = max_stack - target_slot.count
            to_move = min(self.held_count, space)
            target_slot.count += to_move
            self.held_count -= to_move
            if self.held_count <= 0:
                self._clear_held()
        elif self.held_origin_slot is not None:
            # Unterschiedliche Gegenstände → mit Herkunftsslot tauschen
            origin_slot = self.slots[self.held_origin_slot]
            (origin_slot.item, target_slot.item) = (target_slot.item, self.held_item)
            (origin_slot.count, target_slot.count) = (target_slot.count, self.held_count)
            (origin_slot.durability, target_slot.durability) = (
                target_slot.durability, self.held_durability)
            self._clear_held()
        else:
            # Kein Herkunftsslot bekannt → nicht tauschen (Sicherheit)
            self._clear_held()

    def return_held(self):
        """
        Legt einen gehaltenen Gegenstand zurück ins Inventar.

        Wird beim Schließen des Inventars aufgerufen, damit nichts
        verloren geht. Versucht zuerst den Herkunfts-Slot, dann freie
        Slots über add_item().

        :return: True wenn der Gegenstand vollständig zurücklagert
        """
        if self.held_item is None:
            return True
        item, count, dur = self.held_item, self.held_count, self.held_durability

        # Versuch 1: Herkunfts-Slot (noch leer oder gleicher Typ)
        if self.held_origin_slot is not None:
            origin = self.slots[self.held_origin_slot]
            if origin.is_empty():
                origin.item, origin.count, origin.durability = item, count, dur
                self._clear_held()
                return True
            if origin.item == item and origin.can_add(item, count):
                origin.add(item, count, dur)
                self._clear_held()
                return True

        # Versuch 2: normale Ablage
        remaining = self.add_item(item, count, dur)
        if remaining <= 0:
            self._clear_held()
            return True
        self.held_count = remaining
        return False

    def _clear_held(self):
        """Setzt den Drag-and-Drop-Zustand zurück."""
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