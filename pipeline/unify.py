import json


def detect_sport(raw: dict) -> str:
    """Détecte le sport depuis les données brutes"""
    try:
        sport = raw["data"]["event"]["tournament"]["category"]["sport"]["slug"]
        return sport  # "football", "basketball", "tennis"
    except (KeyError, TypeError):
        return "football"  # défaut


def unify_match(raw: dict) -> dict:
    sport = detect_sport(raw)

    if sport == "football":
        from pipeline.sports.football import unify
    elif sport == "basketball":
        from pipeline.sports.basketball import unify
    elif sport == "tennis":
        from pipeline.sports.tennis import unify
    else:
        from pipeline.sports.football import unify

    return unify(raw)