import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """Tu es un expert en analyse sportive et prédiction de paris.
Tu analyses des données statistiques réelles pour prédire des matchs.

RÈGLES STRICTES :
1. Tu ne prédis QUE si tu as suffisamment de données
2. Tu n'inventes JAMAIS de statistiques
3. Si une donnée manque, tu le dis explicitement
4. Tu donnes un niveau de confiance en étoiles (1-5) basé sur la qualité des données
5. Tu réponds UNIQUEMENT en JSON valide, rien d'autre

Niveaux de confiance :
⭐ 1 étoile = < 50% (très risqué)
⭐⭐ 2 étoiles = 50-60% (risqué)
⭐⭐⭐ 3 étoiles = 60-70% (possible)
⭐⭐⭐⭐ 4 étoiles = 70-80% (probable)
⭐⭐⭐⭐⭐ 5 étoiles = > 80% (quasi certain)"""


def predict_match(features: dict) -> dict:
    """
    Génère les prédictions pour un match basé sur les features calculées.
    Met en cache le résultat pour ne pas recalculer.
    """
    team_home = features["team_home"]
    team_away = features["team_away"]
    quality = features["data_quality"]

    # Vérifier le cache
    cache_key = f"{team_home}-{team_away}".lower().replace(" ", "-")
    cache_path = f"data/predictions/{cache_key}.json"
    os.makedirs("data/predictions", exist_ok=True)

    if os.path.exists(cache_path):
        print(f"Cache trouvé pour {team_home} vs {team_away} — lecture du cache")
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)

    # Déterminer quels paris sont possibles
    paris_possibles = []
    paris_impossibles = []

    if quality["has_form_home"] and quality["has_form_away"]:
        paris_possibles.extend(["1N2", "double_chance", "handicap"])
    else:
        paris_impossibles.append({
            "paris": ["1N2", "double_chance", "handicap"],
            "raison": "Forme d'une ou deux équipes insuffisante"
        })

    if quality["has_form_home"] and quality["has_form_away"]:
        paris_possibles.extend(["over_under_25", "btts"])
    
    if quality["has_stats"]:
        paris_possibles.extend(["corners", "fautes", "tirs_totaux", "tirs_cadres"])
    else:
        paris_impossibles.append({
            "paris": ["corners", "fautes", "tirs_totaux", "tirs_cadres"],
            "raison": "Statistiques de jeu non disponibles"
        })

    # Construire le prompt
    prompt = f"""Analyse ce match et génère les prédictions.

DONNÉES DU MATCH :
{json.dumps(features, indent=2, ensure_ascii=False)}

PARIS À PRÉDIRE : {paris_possibles}

Réponds UNIQUEMENT avec ce JSON :
{{
  "match": "{team_home} vs {team_away}",
  "analyse": "2-3 phrases résumant les points clés",
  "predictions": {{
    "1N2": {{
      "result": "1 ou N ou 2",
      "stars": 1-5,
      "confidence_pct": 0-100,
      "reasoning": "explication courte"
    }},
    "over_under_25": {{
      "result": "over ou under",
      "stars": 1-5,
      "confidence_pct": 0-100,
      "reasoning": "explication courte"
    }},
    "btts": {{
      "result": "yes ou no",
      "stars": 1-5,
      "confidence_pct": 0-100,
      "reasoning": "explication courte"
    }},
    "double_chance": {{
      "result": "1X ou X2 ou 12",
      "stars": 1-5,
      "confidence_pct": 0-100,
      "reasoning": "explication courte"
    }},
    "handicap": {{
      "result": "-1.5 ou +1.5",
      "stars": 1-5,
      "confidence_pct": 0-100,
      "reasoning": "explication courte"
    }}
  }},
  "paris_impossibles": {json.dumps(paris_impossibles, ensure_ascii=False)},
  "data_quality": {json.dumps(quality, ensure_ascii=False)}
}}"""

    print(f"Génération des prédictions pour {team_home} vs {team_away}...")
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,  # Low temperature = réponses stables et cohérentes
    )

    raw = response.choices[0].message.content.strip()
    
    # Nettoyer si besoin
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    
    result = json.loads(raw)

    # Sauvegarder dans le cache
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"Prédiction sauvegardée dans {cache_path}")

    return result


if __name__ == "__main__":
    # Charger les features calculées
    with open("data/raw/recent_matches_raw.json", encoding="utf-8") as f:
        matches = json.load(f)

    from pipeline.features import compute_features
    features = compute_features(matches, "Real Madrid", "Atlético Madrid")

    prediction = predict_match(features)
    print(json.dumps(prediction, indent=2, ensure_ascii=False))