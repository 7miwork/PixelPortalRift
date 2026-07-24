"""
utils/__init__.py – Paket-Initialisierung
===========================================

Dieses Paket enthält alle Hilfsmodule für das Spiel PixelPortalRift.
Jedes Modul hat eine bestimmte Aufgabe:

- constants.py:    Alle festen Werte (Farben, Block-Eigenschaften, Rezepte, etc.)
- asset_loader.py: Lädt Bilder und erstellt Texturen für Blöcke, Items und Gegner
- world_gen.py:    Erzeugt die Block-Welt für jede Dimension
- player.py:       Steuert den Spieler (Bewegung, Kollision, Gesundheit, Hunger)
- inventory.py:    Verwaltet das Inventar (Gegenstände, Hotbar, Drag-and-Drop)
- crafting.py:     Crafting-System (Rezepte, Herstellung von Gegenständen)
- portal.py:       Portal-System und Dimensions-Riss (Übergang zwischen Welten)
- mob.py:          Gegner (Mobs) und deren Steuerung (KI, Spawnen, Kämpfen)
- save_system.py:  Speichern und Laden des Spielstands (JSON-Dateien)
"""

# Dieses leere __init__.py macht den utils-Ordner zu einem Python-Paket.
# Dadurch können wir "from utils.constants import ..." schreiben.