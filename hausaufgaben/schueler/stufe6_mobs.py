"""
PixelPortalRift - Hausaufgabe Stufe 6 von 6: Mob erstellen und Werte setzen
============================================================================
Im Spiel sind alle Gegner mit einem Dictionary in utils/constants.py definiert:
MOB_PROPERTIES["slime"] enthalt Leben, Schaden, Geschwindigkeit, Drop,
Farbe und Groesse.

Die Klasse Mob in utils/mob.py nimmt diese Werte beim Erstellen auf.
Jedes Mob-Objekt bekommt seine eigenen Werte.

DEINE AUFGABE: Ersetze die pass-Zeilen mit den richtigen Werten.
"""


MOB_PROPERTIES = {
    "slime": {
        "health": 10,
        "damage": 2,
        "speed": 1,
        "drop": "slime_ball",
        "size": (24, 24),
    },
    "zombie": {
        "health": 20,
        "damage": 3,
        "speed": 0.8,
        "drop": "rotten_flesh",
        "size": (24, 32),
    },
    "fire_demon": {
        "health": 100,
        "damage": 15,
        "speed": 1.0,
        "drop": "fire_axe",
        "size": (36, 44),
        "is_boss": True,
    },
}


class Mob:
    def __init__(self, mob_type, properties):
        self.mob_type = mob_type
        self.properties = properties

        # Die Aufgabe: Werte aus properties in das Mob-Objekt uebernehmen.
        # .get("health", 10) bedeutet: Nimm health, sonst verwende 10.
        self.health = properties.get("health", 10)
        self.max_health = 0
        self.damage = 0
        self.speed = 0
        self.drop = None
        self.width = 0
        self.height = 0

        # Ersetze die Platzhalter-Werte oben mit den richtigen properties-Werten.


# ---------- FUNKTIONIERENDES BEISPIEL (so geht es) ----------
print("Beispiel: Eigenschaften auslesen")
slime_props = MOB_PROPERTIES["slime"]
print("Schleim-Leben:", slime_props.get("health", 10))

# ---------- DEINE AUFGABE TESTEN ----------
slime = Mob("slime", MOB_PROPERTIES["slime"])
zombie = Mob("zombie", MOB_PROPERTIES["zombie"])
boss = Mob("fire_demon", MOB_PROPERTIES["fire_demon"])

print("Slime:", slime.health, slime.max_health, slime.damage,
      slime.speed, slime.drop, slime.width, slime.height)

# ---------- AUTOMATISCHER CHECK (nichts aendern) ----------
if (slime.health == 10 and slime.max_health == 10
        and slime.damage == 2 and slime.speed == 1
        and slime.drop == "slime_ball"
        and slime.width == 24 and slime.height == 24
        and zombie.health == 20 and zombie.damage == 3
        and boss.health == 100 and boss.speed == 1.0
        and boss.drop == "fire_axe"):
    print("[OK] Stufe 6 geschafft! Du kannst jetzt einen Mob aus Eigenschaften erzeugen.")
    print("     BONUS: Oeffne utils/mob.py und vergleiche die Werte mit Mob.__init__.")
else:
    print("[X] Noch nicht ganz.")
    print("Tipp: Setze max_health, damage, speed, drop und Groesse aus properties.")

# =====================================================================
# ELTERN-KARTE  (erklaere deinen Eltern das Programm in 3 Saetzen)
# =====================================================================
# 1) Das Programm macht ...
# 2) Das wichtigste Wort im Code ist ... und es bedeutet ...
# 3) Wenn ich ... aendere, dann ...
#
# Eltern-Kuerzel: ________   Datum: ________
