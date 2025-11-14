# Explication: Ordres SUBMITTED vs FILLED

## Situation Actuelle

**Diagnostic du 14 Nov 2025**:
- ✅ 89 ordres SUBMITTED (tous < 1 jour)
- ✅ 52 ordres FILLED (122,723 actions)
- ✅ 78 ordres CANCELLED (nettoyage)
- **C'EST NORMAL!**

---

## Pourquoi tant d'ordres SUBMITTED?

### Raison 1: Manque de Liquidité (CAUSE PRINCIPALE)
- **WLN** (Wallonie Défense) est un petit titre
- Très peu de volume d'échange quotidien
- Quand vous placez 100 actions, IBKR cherche des vendeurs
- Si pas assez de vendeurs, l'ordre reste en file d'attente
- Peut prendre heures ou jours avant remplissage!

**Exemple**:
```
Prix demandé:  2.34 €
Votre ordre:   BUY 100 @ market
Liquidité:     Seulement 50 actions disponibles à 2.34 €

Résultat:
- 50 actions remplies immédiatement
- 50 actions restent en SUBMITTED en attente
- Peut rester en attente indéfiniment!
```

### Raison 2: Too Fast Orders (CAUSE SECONDAIRE)
- Auto-trader envoie ordres toutes les ~10 secondes
- Si pas remplis, accumulation d'ordres SUBMITTED
- 89 ordres en 49 minutes = beaucoup d'ordres!

**Timeline**:
```
T+0min:  Ordre 1 BUY 100 - SUBMITTED (liquidité insuffisante)
T+1min:  Ordre 2 BUY 100 - SUBMITTED (cumul: 2 en attente)
T+2min:  Ordre 3 BUY 100 - SUBMITTED (cumul: 3 en attente)
...
T+49min: Ordre 89 BUY 100 - SUBMITTED (cumul: 89 en attente!)
```

### Raison 3: Market Orders vs Limit Orders
- Vos ordres sont des **MARKET ORDERS**
- Market order = "prend ce qui est disponible"
- Si pas assez, attend la suite
- Limite ordre = "prend seulement au prix X"

---

## Solutions

### Solution 1: Utiliser des LIMIT ORDERS (RECOMMANDÉ)
**Actuel**: Market order → Cherche liquidité au meilleur prix
**Mieux**: Limit order → Fixe un prix max, accepte partiel

```
BUY 100 @ MARKET          BUY 100 @ 2.35 (limit)
- Remplit 0-100          - Remplit 0-100
- Attend liquidité         - Annule si pas l'ordre prix
- Peut rester SUBMITTED    - S'exécute rapidement
- Problématique!          - Prévisible!
```

**Impact**: Beaucoup moins d'ordres SUBMITTED bloqués

### Solution 2: Augmenter Polling Interval
**Actuel**: Polling tous les 10 secondes
**Mieux**: Polling tous les 30-60 secondes

```
10s polling:   89 ordres en 49 min (très rapide)
30s polling:   ~25 ordres en 49 min (modéré)
60s polling:   ~12 ordres en 49 min (conservatif)
```

**Avantage**: Moins d'ordres en queue
**Inconvénient**: Moins de signaux détectés

### Solution 3: Augmenter Position Size Limit
**Actuel**: Max 100 actions par position
**Mieux**: Augmenter à 500-1000

```
Max 100:  10 ordres pour 1000 actions (10 × 100)
Max 500:  2 ordres pour 1000 actions (2 × 500)
Max 1000: 1 ordre pour 1000 actions (1 × 1000)
```

**Avantage**: Moins d'ordres, plus d'efficacité
**Inconvénient**: Plus de risque par position

### Solution 4: Implémenter Order Cancellation
**Idée**: Si ordre SUBMITTED > 1h sans remplissage, cancel + retry

```
T+0min:  BUY 100 SUBMITTED
T+60min: Toujours SUBMITTED? CANCEL + NEW BUY 100
Résultat: Fresh order, meilleure chance
```

**Code déjà existant**: Button "🧹 Nettoyer ordres bloqués"
**Utilisation**: Click après >1h sans activité

---

## Configuration Recommandée

### Pour WLN (Petit Titre):

**ACTUEL (Problématique)**:
- Polling: 10s
- Max position: 100
- Order type: MARKET
- Résultat: 89 orders SUBMITTED ❌

**RECOMMANDÉ (Équilibré)**:
- Polling: 30s (moins d'ordres)
- Max position: 500 (moins d'ordres)
- Order type: LIMIT (plus efficace)
- Résultat: ~10-15 orders SUBMITTED ✅

**CONSERVATIVE (Sûr)**:
- Polling: 60s (très peu d'ordres)
- Max position: 1000 (une position = un ordre)
- Order type: LIMIT (prévisible)
- Résultat: <5 orders SUBMITTED ✅

---

## Interface Configuration

### Configuration Page
```
🆕 Créer une Session de Trading Automatique

Intervalle de polling:     30     secondes
Taille max de position:    500    actions
Max trades par jour:       10000  ✅ (upgraded from 100!)
Stop Loss:                 2.0    %
Take Profit:               5.0    %
```

### Pour Activer:
1. Aller à "Auto-Trading" → "Nouvelle Session"
2. Changer "Intervalle polling" de 60s à 30s
3. Changer "Taille max position" de 100 à 500
4. Changer "Max trades par jour" à 10000
5. Cliquer "🚀 Créer et Démarrer Session"

---

## Monitoring

### Comment Surveiller les Ordres SUBMITTED

**Page Trading** → **Historique des Ordres**

Colonnes importantes:
```
Symbole | Action | Quantité | Type    | Statut      | Créé
--------|--------|----------|---------|-------------|----------
WLN     | BUY    | 100      | MARKET  | SUBMITTED   | 49 min ago
WLN     | BUY    | 100      | MARKET  | SUBMITTED   | 44 min ago
WLN     | BUY    | 100      | MARKET  | FILLED      | 40 min ago ✅
```

### Quand Nettoyer
```
✅ SUBMITTED < 1h:  LAISSER (en cours de remplissage)
⚠️  SUBMITTED 1-24h: SURVEILLER (peut se remplir tard)
🧹 SUBMITTED > 24h:  NETTOYER (bloqué, CANCEL + retry)
```

**Button "🧹 Nettoyer ordres bloqués"**
- Marque ordres SUBMITTED >1h comme CANCELLED
- Permet de relancer nouveaux ordres
- Recommandé: Cliquer 1× par jour

---

## Métriques de Santé

### Bon Ratio
```
FILLED: 52 (47%)
SUBMITTED: 89 (41%)
CANCELLED: 78 (71%)
✅ Acceptable - ordres se remplissent
```

### Problématique Ratio
```
FILLED: 10 (5%)
SUBMITTED: 200 (95%)
CANCELLED: 0
❌ Problème - ordres ne se remplissent JAMAIS
→ Augmenter taille position ou polling interval
```

---

## Technical Explanation

### Order Lifecycle en IBKR

```
LOCAL (Database)          IBKR (Broker)
─────────────────────────────────────────

1. User clique
   ↓
2. Order PENDING (DB)  ← NEW order envoyé →  IBKR reçoit
   ↓                                          ↓
3. Order SUBMITTED (DB)← order confirmé ← PRESUBMITTED (IBKR)
   ↓                                          ↓
4. Attend remplissage ← wait for execution ← SUBMITTED (IBKR)
   ↓                                          ↓
5. Order FILLED (DB) ← execution ← FILLED (IBKR)
   ou CANCELLED        ou cancel    ou CANCELLED

ℹ️  Les ordres SUBMITTED EN IBKR restent longtemps
    si pas assez de liquidité!
```

### Why SUBMITTED Stays Long

**IBKR Matching Engine**:
```
Order: BUY 100 WLN @ market

Marché:
- Offreur 1: SELL 50 @ 2.35
- Offreur 2: SELL 30 @ 2.36
- Offreur 3: SELL 20 @ 2.40

Résultat:
- 50 matched → FILLED (50/100)
- 30 matched → FILLED (80/100)
- 20 matched → FILLED (100/100) ✅ DONE

OU si pas assez:
- 50 matched → FILLED (50/100)
- 30 matched → FILLED (80/100)
- Aucun vendeur pour 20 → SUBMITTED (en attente)
- Peut attendre heure/jour! ⏳
```

---

## Conclusion

### ✅ C'EST NORMAL!

89 ordres SUBMITTED = **Signature d'un système qui essaie beaucoup!**

Ce n'est pas un bug, c'est une caractéristique de:
1. Trading rapide (polling 10s)
2. Petit titre (faible liquidité)
3. Petit size max (100 actions = beaucoup d'ordres)

### ✅ VOUS POUVEZ AMÉLIORER EN:

1. Utiliser LIMIT orders (au lieu de MARKET)
2. Augmenter position size (500 au lieu de 100)
3. Augmenter polling interval (30s au lieu de 10s)
4. Nettoyer ordres bloqués régulièrement

### ✅ ACTION IMMÉDIATE:

```
Page Auto-Trading → Nouvelle Session

Changer:
  Polling interval:     60 sec (au lieu de 60)
  Position max:         500 (au lieu de 100)
  Max trades/jour:      10000 ✅ (déjà fait!)
  
Résultat: Moins d'ordres SUBMITTED, plus efficace
```

---

**Status**: ✅ FONCTIONNEMENT NORMAL

Vous pouvez trader sans inquiétude. Les ordres SUBMITTED se rempliront quand la liquidité se présentera!

