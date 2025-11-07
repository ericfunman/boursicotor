# Système de Passage d'Ordres - Guide Utilisateur

## 🎯 Vue d'ensemble

Le système de passage d'ordres permet de **créer, suivre et gérer** des ordres de trading sur Interactive Brokers (IBKR) depuis l'interface Boursicotor.

## 📋 Prérequis

### 1. Configuration IBKR
- **IB Gateway** ou **TWS** en cours d'exécution
- **API activée** : Configuration → API → Settings → "Enable ActiveX and Socket Clients"
- **Port** : 4002 (paper trading) ou 7497 (live trading)
- **IP autorisée** : Ajoutez `127.0.0.1` dans "Trusted IPs"

### 2. Configuration Boursicotor
- Base de données initialisée
- Table `orders` créée (via migration)
- Connexion IBKR active dans l'application

## 🚀 Utilisation

### Accès
Depuis la sidebar → **📝 Passage d'Ordres**

### 4 Onglets Disponibles

#### 1️⃣ Nouvel Ordre
**Créer un ordre de trading**

**Champs requis :**
- **Action** : Sélection depuis la base de données ou saisie manuelle
- **Action** : BUY (acheter) ou SELL (vendre)
- **Quantité** : Nombre d'actions
- **Type d'ordre** :
  - `MARKET` : Exécution immédiate au prix du marché
  - `LIMIT` : Exécution au prix limite ou mieux
  - `STOP` : Stop-loss (devient MARKET si prix atteint)
  - `STOP_LIMIT` : Combinaison stop + limite

**Champs optionnels :**
- **Prix Limite** : Pour ordres LIMIT/STOP_LIMIT
- **Prix Stop** : Pour ordres STOP/STOP_LIMIT
- **Stratégie** : Associer à une stratégie existante
- **Notes** : Commentaires personnels
- **Mode Simulation** : Paper trading (coché) ou argent réel (décoché)

**Action :**
- Cliquez sur **📤 Envoyer l'Ordre**
- L'ordre est enregistré en base ET envoyé à IBKR (si connecté)
- Un ID d'ordre est généré

#### 2️⃣ Ordres en Cours
**Surveiller les ordres actifs**

**Affichage :**
- Tableau des ordres PENDING et SUBMITTED
- Informations : ID, symbole, type, quantité, prix, statut
- Mise à jour en temps réel

**Actions :**
- **🔄 Rafraîchir** : Recharger la page
- **🔄 Sync IBKR** : Synchroniser avec IBKR
- **❌ Annuler** : Annuler un ordre par son ID

#### 3️⃣ Historique
**Consulter tous les ordres passés**

**Filtres :**
- Par symbole (ex: WLN)
- Par statut (FILLED, CANCELLED, etc.)
- Limite de résultats (10-500)

**Affichage :**
- Date, symbole, action, type
- Quantité, quantité remplie, prix moyen
- Commission, statut, stratégie
- Mode paper/réel

**Export :**
- **📥 Télécharger CSV** : Export complet de l'historique

#### 4️⃣ Statistiques
**Analytics et métriques**

**Statistiques globales :**
- Total ordres créés
- Nombre d'ordres exécutés
- Ordres en cours
- Taux d'exécution (%)
- Volume total tradé
- Commissions totales

**Statistiques par action :**
- Répartition par symbole
- Taux de remplissage
- Volume par ticker

## ⚙️ Backend - OrderManager

### Fonctionnalités principales

```python
from backend.order_manager import OrderManager

# Initialiser
order_manager = OrderManager(ibkr_collector)

# Créer un ordre
order = order_manager.create_order(
    symbol="WLN",
    action="BUY",
    quantity=10,
    order_type="LIMIT",
    limit_price=12.50,
    is_paper_trade=True
)

# Annuler un ordre
order_manager.cancel_order(order_id=123)

# Récupérer les ordres
orders = order_manager.get_orders(ticker_symbol="WLN", status=OrderStatus.FILLED)

# Synchroniser avec IBKR
count = order_manager.sync_with_ibkr()

# Statistiques
stats = order_manager.get_order_statistics()
```

## 📊 Modèle de Données

### Table `orders`

| Champ | Type | Description |
|-------|------|-------------|
| id | Integer | ID unique (clé primaire) |
| ibkr_order_id | Integer | ID IBKR (unique) |
| ticker_id | Integer | Référence à la table tickers |
| strategy_id | Integer | Référence à la table strategies (optionnel) |
| action | String | BUY ou SELL |
| order_type | String | MARKET, LIMIT, STOP, STOP_LIMIT |
| quantity | Integer | Nombre d'actions |
| limit_price | Float | Prix limite (optionnel) |
| stop_price | Float | Prix stop (optionnel) |
| filled_quantity | Integer | Quantité exécutée |
| avg_fill_price | Float | Prix moyen d'exécution |
| commission | Float | Commissions payées |
| status | Enum | PENDING, SUBMITTED, FILLED, CANCELLED, etc. |
| is_paper_trade | Boolean | Mode simulation |
| created_at | DateTime | Date de création |
| submitted_at | DateTime | Date de soumission à IBKR |
| filled_at | DateTime | Date d'exécution |

### Statuts disponibles

| Statut | Description |
|--------|-------------|
| PENDING | Ordre créé, pas encore soumis |
| SUBMITTED | Envoyé à IBKR, en attente d'exécution |
| FILLED | Entièrement exécuté |
| PARTIALLY_FILLED | Partiellement exécuté |
| CANCELLED | Annulé par l'utilisateur |
| REJECTED | Rejeté par IBKR |
| ERROR | Erreur lors de la soumission |

## 🔒 Sécurité

### Paper Trading
- Par défaut, tous les ordres sont en **mode simulation**
- Utilisent de l'argent fictif
- Utile pour tester sans risque

### Trading Réel
⚠️ **ATTENTION** : Décocher "Mode Simulation" utilise de l'argent réel !

**Précautions :**
1. Vérifier le compte IBKR (paper vs live)
2. Vérifier le port de connexion (4002 vs 7497)
3. Commencer avec de petites quantités
4. Tester en paper trading d'abord

## 🐛 Troubleshooting

### Ordre non envoyé à IBKR
- **Problème** : Ordre enregistré mais statut PENDING
- **Cause** : IBKR non connecté
- **Solution** : Vérifier la connexion dans la sidebar

### Ordre rejeté
- **Causes possibles** :
  - Fonds insuffisants
  - Prix limite invalide
  - Action non tradable
  - Heures de marché fermées
- **Solution** : Vérifier le status_message de l'ordre

### Synchronisation échouée
- **Problème** : Sync IBKR ne met pas à jour
- **Cause** : Perte de connexion temporaire
- **Solution** : Reconnecter IBKR et réessayer

## 📈 Exemples d'utilisation

### Ordre Market simple
```
Action: WLN
Action: BUY
Quantité: 10
Type: MARKET
Mode Simulation: ✅
```

### Ordre Limit avec stop-loss
```
Action: TTE
Action: BUY
Quantité: 50
Type: LIMIT
Prix Limite: 65.00 €
Mode Simulation: ✅
Notes: "Entrée sur support"
```

### Short avec stop-limit
```
Action: GLE
Action: SELL
Quantité: 20
Type: STOP_LIMIT
Prix Stop: 58.00 €
Prix Limite: 57.50 €
Mode Simulation: ✅
Notes: "Short sur résistance"
```

## 🔄 Workflow recommandé

1. **Préparation**
   - Analyser l'action (Analyse Technique)
   - Backtester la stratégie (Backtesting)
   - Définir les niveaux (stop-loss, take-profit)

2. **Passage d'ordre**
   - Créer l'ordre en mode simulation
   - Vérifier la confirmation
   - Surveiller dans "Ordres en Cours"

3. **Suivi**
   - Synchroniser régulièrement avec IBKR
   - Vérifier l'exécution
   - Consulter l'historique

4. **Analyse**
   - Examiner les statistiques
   - Calculer le taux de remplissage
   - Optimiser les paramètres

## 📝 Notes importantes

- Les ordres sont **persistés en base de données**
- L'historique est **conservé indéfiniment**
- Les **commissions IBKR** sont automatiquement enregistrées
- Le système supporte les **ordres bracket** (parent/child)
- Tous les ordres sont **horodatés UTC**

## 🚀 Prochaines fonctionnalités

- [ ] Ordres OCO (One-Cancels-Other)
- [ ] Ordres bracket automatiques
- [ ] Trailing stop
- [ ] Alertes email/Telegram sur exécution
- [ ] Graphiques de performance
- [ ] Calcul automatique du P&L
- [ ] Position tracking intégré
- [ ] Risk management automatique

---

**Version** : 1.0.0  
**Date** : 2025-11-04  
**Auteur** : Boursicotor Team
