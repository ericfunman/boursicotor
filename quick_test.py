"""
Script de test rapide pour optimisation
50 itérations pour tester rapidement
"""
import sys
import pandas as pd
from datetime import datetime
from backend.config import logger
from backend.models import SessionLocal, Ticker, HistoricalData
from backend.backtesting_engine import StrategyGenerator, BacktestingEngine
import logging

# DÉSACTIVER LES LOGS DEBUG POUR ACCÉLÉRER
logging.getLogger('backend.backtesting_engine').setLevel(logging.INFO)

def quick_test(iterations=50):
    """Test rapide avec 50 itérations"""
    print(f"\n{'='*80}")
    print(f"🚀 TEST RAPIDE - {iterations} itérations")
    print(f"{'='*80}\n")
    
    # Charger les données WLN
    db = SessionLocal()
    try:
        ticker = db.query(Ticker).filter(Ticker.symbol == "WLN").first()
        if not ticker:
            print("❌ Ticker WLN non trouvé")
            return None, None
        
        data = db.query(HistoricalData).filter(
            HistoricalData.ticker_id == ticker.id
        ).order_by(HistoricalData.timestamp.asc()).all()
        
        if len(data) < 100:
            print(f"❌ Pas assez de données ({len(data)} points)")
            return None, None
        
        df = pd.DataFrame([{
            'timestamp': d.timestamp,
            'open': d.open,
            'high': d.high,
            'low': d.low,
            'close': d.close,
            'volume': d.volume
        } for d in data])
        
        df.set_index('timestamp', inplace=True)
        print(f"✅ {len(df)} points chargés\n")
        
    finally:
        db.close()
    
    # Tester les stratégies
    generator = StrategyGenerator(target_return=5.0)
    engine = BacktestingEngine(initial_capital=1000.0)
    
    best_return = -float('inf')
    best_strategy = None
    best_result = None
    
    strategy_counts = {'ultimate': 0, 'hyper': 0, 'mega': 0, 'others': 0}
    
    import numpy as np
    
    print(f"🔄 Test de {iterations} stratégies...\n")
    
    for i in range(iterations):
        # Distribution: 85% ULTIMATE, 5% HYPER, 5% MEGA, 5% autres
        strategy_type = np.random.choice(
            ['ultimate', 'ultimate', 'ultimate', 'hyper', 'mega', 'multi'],
            p=[0.45, 0.40, 0.10, 0.02, 0.02, 0.01]
        )
        
        try:
            if strategy_type == 'ultimate':
                strategy = generator.generate_random_ultimate_strategy()
                strategy_counts['ultimate'] += 1
            elif strategy_type == 'hyper':
                strategy = generator.generate_random_hyper_strategy()
                strategy_counts['hyper'] += 1
            elif strategy_type == 'mega':
                strategy = generator.generate_random_mega_strategy()
                strategy_counts['mega'] += 1
            else:
                strategy = generator.generate_random_multi_strategy()
                strategy_counts['others'] += 1
            
            # Backtester (sans logs DEBUG)
            result = engine.run_backtest(df, strategy, "WLN")
            
            # Meilleur ?
            if result.total_return > best_return:
                best_return = result.total_return
                best_strategy = strategy
                best_result = result
                print(f"  ✨ Iter {i+1:3d}/{iterations} - Nouveau best: {result.total_return:+7.2f}% | {strategy.name} | {result.total_trades} trades")
            
            # Progression
            elif (i+1) % 10 == 0:
                print(f"  ⏳ Iter {i+1:3d}/{iterations} - Best actuel: {best_return:+7.2f}%")
        
        except Exception as e:
            print(f"  ⚠️  Erreur iteration {i+1}: {e}")
            continue
    
    # Résultats
    print(f"\n{'─'*80}")
    print(f"📊 RÉSULTATS TEST RAPIDE")
    print(f"{'─'*80}")
    print(f"🎯 Meilleur retour: {best_return:+.2f}% (objectif: 5.0%)")
    print(f"📈 Stratégie: {best_strategy.name if best_strategy else 'N/A'}")
    
    if best_result:
        print(f"💼 Capital final: {best_result.final_capital:.2f} € (initial: 1000 €)")
        print(f"🔄 Trades: {best_result.total_trades}")
        print(f"✅ Win rate: {best_result.win_rate:.1f}%")
        print(f"📉 Max drawdown: {best_result.max_drawdown:.2f}%")
    
    print(f"\n🎲 Distribution:")
    print(f"   ULTIMATE:  {strategy_counts['ultimate']:3d} ({strategy_counts['ultimate']/iterations*100:.1f}%)")
    print(f"   HYPER:     {strategy_counts['hyper']:3d} ({strategy_counts['hyper']/iterations*100:.1f}%)")
    print(f"   MEGA:      {strategy_counts['mega']:3d} ({strategy_counts['mega']/iterations*100:.1f}%)")
    print(f"   AUTRES:    {strategy_counts['others']:3d} ({strategy_counts['others']/iterations*100:.1f}%)")
    print(f"{'='*80}\n")
    
    return best_return, best_strategy


if __name__ == "__main__":
    max_attempts = 3
    
    for attempt in range(1, max_attempts + 1):
        print(f"\n{'█'*80}")
        print(f"🔄 TENTATIVE {attempt}/{max_attempts}")
        print(f"{'█'*80}")
        
        best_return, best_strategy = quick_test(50)
        
        if best_return is None:
            print("❌ Échec du test")
            sys.exit(1)
        
        if best_return >= 5.0:
            print(f"\n🎉 SUCCÈS ! Objectif atteint: {best_return:.2f}% >= 5.0%")
            print(f"🏆 Stratégie gagnante: {best_strategy.name}")
            break
        
        else:
            print(f"\n⚠️  Objectif NON atteint: {best_return:.2f}% < 5.0%")
            
            if attempt < max_attempts:
                print(f"\n💡 AMÉLIORATION NÉCESSAIRE - Tentative {attempt + 1}...")
                print("🔧 Les stratégies actuelles (ULTIMATE avec 60+ indicateurs) seront retestées")
                print("    Augmenter les itérations ou modifier les seuils pour la prochaine tentative\n")
            else:
                print(f"\n❌ Objectif non atteint après {max_attempts} tentatives")
                print(f"📊 Meilleur résultat obtenu: {best_return:.2f}%")
                print("\n💭 Suggestions d'amélioration:")
                print("   1. Augmenter min_signals (moins de trades, meilleure qualité)")
                print("   2. Ajouter filtres de volatilité (ne trader que quand conditions optimales)")
                print("   3. Implémenter stop-loss dynamique")
                print("   4. Changer de timeframe (5min au lieu de 1min)")
                print("   5. Utiliser machine learning pour sélection des indicateurs")
    
    print(f"\n{'█'*80}\n")
