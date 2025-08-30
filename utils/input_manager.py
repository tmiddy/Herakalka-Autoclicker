from PyQt6.QtCore import QThread, pyqtSignal
from pynput import keyboard, mouse
import time

class InputManager(QThread):
    primary_hotkey_pressed = pyqtSignal()
    secondary_hotkey_pressed = pyqtSignal(str)
    fast_click_detected = pyqtSignal()
    
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(InputManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized: return
        super().__init__()

        self.primary_keyboard_hotkey = set()
        self.primary_mouse_hotkey = None
        self.primary_hotkey_active = False

        self.secondary_hotkeys = {}
        self.current_keys = set()
        
        self.fast_click_settings = {'enabled': False, 'count': 3, 'max_interval_ms': 150}
        self.last_clicks_ts = []


        self.is_synthetic_click = False
        
        self.keyboard_listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.mouse_listener = mouse.Listener(on_click=self.on_click)
        self._initialized = True
            
    def set_primary_hotkey(self, hotkey_str):
        self.primary_keyboard_hotkey.clear()
        self.primary_mouse_hotkey = None
        if hotkey_str and hotkey_str.startswith("mouse."):
            button_map = {
                "mouse.left": mouse.Button.left, "mouse.right": mouse.Button.right,
                "mouse.middle": mouse.Button.middle, "mouse.x1": mouse.Button.x1,
                "mouse.x2": mouse.Button.x2,
            }
            self.primary_mouse_hotkey = button_map.get(hotkey_str)
        else:
            self.primary_keyboard_hotkey = self._parse_hotkey_str(hotkey_str)

    def set_fast_click_settings(self, enabled, count, max_interval_ms=150):
        self.fast_click_settings = {'enabled': enabled, 'count': count, 'max_interval_ms': max_interval_ms}
        self.last_clicks_ts = []

    def on_press(self, key):

        for key_str, key_obj in self.secondary_hotkeys.items():
            if key == key_obj:
                self.secondary_hotkey_pressed.emit(key_str)
        if key in self.primary_keyboard_hotkey:
            self.current_keys.add(key)
        is_subset = self.primary_keyboard_hotkey.issubset(self.current_keys)
        if self.primary_keyboard_hotkey and is_subset and not self.primary_hotkey_active:
            self.primary_hotkey_active = True
            self.primary_hotkey_pressed.emit()

    def on_release(self, key):

        if key in self.primary_keyboard_hotkey:
            self.primary_hotkey_active = False
        if key in self.current_keys:
            self.current_keys.remove(key)

    def on_click(self, x, y, button, pressed):

        if self.is_synthetic_click:
            return

        if pressed and button == self.primary_mouse_hotkey:
            self.primary_hotkey_pressed.emit()
            return

        if self.fast_click_settings['enabled'] and pressed and button == mouse.Button.left:
            current_time = time.perf_counter()
            if self.last_clicks_ts and (current_time - self.last_clicks_ts[-1]) * 1000 > self.fast_click_settings['max_interval_ms']:
                self.last_clicks_ts = []
            self.last_clicks_ts.append(current_time)
            if len(self.last_clicks_ts) >= self.fast_click_settings['count']:
                self.fast_click_detected.emit()
                self.last_clicks_ts = []


    def register_secondary_hotkey(self, key_str):
        key_obj = self._parse_key_str(key_str.lower());
        if key_obj: self.secondary_hotkeys[key_str.lower()] = key_obj
    def unregister_secondary_hotkey(self, key_str):
        if key_str.lower() in self.secondary_hotkeys: del self.secondary_hotkeys[key_str.lower()]
    def clear_secondary_hotkeys(self): self.secondary_hotkeys.clear()
    def _parse_hotkey_str(self, hotkey_str):
        parsed_keys = set()
        if not isinstance(hotkey_str, str): hotkey_str = "Key.f6"
        keys_to_parse = hotkey_str.split('+')
        for key_str in keys_to_parse:
            key_obj = self._parse_key_str(key_str)
            if key_obj: parsed_keys.add(key_obj)
        return parsed_keys
    def _parse_key_str(self, key_str):
        key_str_cleaned = key_str.strip().lower()
        if not key_str_cleaned: return None
        try: return keyboard.Key[key_str_cleaned.replace('key.', '')]
        except KeyError:
            if len(key_str_cleaned) == 1: return keyboard.KeyCode.from_char(key_str_cleaned)
        return None
    def run(self):
        self.keyboard_listener.start(); self.mouse_listener.start()
        self.keyboard_listener.join(); self.mouse_listener.join()
    def stop_listening(self):
        try:
            if self.keyboard_listener.is_alive(): self.keyboard_listener.stop()
            if self.mouse_listener.is_alive(): self.mouse_listener.stop()
        except Exception: pass