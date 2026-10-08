"""Temporäres Splice-Skript: entfernt pygame-Methoden aus inventory.py."""
from pathlib import Path

p = Path(__file__).parent / "utils" / "inventory.py"
lines = p.read_text(encoding="utf-8").splitlines(keepends=True)


def find(prefix, start=0):
    for i in range(start, len(lines)):
        if lines[i].startswith(prefix):
            return i
    raise SystemExit(f"nicht gefunden: {prefix!r}")


# --- Region 1: get_slot_at_pos + handle_mouse_click ersetzen -------------
a = find("    def get_slot_at_pos")
b = find("    def swap_slots")
new_method = '''    def handle_slot_click(self, slot_index):
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

'''
lines[a:b] = [new_method]

# --- Region 2: draw_hotbar + draw_full_inventory entfernen ---------------
a = find("    def draw_hotbar")
b = find("    def get_save_data")
lines[a:b] = ["\n"]

p.write_text("".join(lines), encoding="utf-8")
print("OK: inventory.py gespliced")