import discord
import logging
from typing import Dict, Any

logger = logging.getLogger("IslamFatwa.views.settings")

COLOR_OPTIONS = {
    0x0a58ca: "Königsblau (Branding)",
    0x11806a: "Smaragdgrün (Klassisch)",
    0x0f5e54: "Tiefes Schiefer-Teal",
    0xe74c3c: "Karmesinrot",
    0xffc107: "Goldgelb"
}

STYLE_OPTIONS = {
    "success": "Grün (Erfolg)",
    "primary": "Blau (Primär)",
    "secondary": "Grau (Sekundär)"
}

class ColorSelect(discord.ui.Select):
    def __init__(self, current_color: int):
        options = []
        for code, name in COLOR_OPTIONS.items():
            options.append(discord.SelectOption(
                label=name,
                value=str(code),
                default=(code == current_color)
            ))
        super().__init__(
            placeholder="Theme-Farbe wählen...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="settings_color_select"
        )

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if view:
            view.temp_embed_color = int(self.values[0])
            await view.update_panel(interaction)


class BookmarkStyleSelect(discord.ui.Select):
    def __init__(self, current_style: str):
        options = []
        for key, name in STYLE_OPTIONS.items():
            options.append(discord.SelectOption(
                label=name,
                value=key,
                default=(key == current_style)
            ))
        super().__init__(
            placeholder="Lesezeichen Button-Farbe...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="settings_style_select"
        )

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if view:
            view.temp_bookmark_button_style = self.values[0]
            await view.update_panel(interaction)


class SettingsDashboardView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=300)
        self.bot = bot
        
        # Load active settings into temporary state
        self.temp_embed_color = bot.settings.get("embed_color")
        self.temp_search_limit = bot.settings.get("search_limit")
        self.temp_bookmark_button_style = bot.settings.get("bookmark_button_style")
        self.temp_daily_fatwa_enabled = bot.settings.get("daily_fatwa_enabled")
        self.temp_daily_fatwa_mode = bot.settings.get("daily_fatwa_mode")
        self.temp_daily_channel_id = bot.settings.get("daily_channel_id")
        self.temp_show_thumbnails = bot.settings.get("show_thumbnails")
        
        self.prepare_items()

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="⚙️ Bot-Konfiguration & Einstellungen",
            description="Passe das Design und Verhalten des **Islam Fatwa** Bots an. Alle Änderungen können unten konfiguriert und anschließend gespeichert werden.",
            color=self.temp_embed_color
        )
        
        embed.set_author(
            name="Islam Fatwa • Settings",
            url="https://islamfatwa.net/",
            icon_url="https://islamfatwa.net/images/apple-touch-icon.png"
        )
        if self.temp_show_thumbnails:
            embed.set_thumbnail(url="https://islamfatwa.net/images/apple-touch-icon.png")

        # Color label
        color_name = COLOR_OPTIONS.get(self.temp_embed_color, f"Benutzerdefiniert ({hex(self.temp_embed_color)})")
        style_name = STYLE_OPTIONS.get(self.temp_bookmark_button_style, self.temp_bookmark_button_style)
        
        daily_channel_mention = "*Nicht konfiguriert*"
        if self.temp_daily_channel_id:
            daily_channel_mention = f"<#{self.temp_daily_channel_id}>"

        embed.add_field(
            name="🎨 Design & Ästhetik",
            value=(
                f"• **Theme-Farbe:** {color_name}\n"
                f"• **Lesezeichen Button:** {style_name}\n"
                f"• **Bilder-Vorschau (Thumbnails):** {'✅ AN' if self.temp_show_thumbnails else '❌ AUS'}"
            ),
            inline=False
        )

        embed.add_field(
            name="🔍 Sucheinstellungen",
            value=f"• **Anzahl Suchergebnisse:** `{self.temp_search_limit}` (max. parallel geladen)",
            inline=False
        )

        embed.add_field(
            name="🕌 Täglicher Fatwa-Post (Automatisch)",
            value=(
                f"• **Status:** {'✅ Aktiviert' if self.temp_daily_fatwa_enabled else '❌ Deaktiviert'}\n"
                f"• **Posting-Kanal:** {daily_channel_mention}\n"
                f"• **Modus:** `{'Neueste' if self.temp_daily_fatwa_mode == 'latest' else 'Zufällig'}`"
            ),
            inline=False
        )

        embed.set_footer(
            text="Tippe auf 'Speichern', um die Änderungen in settings.json zu übernehmen.",
            icon_url="https://islamfatwa.net/images/favicon.png"
        )
        return embed

    def prepare_items(self):
        self.clear_items()
        
        # Row 1: Dropdown Color
        self.add_item(ColorSelect(self.temp_embed_color))
        
        # Row 2: Dropdown Bookmark Style
        self.add_item(BookmarkStyleSelect(self.temp_bookmark_button_style))
        
        # Row 3: Config buttons (Limits & Toggles)
        # Search limit cycle button
        self.add_item(discord.ui.Button(
            style=discord.ButtonStyle.primary,
            label=f"Limit: {self.temp_search_limit}",
            emoji="🔢",
            custom_id="btn_set_limit",
            row=2
        ))
        
        # Daily Fatwa status toggle
        self.add_item(discord.ui.Button(
            style=discord.ButtonStyle.success if self.temp_daily_fatwa_enabled else discord.ButtonStyle.danger,
            label=f"Täglich: {'AN' if self.temp_daily_fatwa_enabled else 'AUS'}",
            emoji="📅",
            custom_id="btn_toggle_daily",
            row=2
        ))
        
        # Daily Fatwa mode toggle
        self.add_item(discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label=f"Tägl. Modus: {'Neu' if self.temp_daily_fatwa_mode == 'latest' else 'Zufall'}",
            emoji="🔄",
            custom_id="btn_toggle_daily_mode",
            row=2
        ))

        # Show thumbnails toggle
        self.add_item(discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label=f"Vorschau: {'AN' if self.temp_show_thumbnails else 'AUS'}",
            emoji="🖼️",
            custom_id="btn_toggle_thumbs",
            row=3
        ))

        # Channel set to current channel
        self.add_item(discord.ui.Button(
            style=discord.ButtonStyle.primary,
            label="Kanal festlegen",
            emoji="📍",
            custom_id="btn_set_channel",
            row=3
        ))

        # Row 4/5: Actions (Save & Reset)
        self.add_item(discord.ui.Button(
            style=discord.ButtonStyle.success,
            label="Änderungen speichern",
            emoji="💾",
            custom_id="btn_save_settings",
            row=4
        ))
        self.add_item(discord.ui.Button(
            style=discord.ButtonStyle.danger,
            label="Zurücksetzen",
            emoji="↩️",
            custom_id="btn_reset_settings",
            row=4
        ))

    async def update_panel(self, interaction: discord.Interaction):
        self.prepare_items()
        embed = self.build_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    # Intercept all button interactions
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Standard check: only let admins run operations, but slash command check handles this mostly
        custom_id = interaction.data.get("custom_id")
        
        if custom_id == "btn_set_limit":
            # Cycle limit 1 -> 3 -> 5 -> 1
            limits = [1, 3, 5]
            current_idx = limits.index(self.temp_search_limit) if self.temp_search_limit in limits else 1
            self.temp_search_limit = limits[(current_idx + 1) % len(limits)]
            await self.update_panel(interaction)
            
        elif custom_id == "btn_toggle_daily":
            self.temp_daily_fatwa_enabled = not self.temp_daily_fatwa_enabled
            await self.update_panel(interaction)
            
        elif custom_id == "btn_toggle_daily_mode":
            self.temp_daily_fatwa_mode = "random" if self.temp_daily_fatwa_mode == "latest" else "latest"
            await self.update_panel(interaction)
            
        elif custom_id == "btn_toggle_thumbs":
            self.temp_show_thumbnails = not self.temp_show_thumbnails
            await self.update_panel(interaction)
            
        elif custom_id == "btn_set_channel":
            self.temp_daily_channel_id = interaction.channel_id
            await self.update_panel(interaction)
            
        elif custom_id == "btn_save_settings":
            await interaction.response.defer()
            # Save state into bot settings
            self.bot.settings.set("embed_color", self.temp_embed_color)
            self.bot.settings.set("search_limit", self.temp_search_limit)
            self.bot.settings.set("bookmark_button_style", self.temp_bookmark_button_style)
            self.bot.settings.set("daily_fatwa_enabled", self.temp_daily_fatwa_enabled)
            self.bot.settings.set("daily_fatwa_mode", self.temp_daily_fatwa_mode)
            self.bot.settings.set("daily_channel_id", self.temp_daily_channel_id)
            self.bot.settings.set("show_thumbnails", self.temp_show_thumbnails)
            self.bot.settings.save()
            
            # Recreate views and inform cog loops if necessary
            # e.g., register the persistent BookmarkView with the new style
            try:
                # We need to recreate the persistent BookmarkView style.
                # In discord.py, you can't easily remove a view with the same ID except by restarting or
                # adding the view again, adding the view overrides the old callbacks
                # Let's register it to be safe
                from views.reference_view import BookmarkView
                self.bot.add_view(BookmarkView(self.temp_bookmark_button_style))
            except Exception as e:
                logger.error(f"Error updating persistent bookmark view dynamically: {e}")

            save_embed = discord.Embed(
                title="✅ Einstellungen gespeichert!",
                description="Deine Konfigurationsänderungen wurden erfolgreich in `settings.json` persistiert und auf alle Bot-Komponenten angewendet.",
                color=self.temp_embed_color
            )
            await interaction.followup.send(embed=save_embed, ephemeral=True)
            # Re-render main panel to show saved state
            await self.update_panel(interaction)
            
        elif custom_id == "btn_reset_settings":
            # Discard temp changes and reload from file
            self.bot.settings.load()
            self.temp_embed_color = self.bot.settings.get("embed_color")
            self.temp_search_limit = self.bot.settings.get("search_limit")
            self.temp_bookmark_button_style = self.bot.settings.get("bookmark_button_style")
            self.temp_daily_fatwa_enabled = self.bot.settings.get("daily_fatwa_enabled")
            self.temp_daily_fatwa_mode = self.bot.settings.get("daily_fatwa_mode")
            self.temp_daily_channel_id = self.bot.settings.get("daily_channel_id")
            self.temp_show_thumbnails = self.bot.settings.get("show_thumbnails")
            await self.update_panel(interaction)

        return True
