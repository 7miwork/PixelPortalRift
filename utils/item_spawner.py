"""
utils/item_spawner.py – Verstecktes Entwickler-Menü zum Spawnen von Items
===========================================================================

Dieses Modul enthält das ItemSpawnerMenu, ein verstecktes Menü, mit dem man
sich beliebige Gegenstände direkt ins Inventar geben kann.

WICHTIG: Dieses Menü ist absichtlich VERSTECKT und nur für den Entwickler/
Lehrer bestimmt. Es ist NICHT im normalen Hilfe-Menü (Taste H) aufgeführt,
damit Spieler nicht zufällig darauf stoßen.

Die Tastenkombination zum Öffnen/Schließen lautet:
    Strg + Umschalt + K  (Ctrl + Shift + K)

Alle Items aus ITEM_PROPERTIES werden in einem Raster angezeigt.
Ein Klick gibt 10 Stück des jeweiligen Items ins Inventar.
"""

import pygame
from utils.constants import ITEM_PROPERTIES, SCREEN_WIDTH, SCREEN_HEIGHT


class ItemSpawnerMenu:
    """
    Das versteckte Item-Spawner-Menü für Entwickler/Testzwecke.
    
    Wichtige Attribute:
        is_open:      Ist das Menü aktuell geöffnet?
        cols:         Anzahl Spalten im Item-Raster
        slot_size:    Größe jedes Item-Slots in Pixeln
        padding:      Abstand zwischen den Slots
        mouse_pos:    Aktuelle Mausposition (für Klick-Erkennung)
    """
    
    def __init__(self):
        """Initialisiert das Menü (standardmäßig geschlossen)."""
        self.is_open = False
        self.cols = 6                # 6 Spalten im Raster
        self.slot_size = 60          # Jeder Slot ist 60x60 Pixel
        self.padding = 8             # 8 Pixel Abstand zwischen Slots
        self.mouse_pos = (0, 0)
    
    def toggle_open(self, inventory=None):
        """
        Öffnet oder schließt das Menü.
        
        Wenn es geöffnet wird, werden andere Menüs (Inventar, Crafting)
        automatisch geschlossen, damit sie sich nicht überlappen.
        
        :param inventory: Das Inventar des Spielers (wird aktuell nicht benötigt,
                         aber als Parameter für spätere Erweiterungen vorgesehen)
        """
        self.is_open = not self.is_open
    
    def close(self):
        """Schließt das Menü explizit."""
        self.is_open = False
    
    def update_mouse_pos(self, mouse_pos):
        """
        Aktualisiert die gespeicherte Mausposition.
        
        Wird jedes Frame aus main.py aufgerufen, damit Klicks korrekt
        erkannt werden.
        
        :param mouse_pos: (x, y) der aktuellen Mausposition
        """
        self.mouse_pos = mouse_pos
    
    def get_slot_at_pos(self, mouse_pos):
        """
        Findet heraus, welcher Item-Slot an einer Bildschirm-Position ist.
        
        Berechnet die Position jedes Slots im Menü und prüft, ob die
        Mausposition innerhalb eines Slots liegt.
        
        :param mouse_pos: (x, y) Mausposition
        :return: Item-Name oder None (wenn kein Slot getroffen wurde)
        """
        mx, my = mouse_pos
        
        # Alle Items aus ITEM_PROPERTIES sammeln
        item_names = list(ITEM_PROPERTIES.keys())
        
        # Größe des gesamten Menüs berechnen
        total_width = self.cols * (self.slot_size + self.padding) - self.padding
        rows = (len(item_names) + self.cols - 1) // self.cols  # Aufrunden
        total_height = rows * (self.slot_size + self.padding) - self.padding
        
        # Menü zentriert auf dem Bildschirm
        start_x = (SCREEN_WIDTH - total_width) // 2
        start_y = (SCREEN_HEIGHT - total_height) // 2
        
        # Prüfen, welcher Slot getroffen wurde
        for i, item_name in enumerate(item_names):
            row = i // self.cols
            col = i % self.cols
            x = start_x + col * (self.slot_size + self.padding)
            y = start_y + row * (self.slot_size + self.padding)
            
            if x <= mx <= x + self.slot_size and y <= my <= y + self.slot_size:
                return item_name
        
        return None
    
    def handle_click(self, mouse_pos, inventory, show_message_callback):
        """
        Verarbeitet Mausklicks im Menü.
        
        Wenn ein Item angeklickt wird, werden 10 Stück davon ins Inventar gelegt
        und eine Bestätigungsnachricht angezeigt.
        
        :param mouse_pos: (x, y) Mausposition des Klicks
        :param inventory: Das Inventar des Spielers
        :param show_message_callback: Funktion, um eine Nachricht anzuzeigen
                                      (z.B. game.show_message)
        :return: True wenn ein Item gespawnt wurde, sonst False
        """
        if not self.is_open:
            return False
        
        item_name = self.get_slot_at_pos(mouse_pos)
        if item_name:
            # 10 Stück des Items ins Inventar legen
            # HINWEIS: Die Anzahl 10 kann hier leicht angepasst werden,
            # falls man lieber eine andere Menge spawnen möchte.
            inventory.add_item(item_name, count=10)
            
            # Bestätigungsnachricht anzeigen (wie bei anderen Aktionen im Spiel)
            if show_message_callback:
                show_message_callback(f"{item_name} x10 erhalten!")
            
            return True
        
        return False
    
    def draw(self, screen, asset_loader):
        """
        Zeichnet das Item-Spawner-Menü auf den Bildschirm.
        
        Das Menü zeigt ein Raster aller Items aus ITEM_PROPERTIES.
        Jeder Slot enthält:
        - Die Item-Textur (wenn vorhanden)
        - Den Item-Namen als Text darunter
        
        :param screen: Die pygame-Oberfläche
        :param asset_loader: Für die Item-Texturen
        """
        if not self.is_open:
            return
        
        # Halbtransparenter Hintergrund über den gesamten Bildschirm
        overlay = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        # Alle Items sammeln
        item_names = list(ITEM_PROPERTIES.keys())
        
        # Menügröße berechnen
        total_width = self.cols * (self.slot_size + self.padding) - self.padding
        rows = (len(item_names) + self.cols - 1) // self.cols
        total_height = rows * (self.slot_size + self.padding) - self.padding
        
        # Menü zentriert positionieren
        start_x = (SCREEN_WIDTH - total_width) // 2
        start_y = (SCREEN_HEIGHT - total_height) // 2
        
        # Hintergrund-Rechteck für das Menü
        bg_rect = pygame.Rect(start_x - 20, start_y - 60, total_width + 40, total_height + 100)
        pygame.draw.rect(screen, (60, 60, 60), bg_rect)
        pygame.draw.rect(screen, (100, 100, 100), bg_rect, 3)
        
        # Titel
        font = pygame.font.Font(None, 40)
        title = font.render("Item Spawner (DEBUG)", True, (255, 255, 255))
        screen.blit(title, (start_x, start_y - 45))
        
        # Slots zeichnen
        for i, item_name in enumerate(item_names):
            row = i // self.cols
            col = i % self.cols
            x = start_x + col * (self.slot_size + self.padding)
            y = start_y + row * (self.slot_size + self.padding)
            
            # Slot-Hintergrund
            pygame.draw.rect(screen, (40, 40, 40), (x, y, self.slot_size, self.slot_size))
            pygame.draw.rect(screen, (80, 80, 80), (x, y, self.slot_size, self.slot_size), 2)
            
            # Item-Textur laden und zeichnen
            texture = asset_loader.get_item_texture(item_name)
            if texture:
                scaled = pygame.transform.scale(texture, (self.slot_size - 8, self.slot_size - 20))
                screen.blit(scaled, (x + 4, y + 4))
            
            # Item-Name unter der Textur anzeigen
            name_font = pygame.font.Font(None, 18)
            name_text = name_font.render(item_name, True, (200, 200, 200))
            text_x = x + self.slot_size // 2
            text_y = y + self.slot_size - 16
            text_rect = name_text.get_rect(center=(text_x, text_y))
            screen.blit(name_text, text_rect)
        
        # Fußzeile mit Hinweis
        footer_y = start_y + total_height + 25
        help_font = pygame.font.Font(None, 24)
        hint = help_font.render("Click item to spawn 10x | ESC or Ctrl+Shift+K to close", True, (200, 200, 200))
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, footer_y))
        screen.blit(hint, hint_rect)