#!/usr/bin/env python3
import sqlite3
from datetime import datetime, timezone

conn = sqlite3.connect('/root/7day-income-site/tracking.db')
conn.row_factory = sqlite3.Row

# Get today's date
today = datetime.now(timezone.utc).date().isoformat()
print(f"Today: {today}")

# Get today's daily stats
row = conn.execute('SELECT * FROM daily_stats WHERE date = ?', (today,)).fetchone()
print("\nToday's daily stats:")
if row:
    for key in row.keys():
        print(f"  {key}: {row[key]}")
else:
    print("  No data for today")

# Get all daily stats
print("\nAll daily stats:")
all_stats = conn.execute('SELECT * FROM daily_stats ORDER BY date DESC').fetchall()
for s in all_stats:
    print(f"  {dict(s)}")

# Get conversions
print("\nConversions by program:")
conversions = conn.execute('''
    SELECT affiliate_program, COUNT(*) as conversions, SUM(commission_eur) as total_commission
    FROM conversions
    WHERE status = 'confirmed'
    GROUP BY affiliate_program
''').fetchall()
for c in conversions:
    print(f"  {dict(c)}")

# Get clicks by program
print("\nClicks by program:")
clicks = conn.execute('''
    SELECT affiliate_program, COUNT(*) as clicks
    FROM clicks
    GROUP BY affiliate_program
''').fetchall()
for c in clicks:
    print(f"  {dict(c)}")

# Get subscriber count
print("\nSubscribers:")
subs = conn.execute('SELECT COUNT(*) as count, confirmed FROM subscribers GROUP BY confirmed').fetchall()
for s in subs:
    print(f"  {s['confirmed']}: {s['count']}")

# Get total affiliate clicks
total_aff = conn.execute('SELECT COUNT(*) as cnt FROM clicks WHERE affiliate_program IN ("mixo", "elevenlabs", "runpod", "surfer_seo", "carrd", "vast_ai", "together_ai")').fetchone()
print(f"\nTotal affiliate clicks: {total_aff['cnt']}")

conn.close()