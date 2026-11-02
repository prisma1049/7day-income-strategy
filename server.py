#!/usr/bin/env python3
"""
Lightweight tracking server for 7-Day Revenue Sprint
Provides dashboard API and serves static site. Click tracking via JS sendBeacon.
"""

import os
import json
import sqlite3
from datetime import datetime, timezone
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path

SITE_DIR = Path(__file__).parent
DB_PATH = SITE_DIR / "tracking.db"

# Affiliate programs config (for dashboard display)
AFFILIATE_PROGRAMS = {
    "mixo": {"name": "Mixo", "base_url": "https://mixo.io", "param": "ref", "rate": 0.50},
    "elevenlabs": {"name": "ElevenLabs", "base_url": "https://elevenlabs.io", "param": "via", "rate": 0.50},
    "runpod": {"name": "RunPod", "base_url": "https://runpod.io", "param": "ref", "rate": 0.20},
    "surfer_seo": {"name": "Surfer SEO", "base_url": "https://surferseo.com", "param": "ref", "rate": 0.30},
    "carrd": {"name": "Carrd", "base_url": "https://carrd.co", "param": "ref", "rate": 0.30},
    "vast_ai": {"name": "Vast.ai", "base_url": "https://vast.ai", "param": "ref", "rate": 0.10},
    "together_ai": {"name": "Together AI", "base_url": "https://api.together.xyz", "param": "model_name", "rate": 0.20},
}

ARTICLE_MAP = {
    "mixo-review.html": "mixo",
    "elevenlabs-review.html": "elevenlabs",
    "runpod-review.html": "runpod",
    "surfer-seo-review.html": "surfer_seo",
    "mixo-vs-carrd-vs-wix.html": "mixo_carrd_comparison",
    "elevenlabs-vs-speechify.html": "elevenlabs_speechify_comparison",
    "runpod-vs-vast-vs-lambda.html": "runpod_vast_lambda_comparison",
    "together-vs-replicate-vs-fireworks.html": "together_replicate_fireworks_comparison",
    "content-framework.md": "framework",
    "editorial-calendar.md": "calendar",
}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def log_click(program_key, article_slug, utm_source, utm_medium, utm_campaign, utm_content, ip_hash, user_agent, referrer):
    """Log click to database."""
    conn = get_db()
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
    conn.close()

def get_dashboard_data():
    """Get dashboard data."""
    conn = get_db()
    
    clicks_by_program = conn.execute("""
        SELECT affiliate_program, COUNT(*) as clicks
        FROM clicks
        GROUP BY affiliate_program
    """).fetchall()
    
    conversions_by_program = conn.execute("""
        SELECT affiliate_program, COUNT(*) as conversions, SUM(commission_eur) as total_commission
        FROM conversions
        WHERE status = 'confirmed'
        GROUP BY affiliate_program
    """).fetchall()
    
    daily_stats = conn.execute("""
        SELECT * FROM daily_stats ORDER BY date DESC LIMIT 7
    """).fetchall()
    
    recent_clicks = conn.execute("""
        SELECT timestamp, affiliate_program, article_slug, utm_source, utm_medium, ip_hash
        FROM clicks ORDER BY timestamp DESC LIMIT 50
    """).fetchall()
    
    recent_conversions = conn.execute("""
        SELECT timestamp, affiliate_program, amount_eur, commission_eur, status
        FROM conversions ORDER BY timestamp DESC LIMIT 20
    """).fetchall()
    
    # Totals
    total_clicks = conn.execute("SELECT COUNT(*) FROM clicks").fetchone()[0]
    total_conversions = conn.execute("SELECT COUNT(*) FROM conversions WHERE status='confirmed'").fetchone()[0]
    total_commission = conn.execute("SELECT SUM(commission_eur) FROM conversions WHERE status='confirmed'").fetchone()[0] or 0
    
    conn.close()
    
    return {
        "totals": {
            "clicks": total_clicks,
            "conversions": total_conversions,
            "commission_eur": round(total_commission, 2)
        },
        "clicks_by_program": [dict(r) for r in clicks_by_program],
        "conversions_by_program": [dict(r) for r in conversions_by_program],
        "daily_stats": [dict(r) for r in daily_stats],
        "recent_clicks": [dict(r) for r in recent_clicks],
        "recent_conversions": [dict(r) for r in recent_conversions],
    }

class TrackingHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SITE_DIR), **kwargs)
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        # Dashboard API
        if path == '/api/dashboard':
            self.send_json(get_dashboard_data())
            return
        
        # Dashboard HTML page
        if path == '/dashboard' or path == '/dashboard/':
            self.serve_dashboard()
            return
        
        # Tracking endpoint (for JS sendBeacon)
        if path == '/api/track':
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                body = self.rfile.read(content_length).decode('utf-8')
                try:
                    data = json.loads(body)
                    ip = self.client_address[0]
                    ip_hash = __import__('hashlib').sha256(ip.encode()).hexdigest()[:16]
                    user_agent = self.headers.get('User-Agent', '')[:500]
                    referrer = self.headers.get('Referer', '')[:500]
                    
                    log_click(
                        data.get('program', ''),
                        data.get('article', ''),
                        data.get('utm_source', ''),
                        data.get('utm_medium', ''),
                        data.get('utm_campaign', ''),
                        data.get('utm_content', ''),
                        ip_hash,
                        user_agent,
                        referrer
                    )
                    self.send_response(204)
                except Exception as e:
                    self.send_response(400)
                self.end_headers()
            else:
                self.send_response(204)
                self.end_headers()
            return
        
        # Default: serve static files
        super().do_GET()
    
    def serve_dashboard(self):
        """Serve the dashboard HTML."""
        dashboard_html = self.generate_dashboard_html()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(dashboard_html.encode('utf-8'))
    
    def send_json(self, data):
        json_bytes = json.dumps(data).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json_bytes)
    
    def generate_dashboard_html(self):
        data = get_dashboard_data()
        
        # Program cards
        program_cards = ""
        for p_key, p_info in AFFILIATE_PROGRAMS.items():
            clicks = next((c['clicks'] for c in data['clicks_by_program'] if c['affiliate_program'] == p_key), 0)
            conv = next((c for c in data['conversions_by_program'] if c['affiliate_program'] == p_key), None)
            conversions = conv['conversions'] if conv else 0
            commission = conv['total_commission'] if conv else 0
            ctr = f"{(conversions/clicks*100):.1f}%" if clicks > 0 else "0%"
            
            program_cards += f"""
            <div class="card">
                <h3>{p_info['name']}</h3>
                <div class="metric"><span>Klicks</span><strong>{clicks}</strong></div>
                <div class="metric"><span>Conversions</span><strong>{conversions}</strong></div>
                <div class="metric"><span>CTR</span><strong>{ctr}</strong></div>
                <div class="metric revenue"><span>Provision</span><strong>{commission:.2f} €</strong></div>
            </div>
            """
        
        # Daily stats rows
        daily_rows = ""
        for d in data['daily_stats']:
            daily_rows += f"<tr><td>{d['date']}</td><td>{d.get('page_views', 0)}</td><td>{d.get('unique_visitors', 0)}</td><td>{d.get('total_clicks', 0)}</td><td>{d.get('affiliate_clicks', 0)}</td><td>{d.get('conversions', 0)}</td><td>{d.get('commission_eur', 0):.2f} €</td></tr>"
        if not daily_rows:
            daily_rows = '<tr><td colspan="7">Keine Daten</td></tr>'
        
        # Recent clicks rows
        clicks_rows = ""
        for c in data['recent_clicks']:
            ts = c['timestamp'][:19].replace('T', ' ')
            source_medium = f"{c['utm_source']}/{c['utm_medium']}" if c['utm_source'] else "direct"
            clicks_rows += f"<tr><td>{ts}</td><td>{c['affiliate_program']}</td><td>{c['article_slug']}</td><td>{source_medium}</td><td>{c['ip_hash']}</td></tr>"
        if not clicks_rows:
            clicks_rows = '<tr><td colspan="5">Keine Klicks</td></tr>'
        
        # Recent conversions rows
        conv_rows = ""
        for c in data['recent_conversions']:
            ts = c['timestamp'][:19].replace('T', ' ')
            conv_rows += f"<tr><td>{ts}</td><td>{c['affiliate_program']}</td><td>{c['amount_eur']:.2f} €</td><td>{c['commission_eur']:.2f} €</td><td>{c['status']}</td></tr>"
        if not conv_rows:
            conv_rows = '<tr><td colspan="5">Keine Conversions</td></tr>'
        
        totals = data['totals']
        
        return f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>7-Day Sprint Dashboard</title>
    <style>
        body {{font-family: system-ui, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5;}}
        h1 {{color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px;}}
        .grid {{display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin: 20px 0;}}
        .card {{background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);}}
        .card h3 {{margin: 0 0 15px 0; color: #007bff; font-size: 1.1rem;}}
        .metric {{display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee;}}
        .metric:last-child {{border-bottom: none;}}
        .metric.revenue strong {{color: #28a745; font-size: 1.2rem;}}
        .totals {{display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 20px 0;}}
        .total-card {{background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);}}
        .total-value {{font-size: 2rem; font-weight: bold; color: #007bff;}}
        .total-value.revenue {{color: #28a745;}}
        .total-label {{color: #666; font-size: 0.9rem;}}
        table {{width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);}}
        th, td {{padding: 12px; text-align: left; border-bottom: 1px solid #eee;}}
        th {{background: #f8f9fa; font-weight: 600;}}
        tr:hover {{background: #f8f9fa;}}
        .refresh {{float: right; padding: 8px 16px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;}}
        .refresh:hover {{background: #0056b3;}}
        .section {{margin-top: 30px;}}
    </style>
</head>
<body>
    <h1>📊 7-Day Revenue Sprint Dashboard <button class="refresh" onclick="location.reload()">🔄 Aktualisieren</button></h1>
    
    <div class="totals">
        <div class="total-card"><div class="total-value">{totals['clicks']}</div><div class="total-label">Gesamt-Klicks</div></div>
        <div class="total-card"><div class="total-value">{totals['conversions']}</div><div class="total-label">Conversions</div></div>
        <div class="total-card"><div class="total-value revenue">{totals['commission_eur']:.2f} €</div><div class="total-label">Provision</div></div>
    </div>
    
    <div class="section">
        <h2>📈 Affiliate-Programme</h2>
        <div class="grid">
            {program_cards}
        </div>
    </div>
    
    <div class="section">
        <h2>📅 Tägliche Statistiken (letzte 7 Tage)</h2>
        <table>
            <thead><tr><th>Datum</th><th>Page Views</th><th>Unique Visitors</th><th>Total Klicks</th><th>Affiliate Klicks</th><th>Conversions</th><th>Provision</th></tr></thead>
            <tbody>{daily_rows}</tbody>
        </table>
    </div>
    
    <div class="section">
        <h2>🖱️ Letzte Klicks</h2>
        <table>
            <thead><tr><th>Zeitstempel</th><th>Programm</th><th>Artikel</th><th>Source/Medium</th><th>IP Hash</th></tr></thead>
            <tbody>{clicks_rows}</tbody>
        </table>
    </div>
    
    <div class="section">
        <h2>💰 Letzte Conversions</h2>
        <table>
            <thead><tr><th>Zeitstempel</th><th>Programm</th><th>Betrag</th><th>Provision</th><th>Status</th></tr></thead>
            <tbody>{conv_rows}</tbody>
        </table>
    </div>
    
    <script>
        setInterval(() => location.reload(), 30000);
    </script>
</body>
</html>"""

def run_server(port=8080):
    os.chdir(SITE_DIR)
    server = HTTPServer(('0.0.0.0', port), TrackingHandler)
    print(f"Server running on http://0.0.0.0:{port}")
    print(f"Dashboard: http://0.0.0.0:{port}/dashboard")
    print(f"API: http://0.0.0.0:{port}/api/dashboard")
    print(f"Tracking endpoint: http://0.0.0.0:{port}/api/track")
    server.serve_forever()

if __name__ == "__main__":
    run_server()