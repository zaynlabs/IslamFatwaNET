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
    safe_print("=== Starting Sitemap Search Engine Tests ===")
    
    from utils.settings_manager import SettingsManager
    mock_bot = MagicMock()
    mock_bot.wait_until_ready = MagicMock(return_value=asyncio.sleep(0))
    mock_bot.settings = SettingsManager()
    
    # Instantiate cog
    cog = ReferenceCog(mock_bot)
    
    # Test 1: Load sitemap.xml
    safe_print("\nTest 1: Loading sitemap.xml...")
    await cog.load_sitemap()
    safe_print(f"-> Success! Cached {len(cog.sitemap_urls)} URLs.")
    
    # Test 2: Search for "wudu"
    safe_print("\nTest 2: Searching sitemap URLs for 'wudu'...")
    wudu_matches = cog.search_sitemap_urls("wudu")
    safe_print(f"-> Found {len(wudu_matches)} matching article URLs.")
    for i, url in enumerate(wudu_matches[:3]):
        safe_print(f"   [{i}] {url}")
        
    # Test 3: Search for "ghusl"
    safe_print("\nTest 3: Searching sitemap URLs for 'ghusl'...")
    ghusl_matches = cog.search_sitemap_urls("ghusl")
    safe_print(f"-> Found {len(ghusl_matches)} matching article URLs.")
    for i, url in enumerate(ghusl_matches[:3]):
        safe_print(f"   [{i}] {url}")

    # Test 4: Concurrently fetch metadata for top 3 "wudu" results
    if wudu_matches:
        safe_print("\nTest 4: Fetching detail metadata concurrently for top 3 'wudu' matches...")
        try:
            tasks_list = [cog.scrape_article_detail(url) for url in wudu_matches[:3]]
            parsed_results = await asyncio.gather(*tasks_list, return_exceptions=True)
            
            successful = []
            for item in parsed_results:
                if isinstance(item, Exception):
                    safe_print(f"   Scraping failed: {item}")
                else:
                    successful.append(item)
            
            safe_print(f"-> Success! Concurrently scraped {len(successful)} articles:")
            for i, res in enumerate(successful, start=1):
                safe_print(f"   {i}. Title: {res['title']}")
                safe_print(f"      Scholar: {res['scholar']} | Category: {res['category']} | Date: {res['date']}")
                safe_print(f"      URL: {res['url']}")
        except Exception as e:
            safe_print(f"-> Failed: {e}")
    else:
        safe_print("\nTest 4: Skipped (no matches found for 'wudu').")

    # Test 5: execute_filtered_search tests
    safe_print("\nTest 5: Running execute_filtered_search tests...")
    
    # Case A: Keyword "wudu" + Category "gottesdienste-ibadah"
    safe_print("\n   [Case A] Keyword='wudu', Category='gottesdienste-ibadah'...")
    try:
        state_a = SearchState(query="wudu", category="gottesdienste-ibadah")
        results_a = await cog.execute_filtered_search(state_a)
        safe_print(f"   -> Found {len(results_a)} results:")
        for idx, res in enumerate(results_a, start=1):
            safe_print(f"      {idx}. {res['title']} | Scholar: {res['scholar']} | Cat: {res['category']}")
    except Exception as e:
        safe_print(f"   -> Failed: {e}")

    # Case B: Keyword "gebet" + Scholar "Ibn Baz"
    safe_print("\n   [Case B] Keyword='gebet', Scholar='Ibn Baz'...")
    try:
        state_b = SearchState(query="gebet", scholar="Ibn Baz")
        results_b = await cog.execute_filtered_search(state_b)
        safe_print(f"   -> Found {len(results_b)} results:")
        for idx, res in enumerate(results_b, start=1):
            safe_print(f"      {idx}. {res['title']} | Scholar: {res['scholar']} | Cat: {res['category']}")
    except Exception as e:
        safe_print(f"   -> Failed: {e}")

    # Test 6: Recent and Random Fatwa functions
    safe_print("\nTest 6: Testing recent and random fatwa retrieval...")
    
    # Case A: Latest Fatwa
    safe_print("   [Case A] Fetching latest fatwa...")
    try:
        latest = await cog._get_latest_fatwa()
        safe_print(f"   -> Success! Title: {latest['title']}")
        safe_print(f"      Scholar: {latest['scholar']} | Category: {latest['category']} | Date: {latest['date']}")
        safe_print(f"      URL: {latest['url']}")
    except Exception as e:
        safe_print(f"   -> Failed latest fatwa: {e}")
        
    # Case B: Random Fatwa
    safe_print("\n   [Case B] Fetching random fatwa...")
    try:
        random_fatwa = await cog._get_random_fatwa()
        safe_print(f"   -> Success! Title: {random_fatwa['title']}")
        safe_print(f"      Scholar: {random_fatwa['scholar']} | Category: {random_fatwa['category']} | Date: {random_fatwa['date']}")
        safe_print(f"      URL: {random_fatwa['url']}")
    except Exception as e:
        safe_print(f"   -> Failed random fatwa: {e}")

    # Cancel loop
    cog.daily_fatwa_loop.cancel()
    safe_print("\n=== Sitemap Search Engine Tests Completed ===")

if __name__ == "__main__":
    asyncio.run(main())
