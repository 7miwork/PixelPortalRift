"""
PixelPortalRift - Hausaufgabe Stufe 2 von 5: Funktion mit Rueckgabewert
=======================================================================
Im Spiel fragt das Crafting-System: "Hat der Spieler genug davon?"
Das macht die Funktion has_item() (siehe utils/inventory.py).
Eine Funktion gibt mit "return" eine Antwort zurueck: hier True oder False.

DEINE AUFGABE: Ersetze die markierte Zeile durch die richtige return-Zeile.
"""

# ---------- FUNKTIONIERENDES BEISPIEL (so geht es) ----------
def ist_voll(count, max_stack):
    return count >= max_stack          # gibt True oder False zurueck

print("Beispiel:", ist_voll(64, 64), ist_voll(10, 64))    # True False

# ---------- DEINE AUFGABE ----------
def has_item(inventory, name, count):
    """True, wenn im Inventar mindestens `count` Stueck von `name` liegen."""
    # Tipp: inventory.get(name, 0) liefert die Anzahl - oder 0, wenn es name nicht gibt.
    return inventory.get(name, 0) >= count

inventory = {"wood": 5, "stick": 1}

print("3 Holz?   ", has_item(inventory, "wood", 3))       # soll True sein
print("2 Stoecke?", has_item(inventory, "stick", 2))      # soll False sein
print("1 Stein?  ", has_item(inventory, "stone", 1))      # soll False sein

# ---------- AUTOMATISCHER CHECK (nichts aendern) ----------
if (has_item(inventory, "wood", 3) is True
        and has_item(inventory, "stick", 2) is False
        and has_item(inventory, "stone", 1) is False):
    print("[OK] Stufe 2 geschafft! Jetzt erklaere es deinen Eltern.")
else:
    print("[X] Noch nicht ganz. Tipp: Die Funktion braucht ein 'return' mit einem Vergleich (>=).")

# =====================================================================
# ELTERN-KARTE  (erklaere deinen Eltern das Programm in 3 Saetzen)
# =====================================================================
# 1) Das Programm macht ...
# 2) Das wichtigste Wort im Code ist ... und es bedeutet ...
# 3) Wenn ich ... aendere, dann ...
#
# Eltern-Kuerzel: ________   Datum: ________
