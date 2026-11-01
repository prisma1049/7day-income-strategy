import sqlite3

conn = sqlite3.connect('tracking.db')
c = conn.cursor()

c.execute('PRAGMA table_info(ab_assignments)')
print('ab_assignments:', c.fetchall())

c.execute('PRAGMA table_info(ab_results)')
print('ab_results:', c.fetchall())

c.execute('PRAGMA table_info(subscribers)')
print('subscribers:', c.fetchall())

c.execute('PRAGMA table_info(subscriber_events)')
print('subscriber_events:', c.fetchall())

conn.close()