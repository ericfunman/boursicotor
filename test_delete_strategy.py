"""
Test de suppression de stratégie
"""
from backend.strategy_manager import StrategyManager

print("Testing strategy deletion...")

# Get all strategies
strategies = StrategyManager.get_all_strategies()
print(f"\nStrategies before deletion: {len(strategies)}")
for strat in strategies:
    print(f"- ID: {strat['id']}, Name: {strat['name']}")

if strategies:
    # Save strategy ID to delete
    strategy_id = strategies[0]['id']
    strategy_name = strategies[0]['name']
    
    # Clear strategies list to release any references
    strategies = None
    
    print(f"\nDeleting strategy ID {strategy_id} ({strategy_name})...")
    success = StrategyManager.delete_strategy(strategy_id)
    
    if success:
        print(f"✅ Strategy deleted successfully")
        
        # Check remaining strategies
        strategies_after = StrategyManager.get_all_strategies()
        print(f"\nStrategies after deletion: {len(strategies_after)}")
        for strat in strategies_after:
            print(f"- ID: {strat['id']}, Name: {strat['name']}")
    else:
        print("❌ Failed to delete strategy")
else:
    print("\nNo strategies to delete")
