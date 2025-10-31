# 🧪 Guide de Test - Nouvelles Fonctionnalités de la Page Cours Live

## 📋 Prérequis

Avant de commencer les tests, assurez-vous d'avoir :

- [x] L'application Boursicotor installée
- [x] Une base de données avec des données historiques
- [x] Python et Streamlit fonctionnels
- [x] Les dépendances installées (pandas, plotly, etc.)

---

## 🚀 Procédure de Test Complète

### Test 1️⃣ : Création des Stratégies d'Exemple

**Objectif :** Créer 2 stratégies de trading dans la base de données

**Commande :**
```bash
python create_example_strategy.py
```

**Résultat attendu :**
```
🎯 Création de stratégies d'exemple...

✅ Stratégie 'RSI + MACD Momentum' créée avec succès!
   - Type: momentum
   - Conditions d'achat: RSI < 30 ET MACD > Signal
   - Conditions de vente: RSI > 70 ET MACD < Signal

✅ Stratégie 'RSI Aggressive' créée avec succès!
   - Type: mean_reversion
   - Conditions d'achat: RSI < 35
   - Conditions de vente: RSI > 65

✅ Terminé! Vous pouvez maintenant tester ces stratégies dans la page 'Cours Live'.
```

**✅ Validation :**
- [ ] 2 messages de succès affichés
- [ ] Aucune erreur Python
- [ ] Stratégies créées dans la table `strategies` de la DB

**❌ En cas d'erreur :**
- Vérifiez la connexion à la base de données
- Vérifiez que la table `strategies` existe
- Relancez les migrations si nécessaire

---

### Test 2️⃣ : Vérification des Données Historiques

**Objectif :** S'assurer qu'il y a des données historiques à afficher

**Option A : Vérifier via SQL**
```sql
SELECT ticker_id, interval, COUNT(*) as nb_records
FROM historical_data
GROUP BY ticker_id, interval;
```

**Option B : Via l'interface**
1. Lancer l'application : `streamlit run frontend/app.py`
2. Aller dans "Collecte de Données"
3. Vérifier le nombre de données pour chaque ticker

**Résultat attendu :**
```
WLN : 1,247 records (interval: 1min)
TTE : 823 records (interval: 1min)
...
```

**✅ Validation :**
- [ ] Au moins 1 ticker a plus de 50 records
- [ ] Les données sont récentes (dernières heures/jours)

**❌ Si pas de données :**
- Utilisez l'onglet "Collecte de Données" pour en générer
- Ou utilisez un des data collectors pour importer des données

---

### Test 3️⃣ : Lancement de l'Application

**Objectif :** Vérifier que l'application démarre sans erreur

**Commande :**
```bash
streamlit run frontend/app.py
```

**Résultat attendu :**
```
You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

**✅ Validation :**
- [ ] Aucune erreur au démarrage
- [ ] Page s'ouvre dans le navigateur
- [ ] Menu de navigation visible

**❌ En cas d'erreur :**
- Vérifiez les imports manquants : `pip install -r requirements.txt`
- Vérifiez la syntaxe Python : `python -m py_compile frontend/app.py`
- Consultez les logs d'erreur

---

### Test 4️⃣ : Navigation vers "Cours Live"

**Objectif :** Accéder à la page des cours en temps réel

**Procédure :**
1. Dans le menu de gauche, cliquez sur "📊 Cours Live"
2. La page doit se charger

**Résultat attendu :**
```
Page affichée avec :
- Titre "📊 Cours Live"
- Sélecteur "🎯 Stratégie de trading"
- Sélecteur "Sélectionner une action"
- Sélecteur "Échelle de temps"
- Bouton "▶️ Démarrer"
```

**✅ Validation :**
- [ ] Page chargée sans erreur
- [ ] Tous les éléments UI visibles
- [ ] Sélecteur de stratégie affiche "Aucune stratégie" + 2 stratégies

**❌ En cas de problème :**
- Vérifiez les logs Streamlit dans la console
- Vérifiez que les stratégies ont bien été créées (Test 1)

---

### Test 5️⃣ : Sélection d'une Stratégie

**Objectif :** Vérifier que le sélecteur de stratégie fonctionne

**Procédure :**
1. Cliquez sur le dropdown "🎯 Stratégie de trading"
2. Vérifiez que 3 options apparaissent :
   - Aucune stratégie
   - RSI + MACD Momentum
   - RSI Aggressive

**Résultat attendu :**
```
🎯 Stratégie de trading
┌────────────────────────────────┐
│ Aucune stratégie               │  ← Option par défaut
│ RSI + MACD Momentum            │
│ RSI Aggressive                 │
└────────────────────────────────┘
```

**✅ Validation :**
- [ ] 3 options visibles
- [ ] Sélection d'une stratégie fonctionne
- [ ] Pas d'erreur lors du changement

---

### Test 6️⃣ : Sélection d'un Ticker et Échelle de Temps

**Objectif :** Sélectionner un ticker avec des données historiques

**Procédure :**
1. Sélectionnez une stratégie (ex: "RSI + MACD Momentum")
2. Sélectionnez un ticker (ex: "WLN - Worldline")
3. Sélectionnez une échelle de temps (ex: "1min")

**Résultat attendu :**
```
Sélectionner une action    Échelle de temps
┌────────────────────┐    ┌────────┐
│ WLN - Worldline   ▼│    │ 1min  ▼│
└────────────────────┘    └────────┘
```

**✅ Validation :**
- [ ] Ticker sélectionné correctement
- [ ] Échelle de temps sélectionnée
- [ ] Pas d'erreur dans la console

---

### Test 7️⃣ : Chargement des Données Historiques

**Objectif :** Vérifier que les données historiques sont chargées automatiquement

**Procédure :**
1. Après avoir sélectionné ticker + échelle de temps + stratégie
2. Attendre quelques secondes
3. Chercher un message de confirmation

**Résultat attendu :**
```
✅ X données historiques chargées depuis la base de données
```
ou
```
ℹ️ Aucune donnée historique. Les données seront collectées en temps réel.
```

**✅ Validation :**
- [ ] Message de chargement affiché
- [ ] Nombre de données cohérent (si données existent)
- [ ] Pas d'erreur JavaScript dans la console du navigateur

**❌ Si "Aucune donnée historique" :**
- Vérifiez qu'il y a des données pour ce ticker (Test 2)
- Vérifiez l'échelle de temps sélectionnée
- Collectez des données via "Collecte de Données"

---

### Test 8️⃣ : Démarrage du Flux en Temps Réel

**Objectif :** Lancer la mise à jour en temps réel

**Procédure :**
1. Cliquez sur le bouton "▶️ Démarrer"
2. Attendre que les données commencent à s'afficher

**Résultat attendu :**
```
┌──────────────────────────────────────┐
│ Prix Actuel  Variation  Volume  MAJ  │
│ 45.32 €      +0.85%    125,450  ...  │
└──────────────────────────────────────┘

📈 Graphique s'affiche avec :
- Ligne bleue (prix)
- Zone bleue (remplissage)
- Triangles (signaux si détectés)
```

**✅ Validation :**
- [ ] Métriques affichées (Prix, Variation, Volume, MAJ)
- [ ] Graphique visible avec courbe de prix
- [ ] Si données historiques chargées : courbe commence au passé
- [ ] Bouton devient "⏸️ Pause"

**❌ En cas de problème :**
- Vérifiez la connexion internet (pour Yahoo Finance)
- Vérifiez que le ticker existe sur le marché
- Consultez les logs d'erreur Streamlit

---

### Test 9️⃣ : Visualisation des Signaux Historiques

**Objectif :** Vérifier que les signaux d'achat/vente historiques s'affichent

**Procédure :**
1. Avec une stratégie sélectionnée (ex: "RSI + MACD Momentum")
2. Avec des données historiques chargées (>50 points)
3. Attendre le calcul des indicateurs

**Résultat attendu :**
```
Sur le graphique :
- 🟢 Triangles verts = Signaux d'achat historiques
- 🔴 Triangles rouges = Signaux de vente historiques

Message :
📊 X signaux détectés : Y achats, Z ventes
```

**✅ Validation :**
- [ ] Triangles visibles sur le graphique
- [ ] Compteur de signaux affiché
- [ ] Nombre d'achats + ventes = total signaux
- [ ] Signaux cohérents avec la stratégie

**⏳ Si "Calcul... (X/50 points)" :**
- Attendez d'avoir au moins 50 points de données
- Le calcul se fera automatiquement

**❌ Si aucun signal :**
- Normal si les conditions de la stratégie ne sont jamais remplies
- Essayez avec une autre stratégie (ex: "RSI Aggressive")
- Vérifiez sur un autre ticker avec plus de volatilité

---

### Test 🔟 : Affichage des Indicateurs Techniques

**Objectif :** Vérifier le calcul et l'affichage du RSI et MACD

**Procédure :**
1. Attendre que >50 points soient collectés
2. Scroller vers le bas sous le graphique
3. Chercher la section "📊 Indicateurs Techniques"

**Résultat attendu :**
```
📊 Indicateurs Techniques

RSI (14)        MACD           Signal
42.15           0.0234         ACHAT 🟢 (RSI + MACD)
Normal          ---            ou VENTE 🔴 ou NEUTRE
```

**✅ Validation :**
- [ ] Section "Indicateurs Techniques" visible
- [ ] RSI affiché avec valeur numérique
- [ ] État RSI : "Normal", "Survendu" ou "Suracheté"
- [ ] MACD affiché avec valeur
- [ ] Signal actuel affiché avec couleur

**❌ Si "---" affiché :**
- Attendez d'avoir 50+ points
- Vérifiez que les données sont valides (pas de NaN)

---

### Test 1️⃣1️⃣ : Analyse de Performance de la Stratégie

**Objectif :** Vérifier l'affichage de l'analyse de performance

**Procédure :**
1. Stratégie sélectionnée (pas "Aucune stratégie")
2. Au moins 50 points de données collectés
3. Des signaux d'achat ET de vente détectés
4. Scroller vers le bas

**Résultat attendu :**
```
🎯 Analyse de la stratégie: RSI + MACD Momentum

Nombre de trades    Taux de réussite    Profit total    Profit moyen
5                   60%                 +6.45 €         +1.29 €
                    3W / 2L             +14.2%          +2.8%
```

**✅ Validation :**
- [ ] Section "Analyse de la stratégie" visible
- [ ] 4 métriques affichées
- [ ] Taux de réussite entre 0% et 100%
- [ ] Nombre de W + L = Nombre de trades
- [ ] Profit total = somme des profits individuels

**ℹ️ Si "Aucun trade complet détecté" :**
- Normal si seulement des signaux d'achat (sans ventes correspondantes)
- Attendez plus de données pour avoir des trades complets
- Essayez avec une autre stratégie ou échelle de temps

---

### Test 1️⃣2️⃣ : Tableau des Derniers Trades

**Objectif :** Vérifier l'affichage du tableau de trades

**Procédure :**
1. Avec au moins 1 trade complet (achat → vente)
2. Scroller jusqu'au bas de la section "Analyse de la stratégie"
3. Chercher "📋 Derniers trades"

**Résultat attendu :**
```
📋 Derniers trades

┌──────────────────────────────────────────────────────┐
│ Entrée          Prix Entrée  Sortie         Prix... │
├──────────────────────────────────────────────────────┤
│ 2024-01-15 10:30  44.20 €   2024-01-15 14:20  45... │
│ 2024-01-16 09:15  46.80 €   2024-01-16 11:45  45... │
│ ...                                                  │
└──────────────────────────────────────────────────────┘
```

**✅ Validation :**
- [ ] Tableau visible et lisible
- [ ] Colonnes : Entrée, Prix Entrée, Sortie, Prix Sortie, Profit, Profit %
- [ ] Dates au format "YYYY-MM-DD HH:MM:SS"
- [ ] Prix au format "XX.XX €"
- [ ] Profit en € et en %
- [ ] Maximum 10 trades affichés

**❌ Si tableau vide :**
- Normal si aucun trade complet
- Voir le message informatif sous le tableau

---

### Test 1️⃣3️⃣ : Signal en Temps Réel

**Objectif :** Vérifier la détection d'un signal actuel

**Procédure :**
1. Laisser tourner le flux en temps réel
2. Attendre qu'un signal se déclenche
3. Observer le graphique et le panneau d'indicateurs

**Résultat attendu (si signal d'achat) :**
```
Sur le graphique :
- 🟢 Grand triangle vert clair au dernier point
- Légende : "Signal Achat (Actuel)"

Dans les indicateurs :
Signal: 🟢 ACHAT 🟢 (RSI + MACD Momentum)
```

**Résultat attendu (si signal de vente) :**
```
Sur le graphique :
- 🔴 Grand triangle rouge orangé au dernier point
- Légende : "Signal Vente (Actuel)"

Dans les indicateurs :
Signal: 🔴 VENTE 🔴 (RSI + MACD Momentum)
```

**✅ Validation :**
- [ ] Triangle de signal actuel plus grand que les historiques
- [ ] Couleur différente (vert clair ou rouge orangé)
- [ ] Signal affiché dans le panneau d'indicateurs
- [ ] Nom de la stratégie entre parenthèses

**⏳ Patience :**
- Les signaux peuvent prendre du temps à apparaître
- Dépend de la volatilité du marché
- Testez avec différentes stratégies

---

### Test 1️⃣4️⃣ : Changement de Stratégie

**Objectif :** Vérifier que le changement de stratégie recalcule les signaux

**Procédure :**
1. Démarrer avec "RSI + MACD Momentum"
2. Noter le nombre de signaux détectés
3. Changer pour "RSI Aggressive"
4. Comparer les résultats

**Résultat attendu :**
```
Avant (RSI + MACD Momentum) :
📊 12 signaux détectés : 7 achats, 5 ventes
Taux de réussite : 60%

Après (RSI Aggressive) :
📊 18 signaux détectés : 10 achats, 8 ventes
Taux de réussite : 55%
```

**✅ Validation :**
- [ ] Nombre de signaux change
- [ ] Triangles sur le graphique repositionnés
- [ ] Métriques de performance recalculées
- [ ] Tableau de trades mis à jour

**💡 Observation :**
- "RSI Aggressive" devrait générer plus de signaux (seuils plus larges)
- Performance peut être meilleure ou pire selon le marché

---

### Test 1️⃣5️⃣ : Changement de Ticker/Échelle

**Objectif :** Vérifier le rechargement des données historiques

**Procédure :**
1. Commencer avec WLN en 1min
2. Noter le nombre de données historiques
3. Changer pour WLN en 5min
4. Observer le rechargement

**Résultat attendu :**
```
Changement détecté → Message :
✅ X données historiques chargées depuis la base de données

Où X est différent de la valeur précédente
```

**✅ Validation :**
- [ ] Message de rechargement affiché
- [ ] Nouveau nombre de données
- [ ] Graphique réinitialisé
- [ ] Signaux recalculés

---

### Test 1️⃣6️⃣ : Bouton Pause/Reprendre

**Objectif :** Vérifier le contrôle du flux temps réel

**Procédure :**
1. Cliquez sur "⏸️ Pause"
2. Attendre quelques secondes
3. Vérifier que les données ne se mettent plus à jour
4. Cliquez sur "▶️ Démarrer"
5. Vérifier que la mise à jour reprend

**Résultat attendu :**
```
Après Pause :
- Bouton devient "▶️ Démarrer"
- Métriques figées
- Graphique ne bouge plus
- Échelle de temps réactivée

Après Démarrer :
- Bouton devient "⏸️ Pause"
- Métriques à jour
- Graphique en mouvement
- Échelle de temps désactivée
```

**✅ Validation :**
- [ ] Bouton change d'état
- [ ] Mise à jour s'arrête/reprend
- [ ] Échelle de temps enable/disable

---

### Test 1️⃣7️⃣ : Performance avec Gros Dataset

**Objectif :** Tester avec beaucoup de données historiques

**Procédure :**
1. Sélectionner un ticker avec >1000 points historiques
2. Sélectionner "RSI + MACD Momentum"
3. Observer le temps de chargement et calcul

**Résultat attendu :**
```
✅ 1,247 données historiques chargées depuis la base de données
Temps de calcul : quelques secondes
📊 X signaux détectés : Y achats, Z ventes
```

**✅ Validation :**
- [ ] Chargement en moins de 10 secondes
- [ ] Pas d'erreur "timeout"
- [ ] Graphique s'affiche correctement
- [ ] Signaux calculés sur tout l'historique

**⚠️ Si lent :**
- Normal pour >5000 points
- Envisager d'optimiser avec NumPy/Pandas vectorization
- Limiter l'historique chargé

---

## 📊 Résultats des Tests

### Tableau Récapitulatif

| # | Test | Résultat | Notes |
|---|------|----------|-------|
| 1 | Création stratégies | ✅ ❌ | |
| 2 | Données historiques | ✅ ❌ | |
| 3 | Lancement app | ✅ ❌ | |
| 4 | Navigation | ✅ ❌ | |
| 5 | Sélecteur stratégie | ✅ ❌ | |
| 6 | Sélection ticker/échelle | ✅ ❌ | |
| 7 | Chargement historique | ✅ ❌ | |
| 8 | Flux temps réel | ✅ ❌ | |
| 9 | Signaux historiques | ✅ ❌ | |
| 10 | Indicateurs techniques | ✅ ❌ | |
| 11 | Analyse performance | ✅ ❌ | |
| 12 | Tableau trades | ✅ ❌ | |
| 13 | Signal temps réel | ✅ ❌ | |
| 14 | Changement stratégie | ✅ ❌ | |
| 15 | Changement ticker/échelle | ✅ ❌ | |
| 16 | Pause/Reprendre | ✅ ❌ | |
| 17 | Gros dataset | ✅ ❌ | |

---

## 🐛 Problèmes Courants et Solutions

### Problème 1 : "Aucune stratégie disponible"
**Cause :** Stratégies pas créées
**Solution :** `python create_example_strategy.py`

### Problème 2 : "Aucune donnée historique"
**Cause :** Pas de données pour ce ticker/échelle
**Solution :** Collectez des données via "Collecte de Données"

### Problème 3 : "Calcul... (X/50 points)"
**Cause :** Pas assez de données pour les indicateurs
**Solution :** Attendez d'avoir 50+ points

### Problème 4 : Graphique vide
**Cause :** Ticker inexistant ou pas de données
**Solution :** Vérifiez le ticker dans la DB

### Problème 5 : Aucun signal détecté
**Cause :** Conditions de stratégie jamais remplies
**Solution :** Normal, essayez autre stratégie/ticker

### Problème 6 : Erreur d'évaluation de stratégie
**Cause :** Syntaxe incorrecte dans les paramètres
**Solution :** Vérifiez les conditions dans la DB

### Problème 7 : Lenteur avec gros dataset
**Cause :** Trop de points à calculer
**Solution :** Limitez l'historique ou optimisez le code

---

## ✅ Validation Finale

**Tous les tests passent ?** 🎉
- [x] Stratégies créées
- [x] Données historiques chargées
- [x] Signaux affichés
- [x] Performance calculée
- [x] Interface réactive

**→ Les fonctionnalités sont prêtes à l'emploi !**

---

## 📝 Rapport de Test

**Date :** ___________
**Testeur :** ___________
**Version :** 1.0.0

**Résumé :**
- Tests réussis : __ / 17
- Tests échoués : __ / 17
- Bugs trouvés : __

**Commentaires :**
_____________________________________
_____________________________________

---

**Bon test ! 🧪🚀**
