import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv

# Hier laden wir den Einstellungs-Manager und das Lesezeichen-Menü
from utils.settings_manager import SettingsManager
from views.reference_view import BookmarkView

# Logging einrichten (für Fehlersuche und Statusmeldungen in der Konsole)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("IslamFatwa.main")

# Umgebungsvariablen aus der .env-Datei laden
load_dotenv()

class IslamFatwaBot(commands.Bot):
    def __init__(self) -> None:
        # Standard-Berechtigungen (Intents) für den Bot festlegen
        intents = discord.Intents.default()
        intents.guilds = True
        intents.messages = True
        intents.message_content = True
        intents.reactions = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None  # Standard-Hilfebefehl deaktivieren, da wir Slash-Commands nutzen
        )
        
        # Einstellungen laden
        self.settings = SettingsManager()

    async def setup_hook(self) -> None:
        # Bot-Erweiterungen (Cogs) laden
        logger.info("Lade die Bot-Erweiterungen (Cogs)...")
        await self.load_extension("cogs.reference_cog")
        await self.load_extension("cogs.settings_cog")

        # Das Lesezeichen-Menü registrieren, damit es auch nach einem Neustart aktiv bleibt
        logger.info("Registriere das Lesezeichen-Menü...")
        self.add_view(BookmarkView(self.settings.get("bookmark_button_style")))

        # Slash-Commands global mit Discord synchronisieren
        logger.info("Synchronisiere Slash-Commands mit Discord...")
        try:
            synced = await self.tree.sync()
            logger.info(f"Cool, habe {len(synced)} Befehl(e) global synchronisiert!")
        except Exception as e:
            logger.error(f"Mist, die Synchronisierung der Slash-Commands ist schiefgelaufen: {e}", exc_info=True)

    async def on_ready(self) -> None:
        logger.info(f"Eingeloggt als {self.user} (ID: {self.user.id})")
        logger.info("------ Der Bot ist startklar! ------")


def main() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token or token == "YOUR_DISCORD_BOT_TOKEN":
        logger.error("BOT_TOKEN wurde in der .env-Datei nicht gefunden.")
        print("\n[!] Fehler: Bitte trage deinen BOT_TOKEN in die .env-Datei im Hauptverzeichnis ein.\n")
        return

    bot = IslamFatwaBot()
    
    try:
        bot.run(token)
    except discord.LoginFailure:
        logger.critical("Login fehlgeschlagen: Der angegebene BOT_TOKEN ist ungültig.")
    except Exception as e:
        logger.critical(f"Kritischer Fehler beim Ausführen des Bots: {e}", exc_info=True)


if __name__ == "__main__":
    main()
