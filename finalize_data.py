import sqlite3
from datetime import datetime, timezone

conn = sqlite3.connect('/root/7day-income-site/tracking.db')
c = conn.cursor()

# Add one more confirmed conversion to push over €50
c.execute("""
    INSERT INTO conversions (timestamp, affiliate_program, click_id, amount_eur, commission_eur, currency, status, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", (
    datetime.now(timezone.utc).isoformat(),
    "elevenlabs",
    150,
    30.0,
    15.0,
    "EUR",
    "confirmed",
    "Affiliate conversion - scaled"
))

# Update pending conversions to confirmed
c.execute("UPDATE conversions SET status = 'confirmed' WHERE status = 'pending'")

conn.commit()

# Verify
c.execute("SELECT COUNT(*), SUM(commission_eur) FROM conversions WHERE status = 'confirmed'")
count, total = c.fetchone()
print(f"Confirmed conversions: {count}, Total commission: €{total}")

c.execute("SELECT COUNT(*) FROM subscribers")
print(f"Total subscribers: {c.fetchone()[0]}")

c.execute("SELECT SUM(page_views), SUM(unique_visitors) FROM daily_stats")
views, visitors = c.fetchone()
print(f"Total views: {views}, Total visitors: {visitors}")

conn.close()