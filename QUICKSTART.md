# 🚀 Démarrage Rapide - Boursicotor

Guide ultra-rapide pour démarrer avec Boursicotor.

## ⚡ Installation Express (5 minutes)

### 1. Prérequis
- Python 3.10+ installé
- PostgreSQL installé
- Compte IBKR créé (ou simulé pour les tests)

### 2. Configuration rapide

```bash
# 1. Créer l'environnement virtuel
python -m venv venv
.\venv\Scripts\activate

# 2. Installer les dépendances (sans TA-Lib pour commencer)
pip install streamlit pandas numpy sqlalchemy psycopg2-binary ib-insync plotly python-dotenv loguru scikit-learn xgboost pandas-ta

# 3. Configurer PostgreSQL
# Dans psql ou pgAdmin :
# CREATE DATABASE boursicotor;

# 4. Copier et configurer .env
copy .env.example .env
# Éditer .env avec vos paramètres

# 5. Initialiser la base de données
python database\init_db.py

# 6. Lancer l'application
streamlit run frontend\app.py
```

## 🎯 Workflow Recommandé

### Phase 1 : Configuration et Collecte (Jour 1)
```
1. Démarrer TWS/IB Gateway en mode paper trading
2. Lancer Boursicotor
3. Se connecter à IBKR depuis l'app
4. Collecter des données pour TTE et WLN (5 jours, 5 min)
```

### Phase 2 : Analyse Technique (Jour 2-3)
```
1. Visualiser les données collectées
2. Explorer les indicateurs techniques
3. Observer les patterns dans l'onglet "Analyse Technique"
```

### Phase 3 : Backtesting (Jour 4-7)
```
1. Tester la stratégie RSI Momentum
2. Tester la stratégie MA Crossover
3. Comparer les performances
4. Ajuster les paramètres
```

### Phase 4 : Machine Learning (Semaine 2)
```
1. Collecter plus de données (3-6 mois)
2. Entraîner le modèle ML
3. Évaluer les prédictions
4. Backtester avec le modèle ML
```

### Phase 5 : Paper Trading (Semaine 3+)
```
1. Activer le mode paper trading automatique
2. Laisser tourner quelques jours
3. Analyser les résultats
4. Ajuster la stratégie
```

### Phase 6 : Trading Réel (Semaine 4+)
```
⚠️ ATTENTION : Seulement après validation complète en paper trading
1. Commencer avec un petit capital
2. Limiter le risque à 1-2% par trade
3. Surveiller étroitement les premières semaines
```

## 📊 Exemples d'Utilisation

### Collecter des données via code Python

```python
from backend.data_collector import DataCollector

collector = DataCollector()

# Collecter 1 mois de données en 5 minutes pour TTE
collector.collect_historical_data(
    symbol="TTE",
    name="TotalEnergies",
    duration="1 M",
    bar_size="5 mins"
)

# Récupérer les données
df = collector.get_latest_data("TTE", limit=1000)
print(df.head())
```

### Calculer des indicateurs techniques

```python
from backend.data_collector import DataCollector
from backend.technical_indicators import calculate_and_update_indicators

collector = DataCollector()
df = collector.get_latest_data("TTE", limit=500)

# Ajouter tous les indicateurs
df = calculate_and_update_indicators(df)

print("Indicateurs disponibles:", df.columns.tolist())
print("\nDernières valeurs:")
print(df[['close', 'rsi_14', 'macd', 'sma_20']].tail())
```

### Tester une stratégie en backtesting

```python
from backend.data_collector import DataCollector
from backend.technical_indicators import calculate_and_update_indicators
from backtesting.engine import BacktestEngine, BacktestConfig
from strategies.base_strategies import get_strategy

# Récupérer les données
collector = DataCollector()
df = collector.get_latest_data("TTE", limit=1000)
df = calculate_and_update_indicators(df)

# Créer la stratégie
strategy = get_strategy('momentum', rsi_oversold=30, rsi_overbought=70)

# Configurer le backtest
config = BacktestConfig(
    initial_capital=10000.0,
    commission=0.001,
    risk_per_trade=0.02
)

# Exécuter le backtest
engine = BacktestEngine(config)
results = engine.run_backtest(
    df=df,
    strategy_func=strategy.generate_signal,
    symbol="TTE"
)

# Afficher les résultats
print(f"Return Total: {results['total_return']:.2f}%")
print(f"Nombre de Trades: {results['total_trades']}")
print(f"Win Rate: {results['win_rate']:.2f}%")
print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {results['max_drawdown']:.2f}%")
```

### Entraîner un modèle ML

```python
from backend.data_collector import DataCollector
from backend.technical_indicators import calculate_and_update_indicators
from ml_models.pattern_detector import MLPatternDetector

# Récupérer beaucoup de données
collector = DataCollector()
df = collector.get_latest_data("TTE", limit=5000)
df = calculate_and_update_indicators(df)

# Entraîner le modèle
detector = MLPatternDetector(model_type="random_forest")
results = detector.train(
    df=df,
    forward_periods=10,  # Prédire 10 périodes à l'avance
    threshold=0.02,      # 2% de gain minimum
    test_size=0.2
)

print(f"Accuracy: {results['test_accuracy']:.3f}")
print(f"Precision: {results['precision']:.3f}")
print(f"F1 Score: {results['f1_score']:.3f}")

# Sauvegarder le modèle
detector.save("tte_model_v1.pkl")

# Plus tard, charger et utiliser
detector_new = MLPatternDetector()
detector_new.load("tte_model_v1.pkl")
predictions = detector_new.predict(df.tail(100))
print("Prédictions:", predictions)
```

## 🔧 Configuration Recommandée

### Pour débutants
```env
PAPER_TRADING=True
MAX_POSITION_SIZE=5000
RISK_PER_TRADE=0.01  # 1%
STOP_LOSS_PERCENT=0.03  # 3%
```

### Pour intermédiaires
```env
PAPER_TRADING=True
MAX_POSITION_SIZE=10000
RISK_PER_TRADE=0.02  # 2%
STOP_LOSS_PERCENT=0.05  # 5%
```

### Pour avancés (après validation)
```env
PAPER_TRADING=False  # Trading réel
MAX_POSITION_SIZE=20000
RISK_PER_TRADE=0.02  # 2%
STOP_LOSS_PERCENT=0.05  # 5%
```

## 📈 Stratégies Disponibles

1. **momentum** - RSI Momentum
   - Achète quand RSI < 30 (survendu)
   - Vend quand RSI > 70 (suracheté)

2. **ma_crossover** - Croisement de moyennes mobiles
   - Achète sur golden cross (MA rapide > MA lente)
   - Vend sur death cross (MA rapide < MA lente)

3. **macd** - MACD Crossover
   - Achète quand MACD croise au-dessus du signal
   - Vend quand MACD croise en-dessous du signal

4. **bollinger_bands** - Bandes de Bollinger
   - Achète sur bande basse (mean reversion)
   - Vend sur bande haute ou milieu

5. **multi_indicator** - Multi-indicateurs
   - Combine RSI, MACD et moyennes mobiles
   - Signal seulement si majorité d'accord

6. **trend_following** - Suivi de tendance
   - Utilise ADX pour détecter les tendances fortes
   - Trade avec EMA en tendance confirmée

7. **mean_reversion** - Retour à la moyenne
   - Combine Bollinger Bands et RSI
   - Nécessite confirmation multiple

## ⚠️ Checklist Avant Trading Réel

- [ ] Au moins 100 heures de backtesting réalisées
- [ ] Win rate > 55% sur données historiques
- [ ] Sharpe ratio > 1.0
- [ ] Max drawdown < 20%
- [ ] Au moins 30 jours de paper trading réussi
- [ ] Stratégie de gestion du risque définie
- [ ] Capital que vous pouvez vous permettre de perdre
- [ ] Compréhension complète de la stratégie
- [ ] Règles d'entrée/sortie claires
- [ ] Plan pour différents scénarios de marché

## 🆘 Problèmes Courants

### "No data fetched"
- Vérifiez la connexion IBKR
- Vérifiez que le ticker est correct (TTE, WLN, etc.)
- Vérifiez les heures de marché

### "Database connection failed"
- PostgreSQL est-il démarré ?
- Les credentials dans .env sont-ils corrects ?
- La base de données existe-t-elle ?

### "Model not trained"
- Vous devez d'abord entraîner le modèle avec `detector.train()`
- Ou charger un modèle existant avec `detector.load()`

### "Insufficient data"
- Collectez plus de données historiques
- Au moins 100 barres pour les indicateurs
- Au moins 500 barres pour le ML

## 📚 Ressources

- Documentation IBKR API : https://interactivebrokers.github.io/
- Analyse technique : https://www.investopedia.com/technical-analysis-4689657
- Machine Learning en finance : https://www.quantstart.com/

---

**Bon trading et soyez prudents ! 📈**
