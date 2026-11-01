#!/usr/bin/env python3
"""
Migration script: Add A/B testing tables and subscriber table to tracking.db
"""
import sqlite3

DB_PATH = "tracking.db"
conn = sqlite3.connect(DB_PATH)

# Add A/B testing tables
MIGRATION_SQL = """
-- A/B Test Variants
CREATE TABLE IF NOT EXISTS ab_variants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_name TEXT NOT NULL,
    variant_name TEXT NOT NULL,  -- 'control', 'variant_a', 'variant_b', etc.
    element_type TEXT NOT NULL,  -- 'cta_button', 'cta_text', 'headline', 'offer'
    element_selector TEXT,       -- CSS selector for the element
    config_json TEXT NOT NULL,   -- JSON config for this variant
    traffic_split REAL DEFAULT 0.5,  -- percentage of traffic (0-1)
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(test_name, variant_name)
);

-- A/B Test Assignments (which variant a user sees)
CREATE TABLE IF NOT EXISTS ab_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    test_name TEXT NOT NULL,
    variant_name TEXT NOT NULL,
    assigned_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(session_id, test_name)
);

-- A/B Test Results
CREATE TABLE IF NOT EXISTS ab_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_name TEXT NOT NULL,
    variant_name TEXT NOT NULL,
    event_type TEXT NOT NULL,  -- 'impression', 'click', 'conversion'
    count INTEGER DEFAULT 1,
    revenue_eur REAL DEFAULT 0,
    date_bucket TEXT NOT NULL,  -- YYYY-MM-DD for daily aggregation
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(test_name, variant_name, event_type, date_bucket)
);

-- Subscribers table (was missing)
CREATE TABLE IF NOT EXISTS subscribers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    source TEXT,
    utm_source TEXT,
    utm_medium TEXT,
    utm_campaign TEXT,
    utm_content TEXT,
    confirmed INTEGER DEFAULT 0,
    confirmation_token TEXT,
    ip_hash TEXT,
    user_agent TEXT
);

CREATE INDEX IF NOT EXISTS idx_subscribers_email ON subscribers(email);
CREATE INDEX IF NOT EXISTS idx_subscribers_timestamp ON subscribers(timestamp);
CREATE INDEX IF NOT EXISTS idx_subscribers_token ON subscribers(confirmation_token);

-- Subscriber events for tracking
CREATE TABLE IF NOT EXISTS subscriber_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscriber_id INTEGER,
    event_type TEXT NOT NULL,  -- 'signup', 'confirm', 'unsubscribe', 'email_open', 'email_click'
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    metadata_json TEXT,
    FOREIGN KEY (subscriber_id) REFERENCES subscribers(id)
);

CREATE INDEX IF NOT EXISTS idx_subscriber_events_sub ON subscriber_events(subscriber_id);
CREATE INDEX IF NOT EXISTS idx_subscriber_events_type ON subscriber_events(event_type);
"""

conn.executescript(MIGRATION_SQL)
conn.commit()

# Verify tables
for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
    print(f"Table: {r[0]}")

conn.close()
print("Migration complete!")