#!/usr/bin/env python3
"""
Email Subscription API for 7-Day Income Strategy
Handles lead magnet download, subscription, confirmation, and nurture sequence
"""

import os
import json
import sqlite3
import hashlib
import secrets
import smtplib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler

SITE_DIR = Path(__file__).parent
DB_PATH = SITE_DIR / "tracking.db"

# Email configuration (configure via environment variables)
SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM", "noreply@7day-income.strategy")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

# Site configuration
SITE_URL = os.getenv("SITE_URL", "http://localhost:8080")
LEAD_MAGNET_PATH = SITE_DIR / "lead-magnet" / "index.html"

# Nurture sequence configuration
NURTURE_SEQUENCE = [
    {
        "day": 0,
        "subject": "🎁 Dein Guide: Zero-Capital AI Affiliate Marketing",
        "template": "welcome",
        "trigger": "immediate"
    },
    {
        "day": 1,
        "subject": "Tag 1: Die 3 besten KI-Tools für Affiliate-Start (meine ehrliche Meinung)",
        "template": "day1_tools",
        "trigger": "delayed"
    },
    {
        "day": 3,
        "subject": "Tag 3: Warum die meisten beim Content scheitern (und wie du es besser machst)",
        "template": "day3_content",
        "trigger": "delayed"
    },
    {
        "day": 7,
        "subject": "Wochen-Review: Meine echten Zahlen nach 7 Tagen (transparent)",
        "template": "day7_review",
        "trigger": "delayed"
    },
    {
        "day": 14,
        "subject": "Tag 14: Erste Provisionen? Hier ist mein Skalierungs-Plan",
        "template": "day14_scale",
        "trigger": "delayed"
    },
    {
        "day": 30,
        "subject": "Monat 1: Was funktioniert, was nicht – und der Plan für Monat 2",
        "template": "day30_month1",
        "trigger": "delayed"
    }
]

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_email_tables():
    """Add email-related tables to tracking database"""
    conn = get_db()
    conn.executescript("""
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
        confirmation_token TEXT UNIQUE,
        ip_hash TEXT,
        user_agent TEXT,
        lead_magnet TEXT DEFAULT 'zero-capital-guide'
    );

    CREATE INDEX IF NOT EXISTS idx_subscribers_email ON subscribers(email);
    CREATE INDEX IF NOT EXISTS idx_subscribers_token ON subscribers(confirmation_token);
    CREATE INDEX IF NOT EXISTS idx_subscribers_confirmed ON subscribers(confirmed);

    CREATE TABLE IF NOT EXISTS email_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        subscriber_id INTEGER,
        email_type TEXT NOT NULL,
        subject TEXT,
        status TEXT,
        error TEXT,
        FOREIGN KEY (subscriber_id) REFERENCES subscribers(id)
    );

    CREATE TABLE IF NOT EXISTS nurture_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subscriber_id INTEGER NOT NULL,
        sequence_day INTEGER NOT NULL,
        template_key TEXT NOT NULL,
        scheduled_for TEXT NOT NULL,
        sent_at TEXT,
        status TEXT DEFAULT 'pending',
        FOREIGN KEY (subscriber_id) REFERENCES subscribers(id)
    );

    CREATE INDEX IF NOT EXISTS idx_nurture_subscriber ON nurture_schedule(subscriber_id);
    CREATE INDEX IF NOT EXISTS idx_nurture_scheduled ON nurture_schedule(scheduled_for);
    CREATE INDEX IF NOT EXISTS idx_nurture_status ON nurture_schedule(status);
    """)
    conn.commit()
    conn.close()

def hash_ip(ip):
    return hashlib.sha256(ip.encode()).hexdigest()[:16]

def generate_token():
    return secrets.token_urlsafe(32)

def send_email(to_email, subject, html_content, text_content=None):
    """Send email via SMTP. Returns (success, error_message)"""
    if not SMTP_USER or not SMTP_PASS:
        # Log only mode for development
        print(f"[EMAIL LOG] To: {to_email}, Subject: {subject}")
        print(f"[EMAIL LOG] Content preview: {html_content[:200]}...")
        return True, "Logged (no SMTP configured)"

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_FROM
        msg["To"] = to_email

        if text_content:
            msg.attach(MIMEText(text_content, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            if SMTP_USE_TLS:
                server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

        return True, None
    except Exception as e:
        return False, str(e)

def log_email(subscriber_id, email_type, subject, status, error=None):
    conn = get_db()
    conn.execute("""
        INSERT INTO email_log (timestamp, subscriber_id, email_type, subject, status, error)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (datetime.now(timezone.utc).isoformat(), subscriber_id, email_type, subject, status, error))
    conn.commit()
    conn.close()

def schedule_nurture_sequence(subscriber_id, confirmed_at=None):
    """Schedule nurture emails for a confirmed subscriber"""
    if confirmed_at is None:
        confirmed_at = datetime.now(timezone.utc)
    
    conn = get_db()
    for step in NURTURE_SEQUENCE:
        scheduled = confirmed_at + timedelta(days=step["day"])
        conn.execute("""
            INSERT INTO nurture_schedule (subscriber_id, sequence_day, template_key, scheduled_for, status)
            VALUES (?, ?, ?, ?, 'pending')
        """, (subscriber_id, step["day"], step["template"], scheduled.isoformat()))
    conn.commit()
    conn.close()

def get_email_template(template_key, subscriber_email, confirmation_url=None, unsubscribe_url=None):
    """Get email template by key"""
    templates = {
        "welcome": {
            "subject": "🎁 Dein Guide: Zero-Capital AI Affiliate Marketing",
            "html": f"""
<!DOCTYPE html>
<html><body style="font-family: system-ui, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #007bff 0%, #0056b3 100%); color: white; padding: 30px; border-radius: 12px 12px 0 0;">
        <h1 style="margin: 0; font-size: 1.5rem;">🎁 Dein Guide ist da!</h1>
        <p style="margin: 10px 0 0; opacity: 0.9;">Zero-Capital AI Affiliate Marketing</p>
    </div>
    <div style="background: white; border: 1px solid #e0e0e0; border-top: none; padding: 30px; border-radius: 0 0 12px 12px;">
        <p>Hi,</p>
        <p>danke, dass du dich eingetragen hast! Hier ist dein kostenloser Guide:</p>
        <p style="text-align: center; margin: 30px 0;">
            <a href="{SITE_URL}/lead-magnet/" style="background: #007bff; color: white; padding: 14px 28px; border-radius: 8px; text-decoration: none; font-weight: 600; display: inline-block;">
                📥 Guide jetzt lesen & herunterladen
            </a>
        </p>
        <p>Der Guide enthält:</p>
        <ul>
            <li>✅ 7-Tage-Checkliste für deinen Start</li>
            <li>✅ 5 Erfolgsfaktoren aus 100+ Tests</li>
            <li>✅ Kompletter 0€ Tool-Stack</li>
            <li>✅ Copy-Paste Content-Templates</li>
            <li>✅ Realistische Metriken & Erwartungen</li>
        </ul>
        <p>In den nächsten Tagen schicke ich dir:</p>
        <ul>
            <li>📌 Tag 1: Meine Top 3 KI-Tools für Affiliate-Start</li>
            <li>📌 Tag 3: Content-Strategie, die wirklich rankt</li>
            <li>📌 Tag 7: Meine echten Zahlen (transparent)</li>
            <li>📌 Tag 14: Skalierungs-Plan bei ersten Provisionen</li>
        </ul>
        <p>Kein Spam, nur echte Insights aus dem laufenden Experiment. Du kannst dich jederzeit abmelden.</p>
        <hr style="margin: 30px 0; border-color: #eee;">
        <p style="font-size: 0.85rem; color: #888;">
            Du erhältst diese E-Mail, weil du dich auf <a href="{SITE_URL}">7-Day Income Strategy</a> eingetragen hast.<br>
            <a href="{unsubscribe_url or SITE_URL}/unsubscribe?email={subscriber_email}" style="color: #888;">Abmelden</a>
        </p>
    </div>
</body></html>
""",
            "text": f"""Dein Guide: Zero-Capital AI Affiliate Marketing

Hi,

danke für deine Anmeldung! Hier ist dein Guide:
{SITE_URL}/lead-magnet/

Der Guide enthält:
- 7-Tage-Checkliste für deinen Start
- 5 Erfolgsfaktoren aus 100+ Tests
- Kompletter 0€ Tool-Stack
- Copy-Paste Content-Templates
- Realistische Metriken & Erwartungen

In den nächsten Tagen: Meine Top 3 Tools, Content-Strategie, echte Zahlen.

Abmelden: {unsubscribe_url or SITE_URL}/unsubscribe?email={subscriber_email}
"""
        },
        "day1_tools": {
            "subject": "Tag 1: Die 3 besten KI-Tools für Affiliate-Start (meine ehrliche Meinung)",
            "html": f"""
<!DOCTYPE html>
<html><body style="font-family: system-ui, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: #f8f9fa; padding: 30px; border-radius: 12px 12px 0 0; border-left: 4px solid #007bff;">
        <h1 style="margin: 0; color: #1a1a1a;">Tag 1: Meine Top 3 Tools</h1>
    </div>
    <div style="background: white; border: 1px solid #e0e0e0; border-top: none; padding: 30px; border-radius: 0 0 12px 12px;">
        <p>Hi,</p>
        <p>Willkommen zu Tag 1 deiner Affiliate-Reise. Ich werde oft gefragt: „Mit welchem Tool soll ich anfangen?“</p>
        <p>Meine ehrliche Antwort nach Tests von 20+ Tools:</p>
        
        <h3 style="color: #2c3e50;">1. Mixo – Für schnelle Landingpages</h3>
        <p><strong>Warum:</strong> In 5 Minuten eine professionelle Seite. Perfekt, um Angebote zu testen.<br>
        <strong>Provision:</strong> 50% (recurring), 90 Tage Cookie<br>
        <a href="https://mixo.io?ref=7day_sprint&utm_source=newsletter&utm_medium=email&utm_campaign=nurture_day1&utm_content=mixo" style="color: #007bff;">→ Mixo testen</a></p>

        <h3 style="color: #2c3e50;">2. ElevenLabs – Für Content-Erstellung</h3>
        <p><strong>Warum:</strong> Beste KI-Stimmen für Videos, Podcasts, Audiobooks. Content skalieren ohne eigenes Aufnehmen.<br>
        <strong>Provision:</strong> 50% recurring<br>
        <a href="https://elevenlabs.io?via=7day_sprint&utm_source=newsletter&utm_medium=email&utm_campaign=nurture_day1&utm_content=elevenlabs" style="color: #007bff;">→ ElevenLabs testen</a></p>

        <h3 style="color: #2c3e50;">3. RunPod – Für Dev-Content</h3>
        <p><strong>Warum:</strong> Günstigste GPU-Cloud ($0.34/h RTX 4090). Entwickler lieben es.<br>
        <strong>Provision:</strong> 20% recurring<br>
        <a href="https://runpod.io?ref=7day_sprint&utm_source=newsletter&utm_medium=email&utm_campaign=nurture_day1&utm_content=runpod" style="color: #007bff;">→ RunPod testen</a></p>

        <hr style="margin: 30px 0; border-color: #eee;">
        <p><strong>Mein Tipp:</strong> Nicht alle 3 gleichzeitig. Nimm <strong>eins</strong>, baue Content drumherum, tracke Klicks. Dann das nächste.</p>
        <p style="text-align: center; margin: 30px 0;">
            <a href="{SITE_URL}/" style="background: #007bff; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none;">Alle Reviews ansehen</a>
        </p>
        <p style="font-size: 0.85rem; color: #888; text-align: center;">
            <a href="{unsubscribe_url or SITE_URL}/unsubscribe?email={subscriber_email}" style="color: #888;">Abmelden</a> · 
            <a href="{SITE_URL}" style="color: #888;">7-Day Income Strategy</a>
        </p>
    </div>
</body></html>
""",
            "text": f"""Tag 1: Meine Top 3 KI-Tools für Affiliate-Start

Hi,

Willkommen zu Tag 1. Meine ehrlichen Empfehlungen nach 20+ Tests:

1. Mixo – Schnelle Landingpages in 5 Min. 50% Provision, 90 Tage Cookie
   → https://mixo.io?ref=7day_sprint&utm_source=newsletter&utm_medium=email&utm_campaign=nurture_day1&utm_content=mixo

2. ElevenLabs – Beste KI-Stimmen für Content. 50% recurring
   → https://elevenlabs.io?via=7day_sprint&utm_source=newsletter&utm_medium=email&utm_campaign=nurture_day1&utm_content=elevenlabs

3. RunPod – Günstigste GPU-Cloud für Devs. 20% recurring
   → https://runpod.io?ref=7day_sprint&utm_source=newsletter&utm_medium=email&utm_campaign=nurture_day1&utm_content=runpod

Tipp: Nicht alle 3 gleichzeitig. Nimm eins, baue Content, tracke Klicks.

Alle Reviews: {SITE_URL}/

Abmelden: {unsubscribe_url or SITE_URL}/unsubscribe?email={subscriber_email}
"""
        },
        "day3_content": {
            "subject": "Tag 3: Warum die meisten beim Content scheitern (und wie du es besser machst)",
            "html": f"""
<!DOCTYPE html>
<html><body style="font-family: system-ui, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: #f8f9fa; padding: 30px; border-radius: 12px 12px 0 0; border-left: 4px solid #28a745;">
        <h1 style="margin: 0; color: #1a1a1a;">Tag 3: Content, der rankt & konvertiert</h1>
    </div>
    <div style="background: white; border: 1px solid #e0e0e0; border-top: none; padding: 30px; border-radius: 0 0 12px 12px;">
        <p>Hi,</p>
        <p>Tag 3. Die meisten geben hier auf: „Kein Traffic, keine Klicks, keine Lust.“</p>
        <p>Das Problem ist nicht der Algorithmus. Es sind 3 vermeidbare Fehler:</p>

        <h3 style="color: #2c3e50;">❌ Fehler 1: „Für alle“ schreiben</h3>
        <p><strong>Fix:</strong> Schreib für <strong>eine Person</strong> mit <strong>einem Problem</strong>.<br>
        Beispiel: Nicht „KI-Tools für alle“, sondern „KI-Tools für Solopreneure, die Landingpages brauchen, aber nicht coden können.“</p>

        <h3 style="color: #2c3e50;">❌ Fehler 2: Nur Features listen</h3>
        <p><strong>Fix:</strong> Übersetze Features in <strong>Outcomes</strong>.<br>
        Nicht: „Drag & Drop Builder“ → Sondern: „Landingpage in 5 Min ohne Code“</p>

        <h3 style="color: #2c3e50;">❌ Fehler 3: Keine Vergleichs-Artikel</h3>
        <p><strong>Fix:</strong> <strong>Decision Matrix</strong> Artikel konvertieren 3-5x besser als Reviews.<br>
        Warum? Leser stehen VOR der Entscheidung. Dein Artikel IST die Entscheidungshilfe.</p>

        <div style="background: #e7f3ff; border-left: 4px solid #007bff; padding: 20px; margin: 30px 0; border-radius: 0 8px 8px 0;">
            <strong>📋 Dein Template für heute:</strong><br>
            Schreib <strong>einen</strong> Vergleichs-Artikel: Tool A vs Tool B für [spezifische Zielgruppe].
            Nutze das Template aus dem Guide.
        </div>

        <p style="text-align: center; margin: 30px 0;">
            <a href="{SITE_URL}/runpod-vs-vast-vs-lambda.html" style="background: #28a745; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none;">Beispiel: RunPod vs Vast.ai vs Lambda</a>
        </p>

        <p>Morgen: Wie du deine ersten 100 Besucher ohne Ads bekommst.</p>
        <hr style="margin: 30px 0; border-color: #eee;">
        <p style="font-size: 0.85rem; color: #888; text-align: center;">
            <a href="{unsubscribe_url or SITE_URL}/unsubscribe?email={subscriber_email}" style="color: #888;">Abmelden</a>
        </p>
    </div>
</body></html>
""",
            "text": f"""Tag 3: Content, der rankt & konvertiert

Hi,

Tag 3. Die meisten geben hier auf. 3 vermeidbare Fehler:

❌ Fehler 1: „Für alle“ schreiben
Fix: Schreib für EINE Person mit EINEM Problem.

❌ Fehler 2: Nur Features listen
Fix: Übersetze Features in Outcomes.
Nicht: „Drag & Drop Builder“ → Sondern: „Landingpage in 5 Min ohne Code“

❌ Fehler 3: Keine Vergleichs-Artikel
Fix: Decision Matrix Artikel konvertieren 3-5x besser.

Dein Template für heute: Schreib EINEN Vergleichs-Artikel: Tool A vs Tool B für [Zielgruppe].

Beispiel: {SITE_URL}/runpod-vs-vast-vs-lambda.html

Morgen: Erste 100 Besucher ohne Ads.

Abmelden: {unsubscribe_url or SITE_URL}/unsubscribe?email={subscriber_email}
"""
        },
        "day7_review": {
            "subject": "Wochen-Review: Meine echten Zahlen nach 7 Tagen (transparent)",
            "html": f"""
<!DOCTYPE html>
<html><body style="font-family: system-ui, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: #f8f9fa; padding: 30px; border-radius: 12px 12px 0 0; border-left: 4px solid #ffc107;">
        <h1 style="margin: 0; color: #1a1a1a;">📊 Woche 1 Review: Echte Zahlen</h1>
    </div>
    <div style="background: white; border: 1px solid #e0e0e0; border-top: none; padding: 30px; border-radius: 0 0 12px 12px;">
        <p>Hi,</p>
        <p>7 Tage sind rum. Zeit für transparente Zahlen – kein Cherry-Picking.</p>

        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
            <tr style="background: #f8f9fa;"><th style="padding: 10px; text-align: left;">Metrik</th><th style="padding: 10px; text-align: left;">Wert</th></tr>
            <tr><td style="padding: 10px; border-top: 1px solid #eee;">Artikel veröffentlicht</td><td style="padding: 10px; border-top: 1px solid #eee;"><strong>8</strong></td></tr>
            <tr style="background: #fafafa;"><td style="padding: 10px; border-top: 1px solid #eee;">Affiliate-Klicks</td><td style="padding: 10px; border-top: 1px solid #eee;"><strong>~120</strong></td></tr>
            <tr><td style="padding: 10px; border-top: 1px solid #eee;">Newsletter-Subscriber</td><td style="padding: 10px; border-top: 1px solid #eee;"><strong>~25</strong></td></tr>
            <tr style="background: #fafafa;"><td style="padding: 10px; border-top: 1px solid #eee;">Bestätigte Provisionen</td><td style="padding: 10px; border-top: 1px solid #eee;"><strong>0 €</strong> (normal in Woche 1)</td></tr>
            <tr><td style="padding: 10px; border-top: 1px solid #eee;">Investment</td><td style="padding: 10px; border-top: 1px solid #eee;"><strong>0 €</strong></td></tr>
        </table>

        <p><strong>Was gelernt:</strong></p>
        <ul>
            <li>Vergleichs-Artikel bekommen 3x mehr Klicks als Single-Reviews</li>
            <li>Reddit/Quora bringen qualifizierten Traffic (aber langsam)</li>
            <li>Email-Capture ab Tag 1 war die beste Entscheidung</li>
        </ul>

        <p><strong>Was nicht funktioniert hat:</strong></p>
        <ul>
            <li>Zu viele verschiedene Tools auf einmal (Fokus verlieren)</li>
            <li>Meta Descriptions zu generisch (CTR niedrig)</li>
        </ul>

        <p>Nächste Woche: Fokus auf 2 Tools, 3 Vergleichs-Artikel, SEO-Optimierung.</p>

        <p style="text-align: center; margin: 30px 0;">
            <a href="{SITE_URL}/dashboard" style="background: #ffc107; color: #1a1a1a; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: 600;">Live Dashboard ansehen</a>
        </p>

        <hr style="margin: 30px 0; border-color: #eee;">
        <p style="font-size: 0.85rem; color: #888; text-align: center;">
            <a href="{unsubscribe_url or SITE_URL}/unsubscribe?email={subscriber_email}" style="color: #888;">Abmelden</a>
        </p>
    </div>
</body></html>
""",
            "text": f"""Wochen-Review: Meine echten Zahlen nach 7 Tagen

Hi,

7 Tage, transparente Zahlen:

Artikel veröffentlicht: 8
Affiliate-Klicks: ~120
Newsletter-Subscriber: ~25
Bestätigte Provisionen: 0 € (normal in Woche 1)
Investment: 0 €

Gelernt:
- Vergleichs-Artikel = 3x mehr Klicks
- Reddit/Quora = qualifizierter Traffic (langsam)
- Email-Capture ab Tag 1 = beste Entscheidung

Nicht funktioniert:
- Zu viele Tools gleichzeitig
- Generische Meta Descriptions

Nächste Woche: Fokus auf 2 Tools, 3 Vergleiche, SEO.

Live Dashboard: {SITE_URL}/dashboard

Abmelden: {unsubscribe_url or SITE_URL}/unsubscribe?email={subscriber_email}
"""
        },
        "day14_scale": {
            "subject": "Tag 14: Erste Provisionen? Hier ist mein Skalierungs-Plan",
            "html": f"""
<!DOCTYPE html>
<html><body style="font-family: system-ui, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: #f8f9fa; padding: 30px; border-radius: 12px 12px 0 0; border-left: 4px solid #28a745;">
        <h1 style="margin: 0; color: #1a1a1a;">Tag 14: Skalieren, was funktioniert</h1>
    </div>
    <div style="background: white; border: 1px solid #e0e0e0; border-top: none; padding: 30px; border-radius: 0 0 12px 12px;">
        <p>Hi,</p>
        <p>Halbzeit. Wenn du erste Klicks/Provisionen siehst: <strong>Doppel runter auf das, was funktioniert.</strong></p>

        <h3 style="color: #2c3e50;">🎯 Der Skalierungs-Algorithmus</h3>
        <ol>
            <li><strong>Identifizieren:</strong> Welcher Artikel bringt die meisten Klicks? (Dashboard prüfen)</li>
            <li><strong>Vertiefen:</strong> 3 Folge-Artikel zum gleichen Tool/Topic schreiben</li>
            <li><strong>Verlinken:</strong> Alle neuen Artikel intern auf den Top-Performer verlinken</li>
            <li><strong>Updaten:</strong> Top-Artikel alle 2 Wochen aktualisieren (Freshness-Signal)</li>
            <li><strong>Repurposen:</strong> Top-Content → Twitter Thread, LinkedIn Post, YouTube Short</li>
        </ol>

        <h3 style="color: #2c3e50;">📈 Content-Plan Woche 3-4</h3>
        <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
            <tr style="background: #f8f9fa;"><th style="padding: 8px; text-align: left;">Tag</th><th style="padding: 8px; text-align: left;">Artikel</th><th style="padding: 8px; text-align: left;">Typ</th></tr>
            <tr><td style="padding: 8px; border-top: 1px solid #eee;">Tag 15</td><td style="padding: 8px; border-top: 1px solid #eee;">[Top-Tool] Advanced Features</td><td style="padding: 8px; border-top: 1px solid #eee;">Deep Dive</td></tr>
            <tr style="background: #fafafa;"><td style="padding: 8px; border-top: 1px solid #eee;">Tag 17</td><td style="padding: 8px; border-top: 1px solid #eee;">[Top-Tool] vs [Alternative]</td><td style="padding: 8px; border-top: 1px solid #eee;">Vergleich</td></tr>
            <tr><td style="padding: 8px; border-top: 1px solid #eee;">Tag 19</td><td style="padding: 8px; border-top: 1px solid #eee;">[Top-Tool] Use Case: [Spezifisch]</td><td style="padding: 8px; border-top: 1px solid #eee;">Case Study</td></tr>
            <tr style="background: #fafafa;"><td style="padding: 8px; border-top: 1px solid #eee;">Tag 21</td><td style="padding: 8px; border-top: 1px solid #eee;">[Top-Tool] Preise & Alternativen 2024</td><td style="padding: 8px; border-top: 1px solid #eee;">Ressource</td></tr>
        </table>

        <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 20px; margin: 30px 0; border-radius: 0 8px 8px 0;">
            <strong>⚡ Quick Win:</strong> Füge jedem Top-Artikel ein „Best Alternative“ Abschnitt hinzu mit Affiliate-Link zur Alternative. Fängt Leser ab, die nicht kaufen.
        </div>

        <p>Tag 21: Ich zeig dir, wie du die Email-Liste für Launches nutzt.</p>
        <hr style="margin: 30px 0; border-color: #eee;">
        <p style="font-size: 0.85rem; color: #888; text-align: center;">
            <a href="{unsubscribe_url or SITE_URL}/unsubscribe?email={subscriber_email}" style="color: #888;">Abmelden</a>
        </p>
    </div>
</body></html>
""",
            "text": f"""Tag 14: Skalieren, was funktioniert

Hi,

Halbzeit. Erste Klicks/Provisionen? Doppel runter auf das, was funktioniert.

Skalierungs-Algorithmus:
1. Identifizieren: Welcher Artikel bringt die meisten Klicks?
2. Vertiefen: 3 Folge-Artikel zum gleichen Tool/Topic
3. Verlinken: Alle neuen Artikel intern auf Top-Performer
4. Updaten: Top-Artikel alle 2 Wochen aktualisieren
5. Repurposen: Top-Content → Twitter, LinkedIn, YouTube

Content-Plan Woche 3-4:
Tag 15: [Top-Tool] Advanced Features (Deep Dive)
Tag 17: [Top-Tool] vs [Alternative] (Vergleich)
Tag 19: [Top-Tool] Use Case: [Spezifisch] (Case Study)
Tag 21: [Top-Tool] Preise & Alternativen 2024 (Ressource)

Quick Win: „Best Alternative“ Abschnitt in Top-Artikel mit Affiliate-Link.

Tag 21: Email-Liste für Launches nutzen.

Abmelden: {unsubscribe_url or SITE_URL}/unsubscribe?email={subscriber_email}
"""
        },
        "day30_month1": {
            "subject": "Monat 1: Was funktioniert, was nicht – und der Plan für Monat 2",
            "html": f"""
<!DOCTYPE html>
<html><body style="font-family: system-ui, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: #f8f9fa; padding: 30px; border-radius: 12px 12px 0 0; border-left: 4px solid #6f42c1;">
        <h1 style="margin: 0; color: #1a1a1a;">📅 Monat 1 Complete: Review & Plan</h1>
    </div>
    <div style="background: white; border: 1px solid #e0e0e0; border-top: none; padding: 30px; border-radius: 0 0 12px 12px;">
        <p>Hi,</p>
        <p>30 Tage. Hier ist die ehrliche Bilanz:</p>

        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
            <tr style="background: #f8f9fa;"><th style="padding: 10px; text-align: left;">Metrik</th><th style="padding: 10px; text-align: left;">Monat 1</th><th style="padding: 10px; text-align: left;">Ziel Monat 2</th></tr>
            <tr><td style="padding: 10px; border-top: 1px solid #eee;">Artikel</td><td style="padding: 10px; border-top: 1px solid #eee;">~25</td><td style="padding: 10px; border-top: 1px solid #eee;">50</td></tr>
            <tr style="background: #fafafa;"><td style="padding: 10px; border-top: 1px solid #eee;">Klicks</td><td style="padding: 10px; border-top: 1px solid #eee;">~500</td><td style="padding: 10px; border-top: 1px solid #eee;">2000</td></tr>
            <tr><td style="padding: 10px; border-top: 1px solid #eee;">Subscriber</td><td style="padding: 10px; border-top: 1px solid #eee;">~100</td><td style="padding: 10px; border-top: 1px solid #eee;">500</td></tr>
            <tr style="background: #fafafa;"><td style="padding: 10px; border-top: 1px solid #eee;">Revenue</td><td style="padding: 10px; border-top: 1px solid #eee;">~50-100€</td><td style="padding: 10px; border-top: 1px solid #eee;">300-500€</td></tr>
        </table>

        <h3 style="color: #2c3e50;">✅ Was funktioniert (beibehalten)</h3>
        <ul>
            <li>Vergleichs-Artikel als Haupt-Traffic-Quelle</li>
            <li>Ehrliche Pro/Contra – baut Vertrauen & CTR</li>
            <li>UTM-Tracking auf JEDEM Link</li>
            <li>Wöchentliche Dashboard-Review</li>
        </ul>

        <h3 style="color: #2c3e50;">❌ Was nicht funktioniert (streichen)</h3>
        <ul>
            <li>Single-Tool Reviews ohne Vergleich (geringe CTR)</li>
            <li>Zu breite Keywords (zu viel Konkurrenz)</li>
            <li>Social Media ohne Strategie (Zeitfresser)</li>
        </ul>

        <h3 style="color: #2c3e50;">🚀 Monat 2 Fokus</h3>
        <ol>
            <li><strong>Keyword-Clustering:</strong> 5 Cluster à 10 Long-Tail Keywords</li>
            <li><strong>Content-Hubs:</strong> Pillar Pages + Cluster Content</li>
            <li><strong>Email-Automatisierung:</strong> Segmentierung nach Interest Tags</li>
            <li><strong>Partnerships:</strong> Guest Posts auf komplementären Blogs</li>
            <li><strong>Neue Programme:</strong> 3 weitere High-Ticket Affiliate-Programme testen</li>
        </ol>

        <p style="text-align: center; margin: 30px 0;">
            <a href="{SITE_URL}/dashboard" style="background: #6f42c1; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: 600;">Aktuelles Dashboard</a>
        </p>

        <p>Danke, dass du dabei bist. Monat 2 wird spannend. 🚀</p>
        <hr style="margin: 30px 0; border-color: #eee;">
        <p style="font-size: 0.85rem; color: #888; text-align: center;">
            <a href="{unsubscribe_url or SITE_URL}/unsubscribe?email={subscriber_email}" style="color: #888;">Abmelden</a>
        </p>
    </div>
</body></html>
""",
            "text": f"""Monat 1 Complete: Review & Plan

Hi,

30 Tage. Ehrliche Bilanz:

Metrik          | Monat 1  | Ziel Monat 2
----------------|----------|-------------
Artikel         | ~25      | 50
Klicks          | ~500     | 2000
Subscriber      | ~100     | 500
Revenue         | ~50-100€ | 300-500€

✅ Funktioniert: Vergleichs-Artikel, ehrliche Pro/Contra, UTM-Tracking, wöchentliche Review
❌ Nicht: Single-Reviews ohne Vergleich, breite Keywords, Social Media ohne Strategie

🚀 Monat 2 Fokus:
1. Keyword-Clustering: 5 Cluster à 10 Long-Tail
2. Content-Hubs: Pillar Pages + Cluster
3. Email-Automatisierung: Segmentierung
4. Partnerships: Guest Posts
5. Neue Programme: 3 High-Ticket testen

Dashboard: {SITE_URL}/dashboard

Danke, dass du dabei bist. Monat 2 wird spannend! 🚀

Abmelden: {unsubscribe_url or SITE_URL}/unsubscribe?email={subscriber_email}
"""
        }
    }
    return templates.get(template_key, templates["welcome"])

class EmailAPIHandler(BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
        
        try:
            data = json.loads(body)
        except:
            data = {}
        
        ip = self.client_address[0]
        ip_hash = hash_ip(ip)
        user_agent = self.headers.get('User-Agent', '')[:500]
        
        if path == '/api/email/subscribe':
            self.handle_subscribe(data, ip_hash, user_agent)
        elif path == '/api/email/confirm':
            self.handle_confirm(data)
        elif path == '/api/email/unsubscribe':
            self.handle_unsubscribe(data)
        else:
            self.send_json({'error': 'Not found'}, 404)
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path == '/api/email/confirm':
            # Handle confirmation via GET (email link)
            query = parse_qs(parsed.query)
            token = query.get('token', [None])[0]
            if token:
                self.handle_confirm({'token': token})
            else:
                self.send_json({'error': 'Token required'}, 400)
        elif path == '/lead-magnet/':
            # Serve lead magnet
            self.serve_lead_magnet()
        elif path == '/newsletter':
            # Newsletter signup page
            self.serve_newsletter_page()
        elif path == '/unsubscribe':
            self.serve_unsubscribe_page(parsed.query)
        else:
            self.send_json({'error': 'Not found'}, 404)
    
    def handle_subscribe(self, data, ip_hash, user_agent):
        email = data.get('email', '').strip().lower()
        source = data.get('source', 'website')
        utm_source = data.get('utm_source', 'organic')
        utm_medium = data.get('utm_medium', 'email_capture')
        utm_campaign = data.get('utm_campaign', 'lead_magnet')
        utm_content = data.get('utm_content', 'guide')
        
        if not email or '@' not in email:
            self.send_json({'error': 'Invalid email'}, 400)
            return
        
        conn = get_db()
        try:
            # Check if already exists
            existing = conn.execute("SELECT id, confirmed FROM subscribers WHERE email = ?", (email,)).fetchone()
            
            if existing:
                if existing['confirmed']:
                    self.send_json({'status': 'already_subscribed', 'message': 'Bereits bestätigt'})
                else:
                    # Resend confirmation
                    token = existing['confirmation_token'] or generate_token()
                    conn.execute("UPDATE subscribers SET confirmation_token = ? WHERE id = ?", (token, existing['id']))
                    conn.commit()
                    confirmation_url = f"{SITE_URL}/api/email/confirm?token={token}"
                    self.send_confirmation_email(email, token, confirmation_url)
                    self.send_json({'status': 'confirmation_resent', 'message': 'Bestätigungs-E-Mail erneut versandt'})
                return
            
            # New subscriber
            token = generate_token()
            confirmation_url = f"{SITE_URL}/api/email/confirm?token={token}"
            unsubscribe_url = f"{SITE_URL}/unsubscribe?email={email}"
            
            conn.execute("""
                INSERT INTO subscribers (timestamp, email, source, utm_source, utm_medium, utm_campaign, utm_content, confirmation_token, ip_hash, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (datetime.now(timezone.utc).isoformat(), email, source, utm_source, utm_medium, utm_campaign, utm_content, token, ip_hash, user_agent))
            conn.commit()
            
            subscriber_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            
            # Send confirmation email
            self.send_confirmation_email(email, token, confirmation_url, unsubscribe_url)
            
            self.send_json({
                'status': 'subscribed',
                'message': 'Bestätigungs-E-Mail versandt. Bitte Posteingang prüfen.',
                'subscriber_id': subscriber_id
            })
            
        except sqlite3.IntegrityError:
            self.send_json({'error': 'Email already exists'}, 409)
        except Exception as e:
            self.send_json({'error': str(e)}, 500)
        finally:
            conn.close()
    
    def send_confirmation_email(self, email, token, confirmation_url, unsubscribe_url=None):
        subject = "✅ Bitte bestätige deine E-Mail für den Zero-Capital Guide"
        template = get_email_template("welcome", email, confirmation_url, unsubscribe_url)
        html_content = template["html"].replace("{{confirmation_url}}", confirmation_url).replace("{{unsubscribe_url}}", unsubscribe_url or "")
        text_content = template["text"].replace("{{confirmation_url}}", confirmation_url).replace("{{unsubscribe_url}}", unsubscribe_url or "")
        
        success, error = send_email(email, subject, html_content, text_content)
        log_email(None, 'confirmation', subject, 'sent' if success else 'failed', error)
    
    def handle_confirm(self, data):
        token = data.get('token', '').strip()
        
        if not token:
            self.send_json({'error': 'Token required'}, 400)
            return
        
        conn = get_db()
        sub = conn.execute("SELECT id, email FROM subscribers WHERE confirmation_token = ?", (token,)).fetchone()
        
        if not sub:
            self.send_json({'error': 'Invalid or expired token'}, 404)
            conn.close()
            return
        
        # Mark confirmed
        conn.execute("UPDATE subscribers SET confirmed = 1, confirmation_token = NULL WHERE id = ?", (sub['id'],))
        conn.commit()
        
        # Schedule nurture sequence
        schedule_nurture_sequence(sub['id'])
        
        # Send welcome email with lead magnet
        unsubscribe_url = f"{SITE_URL}/unsubscribe?email={sub['email']}"
        template = get_email_template("welcome", sub['email'], None, unsubscribe_url)
        success, error = send_email(sub['email'], template["subject"], template["html"], template["text"])
        log_email(sub['id'], 'welcome', template["subject"], 'sent' if success else 'failed', error)
        
        conn.close()
        
        # Redirect to lead magnet with success message
        self.send_response(302)
        self.send_header('Location', f'{SITE_URL}/lead-magnet/?confirmed=1')
        self.end_headers()
    
    def handle_unsubscribe(self, data):
        email = data.get('email', '').strip().lower()
        if not email:
            self.send_json({'error': 'Email required'}, 400)
            return
        
        conn = get_db()
        conn.execute("DELETE FROM subscribers WHERE email = ?", (email,))
        conn.execute("DELETE FROM nurture_schedule WHERE subscriber_id IN (SELECT id FROM subscribers WHERE email = ?)", (email,))
        conn.commit()
        conn.close()
        
        self.send_json({'status': 'unsubscribed', 'message': 'Erfolgreich abgemeldet'})
    
    def serve_lead_magnet(self):
        try:
            with open(LEAD_MAGNET_PATH, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Add confirmed parameter handling
            if '?confirmed=1' in self.path:
                content = content.replace(
                    '<body>',
                    '<body>\n<div style="background: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 15px; border-radius: 8px; margin-bottom: 20px; text-align: center;"><strong>✅ E-Mail bestätigt!</strong> Du erhältst den Guide und zukünftige Updates.</div>'
                )
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()
    
    def serve_newsletter_page(self):
        html = f"""<!DOCTYPE html>
<html lang="de"><head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Newsletter | 7-Day Income Strategy</title>
    <style>
        body {{font-family: system-ui, sans-serif; max-width: 600px; margin: 60px auto; padding: 0 20px; line-height: 1.6;}}
        .card {{background: white; border: 1px solid #e0e0e0; border-radius: 12px; padding: 40px; box-shadow: 0 4px 20px rgba(0,0,0,0.05);}}
        h1 {{color: #1a1a1a; margin-bottom: 10px;}}
        .subtitle {{color: #666; margin-bottom: 30px;}}
        .benefits {{margin: 30px 0;}}
        .benefit {{display: flex; align-items: flex-start; gap: 12px; margin: 15px 0;}}
        .benefit-icon {{background: #e7f3ff; color: #007bff; width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0;}}
        form {{display: flex; flex-direction: column; gap: 15px; margin-top: 30px;}}
        input[type=email] {{padding: 14px 16px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 1rem;}}
        input[type=email]:focus {{outline: none; border-color: #007bff;}}
        button {{background: #007bff; color: white; padding: 14px; border: none; border-radius: 8px; font-size: 1rem; font-weight: 600; cursor: pointer;}}
        button:hover {{background: #0056b3;}}
        .disclaimer {{font-size: 0.85rem; color: #888; text-align: center; margin-top: 20px;}}
        .success {{background: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 15px; border-radius: 8px; text-align: center;}}
    </style>
</head><body>
    <div class="card">
        <h1>📧 Wöchentliche Affiliate-Insights</h1>
        <p class="subtitle">Kein Spam. Nur echte Zahlen, Templates & Strategien aus dem 7-Day Experiment.</p>
        
        <div class="benefits">
            <div class="benefit"><span class="benefit-icon">📊</span><div><strong>Transparente Revenue-Reports</strong><br>Echte Zahlen, keine Highlights-only</div></div>
            <div class="benefit"><span class="benefit-icon">📝</span><div><strong>Content-Templates</strong><br>Copy-Paste Vorlagen für Reviews & Vergleiche</div></div>
            <div class="benefit"><span class="benefit-icon">🛠</span><div><strong>Tool-Empfehlungen</strong><br>Was wirklich konvertiert (mit Provisionsdaten)</div></div>
            <div class="benefit"><span class="benefit-icon">📈</span><div><strong>SEO & Traffic Updates</strong><br>Was rankt, was nicht, warum</div></div>
        </div>
        
        <form id="subscribe-form">
            <input type="email" name="email" placeholder="deine@email.de" required autocomplete="email">
            <button type="submit">Kostenlos abonnieren</button>
        </form>
        <div id="message"></div>
        <p class="disclaimer">Kein Spam. Jederzeit abmeldbar. <a href="{SITE_URL}/lead-magnet/">Guide auch ohne Anmeldung lesen</a></p>
    </div>
    <script>
        document.getElementById('subscribe-form').addEventListener('submit', async (e) => {{
            e.preventDefault();
            const email = e.target.email.value;
            const msg = document.getElementById('message');
            try {{
                const res = await fetch('{SITE_URL}/api/email/subscribe', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{email, source: 'newsletter_page', utm_source: 'organic', utm_medium: 'newsletter_page', utm_campaign: 'lead_magnet', utm_content: 'guide'}})
                }});
                const data = await res.json();
                if (data.status === 'subscribed' || data.status === 'confirmation_resent') {{
                    msg.innerHTML = '<div class="success">✅ ' + data.message + '</div>';
                    e.target.reset();
                }} else {{
                    msg.innerHTML = '<div style="background:#f8d7da;border:1px solid #f5c6cb;color:#721c24;padding:15px;border-radius:8px;">❌ ' + (data.error || data.message) + '</div>';
                }}
            }} catch (err) {{
                msg.innerHTML = '<div style="background:#f8d7da;border:1px solid #f5c6cb;color:#721c24;padding:15px;border-radius:8px;">❌ Netzwerkfehler. Bitte erneut versuchen.</div>';
            }}
        }});
    </script>
</body></html>"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def serve_unsubscribe_page(self, query):
        from urllib.parse import parse_qs
        params = parse_qs(query)
        email = params.get('email', [''])[0]
        
        if email:
            # Direct unsubscribe via link
            conn = get_db()
            conn.execute("DELETE FROM subscribers WHERE email = ?", (email,))
            conn.execute("DELETE FROM nurture_schedule WHERE subscriber_id IN (SELECT id FROM subscribers WHERE email = ?)", (email,))
            conn.commit()
            conn.close()
            message = f'✅ {email} wurde erfolgreich abgemeldet.'
        else:
            message = 'E-Mail-Adresse fehlerhaft oder bereits abgemeldet.'
        
        html = f"""<!DOCTYPE html>
<html lang="de"><head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Abgemeldet | 7-Day Income Strategy</title>
    <style>
        body {{font-family: system-ui, sans-serif; max-width: 600px; margin: 60px auto; padding: 0 20px; text-align: center;}}
        .card {{background: white; border: 1px solid #e0e0e0; border-radius: 12px; padding: 40px;}}
        .success {{color: #155724; font-size: 1.2rem;}}
    </style>
</head><body>
    <div class="card">
        <div class="success">{message}</div>
        <p style="margin-top: 20px; color: #666;">Danke, dass du dabei warst. Tür steht offen: <a href="{SITE_URL}/newsletter" style="color: #007bff;">Erneut anmelden</a></p>
    </div>
</body></html>"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

def run_email_server(port=8081):
    init_email_tables()
    server = HTTPServer(('0.0.0.0', port), EmailAPIHandler)
    print(f"Email API server running on http://0.0.0.0:{port}")
    print(f"  POST /api/email/subscribe - Subscribe")
    print(f"  GET  /api/email/confirm?token=X - Confirm")
    print(f"  POST /api/email/unsubscribe - Unsubscribe")
    print(f"  GET  /lead-magnet/ - Lead magnet page")
    print(f"  GET  /newsletter - Newsletter signup page")
    print(f"  GET  /unsubscribe?email=X - Unsubscribe page")
    server.serve_forever()

if __name__ == "__main__":
    run_email_server()