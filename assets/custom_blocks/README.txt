Eigene Blockbilder – so geht's
===============================

Jeder Block hat einen eigenen Ordner in diesem Ordner (assets\custom_blocks\).
Dort legst du deine Bilddateien ab – nach Neustart des Spiels erscheinen sie
sofort in der Welt UND im Inventar / in der Hotbar.

Live-Beispiel: Ordner "grass" enthält "Gras1.png".


Schritt für Schritt
-------------------
1. Einen Block-Ordner öffnen, z. B.  assets\custom_blocks\dirt\
2. Dein Bild hineinkopieren
3. Die Datei umbenennen, z. B.  dreck_01.png
4. Spiel neu starten – fertig!


WICHTIG – so müssen die Namen sein
-----------------------------------
* Der ORDNERNAMEN muss exakt dem Blocknamen aus dem Spiel entsprechen
  (Groß-/Kleinschreibung beachten!). Erlaubt sind die 38 Namen aus der
  Liste unten. Beispiel: für den Block "dirt" heißt der Ordner "dirt".
* Der DATEINAME ist frei wählbar: dreck_01.png, MeinBild.png, bla.png ...
  Wichtig ist nur, dass die Datei eine der Endungen aus "Formate" hat.
* Mehrere Bilder in einem Ordner gelten als Varianten – das Spiel
  verwendet sie alle. Für das Icon im Inventar zählt der erste Name
  alphabetisch (deshalb Nummern wie _01, _02 empfohlen).
* Dateien, die DIREKT in assets\custom_blocks\ liegen (nicht in einem
  Block-Ordner), werden vom Spiel IGNORIERT. Dort liegt nur die Datei
  "vorlage.png" als Vorlage zum Kopieren.


Formate und Größe
-----------------
* Erlaubte Endungen: .png  .jpg  .jpeg  .bmp  .webp
* Die Größe und das Seitenverhältnis dürfen frei sein: das Spiel schneidet
  das Bild mittig quadratisch zu und skaliert es pixelig auf die Textur-
  größe. Transparenz in PNG-Bildern bleibt erhalten.
* "vorlage.png" ist magenta mit schwarzem Rahmen: Kopiere sie in einen
  Block-Ordner und ersetze sie durch dein eigenes Bild. Solange die
  Vorlage noch im Ordner ist, wird der Block magenta dargestellt – das
  heißt also: Hier fehlt noch dein Bild.


Was passiert, wenn kein Bild da ist?
-------------------------------------
* Leerer Ordner oder gar kein Ordner: der Block behält sein normales Bild
  aus assets\blocks\ (bzw. seine Farbe). Nichts geht kaputt.


Alle 38 Block-Ordner (Namen exakt so übernehmen)
------------------------------------------------
amethyst              ancient_key_vein      clay
coal_ore              cobblestone           contaminated_stone
coral                 crystal               crystal_key_vein
diamond_ore           dirt                  emerald_ore
frozen_key_vein       gold_ore              gravel
grass                 iron_ore              lead
leaves                nuclear_waste         obsidian
pearl_key_vein        pearl_ore             plutonium
portal                portal_frame_gem_world      portal_frame_grassland
portal_frame_nuclear_world     portal_frame_stone_world
portal_frame_water_world       reactor_core
ruby_ore              sand                  seaweed
stone                 uranium               water
wood
