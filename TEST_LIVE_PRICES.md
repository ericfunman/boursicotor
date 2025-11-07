# 🧪 Guide de Test - Page Cours Live (Non-Bloquante)

## ✅ Prérequis Vérifiés

- ✅ Redis running sur `localhost:6379`
- ✅ Celery worker running et chargé avec `backend.live_data_task`
- ✅ Streamlit compilé sans erreurs
- ✅ IBKR connection available

## 🚀 Étapes de Test

### 1. Démarrage des Services

**Console 1 - Redis** (Déjà en cours):
```
C:\redis\redis-server.exe
```

**Console 2 - Celery Worker**:
```powershell
cd c:\Users\Eric LAPINA\Documents\Boursicotor
celery -A backend.celery_config worker --loglevel=info --pool=solo
```

Vous devriez voir :
```
[tasks]
  . backend.live_data_task.stream_live_data_continuous
  . backend.tasks.cleanup_old_jobs
  . backend.tasks.collect_data_ibkr

celery@DESKTOP-ER67VOP ready.
```

**Console 3 - Streamlit**:
```powershell
cd c:\Users\Eric LAPINA\Documents\Boursicotor
streamlit run frontend/app.py
```

Attendez que vous voyiez:
```
  You can now view your Streamlit app in your browser.
  Local URL: http://localhost:8501
```

### 2. Test de la Page Cours Live

1. **Ouvrez le navigateur**:
   - Allez à `http://localhost:8501`

2. **Naviguez à la page "💹 Cours Live"**:
   - Cliquez sur "💹 Cours Live" dans la sidebar

3. **Chargement des données historiques**:
   - Vous devriez voir: `✅ 18 données historiques chargées depuis la base de données`
   - Ou: `ℹ️ Aucune donnée historique. Les données seront collectées en temps réel.`

4. **Sélectionnez un symbole**:
   - Exemple: "WLN (Wallonie)" depuis le dropdown
   - L'échelle de temps par défaut est "1s"

5. **Cliquez sur "▶️ Démarrer"**:
   - Le bouton devrait devenir "⏸️ Pause"
   - Les métriques devraient commencer à se mettre à jour:
     - **Prix Actuel**: ex "42.50 €"
     - **Variation**: ex "+0.25 (+0.59%)"
     - **Volume**: ex "1,234,567"
     - **Dernière MAJ**: ex "17:32:45"
   - Le graphique devrait afficher une courbe de prix

### 3. Vérifications Importantes

#### ✅ L'interface devrait RESTER RESPONSIVE:
- Vous pouvez cliquer sur d'autres pages (Dashboard, Trading, etc.)
- Les métriques et le graphique se mettent à jour régulièrement
- Aucun "lag" ou freeze

#### ✅ Logs Celery devraient afficher:
```
[Stream] Starting live stream for WLN (duration: 1800s)
[Stream] Requesting market data for WLN
[Stream] WLN: 42.50€
[Stream] Collected X data points for WLN
```

#### ✅ Logs Streamlit devraient afficher:
```
[UI] Started live data task <task_id> for WLN
[UI] Got WLN from Redis: 42.50€
```

### 4. Test de Pause/Reprise

1. **Cliquez sur "⏸️ Pause"**:
   - Le bouton devrait redevenir "▶️ Démarrer"
   - Les mises à jour devraient s'arrêter

2. **Cliquez sur "▶️ Démarrer"**:
   - Une NOUVELLE tâche Celery devrait démarrer
   - Les mises à jour devraient reprendre

### 5. Navigation et Tests de Stress

1. **Naviguez entre les pages**:
   - Aller au "Dashboard"
   - Revenir à "Cours Live"
   - Les données devraient se mettre à jour normalement

2. **Ouvrez plusieurs symboles**:
   - Changez de symbole (ex: WLN → autre)
   - Une nouvelle tâche Celery devrait démarrer
   - Les données anciennes devraient être purgées

3. **Laissez tourner 5 minutes**:
   - Vérifiez que l'interface reste responsive
   - Aucun crash ou freeze
   - Les données continuent à s'accumuler

## 🔍 Troubleshooting

### "⚠️ Pas de données temps réel IBKR disponibles"
**Cause**: La tâche Celery ne collecte pas les données
- Vérifiez que Celery est running
- Vérifiez que Redis est accessible: `redis-cli ping` → `PONG`
- Vérifiez les logs Celery pour les erreurs IBKR
- Vérifiez la connexion IBKR depuis la sidebar

### Interface reste gelée
**Cause**: Il y a probablement une boucle bloquante quelque part
- Vérifiez que vous avez la dernière version du code
- Redémarrez Streamlit
- Vérifiez que `st.rerun()` n'est pas appelé dans la page live_prices

### "Cannot connect to redis://localhost:6379/0"
**Cause**: Redis n'est pas running
- Redémarrez Redis: `Start-Process -FilePath "C:\redis\redis-server.exe"`
- Vérifiez la connexion: `redis-cli ping`

### Celery worker se ferme après quelques secondes
**Cause**: Une erreur lors du démarrage
- Vérifiez les logs Celery
- Assurez-vous que `backend/live_data_task.py` existe
- Vérifiez que `celery_config.py` include `'backend.live_data_task'`

## 📊 Résultat Attendu

Une fois que tout fonctionne:

1. **L'interface ne gèle JAMAIS** ✅
2. **Les prix se mettent à jour régulièrement** (toutes les 1-2 secondes) ✅
3. **Vous pouvez naviguer librement entre les pages** ✅
4. **Arrêter/démarrer fonctionne correctement** ✅
5. **Les logs Celery montrent des données collectées** ✅

## 📝 Notes Techniques

### Comment ça fonctionne maintenant:

```
Utilisateur clique "Démarrer"
    ↓
Streamlit lance tâche Celery: stream_live_data_continuous()
    ↓
Celery BACKGROUND TASK:
  - Se connecte à IBKR
  - Boucle toutes les 0.5s:
    * Demande le dernier prix
    * Stocke dans Redis (TTL 60s)
    ↓
Streamlit FRONTEND (NON-BLOQUANT):
  - Lit depuis Redis (rapide!)
  - Affiche prix/graphique/indicateurs
  - Retourne contrôle immédiatement
  - Utilisateur peut cliquer librement
    ↓
Toutes les 1-2 secondes: Page se rafraîchit automatiquement
    (Streamlit refresh cycle normal)
    ↓
Utilisateur clique "Pause"
    - Tâche Celery s'arrête
    - Redis se vide après 60s
```

## ✨ Améliorations Futures

- [ ] Auto-refresh via WebSocket au lieu de polling
- [ ] Stockage des données live dans la base de données
- [ ] Support de plusieurs symboles simultanément
- [ ] Graphique Plotly avec streaming en direct
- [ ] Indicateurs calculés en temps réel

---

**Status**: ✅ **PRÊT À TESTER**
