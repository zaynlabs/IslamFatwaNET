import discord
import logging
import re
from typing import List, Dict, Any

logger = logging.getLogger("IslamFatwa.views.search")

# ==========================================
# 📊 Datenmodell
# ==========================================

class SearchState:
    """
    Speichert den Zustand (Filter & Suchwort) der aktuellen Suchanfrage eines Users.
    """
    def __init__(self, query: str = "", category: str = None, scholar: str = None):
        self.query = query
        self.category = category  # z. B. 'gottesdienste-ibadah' oder None
        self.scholar = scholar    # z. B. 'Ibn Baz' oder None


# ==========================================
# 📝 Such-Modals (Eingabemaske)
# ==========================================

class SearchKeywordModal(discord.ui.Modal):
    """
    Ein modales Fenster, über das User ihren Suchbegriff eingeben oder ändern können.
    """
    def __init__(self, dashboard_view: "SearchDashboardView"):
        super().__init__(title="Suchbegriff eingeben")
        self.dashboard_view = dashboard_view

        self.keyword_input = discord.ui.TextInput(
            label="Was suchst du?",
            placeholder="z. B. Wudu, Ghusl, Fasten, Erbschaft...",
            default=dashboard_view.state.query,
            required=True,
            min_length=1,
            max_length=100
        )
        self.add_item(self.keyword_input)

    async def on_submit(self, interaction: discord.Interaction):
        # Eingegebenen Begriff sichern und das Such-Dashboard aktualisieren
        self.dashboard_view.state.query = self.keyword_input.value.strip()
        await self.dashboard_view.update_dashboard(interaction)


# ==========================================
# 📁 Auswahllisten (Dropdowns)
# ==========================================

class CategorySelect(discord.ui.Select):
    """
    Dropdown-Menü zur Filterung der Suche nach Kategorien.
    """
    def __init__(self, current_value: str = None):
        options = [
            discord.SelectOption(label="Alle Kategorien", value="all", default=current_value is None),
            discord.SelectOption(label="Aqidah (Fundamente)", value="aqidah-tauhid", default=current_value == "aqidah-tauhid"),
            discord.SelectOption(label="Manhaj (Methodik)", value="manhaj", default=current_value == "manhaj"),
            discord.SelectOption(label="Ibadah (Gottesdienste)", value="gottesdienste-ibadah", default=current_value == "gottesdienste-ibadah"),
            discord.SelectOption(label="Qur'an & Sunnah", value="qur-an-sunnah-offenbarungsschriften", default=current_value == "qur-an-sunnah-offenbarungsschriften"),
            discord.SelectOption(label="Krankheit & Heilung", value="krankheit-heilung", default=current_value == "krankheit-heilung"),
            discord.SelectOption(label="Soziale Angelegenheiten", value="soziale-angelegenheiten", default=current_value == "soziale-angelegenheiten"),
            discord.SelectOption(label="Kleidung & Körper", value="kleidung-schmuck", default=current_value == "kleidung-schmuck")
        ]
        super().__init__(
            placeholder="Filter nach einer Kategorie...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="search_category_select"
        )

    async def callback(self, interaction: discord.Interaction):
        val = self.values[0]
        view: SearchDashboardView = self.view
        view.state.category = None if val == "all" else val
        await view.update_dashboard(interaction)


class ScholarSelect(discord.ui.Select):
    """
    Dropdown-Menü zur Filterung der Suche nach bestimmten Gelehrten.
    """
    def __init__(self, current_value: str = None):
        options = [
            discord.SelectOption(label="Alle Gelehrten", value="all", default=current_value is None),
            discord.SelectOption(label="Scheich Ibn Bāz", value="Ibn Baz", default=current_value == "Ibn Baz"),
            discord.SelectOption(label="Scheich al-Uthaimīn", value="Uthaimin", default=current_value == "Uthaimin"),
            discord.SelectOption(label="Scheich al-Fauzān", value="Fauzan", default=current_value == "Fauzan"),
            discord.SelectOption(label="Scheich al-Luḥaidān", value="Luhaidan", default=current_value == "Luhaidan"),
            discord.SelectOption(label="Scheich al-Albānī", value="Albani", default=current_value == "Albani"),
            discord.SelectOption(label="Ständiges Komitee (Lajna)", value="Lajna", default=current_value == "Lajna")
        ]
        super().__init__(
            placeholder="Filter nach einem Gelehrten...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="search_scholar_select"
        )

    async def callback(self, interaction: discord.Interaction):
        val = self.values[0]
        view: SearchDashboardView = self.view
        view.state.scholar = None if val == "all" else val
        await view.update_dashboard(interaction)


# ==========================================
# 🔘 Interaktive Buttons
# ==========================================

class SearchItemButton(discord.ui.Button):
    """
    Ein durchnummerierter Button, der für einen Suchtreffer steht.
    Lädt das entsprechende Rechtsurteil direkt in den Chat.
    """
    def __init__(self, index: int, label: str, emoji: str, custom_id: str):
        super().__init__(
            style=discord.ButtonStyle.primary,
            label=label,
            emoji=emoji,
            custom_id=custom_id
        )
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        view: SearchDashboardView = self.view
        if not view:
            return

        try:
            # Details des ausgewählten Fatwas holen und Embed erstellen
            fatwa = view.current_results[self.index]
            detail_embed = view.cog.create_fatwa_embed(fatwa)
            
            # Ansicht auf die Detail-Ansicht wechseln
            detail_view = FatwaDetailView(view.cog, view, detail_embed)
            await interaction.followup.edit_message(
                message_id=interaction.message.id,
                embed=detail_embed,
                view=detail_view
            )
        except Exception as e:
            logger.error(f"Fehler beim Anzeigen der Fatwa-Details: {e}", exc_info=True)
            error_embed = discord.Embed(
                color=0xe74c3c
            )
            error_embed.description = (
                "### ❌ Ladefehler\n"
                "Ich konnte das ausgewählte Fatwa leider nicht laden.\n\n"
                f"> ⚠️ **Details:** *{str(e)}*"
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)


class EditKeywordButton(discord.ui.Button):
    """
    Ein grauer Button, der das Eingabefenster für das Suchwort öffnet.
    """
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="Suchwort ändern",
            emoji="📝",
            custom_id="search_edit_keyword_btn"
        )

    async def callback(self, interaction: discord.Interaction):
        view: SearchDashboardView = self.view
        if view:
            await interaction.response.send_modal(SearchKeywordModal(view))


class ResetButton(discord.ui.Button):
    """
    Ein roter Button, der alle Filter und Suchbegriffe sofort leert.
    """
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.danger,
            label="Zurücksetzen",
            emoji="🔄",
            custom_id="search_reset_btn"
        )

    async def callback(self, interaction: discord.Interaction):
        view: SearchDashboardView = self.view
        if view:
            view.state.query = ""
            view.state.category = None
            view.state.scholar = None
            await view.update_dashboard(interaction)


# ==========================================
# 🖥️ Dashboard Views (Hauptmenüs)
# ==========================================

class SearchDashboardView(discord.ui.View):
    """
    Die Hauptansicht für die Suche. Bietet Knöpfe zur Navigation und zeigt Ergebnisse an.
    """
    def __init__(self, cog, state: SearchState):
        super().__init__(timeout=300)  # Das Menü schaltet sich nach 5 Min. Inaktivität ab
        self.cog = cog
        self.state = state
        self.current_results: List[Dict[str, Any]] = []
        self.search_embed: discord.Embed = None

    async def update_dashboard(self, interaction: discord.Interaction):
        """Wendet die aktuellen Filter an und baut das Dashboard neu auf."""
        if not interaction.response.is_done():
            await interaction.response.defer()

        try:
            # Suche mit den aktuellen Filtern ausführen
            self.current_results = await self.cog.execute_filtered_search(self.state)
            
            # Embed und Bedienelemente aktualisieren
            self.search_embed = self.build_embed()
            self.prepare_items()
            
            await interaction.followup.edit_message(
                message_id=interaction.message.id,
                embed=self.search_embed,
                view=self
            )
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren des Such-Dashboards: {e}", exc_info=True)
            error_embed = discord.Embed(
                color=0xe74c3c
            )
            error_embed.description = (
                "### ❌ Fehler bei der Suche\n"
                "Beim Filtern der Ergebnisse gab es ein Problem.\n\n"
                f"> ⚠️ **Details:** *{str(e)}*"
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

    def build_embed(self) -> discord.Embed:
        """Erstellt das Status-Embed für das Such-Dashboard."""
        color = self.cog.bot.settings.get("embed_color")
        embed = discord.Embed(
            title="🔍 Fatwa-Suche",
            color=color
        )

        embed.set_author(
            name="Islam Fatwa",
            url="https://islamfatwa.net/",
            icon_url="https://islamfatwa.net/images/apple-touch-icon.png"
        )
        if self.cog.bot.settings.get("show_thumbnails"):
            embed.set_thumbnail(url="https://islamfatwa.net/images/apple-touch-icon.png")

        cat_labels = {
            "aqidah-tauhid": "Aqidah (Fundamente)",
            "manhaj": "Manhaj (Methodik)",
            "gottesdienste-ibadah": "Ibadah (Gottesdienste)",
            "qur-an-sunnah-offenbarungsschriften": "Qur'an & Sunnah",
            "krankheit-heilung": "Krankheit & Heilung",
            "soziale-angelegenheiten": "Soziale Angelegenheiten",
            "kleidung-schmuck": "Kleidung & Körper"
        }
        
        cat_label = cat_labels.get(self.state.category, "Alle Kategorien")
        scholar_label = self.state.scholar or "Alle Gelehrten"
        query_label = f"**{self.state.query}**" if self.state.query else "*Keins*"

        desc_parts = [
            "Hier kannst du nach Rechtsurteilen (Fatawa) auf **islamfatwa.net** suchen.",
            "",
            "### ⚙️ Deine aktiven Filter",
            f"• 📝 **Suchbegriff:** {query_label}",
            f"• 📁 **Kategorie:** *{cat_label}*",
            f"• 👤 **Gelehrter:** *{scholar_label}*",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ]

        if not self.state.query and not self.state.category and not self.state.scholar:
            desc_parts.extend([
                "### 💡 Erste Schritte",
                "Wähle eine Kategorie oder einen Gelehrten aus den Dropdowns oder klick auf **Suchwort ändern**, um die Suche zu starten."
            ])
        elif not self.current_results:
            desc_parts.extend([
                "### ⚠️ Keine Ergebnisse",
                "Dazu habe ich leider nichts gefunden. Versuch's mal mit anderen Filtern oder einem anderen Begriff!"
            ])
        else:
            search_limit = self.cog.bot.settings.get("search_limit", 3)
            desc_parts.append(f"### 📋 Suchergebnisse (Top {search_limit})")
            emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
            for i, res in enumerate(self.current_results[:search_limit]):
                emoji = emojis[i]
                desc_parts.extend([
                    f"{emoji} **{res['title']}**",
                    f"> 👤 *{res['scholar']}* • 📁 *{res['category']}*",
                    f"> 📅 *{res['date']}* • 🔗 [Im Browser lesen]({res['url']})",
                    ""
                ])

        embed.description = "\n".join(desc_parts)
        embed.set_footer(
            text="Such-Panel • Wähle unten einen Beitrag zum Lesen aus • islamfatwa.net",
            icon_url="https://islamfatwa.net/images/favicon.png"
        )
        return embed

    def prepare_items(self):
        """Baut die interaktiven Dropdowns und Buttons für das Menü zusammen."""
        self.clear_items()
        
        # Filter-Dropdowns hinzufügen
        self.add_item(CategorySelect(self.state.category))
        self.add_item(ScholarSelect(self.state.scholar))
        
        # Gefundene Treffer als Lese-Buttons hinzufügen
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
        search_limit = self.cog.bot.settings.get("search_limit", 3)
        for i in range(min(len(self.current_results), search_limit)):
            self.add_item(SearchItemButton(
                index=i,
                label=f"Beitrag {i+1} öffnen",
                emoji=emojis[i],
                custom_id=f"search_read_btn_{i}"
            ))

        # Kontroll-Buttons hinzufügen
        self.add_item(EditKeywordButton())
        self.add_item(ResetButton())


class FatwaDetailView(discord.ui.View):
    """
    Detail-Ansicht für einen Treffer. Erlaubt Speichern oder Zurückkehren zur Liste.
    """
    def __init__(self, cog, search_view: SearchDashboardView, detail_embed: discord.Embed):
        super().__init__(timeout=180)
        self.cog = cog
        self.search_view = search_view
        self.detail_embed = detail_embed

        # Button-Farbe aus den Einstellungen laden
        style_map = {
            "success": discord.ButtonStyle.success,
            "primary": discord.ButtonStyle.primary,
            "secondary": discord.ButtonStyle.secondary
        }
        style_str = self.cog.bot.settings.get("bookmark_button_style")
        target_style = style_map.get(style_str, discord.ButtonStyle.success)
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.custom_id == "bookmark_fatwa_detail_btn":
                child.style = target_style

    @discord.ui.button(
        label="Als Lesezeichen speichern",
        style=discord.ButtonStyle.success,
        emoji="🔖",
        custom_id="bookmark_fatwa_detail_btn"
    )
    async def bookmark_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        message = interaction.message
        if not message or not message.embeds:
            await interaction.response.send_message(
                "❌ **Lesezeichen fehlgeschlagen!** Ich konnte kein Fatwa-Embed in dieser Nachricht finden.",
                ephemeral=True
            )
            return

        user = interaction.user
        await interaction.response.defer(ephemeral=True)

        try:
            embeds_to_send = []
            for original_embed in message.embeds:
                cloned_embed = discord.Embed.from_dict(original_embed.to_dict())
                cloned_embed.set_author(
                    name="Islam Fatwa • Gespeichertes Lesezeichen",
                    url="https://islamfatwa.net/",
                    icon_url="https://islamfatwa.net/images/apple-touch-icon.png"
                )
                embeds_to_send.append(cloned_embed)

            dm_channel = await user.create_dm()
            await dm_channel.send(
                content=(
                    "### 🔖 Gespeichertes Lesezeichen\n"
                    f"Hallo {user.mention}! 👋\n"
                    "Du hast folgendes Rechtsurteil von **islamfatwa.net** in deiner Lesezeichen-Sammlung gespeichert:"
                ),
                embeds=embeds_to_send
            )
            
            await interaction.followup.send(
                "### ✅ Lesezeichen gespeichert\n"
                "Ich hab dir das Fatwa als Direktnachricht (DM) geschickt. Schau mal in deinen Posteingang! 📩",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.followup.send(
                "### ⚠️ Nachricht nicht zustellbar\n"
                "Deine Direktnachrichten (DMs) für diesen Server sind leider blockiert. So kannst du sie erlauben:\n\n"
                "1️⃣ **Rechtsklick** auf das Server-Icon (auf dem Handy: gedrückt halten).\n"
                "2️⃣ Geh auf ⚙️ **Privatsphäre-Einstellungen**.\n"
                "3️⃣ Aktiviere den Schalter bei 💬 **Direktnachrichten von Servermitgliedern erlauben**.\n\n"
                "*Danach einfach nochmal auf den Button klicken, um das Lesezeichen zu speichern! ✨*",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Fehler beim Senden des DM-Lesezeichens aus der Detailansicht an User {user.id}: {e}", exc_info=True)
            await interaction.followup.send(
                "### ❌ Fehler beim Speichern\n"
                "Ich konnte dir das Lesezeichen leider nicht als DM schicken. Versuch es bitte gleich nochmal.",
                ephemeral=True
            )

    @discord.ui.button(
        label="Zurück zur Suche",
        style=discord.ButtonStyle.secondary,
        emoji="◀️",
        custom_id="back_to_search_dashboard_btn"
    )
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Zum Suchmenü zurückkehren und alte Knöpfe wiederherstellen
        await interaction.response.defer()
        await interaction.followup.edit_message(
            message_id=interaction.message.id,
            embed=self.search_view.search_embed,
            view=self.search_view
        )
