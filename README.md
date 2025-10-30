# 🚀 Boursicotor

Plateforme de trading algorithmique avec analyse technique, machine learning et backtesting pour le marché des actions françaises.

## 📋 Fonctionnalités

- ✅ Connexion à Saxo Bank ou Interactive Brokers (IBKR)
- 📊 Collecte de données historiques et temps réel (1s-10s intervals)
- 💾 Stockage optimisé dans PostgreSQL ou SQLite
- 📈 30+ indicateurs techniques (RSI, MACD, Bollinger Bands, etc.)
- 🤖 Machine Learning pour détection de patterns
- 🔙 Engine de backtesting complet avec métriques de confiance
- 📉 Visualisation interactive avec Streamlit
- 🛡️ Paper trading et gestion des risques (stop-loss)
- ⚡ Trading automatique intraday

## 🏗️ Architecture

```
boursicotor/
├── backend/          # API et logique métier
├── frontend/         # Interface Streamlit
├── database/         # Schémas et migrations
├── strategies/       # Stratégies de trading
├── ml_models/        # Modèles de Machine Learning
├── backtesting/      # Moteur de backtesting
├── brokers/          # Intégration Saxo Bank / IBKR
└── utils/            # Utilitaires communs
```

## 🚀 Installation

### Prérequis

- Python 3.10+
- PostgreSQL 14+ ou SQLite (pour développement rapide)
- Compte Saxo Bank ou Interactive Brokers
- TWS ou IB Gateway (pour IBKR)

### Configuration

1. Cloner le projet
```bash
cd Boursicotor
```

2. Créer un environnement virtuel
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

3. Installer les dépendances
```bash
pip install -r requirements.txt
```

4. Configurer PostgreSQL
```bash
# Créer la base de données
psql -U postgres
CREATE DATABASE boursicotor;
\q

# Exécuter les migrations
python database/init_db.py
```

5. Configurer les variables d'environnement
```bash
cp .env.example .env
# Éditer .env avec vos paramètres
```

## 🔑 APIs de Données

Boursicotor supporte plusieurs sources de données gratuites pour récupérer des données financières :

### Sources Disponibles (par ordre de priorité)

1. **🏦 Saxo Bank** (recommandé pour données temps réel)
   - Données intraday précises
   - Nécessite un compte Saxo Bank

2. **📈 Yahoo Finance** (gratuit, pas de clé API)
   - Données historiques fiables
   - Support des marchés européens (.PA pour Paris)
   - Limites : pas de données temps réel

3. **📊 Alpha Vantage** (gratuit avec clé API)
   - Clé API gratuite (5 appels/minute, 500/jour)
   - Données temps réel et historiques
   - [Obtenir une clé gratuite](https://www.alphavantage.co/support/#api-key)

4. **🔷 Polygon.io** (gratuit avec clé API)
   - Clé API gratuite (5 appels/minute, 2M/jour)
   - Données temps réel et historiques
   - Excellente documentation
   - [Obtenir une clé gratuite](https://polygon.io/)

### Configuration des APIs

Ajoutez vos clés API dans le fichier `.env` :

```bash
# APIs externes (optionnel)
ALPHA_VANTAGE_API_KEY=votre_clé_alpha_vantage
POLYGON_API_KEY=votre_clé_polygon
```

### Test des Sources

```bash
# Tester toutes les sources disponibles
python test_new_data_sources.py
```

## 🎯 Utilisation

### Lancer l'application

```bash
streamlit run frontend/app.py
```

### Collecter des données

```bash
python backend/data_collector.py --ticker TTE --interval 1min --days 30
```

### Lancer un backtest

```bash
python backtesting/run_backtest.py --strategy momentum --ticker TTE --start 2024-01-01 --end 2024-12-31
```

## 📊 Phase de développement

- [x] Phase 1: Structure du projet
- [ ] Phase 2: Connexion IBKR et collecte de données
- [ ] Phase 3: Base de données PostgreSQL
- [ ] Phase 4: Interface Streamlit
- [ ] Phase 5: Indicateurs techniques
- [ ] Phase 6: Backtesting
- [ ] Phase 7: Machine Learning
- [ ] Phase 8: Paper Trading
- [ ] Phase 9: Trading automatique

## ⚠️ Avertissement

Ce logiciel est fourni à des fins éducatives uniquement. Le trading comporte des risques financiers importants. Ne tradez jamais avec de l'argent que vous ne pouvez pas vous permettre de perdre.

## 📝 License

MIT License - voir LICENSE pour plus de détails

## 👨‍💻 Auteur

Développé avec ❤️ pour optimiser le trading algorithmique
