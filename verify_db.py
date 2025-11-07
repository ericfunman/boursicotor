#!/usr/bin/env python
"""Verify database tables"""
import sqlite3

conn = sqlite3.connect('boursicotor.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = cursor.fetchall()
print("✅ Database Tables Created:")
for table in tables:
    print(f"  - {table[0]}")
conn.close()
