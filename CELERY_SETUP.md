# Système de collecte asynchrone avec Celery + Redis

## 📋 Vue d'ensemble

Ce système permet de collecter des données de manière asynchrone en arrière-plan, avec les avantages suivants :

- ✅ Survit aux changements de page
- ✅ Survit à la fermeture du navigateur
- ✅ Survit à la mise en veille
- ✅ Survit au redémarrage du serveur Streamlit
- ✅ Progression en temps réel
- ✅ Monitoring via Flower
- ✅ Retry automatique en cas d'erreur

## 🚀 Installation

### 1. Installer Redis (Windows)

**Option A : Via Chocolatey**
```powershell
choco install redis-64
```

**Option B : Via WSL (recommandé)**
```bash
# Dans WSL Ubuntu
sudo apt update
sudo apt install redis-server
sudo service redis-server start
```

**Option C : Docker**
```bash
docker run -d -p 6379:6379 redis:latest
```

### 2. Installer les dépendances Python

```bash
pip install -r requirements_celery.txt
```

### 3. Mettre à jour la base de données

```bash
python -c "from backend.models import init_db; init_db()"
```

## 🏃 Lancement

### Terminal 1 : Redis (si pas déjà lancé)
```bash
# WSL
sudo service redis-server start

# Ou Docker
docker start redis
```

### Terminal 2 : Celery Worker
```bash
celery -A backend.celery_config worker --loglevel=info --pool=solo
```

> Note : `--pool=solo` est nécessaire sur Windows

### Terminal 3 : Flower (monitoring optionnel)
```bash
celery -A backend.celery_config flower
```
Puis ouvrez http://localhost:5555

### Terminal 4 : Streamlit
```bash
streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0
```

## 📊 Utilisation

1. Connectez-vous à IBKR via la sidebar
2. Allez dans "Collecte de Données"
3. Sélectionnez un ticker et les paramètres
4. Cliquez sur "Récupérer les données"
5. Un job est créé → vous pouvez changer de page
6. Allez dans "Historique des collectes" pour voir la progression
7. La collecte continue même si vous fermez le navigateur !

## 🔧 Configuration

Dans `.env`, ajoutez :
```env
# Redis configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

## 📈 Monitoring

### Via Flower (Web UI)
- URL : http://localhost:5555
- Voir tous les workers actifs
- Voir toutes les tâches en cours/terminées
- Statistiques en temps réel

### Via la base de données
```python
from backend.job_manager import JobManager

# Statistiques
stats = JobManager.get_statistics()
print(stats)

# Jobs actifs
active = JobManager.get_active_jobs()

# Jobs récents
recent = JobManager.get_recent_jobs(limit=20)
```

## 🔄 Maintenance

### Nettoyer les vieux jobs (automatique)
```python
from backend.tasks import cleanup_old_jobs

# Supprimer les jobs de plus de 7 jours
cleanup_old_jobs.delay(days_to_keep=7)
```

### Monitoring Redis
```bash
redis-cli ping  # Should return PONG
redis-cli info
```

### Redémarrer Celery Worker
```bash
# Graceful shutdown
celery -A backend.celery_config control shutdown

# Puis relancer
celery -A backend.celery_config worker --loglevel=info --pool=solo
```

## 🐛 Troubleshooting

### Redis ne démarre pas
```bash
# Vérifier le port
netstat -an | findstr 6379

# Tester la connexion
redis-cli ping
```

### Celery worker ne démarre pas
- Vérifier que Redis est accessible
- Sur Windows, toujours utiliser `--pool=solo`
- Vérifier les logs pour les erreurs d'import

### Les jobs restent en PENDING
- Vérifier que le worker Celery tourne
- Vérifier la connexion Redis
- Vérifier les logs du worker

### IBKR timeout dans les tasks
- Les tasks ont un timeout de 1 heure par défaut
- Configurable dans `backend/celery_config.py`

## 📝 Architecture

```
┌─────────────┐
│  Streamlit  │ ──┐
└─────────────┘   │
                  ├──> ┌───────┐     ┌────────────┐
┌─────────────┐   │    │ Redis │ ──> │   Celery   │
│  Database   │ <─┴──> │ Broker│     │   Worker   │
└─────────────┘        └───────┘     └────────────┘
                            │              │
                            │              ↓
                            │         ┌────────────┐
                            └────────>│    IBKR    │
                                      │   Yahoo    │
                                      └────────────┘
```

## 🎯 Prochaines étapes

1. ✅ Infrastructure Celery + Redis
2. ✅ Modèle de jobs en base
3. ✅ Tasks Celery pour IBKR et Yahoo
4. ✅ Job Manager
5. ⏳ Interface Streamlit (prochaine étape)
6. ⏳ Page de monitoring des jobs
7. ⏳ Notifications (optionnel)
