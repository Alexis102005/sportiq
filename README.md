# Sportiq 🏆

Application de prédiction sportive IA qui analyse les statistiques **et** le contexte (forme récente, blessures, météo, back-to-back, H2H).

## Sports couverts
- ⚽ Football
- 🏀 Basketball
- 🎾 Tennis

## Architecture

```
Apify (scraping) → Pipeline de normalisation → Moteur IA → App mobile
```

## Stack
- **Scraping** : Apify
- **Backend / Pipeline** : Python
- **Modèle ML** : XGBoost
- **Analyse contextuelle** : LLM (Claude API)
- **App mobile** : React Native

## Installation

```bash
git clone https://github.com/TON_USERNAME/sportiq.git
cd sportiq
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # puis remplis tes clés API
```

## Structure du projet

```
sportiq/
├── data/
│   ├── raw/          # données brutes Apify (gitignored)
│   └── processed/    # données normalisées (gitignored)
├── scrapers/
│   └── apify_client.py
├── pipeline/
│   ├── unify.py
│   ├── clean.py
│   └── features.py
├── models/
│   ├── ml_model.py
│   └── llm_context.py
└── app/              # React Native (à venir)
```

## Variables d'environnement

Copie `.env.example` en `.env` et remplis :

```
APIFY_API_TOKEN=ton_token_ici
```

## Progression

- [x] Structure du projet
- [ ] Scraping Apify (matchs football)
- [ ] Pipeline de normalisation
- [ ] Modèle ML
- [ ] Analyse contextuelle LLM
- [ ] App mobile React Native
