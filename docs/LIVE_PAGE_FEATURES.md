# Nouvelles Fonctionnalités - Page Cours Live 📈

## 🎉 3 Nouvelles Fonctionnalités Ajoutées

### 1. 📊 Chargement des Données Historiques

La page "Cours Live" charge maintenant **automatiquement les données historiques** depuis la base de données au démarrage.

**Fonctionnement :**
- Lorsque vous sélectionnez un ticker et une échelle de temps, toutes les données historiques stockées dans la base de données sont chargées
- Les données sont affichées sur le graphique avec les nouvelles données en temps réel qui s'ajoutent continuellement
- Si vous changez de ticker ou d'échelle de temps, les données historiques correspondantes sont rechargées automatiquement

**Exemple :**
```
Ticker: WLN
Échelle: 1min
Résultat: Affiche toutes les données 1min de WLN stockées dans la DB + nouvelles données en temps réel
```

---

### 2. 🎯 Sélecteur de Stratégie

Vous pouvez maintenant **sélectionner une stratégie de trading** pour visualiser les signaux d'achat/vente.

**Fonctionnement :**
- Un nouveau sélecteur "🎯 Stratégie de trading" apparaît en haut de la page
- Sélectionnez une stratégie existante ou "Aucune stratégie" pour utiliser la stratégie par défaut (RSI < 30 & MACD > Signal)
- La stratégie sélectionnée est appliquée à toutes les données (historiques + temps réel)

**Stratégies d'exemple incluses :**
1. **RSI + MACD Momentum** : Achat RSI < 30 ET MACD > Signal, Vente RSI > 70 ET MACD < Signal
2. **RSI Aggressive** : Achat RSI < 35, Vente RSI > 65

Pour créer ces stratégies d'exemple, exécutez :
```bash
python create_example_strategy.py
```

---

### 3. 📈 Affichage des Signaux de Trading

Les signaux d'achat/vente basés sur la stratégie sélectionnée sont maintenant **affichés visuellement sur le graphique**.

**Affichage visuel :**
- 🟢 **Triangles verts vers le haut** : Signaux d'ACHAT historiques
- 🔴 **Triangles rouges vers le bas** : Signaux de VENTE historiques
- 🟢 **Triangle vert clair (plus grand)** : Signal d'ACHAT actuel
- 🔴 **Triangle rouge orangé (plus grand)** : Signal de VENTE actuel

**Analyse des trades :**

Un nouveau panneau "🎯 Analyse de la stratégie" s'affiche sous les indicateurs techniques, montrant :

1. **Métriques de performance :**
   - Nombre total de trades exécutés
   - Taux de réussite (% de trades gagnants)
   - Nombre de trades gagnants (W) et perdants (L)
   - Profit total en € et en %
   - Profit moyen par trade

2. **Tableau des derniers trades :**
   - Date/heure d'entrée et de sortie
   - Prix d'entrée et de sortie
   - Profit en € et en %
   - Les 10 derniers trades sont affichés

**Simulation des trades :**
Le système simule automatiquement l'exécution de trades basée sur les signaux :
- Un signal d'ACHAT ouvre une position LONG
- Un signal de VENTE ferme la position LONG et calcule le profit/perte
- Seuls les trades complets (achat → vente) sont comptabilisés

---

## 🚀 Comment Utiliser

### Étape 1 : Créer les Stratégies d'Exemple
```bash
python create_example_strategy.py
```

### Étape 2 : Lancer l'Application
```bash
streamlit run frontend/app.py
```

### Étape 3 : Naviguer vers "Cours Live"
- Sélectionnez un ticker (ex: WLN)
- Sélectionnez une stratégie (ex: RSI + MACD Momentum)
- Sélectionnez une échelle de temps (ex: 1min)
- Cliquez sur "▶️ Démarrer"

### Étape 4 : Analyser les Résultats
- Visualisez les signaux historiques sur le graphique
- Consultez les métriques de performance de la stratégie
- Vérifiez le tableau des derniers trades
- Observez les signaux en temps réel qui apparaissent

---

## 📝 Exemple de Stratégie dans la Base de Données

Pour créer votre propre stratégie, vous devez définir les conditions d'achat et de vente en Python :

```python
parameters = {
    "buy_conditions": "rsi is not None and macd is not None and macd_signal is not None and rsi < 30 and macd > macd_signal",
    "sell_conditions": "rsi is not None and macd is not None and macd_signal is not None and rsi > 70 and macd < macd_signal",
    "indicators": ["RSI_14", "MACD"],
    "description": "Description de la stratégie"
}
```

**Variables disponibles dans les conditions :**
- `rsi` : Valeur du RSI (14 périodes)
- `macd` : Valeur du MACD
- `macd_signal` : Ligne de signal du MACD
- `price` : Prix actuel

**Opérateurs logiques :**
- `and` : ET logique
- `or` : OU logique
- `not` : NON logique
- `<`, `>`, `<=`, `>=`, `==`, `!=` : Comparaisons

---

## 🔍 Détails Techniques

### Chargement des Données Historiques
```python
# Les données sont rechargées quand :
reload_needed = (
    st.session_state.get('last_ticker') != selected_symbol or
    st.session_state.get('last_time_scale') != time_scale
)

# Requête SQL pour charger les données
historical_records = db.query(HistoricalData).filter(
    HistoricalData.ticker_id == ticker_obj.id,
    HistoricalData.interval == time_scale
).order_by(HistoricalData.timestamp.asc()).all()
```

### Évaluation des Conditions de Stratégie
Les conditions sont évaluées avec la fonction `eval()` de Python en passant les valeurs des indicateurs :
```python
buy_condition = eval(params['buy_conditions'], {
    'rsi': current_rsi,
    'macd': current_macd,
    'macd_signal': current_macd_signal,
    'price': current_price,
})
```

### Simulation des Trades
```python
# Logique de simulation
if signal_type == 'buy' and no_position:
    open_position()
elif signal_type == 'sell' and has_position:
    close_position()
    calculate_profit()
```

---

## 🎨 Améliorations Futures Possibles

1. **Gestion de l'effet de levier** : Multiplier les profits/pertes
2. **Stop-loss et take-profit** : Sortie automatique des positions
3. **Trailing stop** : Stop-loss qui suit le prix
4. **Position sizing** : Calcul de la taille de position selon le risque
5. **Backtesting complet** : Tester sur plusieurs années de données
6. **Optimisation de paramètres** : Trouver les meilleurs seuils RSI/MACD
7. **Stratégies multi-indicateurs** : Combiner plus de 2 indicateurs
8. **Machine Learning** : Stratégies basées sur l'IA

---

## 📞 Support

Si vous rencontrez des problèmes ou avez des questions :
1. Vérifiez que les données historiques existent dans la base de données
2. Vérifiez que les stratégies sont bien créées (exécutez `create_example_strategy.py`)
3. Vérifiez que les indicateurs techniques sont calculés (minimum 50 points requis)

---

**Bonne analyse de trading ! 🚀📈**
