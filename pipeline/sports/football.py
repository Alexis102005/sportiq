from datetime import datetime


def unify(raw: dict) -> dict:
    """Normalise un match de football brut SofaScore"""
    event = raw["data"]["event"]
    incidents = raw["data"].get("incidents", [])
    meta = raw["data"].get("eventMeta", {})

    goals = []
    cards = []

    for inc in incidents:
        if inc.get("incidentType") == "goal":
            goals.append({
                "player": inc.get("player", {}).get("name"),
                "team": "home" if inc.get("isHome") else "away",
                "minute": inc.get("time"),
                "type": inc.get("incidentClass"),
            })
        elif inc.get("incidentType") == "card":
            cards.append({
                "player": inc.get("player", {}).get("name"),
                "team": "home" if inc.get("isHome") else "away",
                "minute": inc.get("time"),
                "type": inc.get("incidentClass"),
            })

    return {
        "sport": "football",
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


def compute_form(matches: list, team_name: str) -> dict:
    results = []
    goals_scored = []
    goals_conceded = []
    home_results = []
    away_results = []

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

        if scored > conceded:
            result = "W"
        elif scored == conceded:
            result = "D"
        else:
            result = "L"

        results.append(result)
        goals_scored.append(scored)
        goals_conceded.append(conceded)

        if is_home:
            home_results.append(result)
        else:
            away_results.append(result)

    if len(results) < 2:
        return {"available": False, "reason": "Pas assez de matchs"}

    return {
        "available": True,
        "matches_analyzed": len(results),
        "form_string": "".join(results),
        "points": sum(3 if r == "W" else 1 if r == "D" else 0 for r in results),
        "win_rate": round(results.count("W") / len(results), 2),
        "avg_scored": round(sum(goals_scored) / len(goals_scored), 2),
        "avg_conceded": round(sum(goals_conceded) / len(goals_conceded), 2),
        "btts_rate": round(sum(1 for s, c in zip(goals_scored, goals_conceded) if s > 0 and c > 0) / len(results), 2),
        "over25_rate": round(sum(1 for s, c in zip(goals_scored, goals_conceded) if s + c > 2) / len(results), 2),
        "home_form": "".join(home_results) if home_results else "N/A",
        "away_form": "".join(away_results) if away_results else "N/A",
    }


def compute_features(matches: list, team_home: str, team_away: str) -> dict:
    form_home = compute_form(matches, team_home)
    form_away = compute_form(matches, team_away)

    h2h_matches = [
        m for m in matches
        if m.get("data", {}).get("event", {}).get("homeTeam", {}).get("name") in [team_home, team_away]
        and m.get("data", {}).get("event", {}).get("awayTeam", {}).get("name") in [team_home, team_away]
    ]

    h2h = {"available": False, "reason": "Pas de H2H dans les données"}
    if h2h_matches:
        home_wins = away_wins = draws = 0
        for m in h2h_matches:
            e = m["data"]["event"]
            hs = e["homeScore"]["current"]
            as_ = e["awayScore"]["current"]
            ht = e["homeTeam"]["name"]
            if hs > as_:
                if ht == team_home: home_wins += 1
                else: away_wins += 1
            elif hs == as_:
                draws += 1
            else:
                if ht == team_away: away_wins += 1
                else: home_wins += 1

        h2h = {
            "available": True,
            "total": len(h2h_matches),
            f"{team_home}_wins": home_wins,
            f"{team_away}_wins": away_wins,
            "draws": draws,
        }

    return {
        "sport": "football",
        "team_home": team_home,
        "team_away": team_away,
        "form_home": form_home,
        "form_away": form_away,
        "h2h": h2h,
        "data_quality": {
            "has_form_home": form_home.get("available", False),
            "has_form_away": form_away.get("available", False),
            "has_h2h": h2h.get("available", False),
            "has_stats": False,
            "has_lineups": False,
        }
    }