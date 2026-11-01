#!/usr/bin/env python3
import sqlite3
conn = sqlite3.connect('tracking.db')
conn.row_factory = sqlite3.Row
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print('Tables:', [t[0] for t in tables])

try:
    variants = conn.execute('SELECT * FROM ab_variants WHERE is_active=1').fetchall()
    print('\nActive A/B Variants:')
    for v in variants:
        print(f'  {dict(v)}')
except Exception as e:
    print('Error:', e)

try:
    results = conn.execute('SELECT * FROM ab_results ORDER BY timestamp DESC LIMIT 20').fetchall()
    print('\nA/B Results:')
    for r in results:
        print(f'  {dict(r)}')
except Exception as e:
    print('ab_results error:', e)

conn.close()