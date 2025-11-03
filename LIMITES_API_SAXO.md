# 📊 Limites de l'API Saxo Bank

## Limite de Points par Requête

### ⚠️ Limite Actuelle : **1200 points maximum**

Cette limite est imposée par l'API Saxo Bank et **n'est pas configurable**. Elle s'applique à toutes les requêtes de données historiques (Chart API).

## Pourquoi cette limite ?

L'API Saxo Bank impose des limitations pour :
1. **Performance des serveurs** - Éviter les requêtes trop lourdes
2. **Rate limiting** - Protéger l'API contre les abus
3. **Équité d'accès** - Assurer un service équitable pour tous les utilisateurs

## Impact sur la Collecte de Données

### Exemples de Limitations

| Durée | Intervalle | Points Calculés | Points Reçus | Note |
|-------|-----------|-----------------|--------------|------|
| 1 heure | 1 seconde | 3,600 | **1,200** | ⚠️ Limité |
| 1 jour | 1 seconde | 86,400 | **1,200** | ⚠️ Limité |
| 1 heure | 5 secondes | 720 | 720 | ✅ OK |
| 1 jour | 1 minute | 1,440 | **1,200** | ⚠️ Limité |
| 1 semaine | 5 minutes | 2,016 | **1,200** | ⚠️ Limité |
| 1 mois | 1 heure | 720 | 720 | ✅ OK |
| 1 an | 1 jour | ~250 | 250 | ✅ OK |

### 🔍 Calcul du Nombre de Points

```python
# Formule simplifiée
points = durée_en_minutes / intervalle_en_minutes

# Exemple 1 : 1 heure avec intervalle de 1 seconde
points = (60 minutes × 60 secondes) / 1 seconde = 3,600 points
→ Limité à 1,200 points ⚠️

# Exemple 2 : 1 mois avec intervalle de 1 heure  
points = (30 jours × 24 heures) / 1 heure = 720 points
→ Pas de limitation ✅
```

## Solutions de Contournement

### 1. Ajuster Durée/Intervalle

Pour collecter plus de données, **ajustez la combinaison durée/intervalle** :

#### ❌ Mauvais (limité à 1200)
```
Durée: 1 jour
Intervalle: 1 seconde
→ 86,400 points demandés → 1,200 reçus
```

#### ✅ Bon (pas de limite)
```
Durée: 1 heure
Intervalle: 3 secondes
→ 1,200 points demandés → 1,200 reçus
```

### 2. Requêtes Multiples

Pour obtenir plus de données historiques, faites **plusieurs requêtes successives** :

```python
# Exemple : Collecter 3 jours avec intervalle de 1 minute
# Au lieu de 1 requête de 3 jours (4,320 points → limité à 1,200)
# Faire 3 requêtes de 1 jour (1,440 points chacune)

for day in range(3):
    collector.collect_historical_data(
        symbol="GLE",
        duration="1D",
        bar_size="1min"
    )
```

### 3. Intervalles Adaptés

Choisissez l'intervalle en fonction de vos besoins :

| Usage | Durée Recommandée | Intervalle Recommandé |
|-------|-------------------|----------------------|
| **Trading Haute Fréquence** | 1 heure | 3 secondes |
| **Day Trading** | 1 jour | 1 minute |
| **Swing Trading** | 1 semaine | 5 minutes |
| **Analyse Moyen Terme** | 1 mois | 1 heure |
| **Analyse Long Terme** | 1 an | 1 jour |

## Mode Simulation

En mode simulation (utilisé actuellement), des données **simulées réalistes** sont générées lorsque :
- L'API Chart retourne une erreur 404
- La requête échoue

Ces données simulées :
- ✅ Sont basées sur le **prix réel actuel** (via InfoPrices API)
- ✅ Utilisent une **volatilité réaliste** (0.2% par bar)
- ✅ Génèrent OHLCV complets (Open, High, Low, Close, Volume)
- ✅ Respectent la limite de 1,200 points

## Autres Limites de l'API Saxo

### Rate Limiting
- **Requêtes par minute** : Non documenté officiellement
- **Solution** : Délai de 1 seconde entre requêtes (configurable dans Paramètres)

### Timeout
- **Timeout par défaut** : 30 secondes
- **Solution** : Le client gère automatiquement les timeouts

### Endpoints Disponibles

En mode **Simulation** (actuellement utilisé) :
- ✅ `/ref/v1/instruments` - Recherche d'instruments
- ✅ `/trade/v1/infoprices` - Prix en temps réel
- ❌ `/chart/v1/charts` - **Non disponible** (d'où les données simulées)

En mode **Production** (avec compte réel) :
- ✅ Tous les endpoints disponibles
- ✅ Données historiques réelles via Chart API

## Recommandations

### Pour Maximiser les Données

1. **Utilisez des intervalles plus larges** pour des durées longues
   ```
   ✅ 1 an + 1 jour = 250 points
   ❌ 1 an + 1 heure = limité à 1,200 points
   ```

2. **Fragmentez les requêtes** pour les analyses détaillées
   ```
   Au lieu de : 1 semaine + 1 seconde
   Faire : 7 × (1 jour + 1 seconde)
   ```

3. **Privilégiez la qualité à la quantité**
   ```
   1,200 points bien espacés > 10,000 points redondants
   ```

### Pour l'Analyse Technique

La plupart des indicateurs techniques fonctionnent bien avec **100-200 points** :
- RSI : 14-30 points minimum
- MACD : 26-50 points minimum
- Bollinger Bands : 20-50 points minimum
- SMA/EMA : Selon la période

**1,200 points sont largement suffisants** pour l'analyse technique ! 📈

## Configuration Actuelle

Dans **Boursicotor v2.0.0** :
- ✅ Limite codée en dur : **1,200 points**
- ✅ Information visible dans les Paramètres
- ✅ Documentation complète
- ✅ Fallback automatique sur données simulées

## Documentation Officielle

Pour plus d'informations :
- [Saxo OpenAPI - Chart](https://www.developer.saxo/openapi/referencedocs/chart/v1/charts)
- [Saxo OpenAPI - Rate Limits](https://www.developer.saxo/openapi/learn/rate-limiting)
- [Saxo Developer Portal](https://www.developer.saxo/)

## Résumé

| Aspect | Valeur |
|--------|--------|
| **Limite maximale** | 1,200 points |
| **Configurable ?** | ❌ Non |
| **Contournable ?** | ✅ Oui (requêtes multiples) |
| **Impact sur l'analyse ?** | ✅ Minimal (1,200 points suffisent) |
| **Solution Boursicotor** | ✅ Données simulées en fallback |

---

**Dernière mise à jour** : 21 octobre 2025  
**Version Boursicotor** : 2.0.0
