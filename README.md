# 🕌 Islam Fatwa Discord Bot

Ein moderner, benutzerfreundlicher Discord-Bot zum Suchen, Lesen und Speichern von Rechtsurteilen (Fatawa) direkt von [islamfatwa.net](https://islamfatwa.net/). Komplett auf Deutsch, mit schickem Interface (Embeds, Knöpfe, Dropdown-Menüs) und praktischen Lesezeichen per Direktnachricht (DM).

---

## ⚡ Schnellstart für Windows (Ohne Vorkenntnisse)

Du musst keine Befehle in eine Konsole eintippen! Folge einfach diesen Schritten:

1. Lade das Projekt herunter und entpacke es.
2. Doppelklicke auf die Datei **`starten.bat`** im Hauptordner.
3. Der Assistent installiert automatisch alle benötigten Pakete und führt dich durch das Eintragen deines Discord-Bot-Tokens.

---

## 🛠️ Manuelle Installation & Setup (Für Fortgeschrittene)

### Voraussetzungen
Stelle sicher, dass du Python 3.8+ installiert hast.

1. **Repository klonen oder herunterladen:**
   ```bash
   git clone https://github.com/zaynlabs/IslamFatwaNET.git
   cd IslamFatwaNET
   ```

2. **Abhängigkeiten installieren:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Bot-Token einrichten:**
   Erstelle eine `.env`-Datei im Hauptverzeichnis des Bots und trage deinen Discord Bot-Token sowie optional den Kanal für den täglichen Post ein:
   ```env
   # Discord Bot Configuration
   BOT_TOKEN=DEIN_DISCORD_BOT_TOKEN
   
   # Kanal-ID für das tägliche Fatwa (kann auch über /einstellungen geändert werden)
   DAILY_CHANNEL_ID=123456789012345678
   ```

4. **Bot starten:**
   ```bash
   python main.py
   ```

---

## 🤖 Befehle (Slash-Commands)

- `🔍 /suche [suchbegriff] [kategorie] [gelehrter]` — Öffnet das interaktive Such-Dashboard.
- `🕌 /daily` — Postet das aktuelle Fatwa des Tages manuell in den Kanal.
- `🔄 /random` — Postet ein zufälliges Fatwa aus der Datenbank.
- `⚙️ /einstellungen` — Öffnet das Konfigurationsmenü (nur für Server-Admins).

---

## ⚙️ Einstellungen anpassen

Die Konfiguration wird in der `settings.json` im Hauptverzeichnis gespeichert. Du kannst dort oder direkt über `/einstellungen` im Discord folgende Dinge anpassen:

- `embed_color`: Hex-Farbe der Embed-Karten (z. B. Königsblau, Smaragdgrün, Karmesinrot).
- `bookmark_button_style`: Farbe des Lesezeichen-Buttons (Grün, Blau, Grau).
- `search_limit`: Maximale Anzahl der parallel geladenen Suchergebnisse (1, 3 oder 5).
- `daily_fatwa_enabled`: Schaltet den automatischen täglichen Post an/aus.
- `daily_fatwa_mode`: Legt fest, ob das tägliche Fatwa das *neueste* (`latest`) oder ein *zufälliges* (`random`) sein soll.
- `show_thumbnails`: Schaltet Vorschaubilder (Thumbnails) an/aus.

---

## 🧪 Tests ausführen

Um die Sitemap-Suche und den Scraper lokal auf Herz und Nieren zu prüfen, kannst du die Test-Suite starten:

```bash
# Einstellungs-Manager testen
python test_settings.py

# Scraper, Sitemap-Caching und Suche testen
python test_bot_scraper.py
```
