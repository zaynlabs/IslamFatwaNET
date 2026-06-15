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
            placeholder="Theme-Farbe aussuchen...",
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
            placeholder="Lesezeichen-Button Farbe...",
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
    """
    Das Dashboard für die Bot-Einstellungen.
    Hier können Admins das Design und das automatische Posten anpassen.
    """
    def __init__(self, bot):
        super().__init__(timeout=300)
        self.bot = bot
        
        # Aktive Einstellungen in den temporären Zustand laden
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
            description="Hier kannst du den Islam Fatwa Bot nach deinen Wünschen einrichten. Unten einstellen und einfach speichern!",
            color=self.temp_embed_color
        )
        
        embed.set_author(
            name="Islam Fatwa • Settings",
            url="https://islamfatwa.net/",
            icon_url="https://islamfatwa.net/images/apple-touch-icon.png"
        )
        if self.temp_show_thumbnails:
            embed.set_thumbnail(url="https://islamfatwa.net/images/apple-touch-icon.png")

        # Bezeichnungen für Farben und Stile auslesen
        color_name = COLOR_OPTIONS.get(self.temp_embed_color, f"Benutzerdefiniert ({hex(self.temp_embed_color)})")
        style_name = STYLE_OPTIONS.get(self.temp_bookmark_button_style, self.temp_bookmark_button_style)
        
        daily_channel_mention = "*Nicht konfiguriert*"
        if self.temp_daily_channel_id:
            daily_channel_mention = f"<#{self.temp_daily_channel_id}>"

        embed.add_field(
            name="🎨 Design & Ästhetik",
            value=(
                f"• **Theme-Farbe:** {color_name}\n"
                f"• **Lesezeichen-Button:** {style_name}\n"
                f"• **Bilder-Vorschau:** {'✅ AN' if self.temp_show_thumbnails else '❌ AUS'}"
            ),
            inline=False
        )

        embed.add_field(
            name="🔍 Suche",
            value=f"• **Anzahl Suchergebnisse:** `{self.temp_search_limit}` (gleichzeitig geladen)",
            inline=False
        )

        embed.add_field(
            name="🕌 Täglicher Fatwa-Post",
            value=(
                f"• **Status:** {'✅ Aktiviert' if self.temp_daily_fatwa_enabled else '❌ Deaktiviert'}\n"
                f"• **Kanal:** {daily_channel_mention}\n"
                f"• **Modus:** `{'Neueste' if self.temp_daily_fatwa_mode == 'latest' else 'Zufällig'}`"
            ),
            inline=False
        )

        embed.set_footer(
            text="Klick auf 'Speichern', um deine Einstellungen zu sichern.",
            icon_url="https://islamfatwa.net/images/favicon.png"
        )
        return embed

    def prepare_items(self):
        self.clear_items()
        
        # Zeile 1: Dropdown Farbe
        self.add_item(ColorSelect(self.temp_embed_color))
        
        # Zeile 2: Dropdown Lesezeichen-Stil
        self.add_item(BookmarkStyleSelect(self.temp_bookmark_button_style))
        
        # Zeile 3: Konfigurations-Knöpfe
        # Suchlimit
        self.add_item(discord.ui.Button(
            style=discord.ButtonStyle.primary,
            label=f"Suchlimit: {self.temp_search_limit}",
            emoji="🔢",
            custom_id="btn_set_limit",
            row=2
        ))
        
        # Täglicher Post Status
        self.add_item(discord.ui.Button(
            style=discord.ButtonStyle.success if self.temp_daily_fatwa_enabled else discord.ButtonStyle.danger,
            label=f"Täglicher Post: {'AN' if self.temp_daily_fatwa_enabled else 'AUS'}",
            emoji="📅",
            custom_id="btn_toggle_daily",
            row=2
        ))
        
        # Täglicher Post Modus
        self.add_item(discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label=f"Modus: {'Neu' if self.temp_daily_fatwa_mode == 'latest' else 'Zufall'}",
            emoji="🔄",
            custom_id="btn_toggle_daily_mode",
            row=2
        ))

        # Bilder Vorschau an/aus
        self.add_item(discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label=f"Bilder: {'AN' if self.temp_show_thumbnails else 'AUS'}",
            emoji="🖼️",
            custom_id="btn_toggle_thumbs",
            row=3
        ))

        # Kanal auf den aktuellen Kanal festlegen
        self.add_item(discord.ui.Button(
            style=discord.ButtonStyle.primary,
            label="Kanal festlegen",
            emoji="📍",
            custom_id="btn_set_channel",
            row=3
        ))

        # Zeile 4: Aktionen (Speichern & Zurücksetzen)
        self.add_item(discord.ui.Button(
            style=discord.ButtonStyle.success,
            label="Speichern",
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

    # Alle Interaktionen verarbeiten
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        custom_id = interaction.data.get("custom_id")
        
        if custom_id == "btn_set_limit":
            # Limit im Kreis schalten: 1 -> 3 -> 5 -> 1
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
            # Werte in den Einstellungs-Manager übertragen
            self.bot.settings.set("embed_color", self.temp_embed_color)
            self.bot.settings.set("search_limit", self.temp_search_limit)
            self.bot.settings.set("bookmark_button_style", self.temp_bookmark_button_style)
            self.bot.settings.set("daily_fatwa_enabled", self.temp_daily_fatwa_enabled)
            self.bot.settings.set("daily_fatwa_mode", self.temp_daily_fatwa_mode)
            self.bot.settings.set("daily_channel_id", self.temp_daily_channel_id)
            self.bot.settings.set("show_thumbnails", self.temp_show_thumbnails)
            self.bot.settings.save()
            
            # Persistente Views mit neuem Button-Stil registrieren
            try:
                from views.reference_view import BookmarkView
                self.bot.add_view(BookmarkView(self.temp_bookmark_button_style))
            except Exception as e:
                logger.error(f"Fehler beim dynamischen Aktualisieren des persistenten Lesezeichen-Buttons: {e}")

            save_embed = discord.Embed(
                title="✅ Einstellungen gespeichert!",
                description="Alles klar! Deine Einstellungen wurden in `settings.json` gespeichert und übernommen.",
                color=self.temp_embed_color
            )
            await interaction.followup.send(embed=save_embed, ephemeral=True)
            # Panel neu laden, um den gespeicherten Stand anzuzeigen
            await self.update_panel(interaction)
            
        elif custom_id == "btn_reset_settings":
            # Änderungen verwerfen und aus der Datei neu laden
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
