# ⚡ Quick Start - Test Live Prices Fix

## 🎯 Objectif
Tester que la page "Cours Live" n'est plus gelée.

## ⏱️ Temps: 5 minutes

---

## 🚀 Démarrage Rapide

### 1️⃣ Redis (30 secondes)
```powershell
# Vérifier Redis
"C:\redis\redis-cli.exe" ping
# → Devrait afficher: PONG
```

### 2️⃣ Celery Worker (1 minute)
```powershell
cd c:\Users\Eric LAPINA\Documents\Boursicotor
celery -A backend.celery_config worker --loglevel=info --pool=solo
```

Attendez de voir:
```
✓ celery@DESKTOP-ER67VOP ready.
✓ [tasks] . backend.live_data_task.stream_live_data_continuous
```

### 3️⃣ Streamlit (1 minute)
**Dans une NEW fenêtre PowerShell**:
```powershell
cd c:\Users\Eric LAPINA\Documents\Boursicotor
streamlit run frontend/app.py
```

Attendez:
```
✓ You can now view your Streamlit app in your browser.
✓ Local URL: http://localhost:8501
```

### 4️⃣ Browser (2 minutes)
- Ouvrez: `http://localhost:8501`
- Allez à: **💹 Cours Live** (dans la sidebar)
- Sélectionnez: **WLN (Wallonie)**
- Cliquez: **▶️ Démarrer**

---

## ✅ Vérifications Clés

### ✓ Doit voir:
- [ ] Prix actuel (ex: 42.50 €)
- [ ] Graphique avec courbe bleue
- [ ] "Dernière MAJ" se change toutes les 1-2s
- [ ] Peut cliquer sur d'autres pages

### ✓ Doit PAS voir:
- [ ] "Interface gelée"
- [ ] "Aucune donnée"
- [ ] "Erreur de connexion"
- [ ] Logs d'erreur Celery

---

## 🎯 Test Critique: "Est-ce que c'est responsive ?"

**Action**: Pendant que les prix se mettent à jour:
1. Cliquez sur **Dashboard** → Doit charger normalement
2. Cliquez sur **Cours Live** → Les prix continuent de se mettre à jour

**Résultat Attendu**: L'interface ne gèle JAMAIS ✅

---

## 🔧 Si quelque chose ne marche pas

### Redis connection error?
```powershell
# Redémarrer Redis
Remove-Item dump.rdb -Force 2>$null
Start-Process "C:\redis\redis-server.exe"
```

### Celery worker crash?
```powershell
# Vérifier que redis est running
"C:\redis\redis-cli.exe" ping  # → PONG

# Relancer Celery
celery -A backend.celery_config worker --loglevel=debug
```

### Streamlit s'arrête?
```powershell
# Vérifier Python
python --version  # → 3.13.x

# Tester imports
python -c "from frontend.app import live_prices_page; print('OK')"

# Lancer avec debug
streamlit run frontend/app.py --logger.level=debug
```

---

## 📊 Logs à Vérifier

### Celery (devrait voir):
```
[Stream] Starting live stream for WLN
[Stream] Requesting market data for WLN
[Stream] WLN: 42.50€
celery@DESKTOP-ER67VOP ready.
```

### Streamlit (devrait voir):
```
[UI] Started live data task XXX-XXX-XXX for WLN
[UI] Got WLN from Redis: 42.50€
```

---

## 🎉 Résultat: SUCCESS!

Si vous voyez les prix se mettre à jour toutes les secondes sans que l'interface gèle:

### 🟢 **LA FIX EST FONCTIONNELLE !**

Félicitations, vous avez maintenant une page Cours Live responsive et en temps réel ! 🚀

---

## 📞 Support

Si problème persiste:
1. Consultez `README_LIVE_PRICES_FIX.md`
2. Consultez `TEST_LIVE_PRICES.md`
3. Consultez `LIVE_PRICES_FIX.md` pour tech details

---

**Time to test: 5 minutes**  
**Status: ✅ READY**
