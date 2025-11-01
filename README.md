# 🚀 Boursicotor

Plateforme de trading algorithmique avec analyse technique, machine learning et backtesting pour le marché des actions françaises.

## 📋 Fonctionnalités

- ✅ Connexion à Interactive Brokers (IBKR) / Lynx
- 📊 Collecte de données historiques et temps réel (5s-1 mois intervals)
- 🔄 **Collecte asynchrone avec Celery + Redis** (nouveau !)
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
pip install -r requirements_celery.txt  # Pour collecte asynchrone
```

4. Installer et configurer Redis (pour Celery)
```bash
# Option 1: Chocolatey (Windows)
choco install redis-64

# Option 2: WSL
wsl
sudo apt-get install redis-server

# Option 3: Docker
docker run -d -p 6379:6379 redis:latest
```

5. Configurer PostgreSQL
```bash
# Créer la base de données
psql -U postgres
CREATE DATABASE boursicotor;
\q

# Exécuter les migrations
python database/init_db.py
```

6. Configurer les variables d'environnement
```bash
cp .env.example .env
# Éditer .env avec vos paramètres
```

## 🔑 Sources de Données

Boursicotor utilise deux sources de données fiables :

### Sources Disponibles

1. **🏦 Interactive Brokers (IBKR) / Lynx** (recommandé)
   - Données temps réel et historiques précises
   - Intervalles de 5 secondes à 1 mois
   - Chunking automatique pour grandes périodes
   - Nécessite un compte IBKR/Lynx et TWS/IB Gateway

2. **📈 Yahoo Finance** (gratuit, backup)
   - Données historiques fiables
   - Support des marchés européens (.PA pour Paris)
   - Pas de clé API requise
   - Limites : données moins précises pour l'intraday

### Configuration IBKR

1. Installez TWS ou IB Gateway
2. Configurez l'API dans TWS :
   - File → Global Configuration → API → Settings
   - Enable ActiveX and Socket Clients
   - Socket port: 7497 (paper trading) ou 7496 (live)
   - Trusted IPs: 127.0.0.1

Pour plus de détails, consultez `CELERY_SETUP.md`

## 🎯 Utilisation

### Démarrage rapide avec Celery (Recommandé)

Le système de collecte de données fonctionne maintenant en arrière-plan grâce à Celery + Redis !

#### 🚀 Lancer l'application (Windows) - SIMPLE

**Double-cliquez sur `startBoursicotor.bat`** - Le script lance automatiquement :
- ✅ Redis (broker de messages)
- ✅ Celery Worker (exécuteur de jobs)
- ✅ Streamlit (interface web)

**Pour arrêter proprement tous les services :**
Double-cliquez sur `stopBoursicotor.bat`

#### Lancement manuel (si vous préférez le contrôle total)
```bash
# Terminal 1 : Redis
redis-server

# Terminal 2 : Celery Worker
celery -A backend.tasks worker --loglevel=info --pool=solo

# Terminal 3 : Streamlit
streamlit run frontend/app.py
```

**⚠️ IMPORTANT** : Les 3 services doivent rester ouverts pour que la collecte asynchrone fonctionne !

#### Lancer Flower (monitoring web optionnel)
```bash
celery -A backend.tasks flower
# Ouvrir http://localhost:5555
```

### Utilisation classique (sans Celery)

```bash
streamlit run frontend/app.py
```

### Collecter des données

**Via l'interface Streamlit (recommandé) :**
1. Connectez-vous à IBKR depuis la sidebar
2. Allez sur "💾 Collecte de Données"
3. Sélectionnez un ticker, période et intervalle
4. Cliquez sur "📊 Collecter les données"
5. Suivez la progression sur "📋 Historique des collectes"

**Via ligne de commande :**
```bash
python backend/data_collector.py --ticker TTE --interval 1min --days 30
```

### Lancer un backtest

```bash
python backtesting/run_backtest.py --strategy momentum --ticker TTE --start 2024-01-01 --end 2024-12-31
```

## 📚 Documentation

- 📖 [CELERY_SETUP.md](CELERY_SETUP.md) - Installation et configuration de Celery + Redis
- 📖 [CELERY_USAGE.md](CELERY_USAGE.md) - Guide d'utilisation de la collecte asynchrone
- 📖 [docs/](docs/) - Documentation technique complète

## 📊 Phase de développement

- [x] Phase 1: Structure du projet
- [x] Phase 2: Connexion IBKR et collecte de données
- [x] Phase 2.5: Infrastructure Celery + Redis pour collecte asynchrone
- [x] Phase 3: Base de données PostgreSQL
- [x] Phase 4: Interface Streamlit
- [x] Phase 5: Indicateurs techniques
- [ ] Phase 6: Backtesting
- [ ] Phase 7: Machine Learning
- [ ] Phase 8: Paper Trading
- [ ] Phase 9: Trading automatique

## 🆕 Nouveautés (Version actuelle)

### Collecte asynchrone avec Celery + Redis

- ✅ **Collectes en arrière-plan** : Ne bloque plus l'interface
- ✅ **Résistant aux interruptions** : Continue même si vous fermez le navigateur
- ✅ **Suivi en temps réel** : Progression visible avec barre de progression
- ✅ **Historique complet** : Tous les jobs enregistrés en base de données
- ✅ **Annulation possible** : Possibilité d'annuler un job en cours
- ✅ **Monitoring web** : Interface Flower pour supervision avancée
- ✅ **Nettoyage automatique** : Jobs anciens supprimés après 7 jours

## ⚠️ Avertissement

Ce logiciel est fourni à des fins éducatives uniquement. Le trading comporte des risques financiers importants. Ne tradez jamais avec de l'argent que vous ne pouvez pas vous permettre de perdre.

## 📝 License

MIT License - voir LICENSE pour plus de détails

## 👨‍💻 Auteur

Développé avec ❤️ pour optimiser le trading algorithmique
