Eigene Blockbilder
==================

Lege Bilder in den Unterordner mit dem Namen des Blocks:

    assets/custom_blocks/grass/gras_01.png
    assets/custom_blocks/grass/gras_02.png
    assets/custom_blocks/stone/stein_01.jpg

Alle Bilder in einem Block-Ordner werden als Varianten gemischt. Der
Dateiname darf frei gewählt werden. Unterstützt werden PNG, JPG, JPEG,
BMP und WEBP.

Die Bilder dürfen unterschiedliche Größen und Seitenverhältnisse haben.
Das Spiel schneidet sie mittig quadratisch zu und skaliert sie pixelig
auf die Texturgröße der Blöcke. Transparenz in PNG-Bildern bleibt erhalten.

Sobald mindestens ein gültiges Bild im Ordner liegt, ersetzt es für diesen
Block das normale Design. Ein leerer Ordner ändert nichts: Dann wird weiter
das vorhandene Bild aus assets/blocks/ oder die Standardfarbe benutzt.

Beispiele für Block-Ordner:
    grass, dirt, stone, cobblestone, wood, leaves, sand, coal_ore

Der Ordnername muss exakt dem Blocknamen aus utils/constants.py entsprechen.
Zum Beispiel kommen die Bilder für Gras in den Ordner "grass".
