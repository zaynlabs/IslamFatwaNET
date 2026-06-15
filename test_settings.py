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

    def test_default_creation(self):
        # 1. Instantiating creates a settings.json file with default values
        manager = SettingsManager(self.filename)
        self.assertTrue(os.path.exists(self.filename))
        self.assertEqual(manager.get("embed_color"), 0x0a58ca)
        self.assertEqual(manager.get("search_limit"), 3)
        self.assertEqual(manager.get("bookmark_button_style"), "success")
        self.assertTrue(manager.get("daily_fatwa_enabled"))
        self.assertTrue(manager.get("show_thumbnails"))

    def test_set_and_save(self):
        # 2. Setting values and saving persists them to file
        manager = SettingsManager(self.filename)
        manager.set("embed_color", 0x11806a)
        manager.set("search_limit", 5)
        manager.set("bookmark_button_style", "primary")
        manager.set("daily_fatwa_enabled", False)
        manager.set("show_thumbnails", False)
        manager.save()

        # Load in another manager instance to verify disk persistence
        manager2 = SettingsManager(self.filename)
        self.assertEqual(manager2.get("embed_color"), 0x11806a)
        self.assertEqual(manager2.get("search_limit"), 5)
        self.assertEqual(manager2.get("bookmark_button_style"), "primary")
        self.assertFalse(manager2.get("daily_fatwa_enabled"))
        self.assertFalse(manager2.get("show_thumbnails"))

    def test_hex_color_parsing(self):
        # 3. Hex colors saved as string format (e.g. 0x0a58ca or #123456) parse back to integers
        with open(self.filename, "w", encoding="utf-8") as f:
            f.write('{"embed_color": "0x11806a", "search_limit": 1}')
        
        manager = SettingsManager(self.filename)
        self.assertEqual(manager.get("embed_color"), 0x11806a)
        self.assertEqual(manager.get("search_limit"), 1)

        # Test fallback format with #
        with open(self.filename, "w", encoding="utf-8") as f:
            f.write('{"embed_color": "#ffc107", "search_limit": 2}')
        
        manager2 = SettingsManager(self.filename)
        self.assertEqual(manager2.get("embed_color"), 0xffc107)

if __name__ == "__main__":
    unittest.main()
