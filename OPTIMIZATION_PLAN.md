# Optimisation du Backtesting - Plan d'implémentation

## Objectif
Réduire le temps d'exécution de 2000 itérations de backtesting de **2-4 heures** à **10-15 minutes**.

## Optimisations implémentées

### 1. Parallélisation avec multiprocessing ⭐⭐⭐⭐⭐
- Utilisation de `multiprocessing.Pool` pour distribuer les backtests
- Nombre de workers = nombre de cœurs CPU (typiquement 4-8)
- Gain estimé : **6-8x plus rapide**

### 2. Pré-calcul des indicateurs de base ⭐⭐⭐
- Calcul unique des SMA standards (5, 10, 20, 50, 100, 200)
- Calcul unique des RSI standards (14)
- Réutilisation dans toutes les itérations
- Gain estimé : **2-3x plus rapide**

### 3. Vectorisation et optimisations pandas ⭐⭐
- Remplacement des boucles par opérations vectorisées
- Utilisation de numpy pour calculs intensifs
- Gain estimé : **1.5-2x plus rapide**

## Gain total estimé
**15-20x plus rapide** = de 2-4h à 10-15 minutes

## Implémentation
1. Nouvelle fonction `run_parallel_optimization()` dans `backtesting_engine.py`
2. Fonction worker `_run_single_backtest_worker()` pour multiprocessing
3. Fonction `_precalculate_indicators()` pour pré-calculs
4. Mise à jour de l'interface Streamlit pour utiliser la nouvelle fonction

## Compatibilité
- ✅ Conserve l'ancienne fonction pour compatibilité
- ✅ Ajoute option "Mode parallèle" dans l'interface
- ✅ Pas de breaking changes
