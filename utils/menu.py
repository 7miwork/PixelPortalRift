"""
utils/menu.py – Hauptmenü, Pausenmenü und Save/Load-UI für PixelPortalRift 3D
"""

from ursina import (
    Entity, Text, camera, color, destroy, invoke, mouse,
)
from utils.save_system import SaveSystem


class MenuPanel(Entity):
    def __init__(self, title, width=0.5, height=0.7):
        super().__init__(parent=camera.ui, enabled=False, z=-10)
        self.buttons = []
        self.selected_button = 0
        self.bg = Entity(
            parent=self, model="quad", scale=(4, 3),
            color=color.rgba(0, 0, 0, 0.7), z=0.10,
        )
        self.panel = Entity(
            parent=self, model="quad",
            scale=(width, height),
            color=color.rgba(0.12, 0.12, 0.14, 0.95), z=-0.10,
        )
        self.title = Text(
            parent=self, text=title, origin=(0, 0),
            y=height / 2 - 0.08, scale=3.8, color=color.white, z=-0.20,
        )

    def add_button(self, text, action, y_offset=0, scale=0.08):
        btn = Entity(
            parent=self,
            model="quad",
            y=y_offset,
            scale=(0.55, scale * 1.35),
            color=color.rgba(0.3, 0.3, 0.35, 1),
            collider="box",
            z=-0.30,
        )
        btn._menu_action = action
        btn.label = Text(
            parent=self,
            text=text,
            origin=(0, 0),
            y=y_offset,
            scale=3.2,
            z=-0.40,
            color=color.white,
        )
        btn.normal_color = color.rgba(0.3, 0.3, 0.35, 1)
        btn.hover_color = color.rgba(0.45, 0.45, 0.5, 1)
        btn.normal_scale_y = scale * 1.35
        self.buttons.append(btn)
        self.update_button_selection()
        return btn

    def enable(self):
        self.enabled = True
        self.selected_button = 0
        self.update_button_selection()
        mouse.locked = False
        mouse.visible = True
        invoke(self._force_mouse_enabled, delay=0.05)

    def _force_mouse_enabled(self):
        if self.enabled:
            mouse.locked = False
            mouse.visible = True

    def disable(self):
        self.enabled = False
        mouse.locked = True
        mouse.visible = False

    def destroy_buttons(self):
        for btn in self.buttons:
            if getattr(btn, "label", None):
                destroy(btn.label)
            destroy(btn)
        self.buttons.clear()

    def update(self):
        """Sorgt dafür, dass die Maus im Menü sichtbar und entsperrt bleibt."""
        if self.enabled:
            mouse.locked = False
            mouse.visible = True
            hovered_index = next(
                (i for i, button in enumerate(self.buttons)
                 if getattr(button, "hovered", False)),
                None,
            )
            if hovered_index is not None:
                self.selected_button = hovered_index
                self.update_button_selection()

    def input(self, key):
        """Leertaste/Escape im Menü blockieren, damit sie nicht an das Spiel durchgereicht werden."""
        if not self.enabled:
            return False
        if key in ("escape",):
            return True
        if key == "left mouse down":
            hovered_button = getattr(mouse, "hovered_entity", None)
            for button in self.buttons:
                if button is hovered_button or getattr(button, "hovered", False):
                    action = getattr(button, "_menu_action", None)
                    if action:
                        action()
                        return True
            return False
        if key in ("up arrow", "w", "scroll up"):
            self.selected_button = max(0, self.selected_button - 1)
            self.update_button_selection()
            return True
        if key in ("down arrow", "s", "scroll down"):
            self.selected_button = min(len(self.buttons) - 1, self.selected_button + 1)
            self.update_button_selection()
            return True
        if key in ("enter", "return", "space"):
            if 0 <= self.selected_button < len(self.buttons):
                action = getattr(self.buttons[self.selected_button], "_menu_action", None)
                if action:
                    action()
            return True
        return False

    def update_button_selection(self):
        for i, button in enumerate(self.buttons):
            selected = i == self.selected_button
            button.scale_y = button.normal_scale_y * 1.08 if selected else button.normal_scale_y
            button.color = button.hover_color if selected else button.normal_color


class MainMenu(MenuPanel):
    def __init__(self, on_new_game, on_load_game, on_quit):
        super().__init__(title="PixelPortalRift", width=0.68, height=0.78)
        self.on_new_game = on_new_game
        self.on_load_game = on_load_game
        self.on_quit = on_quit

        self.add_button("Neues Spiel", self._new_game, y_offset=0.15)
        self.add_button("Laden", self._load, y_offset=0.05)
        self.add_button("Beenden", self._quit, y_offset=-0.05)

        self.status = Text(
            parent=self, text="", origin=(0, 0),
            y=-0.30, scale=1.7, color=color.rgba(0.8, 0.8, 0.8, 1),
        )

    def _new_game(self):
        self.disable()
        self.on_new_game()

    def _load(self):
        self.destroy_buttons()
        saves = SaveSystem().list_saves()
        y = 0.15
        if not saves:
            self.add_button("(keine Spielstände)", lambda: None, y_offset=y)
            y -= 0.1
        else:
            for save in saves:
                label = f"{save['name']}  ({save.get('dimension', '?')})"
                btn = self.add_button(
                    label,
                    lambda s=save['name']: self._load_save(s),
                    y_offset=y,
                )
                y -= 0.12
        self.add_button("Zurück", self._back, y_offset=y - 0.02)

    def _load_save(self, slot_name):
        self.destroy_buttons()
        save_system = SaveSystem()
        ok, msg = save_system.load_game(slot_name)
        if ok:
            self.status.text = msg
            self.on_load_game(slot_name)
        else:
            self.status.text = msg
            invoke(self._clear_status, delay=2.5)
            self._build_main_buttons()

    def _back(self):
        self.destroy_buttons()
        self._build_main_buttons()
        self.status.text = ""

    def _build_main_buttons(self):
        self.add_button("Neues Spiel", self._new_game, y_offset=0.15)
        self.add_button("Laden", self._load, y_offset=0.05)
        self.add_button("Beenden", self._quit, y_offset=-0.05)

    def _quit(self):
        self.on_quit()

    def _clear_status(self):
        self.status.text = ""


class PauseMenu(MenuPanel):
    def __init__(self, on_resume, on_save, on_load, on_main_menu, on_quit):
        super().__init__(title="Pause", width=0.68, height=0.78)
        self.on_resume = on_resume
        self.on_save = on_save
        self.on_load = on_load
        self.on_main_menu = on_main_menu
        self.on_quit = on_quit

        self.add_button("Fortsetzen", self._resume, y_offset=0.15)
        self.add_button("Speichern", self._save, y_offset=0.05)
        self.add_button("Laden", self._load, y_offset=-0.05)
        self.add_button("Hauptmenü", self._main_menu, y_offset=-0.15)
        self.add_button("Beenden", self._quit, y_offset=-0.25)

        self.status = Text(
            parent=self, text="", origin=(0, 0),
            y=-0.32, scale=1.7, color=color.rgba(0.8, 0.8, 0.8, 1),
        )

    def _resume(self):
        self.disable()
        self.on_resume()

    def _save(self):
        ok, msg = self.on_save()
        self.status.text = msg
        if ok:
            invoke(self._clear_status, delay=2.5)

    def _load(self):
        self.destroy_buttons()
        saves = SaveSystem().list_saves()
        y = 0.15
        if not saves:
            self.add_button("(keine Spielstände)", lambda: None, y_offset=y)
            y -= 0.1
        else:
            for save in saves:
                label = f"{save['name']}  ({save.get('dimension', '?')})"
                self.add_button(
                    label,
                    lambda s=save['name']: self._load_save(s),
                    y_offset=y,
                )
                y -= 0.12
        self.add_button("Zurück", self._back, y_offset=y - 0.02)

    def _load_save(self, slot_name):
        ok, msg = self.on_load(slot_name)
        self.status.text = msg
        if ok:
            self.disable()
            self.on_resume()
        else:
            invoke(self._clear_status, delay=2.5)

    def _back(self):
        self.destroy_buttons()
        self.add_button("Fortsetzen", self._resume, y_offset=0.15)
        self.add_button("Speichern", self._save, y_offset=0.05)
        self.add_button("Laden", self._load, y_offset=-0.05)
        self.add_button("Hauptmenü", self._main_menu, y_offset=-0.15)
        self.add_button("Beenden", self._quit, y_offset=-0.25)
        self.status.text = ""

    def _main_menu(self):
        self.disable()
        self.on_main_menu()

    def _quit(self):
        self.on_quit()

    def _clear_status(self):
        self.status.text = ""

class MenuManager:
    def __init__(self, game):
        self.game = game
        self.save_system = SaveSystem()
        self.main_menu = None
        self.pause_menu = None
        self.in_game = False

    def show_main_menu(self):
        self.in_game = False
        self.main_menu = MainMenu(
            on_new_game=self._start_new_game,
            on_load_game=self._start_loaded_game,
            on_quit=self._quit_game,
        )
        self.main_menu.enable()
        self.game._set_game_active(False)
        if getattr(self.game, "hud_text", None):
            self.game.hud_text.enabled = False

    def hide_main_menu(self):
        if self.main_menu:
            self.main_menu.disable()
            destroy(self.main_menu)
            self.main_menu = None

    def show_pause_menu(self):
        if not self.in_game:
            return
        self.pause_menu = PauseMenu(
            on_resume=self._resume_game,
            on_save=self._save_game,
            on_load=self._load_game,
            on_main_menu=self._return_to_main_menu,
            on_quit=self._quit_game,
        )
        self.pause_menu.enable()
        self.game._set_game_active(False)

    def hide_pause_menu(self):
        if self.pause_menu:
            self.pause_menu.disable()
            destroy(self.pause_menu)
            self.pause_menu = None

    def _start_new_game(self):
        self.hide_main_menu()
        self.game.start_new_game()
        self.in_game = True
        if getattr(self.game, "hud_text", None):
            self.game.hud_text.enabled = True

    def _start_loaded_game(self, slot_name):
        self.hide_main_menu()
        ok, msg = self.game.load_game(slot_name)
        if ok:
            self.in_game = True
            if getattr(self.game, "hud_text", None):
                self.game.hud_text.enabled = True
        else:
            self.show_main_menu()

    def _quit_game(self):
        self.game.app.quit()

    def _resume_game(self):
        self.hide_pause_menu()
        self.game._set_game_active(True)

    def _save_game(self):
        return self.game.save_game()

    def _load_game(self, slot_name):
        return self.game.load_game(slot_name)

    def _return_to_main_menu(self):
        self.hide_pause_menu()
        self.game.stop_game()
        self.in_game = False
        self.show_main_menu()

    def _quit_game(self):
        self.game.app.quit()

