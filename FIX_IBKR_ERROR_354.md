# Fix pour IBKR Error 354 - Delayed Data Not Available

## Le Problème

Vous recevez cette erreur lors de la demande de données en direct (live prices) :
```
Error 354: Vous n'êtes pas abonné à ces données de marché.
Des données de marché en différé sont disponibles.
contract: Stock(..., exchange='SMART', ...)
```

## Analyse du Problème

1. **L'erreur 354 signifie que vous avez l'accès gratuit (delayed data) mais PAS les données en temps réel**
2. **IMPORTANT**: Quand ib_insync qualifie un contract, il le change de `SBF` en `SMART`
3. **Le problème**: IBKR refuse de donner les données retardées sur `SMART` pour WLN, même si elles sont disponibles sur `SBF`

## La Solution

### Changement 1: Amélioration du `get_contract()`

**Fichier**: `backend/ibkr_collector.py`

Le `get_contract()` essaie maintenant `SBF` d'abord pour les stocks EUR, puis `SMART` en fallback:

```python
def get_contract(self, symbol: str, exchange: str = 'SMART', currency: str = 'EUR'):
    exchanges_to_try = []
    if exchange == 'SMART' and currency == 'EUR':
        exchanges_to_try = ['SBF', 'SMART']  # SBF d'abord pour Euronext
    else:
        exchanges_to_try = [exchange]
    
    for ex in exchanges_to_try:
        try:
            contract = Stock(symbol, ex, currency)
            contracts = self.ib.qualifyContracts(contract)
            if contracts:
                return contracts[0]
        except:
            continue
```

### Changement 2: Meilleure gestion dans `live_data_task.py`

**Fichier**: `backend/live_data_task.py`

- ✅ Attente plus longue (7.5 secondes au lieu de 5)
- ✅ Messages de debug améliorés
- ✅ Tracking de `last_price` pour éviter les doublons
- ✅ Meilleur logging des champs disponibles

### Changement 3: UI améliorée

**Fichier**: `frontend/app.py` (live_prices_page)

- ✅ Attente augmentée à 2 secondes
- ✅ Fallback sur `close` si `last` n'est pas disponible
- ✅ Meilleurs logs

## Comportement Attendu

Quand vous cliquez "Démarrer" dans "Cours en direct":

1. ✅ Le contract est qualifié sur `SBF` (pas `SMART`)
2. ✅ Les données retardées arrivent après 2-5 secondes
3. ✅ Le prix s'affiche avec les champs disponibles
4. ✅ Le graphique se remplit progressivement

**Note**: Les données seront retardées de 15-20 minutes (limite IBKR free-tier)

## Debugging

Si ça continue de ne pas marcher:

### Test 1: Vérifier le contract qualifié
```bash
python test_contract_sbf.py
```

Doit afficher:
```
Exchange: SBF  (pas SMART)
Primary Exchange: SBF
```

### Test 2: Tester les données retardées
```bash
python test_delayed_detailed.py
```

Doit afficher un des ces champs après 2-5 secondes:
```
Last:     53.49 ✅
Close:    53.5 ✅
```

### Test 3: Logs Celery

Vérifiez les logs Celery lors du lancement live prices. Cherchez:

```
✅ Got data for WLN after 2.5s
```

ou

```
⚠️ No data received after 7.5s for WLN (delayed data may be unavailable)
```

## Limitations Connues

1. **Données retardées**: 15-20 minutes de retard (limite gratuit IBKR)
2. **Certains champs peuvent être 0**: En fonction de ce que IBKR envoie
3. **Error 354 peut récidiver**: Si contract.exchange revient à SMART après qualification

## Solutions Avancées (Si ça continue de ne pas marcher)

### Option 1: Utiliser le prix du portefeuille

Si vous avez la position en portefeuille (ce qui est le cas pour WLN avec 110 actions), on peut utiliser `updatePortfolio` comme source de prix en temps réel au lieu de `reqMktData`.

### Option 2: Demander un abonnement IBKR

Pour avoir les données vraiment en direct (pas retardées), il faut s'abonner aux données IBKR (payant ~10$/mois pour Euronext).

### Option 3: Yahoo Finance comme fallback

Utiliser Yahoo Finance pour les données en direct si IBKR échoue (implémentation possible).

## Fichiers Modifiés

- `backend/ibkr_collector.py` - Amélioration `get_contract()` avec priorité SBF
- `backend/live_data_task.py` - Meilleure gestion delayed data, meilleur logging
- `frontend/app.py` - UI améliorée pour delayed data
- `IBKR_DELAYED_DATA_FIX.md` - Doc précédente sur delayed data (toujours valide)
