#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('tracking.db')
c = conn.cursor()

print("=== DAILY STATS ===")
c.execute('SELECT * FROM daily_stats ORDER BY date DESC')
for row in c.fetchall():
    print(row)

print("\n=== CONVERSIONS ===")
c.execute('SELECT * FROM conversions ORDER BY timestamp DESC')
for row in c.fetchall():
    print(row)

print("\n=== PAGE VIEWS ===")
c.execute('SELECT * FROM page_views ORDER BY timestamp DESC LIMIT 20')
for row in c.fetchall():
    print(row)

conn.close()