import json
import os
import logging
from typing import Dict, Any

logger = logging.getLogger("IslamFatwa.utils.settings_manager")

DEFAULT_SETTINGS = {
    "embed_color": 0x0a58ca,
    "search_limit": 3,
    "bookmark_button_style": "success",
    "daily_fatwa_enabled": True,
    "daily_fatwa_mode": "latest",
    "daily_channel_id": None,
    "show_thumbnails": True,
    "footer_text": "Quelle: islamfatwa.net • Fatwa-Datenbank nach Quran & Sunnah • Lesezeichen 🔖"
}

class SettingsManager:
    def __init__(self, filepath: str = "settings.json") -> None:
        self.filepath = filepath
        self.settings: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Loads settings from settings.json or initializes them with defaults if file doesn't exist."""
        if not os.path.exists(self.filepath):
            logger.info(f"Settings file {self.filepath} not found. Creating default settings.")
            self.settings = DEFAULT_SETTINGS.copy()
            self.save()
            return
        
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Merge with defaults to ensure all keys exist
            self.settings = DEFAULT_SETTINGS.copy()
            for key, val in data.items():
                if key == "embed_color" and isinstance(val, str):
                    try:
                        if val.startswith("0x") or val.startswith("0X"):
                            self.settings[key] = int(val, 16)
                        elif val.startswith("#"):
                            self.settings[key] = int(val[1:], 16)
                        else:
                            self.settings[key] = int(val, 16)
                    except ValueError:
                        logger.warning(f"Invalid hex color '{val}' in settings. Reverting to default.")
                        self.settings[key] = DEFAULT_SETTINGS["embed_color"]
                else:
                    self.settings[key] = val
            logger.info("Settings loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load settings from {self.filepath}: {e}", exc_info=True)
            self.settings = DEFAULT_SETTINGS.copy()

    def save(self) -> None:
        """Saves current settings to settings.json in a formatted JSON structure."""
        try:
            # We want to format the hex color nicely in the JSON file for readability
            save_data = self.settings.copy()
            # Convert color back to hex string format for JSON
            if isinstance(save_data["embed_color"], int):
                save_data["embed_color"] = f"0x{save_data['embed_color']:06x}"
            
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=4, ensure_ascii=False)
            logger.info("Settings saved successfully.")
        except Exception as e:
            logger.error(f"Failed to save settings to {self.filepath}: {e}", exc_info=True)

    def get(self, key: str, default: Any = None) -> Any:
        """Returns the value for the given settings key."""
        return self.settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Sets a settings key to a value. Note: call save() to persist changes."""
        self.settings[key] = value
