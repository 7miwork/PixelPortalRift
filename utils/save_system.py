import json
import os
from datetime import datetime

class SaveSystem:
    def __init__(self, save_dir="data/saves"):
        self.save_dir = save_dir
        self.ensure_save_directory()
    
    def ensure_save_directory(self):
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
    
    def save_game(self, game_state, slot_name="save1"):
        save_path = os.path.join(self.save_dir, f"{slot_name}.json")
        
        save_data = {
            "timestamp": datetime.now().isoformat(),
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
            "mobs": game_state["mob_manager"].get_save_data()
        }
        
        try:
            with open(save_path, 'w') as f:
                json.dump(save_data, f, indent=2)
            return True, "Game saved successfully!"
        except Exception as e:
            return False, f"Error saving game: {str(e)}"
    
    def load_game(self, slot_name="save1"):
        save_path = os.path.join(self.save_dir, f"{slot_name}.json")
        
        if not os.path.exists(save_path):
            return None, "No save file found!"
        
        try:
            with open(save_path, 'r') as f:
                save_data = json.load(f)
            return save_data, "Game loaded successfully!"
        except Exception as e:
            return None, f"Error loading game: {str(e)}"
    
    def list_saves(self):
        saves = []
        if os.path.exists(self.save_dir):
            for filename in os.listdir(self.save_dir):
                if filename.endswith('.json'):
                    save_path = os.path.join(self.save_dir, filename)
                    try:
                        with open(save_path, 'r') as f:
                            data = json.load(f)
                        saves.append({
                            "name": filename[:-5],
                            "timestamp": data.get("timestamp", "Unknown"),
                            "dimension": data.get("current_dimension", "Unknown")
                        })
                    except:
                        pass
        return saves
    
    def delete_save(self, slot_name="save1"):
        save_path = os.path.join(self.save_dir, f"{slot_name}.json")
        
        if os.path.exists(save_path):
            try:
                os.remove(save_path)
                return True, "Save deleted!"
            except Exception as e:
                return False, f"Error deleting save: {str(e)}"
        return False, "Save not found!"
