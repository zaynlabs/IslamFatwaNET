import json
import os
import logging
from typing import Dict, Any

logger = logging.getLogger("IslamFatwa.utils.settings_manager")

# Standard-Einstellungen, falls keine settings.json existiert
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
        """Lädt die Einstellungen aus settings.json oder erstellt sie neu mit den Standardwerten."""
        if not os.path.exists(self.filepath):
            logger.info(f"Die Einstellungsdatei {self.filepath} wurde nicht gefunden. Erstelle Standard-Einstellungen.")
            self.settings = DEFAULT_SETTINGS.copy()
            self.save()
            return
        
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Mit Standardwerten zusammenführen, um sicherzustellen, dass alle Keys vorhanden sind
            self.settings = DEFAULT_SETTINGS.copy()
            for key, val in data.items():
                if key == "embed_color" and isinstance(val, str):
                    try:
                        # Farbwert (Hex) sauber in Integer umwandeln
                        if val.startswith("0x") or val.startswith("0X"):
                            self.settings[key] = int(val, 16)
                        elif val.startswith("#"):
                            self.settings[key] = int(val[1:], 16)
                        else:
                            self.settings[key] = int(val, 16)
                    except ValueError:
                        logger.warning(f"Ungültiger Hex-Farbcode '{val}' in den Einstellungen. Setze auf Standard zurück.")
                        self.settings[key] = DEFAULT_SETTINGS["embed_color"]
                else:
                    self.settings[key] = val
            logger.info("Einstellungen wurden erfolgreich geladen.")
        except Exception as e:
            logger.error(f"Fehler beim Laden der Einstellungen aus {self.filepath}: {e}", exc_info=True)
            self.settings = DEFAULT_SETTINGS.copy()

    def save(self) -> None:
        """Speichert die aktuellen Einstellungen in der settings.json."""
        try:
            # Wir möchten die Farbe im JSON als lesbaren Hex-String speichern (z.B. "0x0a58ca")
            save_data = self.settings.copy()
            if isinstance(save_data["embed_color"], int):
                save_data["embed_color"] = f"0x{save_data['embed_color']:06x}"
            
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=4, ensure_ascii=False)
            logger.info("Einstellungen wurden erfolgreich gespeichert.")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Einstellungen in {self.filepath}: {e}", exc_info=True)

    def get(self, key: str, default: Any = None) -> Any:
        """Gibt den Wert für den angegebenen Einstellungsschlüssel zurück."""
        return self.settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Setzt eine Einstellung auf einen neuen Wert. (Danach save() aufrufen, um es zu speichern!)"""
        self.settings[key] = value
