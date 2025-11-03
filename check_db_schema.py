import sqlite3

conn = sqlite3.connect('boursicotor.db')
cursor = conn.cursor()

# Check foreign keys setting
cursor.execute('PRAGMA foreign_keys')
print('Foreign keys enabled:', cursor.fetchone())

# Get backtests table schema
cursor.execute('SELECT sql FROM sqlite_master WHERE name="backtests"')
print('\nBacktests table:')
print(cursor.fetchone()[0])

# Get strategies table schema  
cursor.execute('SELECT sql FROM sqlite_master WHERE name="strategies"')
print('\nStrategies table:')
print(cursor.fetchone()[0])

# Check for triggers
cursor.execute('SELECT name, sql FROM sqlite_master WHERE type="trigger"')
triggers = cursor.fetchall()
if triggers:
    print('\n Triggers:')
    for name, sql in triggers:
        print(f'\n{name}:')
        print(sql)
else:
    print('\nNo triggers found')

conn.close()
