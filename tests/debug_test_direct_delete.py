"""Module documentation."""

import sqlite3

# Direct SQLite connection - no SQLAlchemy at all
conn = sqlite3.connect('boursicotor.db')
cursor = conn.cursor()

# Check current strategies
cursor.execute("SELECT id, name FROM strategies")
strategies = cursor.fetchall()
print(f"Strategies before deletion: {len(strategies)}")
for sid, name in strategies:
    print(f"- ID: {sid}, Name: {name}")

if strategies:
    strategy_id = strategies[0][0]
    strategy_name = strategies[0][1]
    
    print(f"\nDeleting strategy ID {strategy_id} ({strategy_name})...")
    
    # Delete backtests first
    cursor.execute("DELETE FROM backtests WHERE strategy_id = ?", (strategy_id,))
    print(f"Deleted {cursor.rowcount} backtests")
    
    # Delete strategy
    cursor.execute("DELETE FROM strategies WHERE id = ?", (strategy_id,))
    print(f"Deleted {cursor.rowcount} strategies")
    
    conn.commit()
    
    # Check remaining
    cursor.execute("SELECT id, name FROM strategies")
    remaining = cursor.fetchall()
    print(f"\nStrategies after deletion: {len(remaining)}")
    for sid, name in remaining:
        print(f"- ID: {sid}, Name: {name}")
        
    print("\n✅ Deletion successful!")
else:
    print("\nNo strategies to delete")

conn.close()
