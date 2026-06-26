"""
Dev-Check: Validiert, ob alle Portal- und Schluessel-Rezepte nur Materialien
aus der Welt verwenden, in der das Rezept benoetigt wird (oder frueheren Welten).

Nur zur Entwicklung — kein Teil des Spiels.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from utils.constants import (
    CRAFTING_RECIPES, WORLD_ITEM_POOLS, DIMENSIONS,
    ITEM_PROPERTIES, BLOCK_PROPERTIES
)

# Dimensionen in Reihenfolge (je weiter hinten, desto spaeter erreicht)
DIM_ORDER = ["grassland", "stone_world", "water_world", "gem_world", "nuclear_world"]

def get_available_items(dim):
    """Alle Items, die in einer Dimension direkt verfuegbar sind."""
    pool = WORLD_ITEM_POOLS.get(dim, {})
    items = set()
    for category in pool.values():
        items.update(category)
    # Zusaetzlich Bloecke, die in der Dimension generiert werden
    dim_data = DIMENSIONS.get(dim, {})
    items.update(dim_data.get("blocks", []))
    return items

def get_all_available_items_up_to(dim):
    """Alle Items, die bis einschliesslich der gegebenen Dimension verfuegbar sind."""
    idx = DIM_ORDER.index(dim)
    items = set()
    for i in range(idx + 1):
        items.update(get_available_items(DIM_ORDER[i]))
    return items

def resolve_ingredient(item, visited=None):
    """Löst ein Ingredient rekursiv auf zu den Basis-Ressourcen (aus WORLD_ITEM_POOLS)."""
    if visited is None:
        visited = set()
    if item in visited:
        return {item}
    visited.add(item)

    # Wenn das Item direkt in einem Pool vorkommt, ist es eine Basis-Ressource
    all_items = set()
    for pool in WORLD_ITEM_POOLS.values():
        for cat in pool.values():
            all_items.update(cat)

    if item in all_items:
        return {item}

    # Wenn es ein Crafting-Rezept gibt, dessen Zutaten aufloesen
    recipe = CRAFTING_RECIPES.get(item)
    if recipe:
        resolved = set()
        for ing in recipe["ingredients"]:
            resolved.update(resolve_ingredient(ing, visited))
        return resolved
    return {item}

def main():
    print("=" * 60)
    print("VALIDIERUNG: Crafting-Rezepte auf Welt-Verfuegbarkeit")
    print("=" * 60)

    errors = []
    warnings = []

    # Definiere, in welcher Dimension jedes Rezept benoetigt wird
    # (portal_frame_* -> in dieser Dimension)
    # (portal_keys -> in der Welt, aus der man herausgeht)
    dimension_map = {
        "portal_frame_grassland": "grassland",
        "portal_frame_stone_world": "stone_world",
        "portal_frame_water_world": "water_world",
        "portal_frame_gem_world": "gem_world",
        "stone_key": "stone_world",
        "water_key": "water_world",
        "gem_key": "gem_world",
        "nuclear_key": "nuclear_world",
    }

    # Rezepte, die fuer Portal-Aktivator/Frame relevant sind
    portal_recipes = {k: v for k, v in CRAFTING_RECIPES.items()
                      if k in dimension_map or k.startswith("portal_frame_")}

    for recipe_name, recipe_data in portal_recipes.items():
        dim = dimension_map.get(recipe_name)
        if not dim:
            continue

        available = get_all_available_items_up_to(dim)
        ingredients = recipe_data.get("ingredients", {})

        # Pruefe direkt: koennen Zutaten in dieser oder frueheren Welten gefunden werden?
        for ing, count in ingredients.items():
            # Versuche, das Ingredient aufzuloesen
            base_items = resolve_ingredient(ing)
            if not base_items.issubset(available):
                errors.append(
                    f"FEHLER: '{recipe_name}' (benoetigt in {dim}) "
                    f"verwendet '{ing}' (aufgeloest: {base_items}), "
                    f"die erst in spaeteren Welten verfuegbar sind!"
                )

    # Zusaetzlich: Pruefe alle Rezepte generell auf "Zukunfts-Materialien"
    # (Items, die nur in spaeteren Dimensionen vorkommen, aber in fruehen verwendet werden)
    for recipe_name, recipe_data in CRAFTING_RECIPES.items():
        dim = dimension_map.get(recipe_name)
        if not dim:
            continue

        available = get_all_available_items_up_to(dim)
        for ing in recipe_data.get("ingredients", {}):
            base_items = resolve_ingredient(ing)
            if not base_items.issubset(available):
                # Fehler already reported above, skip duplicate
                pass

    # --- Ausgabe ---
    if errors:
        print(f"\n{len(errors)} FEHLER gefunden:")
        for e in errors:
            print(f"  - {e}")
    else:
        print("\nKeine Fehler gefunden! Alle Portal-Rezepte verwenden")
        print("nur Materialien aus der jeweiligen oder frueheren Welten.")

    # Pruefe auch, ob alle portal_frame_* Bloecke in BLOCK_PROPERTIES existieren
    print("\n--- Pruefe BLOCK_PROPERTIES fuer portal_frame_* ---")
    for dim in DIM_ORDER:
        block_name = f"portal_frame_{dim}"
        if block_name not in BLOCK_PROPERTIES:
            errors.append(f"FEHLEN: '{block_name}' fehlt in BLOCK_PROPERTIES!")
            print(f"  FEHLER: '{block_name}' fehlt in BLOCK_PROPERTIES!")
        else:
            print(f"  OK: '{block_name}' vorhanden")

    # Pruefe Crafting-Rezepte-Vollstaendigkeit
    print("\n--- Pruefe CRAFTING_RECIPES fuer portal_frame_* ---")
    for dim in DIM_ORDER:
        recipe_name = f"portal_frame_{dim}"
        if recipe_name not in CRAFTING_RECIPES:
            errors.append(f"FEHLEN: Rezept '{recipe_name}' fehlt in CRAFTING_RECIPES!")
            print(f"  FEHLER: Rezept '{recipe_name}' fehlt!")
        else:
            print(f"  OK: Rezept '{recipe_name}' vorhanden")

    if not errors:
        print("\n" + "=" * 60)
        print("ALLE PRUEFUNGEN BESTANDEN!")
        print("=" * 60)
        return 0
    else:
        print(f"\n{'=' * 60}")
        print(f"{len(errors)} PROBLEME GEFUNDEN — bitte beheben!")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())