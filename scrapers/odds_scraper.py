import os
import httpx
from dotenv import load_dotenv

load_dotenv()

ODDS_API_KEY = os.getenv("ODDS_API_KEY")
BASE_URL = "https://api.the-odds-api.com/v4"

# Mapping sport → clé Odds API
SPORT_KEYS = {
    "football": "soccer_epl",        # Premier League par défaut
    "basketball": "basketball_nba",
    "tennis": "tennis_atp_french_open",
}

# Toutes les ligues foot qu'on veut couvrir
FOOTBALL_LEAGUES = [
    "soccer_epl",           # Premier League
    "soccer_spain_la_liga", # LaLiga
    "soccer_italy_serie_a", # Serie A
    "soccer_germany_bundesliga",  # Bundesliga
    "soccer_france_ligue_one",    # Ligue 1
    "soccer_uefa_champs_league",  # Champions League
]


def get_upcoming_matches(sport: str = "football", regions: str = "eu", markets: str = "h2h") -> list:
    """
    Récupère les matchs à venir avec leurs cotes.
    """
    results = []

    if sport == "football":
        leagues = FOOTBALL_LEAGUES
    elif sport == "basketball":
        leagues = ["basketball_nba"]
    elif sport == "tennis":
        leagues = ["tennis_atp_french_open", "tennis_wta_french_open"]
    else:
        leagues = [SPORT_KEYS.get(sport, "soccer_epl")]

    for league in leagues:
        try:
            url = f"{BASE_URL}/sports/{league}/odds"
            params = {
                "apiKey": ODDS_API_KEY,
                "regions": regions,
                "markets": markets,
                "oddsFormat": "decimal",
                "dateFormat": "iso",
            }
            response = httpx.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                matches = response.json()
                for m in matches:
                    results.append({
                        "sport": sport,
                        "league": league,
                        "match_id": m.get("id"),
                        "team_home": m.get("home_team"),
                        "team_away": m.get("away_team"),
                        "commence_time": m.get("commence_time"),
                        "bookmakers": extract_best_odds(m.get("bookmakers", [])),
                    })
            else:
                print(f"Erreur {response.status_code} pour {league}")
        except Exception as e:
            print(f"Erreur {league}: {e}")

    return results


def extract_best_odds(bookmakers: list) -> dict:
    """
    Extrait les meilleures cotes parmi tous les bookmakers.
    """
    if not bookmakers:
        return {}

    best = {"home": 0, "draw": 0, "away": 0}

    for bm in bookmakers:
        for market in bm.get("markets", []):
            if market.get("key") == "h2h":
                outcomes = market.get("outcomes", [])
                for o in outcomes:
                    name = o.get("name", "")
                    price = o.get("price", 0)
                    if name == best.get("home_team") or len(outcomes) >= 1:
                        # On prend juste la première cote disponible par position
                        pass

    # Approche simplifiée : prendre le premier bookmaker
    if bookmakers:
        bm = bookmakers[0]
        for market in bm.get("markets", []):
            if market.get("key") == "h2h":
                outcomes = market.get("outcomes", [])
                if len(outcomes) >= 2:
                    best["home_odds"] = outcomes[0].get("price")
                    best["home_team"] = outcomes[0].get("name")
                    best["away_odds"] = outcomes[1].get("price")
                    best["away_team"] = outcomes[1].get("name")
                if len(outcomes) == 3:
                    best["draw_odds"] = outcomes[2].get("price")

    return best


if __name__ == "__main__":
    import json
    print("Récupération des matchs du jour...")
    
    for sport in ["football", "basketball", "tennis"]:
        matches = get_upcoming_matches(sport)
        print(f"\n{sport.upper()}: {len(matches)} matchs trouvés")
        for m in matches[:3]:
            odds = m.get("bookmakers", {})
            print(f"  {m['team_home']} vs {m['team_away']}")
            print(f"  Cotes: {odds.get('home_odds')} / {odds.get('draw_odds')} / {odds.get('away_odds')}")