"""
PixelPortalRift - Hausaufgabe Stufe 4 von 5: Klasse und Objekt
==============================================================
Das Inventar besteht aus Slots. Jeder Slot ist ein Objekt der Klasse
InventorySlot (utils/inventory.py). Die Klasse ist der Bauplan,
jedes slot = Slot() ist ein gebautes Objekt.

DEINE AUFGABE: In der Methode remove() fehlt die Zeile, die die Anzahl verkleinert.
"""

class Slot:
    def __init__(self):
        self.item = None
        self.count = 0

    def is_empty(self):
        return self.item is None or self.count <= 0

    # ---------- FUNKTIONIERENDES BEISPIEL (so geht es) ----------
    def add(self, item, count):
        self.item = item
        self.count += count            # <- so zaehlt man hoch

    # ---------- DEINE AUFGABE ----------
    def remove(self, count):
        # Ziehe `count` von der Anzahl dieses Slots ab (denk an das "self.").
        self.count -= count
        if self.count <= 0:            # Slot leer -> Item vergessen
            self.item = None
            self.count = 0


slot = Slot()
print("leer?", slot.is_empty())                      # True
slot.add("wood", 5)
print("nach add:    ", slot.item, slot.count)        # wood 5
slot.remove(2)
print("nach remove 2:", slot.item, slot.count)       # wood 3
slot.remove(3)
print("nach remove 3:", slot.item, slot.count, "leer?", slot.is_empty())   # None 0 True

# ---------- AUTOMATISCHER CHECK (nichts aendern) ----------
test = Slot()
test.add("wood", 5)
test.remove(2)
erste_pruefung = (test.count == 3 and test.item == "wood")
test.remove(3)
zweite_pruefung = (test.count == 0 and test.item is None and test.is_empty())
if erste_pruefung and zweite_pruefung:
    print("[OK] Stufe 4 geschafft! Jetzt erklaere es deinen Eltern.")
else:
    print("[X] Noch nicht ganz. Tipp: Schau dir an, wie add() die Anzahl veraendert - bei remove() ist es das Gegenteil.")

# =====================================================================
# ELTERN-KARTE  (erklaere deinen Eltern das Programm in 3 Saetzen)
# =====================================================================
# 1) Das Programm macht ...
# 2) Das wichtigste Wort im Code ist ... und es bedeutet ...
# 3) Wenn ich ... aendere, dann ...
#
# Eltern-Kuerzel: ________   Datum: ________
