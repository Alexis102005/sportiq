import os
import json
from curl_cffi import requests as cf_requests
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

# Validate Apify token early and provide clearer diagnostics
APIFY_TOKEN = os.getenv("APIFY_API_TOKEN")
if not APIFY_TOKEN:
    raise RuntimeError(
        "APIFY_API_TOKEN is not set. Please add it to your environment or .env file."
    )


def _mask_token(t: str) -> str:
    if not t or len(t) < 8:
        return "***REDACTED***"
    return f"{t[:4]}...{t[-4:]}"

print(f"Using Apify token: {_mask_token(APIFY_TOKEN)}")
client = ApifyClient(APIFY_TOKEN)

# Headers qui imitent un vrai navigateur
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.sofascore.com/",
    "Origin": "https://www.sofascore.com",
    "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "Connection": "keep-alive",
}


def search_team(team_name: str, sport: str = "football") -> dict:
    """Cherche une équipe ou joueur par nom"""

    # Pour le tennis, chercher dans les joueurs
    if sport == "tennis":
        url = f"https://www.sofascore.com/api/v1/search/players?q={team_name}&page=0"
        response = cf_requests.get(
            url,
            impersonate="chrome120",
            timeout=10
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            if results:
                entity = results[0].get("entity", {})
                return {
                    "id": entity.get("id"),
                    "name": entity.get("name"),
                    "slug": entity.get("slug"),
                }
        return None

    # Pour football et basketball
    url = f"https://www.sofascore.com/api/v1/search/teams?q={team_name}&page=0"
    response = cf_requests.get(url, impersonate="chrome120", timeout=10)

    if response.status_code != 200:
        print(f"Erreur {response.status_code} pour {team_name}")
        return None

    data = response.json()
    results = data.get("results", [])

    sport_map = {"football": 1, "basketball": 2, "tennis": 5}
    sport_id = sport_map.get(sport, 1)

    for result in results:
        entity = result.get("entity", {})
        if entity.get("sport", {}).get("id") == sport_id:
            return {
                "id": entity.get("id"),
                "name": entity.get("name"),
                "slug": entity.get("slug"),
            }
    return None


def get_team_recent_matches(team_id: int, pages: int = 2, sport: str = "football") -> list:
    """Récupère les derniers matchs d'une équipe ou joueur"""
    matches = []

    # Tennis : endpoint joueur différent (same base here but kept for clarity)
    if sport == "tennis":
        base_url = f"https://www.sofascore.com/api/v1/team/{team_id}/events/last"
    else:
        base_url = f"https://www.sofascore.com/api/v1/team/{team_id}/events/last"

    for page in range(pages):
        url = f"{base_url}/{page}"
        response = cf_requests.get(url, impersonate="chrome120", timeout=10)
        if response.status_code != 200:
            print(f"Erreur {response.status_code} pour team_id {team_id} page {page}")
            break
        data = response.json()
        events = data.get("events", [])
        if not events:
            break
        matches.extend(events)
        print(f"  Page {page}: {len(events)} matchs")

    return matches


def find_recent_matches(team_home: str, team_away: str, sport: str = "football") -> list:
    """
    Trouve automatiquement les matchs récents des deux équipes
    """
    print(f"Recherche de {team_home}...")
    home_team = search_team(team_home, sport)

    print(f"Recherche de {team_away}...")
    away_team = search_team(team_away, sport)

    if not home_team and not away_team:
        print("Aucune équipe trouvée")
        return []

    all_events = []

    if home_team:
        print(f"Trouvé: {home_team['name']} (ID: {home_team['id']})")
        events = get_team_recent_matches(home_team["id"], sport=sport)
        # Convertir au format attendu par le pipeline
        for e in events:
            all_events.append({"data": {"event": e}, "url": ""})

    if away_team:
        print(f"Trouvé: {away_team['name']} (ID: {away_team['id']})")
        events = get_team_recent_matches(away_team["id"], sport=sport)
        for e in events:
            all_events.append({"data": {"event": e}, "url": ""})

    return all_events


def scrape_matches(urls: list) -> list:
    """Scrape des matchs via azzouzana/sofascore-scraper-pro
    urls : liste de strings directes (pas de dicts)
    """
    run_input = {"startUrls": urls}
    print(f"Scraping de {len(urls)} match(s)...")
    try:
        run = client.actor("azzouzana/sofascore-scraper-pro").call(run_input=run_input)
    except Exception as e:
        print("Apify actor call failed:", repr(e))
        # Try to surface HTTP / response details if available
        if hasattr(e, "status_code"):
            print("Status code:", getattr(e, "status_code"))
        if hasattr(e, "response") and getattr(e, "response") is not None:
            try:
                resp = getattr(e, "response")
                # Some exception objects expose .text or .content
                if hasattr(resp, "text"):
                    print("Response text:", resp.text)
                elif hasattr(resp, "content"):
                    print("Response content:", resp.content)
            except Exception:
                pass
        raise

    results = []
    for item in client.dataset(run["defaultDatasetId"]).iterate_items(): # type: ignore
        results.append(item)
    return results


if __name__ == "__main__":
    print("Test recherche Arsenal...")
    team = search_team("Arsenal", "football")
    print(f"Résultat: {team}")

    if team:
        print(f"\nMatchs récents de {team['name']}...")
        matches = get_team_recent_matches(team["id"], pages=1)
        print(f"{len(matches)} matchs trouvés")
        if matches:
            m = matches[0]
            print(f"Dernier match: {m.get('homeTeam', {}).get('name')} vs {m.get('awayTeam', {}).get('name')}")