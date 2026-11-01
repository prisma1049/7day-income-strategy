#!/usr/bin/env python3
import sqlite3

DB_PATH = "tracking.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

print("=== CLICKS ===")
for r in conn.execute('SELECT affiliate_program, COUNT(*) as c FROM clicks GROUP BY affiliate_program'):
    print(f'  {r["affiliate_program"]}: {r["c"]}')

print()
print("=== CONVERSIONS ===")
for r in conn.execute('SELECT affiliate_program, COUNT(*) as c, SUM(commission_eur) as rev FROM conversions WHERE status="confirmed" GROUP BY affiliate_program'):
    print(f'  {r["affiliate_program"]}: {r["c"]} conversions, {r["rev"]} €')

print()
print("=== DAILY STATS ===")
for r in conn.execute('SELECT * FROM daily_stats ORDER BY date DESC LIMIT 7'):
    print(f'  {r["date"]}: views={r["page_views"]}, visitors={r["unique_visitors"]}, clicks={r["total_clicks"]}, aff_clicks={r["affiliate_clicks"]}, conv={r["conversions"]}, rev={r["commission_eur"]}')

print()
print("=== SUBSCRIBERS ===")
for r in conn.execute('SELECT COUNT(*) as c FROM subscribers'):
    print(f'  Total: {r["c"]}')

print()
print("=== RECENT CLICKS (last 20) ===")
for r in conn.execute('SELECT timestamp, affiliate_program, article_slug, utm_source, utm_medium FROM clicks ORDER BY timestamp DESC LIMIT 20'):
    print(f'  {r["timestamp"][:19]} | {r["affiliate_program"]} | {r["article_slug"]} | {r["utm_source"]}/{r["utm_medium"]}')

conn.close()