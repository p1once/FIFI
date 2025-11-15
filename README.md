# FIFI – Assistant d'investissement assisté par IA

Cette application Windows fournit une interface unifiée pour agréger des données de marché, analyser la situation d'un actif (technique, fondamentale, sentiment), dialoguer avec l'API d'OpenAI et proposer des signaux d'investissement avec gestion du risque.

## Fonctionnalités principales

- **Tableau de bord** : visualisation synthétique des scores et recommandations.
- **Analyse multi-facteurs** : calcul d'indicateurs techniques, évaluation fondamentale simplifiée et agrégation du sentiment des actualités.
- **Pondération personnalisable** : ajustez le poids de chaque pilier (technique, fondamental, sentiment).
- **Intégration OpenAI** : prompts structurés pour enrichir l'analyse avec des explications qualitatives.
- **Gestion des risques** : dimensionnement des positions et alertes sur les pertes potentielles.
- **Configuration sécurisée** : stockage chiffré optionnel des clés API, tests de connexion et gestion des notifications.

## Structure du projet

```
src/
  fifi_app/
    __init__.py
    ai.py
    app.py
    config.py
    fundamental.py
    logging_utils.py
    main.py
    market_data.py
    risk.py
    scoring.py
    sentiment.py
    technical.py
```

## Prérequis

- Python 3.10+
- Clé API OpenAI et fournisseurs de données (Alpha Vantage, Finnhub, etc.) selon les connecteurs utilisés.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # ou .venv\\Scripts\\activate sur Windows
pip install -e .
```

Sous Windows, vous pouvez automatiser cette étape avec `setup_env.bat` :

```bat
setup_env.bat
```

## Utilisation

```bash
fifi-app
```

Sur Windows, un script `run_fifi.bat` est fourni pour activer l'environnement virtuel
et lancer l'application en une seule commande :

```bat
run_fifi.bat
```

La première exécution crée un dossier de configuration dans `~/.config/fifi-app` (ou `%APPDATA%\\fifi-app%` sous Windows). Configurez vos clés API dans l'onglet **Paramètres** puis commencez vos analyses.

## Tests unitaires

_Aucun test automatisé n'est fourni pour le moment. Ajoutez vos propres scénarios de tests en fonction des connecteurs implémentés._

## Licence

Projet fourni à titre d'exemple éducatif. Vérifiez les exigences réglementaires et contractuelles avant tout usage en conditions réelles.
