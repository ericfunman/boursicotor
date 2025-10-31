# 🚀 Guide de Démarrage Rapide - Page Cours Live

## Installation en 3 étapes

### Étape 1️⃣ : Créer les stratégies d'exemple
```bash
python create_example_strategy.py
```

**Sortie attendue :**
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

---

### Étape 2️⃣ : Lancer l'application
```bash
streamlit run frontend/app.py
```

---

### Étape 3️⃣ : Utiliser la page Cours Live

#### Interface utilisateur

```
┌─────────────────────────────────────────────────────────┐
│  📊 Cours Live                                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  🎯 Stratégie de trading                                │
│  ┌──────────────────────────────────────────────────┐  │
│  │ RSI + MACD Momentum                              ▼│  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  Sélectionner une action    Échelle    Contrôles       │
│  ┌────────────────────┐  ┌────────┐  ┌──────────┐     │
│  │ WLN - Worldline   ▼│  │ 1min  ▼│  │ ▶️ Démarrer│     │
│  └────────────────────┘  └────────┘  └──────────┘     │
│                                                          │
├─────────────────────────────────────────────────────────┤
│  Prix Actuel    Variation    Volume      Dernière MAJ  │
│  45.32 €        +0.85%       125,450     14:32:15      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  📈 Graphique avec Signaux                              │
│  ┌────────────────────────────────────────────────────┐│
│  │  48 ┤                           🔴                  ││
│  │     ┤         🟢               ╱                    ││
│  │  46 ┤        ╱  ╲            ╱                      ││
│  │     ┤      ╱      ╲        ╱    🟢                  ││
│  │  44 ┤    ╱          ╲    ╱    ╱  ╲                 ││
│  │     ┤  ╱              ╲╱    ╱      ╲               ││
│  │  42 ┤╱                 🟢 ╱          ╲     🔴       ││
│  │     └────────────────────────────────────────────  ││
│  │      10:00  11:00  12:00  13:00  14:00            ││
│  └────────────────────────────────────────────────────┘│
│                                                          │
│  📊 5 signaux détectés : 3 achats, 2 ventes             │
│                                                          │
├─────────────────────────────────────────────────────────┤
│  📊 Indicateurs Techniques                              │
│                                                          │
│  RSI (14)       MACD           Signal                   │
│  42.15          0.0234         ACHAT 🟢 (RSI + MACD)    │
│  Normal         ---                                     │
│                                                          │
├─────────────────────────────────────────────────────────┤
│  🎯 Analyse de la stratégie: RSI + MACD Momentum        │
│                                                          │
│  Nombre de trades    Taux de réussite    Profit total  │
│  8                   62.5%               +4.25 €        │
│                      5W / 3L             +9.35%         │
│                                                          │
│  📋 Derniers trades                                     │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Entrée     Prix   Sortie    Prix    Profit  %   │  │
│  ├──────────────────────────────────────────────────┤  │
│  │ 14:25:30  44.20€  14:32:15  45.32€  +1.12€ +2.5%│  │
│  │ 13:45:12  46.80€  14:10:22  45.90€  -0.90€ -1.9%│  │
│  │ 12:30:45  43.15€  13:20:10  46.50€  +3.35€ +7.8%│  │
│  │ ...                                              │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 Interprétation des Signaux

### Signaux d'Achat 🟢
- **Petit triangle vert** : Signal d'achat historique détecté
- **Grand triangle vert clair** : Signal d'achat ACTUEL (trade possible)

**Exemple avec RSI + MACD Momentum :**
```
Conditions : RSI < 30 ET MACD > Signal
Interprétation : Action survendue + momentum haussier
```

### Signaux de Vente 🔴
- **Petit triangle rouge** : Signal de vente historique détecté
- **Grand triangle rouge orangé** : Signal de vente ACTUEL (trade possible)

**Exemple avec RSI + MACD Momentum :**
```
Conditions : RSI > 70 ET MACD < Signal
Interprétation : Action surachetée + momentum baissier
```

---

## 📊 Métriques de Performance

### Nombre de trades
- **Total de positions ouvertes et fermées** selon les signaux
- Un trade = Achat → Vente

### Taux de réussite
- **% de trades gagnants** sur le total
- Formule : `(Trades gagnants / Total trades) × 100`

### Profit total
- **Somme des profits/pertes** de tous les trades
- Affiché en € et en %

### Profit moyen
- **Profit moyen par trade**
- Formule : `Profit total / Nombre de trades`

---

## 🔍 Exemple Concret

### Scénario : WLN avec stratégie "RSI + MACD Momentum"

**Données chargées :**
```
✅ 1,247 données historiques chargées depuis la base de données
```

**Signaux détectés :**
```
📊 12 signaux détectés : 7 achats, 5 ventes
```

**Performance :**
```
┌──────────────────────────────────────────────┐
│ Nombre de trades    : 5                      │
│ Taux de réussite    : 60% (3W / 2L)         │
│ Profit total        : +6.45 € (+14.2%)      │
│ Profit moyen        : +1.29 € (+2.8%)       │
└──────────────────────────────────────────────┘
```

**Détail des trades :**
```
┌────────────────────────────────────────────────────────────┐
│ # │ Entrée          │ Sortie          │ Profit │ % │ Type │
├───┼─────────────────┼─────────────────┼────────┼───┼──────┤
│ 1 │ 2024-01-15 10:30│ 2024-01-15 14:20│ +2.30€ │+5%│ 🟢   │
│ 2 │ 2024-01-16 09:15│ 2024-01-16 11:45│ -1.10€ │-2%│ 🔴   │
│ 3 │ 2024-01-17 13:00│ 2024-01-17 15:30│ +3.20€ │+7%│ 🟢   │
│ 4 │ 2024-01-18 10:45│ 2024-01-18 12:15│ +2.50€ │+6%│ 🟢   │
│ 5 │ 2024-01-19 14:00│ 2024-01-19 16:00│ -0.45€ │-1%│ 🔴   │
└────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Configuration Avancée

### Créer une Stratégie Personnalisée

1. **Créer un fichier Python** (ex: `my_strategy.py`) :

```python
from backend.models import SessionLocal, Strategy
import json

db = SessionLocal()

# Définir les conditions
parameters = {
    "buy_conditions": "rsi is not None and rsi < 40",
    "sell_conditions": "rsi is not None and rsi > 60",
    "indicators": ["RSI_14"],
    "description": "Achat RSI < 40, Vente RSI > 60"
}

# Créer la stratégie
strategy = Strategy(
    name="Ma Stratégie Custom",
    description="Description de ma stratégie",
    strategy_type="custom",
    parameters=json.dumps(parameters),
    is_active=True
)

db.add(strategy)
db.commit()
db.close()

print("✅ Stratégie créée!")
```

2. **Exécuter le script** :
```bash
python my_strategy.py
```

3. **Utiliser dans l'interface** :
- La stratégie apparaîtra dans le sélecteur
- Sélectionnez-la et démarrez l'analyse

---

## 🐛 Dépannage

### Problème : "Aucune donnée historique"
**Solution :** Collectez des données d'abord dans l'onglet "Collecte de Données"

### Problème : "Calcul... (X/50 points)"
**Solution :** Attendez d'avoir au moins 50 points de données pour calculer les indicateurs

### Problème : "Aucune stratégie disponible"
**Solution :** Exécutez `python create_example_strategy.py` pour créer les stratégies d'exemple

### Problème : Graphique vide
**Solution :** Vérifiez que le ticker sélectionné a des données dans la base de données

### Problème : Erreur lors de l'évaluation de la stratégie
**Solution :** Vérifiez la syntaxe des conditions dans les paramètres de la stratégie

---

## 📚 Ressources

- **Documentation complète** : `docs/LIVE_PAGE_FEATURES.md`
- **Changelog détaillé** : `docs/CHANGELOG_LIVE_PAGE.md`
- **Script de création de stratégies** : `create_example_strategy.py`

---

**Bon trading ! 🚀📈💰**
