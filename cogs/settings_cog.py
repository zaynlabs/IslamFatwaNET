import discord
from discord.ext import commands
from discord import app_commands
import logging
from views.settings_view import SettingsDashboardView

logger = logging.getLogger("IslamFatwa.cogs.settings")

class SettingsCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="settings", description="Öffnet das Einstellungs-Panel für den Islam Fatwa Bot")
    @app_commands.default_permissions(administrator=True)
    async def settings(self, interaction: discord.Interaction) -> None:
        """Öffnet das Einstellungs-Menü für den Bot (nur für Admins sichtbar)."""
        logger.info(f"Der User {interaction.user} (ID: {interaction.user.id}) hat das Einstellungs-Panel geöffnet.")
        view = SettingsDashboardView(self.bot)
        embed = view.build_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SettingsCog(bot))
