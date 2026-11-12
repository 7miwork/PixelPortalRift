"""
PixelPortalRift - Hausaufgabe Stufe 5 von 5: Mini-Crafting (alles zusammen)
===========================================================================
Das ist die Idee der echten Funktion craft() in utils/crafting.py:
1) Pruefen, ob alle Zutaten da sind.
2) Zutaten aus dem Inventar entfernen.
3) Das Ergebnis ins Inventar legen.

DEINE AUFGABE: Schritt 2 fehlt! Ohne ihn waere Crafting gratis und unendlich.
"""

# ---------- FUNKTIONIERENDES BEISPIEL (so geht es) ----------
beispiel = {"wood": 5}
beispiel["wood"] -= 2                  # "-=" zieht ab: 5 - 2
print("Beispiel: Holz nach Abziehen:", beispiel["wood"])     # 3

# ---------- DEINE AUFGABE ----------
def craft(name, recipes, inventory):
    zutaten = recipes[name]["ingredients"]

    # Schritt 1: Sind alle Zutaten da?
    for zutat, anzahl in zutaten.items():
        if inventory.get(zutat, 0) < anzahl:
            return False

    # Schritt 2: Zutaten aus dem Inventar entfernen
    for zutat, anzahl in zutaten.items():
        inventory[zutat] -= anzahl

    # Schritt 3: Ergebnis hinzufuegen
    inventory[name] = inventory.get(name, 0) + recipes[name]["result_count"]
    return True


recipes = {"stick": {"ingredients": {"wood": 2}, "result_count": 4}}
inventory = {"wood": 5}

print("1. craft:", craft("stick", recipes, inventory), inventory)  # True  {'wood': 3, 'stick': 4}
print("2. craft:", craft("stick", recipes, inventory), inventory)  # True  {'wood': 1, 'stick': 8}
print("3. craft:", craft("stick", recipes, inventory), inventory)  # False (nur noch 1 Holz!)

# ---------- AUTOMATISCHER CHECK (nichts aendern) ----------
t = {"wood": 5}
r1 = craft("stick", recipes, t) and t == {"wood": 3, "stick": 4}
r2 = craft("stick", recipes, t) and t == {"wood": 1, "stick": 8}
r3 = (craft("stick", recipes, t) is False) and t == {"wood": 1, "stick": 8}
if r1 and r2 and r3:
    print("[OK] Stufe 5 geschafft! Das ist genau die Idee hinter dem Crafting-Menue.")
    print("     BONUS: Oeffne utils/crafting.py und zeig deinen Eltern die echte craft()-Funktion.")
else:
    print("[X] Noch nicht ganz. Tipp: Das Beispiel oben zeigt, wie man abzieht (-=).")

# =====================================================================
# ELTERN-KARTE  (erklaere deinen Eltern das Programm in 3 Saetzen)
# =====================================================================
# 1) Das Programm macht ...
# 2) Das wichtigste Wort im Code ist ... und es bedeutet ...
# 3) Wenn ich ... aendere, dann ...
#
# Eltern-Kuerzel: ________   Datum: ________
