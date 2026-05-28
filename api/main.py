import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from scrapers.odds_scraper import get_upcoming_matches
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Sportiq API", version="1.0.0")

# Autoriser les appels depuis l'app mobile
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from scrapers.sofascore_scraper import scrape_matches
from pipeline.unify import unify_match
from pipeline.features import compute_features
from models.llm_predictor import predict_match


@app.get("/")
def root():
    return {"status": "ok", "message": "Sportiq API is running 🏆"}


@app.get("/predict")
def predict(home: str, away: str, sport: str = "football"):
    try:
        cache_key = f"{sport}-{home}-{away}".lower().replace(" ", "-")
        cache_path = f"data/predictions/{cache_key}.json"
        os.makedirs("data/predictions", exist_ok=True)

        if os.path.exists(cache_path):
            print(f"Cache trouvé")
            with open(cache_path, encoding="utf-8") as f:
                return json.load(f)

        # Chercher automatiquement les matchs récents des deux équipes
        print(f"Recherche des matchs récents pour {home} et {away}...")
        from scrapers.sofascore_scraper import find_recent_matches
        raw_matches = find_recent_matches(home, away, sport)

        if not raw_matches:
            raise HTTPException(
                status_code=404,
                detail=f"Impossible de trouver les matchs récents pour {home} et {away}"
            )

        features = compute_features(raw_matches, home, away)
        prediction = predict_match(features)

        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(prediction, f, ensure_ascii=False, indent=2)

        return prediction

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "cache_count": len(os.listdir("data/predictions")) if os.path.exists("data/predictions") else 0
    }

@app.get("/today/{sport}")
def today(sport: str):
    """
    Retourne les matchs du jour avec cotes pour un sport donné.
    sport: football | basketball | tennis
    """
    try:
        matches = get_upcoming_matches(sport)
        
        if not matches:
            return {"sport": sport, "matches": [], "message": "Aucun match trouvé"}

        return {
            "sport": sport,
            "total": len(matches),
            "matches": matches
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))