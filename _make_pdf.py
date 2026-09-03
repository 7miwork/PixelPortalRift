# -*- coding: utf-8 -*-
"""Erzeugt die PDF-Anleitung 'Von Pygame zu Ursina' fuer den Unterricht."""
import os
from fpdf import FPDF

FONT = r"C:\Windows\Fonts\arial.ttf"
FONT_B = r"C:\Windows\Fonts\arialbd.ttf"
FONT_MONO = r"C:\Windows\Fonts\consola.ttf"
OUT = os.path.join(os.path.dirname(__file__), "Anleitung_Pygame_zu_Ursina.pdf")


class PDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font("Arial", "", 8)
            self.set_text_color(120, 120, 120)
            self.cell(0, 6, "Von Pygame zu Ursina - PixelPortalRift 3D", align="R")
            self.ln(8)

    def footer(self):
        self.set_y(-12)
        self.set_font("Arial", "", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, f"Seite {self.page_no()}/{{nb}}", align="C")


pdf = PDF()
pdf.add_font("Arial", "", FONT)
pdf.add_font("Arial", "B", FONT_B)
pdf.add_font("Consola", "", FONT_MONO)
pdf.set_margins(18, 16, 18)
pdf.set_auto_page_break(True, 18)


def h1(text):
    pdf.set_font("Arial", "B", 18)
    pdf.set_text_color(20, 60, 120)
    pdf.multi_cell(0, 9, text)
    pdf.ln(2)


def h2(text):
    pdf.ln(2)
    pdf.set_font("Arial", "B", 13)
    pdf.set_text_color(20, 60, 120)
    pdf.multi_cell(0, 7, text)
    pdf.ln(1)


def para(text):
    pdf.set_font("Arial", "", 10.5)
    pdf.set_text_color(30, 30, 30)
    pdf.multi_cell(0, 5.5, text)
    pdf.ln(1.5)


def bullet(items):
    pdf.set_font("Arial", "", 10.5)
    pdf.set_text_color(30, 30, 30)
    for it in items:
        pdf.set_x(pdf.l_margin + 3)
        pdf.multi_cell(0, 5.5, "-  " + it)
    pdf.ln(1.5)


def code(text):
    pdf.set_font("Consola", "", 9.5)
    pdf.set_fill_color(240, 243, 248)
    pdf.set_text_color(25, 25, 25)
    pdf.multi_cell(0, 5, text, fill=True)
    pdf.ln(2)


def table(rows, widths, header=True):
    pdf.set_font("Arial", "", 9.5)
    for i, row in enumerate(rows):
        if header and i == 0:
            pdf.set_font("Arial", "B", 9.5)
            pdf.set_fill_color(220, 230, 245)
        else:
            pdf.set_fill_color(250, 250, 252)
        pdf.set_text_color(30, 30, 30)
        for j, cell in enumerate(row):
            pdf.multi_cell(widths[j], 5.5, cell, border=1, fill=True,
                           new_x="RIGHT", new_y="TOP")
        pdf.ln(-1)
    pdf.ln(3)


# ================= Seite 1: Titel =================
pdf.add_page()
pdf.ln(30)
pdf.set_font("Arial", "B", 26)
pdf.set_text_color(20, 60, 120)
pdf.cell(0, 12, "Von Pygame zu Ursina", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Arial", "", 15)
pdf.set_text_color(60, 60, 60)
pdf.cell(0, 10, "Dein Spiel wird 3D! - PixelPortalRift, Phase 1", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.ln(20)
pdf.set_font("Arial", "", 11)
for line in [
    "Du kennst Pygame: Fenster, Schleife, Pixel, Sprites.",
    "Jetzt lernst du Ursina kennen: eine 3D-Engine fuer Python,",
    "die dir blaettrige Arbeit wie Kamera, Licht und Schwerkraft abnimmt.",
    "",
    "In diesem Heft:",
    "  1.  Die wichtigsten Unterschiede Pygame vs. Ursina",
    "  2.  Ein kleines Beispiel nebeneinander",
    "  3.  Was in Phase 1 unseres Projekts schon gebaut wurde",
    "  4.  Deine Aufgaben fuer die naechsten Schritte",
]:
    pdf.cell(0, 7, line, align="C", new_x="LMARGIN", new_y="NEXT")

# ================= Seite 2: Unterschiede =================
pdf.add_page()
h1("1. Was ist anders in Ursina?")
para("Pygame ist eine Bibliothek: Du schreibst selbst alles - die Game-Loop, "
     "das Zeichnen, die Kollision. Ursina ist eine Engine: Sie bringt Fenster, "
     "Kamera, 3D-Modelle, Schwerkraft und Eingaben fertig mit. Du sagst ihr nur, "
     "WAS passieren soll.")
h2("1.1 Die grosse Vergleichstabelle")
table([
    ["Thema", "Pygame (2D)", "Ursina (3D)"],
    ["Start", "pygame.init() + Display setzen", "app = Ursina()"],
    ["Game-Loop", "while running: ... selbst schreiben", "app.run() - die Engine ruft deine update() und input() Methoden automatisch auf"],
    ["Position", "(x, y) in Pixeln, Ursprung oben links", "(x, y, z) in Block-Einheiten, y ist die HOEHE"],
    ["Objekte", "Surface laden + blitten", "Entity(model='cube', texture=..., position=...)"],
    ["Spieler", "Selbst bewegen + Kollision + Sprung bauen", "FirstPersonController - fertig mit WASD, Maus, Springen, Schwerkraft"],
    ["Kollision", "rect.collide_rect(...) selbst pruefen", "collider='box' setzen, Engine prueft selbst"],
    ["Bilder", "pygame.image.load(...)", "texture='grass.png' oder Texture('grass.png')"],
    ["Text/HUD", "Font-Objekt + render", "Text('Hallo', parent=camera.ui)"],
    ["Farben", "(255, 0, 0) - Werte 0-255", "color.red oder color.rgba(r, g, b) - Werte 0 bis 1"],
], [30, 70, 88])
h2("1.2 Die zwei wichtigsten Ursina-Ideen")
bullet([
    "ALLES ist ein Entity. Bloecke, Spieler, Licht, Himmel, Text - alles ist ein Entity mit position, rotation, scale, texture, collider. Du konfigurierst Entities statt Pixel zu zeichnen.",
    "update() und input() statt eigener while-Schleife. In jedem Frame ruft Ursina update() auf, bei jedem Tastendruck input(key). Logik, die frueher in der Pygame-Schleife stand, gehoert jetzt in update().",
])

# ================= Seite 3: Beispiel =================
pdf.add_page()
h1("2. Das gleiche Spiel zweimal: Pygame vs. Ursina")
para("Links das, was du kennst (2D, Block bewegt sich mit Pfeiltasten). "
     "Rechts dasselbe in 3D mit Ursina - Achtung: viel weniger Code!")
para("Pygame-Version:")
code('''import pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
player = pygame.Rect(100, 100, 32, 32)
clock = pygame.time.Clock()
running = True

while running:                      # Game-Loop selbst schreiben!
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    keys = pygame.key.get_pressed()
    if keys[pygame.K_RIGHT]: player.x += 5
    if keys[pygame.K_LEFT]:  player.x -= 5
    screen.fill((135, 206, 235))    # Himmel zeichnen
    pygame.draw.rect(screen, (0, 200, 0), player)
    pygame.display.flip()
    clock.tick(60)''')
para("Ursina-Version:")
code('''from ursina import *

app = Ursina()

player = Entity(model='cube', color=color.red,
                position=(0, 0, 0))    # x, y, z statt (x, y)-Pixel

def update():                          # wird jeden Frame aufgerufen
    player.x += held_keys['d'] * time.dt * 5   # time.dt = Zeit seit letztem Frame
    player.x -= held_keys['a'] * time.dt * 5

app.run()                              # Game-Loop macht die Engine''')
para("Beachte: time.dt sorgt dafuer, dass die Geschwindigkeit unabhaengig von den FPS ist. "
     "In Pygame hast du dafuer einen Fixwert pro Frame benutzt.")

# ================= Seite 4: Koordinaten & Entities =================
pdf.add_page()
h1("3. Von Pixeln zu Voxeln")
h2("3.1 Neue Koordinaten")
para("Frueher: eine Position (x, y) in Pixeln, Ursprung oben links, y wächst nach UNTEN.")
para("Jetzt: eine Position (x, y, z) in Block-Einheiten:")
bullet([
    "x und z = horizontale Grundflaeche (wie in Minecraft)",
    "y = Hoehe, wächst nach OBEN (kein Bildschirm-Ursprung mehr!)",
    "Ein Block ist 1x1x1 gross - kein TILE_SIZE mehr noetig",
])
h2("3.2 Die Welt als Voxel-Gitter")
para("Unser Spiel ist ein Minecraft-Klon: Die Welt besteht aus Bloecken (Voxel). "
     "Statt einer Tile-Liste speichern wir Bloecke in einem Dictionary:")
code('''# Von 2D ...
tiles = {(x, y): block_name}

# ... zu 3D
blocks = {(x, y, z): block_name}   # z.B. {(8, 4, 8): "grass"}''')
h2("3.3 Nur sichtbare Bloecke rendern (Culling)")
para("Ein 16x16-Chunk mit nur 5 Schichten Tiefe haette 1280 Bloecke - in einer "
     "grossen Welt Millionen. Der Trick: Ein Block wird nur als Entity gerendert, "
     "wenn er mindestens eine sichtbare Flaeche hat (also mindestens einen Nachbarn "
     "als Luft hat). Ganz innenliegende Bloecke bleiben unsichtbar - die Kamera "
     "koennte sie nie sehen. Das ist wie das Frustum-Culling in echten Engines.")

# ================= Seite 5: Was Phase 1 gebaut hat =================
pdf.add_page()
h1("4. Was in Phase 1 schon fertig ist")
para("Das Projekt wurde bereits auf Ursina migriert. So ist der Code aufgebaut:")
table([
    ["Datei", "Was drin steckt"],
    ["main.py", "Ursina-Fenster, Sky, Licht, FirstPersonController, HUD-Text (Position/FPS)"],
    ["utils/voxel_world.py", "VoxelWorld, Chunk, BlockTextureLibrary - die 3D-Block-Welt"],
    ["utils/constants.py", "Alle Werte wie frueher: BLOCK_PROPERTIES, DIMENSIONS, 3D-Spielerwerte"],
], [42, 146])
h2("4.1 Der Aufbau von main.py (auszugsweise)")
code('''from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

class Game:
    def __init__(self):
        self.app = Ursina(title="PixelPortalRift 3D")
        self.sky = Sky(color=sky_color)            # Himmel
        DirectionalLight(...)                       # Licht (sonst flach!)
        self.world = VoxelWorld(BlockTextureLibrary())
        self.world.generate_flat_test_chunk()       # Phase-1-Testwelt
        self.player = FirstPersonController(        # fertiger Spieler!
            position=(8, TEST_CHUNK_SURFACE_Y + 3, 8),
            speed=PLAYER_SPEED_3D,
            jump_height=PLAYER_JUMP_HEIGHT_3D,
        )
        self.player.gravity = PLAYER_GRAVITY_3D''')
para("Erkennst du die Pygame-Bausteine wieder? Was frueher player.py + "
     "world_gen.py + asset_loader.py zusammen machten, erledigen hier drei "
     "Ursina-Fertigteile: Sky, Licht und FirstPersonController.")
h2("4.2 Wie ein Block gezeichnet wird (aus Chunk.render)")
code('''entity = Entity(
    parent=self.world_group,   # gehoert zur Welt
    model="cube",              # ein Wuerfel
    texture=texture,           # z.B. assets/blocks/grass.png
    color=ursina_color,        # Fallback, wenn keine Textur da ist
    position=(x, y, z),        # Block-Position in der Welt
    collider="box",            # damit der Spieler drauf stehen kann
)''')
para("Ganz wichtig: RGB-Farben aus constants.py (Werte 0-255) muessen fuer "
     "Ursina durch 255 geteilt werden (Werte 0-1). Genau das macht die Funktion "
     "rgb_to_ursina_color() in main.py.")

h2("1.1 Die grosse Vergleichstabelle")
table([
    ["Thema", "Pygame (2D)", "Ursina (3D)"],
    ["Start", "pygame.init() + Display setzen", "app = Ursina()"],
    ["Game-Loop", "while running: ... selbst schreiben", "app.run() - die Engine ruft deine update() und input() Methoden automatisch auf"],
    ["Position", "(x, y) in Pixeln, Ursprung oben links", "(x, y, z) in Block-Einheiten, y ist die HOEHE"],
    ["Objekte", "Surface laden + blitten", "Entity(model='cube', texture=..., position=...)"],
    ["Spieler", "Selbst bewegen + Kollision + Sprung selbst bauen", "FirstPersonController - fertig mit WASD, Maus, Springen, Schwerkraft"],
    ["Kollision", "rect.collide_rect(...) selbst pruefen", "collider='box' setzen, Engine prueft selbst"],
    ["Bilder", "pygame.image.load(...)", "texture='grass.png' oder Texture('grass.png')"],
    ["Text/HUD", "Font-Objekt + render", "Text('Hallo', parent=camera.ui)"],
    ["Farben", "(255, 0, 0) - Werte 0-255", "color.red oder color.rgba(r, g, b) - Werte 0 bis 1"],
], [30, 70, 88])
# ================= Seite 6-7: Aufgaben =================
pdf.add_page()
h1("5. Deine Aufgaben: Phase 2 selbst umbauen")
para("Phase 1 laeuft schon - jetzt bist du dran! Arbeite die Aufgaben der Reihe "
     "nach durch. Fuer jede Aufgabe steht in der Datei ein Kommentar, wo sie hingehoert.")
h2("Aufgabe 1: Warmwerden - ein eigener Block")
bullet([
    "Oeffne utils/voxel_world.py und aendere in generate_flat_test_chunk() den obersten Block 'grass' gegen 'stone'.",
    "Starte python main.py und laufe mit WASD + Maus durch deine Welt.",
])
h2("Aufgabe 2: Terrain mit Huegeln statt flacher Ebene")
para("Ersetze in generate_flat_test_chunk() die feste Hoehe durch eine "
     "Heightmap-Funktion, z.B. mit math.sin:")
code('''def get_height(x, z):
    return TEST_CHUNK_SURFACE_Y + int(2 * math.sin(x / 5) + 2 * math.cos(z / 7))''')
bullet([
    "Lege die Bloecke von y=0 bis zur Hoehe get_height(x, z) ab (unten Stein, oben Gras/Erde).",
    "Zusatz: Vergiss nicht das Culling - nur Bloecke mit Luft-Nachbarn rendern!",
])
h2("Aufgabe 3: Bloecke abbauen (Mausklick)")
para("Ursina weiss, welches Entity unter der Maus liegt. Baue in Game.input() ein:")
code('''def input(self, key):
    if key == "left mouse down":          # Linksklick = abbauen
        hit = self.player.raycast(origin=self.player.position,
                                  direction=self.player.forward,
                                  distance=MAX_INTERACTION_RANGE)
        if hit and hit.entity.block_name:
            coords = hit.entity.block_coords
            self.world.set_block(*coords, None)   # Block entfernen
            hit.chunk.render()                    # Chunk neu rendern''')
para("Tipp: Damit das klappt, muss das Entity die Attribute block_name und "
     "block_coords haben - schau in voxel_world.py, ob das schon passiert.")
h2("Aufgabe 4: Bloecke platzieren")
bullet([
    "Bei 'right mouse down': nimm hit.entity.block_coords, geh einen Schritt in Blickrichtung und setze dort mit world.set_block(...) den Block aus deiner Hotbar.",
    "Danach wieder chunk.render() aufrufen.",
])
h2("Aufgabe 5: Hotbar-Anzeige")
bullet([
    "Erzeuge 9 kleine Entities unter parent=camera.ui (so wie das HUD-Text-Overlay in main.py).",
    "Tasten 1-9 in Game.input() verarbeiten, gewaehlten Block markieren.",
])
h2("Aufgabe 6: Erste Mob-Entity")
bullet([
    "Erstelle eine Klasse Mob(Entity): model='cube', Farbe aus MOB_PROPERTIES, collider='box'.",
    "In update(): ein kleiner Schritt Richtung Spieler (self.position += direction * speed * time.dt).",
    "Gehoert der Mob zur Block-Welt? Bekommt er Schwerkraft? Ueberlege dir das zuerst!",
])

# ================= Seite 8: Tipps =================
pdf.add_page()
h1("6. Tipps, Stolpersteine und Hilfe")
h2("Stolpersteine, die oft reinspringen")
bullet([
    "Aenderst du Bloecke in einem Chunk, vergiss chunk.render() nicht - sonst passiert scheinbar nichts.",
    "Licht nicht vergessen: Ohne DirectionalLight/AmbientLight sehen Wuerfel flach aus.",
    "y ist HOEHE. Ein Position-Fehler zeigt sich oft als Spieler, der 'in die Tiefe faellt'.",
    "Aenderungen an constants.py wirken sofort - schau immer zuerst dort nach, bevor du Werte hartkodierst (das ist die Regel des Projekts: keine hartkodierten Werte!).",
    "Nach einem Crash hilft print(): Lass dir Variablen mit print(...) im Terminal ausgeben, wie frueher auch.",
])
h2("Debuggen mit dem HUD")
para("Das HUD oben links zeigt Position, Dimension und FPS an. Mit F3 blendest "
     "du es ein/aus (siehe Game.input in main.py). Nutze es, um zu pruefen, "
     "wo du gerade stehst!")
h2("Wo nachschlagen")
bullet([
    "Offizielle Docs: www.ursinaengine.org/documentation.html",
    "Wichtige Seiten: 'Entity', 'FirstPersonController', 'Raycast'",
    "In der Python-Konsole: from ursina import *; help(Entity)",
    "Im Projekt: Kommentare in main.py und voxel_world.py erklaeren jeden Schritt (PHASE-1-Hinweise).",
])
h2("Projekt-Plan (fuer die naechsten Phasen)")
table([
    ["Phase", "Inhalt", "Ursina-Thema, das du dafuer brauchst"],
    ["Phase 1 (fertig)", "Testchunk, Spieler, HUD", "Entity, Sky, Licht, FirstPersonController"],
    ["Phase 2", "Terrain-Generierung (Huegel, Erze, Baeume)", "Dictionary-Welt + Heightmap"],
    ["Phase 3", "Bloecke abbauen/platzieren, Inventar", "Raycast, camera.ui, input(key)"],
    ["Phase 3+", "Mobs, Portale, Dimensionswechsel, Crafting, Speichern", "Eigene Entity-Klassen, Welt neu aufbauen"],
], [40, 60, 68])
para("Viel Erfolg - und merke dir: Ursina nimmt dir das Zeichnen ab, damit du "
     "deine Zeit ins Spiel-Design stecken kannst. Genau das hast du dir mit dem "
     "Wechsel auf 3D gewuenscht!")

pdf.output(OUT)
print("PDF erstellt:", OUT)

