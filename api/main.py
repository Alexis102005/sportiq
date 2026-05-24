import os
import json
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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
def predict(home: str, away: str, urls: str = ""):
    """
    Prédit un match entre deux équipes.
    
    Params:
    - home : nom équipe domicile (ex: Real Madrid)
    - away : nom équipe extérieur (ex: Barcelona)
    - urls : URLs des matchs récents séparées par virgule (optionnel)
    """
    try:
        # Vérifier le cache d'abord
        cache_key = f"{home}-{away}".lower().replace(" ", "-")
        cache_path = f"data/predictions/{cache_key}.json"

        if os.path.exists(cache_path):
            with open(cache_path, encoding="utf-8") as f:
                return json.load(f)

        # Scraper les matchs si URLs fournies
        if not urls:
            raise HTTPException(
                status_code=400,
                detail="URLs des matchs récents requises. Passez ?urls=url1,url2,..."
            )

        match_urls = [u.strip() for u in urls.split(",")]
        raw_matches = scrape_matches(match_urls)

        if not raw_matches:
            raise HTTPException(
                status_code=404,
                detail="Aucun match trouvé avec ces URLs"
            )

        # Pipeline complet
        features = compute_features(raw_matches, home, away)
        prediction = predict_match(features)

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