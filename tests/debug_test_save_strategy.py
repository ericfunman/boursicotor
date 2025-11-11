"""
Test de la sauvegarde de stratégie
"""
from datetime import datetime
from backend.strategy_manager import StrategyManager
from backend.backtesting_engine import MovingAverageCrossover, BacktestResult

# Create a simple strategy
strategy = MovingAverageCrossover(fast_period=20, slow_period=50)
strategy.name = "TTE_7.8%"

# Create a mock backtest result
result = BacktestResult(
    strategy_name="TTE_7.8%",
    symbol="TTE.PA",
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31),
    initial_capital=1000.0,
    final_capital=1078.0,
    total_return=7.8,
    sharpe_ratio=1.5,
    max_drawdown=-5.2,
    win_rate=65.0,
    total_trades=10,
    winning_trades=7,
    losing_trades=3,
    trades=[]
)

print("Testing strategy save...")
print(f"Strategy name: {strategy.name}")
print(f"Strategy type: {strategy.__class__.__name__}")
print(f"Parameters: {strategy.parameters}")
print(f"Symbol: {result.symbol}")
print(f"Return: {result.total_return}%")

# Save the strategy
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
else:
    print("\n❌ Failed to save strategy")
