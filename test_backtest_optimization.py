"""
Script de test des optimisations de backtesting
Compare les performances avant/après optimisations
"""
import time
import pandas as pd
import numpy as np
from backend.backtesting_engine import BacktestingEngine, MovingAverageCrossover
from backend.models import SessionLocal, Ticker, HistoricalData

def generate_test_data(n_points=1000):
    """Génère des données de test"""
    dates = pd.date_range('2023-01-01', periods=n_points, freq='1H')
    np.random.seed(42)
    
    # Génération de prix réalistes avec tendance
    price = 100
    prices = []
    for _ in range(n_points):
        price += np.random.randn() * 2
        prices.append(max(price, 1))  # Prix minimum de 1
    
    df = pd.DataFrame({
        'open': prices,
        'high': [p * (1 + abs(np.random.randn()) * 0.02) for p in prices],
        'low': [p * (1 - abs(np.random.randn()) * 0.02) for p in prices],
        'close': prices,
        'volume': np.random.randint(1000, 100000, n_points)
    }, index=dates)
    
    return df

def test_indicator_calculation_speed():
    """Test la vitesse de calcul des indicateurs"""
    print("=" * 70)
    print("📊 TEST 1: Vitesse de calcul des indicateurs")
    print("=" * 70)
    
    df = generate_test_data(2000)
    
    # Test sans cache
    print("\n🔄 Premier calcul (sans cache)...")
    start = time.time()
    indicators1 = BacktestingEngine._precalculate_indicators(df, use_cache=False)
    time1 = time.time() - start
    print(f"   ⏱️  Temps: {time1:.4f}s")
    print(f"   📈 Indicateurs calculés: {len(indicators1)}")
    
    # Test avec cache (devrait être instantané)
    print("\n🔄 Deuxième calcul (avec cache)...")
    start = time.time()
    indicators2 = BacktestingEngine._precalculate_indicators(df, use_cache=True)
    time2 = time.time() - start
    print(f"   ⏱️  Temps: {time2:.4f}s")
    print(f"   🚀 Accélération: {time1/time2:.1f}x plus rapide")
    
    # Stats du cache
    stats = BacktestingEngine.get_cache_stats()
    print(f"\n📦 Cache stats:")
    print(f"   - Entrées: {stats['cache_size']}")
    print(f"   - Numba: {'✅ Activé' if stats['numba_enabled'] else '❌ Désactivé'}")

def test_backtest_speed():
    """Test la vitesse d'un backtest complet"""
    print("\n" + "=" * 70)
    print("🎯 TEST 2: Vitesse d'un backtest complet")
    print("=" * 70)
    
    df = generate_test_data(1000)
    strategy = MovingAverageCrossover(fast_period=10, slow_period=30)
    
    # Test avec vectorisation
    print("\n🔄 Backtest avec vectorisation...")
    engine = BacktestingEngine(initial_capital=10000)
    start = time.time()
    result = engine.run_backtest(df, strategy, 'TEST', use_vectorized=True)
    time_vec = time.time() - start
    print(f"   ⏱️  Temps: {time_vec:.4f}s")
    print(f"   💰 Résultat: {result.total_return:.2f}%")
    print(f"   📊 Trades: {result.total_trades}")

def test_parallel_optimization():
    """Test l'optimisation parallèle"""
    print("\n" + "=" * 70)
    print("⚡ TEST 3: Optimisation parallèle (100 stratégies)")
    print("=" * 70)
    
    # Charger de vraies données si disponibles
    db = SessionLocal()
    try:
        ticker = db.query(Ticker).filter(Ticker.symbol.like('%WLN%')).first()
        if ticker:
            print(f"\n📥 Chargement des données pour {ticker.symbol}...")
            data = db.query(HistoricalData).filter(
                HistoricalData.ticker_id == ticker.id
            ).order_by(HistoricalData.timestamp.asc()).limit(1000).all()
            
            if data:
                df = pd.DataFrame([{
                    'open': d.open,
                    'high': d.high,
                    'low': d.low,
                    'close': d.close,
                    'volume': d.volume
                } for d in data])
                df.index = pd.DatetimeIndex([d.timestamp for d in data])
                print(f"   ✅ {len(df)} points chargés")
            else:
                print("   ⚠️  Pas de données, utilisation de données de test")
                df = generate_test_data(1000)
        else:
            print("   ⚠️  Ticker non trouvé, utilisation de données de test")
            df = generate_test_data(1000)
    finally:
        db.close()
    
    # Test optimisation
    print("\n🔄 Lancement de l'optimisation (100 itérations)...")
    engine = BacktestingEngine(initial_capital=10000)
    
    start = time.time()
    best_strategy, best_result, all_results = engine.run_parallel_optimization(
        df=df,
        symbol='TEST',
        num_iterations=100,
        target_return=5.0,
        num_processes=4
    )
    elapsed = time.time() - start
    
    print(f"\n✅ Optimisation terminée!")
    print(f"   ⏱️  Temps total: {elapsed:.2f}s")
    print(f"   ⚡ Vitesse: {100/elapsed:.1f} stratégies/seconde")
    print(f"   🏆 Meilleur retour: {best_result.total_return:.2f}%")
    print(f"   📊 Stratégies testées: {len(all_results)}")
    print(f"   ✅ Stratégies profitables: {sum(1 for _, r in all_results if r.total_return > 0)}")
    
    # Stats cache
    stats = BacktestingEngine.get_cache_stats()
    print(f"\n📦 Cache après optimisation:")
    print(f"   - Entrées: {stats['cache_size']}")

def main():
    """Execute tous les tests"""
    print("\n" + "=" * 70)
    print("🚀 TESTS DES OPTIMISATIONS DE BACKTESTING")
    print("=" * 70)
    
    # Vider le cache avant les tests
    BacktestingEngine.clear_indicators_cache()
    
    # Tests
    test_indicator_calculation_speed()
    test_backtest_speed()
    test_parallel_optimization()
    
    print("\n" + "=" * 70)
    print("✅ TOUS LES TESTS TERMINÉS")
    print("=" * 70)
    print("\n💡 Recommandations:")
    print("   - Si Numba est activé: 10-50x plus rapide sur les indicateurs")
    print("   - Le cache évite les recalculs inutiles")
    print("   - La parallélisation utilise tous vos CPU")
    print("   - Pour de meilleures perfs: installez Numba avec install_numba.bat")
    print()

if __name__ == "__main__":
    main()
