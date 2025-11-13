#!/usr/bin/env python3
"""
Replace duplicated strings with constants in ibkr_collector.py
"""
from pathlib import Path

file_path = Path("backend/ibkr_collector.py")

# Read the file
with open(file_path, encoding='utf-8') as f:
    content = f.read()

# Replace patterns (from most specific to least specific)
replacements = [
    (' Europe/Paris', 'TIMEZONE_PARIS'),
    ("'5 secs'", 'TIMEFRAME_5SECS'),
    ("'1 min'", 'TIMEFRAME_1MIN'),
    ("'5 mins'", 'TIMEFRAME_5MINS'),
    ("'15 mins'", 'TIMEFRAME_15MINS'),
    ("'30 mins'", 'TIMEFRAME_30MINS'),
    ("'1 hour'", 'TIMEFRAME_1HOUR'),
    ("'1 day'", 'TIMEFRAME_1DAY'),
    ("'No data received'", 'ERROR_NO_DATA'),
]

count = 0
for old, new in replacements:
    old_count = content.count(old)
    content = content.replace(old, new)
    count += old_count
    if old_count > 0:
        print(f"✅ Replaced {old_count}x '{old}' → {new}")

# Write back
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n✅ TOTAL REPLACEMENTS: {count}")
print(f"💾 File updated: {file_path}")
