# Hausaufgabe vom 20.11.2026: Mob-Bilder erstellen

## Aufgabe

Erstelle für jeden Mob eigene 3D-Seitenansichten. Die Vorlagen liegen in:

`hausaufgaben/schueler/mob_bilder/<mob-name>/`

Zeichne für jeden Mob sechs Bilder und behalte dabei die Dateinamen bei:

| Datei | Seite |
|---|---|
| `front.png` | Vorderseite |
| `back.png` | Rückseite |
| `left.png` | Linke Seite |
| `right.png` | Rechte Seite |
| `top.png` | Oben |
| `bottom.png` | Unten |

## Richtige Eigenschaften beachten

Die Bilder sollen zum Mob passen. Nutze dafür die Werte aus
`utils/constants.py -> MOB_PROPERTIES`:

- Leben: `health`
- Schaden: `damage`
- Geschwindigkeit: `speed`
- Drop: `drop`
- Größe: `size`
- Farbe: `color`
- Endgegner: `is_boss`

## Vorgaben

- Eine Seite pro Datei.
- Vorderseite zuerst wie in einem Porträt oder Spielfigur-Sprite zeichnen.
- Rückseite und linke/rechte Seite müssen zum gleichen Mob gehören.
- Oben und unten zeichnen, als würde man von oben beziehungsweise von unten schauen.
- Farben und Muster über alle sechs Seiten zusammenhalten.
- PNG-Dateien verwenden.
- Für jede Datei darfst du eine eigene Zeichnung oder Pixelart erstellen.

## Mob-Liste

Die vorbereiteten Ordner sind für diese Gegner:

- `slime`
- `zombie`
- `golem`
- `bat`
- `fish`
- `shark`
- `crystal_golem`
- `gem_spider`
- `mutant`
- `radioactive_slime`
- `elite_zombie`
- `fire_demon`

## Abgabe

Für jeden gewählten Mob müssen alle sechs Dateien vorhanden sein.
Beispiel für einen Schleim:

```text
mob_bilder/slime/
  front.png
  back.png
  left.png
  right.png
  top.png
  bottom.png
```

Die Vorlagen sind in der Größe `64 x 64` Pixel vorbereitet. Die roten bzw.
beschrifteten Rahmen dürfen nach dem Zeichnen entfernt werden.

Zusätzlich in jedem bearbeiteten Ordner:

- einen kurzen Namen des Mobs,
- die Werte `health`, `damage`, `speed`, `drop` und `size` auf einem Blatt.
