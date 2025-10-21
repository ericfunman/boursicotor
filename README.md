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
