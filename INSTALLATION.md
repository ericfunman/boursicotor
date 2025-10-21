# 📋 Guide d'Installation - Boursicotor

Ce guide vous aidera à installer et configurer Boursicotor sur votre machine Windows.

## ✅ Prérequis

### 1. Python 3.10 ou supérieur
Téléchargez et installez Python depuis [python.org](https://www.python.org/downloads/)

Vérifiez l'installation :
```bash
python --version
```

### 2. PostgreSQL 14 ou supérieur
Téléchargez et installez PostgreSQL depuis [postgresql.org](https://www.postgresql.org/download/windows/)

### 3. Compte Interactive Brokers
- Créez un compte sur [Interactive Brokers](https://www.interactivebrokers.com/)
- Téléchargez TWS (Trader Workstation) ou IB Gateway
- Activez l'API dans TWS : File → Global Configuration → API → Settings
  - Cochez "Enable ActiveX and Socket Clients"
  - Notez le port (7497 pour paper trading, 7496 pour live)

## 🚀 Installation

### Étape 1 : Configuration de l'environnement Python

1. Ouvrez un terminal dans le dossier Boursicotor
2. Créez un environnement virtuel :
```bash
python -m venv venv
```

3. Activez l'environnement virtuel :
```bash
.\venv\Scripts\activate
```

4. Mettez à jour pip :
```bash
python -m pip install --upgrade pip
```

### Étape 2 : Installation des dépendances

**IMPORTANT** : TA-Lib nécessite une installation spéciale sur Windows

#### Installation de TA-Lib sur Windows :

1. Téléchargez le fichier wheel approprié depuis :
   https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib

   Exemple pour Python 3.10 64-bit :
   `TA_Lib‑0.4.28‑cp310‑cp310‑win_amd64.whl`

2. Installez le fichier wheel :
```bash
pip install chemin\vers\TA_Lib‑0.4.28‑cp310‑cp310‑win_amd64.whl
```

3. Installez les autres dépendances :
```bash
pip install -r requirements.txt
```

**Si vous rencontrez des problèmes avec TA-Lib**, vous pouvez continuer sans :
- Les indicateurs de base fonctionneront avec pandas_ta
- Commentez `ta-lib==0.4.28` dans requirements.txt

### Étape 3 : Configuration de PostgreSQL

1. Lancez pgAdmin ou utilisez psql
2. Créez la base de données :
```sql
CREATE DATABASE boursicotor;
```

3. (Optionnel) Créez un utilisateur dédié :
```sql
CREATE USER boursicotor_user WITH PASSWORD 'votre_mot_de_passe';
GRANT ALL PRIVILEGES ON DATABASE boursicotor TO boursicotor_user;
```

### Étape 4 : Configuration de l'application

1. Copiez le fichier de configuration exemple :
```bash
copy .env.example .env
```

2. Éditez `.env` avec vos paramètres :
```env
# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=boursicotor
DB_USER=postgres
DB_PASSWORD=votre_mot_de_passe

# Interactive Brokers
IBKR_HOST=127.0.0.1
IBKR_PORT=7497  # 7497 pour paper trading, 7496 pour live
IBKR_CLIENT_ID=1
IBKR_ACCOUNT=votre_compte_ibkr

# Trading (laisser en mode paper trading au début)
PAPER_TRADING=True
MAX_POSITION_SIZE=10000
RISK_PER_TRADE=0.02
STOP_LOSS_PERCENT=0.05
```

### Étape 5 : Initialisation de la base de données

```bash
python database\init_db.py
```

Vous devriez voir :
```
✅ Database tables created successfully
✅ Initial tickers added successfully
✅ Database initialization completed
```

## 🎮 Lancement de l'application

### 1. Démarrez TWS ou IB Gateway
- Lancez TWS (Trader Workstation) ou IB Gateway
- Connectez-vous avec vos identifiants
- Assurez-vous que l'API est activée

### 2. Lancez Boursicotor
```bash
streamlit run frontend\app.py
```

L'application s'ouvrira automatiquement dans votre navigateur à l'adresse :
`http://localhost:8501`

## 🧪 Vérification de l'installation

### Test de connexion à la base de données :
```bash
python -c "from backend.models import SessionLocal; db = SessionLocal(); print('✅ Database OK'); db.close()"
```

### Test de connexion IBKR :
```bash
python brokers\ibkr_client.py
```

## 📝 Premiers pas

1. **Connectez-vous à IBKR** dans l'application (sidebar)
2. **Collectez des données** : Page "Collecte de Données"
   - Sélectionnez TTE (TotalEnergies) ou WLN (Worldline)
   - Choisissez une durée (ex: 5 jours)
   - Téléchargez les données

3. **Visualisez l'analyse technique** : Page "Analyse Technique"
   - Sélectionnez un ticker
   - Consultez les indicateurs calculés

4. **Testez une stratégie** : Page "Backtesting" (à venir)

## ⚠️ Dépannage

### Erreur : "ModuleNotFoundError"
```bash
# Assurez-vous que l'environnement virtuel est activé
.\venv\Scripts\activate

# Réinstallez les dépendances
pip install -r requirements.txt
```

### Erreur : "Connection refused" (IBKR)
- Vérifiez que TWS/IB Gateway est démarré
- Vérifiez le port dans `.env` (7497 ou 7496)
- Vérifiez que l'API est activée dans TWS

### Erreur : "Database connection failed"
- Vérifiez que PostgreSQL est démarré
- Vérifiez les credentials dans `.env`
- Vérifiez que la base de données `boursicotor` existe

### TA-Lib ne s'installe pas
- Utilisez le fichier wheel (.whl) approprié pour votre version de Python
- Ou commentez `ta-lib` dans requirements.txt et continuez sans

## 📚 Structure du projet

```
boursicotor/
├── backend/              # Logique métier et API
│   ├── config.py        # Configuration
│   ├── models.py        # Modèles de base de données
│   ├── data_collector.py # Collecte de données
│   └── technical_indicators.py # Indicateurs techniques
├── frontend/            # Interface Streamlit
│   └── app.py          # Application principale
├── brokers/            # Intégration brokers
│   └── ibkr_client.py # Client Interactive Brokers
├── strategies/         # Stratégies de trading
│   └── base_strategies.py
├── backtesting/       # Moteur de backtesting
│   └── engine.py
├── ml_models/         # Modèles ML
│   └── pattern_detector.py
├── database/          # Scripts SQL
│   ├── init_db.py
│   └── schema.sql
└── utils/            # Utilitaires
    └── helpers.py
```

## 🔒 Sécurité

- **Ne commitez JAMAIS le fichier `.env`** sur Git
- Utilisez le mode **paper trading** pour les tests
- Testez vos stratégies sur des données historiques avant de trader en réel
- Limitez toujours votre risque par trade

## 📞 Support

En cas de problème :
1. Consultez les logs dans `logs/boursicotor.log`
2. Vérifiez la configuration dans `.env`
3. Consultez la documentation IBKR : https://interactivebrokers.github.io/

## 🎯 Prochaines étapes

Une fois l'installation réussie :
1. Collectez des données historiques pour plusieurs tickers
2. Explorez les indicateurs techniques
3. Testez différentes stratégies en backtesting
4. Entraînez des modèles ML
5. Activez le paper trading pour tester en conditions réelles

---

**Bon trading ! 🚀**
