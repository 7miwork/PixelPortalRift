"""
utils/mob.py – Gegner (Mobs) und Gegner-Manager
================================================

Dieses Modul enthält zwei Klassen:
- Mob: Ein einzelner Gegner (z.B. Schleim, Zombie, Golem).
  Jeder Mob hat Leben, Schaden, Geschwindigkeit, eine KI (Künstliche Intelligenz)
  und lässt beim Tod Gegenstände fallen.
- MobManager: Verwaltet alle Gegner in der aktuellen Welt.
  Er sorgt dafür, dass Gegner spawnen, sich bewegen und kämpfen.

Die Gegner-KI (Künstliche Intelligenz) arbeitet so:
- "idle": Der Gegner steht rum und wartet.
- "wander": Der Gegner läuft ziellos umher.
- "chase": Der Gegner hat den Spieler bemerkt und jagt ihn.
  (Sichtweite: 200 Pixel zum Erkennen, 400 Pixel zum Verlieren)
"""

import pygame
import random
import math
from utils.constants import TILE_SIZE, MOB_PROPERTIES, DIMENSIONS, WORLD_ITEM_POOLS


class Mob:
    """
    Ein einzelner Gegner in der Spielwelt.
    
    Wichtige Attribute:
        x, y:           Position in Pixeln
        mob_type:       Name des Gegner-Typs (z.B. "slime", "zombie")
        properties:     Dictionary mit Eigenschaften aus MOB_PROPERTIES
        width, height:  Größe in Pixeln
        health:         Aktuelle Lebenspunkte
        damage:         Schaden pro Treffer
        speed:          Bewegungsgeschwindigkeit
        drop:           Item, das fallen gelassen wird (oder None)
        ai_state:       Aktueller KI-Zustand ("idle", "wander", "chase")
        texture:        Die Gegner-Grafik
    """
    
    def __init__(self, x, y, mob_type, asset_loader):
        """
        Erzeugt einen neuen Gegner.
        
        :param x: Start-x-Position in Pixeln
        :param y: Start-y-Position in Pixeln
        :param mob_type: Name des Gegner-Typs
        :param asset_loader: Für die Gegner-Grafik
        """
        self.x = x
        self.y = y
        self.mob_type = mob_type
        self.properties = MOB_PROPERTIES.get(mob_type, {})
        
        # Größe und Werte aus den Eigenschaften übernehmen
        self.width, self.height = self.properties.get("size", (24, 24))
        self.health = self.properties.get("health", 10)
        self.max_health = self.health
        self.damage = self.properties.get("damage", 1)
        self.speed = self.properties.get("speed", 1)
        self.drop = self.properties.get("drop")
        
        # Bewegung
        self.velocity_x = 0
        self.velocity_y = 0
        self.gravity = 0.3          # Schwerkraft (wie beim Spieler)
        self.on_ground = False
        self.facing_right = random.choice([True, False])  # Zufällige Start-Richtung
        
        # KI (Künstliche Intelligenz)
        self.ai_timer = 0
        self.ai_state = "idle"       # Start-Zustand: rumstehen
        self.target = None           # Aktuelles Ziel (der Spieler)
        self.attack_cooldown = 0     # Verhindert Dauer-Angriffe
        self.damage_cooldown = 0     # Verhindert Dauer-Schaden
        
        # Grafik
        self.texture = asset_loader.get_mob_texture(mob_type)
    
    def update(self, world, player, dt):
        """
        Aktualisiert den Gegner (jeden Frame).
        
        Die KI entscheidet, was der Gegner tut:
        1. Ist der Spieler nah (< 200 Pixel)? → jagen
        2. Ist der Spieler weit weg (> 400 Pixel)? → ziellos umherlaufen
        3. Sonst: rumstehen
        
        :param world: Die aktuelle World-Instanz
        :param player: Der Spieler
        :param dt: Zeit seit dem letzten Frame in Millisekunden
        """
        self.ai_timer += dt
        self.attack_cooldown = max(0, self.attack_cooldown - dt)
        self.damage_cooldown = max(0, self.damage_cooldown - dt)
        
        # Entfernung zum Spieler berechnen
        player_dist = math.sqrt((player.x - self.x) ** 2 + (player.y - self.y) ** 2)
        
        # KI-Entscheidungen basierend auf Entfernung zum Spieler
        if player_dist < 200:
            self.ai_state = "chase"      # Spieler ist nah → jagen
            self.target = player
        elif player_dist > 400:
            self.ai_state = "wander"     # Spieler ist weit weg → umherlaufen
            self.target = None
        
        # ---- Verschiedene KI-Zustände ----
        if self.ai_state == "idle":
            # Rumstehen: Nach 2 Sekunden vielleicht umherlaufen
            if self.ai_timer > 2000:
                self.ai_timer = 0
                if random.random() < 0.5:
                    self.ai_state = "wander"
        
        elif self.ai_state == "wander":
            # Ziellos umherlaufen: Nach 3 Sekunden vielleicht anhalten
            if self.ai_timer > 3000:
                self.ai_timer = 0
                self.facing_right = random.choice([True, False])
                if random.random() < 0.3:
                    self.ai_state = "idle"
            
            self.velocity_x = self.speed if self.facing_right else -self.speed
            
            # Ab und zu springen
            if random.random() < 0.02 and self.on_ground:
                self.velocity_y = -8
        
        elif self.ai_state == "chase":
            # Spieler jagen: Auf den Spieler zulaufen
            if self.target:
                if self.target.x > self.x:
                    self.velocity_x = self.speed * 1.5  # Schneller als beim Wandern
                    self.facing_right = True
                else:
                    self.velocity_x = -self.speed * 1.5
                    self.facing_right = False
                
                # Springen, wenn nötig
                if self.on_ground and random.random() < 0.05:
                    self.velocity_y = -10
                
                # Angreifen, wenn nah genug
                if player_dist < 40 and self.attack_cooldown <= 0:
                    self.attack(player)
        
        # ---- Schwerkraft anwenden ----
        self.velocity_y += self.gravity
        if self.velocity_y > 10:
            self.velocity_y = 10
        
        # ---- Horizontale Bewegung + Kollision ----
        new_x = self.x + self.velocity_x
        if not self.check_collision(world, new_x, self.y):
            self.x = new_x
        else:
            self.velocity_x = 0
            self.facing_right = not self.facing_right  # Richtung umkehren
        
        # ---- Vertikale Bewegung + Kollision ----
        new_y = self.y + self.velocity_y
        if not self.check_collision(world, self.x, new_y):
            self.y = new_y
            self.on_ground = False
        else:
            if self.velocity_y > 0:
                self.on_ground = True  # Auf dem Boden gelandet
            self.velocity_y = 0
    
    def check_collision(self, world, x, y):
        """
        Prüft, ob der Gegner an Position (x, y) mit einem festen Block kollidiert.
        
        Es werden die 4 Ecken des Gegners getestet.
        
        :param world: Die World-Instanz
        :param x: Zu prüfende x-Position
        :param y: Zu prüfende y-Position
        :return: True wenn Kollision
        """
        points = [
            (x, y),                              # Oben links
            (x + self.width, y),                  # Oben rechts
            (x, y + self.height),                 # Unten links
            (x + self.width, y + self.height)     # Unten rechts
        ]
        
        for px, py in points:
            tile_x = int(px) // TILE_SIZE
            tile_y = int(py) // TILE_SIZE
            block = world.get_block(tile_x, tile_y)
            if block and world.is_solid(block):
                return True
        return False
    
    def attack(self, player):
        """
        Greift den Spieler an.
        
        :param player: Der Spieler (nimmt Schaden)
        """
        if self.attack_cooldown <= 0:
            if player.take_damage(self.damage):
                self.attack_cooldown = 1000  # 1 Sekunde Pause zwischen Angriffen
    
    def take_damage(self, amount):
        """
        Fügt dem Gegner Schaden zu.
        
        :param amount: Schadens-Punkte
        :return: True wenn Schaden genommen wurde
        """
        if self.damage_cooldown <= 0:
            self.health -= amount
            self.damage_cooldown = 500  # 0,5 Sekunden Immunität
            
            # Rückstoß (knockback) beim Treffer
            knockback = 5 if self.facing_right else -5
            self.velocity_x = -knockback
            self.velocity_y = -3
            
            return True
        return False
    
    def is_alive(self):
        """Gibt True zurück, wenn der Gegner noch lebt (health > 0)."""
        return self.health > 0
    
    def get_drop(self):
        """
        Gibt das Item zurück, das der Gegner beim Tod fallen lässt.
        
        :return: Item-Name oder None (80% Wahrscheinlichkeit für Drop)
        """
        if self.drop and random.random() < 0.8:
            return self.drop
        return None
    
    def get_world_drop(self, world_dimension):
        """
        Gibt einen zufälligen Drop aus dem Welt-Item-Pool zurück.
        
        :param world_dimension: Name der aktuellen Dimension
        :return: Item-Name oder None
        """
        pool = WORLD_ITEM_POOLS.get(world_dimension, {})
        mob_drops = pool.get("mob_drops", [])
        if mob_drops and random.random() < 0.8:
            return random.choice(mob_drops)
        if self.drop:
            return self.drop
        return None
    
    def get_rect(self):
        """Gibt ein pygame.Rect für Kollisionsabfragen zurück."""
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def draw(self, screen, camera_x, camera_y):
        """
        Zeichnet den Gegner auf den Bildschirm.
        
        :param screen: Die pygame-Oberfläche
        :param camera_x: Kamera-Versatz x
        :param camera_y: Kamera-Versatz y
        """
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y
        
        # Textur zeichnen (oder einfarbiges Rechteck als Fallback)
        if self.texture:
            if not self.facing_right:
                flipped = pygame.transform.flip(self.texture, True, False)
                screen.blit(flipped, (draw_x, draw_y))
            else:
                screen.blit(self.texture, (draw_x, draw_y))
        else:
            color = self.properties.get("color", (255, 0, 0))
            pygame.draw.rect(screen, color, (draw_x, draw_y, self.width, self.height))
        
        # Rot-Blitz wenn getroffen (damage_flash)
        if self.damage_cooldown > 0:
            damage_overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            damage_overlay.fill((255, 0, 0, 100))
            screen.blit(damage_overlay, (draw_x, draw_y))
        
        # Lebensbalken über dem Gegner
        health_bar_width = self.width
        health_bar_height = 4
        health_percent = self.health / self.max_health
        
        pygame.draw.rect(screen, (100, 0, 0), (draw_x, draw_y - 8, health_bar_width, health_bar_height))
        pygame.draw.rect(screen, (0, 255, 0), (draw_x, draw_y - 8, int(health_bar_width * health_percent), health_bar_height))


class MobManager:
    """
    Verwaltet alle Gegner in der aktuellen Welt.
    
    Wichtige Attribute:
        mobs:       Liste aller aktiven Mob-Objekte
        asset_loader: Für die Gegner-Grafiken
        spawn_timer: Zählt die Zeit bis zum nächsten Spawn
        max_mobs:   Maximale Anzahl Gegner gleichzeitig (15)
    
    Der MobManager sorgt dafür, dass:
    - Regelmäßig neue Gegner spawnen (alle 5 Sekunden)
    - Gegner sich bewegen und kämpfen
    - Tote Gegner entfernt werden und Items droppen
    """
    
    def __init__(self, asset_loader):
        """
        Initialisiert den MobManager.
        
        :param asset_loader: Für die Gegner-Grafiken
        """
        self.mobs = []
        self.asset_loader = asset_loader
        self.spawn_timer = 0
        self.max_mobs = 15
    
    # Zuordnung: je Welt der stärkere Mob und der passende Schlüssel zur nächsten Welt
    # Der stärkere Mob hat eine kleine Chance (10%), den Schlüssel für die nächste
    # Welt fallen zu lassen. So kann der Spieler auch durch Kämpfe an Schlüssel kommen.
    WORLD_KEY_DROP = {
        "grassland": ("zombie", "stone_key"),
        "stone_world": ("golem", "water_key"),
        "water_world": ("shark", "gem_key"),
        "gem_world": ("gem_spider", "nuclear_key")
    }

    def update(self, world, player, inventory, dt):
        """
        Aktualisiert alle Gegner (jeden Frame).
        
        1. Neue Gegner spawnen (wenn nötig)
        2. Jeden Gegner aktualisieren
        3. Tote Gegner entfernen und Drops ins Inventar legen
        
        :param world: Die aktuelle World-Instanz
        :param player: Der Spieler
        :param inventory: Das Inventar (für Drops)
        :param dt: Zeit seit dem letzten Frame
        """
        self.spawn_timer += dt
        
        # Alle 5 Sekunden: Neuen Gegner spawnen (wenn nicht schon zu viele)
        if self.spawn_timer >= 5000 and len(self.mobs) < self.max_mobs:
            self.spawn_timer = 0
            self.try_spawn_mob(world, player)
        
        # Alle Gegner aktualisieren
        for mob in self.mobs[:]:
            mob.update(world, player, dt)
            
            # Tote Gegner entfernen
            if not mob.is_alive():
                drop = None
                
                # Prüfen, ob der stärkere Mob dieser Welt einen Schlüssel droppt
                world_rule = self.WORLD_KEY_DROP.get(world.dimension)
                if world_rule and world_rule[0] == mob.mob_type:
                    # 10% Chance auf den Schlüssel zur nächsten Welt
                    if random.random() < 0.10:
                        drop = world_rule[1]
                
                # Normale Loot-Regeln (wenn kein Schlüssel gedroppt wurde)
                if drop is None:
                    if mob.properties.get("is_boss", False):
                        # Bosse droppen das übermächtige Schwert
                        drop = "overpowered_sword"
                    else:
                        drop = mob.get_world_drop(world.dimension)
                
                # Drop ins Inventar legen
                if drop:
                    inventory.add_item(drop)
                
                self.mobs.remove(mob)
    
    def try_spawn_mob(self, world, player):
        """
        Versucht, einen neuen Gegner zu spawnen.
        
        Der Gegner erscheint zufällig links oder rechts vom Spieler,
        300-500 Pixel entfernt. Er muss auf einem festen Block spawnen.
        
        :param world: Die World-Instanz
        :param player: Der Spieler
        """
        dimension_data = DIMENSIONS.get(world.dimension, {})
        available_mobs = dimension_data.get("mobs", [])
        
        if not available_mobs:
            return  # Keine Gegner in dieser Dimension
        
        # Zufällige Position links oder rechts vom Spieler
        spawn_x = player.x + random.choice([-1, 1]) * random.randint(300, 500)
        
        # Boden finden (ersten festen Block von oben)
        spawn_y = None
        for y in range(10, world.height - 10):
            if world.is_solid(world.get_block(int(spawn_x // TILE_SIZE), y)):
                spawn_y = (y - 2) * TILE_SIZE  # 2 Blöcke über dem Boden
                break
        
        if spawn_y is None:
            return  # Kein Boden gefunden
        
        # Prüfen, ob die Position in der Welt ist
        if 0 <= spawn_x < world.width * TILE_SIZE:
            mob_type = random.choice(available_mobs)
            new_mob = Mob(spawn_x, spawn_y, mob_type, self.asset_loader)
            self.mobs.append(new_mob)
    
    def spawn_mob_at(self, x, y, mob_type):
        """
        Erzeugt einen Gegner an einer bestimmten Position (für Events/Bosse).
        
        :param x: x-Position in Pixeln
        :param y: y-Position in Pixeln
        :param mob_type: Name des Gegner-Typs
        """
        new_mob = Mob(x, y, mob_type, self.asset_loader)
        self.mobs.append(new_mob)
    
    def clear_mobs(self):
        """Entfernt alle Gegner (beim Wechseln der Dimension)."""
        self.mobs.clear()
    
    def check_attack(self, player_rect, damage):
        """
        Prüft, ob der Spieler-Angriff einen Gegner trifft.
        
        :param player_rect: Das Rechteck des Angriffs
        :param damage: Schadens-Punkte
        :return: Liste der getroffenen Gegner
        """
        hits = []
        for mob in self.mobs:
            if player_rect.colliderect(mob.get_rect()):
                if mob.take_damage(damage):
                    hits.append(mob)
        return hits
    
    def draw(self, screen, camera_x, camera_y):
        """Zeichnet alle Gegner."""
        for mob in self.mobs:
            mob.draw(screen, camera_x, camera_y)
    
    def get_save_data(self):
        """
        Gibt den Zustand aller Gegner als Liste zurück (zum Speichern).
        
        :return: Liste mit x, y, Typ und Gesundheit jedes Gegners
        """
        return [{
            "x": mob.x,
            "y": mob.y,
            "mob_type": mob.mob_type,
            "health": mob.health
        } for mob in self.mobs]
    
    def load_save_data(self, data):
        """
        Stellt Gegner aus gespeicherten Daten wieder her.
        
        :param data: Liste aus get_save_data()
        """
        self.mobs.clear()
        for mob_data in data:
            mob = Mob(mob_data["x"], mob_data["y"], mob_data["mob_type"], self.asset_loader)
            mob.health = mob_data["health"]
            self.mobs.append(mob)