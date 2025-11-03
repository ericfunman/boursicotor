"""
Script autonome pour supprimer une stratégie
Usage: python delete_strategy_standalone.py <strategy_id>
"""
import sys
import sqlite3

if len(sys.argv) < 2:
    print("Usage: python delete_strategy_standalone.py <strategy_id>")
    sys.exit(1)

strategy_id = int(sys.argv[1])

try:
    conn = sqlite3.connect('boursicotor.db', isolation_level=None)
    cursor = conn.cursor()
    
    # Delete backtests first
    cursor.execute("DELETE FROM backtests WHERE strategy_id = ?", (strategy_id,))
    backtest_count = cursor.rowcount
    
    # Delete strategy
    cursor.execute("DELETE FROM strategies WHERE id = ?", (strategy_id,))
    strategy_count = cursor.rowcount
    
    conn.close()
    
    if strategy_count > 0:
        print(f"SUCCESS:Deleted strategy {strategy_id} with {backtest_count} backtests")
        sys.exit(0)
    else:
        print(f"ERROR:Strategy {strategy_id} not found")
        sys.exit(1)
        
except Exception as e:
    print(f"ERROR:{str(e)}")
    sys.exit(1)
