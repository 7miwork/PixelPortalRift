"""
utils/player.py – Spieler-Steuerung
=====================================

Dieses Modul enthält die Klasse Player, die den Spieler-Charakter steuert.
Der Spieler kann sich links/rechts bewegen, springen, Schaden nehmen,
heilen und essen. Außerdem gibt es einen Creative-Modus (Taste G),
in dem der Spieler fliegen und keinen Schaden nehmen kann.

Wichtige Mechaniken:
- Schwerkraft (gravity) zieht den Spieler nach unten
- Kollisionserkennung mit Blöcken (horizontal, Decke, Boden)
- Hunger-System: Wenn der Hunger auf 0 fällt, verliert der Spieler Leben
- Kamera: Die Welt scrollt mit dem Spieler mit
"""

import pygame
from utils.constants import TILE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT


class Player:
    """
    Steuert den Spieler-Charakter.
    
    Wichtige Attribute:
        x, y:           Position in Pixeln (linke obere Ecke)
        width, height:  Größe der Spielfigur in Pixeln (24x32)
        velocity_x:     Bewegung in x-Richtung (Pixel pro Frame)
        velocity_y:     Bewegung in y-Richtung (Pixel pro Frame) – Schwerkraft!
        speed:          Laufgeschwindigkeit
        jump_power:     Sprungkraft (nach oben)
        on_ground:      Steht der Spieler auf dem Boden?
        health:         Aktuelle Lebenspunkte (max 100)
        hunger:         Aktueller Hunger (max 100)
        creative_mode:  Im Creative-Modus kann der Spieler fliegen
        texture:        Die Spieler-Grafik (pygame-Surface)
    """
    
    def __init__(self, x, y, asset_loader):
        """
        Erzeugt den Spieler an Position (x, y).
        
        :param x: Start-x-Position in Pixeln
        :param y: Start-y-Position in Pixeln
        :param asset_loader: Der AssetLoader für die Spieler-Grafik
        """
        self.x = x
        self.y = y
        self.width = 24
        self.height = 32

        # Bewegung
        self.velocity_x = 0
        self.velocity_y = 0

        self.speed = 4
        self.jump_power = 12
        self.gravity = 0.5         # Stärke der Schwerkraft (Pixel pro Frame²)
        self.on_ground = False     # Steht der Spieler auf einem festen Block?
        self.is_jumping = False    # Ist der Spieler gerade am Springen?
        self.facing_right = True   # In welche Richtung schaut der Spieler?

        # ===== STATS =====
        self.max_health = 100
        self.health = self.max_health
        self.max_hunger = 100
        self.hunger = self.max_hunger
        self.hunger_timer = 0          # Zählt die Zeit bis zum nächsten Hunger-Abzug
        self.damage_cooldown = 0        # Verhindert Dauer-Schaden (in Millisekunden)

        # Grafik
        self.asset_loader = asset_loader
        self.texture = asset_loader.get_player_texture()
        
        # Creative-Modus (Taste G zum Umschalten)
        self.creative_mode = False

    # =========================================================
    # UPDATE
    # =========================================================
    def update(self, world, dt):
        """
        Aktualisiert den Spieler-Zustand (wird jeden Frame aufgerufen).
        
        Schritte:
        1. Horizontale Bewegung
        2. Schwerkraft anwenden (oder Fliegen im Creative-Modus)
        3. Vertikale Bewegung + Kollision (Boden/Decke)
        4. Hunger/Health aktualisieren
        
        :param world: Die aktuelle World-Instanz (für Kollisionsabfragen)
        :param dt: Zeit seit dem letzten Frame in Millisekunden
        """
        # -------- HORIZONTAL --------
        # Neue x-Position berechnen und auf Kollision prüfen
        new_x = self.x + self.velocity_x
        if not self.check_collision_x(world, new_x):
            self.x = new_x
        else:
            # Wenn Kollision: Bewegung stoppen
            self.velocity_x = 0

        # -------- SCHWERKRAFT / FLIEGEN --------
        # Im Creative-Modus: Keine Schwerkraft, dafür Flugsteuerung
        if self.creative_mode:
            fly_speed = 5
            # W/S/Leertaste/Nach-oben zum Fliegen
            if pygame.key.get_pressed()[pygame.K_w] or pygame.key.get_pressed()[pygame.K_UP] or pygame.key.get_pressed()[pygame.K_SPACE]:
                self.velocity_y = -fly_speed  # Nach oben
            elif pygame.key.get_pressed()[pygame.K_s] or pygame.key.get_pressed()[pygame.K_DOWN]:
                self.velocity_y = fly_speed    # Nach unten
            else:
                self.velocity_y = 0            # Schweben
        else:
            # Normale Schwerkraft (Nicht-Creative)
            self.velocity_y += self.gravity
            # Fallgeschwindigkeit begrenzen (Maximalgeschwindigkeit)
            if self.velocity_y > 15:
                self.velocity_y = 15

        # -------- VERTIKAL --------
        # Neue y-Position berechnen und auf Kollision prüfen
        new_y = self.y + self.velocity_y
        
        hit_ceiling = self.check_ceiling_collision(world, new_y)
        hit_floor = self.check_floor_collision(world, new_y)
        
        if not hit_ceiling and not hit_floor:
            # Frei fallen/schweben
            self.y = new_y
            self.on_ground = False
        elif hit_floor and self.velocity_y >= 0:
            # Landung auf Boden – exakt auf Tile-Kante setzen
            # Berechne die y-Position so, dass die Füße genau auf dem Block stehen
            self.y = (int((new_y + self.height) // TILE_SIZE) * TILE_SIZE) - self.height
            self.on_ground = True
            self.is_jumping = False
            self.velocity_y = 0
        elif hit_ceiling:
            # Kopf stößt an Decke
            self.velocity_y = 0
        else:
            # Sicherheitsnetz: Bodenkontakt aber velocity_y < 0 (sollte nicht passieren)
            self.velocity_y = 0

        # -------- HUNGER / HEALTH --------
        # Im Creative-Modus: Kein Hunger-Abbau und kein Health-Verlust
        if not self.creative_mode:
            self.hunger_timer += dt
            # Alle 5 Sekunden: 1 Hunger-Punkt verlieren
            if self.hunger_timer >= 5000:
                self.hunger = max(0, self.hunger - 1)
                self.hunger_timer = 0
                # Wenn Hunger auf 0: Lebenspunkte verlieren
                if self.hunger <= 0:
                    self.health = max(0, self.health - 1)

        # Schaden-Cooldown herunterzählen
        if self.damage_cooldown > 0:
            self.damage_cooldown -= dt

    # =========================================================
    # KOLLISION
    # =========================================================
    def check_collision_x(self, world, x):
        """
        Prüft, ob der Spieler an Position (x, self.y) horizontal mit einem Block kollidiert.
        
        Es werden 4 Test-Punkte verwendet (Ecken des Spielers, leicht eingerückt).
        
        :param world: Die World-Instanz
        :param x: Zu prüfende x-Position
        :return: True wenn Kollision, False wenn frei
        """
        points = [
            (x + 2, self.y + 2),                             # Oben links
            (x + self.width - 2, self.y + 2),                 # Oben rechts
            (x + 2, self.y + self.height - 2),                # Unten links
            (x + self.width - 2, self.y + self.height - 2),   # Unten rechts
        ]

        for px, py in points:
            # Pixel-Koordinaten in Block-Koordinaten umrechnen
            tile_x = int(px) // TILE_SIZE
            tile_y = int(py) // TILE_SIZE
            block = world.get_block(tile_x, tile_y)
            if block and world.is_solid(block):
                return True
        return False

    def check_ceiling_collision(self, world, y):
        """
        Prüft, ob der Kopf (Oberkante) an einen festen Block stößt.
        
        :param world: Die World-Instanz
        :param y: Zu prüfende y-Position
        :return: True wenn Kollision mit der Decke
        """
        points = [
            (self.x + 2, y),              # Oben links
            (self.x + self.width - 2, y), # Oben rechts
        ]
        for px, py in points:
            tile_x = int(px) // TILE_SIZE
            tile_y = int(py) // TILE_SIZE
            block = world.get_block(tile_x, tile_y)
            if block and world.is_solid(block):
                return True
        return False

    def check_floor_collision(self, world, y):
        """
        Prüft, ob die Füße (Unterkante) auf einem festen Block stehen.
        
        :param world: Die World-Instanz
        :param y: Zu prüfende y-Position
        :return: True wenn Boden-Kollision
        """
        points = [
            (self.x + 2, y + self.height),              # Unten links
            (self.x + self.width - 2, y + self.height), # Unten rechts
        ]
        for px, py in points:
            tile_x = int(px) // TILE_SIZE
            tile_y = int(py) // TILE_SIZE
            block = world.get_block(tile_x, tile_y)
            if block and world.is_solid(block):
                return True
        return False

    # =========================================================
    # BEWEGUNG
    # =========================================================
    def move(self, direction):
        """
        Bewegt den Spieler in die angegebene Richtung.
        
        :param direction: "left", "right" oder "stop" (stehen bleiben)
        """
        if direction == "left":
            self.velocity_x = -self.speed
            self.facing_right = False
        elif direction == "right":
            self.velocity_x = self.speed
            self.facing_right = True
        elif direction == "stop":
            self.velocity_x = 0

    def jump(self):
        """
        Lässt den Spieler springen (nur möglich, wenn er auf dem Boden steht).
        
        :return: True wenn Sprung ausgelöst wurde, False wenn nicht möglich
        """
        if self.on_ground and not self.is_jumping:
            # Nach oben springen (negative y-Richtung)
            self.velocity_y = -self.jump_power
            self.on_ground = False
            self.is_jumping = True
            return True
        return False

    # =========================================================
    # GESUNDHEIT
    # =========================================================
    def take_damage(self, amount):
        """
        Fügt dem Spieler Schaden zu.
        
        Im Creative-Modus wird kein Schaden genommen.
        Der damage_cooldown verhindert, dass der Spieler zu schnell
        hintereinander Schaden bekommt.
        
        :param amount: Schadens-Punkte
        :return: True wenn Schaden genommen wurde, False wenn nicht
        """
        if self.creative_mode:
            return False
        if self.damage_cooldown <= 0:
            self.health = max(0, self.health - amount)
            self.damage_cooldown = 1000  # 1 Sekunde Immunität
            return True
        return False

    def heal(self, amount):
        """
        Stellt Lebenspunkte wieder her (maximal bis max_health).
        
        :param amount: Wie viele Lebenspunkte werden geheilt?
        """
        self.health = min(self.max_health, self.health + amount)

    def eat(self, hunger_restore, health_restore=0):
        """
        Lässt den Spieler essen (stellt Hunger und optional Leben wieder her).
        
        :param hunger_restore: Wie viel Hunger wird gestillt?
        :param health_restore: Wie viel Leben wird geheilt? (optional)
        """
        self.hunger = min(self.max_hunger, self.hunger + hunger_restore)
        if health_restore > 0:
            self.heal(health_restore)

    def is_alive(self):
        """Gibt True zurück, wenn der Spieler noch lebt (health > 0)."""
        return self.health > 0

    # =========================================================
    # RENDER (Zeichnen)
    # =========================================================
    def get_rect(self):
        """
        Gibt ein pygame.Rect-Objekt zurück (für Kollisionsabfragen mit Gegnern).
        
        :return: pygame.Rect an der aktuellen Position
        """
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def get_camera_offset(self):
        """
        Berechnet den Kamera-Versatz, sodass der Spieler immer in der Bildschirm-Mitte ist.
        
        Die Kamera folgt dem Spieler: Wenn der Spieler sich bewegt,
        scrollt die Welt entsprechend.
        
        :return: (camera_x, camera_y) – der Versatz in Pixeln
        """
        return (
            self.x - SCREEN_WIDTH // 2 + self.width // 2,
            self.y - SCREEN_HEIGHT // 2 + self.height // 2
        )

    def draw(self, screen, camera_x, camera_y):
        """
        Zeichnet den Spieler auf den Bildschirm.
        
        :param screen: Die pygame-Oberfläche (Bildschirm)
        :param camera_x: Kameraversatz in x-Richtung
        :param camera_y: Kameraversatz in y-Richtung
        """
        draw_x = self.x - camera_x
        draw_y = self.y - camera_y

        # Textur zeichnen (oder einfarbiges Rechteck als Fallback)
        if self.texture:
            img = self.texture
            # Spieler spiegeln, wenn er nach links schaut
            if not self.facing_right:
                img = pygame.transform.flip(img, True, False)
            screen.blit(img, (draw_x, draw_y))
        else:
            pygame.draw.rect(
                screen,
                (255, 200, 150),  # Hautfarbe
                (draw_x, draw_y, self.width, self.height)
            )

        # Damage-Flash: Rot-Blinken wenn der Spieler gerade getroffen wurde
        if self.damage_cooldown > 0 and int(self.damage_cooldown / 100) % 2 == 0:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((255, 0, 0, 100))  # Rotes Blinken mit 50% Transparenz
            screen.blit(overlay, (draw_x, draw_y))

    def draw_stats(self, screen):
        """
        Zeichnet die Status-Leisten (Leben und Hunger) oben links auf dem Bildschirm.
        
        :param screen: Die pygame-Oberfläche (Bildschirm)
        """
        bar_width = 200
        bar_height = 20
        x = 10
        y = 10

        # ---- Lebenspunkte (rote Leiste) ----
        pygame.draw.rect(screen, (100, 100, 100), (x, y, bar_width, bar_height))  # Hintergrund
        hw = int((self.health / self.max_health) * bar_width)  # Breite = Anteil der Gesundheit
        pygame.draw.rect(screen, (255, 0, 0), (x, y, hw, bar_height))  # Rote Füllung
        pygame.draw.rect(screen, (255, 255, 255), (x, y, bar_width, bar_height), 2)  # Rahmen

        # Text: "HP: 100/100"
        font = pygame.font.Font(None, 20)
        screen.blit(
            font.render(f"HP: {int(self.health)}/{self.max_health}", True, (255, 255, 255)),
            (x + 5, y + 3)
        )

        # ---- Hunger (braune Leiste) ----
        pygame.draw.rect(screen, (100, 100, 100), (x, y + 25, bar_width, bar_height))
        hw = int((self.hunger / self.max_hunger) * bar_width)
        pygame.draw.rect(screen, (139, 90, 43), (x, y + 25, hw, bar_height))  # Braune Füllung
        pygame.draw.rect(screen, (255, 255, 255), (x, y + 25, bar_width, bar_height), 2)

        screen.blit(
            font.render(f"Hunger: {int(self.hunger)}/{self.max_hunger}", True, (255, 255, 255)),
            (x + 5, y + 28)
        )
        
        # ---- Creative-Modus Anzeige ----
        if self.creative_mode:
            creative_font = pygame.font.Font(None, 24)
            creative_text = creative_font.render("CREATIVE MODE", True, (0, 255, 255))
            screen.blit(creative_text, (x, y + 55))