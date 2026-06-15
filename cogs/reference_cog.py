import discord
from discord.ext import commands, tasks
from discord import app_commands
from bs4 import BeautifulSoup
import aiohttp
import asyncio
import random
import re
import os
import logging
import xml.etree.ElementTree as ET
from typing import Optional, List, Dict, Any

# Import the custom views
from views.reference_view import BookmarkView
from views.search_view import SearchDashboardView, SearchState

logger = logging.getLogger("IslamFatwa.cogs.reference")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

class ReferenceCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Cached list of all URLs from sitemap.xml
        self.sitemap_urls: List[str] = []
        # Start the background loop
        self.daily_fatwa_loop.start()

    def cog_unload(self):
        self.daily_fatwa_loop.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info("ReferenceCog is ready and background task loop is active.")

    # --- Sitemap Index Loading & Searching ---

    async def load_sitemap(self) -> None:
        """Fetches and parses sitemap.xml to cache all URLs."""
        try:
            logger.info("Fetching sitemap.xml from islamfatwa.net...")
            xml_content = await self._fetch_html("https://islamfatwa.net/sitemap.xml")
            
            # Use ElementTree to parse sitemap XML safely
            root = ET.fromstring(xml_content.encode("utf-8"))
            # Extract namespace if present (e.g. {http://www.sitemaps.org/schemas/sitemap/0.9})
            namespace = root.tag.split("}")[0] + "}" if root.tag.startswith("{") else ""
            
            urls = []
            for url_node in root.findall(f".//{namespace}loc"):
                if url_node.text:
                    urls.append(url_node.text.strip())
            
            self.sitemap_urls = urls
            logger.info(f"Sitemap parsed successfully. Cached {len(self.sitemap_urls)} URLs.")
        except Exception as e:
            logger.error(f"Error loading sitemap.xml: {e}", exc_info=True)

    def search_sitemap_urls(self, query: str) -> List[str]:
        """Filters cached sitemap URLs based on query keywords, prioritizing article links and excluding categories."""
        def normalize(s: str) -> str:
            s = s.lower()
            # Normalize German umlauts and clean symbols
            s = s.replace("ü", "ue").replace("ä", "ae").replace("ö", "oe").replace("ß", "ss")
            s = re.sub(r'[^a-z0-9\s-]', '', s)
            return s

        norm_query = normalize(query)
        keywords = norm_query.split()
        if not keywords:
            return []

        matches = []
        for url in self.sitemap_urls:
            norm_url = normalize(url)
            if all(kw in norm_url for kw in keywords):
                matches.append(url)

        # Filter and prioritize actual article URLs (numeric IDs in final segment, not parent directories/categories)
        article_matches = []
        for m in matches:
            last_segment = m.rstrip("/").split("/")[-1]
            if re.match(r'^\d+-', last_segment):
                # Filter out parent category pages by checking if this URL is a prefix of any other URL in the sitemap
                is_category = False
                for other_u in self.sitemap_urls:
                    if other_u != m and other_u.startswith(m + "/"):
                        is_category = True
                        break
                if not is_category:
                    article_matches.append(m)

        return article_matches if article_matches else matches

    # --- Scraping Logic ---

    async def _fetch_html(self, url: str, allow_404: bool = False) -> str:
        """Helper to fetch HTML content from a URL asynchronously using aiohttp."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=HEADERS, timeout=10) as response:
                    if response.status == 404 and allow_404:
                        return await response.text()
                    if response.status != 200:
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message=f"HTTP status {response.status}"
                        )
                    return await response.text()
            except asyncio.TimeoutError:
                raise Exception("Die Website hat zu lange gebraucht, um zu antworten (Timeout).")
            except aiohttp.ClientError as e:
                raise Exception(f"Netzwerkfehler beim Abrufen der Seite: {str(e)}")

    async def scrape_article_detail(self, url: str) -> Dict[str, Any]:
        """Scrapes the details of a single fatwa article."""
        html = await self._fetch_html(url)
        soup = BeautifulSoup(html, "html.parser")
        
        item_page = soup.find(class_="item-page")
        if not item_page:
            raise Exception("Das Fatwa-Format auf der Seite konnte nicht erkannt werden.")

        # Title
        title_el = item_page.find("h1")
        title = title_el.get_text().strip() if title_el else "Unbenanntes Urteil"

        # Category
        category = "Allgemein"
        category_el = item_page.find(class_="category-name")
        if category_el:
            category_text = category_el.get_text().strip()
            category = re.sub(r"^(Kategorie|Category):\s*", "", category_text, flags=re.IGNORECASE)

        # Scholar (Gelehrter)
        scholar = "Unbekannter Gelehrter"
        createdby_el = item_page.find(class_="createdby")
        if createdby_el:
            name_el = createdby_el.find(itemprop="name")
            if name_el:
                scholar = name_el.get_text().strip()
            else:
                scholar = createdby_el.get_text().strip()

        # Date
        date_str = "Unbekannt"
        create_el = item_page.find(class_="create")
        if create_el:
            time_el = create_el.find("time")
            if time_el:
                date_str = time_el.get_text().strip()
            else:
                date_str = create_el.get_text().strip()

        # Question and Answer
        body_div = item_page.find(class_="com-content-article__body")
        frage_text = "Keine Frage vorhanden."
        antwort_text = "Keine Antwort vorhanden."
        
        if body_div:
            # Try to get specific question and answer structures
            frage_div = body_div.find(class_="frage")
            fatwa_div = body_div.find(class_="fatwa")
            
            if frage_div:
                # Remove audio tags and forms
                for tag in frage_div.find_all(["audio", "form"]):
                    tag.decompose()
                frage_text = frage_div.get_text(separator="\n").strip()
            
            if fatwa_div:
                for tag in fatwa_div.find_all(["audio", "form"]):
                    tag.decompose()
                antwort_text = fatwa_div.get_text(separator="\n").strip()
            
            # Fallback if specific classes aren't found
            if not frage_div and not fatwa_div:
                clean_body = BeautifulSoup(str(body_div), "html.parser")
                for tag in clean_body.find_all(["audio", "form", "script", "style"]):
                    tag.decompose()
                
                full_text = clean_body.get_text(separator="\n").strip()
                # Try simple split on "Frage:" / "Antwort:"
                parts = re.split(r"\b(Frage|Antwort):\s*", full_text, flags=re.IGNORECASE)
                if len(parts) >= 5:
                    frage_text = parts[2].strip()
                    antwort_text = parts[4].strip()
                else:
                    antwort_text = full_text
                    frage_text = "Siehe Beschreibung."
        
        # Clean up excessive newlines
        frage_text = re.sub(r"\n{3,}", "\n\n", frage_text)
        antwort_text = re.sub(r"\n{3,}", "\n\n", antwort_text)

        return {
            "title": title,
            "category": category,
            "scholar": scholar,
            "date": date_str,
            "frage": frage_text,
            "antwort": antwort_text,
            "url": url
        }

    async def scrape_max_start_offset(self) -> int:
        """Parses the homepage and returns the maximum pagination start value (fallback)."""
        try:
            html = await self._fetch_html("https://islamfatwa.net/")
            soup = BeautifulSoup(html, "html.parser")
            
            start_values = []
            for a in soup.find_all("a", href=True):
                href = a.get("href")
                match = re.search(r"\?start=(\d+)", href)
                if match:
                    start_values.append(int(match.group(1)))
            
            return max(start_values) if start_values else 2250
        except Exception as e:
            logger.warning(f"Error scraping max start offset, defaulting to 2250: {e}")
            return 2250

    async def scrape_articles_from_list(self, list_url: str) -> List[str]:
        """Scrapes article detail URLs from a listing page (fallback)."""
        html = await self._fetch_html(list_url)
        soup = BeautifulSoup(html, "html.parser")
        
        urls = []
        for h2 in soup.find_all("h2", itemprop="headline"):
            a = h2.find("a", itemprop="url")
            if a:
                href = a.get("href")
                if href:
                    abs_url = href if href.startswith("http") else f"https://islamfatwa.net{href}"
                    urls.append(abs_url)
        return urls

    # --- Embed Formatting Helpers ---

    def create_fatwa_embed(self, fatwa: Dict[str, Any]) -> discord.Embed:
        """Formats a single fatwa detail dict into a highly polished Discord Embed."""
        color = self.bot.settings.get("embed_color", 0x0a58ca)
        embed = discord.Embed(
            title=fatwa["title"],
            url=fatwa["url"],
            color=color
        )

        # Apply branding headers and icons
        embed.set_author(
            name="Islam Fatwa",
            url="https://islamfatwa.net/",
            icon_url="https://islamfatwa.net/images/apple-touch-icon.png"
        )
        if self.bot.settings.get("show_thumbnails", True):
            embed.set_thumbnail(url="https://islamfatwa.net/images/apple-touch-icon.png")

        # Let's format the question blockquote safely, ensuring empty lines are blockquoted as well
        blockquote_frage = ""
        if fatwa["frage"] and fatwa["frage"] != "Siehe Beschreibung.":
            lines = []
            for line in fatwa["frage"].splitlines():
                stripped = line.strip()
                if stripped:
                    lines.append(f"> {stripped}")
                else:
                    lines.append("> \u200b")
            blockquote_frage = "\n".join(lines)

        desc_parts = []
        
        # Metadata block
        metadata_block = (
            "### 👤 Details zum Urteil\n"
            f"> 👤 **Gelehrter:** {fatwa['scholar']}\n"
            f"> 📁 **Kategorie:** {fatwa['category']}\n"
            f"> 📅 **Datum:** {fatwa['date']}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        desc_parts.append(metadata_block)

        if blockquote_frage:
            desc_parts.append(f"### 💬 Frage\n{blockquote_frage}")
            
        desc_parts.append(f"### ✍️ Antwort\n{fatwa['antwort']}")
        
        full_desc = "\n\n".join(desc_parts)
        
        # Max description limit is 4096. Let's ensure no overflow.
        max_desc_len = 3800
        if len(full_desc) > max_desc_len:
            meta_len = len(metadata_block)
            frage_len = len(blockquote_frage)
            truncated_len = max_desc_len - meta_len - frage_len - 250
            if truncated_len < 200:
                truncated_len = 200
            
            truncated_ans = fatwa["antwort"][:truncated_len].rstrip()
            
            desc_parts = [metadata_block]
            if blockquote_frage:
                desc_parts.append(f"### 💬 Frage\n{blockquote_frage}")
            
            desc_parts.append(
                f"### ✍️ Antwort (gekürzt)\n"
                f"{truncated_ans}...\n\n"
                f"📖 *[Vollständiges Urteil auf islamfatwa.net lesen]({fatwa['url']})*"
            )
            full_desc = "\n\n".join(desc_parts)

        embed.description = full_desc
        footer_text = self.bot.settings.get("footer_text", "Quelle: islamfatwa.net • Fatwa-Datenbank nach Quran & Sunnah • Lesezeichen 🔖")
        embed.set_footer(
            text=footer_text,
            icon_url="https://islamfatwa.net/images/favicon.png"
        )
        return embed

    # --- Discord Slash Commands ---

    # --- Advanced Filtered Search Executor ---

    async def execute_filtered_search(self, state: SearchState) -> List[Dict[str, Any]]:
        """
        Executes a search query filtered by category and scholar using local sitemap URLs.
        """
        if not self.sitemap_urls:
            await self.load_sitemap()

        def normalize(s: str) -> str:
            s = s.lower()
            s = s.replace("ü", "ue").replace("ä", "ae").replace("ö", "oe").replace("ß", "ss")
            s = re.sub(r'[^a-z0-9\s-]', '', s)
            return s

        keywords = []
        if state.query:
            norm_query = normalize(state.query)
            keywords = norm_query.split()

        # If no query and no filters, return empty results to prevent massive initial scrape load
        if not keywords and not state.category and not state.scholar:
            return []

        # Filter URLs in memory
        matching_urls = []
        for url in self.sitemap_urls:
            # Exclude category parent pages (only keep leaf articles)
            is_category = False
            for other_u in self.sitemap_urls:
                if other_u != url and other_u.startswith(url + "/"):
                    is_category = True
                    break
            if is_category:
                continue

            # Filter by Category
            if state.category and f"/{state.category}" not in url:
                continue

            # Filter by Keyword
            if keywords:
                norm_url = normalize(url)
                if not all(kw in norm_url for kw in keywords):
                    continue

            matching_urls.append(url)

        # Reverse matching URLs to prioritize the newest articles
        matching_urls.reverse()

        # Fetch detail pages concurrently for the top 15 candidates
        tasks_list = [self.scrape_article_detail(url) for url in matching_urls[:15]]
        parsed_results = await asyncio.gather(*tasks_list, return_exceptions=True)

        successful_results = []
        for item in parsed_results:
            if isinstance(item, Exception):
                logger.error(f"Error scraping search candidate: {item}")
            else:
                successful_results.append(item)

        # Filter by Scholar in memory
        if state.scholar:
            def normalize_scholar(text: str) -> str:
                text = text.lower()
                text = text.replace("ü", "ue").replace("ä", "ae").replace("ö", "oe")
                text = text.replace("ā", "a").replace("ī", "i").replace("ū", "u").replace("ḥ", "h").replace("ṣ", "s")
                text = re.sub(r"[^a-z0-9\s]", "", text)
                return text

            norm_scholar = normalize_scholar(state.scholar)
            filtered_by_scholar = []
            for res in successful_results:
                norm_res_scholar = normalize_scholar(res["scholar"])
                if norm_scholar in norm_res_scholar:
                    filtered_by_scholar.append(res)
            successful_results = filtered_by_scholar

        search_limit = self.bot.settings.get("search_limit", 3)
        return successful_results[:search_limit]

    # --- Discord Slash Commands ---

    @app_commands.command(name="suche", description="Sucht nach Fatawa auf islamfatwa.net")
    @app_commands.describe(
        suchbegriff="Der Begriff, nach dem gesucht werden soll (optional)",
        kategorie="Die Kategorie, nach der gefiltert werden soll (optional)",
        gelehrter="Der Gelehrte, nach dem gefiltert werden soll (optional)"
    )
    @app_commands.choices(kategorie=[
        app_commands.Choice(name="Aqidah (Fundamente)", value="aqidah-tauhid"),
        app_commands.Choice(name="Manhaj (Methodik)", value="manhaj"),
        app_commands.Choice(name="Ibadah (Gottesdienste)", value="gottesdienste-ibadah"),
        app_commands.Choice(name="Qur'an & Sunnah", value="qur-an-sunnah-offenbarungsschriften"),
        app_commands.Choice(name="Krankheit & Heilung", value="krankheit-heilung"),
        app_commands.Choice(name="Soziale Angelegenheiten", value="soziale-angelegenheiten"),
        app_commands.Choice(name="Kleidung & Körper", value="kleidung-schmuck")
    ])
    @app_commands.choices(gelehrter=[
        app_commands.Choice(name="Scheich Ibn Bāz", value="Ibn Baz"),
        app_commands.Choice(name="Scheich al-Uthaimīn", value="Uthaimin"),
        app_commands.Choice(name="Scheich al-Fauzān", value="Fauzan"),
        app_commands.Choice(name="Scheich al-Luḥaidān", value="Luhaidan"),
        app_commands.Choice(name="Scheich al-Albānī", value="Albani"),
        app_commands.Choice(name="Ständiges Komitee (Lajna)", value="Lajna")
    ])
    async def suche(
        self, 
        interaction: discord.Interaction, 
        suchbegriff: Optional[str] = None,
        kategorie: Optional[str] = None,
        gelehrter: Optional[str] = None
    ):
        # Defer response since loading index/scraping details takes a few moments
        await interaction.response.defer(ephemeral=False)

        # Force load sitemap if not loaded yet
        if not self.sitemap_urls:
            await self.load_sitemap()

        try:
            # Set up the search state
            state = SearchState(
                query=suchbegriff.strip() if suchbegriff else "",
                category=kategorie,
                scholar=gelehrter
            )
            
            # Instantiate the SearchDashboardView panel
            view = SearchDashboardView(self, state)
            
            # Execute search query and build initial layout
            view.current_results = await self.execute_filtered_search(state)
            search_embed = view.build_embed()
            view.search_embed = search_embed
            view.prepare_items()
            
            await interaction.followup.send(embed=search_embed, view=view)
            
        except Exception as e:
            logger.error(f"Error initializing search panel: {e}", exc_info=True)
            conn_error_embed = discord.Embed(
                color=0xe74c3c # Sleek crimson red
            )
            conn_error_embed.description = (
                "### 🔌 Panel-Ladefehler\n"
                "Das Such-Panel konnte nicht initialisiert werden. Bitte versuche es später noch einmal.\n\n"
                f"> ⚠️ **Details:** *{str(e)}*"
            )
            await interaction.followup.send(embed=conn_error_embed, ephemeral=True)

    @app_commands.command(name="fatwa_des_tages", description="Postet das aktuelle Fatwa des Tages von islamfatwa.net")
    async def fatwa_des_tages(self, interaction: discord.Interaction):
        """Allows users to manually trigger a daily/recent fatwa post in the current channel."""
        await interaction.response.defer(ephemeral=False)
        
        try:
            fatwa = await self._get_latest_fatwa()
            embed = self.create_fatwa_embed(fatwa)
            button_style = self.bot.settings.get("bookmark_button_style", "success")
            await interaction.followup.send(
                content="🕌 **Fatwa des Tages (Aktuell)**",
                embed=embed,
                view=BookmarkView(button_style)
            )
        except Exception as e:
            logger.error(f"Error fetching manual latest fatwa: {e}", exc_info=True)
            error_embed = discord.Embed(
                color=0xe74c3c
            )
            error_embed.description = (
                "### ❌ Fehler beim Laden\n"
                "Das aktuelle Fatwa des Tages konnte leider nicht abgerufen werden.\n\n"
                f"> ⚠️ **Details:** *{str(e)}*"
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

    @app_commands.command(name="zufaellige_fatwa", description="Postet ein zufälliges Fatwa von islamfatwa.net")
    async def zufaellige_fatwa(self, interaction: discord.Interaction):
        """Allows users to manually trigger a random fatwa post in the current channel."""
        await interaction.response.defer(ephemeral=False)
        
        try:
            fatwa = await self._get_random_fatwa()
            embed = self.create_fatwa_embed(fatwa)
            button_style = self.bot.settings.get("bookmark_button_style", "success")
            await interaction.followup.send(
                content="🕌 **Zufälliges Fatwa**",
                embed=embed,
                view=BookmarkView(button_style)
            )
        except Exception as e:
            logger.error(f"Error fetching manual random fatwa: {e}", exc_info=True)
            error_embed = discord.Embed(
                color=0xe74c3c
            )
            error_embed.description = (
                "### ❌ Fehler beim Laden\n"
                "Es konnte kein zufälliges Fatwa abgerufen werden.\n\n"
                f"> ⚠️ **Details:** *{str(e)}*"
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

    # --- Background Loop Logic ---

    async def _get_random_fatwa(self) -> Dict[str, Any]:
        """Fetches a random fatwa by choosing a random article from the cached sitemap."""
        article_urls = []
        if self.sitemap_urls:
            # Filter sitemap for actual article leaf nodes
            for u in self.sitemap_urls:
                last_segment = u.rstrip("/").split("/")[-1]
                if re.match(r'^\d+-', last_segment):
                    # Exclude parent categories/directories
                    is_category = False
                    for other_u in self.sitemap_urls:
                        if other_u != u and other_u.startswith(u + "/"):
                            is_category = True
                            break
                    if not is_category:
                        article_urls.append(u)

        if article_urls:
            random_url = random.choice(article_urls)
            logger.info(f"Selecting random sitemap URL: {random_url}")
            return await self.scrape_article_detail(random_url)

        # Fallback to paginated list scraping if sitemap cache is empty
        logger.warning("Sitemap URLs not available. Falling back to paginated scraping.")
        max_start = await self.scrape_max_start_offset()
        num_pages = max_start // 10
        random_page = random.randint(0, num_pages) * 10
        
        page_url = f"https://islamfatwa.net/?start={random_page}"
        urls = await self.scrape_articles_from_list(page_url)
        if not urls:
            urls = await self.scrape_articles_from_list("https://islamfatwa.net/")
            
        if not urls:
            raise Exception("Es konnten keine Urteils-Links auf der Website gefunden werden.")

        random_url = random.choice(urls)
        return await self.scrape_article_detail(random_url)

    async def _get_latest_fatwa(self) -> Dict[str, Any]:
        """Fetches the latest fatwa posted on the homepage."""
        urls = await self.scrape_articles_from_list("https://islamfatwa.net/")
        if not urls:
            raise Exception("Keine Beiträge auf der Startseite gefunden.")
        latest_url = urls[0]
        return await self.scrape_article_detail(latest_url)

    @tasks.loop(hours=24)
    async def daily_fatwa_loop(self):
        """Background task running every 24 hours to post a fatwa to a designated channel."""
        logger.info("Starting scheduled daily fatwa retrieval...")
        
        # Check settings first to see if daily fatwa is enabled
        if not self.bot.settings.get("daily_fatwa_enabled", True):
            logger.info("Daily fatwa is disabled in settings. Skipping loop execution.")
            return

        # Periodic refresh of the sitemap
        await self.load_sitemap()
        
        channel_id = self.bot.settings.get("daily_channel_id")
        if not channel_id:
            channel_id_str = os.getenv("DAILY_CHANNEL_ID")
            if not channel_id_str:
                logger.error("DAILY_CHANNEL_ID env variable is not set. Skipping daily task.")
                return
            try:
                channel_id = int(channel_id_str)
            except ValueError:
                logger.error(f"DAILY_CHANNEL_ID '{channel_id_str}' is not a valid integer. Skipping daily task.")
                return

        channel = self.bot.get_channel(channel_id)
        if not channel:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except Exception as e:
                logger.error(f"Could not fetch channel with ID {channel_id}: {e}")
                return

        if not channel:
            logger.error(f"Channel with ID {channel_id} not found.")
            return

        try:
            mode = self.bot.settings.get("daily_fatwa_mode", "latest")
            if mode == "random":
                fatwa = await self._get_random_fatwa()
            else:
                try:
                    fatwa = await self._get_latest_fatwa()
                except Exception as e:
                    logger.warning(f"Failed to fetch latest fatwa: {e}. Falling back to random fatwa.")
                    fatwa = await self._get_random_fatwa()

            embed = self.create_fatwa_embed(fatwa)
            button_style = self.bot.settings.get("bookmark_button_style", "success")
            
            await channel.send(
                content="🕌 **Fatwa des Tages**",
                embed=embed,
                view=BookmarkView(button_style)
            )
            logger.info(f"Successfully posted daily fatwa to channel {channel_id}")
            
        except Exception as e:
            logger.error(f"Error in daily fatwa loop execution: {e}", exc_info=True)

    @daily_fatwa_loop.before_loop
    async def before_daily_fatwa_loop(self):
        """Wait until the bot is logged in and populate sitemap cache before starting loop."""
        await self.bot.wait_until_ready()
        await self.load_sitemap()

async def setup(bot: commands.Bot):
    await bot.add_cog(ReferenceCog(bot))
