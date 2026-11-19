"""
Loesung: PixelPortalRift - Hausaufgabe Stufe 6: Mobs
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
        self.health = properties.get("health", 10)
        self.max_health = self.health
        self.damage = properties.get("damage", 1)
        self.speed = properties.get("speed", 1)
        self.drop = properties.get("drop")
        self.width, self.height = properties.get("size", (24, 24))


slime = Mob("slime", MOB_PROPERTIES["slime"])
zombie = Mob("zombie", MOB_PROPERTIES["zombie"])
boss = Mob("fire_demon", MOB_PROPERTIES["fire_demon"])

print("Slime:", slime.health, slime.max_health, slime.damage,
      slime.speed, slime.drop, slime.width, slime.height)
print("Zombie-Leben:", zombie.health)
print("Boss-Drop:", boss.drop)
