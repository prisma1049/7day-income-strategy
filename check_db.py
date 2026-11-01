import sqlite3

conn = sqlite3.connect('tracking.db')
c = conn.cursor()

c.execute('SELECT name FROM sqlite_master WHERE type="table"')
print('Tables:', c.fetchall())

c.execute('SELECT * FROM clicks')
print('Clicks:', c.fetchall())

c.execute('SELECT * FROM conversions')
print('Conversions:', c.fetchall())

c.execute('SELECT * FROM daily_stats')
print('Daily Stats:', c.fetchall())

c.execute('SELECT * FROM ab_tests')
print('AB Tests:', c.fetchall())

c.execute('SELECT * FROM ab_results')
print('AB Results:', c.fetchall())

conn.close()