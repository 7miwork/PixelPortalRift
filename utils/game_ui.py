"""
utils/game_ui.py – Ursina-Benutzeroberfläche (Phase 3: Inventar & Crafting)
=============================================================================

Klasse             Aufgabe
------------------ --------------------------------------------------------
IconLibrary        Texturen für Items/Blöcke (Block-PNG > prozedural > Farbe)
SlotUI             Ein Slot: Hintergrund, Icon, Anzahl, Auswahlrahmen
HotbarUI           9 Slots unten auf dem Bildschirm (Tasten 1-9, Mausrad)
InventoryPanel     Voll-Inventar (36 Slots) mit Drag-and-Drop (Taste E)
CraftingPanel      Rezeptliste, Klick = herstellen (Taste C)
GameUI             Fassade: Tastenrouting, Maus-Lock, Nachrichten, Refresh

Warum diese Datei?
------------------
inventory.py und crafting.py sind reine Spiellogik (kein pygame mehr).
Diese Datei übernimmt die DARSTELLUNG mit Ursina-Entities (parent=camera.ui)
und übersetzt Klicks zurück in die Logik-Aufrufe (handle_slot_click /
craft_selected). Das 2D-Layout des Originals bleibt erhalten: Hotbar unten,
Inventar als 9x4-Raster in der Mitte, Crafting mit Icon + Name + Zutaten
pro Zeile.

Koordinaten (camera.ui): (0,0) = Bildschirmmitte, y von -0.5 bis +0.5
(unten/oben), x von -aspect/2 bis +aspect/2 – identisch zu mouse.x/mouse.y.
Ein Quad mit scale s ist s * Bildschirmhöhe groß. Kind-Entities werden NIE
in einem non-uniform skalierten Parent gehängt (sonst verzerrt sich Text).
"""

import os

import pygame                    # nur fürs Icon-Zeichnen (asset_loader)
from PIL import Image
from panda3d.core import Texture as PTexture
from ursina import Entity, Text, Texture, camera, color, invoke, mouse

from utils.asset_loader import AssetLoader
from utils.constants import BLOCK_PROPERTIES, ITEM_PROPERTIES

# ---- Layout-Konstanten (Bruchteile der Bildschirmhöhe) --------------------
SLOT = 0.052                # Kantenlänge eines Slots
SLOT_GAP = 0.006            # Abstand zwischen Slots
HOTBAR_Y = -0.415           # y-Mitte der Hotbar-Reihe
INV_ROWS = 4
CRAFT_ROWS = 7              # sichtbare Rezeptzeilen (wie im 2D-Original)
CRAFT_ROW_H = 0.085

# Neutrale weiße Textur: Icon-Entities behalten immer eine Textur und werden
# per color moduliert (vermeidet texture=None beim Umschalten).
_WHITE = Texture(Image.new("RGBA", (1, 1), (255, 255, 255, 255)))


def _nearest(tex):
    """Pixel-Look: harte Kanten statt Weichzeichner."""
    try:
        tex.set_minfilter(PTexture.FT_nearest)
        tex.set_magfilter(PTexture.FT_nearest)
    except Exception:
        pass
    return tex


def _surface_to_texture(surf):
    """pygame-Surface → Ursina-Textur (RGBA, zeilenweise wie PIL)."""
    to_bytes = getattr(pygame.image, "tobytes", None) or pygame.image.tostring
    data = to_bytes(surf, "RGBA", False)          # flipped=False: oben = Zeile 0
    return _nearest(Texture(Image.frombytes("RGBA", surf.get_size(), data)))


class IconLibrary:
    """Liefert pro Item-Name eine (Textur, Farbe) – gecacht.

    Reihenfolge: Block-PNG (passt zur sichtbaren Welt) > prozedurale
    Item-Zeichnung (asset_loader, wie im 2D-Spiel) > BLOCK_PROPERTIES-Farbe
    > grau. pygame wird nur fürs einmalige Zeichnen der Icons gebraucht.
    """

    def __init__(self):
        self._loader = AssetLoader()
        self._loader.load_item_textures()   # zeichnet alle Item-Icons einmalig
        self._cache = {}

    def get(self, name):
        if name in self._cache:
            return self._cache[name]

        tex, col = None, None
        png = os.path.join("assets", "blocks", f"{name}.png")
        if name in BLOCK_PROPERTIES:
            if os.path.exists(png):
                tex = _nearest(Texture(png))
            else:
                rgb = BLOCK_PROPERTIES[name].get("color")
                if rgb:
                    col = color.rgba(rgb[0] / 255, rgb[1] / 255,
                                     rgb[2] / 255, 1)
        else:
            surf = self._loader.get_item_texture(name)
            if surf is not None:
                tex = _surface_to_texture(surf)

        if tex is None and col is None:
            col = color.rgba(0.6, 0.6, 0.6, 1)
        self._cache[name] = (tex, col)
        return tex, col


class SlotUI(Entity):
    """Ein einzelner Slot (Container ohne eigenes Modell, scale 1).

    Kind-Entity-Reihenfolge = Zeichenreihenfolge: Auswahlrahmen, Hintergrund,
    Icon, Anzahl-Text, Haltbarkeitsbalken.
    """

    def __init__(self, parent, position, size, icons, on_click=None):
        super().__init__(parent=parent, position=position)
        self.icons = icons
        self.size = size
        s = size
        self.highlight = Entity(
            parent=self, model="quad", scale=s * 1.18,
            color=color.rgba(1, 1, 1, 0.95), enabled=False)
        self.bg = Entity(
            parent=self, model="quad", scale=s,
            color=color.rgba(0.16, 0.16, 0.16, 0.95),
            collider="box" if on_click else None)
        if on_click:
            self.bg.on_click = on_click
        self.icon = Entity(parent=self, model="quad", scale=s * 0.78)
        self.count = Text(
            parent=self, text="", origin=(0.5, -0.5), scale=0.42,
            position=(s / 2 - 0.006, -s / 2 + 0.006), color=color.white)
        # Haltbarkeitsbalken (wie im 2D-Original: nur in der Hotbar)
        self.dur_bg = Entity(
            parent=self, model="quad", scale=(s * 0.8, 0.005),
            position=(0, -s * 0.36), color=color.rgba(0, 0, 0, 0.8),
            enabled=False)
        self.dur_fg = Entity(
            parent=self, model="quad", scale=(s * 0.8, 0.005),
            position=(0, -s * 0.36), color=color.green, enabled=False)

    def paint(self, slot, selected=False, show_durability=True):
        """Slot-Visuals aus einem InventorySlot-Objekt neu zeichnen."""
        self.highlight.enabled = selected
        if slot is None or slot.is_empty():
            self.icon.enabled = False
            self.count.text = ""
            self.dur_bg.enabled = False
            self.dur_fg.enabled = False
            return

        tex, col = self.icons.get(slot.item)
        self.icon.enabled = True
        if tex is not None:
            self.icon.texture = tex
            self.icon.color = color.white
        else:
            self.icon.texture = _WHITE
            self.icon.color = col
        self.count.text = str(slot.count) if slot.count > 1 else ""

        max_dur = ITEM_PROPERTIES.get(slot.item, {}).get("durability")
        if show_durability and slot.durability is not None and max_dur:
            frac = max(0.0, min(1.0, slot.durability / max_dur))
            self.dur_bg.enabled = True
            self.dur_fg.enabled = True
            bar_w = self.size * 0.8
            self.dur_fg.scale = (bar_w * frac, 0.005)
            # links verankert: Mitte verschiebt sich mit der Breite
            self.dur_fg.x = -bar_w / 2 + (bar_w * frac) / 2
            # grün (voll) → rot (leer)
            self.dur_fg.color = color.rgba(1 - frac, frac, 0, 1)
        else:
            self.dur_bg.enabled = False
            self.dur_fg.enabled = False


class HotbarUI(Entity):
    """Die 9 Hotbar-Slots unten auf dem Bildschirm (immer sichtbar).

    Die Slots zeigen inventory.slots[0..8]; der ausgewählte Slot bekommt
    einen weißen Rahmen. Mausklick wählt den Slot (wie Minecraft).
    """

    def __init__(self, parent, inventory, icons, on_change=None):
        super().__init__(parent=parent)
        self.inventory = inventory
        self.on_change = on_change
        n = inventory.hotbar_size
        total = n * SLOT + (n - 1) * SLOT_GAP
        self.slots = []
        for i in range(n):
            x = -total / 2 + SLOT / 2 + i * (SLOT + SLOT_GAP)
            slot = SlotUI(self, (x, HOTBAR_Y), SLOT, icons,
                          on_click=lambda i=i: self._click(i))
            self.slots.append(slot)
        self.refresh()

    def _click(self, index):
        """Slot per Mausklick auswählen (zusätzlich zu Tasten 1-9)."""
        self.inventory.select_slot(index)
        if self.on_change is not None:
            self.on_change()

    def refresh(self):
        """Visuals aus dem Inventar neu zeichnen (günstig: nur bei Änderung)."""
        sel = self.inventory.selected_slot
        for i, view in enumerate(self.slots):
            if i < len(self.inventory.slots):
                view.paint(self.inventory.slots[i],
                           selected=(i == sel), show_durability=True)


class InventoryPanel(Entity):
    """Das Voll-Inventar (9x4 Slots), Taste E öffnet/schließt.

    Drag-and-Drop wie im Original: Klick nimmt den ganzen Stapel auf,
    zweiter Klick legt ab/stapelt/tauscht (Logik in handle_slot_click).
    Der gehaltene Gegenstand folgt der Maus. Beim Schließen wird der
    gehaltene Gegenstand automatisch zurückgelegt (return_held).
    """

    def __init__(self, parent, inventory, icons, on_change=None):
        super().__init__(parent=parent, enabled=False)
        self.inventory = inventory
        self.icons = icons
        self.on_change = on_change

        # Abdunkelnder Hintergrund über dem gesamten Bildschirm
        Entity(parent=self, model="quad", scale=(4, 3),
               color=color.rgba(0, 0, 0, 0.55))

        # Panel (Titel + Raster), zentriert
        self.panel = Entity(parent=self, model="quad",
                            scale=(9 * (SLOT + SLOT_GAP) + 0.06,
                                   INV_ROWS * (SLOT + SLOT_GAP) + 0.14),
                            color=color.rgba(0.12, 0.12, 0.12, 0.97))
        self.title = Text(parent=self, text="Inventar",
                          origin=(0, 0), scale=0.7, y=0.135,
                          color=color.white)

        grid_w = 9 * (SLOT + SLOT_GAP) - SLOT_GAP
        grid_h = INV_ROWS * (SLOT + SLOT_GAP) - SLOT_GAP
        self.slots = []
        for i in range(inventory.size):
            row, col_idx = divmod(i, 9)
            x = -grid_w / 2 + SLOT / 2 + col_idx * (SLOT + SLOT_GAP)
            y = grid_h / 2 - SLOT / 2 - row * (SLOT + SLOT_GAP) - 0.03
            self.slots.append(SlotUI(self, (x, y), SLOT, icons,
                                     on_click=lambda i=i: self._click(i)))

        # Gehaltener Gegenstand folgt der Maus
        self.held_icon = Entity(parent=self, model="quad",
                                scale=SLOT * 0.8, enabled=False)
        self.held_count = Text(parent=self, text="", origin=(0, 0),
                               scale=0.45, color=color.white, enabled=False)

        self.refresh()

    def _click(self, index):
        """Klick auf einen Slot → Logik in inventory.handle_slot_click."""
        self.inventory.handle_slot_click(index)
        if self.on_change is not None:
            self.on_change()
        else:
            self.refresh()

    def open(self):
        self.enabled = True
        self.refresh()

    def close(self):
        # Gehaltenes zurücklegen, damit nichts verloren geht
        self.inventory.return_held()
        self.enabled = False
        self.refresh()

    def refresh(self):
        """Slot-Visuals + gehaltenen Gegenstand neu zeichnen."""
        for i, view in enumerate(self.slots):
            if i < len(self.inventory.slots):
                view.paint(self.inventory.slots[i],
                           selected=False, show_durability=False)

        held = self.inventory.held_item
        self.held_icon.enabled = held is not None
        self.held_count.enabled = held is not None
        if held is not None:
            tex, col = self.icons.get(held)
            if tex is not None:
                self.held_icon.texture = tex
                self.held_icon.color = color.white
            else:
                self.held_icon.texture = _WHITE
                self.held_icon.color = col
            self.held_count.text = str(self.inventory.held_count) \
                if self.inventory.held_count > 1 else ""

    def update(self):
        """Gehaltenen Gegenstand an die Mausposition ziehen."""
        if self.enabled and self.inventory.held_item is not None:
            self.held_icon.position = (mouse.x, mouse.y, -0.1)
            self.held_count.position = (mouse.x + 0.02, mouse.y - 0.02, -0.1)


class CraftingPanel(Entity):
    """Rezeptliste, Taste C öffnet/schließt.

    Jede Zeile: Rezept-Icon, Name, Ergebnis 'xN', Zutaten mit
    'haben/Brauchen' (grün = genug, rot = fehlt). Klick = Rezept auswählen
    und herstellen (craft_selected); Mausrad blättert durch die Rezeptliste
    (CraftingSystem). Fehlende Zutaten bleiben beim Rezept sichtbar, damit
    man es trotzdem noch auswählen kann.
    """

    def __init__(self, parent, crafting, inventory, icons,
                 on_result=None, on_change=None):
        super().__init__(parent=parent, enabled=False)
        self.crafting = crafting
        self.inventory = inventory
        self.icons = icons
        self.on_result = on_result
        self.on_change = on_change

        Entity(parent=self, model="quad", scale=(4, 3),
               color=color.rgba(0, 0, 0, 0.55))
        self.panel = Entity(parent=self, model="quad",
                            scale=(1.10, 1.05),
                            color=color.rgba(0.12, 0.12, 0.12, 0.97))
        self.title = Text(parent=self, text="Fertigen",
                          origin=(0, 0), scale=0.75, y=0.38,
                          color=color.white)

        row_y = 0.30
        self.rows = []
        self.row_content = []
        for i in range(CRAFT_ROWS):
            row_ent = Entity(parent=self, position=(0, row_y),
                             model="quad", scale=(0.88, CRAFT_ROW_H),
                             color=color.rgba(0.28, 0.28, 0.32, 1),
                             collider="box")
            row_ent.on_click = lambda i=i: self._click(i)
            self.rows.append(row_ent)
            self.row_content.append([])
            row_y -= CRAFT_ROW_H + 0.010

        self.scrollbar_track = Entity(parent=self, model="quad",
                                      scale=(0.010, 0.55),
                                      position=(0.5, 0),
                                      color=color.rgba(0.4, 0.4, 0.4, 0.9))
        self.scrollbar_thumb = Entity(parent=self, model="quad",
                                      scale=(0.010, 0.08),
                                      position=(0.5, 0.275),
                                      color=color.rgba(0.7, 0.7, 0.7, 0.9),
                                      enabled=False)

        self.footer = Text(parent=self, text="Klick = herstellen | "
                                         "Mausrad = blättern | C = schliessen",
                           origin=(0, 0), scale=0.42, y=-0.44,
                           color=color.rgba(0.8, 0.8, 0.8, 0.9))

    def _click(self, row_index):
        """Mausklick auf eine Rezeptzeile → craft_selected."""
        crafting = self.crafting
        idx = row_index + crafting.scroll_offset
        if not (0 <= idx < len(crafting.craftable_recipes)):
            return
        crafting.select_recipe(row_index)
        recipe_name = crafting.craftable_recipes[idx][0]
        ok = crafting.craft_selected(self.inventory)
        self.refresh()
        if ok:
            if self.on_result is not None:
                self.on_result(f"{recipe_name} hergestellt")
        elif self.on_result is not None:
            self.on_result("Zutaten fehlen oder Inventar ist voll")
        if self.on_change is not None:
            self.on_change()

    def _paint_row(self, i):
        """Pinsel für Zeile i: Hintergrund, Icon, Name, Zutaten."""
        crafting = self.crafting
        idx = i + crafting.scroll_offset
        row = self.rows[i]
        for child in self.row_content[i]:
            child.destroy()
        self.row_content[i].clear()
        can = crafting.craftable_recipes
        if not (0 <= idx < len(can)):
            row.enabled = False
            row.color = color.rgba(0, 0, 0, 0)
            return

        recipe_name, recipe_data = can[idx][:2]
        selected = (idx == crafting.selected_recipe)
        row.enabled = True
        row.color = color.rgba(0.35, 0.35, 0.45, 1) if not selected \
            else color.rgba(0.45, 0.45, 0.6, 1)

        # Icon
        tex, col = self.icons.get(recipe_name)
        icon = Entity(parent=row, model="quad", scale=(0.045, 0.045),
                      x=-0.40)
        self.row_content[i].append(icon)
        if tex is not None:
            icon.texture = tex
            icon.color = color.white
        else:
            icon.texture = _WHITE
            icon.color = col

        # Name + Ergebnis
        name_text = Text(parent=row, text=recipe_name, origin=(-0.5, 0),
                         x=-0.36, y=0.012, scale=0.42,
                         color=color.white)
        self.row_content[i].append(name_text)
        result = recipe_data.get("result_count", 1)
        if result > 1:
            result_text = Text(parent=row, text="x%d" % result,
                               origin=(0.5, -0.5), x=-0.36, y=-0.012,
                               scale=0.30, color=color.rgba(0.8, 0.8, 0.8, 0.8))
            self.row_content[i].append(result_text)

        # Zutaten (CraftingSystem: ingredients = dict Name → Anzahl)
        for j, (ing_name, need) in enumerate(
                recipe_data.get("ingredients", {}).items()):
            if j >= 4:
                break
            have = self.inventory.count_item(ing_name)
            ok = have >= need
            ingredient_text = Text(
                parent=row, text="%s: %d/%d" % (ing_name, have, need),
                origin=(-0.5, 0), x=-0.08, y=0.012 - j * 0.016,
                scale=0.34, color=color.green if ok else color.red,
            )
            self.row_content[i].append(ingredient_text)

        if selected:
            row.color = color.rgba(0.45, 0.45, 0.6, 1)

    def open(self):
        self.enabled = True

    def close(self):
        self.enabled = False


    def refresh(self):
        """Rezeptliste neu zeichnen (auch bei geöffnetem Crafting)."""
        crafting = self.crafting
        crafting.update_craftable(self.inventory)  # auch beim Öffnen
        for i in range(CRAFT_ROWS):
            self._paint_row(i)

        n = len(crafting.craftable_recipes)
        if n > CRAFT_ROWS:
            self.scrollbar_thumb.enabled = True
            frac = (crafting.scroll_offset + 1) / n
            thumb_h = CRAFT_ROWS / n
            self.scrollbar_thumb.scale = (0.010, thumb_h)
            self.scrollbar_thumb.y = 0.275 - (frac * (0.55 - 0.08)) / 2
        else:
            self.scrollbar_thumb.enabled = False


class GameUI(Entity):
    """Oberfläche über alles: Tasten, Maus-Lock, Nachrichten, Refresh.

    Bleibt immer im Szenenbaum (parent=camera.ui), damit die UI-Entities
    genau im Ursina-Raum liegen und Mausklicks/Kollisionserkennung sauber
    funktionieren. Der Spieler und der HUD-Crosshair werden von außen
    (main.py) mitgegeben, damit das Pink-Cursor-Diamond beim Menü-Open
    ausgeblendet werden kann.
    """

    def __init__(self, inventory, crafting, player=None, crosshair=None):
        super().__init__(parent=camera.ui, name='game_ui')
        self.inventory = inventory
        self.crafting = crafting
        self.player = player
        self.crosshair = crosshair
        self.icons = IconLibrary()
        self.message = Text(parent=camera.ui, origin=(0, 0), scale=0.6,
                            position=(0, 0.315), text='')
        self._msg_token = 0

        # Oberflächen
        self.hotbar = HotbarUI(
            self, inventory, self.icons, on_change=self.refresh,
        )
        self.inventory_panel = InventoryPanel(
            self, inventory, self.icons, on_change=self.refresh,
        )
        self.crafting_panel = CraftingPanel(
            self, crafting, inventory, self.icons,
            on_result=self.show_message, on_change=self.refresh,
        )
        self._sync()

    # ------------------------------------------------------------------
    @property
    def any_open(self):
        return self.inventory_panel.enabled or self.crafting_panel.enabled

    # ------------------------------------------------------------------
    def handle_key(self, key):
        """Liefert True, wenn der Tastendruck verarbeitet wurde."""
        if key == 'escape':
            if self._close_top():
                self._sync()
            return True
        if key == 'e':
            self._toggle_inventory()
            return True
        if key == 'c':
            self._toggle_crafting()
            return True
        if key in ('scroll up', 'scroll down'):
            self._scroll(key)
            return True
        if isinstance(key, str) and len(key) == 1 and key.isdigit():
            self.inventory.select_slot(int(key) - 1)
            self.hotbar.refresh()
            return True
        return False

    def refresh(self):
        """Synchronize inventory visuals after gameplay or UI changes."""
        self.hotbar.refresh()
        if self.inventory_panel.enabled:
            self.inventory_panel.refresh()
        if self.crafting_panel.enabled:
            self.crafting_panel.refresh()

    def _scroll(self, key):
        if self.crafting_panel.enabled:
            self.crafting.scroll(1 if key == 'scroll down' else -1)
            self.crafting_panel.refresh()
        else:
            self.inventory.scroll_selection(-1 if key == 'scroll up' else 1)
        self.hotbar.refresh()

    def _sync(self):
        """Maus-Lock & player.Controls disabled, solange Menü geöffnet ist."""
        self.inventory_panel.enabled = self.inventory.is_open
        self.crafting_panel.enabled = self.crafting.is_open
        any_open = self.any_open
        mouse.locked = not any_open
        if self.player is not None:
            self.player.controls_enabled = not any_open
            if hasattr(self.player, 'cursor'):
                self.player.cursor.enabled = not any_open
        if self.crosshair is not None:
            self.crosshair.enabled = not any_open
        self.refresh()

    def _toggle_inventory(self):
        if self.inventory.is_open:
            self.inventory.return_held()
            self.inventory.is_open = False
        else:
            self.crafting.is_open = False
            self.inventory.is_open = True
        self._sync()

    def _toggle_crafting(self):
        if self.crafting.is_open:
            self.crafting.is_open = False
        else:
            self.crafting.toggle_open(self.inventory)   # is_open + update
            self.inventory.return_held()
            self.inventory.is_open = False
        self._sync()

    def _close_top(self):
        if self.crafting.is_open:
            self.crafting.is_open = False
            return True
        if self.inventory.is_open:
            self.inventory.return_held()
            self.inventory.is_open = False
            return True
        return False

    def show_message(self, text):
        self.message.text = text
        self._msg_token += 1
        self._msg_token_current = self._msg_token
        invoke(self._clear_message, self._msg_token, delay=2.5)

    def _clear_message(self, token):
        if token == self._msg_token:
            self.message.text = ''


#@@TEIL9@@