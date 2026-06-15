import discord
import logging

logger = logging.getLogger("IslamFatwa.views")

class BookmarkView(discord.ui.View):
    """
    A persistent view that contains a button to allow users to bookmark
    embed messages to their DMs with advanced human-friendly feedback.
    """
    def __init__(self, style_str: str = "success"):
        super().__init__(timeout=None)
        # Apply button style dynamically from settings
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
        style=discord.ButtonStyle.success,  # Success style fits save action
        emoji="🔖",
        custom_id="bookmark_fatwa_button"
    )
    async def bookmark_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        message = interaction.message
        if not message or not message.embeds:
            await interaction.response.send_message(
                "❌ **Huch, das hat nicht geklappt!**\nDiese Nachricht enthält leider kein Fatwa, das gespeichert werden kann.",
                ephemeral=True
            )
            return

        user = interaction.user
        
        # Defer response to show loading state
        await interaction.response.defer(ephemeral=True)

        try:
            # Clone embeds to send to DMs
            embeds_to_send = []
            for original_embed in message.embeds:
                cloned_embed = discord.Embed.from_dict(original_embed.to_dict())
                # Highlight in DM that it is a saved bookmark with branding
                cloned_embed.set_author(
                    name="Islam Fatwa • Gespeichertes Lesezeichen",
                    url="https://islamfatwa.net/",
                    icon_url="https://islamfatwa.net/images/apple-touch-icon.png"
                )
                embeds_to_send.append(cloned_embed)

            # Send the embeds to user's DMs with a warm, friendly text
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
                "Ich habe dir das Fatwa soeben als Direktnachricht (DM) zugestellt. Bitte schaue in deinen Posteingang! 📩",
                ephemeral=True
            )
        except discord.Forbidden:
            # Step-by-step guide in German on how to fix closed DMs
            await interaction.followup.send(
                "### ⚠️ Nachricht nicht zustellbar\n"
                "Deine Direktnachrichten (DMs) für diesen Server sind derzeit blockiert. Bitte folge diesen Schritten, um DMs zu erlauben:\n\n"
                "1️⃣ **Rechtsklick** auf das Server-Icon (auf dem Smartphone: gedrückt halten).\n"
                "2️⃣ Wähle ⚙️ **Privatsphäre-Einstellungen**.\n"
                "3️⃣ Aktiviere den Schalter bei 💬 **Direktnachrichten von Servermitgliedern erlauben**.\n\n"
                "*Klicke danach einfach erneut auf den Button, um das Lesezeichen zu speichern! ✨*",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error sending DM bookmark to user {user.id}: {e}", exc_info=True)
            await interaction.followup.send(
                "### ❌ Fehler beim Speichern\n"
                "Ich konnte dir das Lesezeichen leider nicht per Direktnachricht senden. Bitte versuche es in ein paar Minuten erneut.",
                ephemeral=True
            )
