"""
utils/crafting.py – Crafting-System

Dieses Modul enthält das Crafting-System, mit dem der Spieler
neue Gegenstände herstellen kann. Es verwendet die Rezepte aus
CRAFTING_RECIPES in utils/constants.py.

Der Spieler öffnet das Crafting-Menü mit Taste C. Dort sieht er
alle Rezepte, die er craften kann (grün hinterlegt) und welche
Zutaten ihm noch fehlen (rot hinterlegt). Ein Klick auf ein Rezept
stellt den Gegenstand her, wenn alle Zutaten vorhanden sind.

WICHTIG: Dieses Modul ist reine Spiellogik – KEIN pygame. Die Darstellung
(Rezeptliste, Klick-Behandlung) übernimmt die Ursina-UI in
utils/game_ui.py; das Layout (3-Zeilen-Boxen) bleibt dabei gleich.
"""

from utils.constants import CRAFTING_RECIPES


class CraftingSystem:
    """
    Verwaltet das Crafting-Menü und die Herstellung von Gegenständen.
    
    Wichtige Attribute:
        recipes:           Dictionary mit allen Rezepten (aus CRAFTING_RECIPES)
        is_open:           Ist das Crafting-Menü geöffnet?
        selected_recipe:   Index des aktuell ausgewählten Rezepts
        scroll_offset:     Scroll-Position (bei vielen Rezepten)
        craftable_recipes: Liste aller Rezepte mit Info, ob sie herstellbar sind
    """
    
    def __init__(self):
        """Initialisiert das Crafting-System mit allen Rezepten."""
        self.recipes = CRAFTING_RECIPES
        self.is_open = False
        self.selected_recipe = 0
        self.scroll_offset = 0
        self.craftable_recipes = []
    
    def update_craftable(self, inventory):
        """
        Aktualisiert die Liste der herstellbaren Rezepte.
        
        Geht alle Rezepte durch und prüft, ob der Spieler die Zutaten hat.
        """
        self.craftable_recipes = []
        for recipe_name, recipe_data in self.recipes.items():
            if self.can_craft(recipe_name, inventory):
                self.craftable_recipes.append((recipe_name, recipe_data, True))
            else:
                self.craftable_recipes.append((recipe_name, recipe_data, False))
    
    def can_craft(self, recipe_name, inventory):
        """
        Prüft, ob ein bestimmtes Rezept hergestellt werden kann.
        
        :param recipe_name: Name des Rezepts
        :param inventory: Das Inventar des Spielers
        :return: True wenn alle Zutaten vorhanden sind
        """
        if recipe_name not in self.recipes:
            return False
        
        recipe = self.recipes[recipe_name]
        for ingredient, count in recipe["ingredients"].items():
            if not inventory.has_item(ingredient, count):
                return False
        return True
    
    def craft(self, recipe_name, inventory):
        """
        Stellt einen Gegenstand her.
        
        Entfernt die Zutaten aus dem Inventar und fügt das Ergebnis hinzu.
        
        :param recipe_name: Name des Rezepts
        :param inventory: Das Inventar des Spielers
        :return: True wenn erfolgreich
        """
        if not self.can_craft(recipe_name, inventory):
            return False
        
        recipe = self.recipes[recipe_name]
        
        # Zutaten aus dem Inventar entfernen
        for ingredient, count in recipe["ingredients"].items():
            inventory.remove_item(ingredient, count)
        
        # Ergebnis hinzufügen
        result_count = recipe.get("result_count", 1)
        remaining = inventory.add_item(recipe_name, result_count)
        
        return remaining == 0
    
    def toggle_open(self, inventory):
        """Öffnet oder schließt das Crafting-Menü."""
        self.is_open = not self.is_open
        if self.is_open:
            self.update_craftable(inventory)
    
    def scroll(self, direction):
        """
        Scrollt durch die Rezept-Liste (Mausrad).
        
        :param direction: +1 oder -1
        """
        max_visible = 7
        max_scroll = max(0, len(self.craftable_recipes) - max_visible)
        self.scroll_offset = max(0, min(max_scroll, self.scroll_offset + direction))
    
    def select_recipe(self, index):
        """Wählt ein Rezept aus."""
        actual_index = index + self.scroll_offset
        if 0 <= actual_index < len(self.craftable_recipes):
            self.selected_recipe = actual_index
    
    def craft_selected(self, inventory):
        """
        Stellt das aktuell ausgewählte Rezept her.
        
        :param inventory: Das Inventar des Spielers
        :return: True wenn erfolgreich
        """
        if 0 <= self.selected_recipe < len(self.craftable_recipes):
            recipe_name = self.craftable_recipes[self.selected_recipe][0]
            if self.craft(recipe_name, inventory):
                self.update_craftable(inventory)
                return True
        return False
    

