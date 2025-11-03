# Guide d'utilisation - Collecte de données asynchrone avec Celery

## 📋 Vue d'ensemble

Le système de collecte de données utilise maintenant **Celery + Redis** pour exécuter les collectes de données en arrière-plan. Cela permet :

- ✅ **Pas de blocage de l'interface** : Vous pouvez continuer à utiliser l'application pendant la collecte
- ✅ **Résistance aux interruptions** : Les collectes continuent même si vous changez de page ou fermez le navigateur
- ✅ **Suivi en temps réel** : Progression visible à tout moment
- ✅ **Historique complet** : Tous les jobs sont enregistrés en base de données

---

## 🚀 Démarrage rapide

### 1. Installer Redis (première fois uniquement)

Choisissez une des 3 options suivantes :

#### Option A : Chocolatey (Recommandé pour Windows)
```powershell
choco install redis-64
redis-server
```

#### Option B : WSL (Ubuntu)
```bash
wsl
sudo apt-get update
sudo apt-get install redis-server
redis-server
```

#### Option C : Docker
```bash
docker run -d -p 6379:6379 redis:latest
```

### 2. Installer les dépendances Python

```bash
pip install -r requirements_celery.txt
```

### 3. Lancer l'application avec Celery

#### Option automatique (Windows) :
Double-cliquez sur `start_with_celery.bat`

#### Option manuelle :
Ouvrez **3 terminaux** et lancez :

**Terminal 1 - Redis** (si pas déjà lancé) :
```bash
redis-server
```

**Terminal 2 - Celery Worker** :
```bash
celery -A backend.celery_config worker --loglevel=info --pool=solo
```

**Terminal 3 - Streamlit** :
```bash
streamlit run frontend/app.py
```

**Terminal 4 (optionnel) - Flower (monitoring web)** :
```bash
celery -A backend.celery_config flower
```
Puis ouvrez http://localhost:5555

---

## 📊 Utilisation dans l'interface

### 1. Créer une collecte de données

1. Allez sur la page **💾 Collecte de Données**
2. Sélectionnez un ticker
3. Choisissez la source (IBKR ou Yahoo Finance)
4. Configurez la période et l'intervalle
5. Cliquez sur **📊 Collecter les données**

✅ Un job est créé et s'exécute en arrière-plan !

### 2. Suivre la progression

**Deux façons de voir la progression :**

#### A. Bannière globale (en haut de toutes les pages)
- Affiche automatiquement les 3 jobs actifs
- Mise à jour en temps réel
- Cliquez sur "📋 Détails" pour plus d'infos

#### B. Page dédiée (📋 Historique des collectes)
- Liste complète de tous les jobs
- Onglets pour filtrer : En cours / Complétés / Échoués / Tous
- Progression en temps réel avec barre de progression
- Possibilité d'annuler un job en cours

### 3. Consulter l'historique

Sur la page **📋 Historique des collectes** :

- **Onglet En cours** : Jobs actuellement en exécution
  - Voir la progression en temps réel
  - Annuler si nécessaire
  
- **Onglet Complétés** : Jobs terminés avec succès
  - Nombre de nouveaux enregistrements
  - Nombre d'enregistrements mis à jour
  - Temps d'exécution
  
- **Onglet Échoués** : Jobs qui ont rencontré une erreur
  - Message d'erreur détaillé
  
- **Onglet Tous** : Vue tableau de tous les jobs

---

## 🔧 Monitoring avancé avec Flower

Flower est une interface web de monitoring pour Celery.

### Lancer Flower

```bash
celery -A backend.celery_config flower
```

Puis ouvrez : **http://localhost:5555**

### Fonctionnalités de Flower

- 📊 **Dashboard** : Vue d'ensemble des workers et tasks
- 📈 **Graphiques** : Statistiques en temps réel
- 🔍 **Tasks** : Liste de toutes les tâches (en cours, complétées, échouées)
- 💻 **Workers** : État des workers Celery
- 📋 **Broker** : Informations sur Redis

---

## 📁 Structure du système

### Backend

```
backend/
├── celery_config.py      # Configuration Celery
├── tasks.py              # Tâches asynchrones (collect_data_ibkr, collect_data_yahoo)
├── job_manager.py        # Gestion des jobs (CRUD)
└── models.py             # Modèle DataCollectionJob
```

### Frontend

```
frontend/
└── app.py
    ├── main()                      # Bannière de progression globale
    ├── data_collection_page()      # Création de jobs
    └── jobs_monitoring_page()      # Suivi des jobs
```

---

## 🔄 États des jobs

Un job passe par les états suivants :

1. **⏳ PENDING** : Job créé, en attente de démarrage
2. **🔄 RUNNING** : Job en cours d'exécution
3. **✅ COMPLETED** : Job terminé avec succès
4. **❌ FAILED** : Job échoué (erreur)
5. **🚫 CANCELLED** : Job annulé par l'utilisateur

---

## 🧹 Maintenance

### Nettoyage automatique

Les jobs complétés ou échoués sont automatiquement supprimés après **7 jours**.

### Nettoyage manuel

Sur la page **📋 Historique des collectes**, cliquez sur **🗑️ Nettoyer maintenant** pour lancer le nettoyage immédiatement.

---

## ⚠️ Dépannage

### Erreur : "Celery n'est pas installé"

**Solution :**
```bash
pip install -r requirements_celery.txt
```

### Erreur : "Redis connection refused"

**Solution :**
1. Vérifiez que Redis est lancé :
   ```bash
   redis-cli ping
   ```
   Doit retourner : `PONG`

2. Si non, lancez Redis :
   ```bash
   redis-server
   ```

### Les jobs ne démarrent pas

**Solution :**
1. Vérifiez que le Celery worker est lancé :
   ```bash
   celery -A backend.celery_config worker --loglevel=info --pool=solo
   ```

2. Vérifiez les logs du worker pour voir les erreurs

### Flower ne se lance pas

**Solution :**
```bash
pip install flower==2.0.1
celery -A backend.celery_config flower
```

### Worker Windows : "NotImplementedError: pool"

**Solution :**
Utilisez l'option `--pool=solo` :
```bash
celery -A backend.celery_config worker --loglevel=info --pool=solo
```

---

## 🎯 Bonnes pratiques

1. **Toujours lancer Redis en premier** avant le worker Celery
2. **Ne pas fermer le terminal du worker** pendant les collectes
3. **Utiliser Flower** pour debugger les problèmes de tasks
4. **Consulter régulièrement l'historique** pour vérifier les erreurs
5. **Annuler les jobs bloqués** via l'interface de monitoring

---

## 📚 Ressources

- [Documentation Celery](https://docs.celeryproject.org/)
- [Documentation Redis](https://redis.io/documentation)
- [Documentation Flower](https://flower.readthedocs.io/)
- [CELERY_SETUP.md](CELERY_SETUP.md) - Guide d'installation détaillé

---

## 💡 Astuces

### Lancer plusieurs collectes en parallèle

Vous pouvez créer plusieurs jobs en même temps ! Ils s'exécuteront tous en parallèle (selon le nombre de workers).

### Vérifier la progression depuis Flower

1. Ouvrez http://localhost:5555
2. Allez dans "Tasks"
3. Cliquez sur un task pour voir les détails et la progression

### Tester la résistance aux interruptions

1. Créez un job de collecte longue (ex: 1 mois de données IBKR à 5 sec)
2. Fermez le navigateur
3. Attendez quelques minutes
4. Rouvrez l'application
5. Le job continue de progresser ! ✅

---

**Questions ou problèmes ?** Consultez le fichier CELERY_SETUP.md pour plus de détails.
