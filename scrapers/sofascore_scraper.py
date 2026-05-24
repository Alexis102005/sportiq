import os
import json
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

client = ApifyClient(os.getenv("APIFY_API_TOKEN"))

def scrape_match(match_urls: list) -> list:
    run_input = {
        "startUrls": match_urls,  # liste de strings, pas de dicts
    }

    print(f"Scraping de {len(match_urls)} match(s)...")
    run = client.actor("azzouzana/sofascore-scraper-pro").call(run_input=run_input)

    results = []
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        results.append(item)
    return results


if __name__ == "__main__":
    urls = [
        "https://www.sofascore.com/football/match/atletico-madrid-real-madrid/EgbsLgb",
    ]

    matches = scrape_match(urls)
    print(f"{len(matches)} résultats récupérés")

    os.makedirs("data/raw", exist_ok=True)
    with open("data/raw/match_raw.json", "w", encoding="utf-8") as f:
        json.dump(matches, f, indent=2, ensure_ascii=False)

    print("Sauvegardé dans data/raw/match_raw.json")
    
    if matches:
        m = matches[0]["data"]["event"]
        print(f"\n{m['homeTeam']['name']} {m['homeScore']['current']} - {m['awayScore']['current']} {m['awayTeam']['name']}")
        print(f"Stade : {m['venue']['name']} ({m['attendance']} spectateurs)")
        print(f"Buts : {len([i for i in matches[0]['data']['incidents'] if i.get('incidentType') == 'goal'])}")