import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.settings_manager import SettingsManager

class TestSettingsManager(unittest.TestCase):
    def setUp(self):
        self.filename = "test_settings.json"
        if os.path.exists(self.filename):
            os.remove(self.filename)

    def tearDown(self):
        if os.path.exists(self.filename):
            os.remove(self.filename)

    def test_standard_erstellung(self):
        # 1. Das Instanziieren erstellt eine settings.json mit Standardwerten
        manager = SettingsManager(self.filename)
        self.assertTrue(os.path.exists(self.filename))
        self.assertEqual(manager.get("embed_color"), 0x0a58ca)
        self.assertEqual(manager.get("search_limit"), 3)
        self.assertEqual(manager.get("bookmark_button_style"), "success")
        self.assertTrue(manager.get("daily_fatwa_enabled"))
        self.assertTrue(manager.get("show_thumbnails"))

    def test_speichern_und_laden(self):
        # 2. Werte setzen und speichern sichert sie in der Datei
        manager = SettingsManager(self.filename)
        manager.set("embed_color", 0x11806a)
        manager.set("search_limit", 5)
        manager.set("bookmark_button_style", "primary")
        manager.set("daily_fatwa_enabled", False)
        manager.set("show_thumbnails", False)
        manager.save()

        # Einstellungen in einer neuen Manager-Instanz laden, um Festplatten-Speicherung zu prüfen
        manager2 = SettingsManager(self.filename)
        self.assertEqual(manager2.get("embed_color"), 0x11806a)
        self.assertEqual(manager2.get("search_limit"), 5)
        self.assertEqual(manager2.get("bookmark_button_style"), "primary")
        self.assertFalse(manager2.get("daily_fatwa_enabled"))
        self.assertFalse(manager2.get("show_thumbnails"))

    def test_hex_farbe_parsen(self):
        # 3. Hex-Farben als String (z.B. 0x0a58ca oder #123456) werden als Integer geparst
        with open(self.filename, "w", encoding="utf-8") as f:
            f.write('{"embed_color": "0x11806a", "search_limit": 1}')
        
        manager = SettingsManager(self.filename)
        self.assertEqual(manager.get("embed_color"), 0x11806a)
        self.assertEqual(manager.get("search_limit"), 1)

        # Fallback-Format mit # testen
        with open(self.filename, "w", encoding="utf-8") as f:
            f.write('{"embed_color": "#ffc107", "search_limit": 2}')
        
        manager2 = SettingsManager(self.filename)
        self.assertEqual(manager2.get("embed_color"), 0xffc107)

if __name__ == "__main__":
    unittest.main()
