import json
from datetime import datetime


def unify_match(raw: dict) -> dict:
    """
    Transforme un match brut SofaScore en objet normalisé
    prêt pour le pipeline de prédiction.
    """
    event = raw["data"]["event"]
    incidents = raw["data"].get("incidents", [])
    meta = raw["data"].get("eventMeta", {})

    # Extraire les buts
    goals = []
    for inc in incidents:
        if inc.get("incidentType") == "goal":
            goals.append({
                "player": inc.get("player", {}).get("name"),
                "team": "home" if inc.get("isHome") else "away",
                "minute": inc.get("time"),
                "type": inc.get("incidentClass"),  # regular, penalty, own-goal
            })

    # Extraire les cartons
    cards = []
    for inc in incidents:
        if inc.get("incidentType") == "card":
            cards.append({
                "player": inc.get("player", {}).get("name"),
                "team": "home" if inc.get("isHome") else "away",
                "minute": inc.get("time"),
                "type": inc.get("incidentClass"),  # yellow, red
            })

    return {
        "match_id": event.get("id"),
        "url": raw.get("url"),
        "sport": event["tournament"]["category"]["sport"]["name"],
        "tournament": event["tournament"]["name"],
        "date": datetime.fromtimestamp(event["startTimestamp"]).strftime("%Y-%m-%d"),
        "status": event["status"]["type"],

        "team_home": event["homeTeam"]["name"],
        "team_away": event["awayTeam"]["name"],

        "score_home": event["homeScore"]["current"],
        "score_away": event["awayScore"]["current"],
        "score_ht_home": event["homeScore"].get("period1"),
        "score_ht_away": event["awayScore"].get("period1"),

        "winner": "home" if event.get("winnerCode") == 1 else "away" if event.get("winnerCode") == 2 else "draw",

        "venue": event.get("venue", {}).get("name"),
        "attendance": event.get("attendance"),
        "referee": event.get("referee", {}).get("name"),

        "home_position": meta.get("homeTeamStandingsPosition"),
        "away_position": meta.get("awayTeamStandingsPosition"),

        "goals": goals,
        "cards": cards,

        "home_red_cards": sum(1 for c in cards if c["team"] == "home" and c["type"] == "red"),
        "away_red_cards": sum(1 for c in cards if c["team"] == "away" and c["type"] == "red"),
    }


if __name__ == "__main__":
    with open("data/raw/match_raw.json", encoding="utf-8") as f:
        raw_matches = json.load(f)

    # On filtre uniquement les matchs (pas les profils joueurs)
    match_items = [m for m in raw_matches if "event" in m.get("data", {})]

    normalized = [unify_match(m) for m in match_items]

    import os
    os.makedirs("data/processed", exist_ok=True)
    with open("data/processed/match_normalized.json", "w", encoding="utf-8") as f:
        json.dump(normalized, f, indent=2, ensure_ascii=False)
        
    print(f"{len(normalized)} match(s) normalisés")
    for m in normalized:
        print(f"\n{m['team_home']} {m['score_home']} - {m['score_away']} {m['team_away']}")
        print(f"  Date     : {m['date']}")
        print(f"  Stade    : {m['venue']} ({m['attendance']} spectateurs)")
        print(f"  Arbitre  : {m['referee']}")
        print(f"  Positions: {m['team_home']} #{m['home_position']} vs {m['team_away']} #{m['away_position']}")
        print(f"  Buts     : {len(m['goals'])}")
        print(f"  Cartons  : {len(m['cards'])}")