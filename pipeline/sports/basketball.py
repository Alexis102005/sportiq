from datetime import datetime


def unify(raw: dict) -> dict:
    """Normalise un match de basketball brut SofaScore"""
    event = raw["data"]["event"]
    meta = raw["data"].get("eventMeta", {})

    return {
        "sport": "basketball",
        "match_id": event.get("id"),
        "url": raw.get("url"),
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
        "home_position": meta.get("homeTeamStandingsPosition"),
        "away_position": meta.get("awayTeamStandingsPosition"),
    }


def compute_form(matches: list, team_name: str) -> dict:
    results = []
    points_scored = []
    points_conceded = []

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

        is_home = (home == team_name)
        is_away = (away == team_name)

        if not is_home and not is_away:
            continue

        if is_home:
            scored, conceded = home_score, away_score
        else:
            scored, conceded = away_score, home_score

        results.append("W" if scored > conceded else "L")
        points_scored.append(scored)
        points_conceded.append(conceded)

    if len(results) < 2:
        return {"available": False, "reason": "Pas assez de matchs"}

    return {
        "available": True,
        "matches_analyzed": len(results),
        "form_string": "".join(results),
        "win_rate": round(results.count("W") / len(results), 2),
        "avg_scored": round(sum(points_scored) / len(points_scored), 2),
        "avg_conceded": round(sum(points_conceded) / len(points_conceded), 2),
        "over215_rate": round(sum(1 for s, c in zip(points_scored, points_conceded) if s + c > 215) / len(results), 2),
    }


def compute_features(matches: list, team_home: str, team_away: str) -> dict:
    form_home = compute_form(matches, team_home)
    form_away = compute_form(matches, team_away)

    return {
        "sport": "basketball",
        "team_home": team_home,
        "team_away": team_away,
        "form_home": form_home,
        "form_away": form_away,
        "data_quality": {
            "has_form_home": form_home.get("available", False),
            "has_form_away": form_away.get("available", False),
            "has_h2h": False,
            "has_stats": False,
        }
    }