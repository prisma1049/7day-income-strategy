#!/usr/bin/env python3
"""Initialize email tables in tracking database."""
import sqlite3
import os

DB_PATH = '/root/7day-income-site/tracking.db'

def init_email_tables():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Add lead_magnet column to existing subscribers table
    # Check if column already exists
    cursor.execute("PRAGMA table_info(subscribers)")
    columns = [row[1] for row in cursor.fetchall()]
    print("Current subscribers columns:", columns)
    
    if 'lead_magnet' not in columns:
        cursor.execute("ALTER TABLE subscribers ADD COLUMN lead_magnet TEXT DEFAULT 'zero-capital-guide'")
        print("Added lead_magnet column to subscribers table")
    else:
        print("lead_magnet column already exists")
    
    # 2. Create email_log table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            subscriber_id INTEGER,
            email_type TEXT NOT NULL,
            subject TEXT,
            status TEXT,
            error TEXT,
            FOREIGN KEY (subscriber_id) REFERENCES subscribers(id)
        )
    """)
    print("Ensured email_log table exists")
    
    # Create index on email_log
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_log_subscriber ON email_log(subscriber_id)")
    print("Created idx_email_log_subscriber index")
    
    # 3. Create nurture_schedule table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nurture_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subscriber_id INTEGER NOT NULL,
            sequence_day INTEGER NOT NULL,
            template_key TEXT NOT NULL,
            scheduled_for TEXT NOT NULL,
            sent_at TEXT,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (subscriber_id) REFERENCES subscribers(id)
        )
    """)
    print("Ensured nurture_schedule table exists")
    
    # Create indexes on nurture_schedule
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_nurture_subscriber ON nurture_schedule(subscriber_id)")
    print("Created idx_nurture_subscriber index")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_nurture_scheduled ON nurture_schedule(scheduled_for)")
    print("Created idx_nurture_scheduled index")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_nurture_status ON nurture_schedule(status)")
    print("Created idx_nurture_status index")
    
    conn.commit()
    conn.close()
    print("\nEmail tables initialization complete.")

if __name__ == '__main__':
    init_email_tables()