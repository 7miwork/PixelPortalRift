# PixelPortalRift

## Start

Abhängigkeiten installieren und das Spiel starten:

```sh
pip install -r requirements.txt
python main.py
```

## Steuerung

- **WASD** bewegen, **Maus** umsehen, **Leertaste** springen
- **E** öffnet/schließt das Inventar; Gegenstände lassen sich per Drag-and-Drop verschieben
- **C** öffnet/schließt das Crafting-Menü; auf ein Rezept klicken, um es herzustellen
- **1–9** oder **Mausrad** wählt einen Hotbar-Slot
- **Linksklick** baut einen Block ab; **Rechtsklick** platziert einen Block aus der Hotbar
- **Escape** schließt ein geöffnetes Menü

Ergaenzung:
    - Portallogik (muss zur Welt passen)
    -- Bosskaempfe droppen den schluessel geringe droprate
    --- immer kaempfen wenn kein Schluessel da ist in einer kleinen dimension
    - Crafting menue (muss zur Welt passen)
    - Spezielle Superstarke Gegner wenn besiegt droppen diese einen spezielles
      Item z.B. Overpowered Diamantschwert, Feueraxt
      anstatt normale Version

    - 3D Welt (verwendung einer extra Engine weil es einfacher ist)