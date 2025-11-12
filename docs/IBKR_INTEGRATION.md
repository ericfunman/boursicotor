# Guide d'intégration IBKR/Lynx

## 📋 Prérequis

### 1. Télécharger et installer IB Gateway ou TWS

**Pour Lynx (utilise l'infrastructure IBKR):**
- Télécharger IB Gateway: https://www.interactivebrokers.com/en/trading/ibgateway-stable.php
- OU TWS (Trader Workstation): https://www.interactivebrokers.com/en/trading/tws.php

**Recommandation**: IB Gateway est plus léger (pas d'interface graphique)

### 2. Configuration de TWS/IB Gateway

#### Activer l'API:
1. Lancer TWS ou IB Gateway
2. Aller dans **Configuration > API > Settings**
3. Cocher **"Enable ActiveX and Socket Clients"**
4. Noter le **Socket Port** (par défaut: 7496 pour live, 7497 pour paper)
5. Décocher **"Read-Only API"**
6. Pour localhost: cocher **"Allow connections from localhost only"**

#### Configuration recommandée:
- **Lock and Exit**: Choisir "Never lock Trader Workstation" et "Auto restart"
- **API Precautions**: Cocher "Bypass Order Precautions for API orders"
- **Logging**: Activer "Create API message log file" pour le debug

## 🔧 Utilisation du connecteur IBKR

### Connexion basique

```python
from backend.ibkr_connector import IBKRConnector

# Créer le connecteur
connector = IBKRConnector(
    host='127.0.0.1',
    port=7497,  # 7497 = paper trading, 7496 = live trading
    client_id=1
)

# Se connecter
if connector.connect():
    print("Connecté à IBKR!")
    
    # ... faire des opérations ...
    
    connector.disconnect()
```

### Récupérer des données de marché en temps réel

```python
# Créer un contrat pour une action européenne
contract = connector.create_contract(
    symbol='AIR',      # Airbus
    sec_type='STK',    # Stock
    exchange='SMART',  # Smart routing
    currency='EUR'
)

# Récupérer les données de marché
market_data = connector.get_market_data(contract)

if market_data:
    print(f"Prix bid: {market_data.get('bid')}")
    print(f"Prix ask: {market_data.get('ask')}")
    print(f"Dernier prix: {market_data.get('last')}")
    print(f"Volume: {market_data.get('volume')}")
```

### Récupérer des données historiques

```python
# Récupérer 1 mois de données journalières
hist_data = connector.get_historical_data(
    contract=contract,
    duration='1 M',      # 1 mois
    bar_size='1 day',    # Barres journalières
    what_to_show='TRADES'
)

if hist_data is not None:
    print(hist_data.head())
    # DataFrame avec colonnes: open, high, low, close, volume
```

### Paramètres disponibles

#### Duration (durée):
- `'1 D'` = 1 jour
- `'1 W'` = 1 semaine  
- `'1 M'` = 1 mois
- `'1 Y'` = 1 an
- `'2 Y'` = 2 ans (max pour certains instruments)

#### Bar Size (taille des barres):
- `'1 sec'`, `'5 secs'`, `'10 secs'`, `'15 secs'`, `'30 secs'`
- `'1 min'`, `'2 mins'`, `'3 mins'`, `'5 mins'`, `'10 mins'`, `'15 mins'`, `'20 mins'`, `'30 mins'`
- `'1 hour'`, `'2 hours'`, `'3 hours'`, `'4 hours'`, `'8 hours'`
- `'1 day'`, `'1 week'`, `'1 month'`

#### What to Show:
- `'TRADES'` = Prix des transactions
- `'MIDPOINT'` = Point milieu bid/ask
- `'BID'` = Prix bid
- `'ASK'` = Prix ask
- `'BID_ASK'` = Bid et Ask
- `'HISTORICAL_VOLATILITY'` = Volatilité historique
- `'OPTION_IMPLIED_VOLATILITY'` = Volatilité implicite

### Rechercher un symbole

```python
# Trouver tous les contrats correspondant au symbole
details = connector.search_contract('AIR', 'STK')

for detail in details:
    contract = detail.contract
    print(f"Symbole: {contract.symbol}")
    print(f"Exchange: {contract.exchange}")
    print(f"Devise: {contract.currency}")
    print(f"ConId: {contract.conId}")
```

## 🔗 Intégration avec Boursicotor

### Modifier data_collector.py

Ajoutez IBKR comme nouvelle source de données:

```python
from backend.ibkr_connector import IBKRConnector

class DataCollector:
    def __init__(self, use_ibkr=True):
        # ... code existant ...
        self.use_ibkr = use_ibkr
        self.ibkr_connector = None
        
        if use_ibkr:
            self._init_ibkr()
    
    def _init_ibkr(self):
        """Initialise IBKR"""
        try:
            self.ibkr_connector = IBKRConnector()
            if not self.ibkr_connector.connect():
                print("⚠️ Impossible de se connecter à IBKR")
                self.ibkr_connector = None
        except Exception as e:
            print(f"❌ Erreur IBKR: {e}")
            self.ibkr_connector = None
    
    def _get_ibkr_data(self, symbol, period, interval):
        """Récupère les données depuis IBKR"""
        if not self.ibkr_connector:
            return None
        
        try:
            # Créer le contrat
            contract = self.ibkr_connector.create_contract(
                symbol=symbol,
                sec_type='STK',
                exchange='SMART',
                currency='EUR'
            )
            
            # Mapper la période
            duration_map = {
                '1D': '1 D',
                '5D': '5 D',
                '1M': '1 M',
                '6M': '6 M',
                '1Y': '1 Y'
            }
            
            # Mapper l'intervalle
            bar_size_map = {
                '1m': '1 min',
                '5m': '5 mins',
                '1h': '1 hour',
                '1d': '1 day'
            }
            
            # Récupérer les données
            df = self.ibkr_connector.get_historical_data(
                contract=contract,
                duration=duration_map.get(period, '1 M'),
                bar_size=bar_size_map.get(interval, '1 day'),
                what_to_show='TRADES'
            )
            
            if df is not None and not df.empty:
                print(f"✅ IBKR: {len(df)} barres récupérées")
                return df
            
        except Exception as e:
            print(f"❌ Erreur IBKR pour {symbol}: {e}")
        
        return None
```

## 🐛 Dépannage

### Erreur 502: "Couldn't connect to TWS"
- **Solution**: Vérifiez que TWS/IB Gateway est lancé et que l'API est activée

### Erreur 200: "No security definition found"
- **Solution**: Le symbole n'existe pas ou le type de sécurité est incorrect

### Pas de données historiques
- **Solution**: Vérifiez que vous avez les abonnements de données nécessaires

### "Permission denied"
- **Solution**: Vérifiez les permissions de votre compte (paper vs live)

## 📝 Codes d'erreur courants

| Code | Signification |
|------|---------------|
| 502  | Impossible de se connecter à TWS |
| 200  | Aucune définition de sécurité trouvée |
| 354  | Données de marché non souscrites |
| 2104 | Connexion OK (info, pas une erreur) |
| 2106 | Données historiques OK (info) |

## 🔐 Sécurité

- Utilisez toujours le **paper trading** (port 7497) pour les tests
- Ne commitez JAMAIS vos identifiants dans Git
- Pour le live trading (port 7496), utilisez des variables d'environnement

## 📚 Ressources

- Documentation officielle: https://interactivebrokers.github.io/tws-api/
- Forum IBKR: https://www.interactivebrokers.com/en/support/api.php
- Guide Python: https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-doc/
