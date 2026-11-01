#!/usr/bin/env python3
import sqlite3

DB_PATH = "tracking.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# Check tables
print("=== TABLES ===")
for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'"):
    print(f'  {r["name"]}')

print()
print("=== CLICKS ===")
for r in conn.execute('SELECT * FROM clicks ORDER BY timestamp DESC'):
    print(f'  {r["timestamp"]} | {r["affiliate_program"]} | {r["article_slug"]} | {r["utm_source"]}/{r["utm_medium"]} | {r["ip_hash"]}')

print()
print("=== CONVERSIONS ===")
for r in conn.execute('SELECT * FROM conversions'):
    print(f'  {r["timestamp"]} | {r["affiliate_program"]} | click_id={r["click_id"]} | {r["amount_eur"]}€ | {r["commission_eur"]}€ | {r["status"]}')

print()
print("=== DAILY STATS ===")
for r in conn.execute('SELECT * FROM daily_stats'):
    print(f'  {r}')

conn.close()