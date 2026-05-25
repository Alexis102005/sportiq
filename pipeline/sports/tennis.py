from datetime import datetime


def unify(raw: dict) -> dict:
    """Normalise un match de tennis brut SofaScore"""
    event = raw["data"]["event"]

    return {
        "sport": "tennis",
        "match_id": event.get("id"),
        "url": raw.get("url"),
        "tournament": event["tournament"]["name"],
        "date": datetime.fromtimestamp(event["startTimestamp"]).strftime("%Y-%m-%d"),
        "status": event["status"]["type"],
        "player_home": event["homeTeam"]["name"],
        "player_away": event["awayTeam"]["name"],
        "score_home": event["homeScore"]["current"],
        "score_away": event["awayScore"]["current"],
        "sets_home": event["homeScore"].get("period1"),
        "sets_away": event["awayScore"].get("period1"),
        "winner": "home" if event.get("winnerCode") == 1 else "away",
        "surface": event.get("groundType", "unknown"),
    }


def compute_form(matches: list, player_name: str) -> dict:
    results = []
    sets_won = []
    sets_lost = []

    for m in matches:
        event = m.get("data", {}).get("event", {})
        if not event:
            continue

        home = event.get("homeTeam", {}).get("name", "")
        away = event.get("awayTeam", {}).get("name", "")
        home_score = event.get("homeScore", {}).get("current")
        away_score = event.get("awayScore", {}).get("current")

        if home_score is None or away_score is None:
            continue

        is_home = (home == player_name)
        is_away = (away == player_name)

        if not is_home and not is_away:
            continue

        if is_home:
            won, lost = home_score, away_score
        else:
            won, lost = away_score, home_score

        results.append("W" if won > lost else "L")
        sets_won.append(won)
        sets_lost.append(lost)

    if len(results) < 2:
        return {"available": False, "reason": "Pas assez de matchs"}

    return {
        "available": True,
        "matches_analyzed": len(results),
        "form_string": "".join(results),
        "win_rate": round(results.count("W") / len(results), 2),
        "avg_sets_won": round(sum(sets_won) / len(sets_won), 2),
        "avg_sets_lost": round(sum(sets_lost) / len(sets_lost), 2),
    }


def compute_features(matches: list, player_home: str, player_away: str) -> dict:
    form_home = compute_form(matches, player_home)
    form_away = compute_form(matches, player_away)

    return {
        "sport": "tennis",
        "player_home": player_home,
        "player_away": player_away,
        "form_home": form_home,
        "form_away": form_away,
        "data_quality": {
            "has_form_home": form_home.get("available", False),
            "has_form_away": form_away.get("available", False),
            "has_h2h": False,
            "has_stats": False,
        }
    }