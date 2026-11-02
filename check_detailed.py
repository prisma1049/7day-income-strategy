#!/usr/bin/env python3
import tracking
import sqlite3

# Check more detailed data
data = tracking.get_dashboard_data()
print('Full clicks_by_program:', data['clicks_by_program'])
print('Conversions by program:', data['conversions_by_program'])
print('Daily stats:', data['daily_stats'])

# Check clicks table directly
conn = sqlite3.connect('tracking.db')
c = conn.cursor()
c.execute('SELECT * FROM clicks ORDER BY timestamp DESC LIMIT 20')
for row in c.fetchall():
    print('CLICK:', row)
c.execute('SELECT * FROM conversions ORDER BY timestamp DESC LIMIT 20')
for row in c.fetchall():
    print('CONVERSION:', row)
c.execute('SELECT * FROM daily_stats ORDER BY date DESC LIMIT 10')
for row in c.fetchall():
    print('DAILY_STAT:', row)
conn.close()