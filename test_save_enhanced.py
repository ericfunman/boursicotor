"""
Test de sauvegarde d'une stratégie Enhanced
"""
from datetime import datetime
from backend.strategy_manager import StrategyManager
from backend.backtesting_engine import EnhancedMovingAverageStrategy, BacktestResult
import numpy as np

# Create an enhanced strategy (like the optimizer would)
strategy = EnhancedMovingAverageStrategy(
    fast_period=18,
    slow_period=37,
    roc_period=10,
    roc_threshold=2.5,
    adx_period=14,
    adx_threshold=25,
    volume_ratio_short=5,
    volume_ratio_long=20,
    volume_threshold=1.3,
    momentum_period=10,
    momentum_threshold=1.0,
    bb_period=20,
    bb_width_threshold=0.05,
    use_supertrend=True,
    supertrend_period=14,
    supertrend_multiplier=3.0,
    use_parabolic_sar=False,
    use_donchian=True,
    donchian_period=20,
    donchian_threshold=0.04,
    use_vwap=False,
    use_obv=True,
    use_cmf=False,
    cmf_period=20,
    cmf_threshold=0.05,
    use_elder_ray=False,
    elder_ray_period=13,
    min_signals=3
)
strategy.name = "WLN_-38.00%"

# Create a mock backtest result
result = BacktestResult(
    strategy_name="WLN_-38.00%",
    symbol="WLN.PA",
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31),
    initial_capital=1000.0,
    final_capital=620.0,
    total_return=-38.0,
    sharpe_ratio=-1.2,
    max_drawdown=-42.5,
    win_rate=35.0,
    total_trades=15,
    winning_trades=5,
    losing_trades=10,
    trades=[]
)

print("Testing enhanced strategy save...")
print(f"Strategy name: {strategy.name}")
print(f"Strategy type: {strategy.__class__.__name__}")
print(f"Parameters count: {len(strategy.parameters)}")
print(f"Symbol: {result.symbol}")
print(f"Return: {result.total_return}%")

# Save the strategy
try:
    strategy_id = StrategyManager.save_strategy(strategy, result)
    
    if strategy_id:
        print(f"\n✅ Strategy saved successfully with ID: {strategy_id}")
        
        # Retrieve all strategies
        print("\nRetrieving all strategies...")
        strategies = StrategyManager.get_all_strategies()
        print(f"Total strategies found: {len(strategies)}")
        
        for strat in strategies:
            print(f"\n- ID: {strat['id']}")
            print(f"  Name: {strat['name']}")
            print(f"  Type: {strat['type']}")
            print(f"  Description: {strat['description']}")
            print(f"  Latest Return: {strat['latest_return']}%")
            print(f"  Parameters count: {len(strat['parameters'])}")
    else:
        print("\n❌ Failed to save strategy (returned None)")
except Exception as e:
    print(f"\n❌ Exception during save: {e}")
    import traceback
    traceback.print_exc()
