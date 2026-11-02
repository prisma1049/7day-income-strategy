#!/usr/bin/env python3
import sqlite3
conn = sqlite3.connect('tracking.db')
c = conn.cursor()
c.execute('SELECT * FROM clicks ORDER BY timestamp DESC LIMIT 20')
for row in c.fetchall():
    print(row)
c.execute('SELECT * FROM daily_stats')
for row in c.fetchall():
    print(row)
c.execute('SELECT * FROM conversions')
for row in c.fetchall():
    print(row)
conn.close()