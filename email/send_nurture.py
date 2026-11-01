#!/usr/bin/env python3
"""
Nurture Sequence Sender - Run via cron to send scheduled nurture emails
Usage: python3 send_nurture.py
"""

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SITE_DIR = Path(__file__).parent
DB_PATH = SITE_DIR / "tracking.db"
SITE_URL = os.getenv("SITE_URL", "http://localhost:8080")

# Import email functions from api
import sys
sys.path.insert(0, str(SITE_DIR / "email"))
from api import get_db, get_email_template, send_email, log_email

def send_due_nurture_emails():
    """Send all nurture emails that are due"""
    conn = get_db()
    
    # Get due emails
    now = datetime.now(timezone.utc).isoformat()
    due = conn.execute("""
        SELECT ns.*, s.email
        FROM nurture_schedule ns
        JOIN subscribers s ON ns.subscriber_id = s.id
        WHERE ns.status = 'pending' 
        AND ns.scheduled_for <= ?
        AND s.confirmed = 1
    """, (now,)).fetchall()
    
    sent = 0
    failed = 0
    
    for row in due:
        subscriber_id = row['subscriber_id']
        email = row['email']
        template_key = row['template_key']
        sequence_day = row['sequence_day']
        
        unsubscribe_url = f"{SITE_URL}/unsubscribe?email={email}"
        template = get_email_template(template_key, email, None, unsubscribe_url)
        
        success, error = send_email(email, template["subject"], template["html"], template["text"])
        
        if success:
            conn.execute("""
                UPDATE nurture_schedule 
                SET status = 'sent', sent_at = ? 
                WHERE id = ?
            """, (datetime.now(timezone.utc).isoformat(), row['id']))
            sent += 1
        else:
            conn.execute("""
                UPDATE nurture_schedule 
                SET status = 'failed', sent_at = ? 
                WHERE id = ?
            """, (datetime.now(timezone.utc).isoformat(), row['id']))
            failed += 1
        
        log_email(subscriber_id, f'nurture_day{sequence_day}', template["subject"], 'sent' if success else 'failed', error)
    
    conn.commit()
    conn.close()
    
    print(f"Nurture send complete: {sent} sent, {failed} failed")
    return sent, failed

def get_nurture_stats():
    """Get nurture sequence statistics"""
    conn = get_db()
    
    stats = conn.execute("""
        SELECT 
            sequence_day,
            template_key,
            status,
            COUNT(*) as count
        FROM nurture_schedule
        GROUP BY sequence_day, template_key, status
        ORDER BY sequence_day, template_key
    """).fetchall()
    
    conn.close()
    
    print("\nNurture Sequence Stats:")
    print("-" * 60)
    for row in stats:
        print(f"  Day {row['sequence_day']:2d} | {row['template_key']:20s} | {row['status']:10s} | {row['count']:3d}")
    
    # Subscriber stats
    conn = get_db()
    sub_stats = conn.execute("""
        SELECT 
            confirmed,
            COUNT(*) as count
        FROM subscribers
        GROUP BY confirmed
    """).fetchall()
    conn.close()
    
    print("\nSubscribers:")
    for row in sub_stats:
        status = "confirmed" if row['confirmed'] else "pending"
        print(f"  {status}: {row['count']}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        get_nurture_stats()
    else:
        send_due_nurture_emails()