import asyncio
from unittest.mock import MagicMock
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cogs.reference_cog import ReferenceCog
from views.search_view import SearchState

def safe_print(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8"))

async def main():
    safe_print("=== Starte Sitemap Suchmaschinen-Tests ===")
    
    from utils.settings_manager import SettingsManager
    mock_bot = MagicMock()
    mock_bot.wait_until_ready = MagicMock(return_value=asyncio.sleep(0))
    mock_bot.settings = SettingsManager()
    
    # Cog instanziieren
    cog = ReferenceCog(mock_bot)
    
    # Test 1: sitemap.xml laden
    safe_print("\nTest 1: Lade sitemap.xml...")
    await cog.load_sitemap()
    safe_print(f"-> Erfolg! {len(cog.sitemap_urls)} URLs im Cache.")
    
    # Test 2: Nach "wudu" suchen
    safe_print("\nTest 2: Sitemap-URLs nach 'wudu' durchsuchen...")
    wudu_matches = cog.search_sitemap_urls("wudu")
    safe_print(f"-> {len(wudu_matches)} passende Artikel-URLs gefunden.")
    for i, url in enumerate(wudu_matches[:3]):
        safe_print(f"   [{i}] {url}")
        
    # Test 3: Nach "ghusl" suchen
    safe_print("\nTest 3: Sitemap-URLs nach 'ghusl' durchsuchen...")
    ghusl_matches = cog.search_sitemap_urls("ghusl")
    safe_print(f"-> {len(ghusl_matches)} passende Artikel-URLs gefunden.")
    for i, url in enumerate(ghusl_matches[:3]):
        safe_print(f"   [{i}] {url}")

    # Test 4: Details der Top 3 "wudu"-Treffer gleichzeitig abrufen
    if wudu_matches:
        safe_print("\nTest 4: Details der Top 3 'wudu'-Treffer gleichzeitig abrufen...")
        try:
            tasks_list = [cog.scrape_article_detail(url) for url in wudu_matches[:3]]
            parsed_results = await asyncio.gather(*tasks_list, return_exceptions=True)
            
            successful = []
            for item in parsed_results:
                if isinstance(item, Exception):
                    safe_print(f"   Scraping fehlgeschlagen: {item}")
                else:
                    successful.append(item)
            
            safe_print(f"-> Erfolg! {len(successful)} Artikel gleichzeitig geladen:")
            for i, res in enumerate(successful, start=1):
                safe_print(f"   {i}. Titel: {res['title']}")
                safe_print(f"      Gelehrter: {res['scholar']} | Kategorie: {res['category']} | Datum: {res['date']}")
                safe_print(f"      URL: {res['url']}")
        except Exception as e:
            safe_print(f"-> Fehler: {e}")
    else:
        safe_print("\nTest 4: Übersprungen (keine Treffer für 'wudu' gefunden).")

    # Test 5: execute_filtered_search testen
    safe_print("\nTest 5: Führe execute_filtered_search-Tests aus...")
    
    # Fall A: Suchwort "wudu" + Kategorie "gottesdienste-ibadah"
    safe_print("\n   [Fall A] Suchwort='wudu', Kategorie='gottesdienste-ibadah'...")
    try:
        state_a = SearchState(query="wudu", category="gottesdienste-ibadah")
        results_a = await cog.execute_filtered_search(state_a)
        safe_print(f"   -> {len(results_a)} Ergebnisse gefunden:")
        for idx, res in enumerate(results_a, start=1):
            safe_print(f"      {idx}. {res['title']} | Gelehrter: {res['scholar']} | Kategorie: {res['category']}")
    except Exception as e:
        safe_print(f"   -> Fehler: {e}")

    # Fall B: Suchwort "gebet" + Gelehrter "Ibn Baz"
    safe_print("\n   [Fall B] Suchwort='gebet', Gelehrter='Ibn Baz'...")
    try:
        state_b = SearchState(query="gebet", scholar="Ibn Baz")
        results_b = await cog.execute_filtered_search(state_b)
        safe_print(f"   -> {len(results_b)} Ergebnisse gefunden:")
        for idx, res in enumerate(results_b, start=1):
            safe_print(f"      {idx}. {res['title']} | Gelehrter: {res['scholar']} | Kategorie: {res['category']}")
    except Exception as e:
        safe_print(f"   -> Fehler: {e}")

    # Test 6: Abruf des neuesten und eines zufälligen Fatwas testen
    safe_print("\nTest 6: Teste Abruf des neuesten und eines zufälligen Fatwas...")
    
    # Fall A: Neuestes Fatwa
    safe_print("   [Fall A] Lade neuestes Fatwa...")
    try:
        latest = await cog._get_latest_fatwa()
        safe_print(f"   -> Erfolg! Titel: {latest['title']}")
        safe_print(f"      Gelehrter: {latest['scholar']} | Kategorie: {latest['category']} | Datum: {latest['date']}")
        safe_print(f"      URL: {latest['url']}")
    except Exception as e:
        safe_print(f"   -> Fehler beim neuesten Fatwa: {e}")
        
    # Fall B: Zufälliges Fatwa
    safe_print("\n   [Fall B] Lade zufälliges Fatwa...")
    try:
        random_fatwa = await cog._get_random_fatwa()
        safe_print(f"   -> Erfolg! Titel: {random_fatwa['title']}")
        safe_print(f"      Gelehrter: {random_fatwa['scholar']} | Kategorie: {random_fatwa['category']} | Datum: {random_fatwa['date']}")
        safe_print(f"      URL: {random_fatwa['url']}")
    except Exception as e:
        safe_print(f"   -> Fehler beim zufälligen Fatwa: {e}")

    # Hintergrundschleife beenden
    cog.daily_fatwa_loop.cancel()
    safe_print("\n=== Sitemap Suchmaschinen-Tests abgeschlossen ===")

if __name__ == "__main__":
    asyncio.run(main())
