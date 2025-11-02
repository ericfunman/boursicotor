# Boursicotor - Guide d'Installation# 📋 Guide d'Installation - Boursicotor



## 📋 PrérequisCe guide vous aidera à installer et configurer Boursicotor sur votre machine Windows.



### Logiciels requis## ✅ Prérequis

- **Python 3.11+** : https://www.python.org/downloads/

- **Git** : https://git-scm.com/downloads  ### 1. Python 3.10 ou supérieur

- **Redis pour Windows** : https://github.com/tporadowski/redis/releases (Installer dans `C:\redis`)Téléchargez et installez Python depuis [python.org](https://www.python.org/downloads/)

- **IB Gateway 10.37** : https://www.interactivebrokers.com/en/trading/ibgateway-stable.php

Vérifiez l'installation :

---```bash

python --version

## 🚀 Installation Automatique (Sur un nouveau PC)```



### 1. Cloner le repository### 2. PostgreSQL 14 ou supérieur

```bashTéléchargez et installez PostgreSQL depuis [postgresql.org](https://www.postgresql.org/download/windows/)

git clone https://github.com/ericfunman/boursicotor.git

cd boursicotor### 3. Compte Interactive Brokers

```- Créez un compte sur [Interactive Brokers](https://www.interactivebrokers.com/)

- Téléchargez TWS (Trader Workstation) ou IB Gateway

### 2. Installer Python et créer l'environnement virtuel- Activez l'API dans TWS : File → Global Configuration → API → Settings

```bash  - Cochez "Enable ActiveX and Socket Clients"

python -m venv venv  - Notez le port (7497 pour paper trading, 7496 pour live)

venv\Scripts\activate

pip install -r requirements.txt## 🚀 Installation

```

### Étape 1 : Configuration de l'environnement Python

### 3. Créer les fichiers de configuration (CREDENTIALS)

1. Ouvrez un terminal dans le dossier Boursicotor

#### ⚠️ Fichier `.env` (à créer manuellement)2. Créez un environnement virtuel :

```env```bash

# PostgreSQL Database  python -m venv venv

DATABASE_URL=postgresql://user:password@localhost:5432/boursicotor```



# Saxo Bank API (optionnel)3. Activez l'environnement virtuel :

SAXO_APP_KEY=votre_app_key```bash

SAXO_APP_SECRET=votre_app_secret.\venv\Scripts\activate

SAXO_REDIRECT_URI=http://localhost:5000/callback```



# Environment4. Mettez à jour pip :

ENVIRONMENT=development```bash

```python -m pip install --upgrade pip

```

#### ⚠️ Fichier `ibgateway_config.ini` (à créer manuellement)

```ini### Étape 2 : Installation des dépendances

[IBGateway]

# Login Credentials**IMPORTANT** : TA-Lib nécessite une installation spéciale sur Windows

Username=votre_username_ib

Password=votre_password_ib#### Installation de TA-Lib sur Windows :



# Trading Mode (paper ou live)1. Téléchargez le fichier wheel approprié depuis :

TradingMode=paper   https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib



# API Settings   Exemple pour Python 3.10 64-bit :

Port=4002   `TA_Lib‑0.4.28‑cp310‑cp310‑win_amd64.whl`

ReadOnlyApi=no

2. Installez le fichier wheel :

# Auto-restart```bash

AutoRestart=yespip install chemin\vers\TA_Lib‑0.4.28‑cp310‑cp310‑win_amd64.whl

AutoRestartTime=23:55```

```

3. Installez les autres dépendances :

**🔒 Ces fichiers sont automatiquement exclus de Git (.gitignore)**```bash

pip install -r requirements.txt

### 4. Installer IB Gateway```

1. Télécharger IB Gateway 10.37

2. Installer dans `C:\Jts\ibgateway\1037`**Si vous rencontrez des problèmes avec TA-Lib**, vous pouvez continuer sans :

3. ⚠️ Choisir **"Offline"** (pas auto-update)- Les indicateurs de base fonctionneront avec pandas_ta

- Commentez `ta-lib==0.4.28` dans requirements.txt

### 5. Installer Redis

1. Télécharger depuis https://github.com/tporadowski/redis/releases### Étape 3 : Configuration de PostgreSQL

2. Extraire dans `C:\redis`

1. Lancez pgAdmin ou utilisez psql

### 6. Installer IBC (Auto-login pour IB Gateway)2. Créez la base de données :

```bash```sql

install_ibc.batCREATE DATABASE boursicotor;

``````

Ce script installe automatiquement IBC et configure l'auto-login.

3. (Optionnel) Créez un utilisateur dédié :

---```sql

CREATE USER boursicotor_user WITH PASSWORD 'votre_mot_de_passe';

## ▶️ DémarrageGRANT ALL PRIVILEGES ON DATABASE boursicotor TO boursicotor_user;

```

### Lancement automatique

```bash### Étape 4 : Configuration de l'application

startBoursicotor.bat

```1. Copiez le fichier de configuration exemple :

```bash

Le script démarre automatiquement :copy .env.example .env

✅ IB Gateway (avec auto-login)  ```

✅ Redis  

✅ Celery Worker  2. Éditez `.env` avec vos paramètres :

✅ Streamlit → http://localhost:8501```env

# PostgreSQL

### ArrêtDB_HOST=localhost

```bashDB_PORT=5432

stopBoursicotor.batDB_NAME=boursicotor

```DB_USER=postgres

DB_PASSWORD=votre_mot_de_passe

---

# Interactive Brokers

## 📁 Fichiers de configuration requisIBKR_HOST=127.0.0.1

IBKR_PORT=7497  # 7497 pour paper trading, 7496 pour live

**À créer manuellement sur chaque PC :**IBKR_CLIENT_ID=1

- `.env` → Variables d'environnement (DB, Saxo API)IBKR_ACCOUNT=votre_compte_ibkr

- `ibgateway_config.ini` → Credentials IB Gateway

# Trading (laisser en mode paper trading au début)

**Générés automatiquement :**PAPER_TRADING=True

- `C:\IBC\config.ini` → Configuration IBC (par install_ibc.bat)MAX_POSITION_SIZE=10000

RISK_PER_TRADE=0.02

**⚠️ NE JAMAIS COMMITER ces fichiers !** (déjà dans .gitignore)STOP_LOSS_PERCENT=0.05

```

---

### Étape 5 : Initialisation de la base de données

## 🔑 Où récupérer les credentials ?

```bash

### Interactive Brokerspython database\init_db.py

- **Username** : Votre login IB```

- **Password** : Votre mot de passe IB

- **TradingMode** : `paper` (simulation, port 4002) ou `live` (réel, port 4001)Vous devriez voir :

```

### Saxo Bank API✅ Database tables created successfully

1. Créer une app sur https://www.developer.saxo/✅ Initial tickers added successfully

2. Récupérer `SAXO_APP_KEY` et `SAXO_APP_SECRET`✅ Database initialization completed

```

### PostgreSQL

- Configurer `DATABASE_URL` dans `.env` (optionnel)## 🎮 Lancement de l'application



---### 1. Démarrez TWS ou IB Gateway

- Lancez TWS (Trader Workstation) ou IB Gateway

## 🛠️ Dépannage- Connectez-vous avec vos identifiants

- Assurez-vous que l'API est activée

**IB Gateway ne se lance pas :**

→ Réexécuter `install_ibc.bat`### 2. Lancez Boursicotor

```bash

**Redis ne démarre pas :**streamlit run frontend\app.py

→ Vérifier `C:\redis\redis-server.exe` existe```



**Celery Worker erreur :**L'application s'ouvrira automatiquement dans votre navigateur à l'adresse :

→ Vérifier que Redis est bien démarré`http://localhost:8501`



---## 🧪 Vérification de l'installation



## 📦 Mise à jour### Test de connexion à la base de données :

```bash```bash

git pull origin mainpython -c "from backend.models import SessionLocal; db = SessionLocal(); print('✅ Database OK'); db.close()"

pip install -r requirements.txt```

```

### Test de connexion IBKR :

Les fichiers de configuration (`.env`, `ibgateway_config.ini`) sont préservés.```bash

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
