import os
import sys
import subprocess

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    print("=" * 60)
    print(" 🕌   Islam Fatwa Discord Bot - Setup-Assistent   👋")
    print("=" * 60)
    print()

def check_and_install_dependencies():
    print("Schritt 1: Prüfe benötigte Software-Pakete...")
    try:
        import discord
        import bs4
        import aiohttp
        import dotenv
        print("-> Super, alle Pakete sind bereits installiert!\n")
    except ImportError:
        print("Es fehlen noch ein paar Pakete. Ich installiere sie jetzt für dich...")
        try:
            # pip ausführen, um requirements.txt zu installieren
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("-> Installation erfolgreich abgeschlossen!\n")
        except Exception as e:
            print(f"\n[!] Fehler bei der Installation der Pakete: {e}")
            print("Bitte versuche es manuell in der Konsole mit: pip install -r requirements.txt")
            input("\nDrücke Enter zum Beenden...")
            sys.exit(1)

def configure_env():
    print("Schritt 2: Einstellungen für den Bot festlegen\n")
    
    # 1. BOT_TOKEN abfragen
    print("🔑 Discord Bot Token:")
    print("Diesen bekommst du im Discord-Entwicklerportal (https://discord.com/developers/applications).")
    print("Dort erstellst du eine 'Application', fügst unter 'Bot' einen Bot hinzu und klickst auf 'Reset Token'.\n")
    
    bot_token = ""
    while not bot_token:
        bot_token = input("Bitte füge deinen Bot-Token hier ein: ").strip()
        if not bot_token:
            print("Der Token darf nicht leer sein. Bitte gib einen gültigen Token ein.")
            
    # 2. DAILY_CHANNEL_ID abfragen
    print("\n📍 Täglicher Posting-Kanal (optional):")
    print("Das ist die ID des Kanals, in dem jeden Tag automatisch ein Fatwa gepostet wird.")
    print("Um die ID zu bekommen, aktiviere in den Discord-Einstellungen unter 'Erweitert' den 'Entwicklermodus'.")
    print("Mache dann einen Rechtsklick auf deinen Wunsch-Kanal und wähle 'Kanal-ID kopieren'.\n")
    
    channel_id = input("Kanal-ID hier einfügen (oder einfach Enter drücken zum Überspringen): ").strip()
    
    # .env Datei erstellen
    with open(".env", "w", encoding="utf-8") as f:
        f.write("# Discord Bot Configuration\n")
        f.write(f"BOT_TOKEN={bot_token}\n\n")
        f.write("# Channel ID where the daily fatwa will be posted\n")
        if channel_id:
            f.write(f"DAILY_CHANNEL_ID={channel_id}\n")
        else:
            f.write("DAILY_CHANNEL_ID=\n")
            
    print("\n-> Die Datei '.env' wurde erfolgreich erstellt und deine Einstellungen wurden gesichert!\n")

def main():
    clear_screen()
    print_banner()
    
    print("Hallo! Ich helfe dir dabei, deinen Islam Fatwa Bot einzurichten und zu starten.")
    print("Das Ganze dauert nur eine Minute.\n")
    
    input("Drücke Enter, um zu starten...")
    print()
    
    # 1. Pakete prüfen und installieren
    check_and_install_dependencies()
    
    # 2. Konfiguration anlegen
    configure_env()
    
    # 3. Bot starten?
    print("=" * 60)
    print("Die Einrichtung ist abgeschlossen! 🎉")
    print("=" * 60)
    print()
    
    start_now = input("Möchtest du den Bot jetzt direkt starten? (ja/nein): ").strip().lower()
    if start_now in ["ja", "j", "yes", "y"]:
        print("\nStarte den Bot... Drücke STRG + C in der Konsole, um den Bot wieder zu beenden.\n")
        try:
            # main.py starten
            subprocess.run([sys.executable, "main.py"])
        except KeyboardInterrupt:
            print("\nBot wurde gestoppt. Bis zum nächsten Mal! 👋")
    else:
        print("\nAlles klar! Du kannst den Bot jederzeit starten, indem du die Datei 'starten.bat' startest.")
        print("Viel Spaß mit deinem Bot! 👋")
        input("\nDrücke Enter zum Beenden...")

if __name__ == "__main__":
    main()
