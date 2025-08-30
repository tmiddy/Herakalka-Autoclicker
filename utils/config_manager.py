import json
import os

class ConfigManager:
    def __init__(self, filename="config.json"):
        self.filename = filename
        app_data_path = os.getenv('APPDATA')
        self.config_folder = os.path.join(app_data_path, "Herakalka")
        os.makedirs(self.config_folder, exist_ok=True)
        self.filename = os.path.join(self.config_folder, filename)

    def save_settings(self, settings):
        try:
            with open(self.filename, 'w') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def load_settings(self):

        default_settings = {
            "main": {"hotkey": "Key.f6"},
            "simple": {},
            "minecraft": {},
            "macro": {},
            "pixel": {}
        }
        if not os.path.exists(self.filename):
            return default_settings
        try:
            with open(self.filename, 'r') as f:
                loaded = json.load(f)
                
                for key in default_settings:
                    if key not in loaded:
                        loaded[key] = default_settings[key]
                return loaded
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading or parsing config, using defaults: {e}")
            return default_settings