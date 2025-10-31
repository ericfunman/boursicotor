# 📊 Améliorations de la Page "Cours Live"

## 🎯 Vue d'Ensemble

La page "Cours Live" a été améliorée avec **3 nouvelles fonctionnalités majeures** permettant de visualiser et analyser l'historique des données combinées avec les données en temps réel, d'appliquer des stratégies de trading personnalisées, et de visualiser les performances de ces stratégies.

---

## ✨ Nouvelles Fonctionnalités

### 1. 📊 Chargement Automatique des Données Historiques

**Description :** Au démarrage de la page, toutes les données historiques du ticker sélectionné sont chargées depuis la base de données et affichées sur le graphique.

**Avantages :**
- Vue complète de l'historique des prix
- Contexte historique pour les signaux de trading
- Pas besoin d'attendre que les données s'accumulent
- Continuité entre les sessions

**Comment ça marche :**
```
1. Sélection du ticker (ex: WLN)
2. Sélection de l'échelle de temps (ex: 1min)
3. → Chargement automatique depuis HistoricalData
4. → Affichage de toutes les données historiques
5. → Ajout continu des nouvelles données en temps réel
```

---

### 2. 🎯 Sélecteur de Stratégie de Trading

**Description :** Possibilité de sélectionner une stratégie de trading prédéfinie pour générer automatiquement des signaux d'achat/vente.

**Stratégies incluses :**
1. **RSI + MACD Momentum**
   - Achat : RSI < 30 ET MACD > Signal
   - Vente : RSI > 70 ET MACD < Signal
   - Type : Momentum / Mean Reversion

2. **RSI Aggressive**
   - Achat : RSI < 35
   - Vente : RSI > 65
   - Type : Mean Reversion

**Comment créer vos propres stratégies :**
Voir le fichier `create_example_strategy.py` pour des exemples de création de stratégies personnalisées.

---

### 3. 📈 Visualisation des Signaux et Analyse de Performance

**Description :** Affichage visuel des signaux d'achat/vente sur le graphique et analyse détaillée des performances de la stratégie.

**Affichage visuel :**
- 🟢 **Triangles verts** : Signaux d'achat (historiques et actuels)
- 🔴 **Triangles rouges** : Signaux de vente (historiques et actuels)
- **Taille différente** : Les signaux actuels sont plus grands

**Métriques de performance affichées :**
- Nombre total de trades exécutés
- Taux de réussite (% de trades gagnants)
- Nombre de trades gagnants vs perdants
- Profit total (€ et %)
- Profit moyen par trade

**Tableau des trades :**
- Les 10 derniers trades avec détails complets
- Date/heure d'entrée et de sortie
- Prix d'entrée et de sortie
- Profit/perte en € et en %

---

## 🚀 Installation et Utilisation

### Prérequis
```bash
# Base de données avec données historiques
# (utilisez "Collecte de Données" pour en générer)
```

### Étape 1 : Créer les stratégies d'exemple
```bash
python create_example_strategy.py
```

### Étape 2 : Lancer l'application
```bash
streamlit run frontend/app.py
```

### Étape 3 : Utiliser la page
1. Naviguez vers "📊 Cours Live"
2. Sélectionnez une stratégie (ex: "RSI + MACD Momentum")
3. Sélectionnez un ticker (ex: WLN)
4. Sélectionnez une échelle de temps (ex: 1min)
5. Cliquez sur "▶️ Démarrer"
6. Observez les signaux et les performances !

---

## 📁 Fichiers Modifiés

### Code Source
- `frontend/app.py` : Modifications de la fonction `live_prices_page()`
  - Ajout du sélecteur de stratégie
  - Chargement des données historiques
  - Calcul et affichage des signaux
  - Simulation et analyse des trades

### Nouveaux Fichiers
- `create_example_strategy.py` : Script pour créer des stratégies d'exemple
- `docs/LIVE_PAGE_FEATURES.md` : Documentation complète des fonctionnalités
- `docs/CHANGELOG_LIVE_PAGE.md` : Changelog détaillé des modifications
- `docs/QUICK_START_LIVE_PAGE.md` : Guide de démarrage rapide
- `docs/README_LIVE_PAGE.md` : Ce fichier

---

## 🔧 Détails Techniques

### Chargement des Données Historiques

**SQL Query :**
```python
historical_records = db.query(HistoricalData).filter(
    HistoricalData.ticker_id == ticker_obj.id,
    HistoricalData.interval == time_scale
).order_by(HistoricalData.timestamp.asc()).all()
```

**Structure des données :**
```python
st.session_state.live_data = {
    'time': [timestamp1, timestamp2, ...],
    'price': [close1, close2, ...],
    'open': [open1, open2, ...],
    'high': [high1, high2, ...],
    'low': [low1, low2, ...],
    'volume': [volume1, volume2, ...]
}
```

### Évaluation des Stratégies

**Paramètres de stratégie (JSON) :**
```json
{
  "buy_conditions": "rsi is not None and macd is not None and rsi < 30 and macd > macd_signal",
  "sell_conditions": "rsi is not None and macd is not None and rsi > 70 and macd < macd_signal",
  "indicators": ["RSI_14", "MACD"],
  "description": "Description de la stratégie"
}
```

**Variables disponibles :**
- `rsi` : Valeur du RSI
- `macd` : Valeur du MACD
- `macd_signal` : Ligne de signal du MACD
- `price` : Prix actuel

**Évaluation :**
```python
buy_condition = eval(params['buy_conditions'], {
    'rsi': current_rsi,
    'macd': current_macd,
    'macd_signal': current_macd_signal,
    'price': current_price,
})
```

### Simulation des Trades

**Logique :**
1. Signal d'achat → Ouvre une position LONG
2. Signal de vente → Ferme la position LONG
3. Calcul du profit/perte
4. Stockage du trade dans la liste

**Code :**
```python
if signal_type == 'buy' and position is None:
    position = {'entry_time': time, 'entry_price': price}
elif signal_type == 'sell' and position is not None:
    profit = price - position['entry_price']
    profit_pct = (profit / position['entry_price']) * 100
    trades.append({...})
    position = None
```

---

## 📊 Exemple de Résultat

### Données Affichées

**Message de chargement :**
```
✅ 1,247 données historiques chargées depuis la base de données
```

**Nombre de signaux :**
```
📊 12 signaux détectés : 7 achats, 5 ventes
```

**Métriques de performance :**
```
┌──────────────────────────────────────────────┐
│ Nombre de trades    : 5                      │
│ Taux de réussite    : 60% (3W / 2L)         │
│ Profit total        : +6.45 € (+14.2%)      │
│ Profit moyen        : +1.29 € (+2.8%)       │
└──────────────────────────────────────────────┘
```

**Graphique :**
- Ligne bleue : Prix de l'action
- Triangles verts : Signaux d'achat
- Triangles rouges : Signaux de vente
- Zone bleue : Remplissage sous la courbe

---

## 🔍 Points Importants

### Minimum de Points Requis
- **50 points minimum** pour calculer les indicateurs techniques (RSI, MACD)
- Si moins de 50 points : message "Calcul... (X/50 points)"

### Sécurité
- Les conditions de stratégie utilisent `eval()` en Python
- ⚠️ Assurez-vous que les conditions sont sûres et validées

### Performance
- Le calcul sur tous les points historiques peut prendre du temps pour de gros datasets
- Optimisation possible en utilisant NumPy/Pandas vectorization

### Limitations Actuelles
- Seules les positions LONG sont supportées (pas de SHORT)
- Un seul trade ouvert à la fois
- Pas de gestion du risque (stop-loss, take-profit)
- Pas de prise en compte des frais de transaction

---

## 🚀 Améliorations Futures Possibles

### Court Terme
- [ ] Support des positions SHORT
- [ ] Stop-loss et take-profit automatiques
- [ ] Gestion de plusieurs positions simultanées
- [ ] Export des trades en CSV/Excel

### Moyen Terme
- [ ] Optimisation des paramètres de stratégie (grid search)
- [ ] Backtesting complet avec frais de transaction
- [ ] Trailing stop-loss
- [ ] Position sizing basé sur le risque

### Long Terme
- [ ] Machine Learning pour prédiction de signaux
- [ ] Analyse multi-timeframe
- [ ] Comparaison de plusieurs stratégies
- [ ] Génération automatique de rapports PDF

---

## 📚 Documentation

### Fichiers de Documentation
1. **README_LIVE_PAGE.md** (ce fichier) : Vue d'ensemble
2. **LIVE_PAGE_FEATURES.md** : Documentation détaillée des fonctionnalités
3. **CHANGELOG_LIVE_PAGE.md** : Changelog technique détaillé
4. **QUICK_START_LIVE_PAGE.md** : Guide de démarrage rapide avec exemples visuels

### Scripts Utiles
- **create_example_strategy.py** : Création de stratégies d'exemple

---

## 🐛 Support et Dépannage

### Problèmes Courants

**Problème : "Aucune donnée historique"**
- Solution : Utilisez "Collecte de Données" pour collecter des données d'abord

**Problème : "Aucune stratégie disponible"**
- Solution : Exécutez `python create_example_strategy.py`

**Problème : Indicateurs non calculés**
- Solution : Attendez d'avoir au moins 50 points de données

**Problème : Graphique vide**
- Solution : Vérifiez que le ticker a des données dans la base

**Problème : Erreur d'évaluation de stratégie**
- Solution : Vérifiez la syntaxe des conditions dans les paramètres

---

## 📞 Contact

Pour toute question ou problème :
1. Consultez la documentation dans `docs/`
2. Vérifiez les logs de l'application
3. Examinez les données dans la base de données

---

**Bon trading ! 🚀📈💰**

---

## 🎓 Ressources Supplémentaires

### Indicateurs Techniques
- **RSI (Relative Strength Index)** : Mesure la force du mouvement de prix
  - < 30 : Survendu (signal d'achat potentiel)
  - > 70 : Suracheté (signal de vente potentiel)

- **MACD (Moving Average Convergence Divergence)** : Détecte les changements de tendance
  - MACD > Signal : Tendance haussière
  - MACD < Signal : Tendance baissière

### Stratégies de Trading
- **Momentum** : Suit la tendance existante
- **Mean Reversion** : Parie sur un retour à la moyenne
- **Breakout** : Entre sur cassure de niveaux clés

### Gestion du Risque
- **Stop-loss** : Limite les pertes à un seuil prédéfini
- **Take-profit** : Sécurise les gains à un objectif
- **Position sizing** : Ajuste la taille selon le risque
- **Risk/Reward ratio** : Rapport gain potentiel / perte potentielle

---

**Dernière mise à jour : 31 octobre 2024**
