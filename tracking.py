#!/usr/bin/env python3
"""
Tracking Database for 7-Day Revenue Sprint
Stores clicks, conversions, revenue data for affiliate tracking
"""

import sqlite3
import os
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "tracking.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS clicks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    affiliate_program TEXT NOT NULL,
    article_slug TEXT NOT NULL,
    utm_source TEXT,
    utm_medium TEXT,
    utm_campaign TEXT,
    utm_content TEXT,
    ip_hash TEXT,
    user_agent TEXT,
    referrer TEXT
);

CREATE TABLE IF NOT EXISTS conversions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    affiliate_program TEXT NOT NULL,
    click_id INTEGER,
    amount_eur REAL,
    commission_eur REAL,
    currency TEXT DEFAULT 'EUR',
    status TEXT DEFAULT 'pending',
    notes TEXT,
    FOREIGN KEY (click_id) REFERENCES clicks(id)
);

CREATE TABLE IF NOT EXISTS daily_stats (
    date TEXT PRIMARY KEY,
    page_views INTEGER DEFAULT 0,
    unique_visitors INTEGER DEFAULT 0,
    total_clicks INTEGER DEFAULT 0,
    affiliate_clicks INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    revenue_eur REAL DEFAULT 0,
    commission_eur REAL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_clicks_timestamp ON clicks(timestamp);
CREATE INDEX IF NOT EXISTS idx_clicks_program ON clicks(affiliate_program);
CREATE INDEX IF NOT EXISTS idx_clicks_article ON clicks(article_slug);
CREATE INDEX IF NOT EXISTS idx_conversions_timestamp ON conversions(timestamp);
CREATE INDEX IF NOT EXISTS idx_conversions_program ON conversions(affiliate_program);
"""

AFFILIATE_PROGRAMS = {
    "mixo": {
        "name": "Mixo",
        "commission_rate": 0.50,
        "cookie_days": 90,
        "base_url": "https://mixo.io",
        "affiliate_param": "ref",
        "description": "AI Website Builder - 50% commission, 90-day cookie"
    },
    "elevenlabs": {
        "name": "ElevenLabs",
        "commission_rate": 0.50,
        "cookie_days": 90,
        "base_url": "https://elevenlabs.io",
        "affiliate_param": "via",
        "description": "AI Voice/TTS - 50% recurring commission"
    },
    "runpod": {
        "name": "RunPod",
        "commission_rate": 0.20,
        "cookie_days": 60,
        "base_url": "https://runpod.io",
        "affiliate_param": "ref",
        "description": "GPU Cloud - 20% recurring for developers"
    },
    "surfer_seo": {
        "name": "Surfer SEO",
        "commission_rate": 0.30,
        "cookie_days": 90,
        "base_url": "https://surferseo.com",
        "affiliate_param": "ref",
        "description": "SEO Content Optimization - 30% recurring"
    },
    "carrd": {
        "name": "Carrd",
        "commission_rate": 0.30,
        "cookie_days": 30,
        "base_url": "https://carrd.co",
        "affiliate_param": "ref",
        "description": "Simple Sites - 30% commission"
    },
    "vast_ai": {
        "name": "Vast.ai",
        "commission_rate": 0.10,
        "cookie_days": 30,
        "base_url": "https://vast.ai",
        "affiliate_param": "ref",
        "description": "GPU Marketplace - 10% commission"
    }
}

ARTICLE_SLUGS = {
    "mixo-review.html": "mixo",
    "elevenlabs-review.html": "elevenlabs",
    "runpod-review.html": "runpod",
    "surfer-seo-review.html": "surfer_seo",
    "mixo-vs-carrd-vs-wix.html": "mixo_carrd_comparison",
    "elevenlabs-vs-speechify.html": "elevenlabs_speechify_comparison",
    "runpod-review.html": "runpod_vast_comparison",
}

def init_db():
    """Initialize the tracking database."""
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

def generate_affiliate_url(program_key: str, article_slug: str, utm_source: str = "organic", utm_medium: str = "article", utm_campaign: str = "7day_sprint", utm_content: str = "") -> str:
    """Generate a tracked affiliate URL with UTM parameters."""
    if program_key not in AFFILIATE_PROGRAMS:
        raise ValueError(f"Unknown affiliate program: {program_key}")
    
    program = AFFILIATE_PROGRAMS[program_key]
    base = program["base_url"]
    param = program["affiliate_param"]
    
    # Build UTM parameters
    utm_params = {
        "utm_source": utm_source,
        "utm_medium": utm_medium,
        "utm_campaign": utm_campaign,
    }
    if utm_content:
        utm_params["utm_content"] = utm_content
    elif article_slug:
        utm_params["utm_content"] = article_slug
    
    # Add affiliate parameter
    utm_params[param] = "7day_sprint"
    
    # Build URL
    from urllib.parse import urlencode
    query = urlencode(utm_params)
    return f"{base}?{query}"

def log_click(program_key: str, article_slug: str, utm_source: str = "", utm_medium: str = "", utm_campaign: str = "", utm_content: str = "", ip_hash: str = "", user_agent: str = "", referrer: str = ""):
    """Log an affiliate click."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO clicks (timestamp, affiliate_program, article_slug, utm_source, utm_medium, utm_campaign, utm_content, ip_hash, user_agent, referrer)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now(timezone.utc).isoformat(),
        program_key,
        article_slug,
        utm_source,
        utm_medium,
        utm_campaign,
        utm_content,
        ip_hash,
        user_agent,
        referrer
    ))
    conn.commit()
    click_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return click_id

def log_conversion(program_key: str, click_id: int, amount_eur: float, commission_eur: float = None, status: str = "pending", notes: str = ""):
    """Log a conversion/sale."""
    if commission_eur is None:
        commission_eur = amount_eur * AFFILIATE_PROGRAMS[program_key]["commission_rate"]
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO conversions (timestamp, affiliate_program, click_id, amount_eur, commission_eur, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now(timezone.utc).isoformat(),
        program_key,
        click_id,
        amount_eur,
        commission_eur,
        status,
        notes
    ))
    conn.commit()
    conn.close()

def get_dashboard_data():
    """Get aggregated data for dashboard."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Total clicks by program
    clicks_by_program = conn.execute("""
        SELECT affiliate_program, COUNT(*) as clicks
        FROM clicks
        GROUP BY affiliate_program
    """).fetchall()
    
    # Total conversions by program
    conversions_by_program = conn.execute("""
        SELECT affiliate_program, COUNT(*) as conversions, SUM(commission_eur) as total_commission
        FROM conversions
        WHERE status = 'confirmed'
        GROUP BY affiliate_program
    """).fetchall()
    
    # Daily stats for last 7 days
    daily = conn.execute("""
        SELECT * FROM daily_stats
        ORDER BY date DESC
        LIMIT 7
    """).fetchall()
    
    # Recent clicks (last 50)
    recent_clicks = conn.execute("""
        SELECT * FROM clicks
        ORDER BY timestamp DESC
        LIMIT 50
    """).fetchall()
    
    # Recent conversions
    recent_conversions = conn.execute("""
        SELECT * FROM conversions
        ORDER BY timestamp DESC
        LIMIT 20
    """).fetchall()
    
    conn.close()
    
    return {
        "clicks_by_program": [dict(r) for r in clicks_by_program],
        "conversions_by_program": [dict(r) for r in conversions_by_program],
        "daily_stats": [dict(r) for r in daily],
        "recent_clicks": [dict(r) for r in recent_clicks],
        "recent_conversions": [dict(r) for r in recent_conversions],
    }

def update_daily_stats():
    """Update daily aggregated stats."""
    conn = sqlite3.connect(DB_PATH)
    today = datetime.now(timezone.utc).date().isoformat()
    
    # Page views would come from server logs - placeholder
    # For now, compute from clicks
    stats = conn.execute("""
        SELECT 
            COUNT(DISTINCT date(timestamp)) as days,
            COUNT(*) as total_clicks,
            SUM(CASE WHEN affiliate_program IN ('mixo', 'elevenlabs', 'runpod', 'surfer_seo', 'carrd', 'vast_ai') THEN 1 ELSE 0 END) as affiliate_clicks
        FROM clicks
        WHERE date(timestamp) = ?
    """, (today,)).fetchone()
    
    conv_stats = conn.execute("""
        SELECT 
            COUNT(*) as conversions,
            SUM(commission_eur) as commission_eur
        FROM conversions
        WHERE date(timestamp) = ? AND status = 'confirmed'
    """, (today,)).fetchone()
    
    page_views = stats[0] * 10 if stats[0] else 0  # rough estimate
    unique_visitors = stats[0] * 5 if stats[0] else 0
    
    conn.execute("""
        INSERT OR REPLACE INTO daily_stats (date, page_views, unique_visitors, total_clicks, affiliate_clicks, conversions, revenue_eur, commission_eur)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        today,
        page_views,
        unique_visitors,
        stats[2] or 0,
        stats[3] or 0,
        conv_stats[0] or 0,
        conv_stats[1] or 0,
        conv_stats[1] or 0
    ))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Affiliate Programs:")
    for key, prog in AFFILIATE_PROGRAMS.items():
        print(f"  {key}: {prog['name']} - {prog['description']}")
    
    print("\nGenerating sample affiliate URLs:")
    for article, slug in ARTICLE_SLUGS.items():
        for prog_key in ["mixo", "elevenlabs", "runpod"]:
            url = generate_affiliate_url(prog_key, slug)
            print(f"  {article} -> {prog_key}: {url}")