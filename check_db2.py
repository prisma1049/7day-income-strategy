import sqlite3

conn = sqlite3.connect('tracking.db')
c = conn.cursor()

c.execute('SELECT * FROM ab_variants')
print('AB Variants:', c.fetchall())

c.execute('SELECT * FROM ab_assignments')
print('AB Assignments:', c.fetchall())

c.execute('SELECT * FROM ab_results')
print('AB Results:', c.fetchall())

c.execute('SELECT * FROM subscribers')
print('Subscribers:', c.fetchall())

c.execute('SELECT * FROM subscriber_events')
print('Subscriber Events:', c.fetchall())

conn.close()