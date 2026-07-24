"""
utils/save_system.py – Speichern und Laden des Spielstands
============================================================

Dieses Modul enthält die Klasse SaveSystem, die den gesamten
Spielstand in einer JSON-Datei speichert und wieder laden kann.

Der Spieler speichert mit Taste F5 und lädt mit Taste F9.
Die Speicherdaten enthalten:
- Spieler-Position, Leben, Hunger
- Inventar (alle Gegenstände)
- Aktuelle Welt (alle Blöcke)
- Aktuelle Dimension und besuchte Dimensionen
- Portale und Gegner
- Den dimension_cache (alle besuchten Welten)

Die Daten werden im Ordner "data/saves/" als JSON-Dateien gespeichert.
"""

import json
import os
from datetime import datetime


class SaveSystem:
    """
    Verwaltet das Speichern und Laden des Spielstands.
    
    Wichtige Attribute:
        save_dir: Verzeichnis, in dem die Spielstände gespeichert werden
                  (standardmäßig "data/saves")
    
    Die Spielstände werden als JSON-Dateien gespeichert.
    JSON ist ein Text-Format, das man auch mit einem Editor lesen kann.
    """
    
    def __init__(self, save_dir="data/saves"):
        """
        Initialisiert das Speichersystem.
        
        :param save_dir: Ordner für die Spielstände (wird erstellt, falls nicht vorhanden)
        """
        self.save_dir = save_dir
        self.ensure_save_directory()
    
    def ensure_save_directory(self):
        """Stellt sicher, dass der Speicher-Ordner existiert."""
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
    
    def save_game(self, game_state, slot_name="save1"):
        """
        Speichert den aktuellen Spielstand.
        
        Sammelt alle wichtigen Daten aus dem Spiel und schreibt sie
        als JSON-Datei. Der dimension_cache wird komplett mitgespeichert,
        sodass beim Laden alle Welten sofort wiederhergestellt werden können.
        
        :param game_state: Dictionary mit allen Spiel-Daten (aus get_game_state())
        :param slot_name: Name des Speicher-Slots (z.B. "save1")
        :return: (True, "Erfolgsmeldung") oder (False, "Fehlermeldung")
        """
        save_path = os.path.join(self.save_dir, f"{slot_name}.json")
        
        # Alle relevanten Daten sammeln
        save_data = {
            "timestamp": datetime.now().isoformat(),  # Aktuelles Datum + Uhrzeit
            "player": {
                "x": game_state["player"].x,
                "y": game_state["player"].y,
                "health": game_state["player"].health,
                "hunger": game_state["player"].hunger,
                "facing_right": game_state["player"].facing_right
            },
            "inventory": game_state["inventory"].get_save_data(),
            "world": game_state["world"].get_save_data(),
            "current_dimension": game_state["current_dimension"],
            "visited_dimensions": list(game_state["visited_dimensions"]),
            "portals": game_state["portal_system"].get_save_data(),
            "mobs": game_state["mob_manager"].get_save_data(),
            # Der dimension_cache speichert alle besuchten Welten komplett.
            # Dadurch gehen beim Laden keine Welten-Daten verloren.
            "dimension_cache": game_state.get("dimension_cache", {})
        }
        
        try:
            with open(save_path, 'w') as f:
                json.dump(save_data, f, indent=2)  # indent=2 = lesbare Formatierung
            return True, "Spiel gespeichert!"
        except Exception as e:
            return False, f"Fehler beim Speichern: {str(e)}"
    
    def load_game(self, slot_name="save1"):
        """
        Lädt einen gespeicherten Spielstand.
        
        :param slot_name: Name des Speicher-Slots (z.B. "save1")
        :return: (save_data, "Meldung") oder (None, "Fehlermeldung")
        """
        save_path = os.path.join(self.save_dir, f"{slot_name}.json")
        
        if not os.path.exists(save_path):
            return None, "Kein Spielstand gefunden!"
        
        try:
            with open(save_path, 'r') as f:
                save_data = json.load(f)
            return save_data, "Spiel geladen!"
        except Exception as e:
            return None, f"Fehler beim Laden: {str(e)}"
    
    def list_saves(self):
        """
        Listet alle vorhandenen Spielstände auf.
        
        :return: Liste mit Dictionaries (Name, Datum, Dimension)
        """
        saves = []
        if os.path.exists(self.save_dir):
            for filename in os.listdir(self.save_dir):
                if filename.endswith('.json'):
                    save_path = os.path.join(self.save_dir, filename)
                    try:
                        with open(save_path, 'r') as f:
                            data = json.load(f)
                        saves.append({
                            "name": filename[:-5],  # ".json" entfernen
                            "timestamp": data.get("timestamp", "Unbekannt"),
                            "dimension": data.get("current_dimension", "Unbekannt")
                        })
                    except:
                        pass  # Beschädigte Dateien ignorieren
        return saves
    
    def delete_save(self, slot_name="save1"):
        """
        Löscht einen Spielstand.
        
        :param slot_name: Name des Speicher-Slots
        :return: (True, "Meldung") oder (False, "Fehlermeldung")
        """
        save_path = os.path.join(self.save_dir, f"{slot_name}.json")
        
        if os.path.exists(save_path):
            try:
                os.remove(save_path)
                return True, "Spielstand gelöscht!"
            except Exception as e:
                return False, f"Fehler beim Löschen: {str(e)}"
        return False, "Spielstand nicht gefunden!"