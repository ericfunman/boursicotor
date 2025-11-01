# 🚀 Guide de Démarrage Rapide - Boursicotor

## 📋 Pré-requis

1. ✅ IB Gateway ou TWS installé et configuré sur le port 4002
2. ✅ Redis installé (via Chocolatey ou MSI)
3. ✅ Environnement virtuel Python configuré

## 🎯 Démarrage Simple

### Option 1 : Automatique (Recommandé)
Double-cliquez sur `startBoursicotor.bat`

Le script va :
- ✅ Vérifier Redis (et le lancer si nécessaire)
- ✅ Lancer Celery Worker dans un terminal séparé
- ✅ Lancer Streamlit dans le terminal principal

### Option 2 : Manuel (3 terminaux)

**Terminal 1 - Redis**
```powershell
redis-server
```
➡️ **NE PAS FERMER** - Redis doit rester ouvert

**Terminal 2 - Celery Worker**
```powershell
cd C:\Users\lapin\OneDrive\Documents\Developpement\Boursicotor
.\venv\Scripts\activate
celery -A backend.tasks worker --loglevel=info --pool=solo
```
➡️ **NE PAS FERMER** - Celery doit rester ouvert

**Terminal 3 - Streamlit**
```powershell
cd C:\Users\lapin\OneDrive\Documents\Developpement\Boursicotor
.\venv\Scripts\activate
streamlit run frontend/app.py
```

## 🛑 Arrêt de l'application

### Option 1 : Automatique
Double-cliquez sur `stopBoursicotor.bat`

### Option 2 : Manuel
- Fermez chaque terminal avec `Ctrl+C`
- Ou fermez directement les fenêtres

## 🔍 Vérifier que tout fonctionne

### 1. Redis
Ouvrir PowerShell :
```powershell
redis-cli ping
```
Doit répondre : `PONG`

### 2. Celery
Vérifier dans le terminal Celery que vous voyez :
```
[tasks]
  . backend.tasks.collect_data_async
ready.
```

### 3. Streamlit
Ouvrir : http://localhost:8501
Vous devez voir l'interface Boursicotor

## 📊 Utilisation

### 1. Se connecter à IBKR
- Ouvrir IB Gateway ou TWS
- Dans Streamlit (sidebar) : Cliquer sur "🔌 Se connecter à IBKR"
- Vérifier que le statut passe à "✅ Connecté"

### 2. Collecter des données
- Aller sur "💾 Collecte de Données"
- Sélectionner un ticker (ex: TTE)
- Choisir la période et l'intervalle
- Cliquer sur "📊 Collecter les données"

### 3. Suivre la progression
- Aller sur "📋 Historique des collectes"
- Vous verrez le job en cours avec progression en temps réel
- **Vous pouvez naviguer librement pendant la collecte !**

## ❓ Problèmes fréquents

### ❌ "Redis n'est pas reconnu..."
➡️ Redis n'est pas installé ou pas dans le PATH
```powershell
choco install redis-64
```

### ❌ "Celery worker is not ready"
➡️ Le worker Celery n'est pas démarré
- Vérifier le terminal Celery
- Relancer : `celery -A backend.tasks worker --loglevel=info --pool=solo`

### ❌ Dashboard bloque ou demande reconnexion
➡️ Déconnectez-vous et reconnectez-vous à IBKR depuis la sidebar

### ❌ Jobs ne s'exécutent pas
➡️ Vérifier que Redis ET Celery sont bien lancés
- Redis : `redis-cli ping`
- Celery : Vérifier le terminal

## 🎯 Architecture des Services

```
┌─────────────────┐
│   Streamlit     │ ← Interface Web (http://localhost:8501)
│   (Frontend)    │ ← Crée les jobs de collecte
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     Redis       │ ← Broker de messages (file d'attente)
│    (Queue)      │ ← Stocke les jobs en attente
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Celery Worker   │ ← Exécuteur de tâches
│  (Executor)     │ ← Collecte réellement les données
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   SQLite DB     │ ← Stockage des données et statuts
└─────────────────┘
```

**Important** : Les 3 services (Streamlit, Redis, Celery) doivent être lancés pour une collecte asynchrone !

## 📞 Support

En cas de problème, vérifier :
1. Les logs dans le terminal Celery
2. Les logs dans le terminal Streamlit
3. Le fichier `logs/boursicotor.log`
