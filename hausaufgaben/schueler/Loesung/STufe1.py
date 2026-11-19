"""
PixelPortalRift - Hausaufgabe Stufe 1 von 5: Variablen und Dictionary
=====================================================================
Im Spiel ist jeder Gegenstand ein Dictionary (siehe ITEM_PROPERTIES in
utils/constants.py). Ein Dictionary ist wie ein Schrank mit beschrifteten
Faechern: Name -> Wert.

DEINE AUFGABE: Fuege EINE Zeile ein (Markierung unten) und starte das Programm.
Am Ende zeigt dir der Check, ob du es geschafft hast.
"""

# ---------- FUNKTIONIERENDES BEISPIEL (so geht es) ----------
stein = {"name": "cobblestone", "count": 10}
print("Beispiel vorher: ", stein["count"])        # 10
stein["count"] = stein["count"] + 4               # <- so aendert man einen Wert
print("Beispiel nachher:", stein["count"])        # 14

# ---------- DEINE AUFGABE ----------
holz = {"name": "wood", "count": 5}
print("Holz vorher: ", holz["count"])             # 5

# Du hast 3 Holz gefunden! Erhoehe "count" von holz um 3.
# >>> HIER DEINE ZEILE EINFUEGEN <<<

print("Holz nachher:", holz["count"])             # soll 8 sein

# ---------- AUTOMATISCHER CHECK (nichts aendern) ----------
if holz["count"] == 8:
    print("[OK] Stufe 1 geschafft! Jetzt erklaere es deinen Eltern.")
else:
    print("[X] Noch nicht ganz. Tipp: Schau dir das Beispiel oben an.")

# =====================================================================
# ELTERN-KARTE  (erklaere deinen Eltern das Programm in 3 Saetzen)
# =====================================================================
# 1) Das Programm macht ...
# 2) Das wichtigste Wort im Code ist ... und es bedeutet ...
# 3) Wenn ich ... aendere, dann ...
#
# Eltern-Kuerzel: ________   Datum: ________