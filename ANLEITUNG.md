# 🎨 Anleitung: Bilder für PixelPortalRift erstellen

**Für Schüler – Urlaubsaufgabe**

Hallo! In dieser Anleitung lernst du, wie du im Urlaub eigene Pixel-Art-Bilder für unser Spiel **PixelPortalRift** erstellst. Du brauchst dafür nur das kostenlose Programm **LibreSprite**.

---

## 1. Programm herunterladen & installieren

LibreSprite ist ein kostenloses Pixel-Art-Zeichenprogramm (ähnlich wie Aseprite, aber gratis).

### Download
👉 **https://github.com/LibreSprite/LibreSprite/releases/tag/v1.3**

### Installation
1. Öffne den Link oben.
2. Scrolle nach unten zu **Assets**.
3. Lade die Datei für Windows herunter (z.B. `LibreSprite-1.3-windows-installer.exe` oder die ZIP-Datei).
4. Doppelklicke auf die heruntergeladene Datei und folge dem Installationsassistenten.
5. Nach der Installation findest du LibreSprite im Startmenü oder auf dem Desktop.

> 💡 **Tipp:** Wenn du keine Installation machen kannst (z.B. auf einem Schul-PC), nimm die **ZIP-Version** – die kannst du einfach entpacken und ohne Installation starten.

---

## 2. Grundlagen: Wie das Spiel Bilder verwendet

Das Spiel lädt automatisch Bilder aus dem Ordner `assets/`:

| Typ | Ordner | Größe | Beispiel-Dateiname |
|---|---|---|---|
| Blöcke | `assets/blocks/` | 32 × 32 Pixel | `grass.png` |
| Items | `assets/items/` | 32 × 32 Pixel | `diamond.png` |
| Gegner | `assets/mobs/` | variabel (z.B. 24 × 32) | `zombie.png` |
| Spieler | `assets/` | 24 × 32 Pixel | `player.png` |
| Titelbild | `assets/` | 1200 × 800 Pixel | `title.png` |

**Wichtig:** Der Dateiname muss **genau** so heißen wie der Block/Item/Gegner in `utils/constants.py` definiert ist – sonst wird das Bild nicht verwendet!

---

## 3. Schritt-für-Schritt: Ein Bild erstellen

### 3.1 LibreSprite starten & neues Bild anlegen
1. Öffne LibreSprite.
2. Klicke auf **Datei → Neu** (oder `Ctrl+N`).
3. Stelle die Größe ein:
   - **Breite:** 32
   - **Höhe:** 32
   - **Farbtiefe:** RGBA (mit Transparenz)
4. Klicke auf **OK**.

### 3.2 Pixel zeichnen
- Verwende das **Bleistift-Werkzeug** (P) zum Zeichnen einzelner Pixel.
- Verwende das **Füllwerkzeug** (G) zum Ausfüllen von Flächen.
- Verwende die **Farbpalette** rechts, um Farben auszuwählen.
- **Zoom** mit dem Mausrad, um genau zu arbeiten (z.B. 800 %).

### 3.3 Transparenz (wichtig für Items!)
- Items und Gegner sollen einen **transparenten Hintergrund** haben.
- Klicke auf das **Radiergummi** (E), um Pixel transparent zu machen.
- Oder: Hintergrundebene löschen (Ebene → Hintergrund löschen).

### 3.4 Speichern
1. Klicke auf **Datei → Exportieren → Exportieren als**.
2. Wähle **PNG** als Format.
3. Gib den Dateinamen ein (z.B. `diamond.png`).
4. Speichere im richtigen Ordner (z.B. `assets/items/`).

> ⚠️ **Achtung:** Speichere nicht als `.ase` oder `.aseprite` – das Spiel kann diese Formate nicht lesen! Nur **PNG** funktioniert.
---

## 4. Aufgaben fuer den Urlaub

### Aufgabe A: Titelbilder erstellen
Erstelle mindestens 3 verschiedene Titelbilder fuer das Spiel.

- Dateiname: title.png, title2.png, title3.png
- Groesse: 1200 x 800 Pixel
- Inhalt: Ein schoenes Pixel-Art-Motiv passend zum Spiel (z.B. eine Landschaft mit Portal, ein Held vor einem Dungeon, eine Weltkarte mit den 5 Dimensionen).
- Speicherort: assets/

**Ideen fuer Titelbilder:**
1. Der Spieler steht vor einem Portal in der Grassland-Welt (Sonnenaufgang).
2. Unterwasser-Szene mit Korallen, Perlen und einem Schiffswrack (Wasserwelt).
3. Kristallhoehle mit gluehenden Edelsteinen (Edelsteinwelt).
4. Strahlende Atomwelt mit Reaktor und Schutzanzug (Atomwelt).
5. Alle 5 Welten als kleine Inseln auf einer Karte.

### Aufgabe B: Bloecke erstellen
Erstelle eigene Texturen fuer mindestens 5 Bloecke.

Empfohlene Bloecke (einfach):
| Dateiname | Beschreibung | Farbe |
|---|---|---|
| grass.png | Grasblock mit gruenem Oben | Gruen/Braun |
| dirt.png | Erd-Block | Braun |
| stone.png | Stein-Block | Grau |
| wood.png | Holz-Block (Baumstamm) | Braun |
| leaves.png | Blaetter-Block | Gruen |
| sand.png | Sand-Block | Beige/Gelb |
| water.png | Wasser (mit Transparenz!) | Blau (Alpha) |
| coal_ore.png | Kohle-Erz | Schwarz/Grau |
| iron_ore.png | Eisen-Erz | Braun/Grau |
| gold_ore.png | Gold-Erz | Gelb/Grau |

Schwierigere Bloecke:
| Dateiname | Beschreibung |
|---|---|
| coral.png | Korallenblock (bunt) |
| crystal.png | Kristall (leuchtend) |
| obsidian.png | Obsidian (dunkel, glaenzend) |
| uranium.png | Uran (gruen, radioaktiv) |

### Aufgabe C: Items erstellen
Erstelle eigene Icons fuer mindestens 5 Items.

Empfohlene Items (einfach):
| Dateiname | Beschreibung |
|---|---|
| stick.png | Holzstock |
| wood.png | Holzstueck |
| coal.png | Kohlestueck |
| iron_ingot.png | Eisenbarren |
| gold_ingot.png | Goldbarren |
| apple.png | Apfel |
| diamond.png | Diamant |
| emerald.png | Smaragd |
| ruby.png | Rubin |
| pearl.png | Perle |
| torch.png | Fackel |

Schwierigere Items:
| Dateiname | Beschreibung |
|---|---|
| healing_potion.png | Heiltrank (Flaeschchen) |
| radiation_suit.png | Strahlenschutzanzug |
| slime_ball.png | Schleimball |
| shark_tooth.png | Haifischzahn |

### Aufgabe D: Gegner erstellen (optional)
Erstelle eigene Sprites fuer mindestens 2 Gegner.

| Dateiname | Groesse | Beschreibung |
|---|---|---|
| slime.png | 24 x 24 | Gruener Schleim |
| zombie.png | 24 x 32 | Zombie |
| skeleton.png | 24 x 32 | Skelett |
| shark.png | 32 x 16 | Hai (Wasserwelt) |
| nuclear_spider.png | 32 x 32 | Atom-Spinne |


## 5. Wie du deine Bilder testest

1. Kopiere deine PNG-Dateien in den richtigen assets/-Ordner.
2. Starte das Spiel (python main.py).
3. Das Spiel laedt automatisch deine Bilder!
4. Wenn ein Bild nicht geladen wird, pruefe:
   - Ist der Dateiname exakt richtig geschrieben? (Kleinbuchstaben!)
   - Ist die Datei im richtigen Ordner?
   - Ist es wirklich ein PNG?

## 6. Erklaerungsdatei: Was bedeutet was?

Fuer jedes Bild, das du erstellst, solltest du eine kurze Erklaerung schreiben. Hier ist eine Vorlage:

### Vorlage: ERKLAERUNG_<deinname>.md

```
# Meine Bilder fuer PixelPortalRift

**Erstellt von:** [Dein Name]
**Datum:** [Datum]

## Titelbilder
| Dateiname | Beschreibung | Inspiration |
|---|---|---|
| title.png | Sonnenuntergang ueber der Grassland-Welt | Minecraft-Startbildschirm |

## Bloecke
| Dateiname | Beschreibung | Verwendete Farben |
|---|---|---|
| grass.png | Grasblock mit brauner Erde unten | Gruen (34,139,34), Braun (139,90,43) |

## Items
| Dateiname | Beschreibung | Besonderheiten |
|---|---|---|
| diamond.png | Blauer Diamant mit Glanz | Transparenter Hintergrund |

## Gegner
| Dateiname | Beschreibung | Animation? |
|---|---|---|
| slime.png | Gruener Schleim | Nein (statisch) |
```

## 7. Tipps & Tricks fuer Pixel-Art

1. Weniger ist mehr: Pixel-Art lebt von Einfachheit. Verwende wenige Farben.
2. Kontrast: Helle und dunkle Bereiche sorgen fuer Tiefe.
3. Umriss: Ein dunkler Umriss (Outline) macht Objekte lesbarer.
4. Symmetrie: Viele Items sind symmetrisch - nutze das!
5. Referenzen: Schaue dir echte Minecraft-Texturen an und vereinfache sie.
6. Raster: Arbeite immer auf dem 32x32-Raster, nie mit Anti-Aliasing.
7. Transparenz: Items sollten transparenten Hintergrund haben, Bloecke nicht (ausser Wasser).

## 8. Abgabe

Bitte gib deine Bilder zusammen mit der Erklaerungsdatei ab:

1. Alle PNG-Dateien im richtigen Ordner (assets/blocks/, assets/items/, etc.)
2. Die Erklaerungsdatei ERKLAERUNG_<deinname>.md

**Deadline:** [Datum eintragen]

## 9. Hilfe & Ressourcen

- LibreSprite Dokumentation: https://libresprite.github.io/
- Pixel-Art-Tutorials: Suche auf YouTube nach "pixel art tutorial for beginners"
- Minecraft Texturen als Referenz: https://minecraft.wiki/w/Texture

Viel Spass beim Zeichnen!
