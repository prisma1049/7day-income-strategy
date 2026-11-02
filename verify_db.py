import sqlite3
conn = sqlite3.connect('/root/7day-income-site/tracking.db')
subs = conn.execute('SELECT id, email, confirmed FROM subscribers').fetchall()
print(f'Total subscribers: {len(subs)}')
confirmed = [s for s in subs if s[2] == 1]
pending = [s for s in subs if s[2] == 0]
print(f'Confirmed: {len(confirmed)}')
print(f'Pending: {len(pending)}')
ns = conn.execute('SELECT COUNT(*) FROM nurture_schedule').fetchone()
print(f'Nurture schedule entries: {ns[0]}')
# Check lead_magnet column
for s in subs[:3]:
    print(f'  Subscriber: id={s[0]}, email={s[1]}, confirmed={s[2]}, lead_magnet={s[3] if len(s)>3 else "N/A"}')
# Check tables
tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print(f'Tables: {tables}')
conn.close()