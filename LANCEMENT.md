# 🚀 Lancement Rapide - 3 Étapes

## Ordre de lancement

### 1️⃣ Redis (Broker de messages)
**Double-cliquez sur:** `startRedis.bat`
- Une fenêtre s'ouvre avec Redis
- ⚠️ **NE PAS FERMER** cette fenêtre

### 2️⃣ Application complète (Celery + Streamlit)
**Double-cliquez sur:** `startBoursicotor.bat`
- Le script vérifie que Redis tourne
- **Désactive automatiquement la mise en veille** ⚡
- Lance Celery Worker (nouvelle fenêtre)
- Lance Streamlit (fenêtre actuelle)

### 3️⃣ Utiliser l'application
Ouvrir: **http://localhost:8501**

---

## ✋ Arrêt propre

**Double-cliquez sur:** `stopBoursicotor.bat`
- Arrête Streamlit
- Arrête Celery Worker
- Arrête Redis
- **Réactive la mise en veille** 💤

---

## 🪟 Fenêtres attendues

Vous devez voir **3 fenêtres** :

1. **Redis Server** (startRedis.bat)
   ```
   Redis Server - EN COURS
   NE FERMEZ PAS CETTE FENETRE !
   ```

2. **Celery Worker** (lancé par startBoursicotor.bat)
   ```
   Celery Worker - Boursicotor
   [tasks]
     . backend.tasks.collect_data_async
   ready.
   ```

3. **Streamlit** (startBoursicotor.bat)
   ```
   You can now view your Streamlit app in your browser.
   Local URL: http://localhost:8501
   ```

---

## ❌ Problèmes courants

### "Redis n'est pas lancé"
➡️ Lancez d'abord `startRedis.bat` avant `startBoursicotor.bat`

### "Redis non trouvé"
➡️ Installez Redis:
```powershell
choco install redis-64
```

### Jobs ne s'exécutent pas
➡️ Vérifiez que les 3 fenêtres sont ouvertes (Redis, Celery, Streamlit)

---

## 📁 Fichiers de lancement

| Fichier | Fonction |
|---------|----------|
| `startRedis.bat` | Lance Redis uniquement |
| `startBoursicotor.bat` | Lance Celery + Streamlit (après Redis) |
| `stopBoursicotor.bat` | Arrête tout |

---

## 🎯 Workflow quotidien

### Matin (démarrage)
1. Double-clic `startRedis.bat`
2. Double-clic `startBoursicotor.bat`
3. Ouvrir http://localhost:8501

### Soir (arrêt)
1. Double-clic `stopBoursicotor.bat`
2. Ou fermer les 3 fenêtres manuellement

---

Pour plus de détails, consultez **DEMARRAGE.md**
