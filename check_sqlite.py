import sqlite3
print('sqlite3 OK')
conn = sqlite3.connect(':memory:')
print('SQLite works:', conn.execute('SELECT 1').fetchone())