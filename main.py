import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv

# Import settings manager and persistent view
from utils.settings_manager import SettingsManager
from views.reference_view import BookmarkView

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("IslamFatwa.main")

# Load environment variables
load_dotenv()

class IslamFatwaBot(commands.Bot):
    def __init__(self) -> None:
        # Set up intents
        intents = discord.Intents.default()
        intents.guilds = True
        intents.messages = True
        intents.message_content = True
        intents.reactions = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None  # Disable default help since this is a slash command bot
        )
        
        # Load settings
        self.settings = SettingsManager()

    async def setup_hook(self) -> None:
        # Load cogs/extensions
        logger.info("Loading extensions...")
        await self.load_extension("cogs.reference_cog")
        await self.load_extension("cogs.settings_cog")

        # Register persistent views
        logger.info("Registering persistent views...")
        self.add_view(BookmarkView(self.settings.get("bookmark_button_style")))

        # Sync slash commands globally
        logger.info("Syncing slash commands globally...")
        try:
            synced = await self.tree.sync()
            logger.info(f"Successfully synced {len(synced)} command(s) globally.")
        except Exception as e:
            logger.error(f"Failed to sync slash commands: {e}", exc_info=True)

    async def on_ready(self) -> None:
        logger.info(f"Bot logged in as {self.user} (ID: {self.user.id})")
        logger.info("------ Bot is ready ------")


def main() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token or token == "YOUR_DISCORD_BOT_TOKEN":
        logger.error("BOT_TOKEN is not configured in the environment or .env file.")
        print("\n[!] Error: Please configure your BOT_TOKEN inside the .env file in the root directory.\n")
        return

    bot = IslamFatwaBot()
    
    try:
        bot.run(token)
    except discord.LoginFailure:
        logger.critical("Login failed: Invalid BOT_TOKEN provided.")
    except Exception as e:
        logger.critical(f"Fatal error during bot execution: {e}", exc_info=True)


if __name__ == "__main__":
    main()
