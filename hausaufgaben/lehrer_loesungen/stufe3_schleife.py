"""
PixelPortalRift - Hausaufgabe Stufe 3 von 5: Schleife und if
============================================================
Im Crafting-Menue geht das Spiel jedes Rezept durch und prueft die Zutaten
(update_craftable in utils/crafting.py): gruen = herstellbar, rot = es fehlt etwas.

DEINE AUFGABE: Ersetze die markierte Zeile. Der Computer soll sich merken,
dass eine Zutat fehlt.
"""

# ---------- FUNKTIONIERENDES BEISPIEL (so geht es) ----------
slots = {"wood": 5, "stick": 0, "coal": 0}
for name, anzahl in slots.items():          # geht jeden Eintrag durch
    if anzahl == 0:
        print("Beispiel: leer ->", name)    # coal und stick

# ---------- DEINE AUFGABE ----------
recipes = {
    "stick":          {"wood": 2},
    "wooden_sword":   {"wood": 2, "stick": 1},
    "wooden_pickaxe": {"wood": 3, "stick": 2},
    "stone_sword":    {"cobblestone": 2, "stick": 1},
}
inventory = {"wood": 5, "stick": 1}

ergebnis = {}
for name, zutaten in recipes.items():
    ok = True                                # erst mal: alles da
    for zutat, anzahl in zutaten.items():
        if inventory.get(zutat, 0) < anzahl:
            # Hier fehlt etwas! Merke dir: das Rezept ist NICHT herstellbar.
            ok = False
    ergebnis[name] = ok
    print(name, "-> herstellbar" if ok else "-> es fehlt etwas")

# soll herauskommen: stick und wooden_sword herstellbar, die anderen beiden nicht

# ---------- AUTOMATISCHER CHECK (nichts aendern) ----------
if ergebnis == {"stick": True, "wooden_sword": True,
                "wooden_pickaxe": False, "stone_sword": False}:
    print("[OK] Stufe 3 geschafft! Jetzt erklaere es deinen Eltern.")
else:
    print("[X] Noch nicht ganz. Tipp: ok ist eine Variable mit True/False - setze sie auf den passenden Wert.")

# =====================================================================
# ELTERN-KARTE  (erklaere deinen Eltern das Programm in 3 Saetzen)
# =====================================================================
# 1) Das Programm macht ...
# 2) Das wichtigste Wort im Code ist ... und es bedeutet ...
# 3) Wenn ich ... aendere, dann ...
#
# Eltern-Kuerzel: ________   Datum: ________
