"""Test de la stratégie ULTIMATE"""
from backend.backtesting_engine import StrategyGenerator

# Test de génération
generator = StrategyGenerator(target_return=10.0)
strategy = generator.generate_random_ultimate_strategy()

print(f"✅ Stratégie générée: {strategy.name}")
print(f"   - Seuil de signaux: {strategy.min_signals}")
print(f"   - Fibonacci periods: {strategy.fibonacci_periods}")
print(f"   - Ichimoku Tenkan: {strategy.ichimoku_tenkan}")
print(f"   - Ichimoku Kijun: {strategy.ichimoku_kijun}")
print(f"   - Keltner period: {strategy.keltner_period}")
print(f"   - Parabolic SAR accel: {strategy.sar_acceleration:.4f}")
print(f"   - Aroon period: {strategy.aroon_period}")
print(f"   - CMO period: {strategy.cmo_period}")
print(f"   - Ultimate Osc periods: {strategy.ultimate_osc_short}/{strategy.ultimate_osc_medium}/{strategy.ultimate_osc_long}")
print("\n🎯 ULTIMATE Strategy avec 60+ indicateurs prête à tester!")
