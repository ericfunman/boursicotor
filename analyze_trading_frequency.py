"""
Analyse la fréquence de trading des différentes stratégies
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from backend.config import logger
from backend.models import SessionLocal, Ticker, HistoricalData
from backend.backtesting_engine import (
    BacktestingEngine, StrategyGenerator,
    MovingAverageCrossover, RSIStrategy, MultiIndicatorStrategy,
    AdvancedMultiIndicatorStrategy, MomentumBreakoutStrategy, MeanReversionStrategy
)


def analyze_strategy_frequency(df: pd.DataFrame, strategy, strategy_name: str):
    """Analyse la fréquence de trading d'une stratégie"""
    
    print(f"\n{'='*80}")
    print(f"📊 Analyse: {strategy_name}")
    print(f"{'='*80}")
    
    # Générer les signaux
    signals = strategy.generate_signals(df)
    
    # Compter les signaux
    buy_signals = (signals == 1).sum()
    sell_signals = (signals == -1).sum()
    hold_signals = (signals == 0).sum()
    
    # Calculer le nombre de jours
    total_periods = len(df)
    duration = df.index[-1] - df.index[0]
    total_days = duration.days if duration.days > 0 else 1
    
    # Période entre chaque data point
    if len(df) > 1:
        avg_interval = (df.index[-1] - df.index[0]) / (len(df) - 1)
        periods_per_day = timedelta(days=1) / avg_interval
    else:
        periods_per_day = 1
    
    # Statistiques
    print(f"\n📈 Données:")
    print(f"  • Période: {df.index[0]} → {df.index[-1]}")
    print(f"  • Durée: {total_days} jours")
    print(f"  • Nombre de points: {total_periods}")
    print(f"  • Points par jour: {periods_per_day:.1f}")
    
    print(f"\n🎯 Signaux générés:")
    print(f"  • Achats (BUY):  {buy_signals:4d} ({buy_signals/total_periods*100:5.2f}%)")
    print(f"  • Ventes (SELL): {sell_signals:4d} ({sell_signals/total_periods*100:5.2f}%)")
    print(f"  • Attente (HOLD): {hold_signals:4d} ({hold_signals/total_periods*100:5.2f}%)")
    
    # Calculer le nombre de trades potentiels (paires achat-vente)
    potential_trades = min(buy_signals, sell_signals)
    
    print(f"\n💼 Trades potentiels:")
    print(f"  • Paires achat-vente: {potential_trades}")
    print(f"  • Par jour: {potential_trades / total_days:.2f}")
    
    # Backtest complet pour voir les trades réels
    engine = BacktestingEngine(initial_capital=10000.0)
    result = engine.run_backtest(df, strategy, "TEST")
    
    print(f"\n✅ Trades réels (backtest):")
    print(f"  • Nombre total: {result.total_trades}")
    print(f"  • Par jour: {result.total_trades / total_days:.2f}")
    print(f"  • Gagnants: {result.winning_trades} ({result.win_rate:.1f}%)")
    print(f"  • Perdants: {result.losing_trades}")
    print(f"  • Retour total: {result.total_return:.2f}%")
    
    # Analyse de la fréquence
    if result.total_trades > 0:
        avg_duration_periods = total_periods / result.total_trades
        avg_duration_days = total_days / result.total_trades
        print(f"\n⏱️  Durée moyenne par trade:")
        print(f"  • {avg_duration_periods:.1f} périodes")
        print(f"  • {avg_duration_days:.2f} jours")


def main():
    """Fonction principale"""
    
    print("\n" + "="*80)
    print("🔍 ANALYSE DE FRÉQUENCE DE TRADING - BOURSICOTOR")
    print("="*80)
    
    # Récupérer les données WLN
    db = SessionLocal()
    try:
        ticker = db.query(Ticker).filter(Ticker.symbol == 'WLN').first()
        if not ticker:
            print("❌ Ticker WLN non trouvé dans la base de données")
            return
        
        data = db.query(HistoricalData).filter(
            HistoricalData.ticker_id == ticker.id
        ).order_by(HistoricalData.timestamp).all()
        
        if len(data) < 100:
            print(f"❌ Pas assez de données ({len(data)} points)")
            return
        
        # Créer DataFrame
        df = pd.DataFrame([
            {
                'timestamp': d.timestamp,
                'open': d.open_price,
                'high': d.high_price,
                'low': d.low_price,
                'close': d.close_price,
                'volume': d.volume
            }
            for d in data
        ])
        df.set_index('timestamp', inplace=True)
        
        print(f"\n✅ Données chargées: {len(df)} points pour WLN")
        
        # Analyser différentes stratégies
        
        # 1. MA Crossover simple
        ma_strategy = MovingAverageCrossover(fast_period=10, slow_period=30)
        analyze_strategy_frequency(df, ma_strategy, "Moving Average Crossover (10/30)")
        
        # 2. RSI
        rsi_strategy = RSIStrategy(rsi_period=14, oversold=30, overbought=70)
        analyze_strategy_frequency(df, rsi_strategy, "RSI Strategy (14, 30/70)")
        
        # 3. Multi-Indicator basique
        multi_strategy = MultiIndicatorStrategy(
            ma_fast=10, ma_slow=30,
            rsi_period=14, rsi_oversold=30, rsi_overbought=70
        )
        analyze_strategy_frequency(df, multi_strategy, "Multi-Indicator Strategy (3 indicateurs)")
        
        # 4. Advanced Multi-Indicator
        advanced_strategy = AdvancedMultiIndicatorStrategy(
            ma_fast=10, ma_slow=30,
            rsi_period=14, rsi_oversold=30, rsi_overbought=70,
            bb_period=20, bb_std=2.0,
            stoch_k=14, stoch_d=3,
            min_signals=4  # Nécessite 4 indicateurs d'accord
        )
        analyze_strategy_frequency(df, advanced_strategy, "Advanced Multi-Indicator (7 indicateurs, min 4)")
        
        # 5. Momentum Breakout
        momentum_strategy = MomentumBreakoutStrategy(
            lookback_period=20,
            volume_multiplier=1.5
        )
        analyze_strategy_frequency(df, momentum_strategy, "Momentum Breakout Strategy")
        
        # 6. Mean Reversion
        mean_rev_strategy = MeanReversionStrategy(
            bb_period=20,
            bb_std=2.0,
            zscore_threshold=2.0
        )
        analyze_strategy_frequency(df, mean_rev_strategy, "Mean Reversion Strategy")
        
        # Résumé
        print(f"\n{'='*80}")
        print("📋 RÉSUMÉ")
        print(f"{'='*80}")
        print("""
💡 Observations:

1. **Fréquence de trading variable**:
   - Stratégies simples (MA, RSI): Plus de signaux, plus de trades
   - Stratégies avancées: Moins de signaux, mais plus sélectifs
   
2. **Sur données 1 minute (WLN)**:
   - Beaucoup de signaux générés (milliers)
   - Mais trades réels limités par la logique achat → vente
   - Exemple: 1000 signaux BUY + 1000 SELL = max 1000 trades réels
   
3. **Commission impact**:
   - Chaque trade coûte 0.1% × 2 (achat + vente) = 0.2%
   - Trade court (quelques minutes): Doit gagner >0.2% pour être profitable
   - Sur-trading peut tuer la performance
   
4. **Stratégies conservatrices (min_signals=4-5)**:
   - Moins de trades
   - Mais meilleure qualité (plus de confirmation)
   - Recommandé pour éviter les faux signaux

5. **500 itérations**:
   - Teste 500 STRATÉGIES différentes
   - Chaque stratégie a ses propres paramètres
   - Cherche la combinaison optimale pour vos données
        """)
        
    finally:
        db.close()


if __name__ == "__main__":
    main()
