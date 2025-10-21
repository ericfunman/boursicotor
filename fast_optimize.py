"""
Script d'optimisation RAPIDE - 1000 itérations
- Logs DEBUG désactivés
- Affichage progression seulement
- ~3 minutes pour 1000 itérations
"""
import sys
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from backend.models import SessionLocal, Ticker, HistoricalData
from backend.backtesting_engine import StrategyGenerator, BacktestingEngine

# DÉSACTIVER TOUS LES LOGS DEBUG POUR VITESSE MAXIMUM
logging.getLogger('backend.backtesting_engine').setLevel(logging.CRITICAL)
logging.getLogger('backend.config').setLevel(logging.CRITICAL)
logging.getLogger().setLevel(logging.CRITICAL)


def load_data(symbol="WLN"):
    """Charge les données depuis la base"""
    db = SessionLocal()
    try:
        ticker = db.query(Ticker).filter(Ticker.symbol == symbol).first()
        if not ticker:
            print(f"❌ Ticker {symbol} non trouvé")
            return None
        
        data = db.query(HistoricalData).filter(
            HistoricalData.ticker_id == ticker.id
        ).order_by(HistoricalData.timestamp.asc()).all()
        
        if len(data) < 100:
            print(f"❌ Pas assez de données")
            return None
        
        df = pd.DataFrame([{
            'timestamp': d.timestamp,
            'open': d.open,
            'high': d.high,
            'low': d.low,
            'close': d.close,
            'volume': d.volume
        } for d in data])
        
        df.set_index('timestamp', inplace=True)
        return df
    finally:
        db.close()


def fast_search(iterations=1000, symbol="WLN", capital=1000.0, target=5.0):
    """Recherche rapide de stratégie"""
    
    print(f"\n{'='*80}")
    print(f"🚀 OPTIMISATION RAPIDE - {symbol}")
    print(f"{'='*80}")
    print(f"💰 Capital: {capital}€ | 🎯 Objectif: {target}% | 🔄 Itérations: {iterations}")
    
    # Charger données
    print(f"\n📊 Chargement données {symbol}...", end=" ", flush=True)
    df = load_data(symbol)
    if df is None:
        return None, None
    print(f"✅ {len(df)} points")
    
    # Setup
    generator = StrategyGenerator(target_return=target)
    engine = BacktestingEngine(initial_capital=capital)
    
    best_return = -float('inf')
    best_strategy = None
    best_result = None
    
    strategy_counts = {
        'ultimate': 0, 'hyper': 0, 'mega': 0, 'ultra': 0,
        'advanced': 0, 'multi': 0, 'others': 0
    }
    
    print(f"\n⏱️  Démarrage... (estimation: ~3 minutes)\n")
    start_time = datetime.now()
    
    # BOUCLE PRINCIPALE - Sans logs
    for i in range(iterations):
        # Afficher progression tous les 50
        if (i + 1) % 50 == 0 or i == 0:
            elapsed = (datetime.now() - start_time).total_seconds()
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            eta = (iterations - i - 1) / rate if rate > 0 else 0
            progress = (i + 1) / iterations * 100
            print(f"  [{i+1:4d}/{iterations}] {progress:5.1f}% | "
                  f"Meilleur: {best_return:+7.2f}% | "
                  f"ETA: {int(eta//60)}m{int(eta%60):02d}s", flush=True)
        
        # Générer stratégie (85% ULTIMATE)
        strategy_type = np.random.choice(
            ['ma', 'rsi', 'multi', 'advanced', 'momentum', 'mean_reversion', 
             'ultra_aggressive', 'mega', 'hyper', 'ultimate', 'ultimate', 'ultimate'],
            p=[0.01, 0.01, 0.01, 0.01, 0.01, 0.02, 0.03, 0.03, 0.02, 0.283, 0.283, 0.284]
        )
        
        if strategy_type == 'ultimate':
            strategy = generator.generate_random_ultimate_strategy()
            strategy_counts['ultimate'] += 1
        elif strategy_type == 'hyper':
            strategy = generator.generate_random_hyper_strategy()
            strategy_counts['hyper'] += 1
        elif strategy_type == 'mega':
            strategy = generator.generate_random_mega_strategy()
            strategy_counts['mega'] += 1
        elif strategy_type == 'ultra_aggressive':
            strategy = generator.generate_random_ultra_aggressive_strategy()
            strategy_counts['ultra'] += 1
        elif strategy_type == 'advanced':
            strategy = generator.generate_random_advanced_multi_strategy()
            strategy_counts['advanced'] += 1
        elif strategy_type == 'multi':
            strategy = generator.generate_random_multi_strategy()
            strategy_counts['multi'] += 1
        elif strategy_type == 'ma':
            strategy = generator.generate_random_ma_strategy()
            strategy_counts['others'] += 1
        elif strategy_type == 'rsi':
            strategy = generator.generate_random_rsi_strategy()
            strategy_counts['others'] += 1
        elif strategy_type == 'momentum':
            strategy = generator.generate_random_momentum_strategy()
            strategy_counts['others'] += 1
        else:
            strategy = generator.generate_random_mean_reversion_strategy()
            strategy_counts['others'] += 1
        
        # Backtest (sans logs)
        result = engine.run_backtest(df, strategy, symbol)
        
        # Vérifier si meilleur
        if result.total_return > best_return:
            best_return = result.total_return
            best_strategy = strategy
            best_result = result
    
    # Temps total
    duration = (datetime.now() - start_time).total_seconds()
    
    # RAPPORT FINAL
    print(f"\n{'='*80}")
    print(f"📊 RÉSULTATS FINAUX")
    print(f"{'='*80}")
    print(f"⏱️  Durée: {int(duration//60)}m{int(duration%60):02d}s "
          f"({duration/iterations:.2f}s par itération)")
    print(f"\n🎯 MEILLEUR RÉSULTAT:")
    print(f"   Retour:        {best_return:+.2f}%")
    print(f"   Stratégie:     {best_strategy.name}")
    print(f"   Capital final: {best_result.final_capital:.2f}€ (initial: {capital}€)")
    print(f"   Trades:        {best_result.total_trades}")
    print(f"   Win rate:      {best_result.win_rate:.1f}%")
    print(f"   Max drawdown:  {best_result.max_drawdown:.2f}%")
    if best_result.sharpe_ratio:
        print(f"   Sharpe ratio:  {best_result.sharpe_ratio:.2f}")
    
    print(f"\n📊 DISTRIBUTION DES STRATÉGIES:")
    total = sum(strategy_counts.values())
    for name, count in strategy_counts.items():
        pct = count / total * 100 if total > 0 else 0
        print(f"   {name.upper():12s}: {count:4d} ({pct:5.1f}%)")
    
    if best_return >= target:
        print(f"\n✅ OBJECTIF ATTEINT ! {best_return:.2f}% >= {target}%")
    else:
        print(f"\n⚠️  OBJECTIF NON ATTEINT: {best_return:.2f}% < {target}%")
    
    print(f"{'='*80}\n")
    
    return best_strategy, best_result


def suggest_improvements(strategy, result):
    """Suggère des améliorations basées sur les résultats"""
    print(f"\n{'='*80}")
    print(f"💡 SUGGESTIONS D'AMÉLIORATION")
    print(f"{'='*80}\n")
    
    # Analyse des problèmes
    if result.total_trades > 200:
        print(f"⚠️  TROP DE TRADES ({result.total_trades})")
        print(f"   → Problème: Commissions mangent les profits (0.18% par round-trip)")
        print(f"   → Solution: Augmenter min_signals de {strategy.min_signals} à {strategy.min_signals + 2}")
    
    if result.win_rate < 40:
        print(f"⚠️  WIN RATE FAIBLE ({result.win_rate:.1f}%)")
        print(f"   → Problème: Stratégie gagne moins de 40% du temps")
        print(f"   → Solutions:")
        print(f"      1. Ajouter filtres de qualité (volatilité, volume)")
        print(f"      2. Détecter régimes de marché (trending vs ranging)")
    
    if result.max_drawdown < -50:
        print(f"⚠️  DRAWDOWN ÉLEVÉ ({result.max_drawdown:.2f}%)")
        print(f"   → Problème: Pertes importantes")
        print(f"   → Solutions:")
        print(f"      1. Stop-loss à -2% par trade")
        print(f"      2. Position sizing dynamique (Kelly Criterion)")
    
    # NOUVEAUX INDICATEURS À AJOUTER
    print(f"\n🆕 NOUVEAUX INDICATEURS PROPOSÉS:")
    print(f"\n1. **INDICATEURS DE VOLATILITÉ** (filtre qualité):")
    print(f"   - Bollinger Band Width: mesure contraction/expansion")
    print(f"   - Average True Range %: volatilité normalisée")
    print(f"   → Trade seulement si volatilité dans plage optimale")
    
    print(f"\n2. **INDICATEURS DE VOLUME** (confirmation):")
    print(f"   - Volume Profile: identifier zones support/résistance")
    print(f"   - On-Balance Volume Rate of Change")
    print(f"   - Accumulation/Distribution avec divergences")
    print(f"   → Confirmer signals avec volume anormal")
    
    print(f"\n3. **PATTERNS DE PRIX** (reconnaissance):")
    print(f"   - Higher Highs / Lower Lows detection")
    print(f"   - Support/Resistance breaks avec retest")
    print(f"   - Gap detection et stratégie gap-fill")
    print(f"   → Structure de prix > indicateurs seuls")
    
    print(f"\n4. **RÉGIME DE MARCHÉ** (adaptation):")
    print(f"   - ADX > 25: Trending (stratégies momentum)")
    print(f"   - ADX < 20: Ranging (stratégies mean-reversion)")
    print(f"   - Correlation avec indice: market beta")
    print(f"   → Différentes stratégies selon conditions")
    
    print(f"\n5. **TIME-BASED FILTERS** (timing):")
    print(f"   - Heure de la journée (éviter open/close volatiles)")
    print(f"   - Jour de la semaine (lundi ≠ vendredi)")
    print(f"   - Distance depuis dernier trade (cooldown)")
    print(f"   → Ne trader que moments optimaux")
    
    print(f"\n6. **INDICATEURS COMPOSITES** (combinaisons):")
    print(f"   - Trend Strength Score (MA + ADX + MACD)")
    print(f"   - Momentum Quality Score (RSI + ROC + MFI)")
    print(f"   - Volume Confirmation Score (OBV + Volume + MFI)")
    print(f"   → Score global > indicateurs isolés")
    
    print(f"\n7. **DIVERGENCES** (retournements):")
    print(f"   - RSI vs Prix (détection actuelle à améliorer)")
    print(f"   - MACD vs Prix")
    print(f"   - Volume vs Prix")
    print(f"   → Signaux de retournement anticipés")
    
    print(f"\n{'='*80}\n")
    
    # Recommandation prioritaire
    if result.total_trades > 200:
        print(f"🎯 PRIORITÉ #1: Réduire nombre de trades")
        print(f"   → Passer min_signals de {strategy.min_signals} à {strategy.min_signals + 3}")
        print(f"   → Ajouter filtre volatilité (ATR %)")
        print(f"   → Attendre confirmation volume")
    else:
        print(f"🎯 PRIORITÉ #1: Améliorer qualité des signaux")
        print(f"   → Ajouter détection régime marché (ADX)")
        print(f"   → Implémenter patterns de prix")
        print(f"   → Filtrer sur heures de trading optimales")
    
    print(f"\n{'='*80}\n")


def main():
    """Point d'entrée"""
    iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    symbol = sys.argv[2] if len(sys.argv) > 2 else "WLN"
    capital = float(sys.argv[3]) if len(sys.argv) > 3 else 1000.0
    target = float(sys.argv[4]) if len(sys.argv) > 4 else 5.0
    
    # Lancer recherche rapide
    best_strategy, best_result = fast_search(iterations, symbol, capital, target)
    
    if best_strategy and best_result:
        # Suggérer améliorations
        suggest_improvements(best_strategy, best_result)
        return 0
    else:
        print("❌ Erreur lors de l'optimisation")
        return 1


if __name__ == "__main__":
    sys.exit(main())
