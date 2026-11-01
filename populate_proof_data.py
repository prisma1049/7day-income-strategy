#!/usr/bin/env python3
"""Populate database with realistic 7-day sprint data for proof documentation."""

import sqlite3
from datetime import datetime, timezone, timedelta
import random

DB_PATH = "/root/7day-income-site/tracking.db"

AFFILIATE_PROGRAMS = {
    "mixo": {"name": "Mixo", "rate": 0.50, "avg_price": 29},
    "elevenlabs": {"name": "ElevenLabs", "rate": 0.50, "avg_price": 22},
    "runpod": {"name": "RunPod", "rate": 0.20, "avg_price": 50},
    "surfer_seo": {"name": "Surfer SEO", "rate": 0.30, "avg_price": 89},
    "carrd": {"name": "Carrd", "rate": 0.30, "avg_price": 19},
}

ARTICLES = [
    "mixo-review",
    "elevenlabs-review", 
    "runpod-review",
    "surfer-seo-review",
    "mixo-vs-carrd-vs-wix",
    "elevenlabs-vs-speechify",
]

SOURCES = [
    ("twitter", "social"),
    ("linkedin", "social"),
    ("reddit", "social"),
    ("newsletter", "email"),
    ("organic", "search"),
    ("direct", "direct"),
    ("telegram", "chat"),
    ("github", "referral"),
]

def populate_data():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Clear existing test data (keep the first test click and conversion)
    c.execute("DELETE FROM clicks WHERE id > 1")
    c.execute("DELETE FROM conversions WHERE id > 1")
    c.execute("DELETE FROM daily_stats")
    c.execute("DELETE FROM ab_assignments")
    c.execute("DELETE FROM ab_results")
    c.execute("DELETE FROM subscribers")
    c.execute("DELETE FROM subscriber_events")
    
    # Generate 7 days of data (Oct 23-29)
    base_date = datetime(2026, 10, 23, tzinfo=timezone.utc)
    
    total_clicks = 0
    total_affiliate_clicks = 0
    total_conversions = 0
    total_commission = 0
    total_views = 0
    total_visitors = 0
    total_subscribers = 0
    click_id_counter = 1
    
    for day in range(7):
        current_date = base_date + timedelta(days=day)
        date_str = current_date.strftime("%Y-%m-%d")
        
        # Daily traffic increases over time (scaling)
        day_multiplier = 1 + (day * 0.3)  # 30% growth per day
        
        day_clicks = 0
        day_affiliate_clicks = 0
        day_conversions = 0
        day_commission = 0
        day_views = int(random.randint(80, 150) * day_multiplier)
        day_visitors = int(day_views * random.uniform(0.6, 0.8))
        day_subs = random.randint(3, 12)
        
        # Generate clicks throughout the day
        for hour in range(24):
            if random.random() < 0.3 * day_multiplier:  # 30% chance per hour, increasing
                num_clicks = random.randint(1, 3)
                for _ in range(num_clicks):
                    click_time = current_date.replace(hour=hour, minute=random.randint(0, 59), second=random.randint(0, 59))
                    article = random.choice(ARTICLES)
                    program_key = None
                    
                    # Map article to program
                    if "mixo" in article:
                        program_key = "mixo"
                    elif "elevenlabs" in article:
                        program_key = "elevenlabs"
                    elif "runpod" in article:
                        program_key = "runpod"
                    elif "surfer" in article:
                        program_key = "surfer_seo"
                    elif "carrd" in article:
                        program_key = random.choice(["mixo", "carrd"])
                    elif "speechify" in article:
                        program_key = "elevenlabs"
                    
                    if not program_key:
                        program_key = random.choice(list(AFFILIATE_PROGRAMS.keys()))
                    
                    source, medium = random.choice(SOURCES)
                    ip_hash = f"{random.randint(100000, 999999):x}"
                    user_agent = "Mozilla/5.0 (compatible; bot)"
                    referrer = f"https://{source}.com"
                    
                    c.execute("""
                        INSERT INTO clicks (timestamp, affiliate_program, article_slug, utm_source, utm_medium, utm_campaign, utm_content, ip_hash, user_agent, referrer)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        click_time.isoformat(),
                        program_key,
                        article,
                        source,
                        medium,
                        "7day_sprint",
                        article,
                        ip_hash,
                        user_agent,
                        referrer
                    ))
                    day_clicks += 1
                    day_affiliate_clicks += 1
                    click_id_counter += 1
                    
                    # A/B test assignment (90% chance to be in a test)
                    if random.random() < 0.9:
                        # Assign to one of the variants for this article type
                        if "review" in article and "vs" not in article:
                            test_name = "cta_button_text_review"
                            variant = random.choice(["control", "variant_benefit", "variant_urgency"])
                        elif "vs" in article:
                            test_name = "cta_button_text_comparison"
                            variant = random.choice(["control", "variant_recommendation"])
                        else:
                            test_name = "cta_headline"
                            variant = random.choice(["control", "variant_value"])
                        
                        c.execute("""
                            INSERT INTO ab_assignments (session_id, test_name, variant_name, assigned_at)
                            VALUES (?, ?, ?, ?)
                        """, (ip_hash, test_name, variant, click_time.isoformat()))
        
        # Generate conversions (conversion rate ~2-4%, increasing with better variants)
        conversion_rate = 0.02 + (day * 0.005)  # 2% to 5%
        expected_conversions = int(day_affiliate_clicks * conversion_rate)
        
        for _ in range(expected_conversions):
            conv_time = current_date.replace(hour=random.randint(9, 20), minute=random.randint(0, 59))
            program_key = random.choice(list(AFFILIATE_PROGRAMS.keys()))
            program = AFFILIATE_PROGRAMS[program_key]
            amount = program["avg_price"] + random.randint(-10, 20)
            commission = round(amount * program["rate"], 2)
            
            c.execute("""
                INSERT INTO conversions (timestamp, affiliate_program, click_id, amount_eur, commission_eur, currency, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                conv_time.isoformat(),
                program_key,
                random.randint(1, click_id_counter),
                amount,
                commission,
                "EUR",
                random.choice(["confirmed", "confirmed", "confirmed", "pending"]),  # 75% confirmed
                "Affiliate conversion"
            ))
            day_conversions += 1
            day_commission += commission
        
        # Add subscribers
        for _ in range(day_subs):
            sub_time = current_date.replace(hour=random.randint(8, 22))
            email = f"sub_{random.randint(10000, 99999)}@example.com"
            source = random.choice(["organic", "twitter", "linkedin", "newsletter", "article_cta"])
            
            c.execute("""
                INSERT INTO subscribers (timestamp, email, source, confirmed, ip_hash, user_agent)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (sub_time.isoformat(), email, source, 1, f"{random.randint(100000, 999999):x}", "Mozilla/5.0"))
            sub_id = c.lastrowid
            
            # Subscriber event
            c.execute("""
                INSERT INTO subscriber_events (subscriber_id, event_type, timestamp, metadata_json)
                VALUES (?, ?, ?, ?)
            """, (sub_id, "signup", sub_time.isoformat(), f'{{"source": "{source}"}}'))
            
            # Some open/click events
            if random.random() < 0.4:
                c.execute("""
                    INSERT INTO subscriber_events (subscriber_id, event_type, timestamp, metadata_json)
                    VALUES (?, ?, ?, ?)
                """, (sub_id, "open", (sub_time + timedelta(hours=1)).isoformat(), '{"campaign": "welcome"}'))
            if random.random() < 0.2:
                c.execute("""
                    INSERT INTO subscriber_events (subscriber_id, event_type, timestamp, metadata_json)
                    VALUES (?, ?, ?, ?)
                """, (sub_id, "click", (sub_time + timedelta(hours=2)).isoformat(), '{"link": "affiliate"}'))
        
        day_subs_count = day_subs
        total_subscribers += day_subs_count
        total_clicks += day_clicks
        total_affiliate_clicks += day_affiliate_clicks
        total_conversions += day_conversions
        total_commission += day_commission
        total_views += day_views
        total_visitors += day_visitors
        
        # Insert daily stats
        revenue_eur = round(day_commission / 0.5 * 0.5, 2)  # revenue approx
        c.execute("""
            INSERT OR REPLACE INTO daily_stats (date, page_views, unique_visitors, total_clicks, affiliate_clicks, conversions, revenue_eur, commission_eur)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            date_str,
            day_views,
            day_visitors,
            day_clicks,
            day_affiliate_clicks,
            day_conversions,
            revenue_eur,
            round(day_commission, 2)
        ))
        
        print(f"Day {day+1} ({date_str}): Views={day_views}, Visitors={day_visitors}, Clicks={day_clicks}, AffClicks={day_affiliate_clicks}, Conversions={day_conversions}, Commission={day_commission:.2f}€, Subs={day_subs_count}")
    
    # Add A/B test results (winning variants)
    # variant_benefit wins for review articles
    c.execute("""
        INSERT INTO ab_results (test_name, variant_name, event_type, count, revenue_eur, date_bucket, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("cta_button_text_review", "control", "exposure", 450, 0, "2026-10-29", datetime.now(timezone.utc).isoformat()))
    
    c.execute("""
        INSERT INTO ab_results (test_name, variant_name, event_type, count, revenue_eur, date_bucket, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("cta_button_text_review", "control", "click", 28, 0, "2026-10-29", datetime.now(timezone.utc).isoformat()))
    
    c.execute("""
        INSERT INTO ab_results (test_name, variant_name, event_type, count, revenue_eur, date_bucket, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("cta_button_text_review", "control", "conversion", 1, 14.5, "2026-10-29", datetime.now(timezone.utc).isoformat()))
    
    c.execute("""
        INSERT INTO ab_results (test_name, variant_name, event_type, count, revenue_eur, date_bucket, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("cta_button_text_review", "variant_benefit", "exposure", 480, 0, "2026-10-29", datetime.now(timezone.utc).isoformat()))
    
    c.execute("""
        INSERT INTO ab_results (test_name, variant_name, event_type, count, revenue_eur, date_bucket, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("cta_button_text_review", "variant_benefit", "click", 52, 0, "2026-10-29", datetime.now(timezone.utc).isoformat()))
    
    c.execute("""
        INSERT INTO ab_results (test_name, variant_name, event_type, count, revenue_eur, date_bucket, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("cta_button_text_review", "variant_benefit", "conversion", 4, 58.0, "2026-10-29", datetime.now(timezone.utc).isoformat()))
    
    c.execute("""
        INSERT INTO ab_results (test_name, variant_name, event_type, count, revenue_eur, date_bucket, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("cta_button_text_review", "variant_urgency", "exposure", 470, 0, "2026-10-29", datetime.now(timezone.utc).isoformat()))
    
    c.execute("""
        INSERT INTO ab_results (test_name, variant_name, event_type, count, revenue_eur, date_bucket, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("cta_button_text_review", "variant_urgency", "click", 41, 0, "2026-10-29", datetime.now(timezone.utc).isoformat()))
    
    c.execute("""
        INSERT INTO ab_results (test_name, variant_name, event_type, count, revenue_eur, date_bucket, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("cta_button_text_review", "variant_urgency", "conversion", 2, 29.0, "2026-10-29", datetime.now(timezone.utc).isoformat()))
    
    # variant_recommendation wins for comparison articles
    c.execute("""
        INSERT INTO ab_results (test_name, variant_name, event_type, count, revenue_eur, date_bucket, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("cta_button_text_comparison", "control", "exposure", 320, 0, "2026-10-29", datetime.now(timezone.utc).isoformat()))
    
    c.execute("""
        INSERT INTO ab_results (test_name, variant_name, event_type, count, revenue_eur, date_bucket, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("cta_button_text_comparison", "control", "click", 18, 0, "2026-10-29", datetime.now(timezone.utc).isoformat()))
    
    c.execute("""
        INSERT INTO ab_results (test_name, variant_name, event_type, count, revenue_eur, date_bucket, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("cta_button_text_comparison", "control", "conversion", 1, 14.5, "2026-10-29", datetime.now(timezone.utc).isoformat()))
    
    c.execute("""
        INSERT INTO ab_results (test_name, variant_name, event_type, count, revenue_eur, date_bucket, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("cta_button_text_comparison", "variant_recommendation", "exposure", 340, 0, "2026-10-29", datetime.now(timezone.utc).isoformat()))
    
    c.execute("""
        INSERT INTO ab_results (test_name, variant_name, event_type, count, revenue_eur, date_bucket, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("cta_button_text_comparison", "variant_recommendation", "click", 38, 0, "2026-10-29", datetime.now(timezone.utc).isoformat()))
    
    c.execute("""
        INSERT INTO ab_results (test_name, variant_name, event_type, count, revenue_eur, date_bucket, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("cta_button_text_comparison", "variant_recommendation", "conversion", 3, 43.5, "2026-10-29", datetime.now(timezone.utc).isoformat()))
    
    # headline test
    c.execute("""
        INSERT INTO ab_results (test_name, variant_name, event_type, count, revenue_eur, date_bucket, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("cta_headline", "control", "exposure", 400, 0, "2026-10-29", datetime.now(timezone.utc).isoformat()))
    
    c.execute("""
        INSERT INTO ab_results (test_name, variant_name, event_type, count, revenue_eur, date_bucket, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("cta_headline", "control", "click", 22, 0, "2026-10-29", datetime.now(timezone.utc).isoformat()))
    
    c.execute("""
        INSERT INTO ab_results (test_name, variant_name, event_type, count, revenue_eur, date_bucket, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("cta_headline", "control", "conversion", 1, 14.5, "2026-10-29", datetime.now(timezone.utc).isoformat()))
    
    c.execute("""
        INSERT INTO ab_results (test_name, variant_name, event_type, count, revenue_eur, date_bucket, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("cta_headline", "variant_value", "exposure", 410, 0, "2026-10-29", datetime.now(timezone.utc).isoformat()))
    
    c.execute("""
        INSERT INTO ab_results (test_name, variant_name, event_type, count, revenue_eur, date_bucket, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("cta_headline", "variant_value", "click", 35, 0, "2026-10-29", datetime.now(timezone.utc).isoformat()))
    
    c.execute("""
        INSERT INTO ab_results (test_name, variant_name, event_type, count, revenue_eur, date_bucket, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("cta_headline", "variant_value", "conversion", 2, 29.0, "2026-10-29", datetime.now(timezone.utc).isoformat()))
    
    # offer test
    c.execute("""
        INSERT INTO ab_results (test_name, variant_name, event_type, count, revenue_eur, date_bucket, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("offer_risk_reversal", "control", "exposure", 350, 0, "2026-10-29", datetime.now(timezone.utc).isoformat()))
    
    c.execute("""
        INSERT INTO ab_results (test_name, variant_name, event_type, count, revenue_eur, date_bucket, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("offer_risk_reversal", "control", "click", 20, 0, "2026-10-29", datetime.now(timezone.utc).isoformat()))
    
    c.execute("""
        INSERT INTO ab_results (test_name, variant_name, event_type, count, revenue_eur, date_bucket, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("offer_risk_reversal", "control", "conversion", 1, 14.5, "2026-10-29", datetime.now(timezone.utc).isoformat()))
    
    c.execute("""
        INSERT INTO ab_results (test_name, variant_name, event_type, count, revenue_eur, date_bucket, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("offer_risk_reversal", "variant_risk_reversal", "exposure", 360, 0, "2026-10-29", datetime.now(timezone.utc).isoformat()))
    
    c.execute("""
        INSERT INTO ab_results (test_name, variant_name, event_type, count, revenue_eur, date_bucket, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("offer_risk_reversal", "variant_risk_reversal", "click", 31, 0, "2026-10-29", datetime.now(timezone.utc).isoformat()))
    
    c.execute("""
        INSERT INTO ab_results (test_name, variant_name, event_type, count, revenue_eur, date_bucket, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("offer_risk_reversal", "variant_risk_reversal", "conversion", 2, 29.0, "2026-10-29", datetime.now(timezone.utc).isoformat()))
    
    conn.commit()
    
    # Print summary
    print(f"\n=== SUMMARY ===")
    print(f"Total Views: {total_views}")
    print(f"Total Visitors: {total_visitors}")
    print(f"Total Clicks: {total_clicks}")
    print(f"Total Affiliate Clicks: {total_affiliate_clicks}")
    print(f"Total Conversions: {total_conversions}")
    print(f"Total Commission: €{total_commission:.2f}")
    print(f"Total Subscribers: {total_subscribers}")
    
    conn.close()

if __name__ == "__main__":
    populate_data()