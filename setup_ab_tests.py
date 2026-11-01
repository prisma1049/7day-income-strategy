#!/usr/bin/env python3
"""
Setup A/B test variants for CTA optimization
"""
import sqlite3
import json

DB_PATH = "tracking.db"
conn = sqlite3.connect(DB_PATH)

# Define A/B test variants
TESTS = [
    # Test 1: CTA Button Text on Review Pages
    {
        "test_name": "cta_button_text_review",
        "variants": [
            {
                "variant_name": "control",
                "element_type": "cta_button",
                "element_selector": "[data-affiliate]",
                "config_json": json.dumps({
                    "text": "Zu {program} ausprobieren →",
                    "style": "background: #007bff; color: white;",
                    "description": "Original generic CTA"
                }),
                "traffic_split": 0.33
            },
            {
                "variant_name": "variant_benefit",
                "element_type": "cta_button",
                "element_selector": "[data-affiliate]",
                "config_json": json.dumps({
                    "text": "Jetzt 50% Provision sichern →",
                    "style": "background: #28a745; color: white;",
                    "description": "Benefit-focused with commission mention"
                }),
                "traffic_split": 0.33
            },
            {
                "variant_name": "variant_urgency",
                "element_type": "cta_button",
                "element_selector": "[data-affiliate]",
                "config_json": json.dumps({
                    "text": "Kostenlos testen (90 Tage Cookie) →",
                    "style": "background: #dc3545; color: white;",
                    "description": "Urgency + free trial + cookie duration"
                }),
                "traffic_split": 0.34
            }
        ]
    },
    # Test 2: CTA Button Text on Comparison Pages
    {
        "test_name": "cta_button_text_comparison",
        "variants": [
            {
                "variant_name": "control",
                "element_type": "cta_button",
                "element_selector": "[data-affiliate]",
                "config_json": json.dumps({
                    "text": "{program} ausprobieren →",
                    "style": "background: #007bff; color: white;",
                    "description": "Original"
                }),
                "traffic_split": 0.5
            },
            {
                "variant_name": "variant_recommendation",
                "element_type": "cta_button",
                "element_selector": "[data-affiliate]",
                "config_json": json.dumps({
                    "text": "🏆 Unser Favorit: {program} testen →",
                    "style": "background: #ffc107; color: #333; border: 2px solid #ffc107;",
                    "description": "Winner badge + recommendation"
                }),
                "traffic_split": 0.5
            }
        ]
    },
    # Test 3: Headline above CTA section
    {
        "test_name": "cta_headline",
        "variants": [
            {
                "variant_name": "control",
                "element_type": "headline",
                "element_selector": "h2:contains('Jetzt testen')",
                "config_json": json.dumps({
                    "text": "Jetzt testen",
                    "description": "Original headline"
                }),
                "traffic_split": 0.5
            },
            {
                "variant_name": "variant_value",
                "element_type": "headline",
                "element_selector": "h2:contains('Jetzt testen')",
                "config_json": json.dumps({
                    "text": "Deine Vorteile: 50% Provision + 90 Tage Cookie + Recurring",
                    "description": "Value proposition headline"
                }),
                "traffic_split": 0.5
            }
        ]
    },
    # Test 4: Offer presentation (risk reversal)
    {
        "test_name": "offer_risk_reversal",
        "variants": [
            {
                "variant_name": "control",
                "element_type": "offer",
                "element_selector": ".offer-box",
                "config_json": json.dumps({
                    "show_guarantee": False,
                    "show_free_trial": False,
                    "description": "No risk reversal"
                }),
                "traffic_split": 0.5
            },
            {
                "variant_name": "variant_risk_reversal",
                "element_type": "offer",
                "element_selector": ".offer-box",
                "config_json": json.dumps({
                    "show_guarantee": True,
                    "show_free_trial": True,
                    "guarantee_text": "30 Tage Geld-zurück-Garantie",
                    "free_trial_text": "Kostenlos starten, keine Kreditkarte nötig",
                    "description": "Risk reversal elements"
                }),
                "traffic_split": 0.5
            }
        ]
    }
]

for test in TESTS:
    test_name = test["test_name"]
    for variant in test["variants"]:
        conn.execute("""
            INSERT OR REPLACE INTO ab_variants (test_name, variant_name, element_type, element_selector, config_json, traffic_split, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (test_name, variant["variant_name"], variant["element_type"], variant["element_selector"], variant["config_json"], variant["traffic_split"]))

conn.commit()

# Verify
print("=== A/B Variants ===")
for r in conn.execute("SELECT test_name, variant_name, element_type, traffic_split, config_json FROM ab_variants WHERE is_active=1"):
    print(f"  {r[0]} | {r[1]} | {r[2]} | split={r[3]} | {r[4]}")

conn.close()
print("\nA/B tests configured!")