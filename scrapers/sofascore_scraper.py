import os
import json
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

client = ApifyClient(os.getenv("APIFY_API_TOKEN"))

def scrape_matches(urls: list) -> list:
    """
    Scrape des matchs via azzouzana/sofascore-scraper-pro
    urls : liste de strings directes (pas de dicts)
    """
    run_input = {
        "startUrls": urls,
    }
    print(f"Scraping de {len(urls)} match(s)...")
    run = client.actor("azzouzana/sofascore-scraper-pro").call(run_input=run_input)

    results = []
    for item in client.dataset(run["defaultDatasetId"]).iterate_items(): # type: ignore
        results.append(item)
    return results


if __name__ == "__main__":
    urls = [
        "https://www.sofascore.com/football/match/atletico-madrid-real-madrid/EgbsLgb",
        "https://www.sofascore.com/football/match/real-madrid-rayo-vallecano/Egbsbhb",
        "https://www.sofascore.com/football/match/real-madrid-osasuna/rgbsEgb",
        "https://www.sofascore.com/football/match/atletico-madrid-real-madrid-b/EgbsIgb",
    ]

    matches = scrape_matches(urls)
    print(f"{len(matches)} matchs récupérés")

    os.makedirs("data/raw", exist_ok=True)
    with open("data/raw/recent_matches_raw.json", "w", encoding="utf-8") as f:
        json.dump(matches, f, indent=2, ensure_ascii=False)

    print("Sauvegardé dans data/raw/recent_matches_raw.json")
    for m in matches:
        if "event" in m.get("data", {}):
            e = m["data"]["event"]
            print(f"  {e['homeTeam']['name']} {e['homeScore']['current']} - {e['awayScore']['current']} {e['awayTeam']['name']}")