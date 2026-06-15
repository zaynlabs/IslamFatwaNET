import discord
import logging

logger = logging.getLogger("IslamFatwa.views")

class BookmarkView(discord.ui.View):
    """
    Ein Lesezeichen-Menü, das aktiv bleibt (persistent) und es Usern ermöglicht,
    Beiträge per Button-Klick in ihren privaten Nachrichten (DMs) abzuspeichern.
    """
    def __init__(self, style_str: str = "success"):
        super().__init__(timeout=None)
        # Button-Farbe dynamisch aus den Einstellungen laden
        style_map = {
            "success": discord.ButtonStyle.success,
            "primary": discord.ButtonStyle.primary,
            "secondary": discord.ButtonStyle.secondary
        }
        target_style = style_map.get(style_str, discord.ButtonStyle.success)
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.custom_id == "bookmark_fatwa_button":
                child.style = target_style

    @discord.ui.button(
        label="Als Lesezeichen speichern",
        style=discord.ButtonStyle.success,  # Passt farblich gut zum Speichern
        emoji="🔖",
        custom_id="bookmark_fatwa_button"
    )
    async def bookmark_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        message = interaction.message
        if not message or not message.embeds:
            await interaction.response.send_message(
                "❌ **Huch, das hat nicht geklappt!**\nIn dieser Nachricht steckt leider kein Fatwa, das ich speichern könnte.",
                ephemeral=True
            )
            return

        user = interaction.user
        
        # Lade-Status anzeigen
        await interaction.response.defer(ephemeral=True)

        try:
            # Embeds für die DMs duplizieren
            embeds_to_send = []
            for original_embed in message.embeds:
                cloned_embed = discord.Embed.from_dict(original_embed.to_dict())
                # In den DMs kennzeichnen, dass es sich um ein gespeichertes Lesezeichen handelt
                cloned_embed.set_author(
                    name="Islam Fatwa • Gespeichertes Lesezeichen",
                    url="https://islamfatwa.net/",
                    icon_url="https://islamfatwa.net/images/apple-touch-icon.png"
                )
                embeds_to_send.append(cloned_embed)

            # Die Embeds mit einer netten Nachricht an die DMs des Users senden
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
            # Schritt-für-Schritt-Anleitung, falls DMs deaktiviert sind
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
            logger.error(f"Fehler beim Senden des DM-Lesezeichens an User {user.id}: {e}", exc_info=True)
            await interaction.followup.send(
                "### ❌ Fehler beim Speichern\n"
                "Ich konnte dir das Lesezeichen leider nicht per Direktnachricht senden. Bitte versuch es in ein paar Minuten noch einmal.",
                ephemeral=True
            )
