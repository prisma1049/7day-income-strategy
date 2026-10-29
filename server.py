#!/usr/bin/env python3
"""
Lightweight tracking redirect server for 7-Day Revenue Sprint
Handles affiliate link clicks with tracking, serves static site, provides dashboard API
"""

import os
import json
import hashlib
import sqlite3
from datetime import datetime, timezone
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path

SITE_DIR = Path(__file__).parent
DB_PATH = SITE_DIR / "tracking.db"

# Affiliate programs config
AFFILIATE_PROGRAMS = {
    "mixo": {"name": "Mixo", "base_url": "https://mixo.io", "param": "ref", "rate": 0.50},
    "elevenlabs": {"name": "ElevenLabs", "base_url": "https://elevenlabs.io", "param": "via", "rate": 0.50},
    "runpod": {"name": "RunPod", "base_url": "https://runpod.io", "param": "ref", "rate": 0.20},
    "surfer_seo": {"name": "Surfer SEO", "base_url": "https://surferseo.com", "param": "ref", "rate": 0.30},
    "carrd": {"name": "Carrd", "base_url": "https://carrd.co", "param": "ref", "rate": 0.30},
    "vast_ai": {"name": "Vast.ai", "base_url": "https://vast.ai", "param": "ref", "rate": 0.10},
}

ARTICLE_MAP = {
    "mixo-review.html": "mixo",
    "elevenlabs-review.html": "elevenlabs",
    "runpod-review.html": "runpod",
    "surfer-seo-review.html": "surfer_seo",
    "mixo-vs-carrd-vs-wix.html": "mixo_carrd_comparison",
    "elevenlabs-vs-speechify.html": "elevenlabs_speechify_comparison",
    "runpod-review.html": "runpod_vast_comparison",
    "content-framework.md": "framework",
    "editorial-calendar.md": "calendar",
}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def log_click(program_key, article_slug, request):
    """Log click to database."""
    ip = request.client_address[0]
    ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:16]
    user_agent = request.headers.get('User-Agent', '')[:500]
    referrer = request.headers.get('Referer', '')[:500]
    
    # Parse UTM params from query
    query = parse_qs(urlparse(request.path).query)
    utm_source = query.get('utm_source', [''])[0]
    utm_medium = query.get('utm_medium', [''])[0]
    utm_campaign = query.get('utm_campaign', [''])[0]
    utm_content = query.get('utm_content', [article_slug])[0]
    
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
        
        # Affiliate redirect endpoint: /go/<program>/<article_slug>
        if path.startswith('/go/'):
            self.handle_redirect(path, parsed.query)
            return
        
        # Dashboard API
        if path == '/api/dashboard':
            self.send_json(get_dashboard_data())
            return
        
        # Dashboard HTML page
        if path == '/dashboard' or path == '/dashboard/':
            self.serve_dashboard()
            return
        
        # Default: serve static files
        super().do_GET()
    
    def handle_redirect(self, path, query):
        """Handle /go/<program>/<article_slug>?utm_* redirects."""
        parts = path.split('/')
        if len(parts) < 4:
            self.send_error(404, "Invalid redirect path")
            return
        
        program_key = parts[2]
        article_slug = parts[3]
        
        if program_key not in AFFILIATE_PROGRAMS:
            self.send_error(404, f"Unknown program: {program_key}")
            return
        
        # Log the click
        log_click(program_key, article_slug, self)
        
        # Build destination URL
        program = AFFILIATE_PROGRAMS[program_key]
        base_url = program["base_url"]
        param = program["param"]
        
        # Parse incoming UTM params
        utm_params = parse_qs(query)
        
        # Build outgoing URL with affiliate param + UTM
        from urllib.parse import urlencode, urlunparse
        outbound_params = {
            param: "7day_sprint",
            "utm_source": utm_params.get('utm_source', ['organic'])[0],
            "utm_medium": utm_params.get('utm_medium', ['article'])[0],
            "utm_campaign": utm_params.get('utm_campaign', ['7day_sprint'])[0],
            "utm_content": utm_params.get('utm_content', [article_slug])[0],
        }
        
        dest_url = f"{base_url}?{urlencode(outbound_params)}"
        
        # Redirect
        self.send_response(302)
        self.send_header('Location', dest_url)
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
    
    def serve_dashboard(self):
        """Serve the dashboard HTML."""
        dashboard_html = self.generate_dashboard_html()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(dashboard_html.encode('utf-8'))
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def generate_dashboard_html(self):
        data = get_dashboard_data()
        
        # Build program cards
        program_cards = ""
        for prog in AFFILIATE_PROGRAMS.values():
            key = prog["name"].lower().replace(" ", "_").replace(".", "_")
            clicks = next((c['clicks'] for c in data['clicks_by_program'] if c['affiliate_program'] == key), 0)
            conv = next((c for c in data['conversions_by_program'] if c['affiliate_program'] == key), None)
            conversions = conv['conversions'] if conv else 0
            commission = conv['total_commission'] if conv else 0
            ctr = f"{(conversions/clicks*100):.1f}%" if clicks > 0 else "0%"
            
            program_cards += f"""
            <div class="card">
                <h3>{prog['name']}</h3>
                <div class="metric"><span>Klicks</span><strong>{clicks}</strong></div>
                <div class="metric"><span>Conversions</span><strong>{conversions}</strong></div>
                <div class="metric"><span>CTR</span><strong>{ctr}</strong></div>
                <div class="metric revenue"><span>Provision</span><strong>{commission:.2f} €</strong></div>
            </div>
            """
        
        # Recent clicks table
        clicks_rows = ""
        for c in data['recent_clicks'][:20]:
            ts = c['timestamp'][:19].replace('T', ' ')
            clicks_rows += f"<tr><td>{ts}</td><td>{c['affiliate_program']}</td><td>{c['article_slug']}</td><td>{c['utm_source']}/{c['utm_medium']}</td><td>{c['ip_hash']}</td></tr>"
        
        # Daily stats
        daily_rows = ""
        for d in data['daily_stats']:
            daily_rows += f"<tr><td>{d['date']}</td><td>{d['page_views']}</td><td>{d['unique_visitors']}</td><td>{d['total_clicks']}</td><td>{d['affiliate_clicks']}</td><td>{d['conversions']}</td><td>{d['commission_eur']:.2f} €</td></tr>"
        
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
        <div class="grid">{program_cards}</div>
    </div>
    
    <div class="section">
        <h2>📅 Tägliche Statistiken (letzte 7 Tage)</h2>
        <table>
            <thead><tr><th>Datum</th><th>Page Views</th><th>Unique Visitors</th><th>Total Klicks</th><th>Affiliate Klicks</th><th>Conversions</th><th>Provision</th></tr></thead>
            <tbody>{daily_rows or '<tr><td colspan="7">Keine Daten</td></tr>'}</tbody>
        </table>
    </div>
    
    <div class="section">
        <h2>🖱️ Letzte Klicks</h2>
        <table>
            <thead><tr><th>Zeitstempel</th><th>Programm</th><th>Artikel</th><th>Source/Medium</th><th>IP Hash</th></tr></thead>
            <tbody>{clicks_rows or '<tr><td colspan="5">Keine Klicks</td></tr>'}</tbody>
        </table>
    </div>
    
    <div class="section">
        <h2>💰 Letzte Conversions</h2>
        <table>
            <thead><tr><th>Zeitstempel</th><th>Programm</th><th>Betrag</th><th>Provision</th><th>Status</th></tr></thead>
            <tbody>
"""
        for c in data['recent_conversions']:
            ts = c['timestamp'][:19].replace('T', ' ')
            program_cards += f"<tr><td>{ts}</td><td>{c['affiliate_program']}</td><td>{c['amount_eur']:.2f} €</td><td>{c['commission_eur']:.2f} €</td><td>{c['status']}</td></tr>"
        
        return dashboard_html + """
            </tbody>
        </table>
    </div>
    
    <script>
        // Auto-refresh every 30 seconds
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
    print(f"Affiliate redirects: http://0.0.0.0:{port}/go/<program>/<article>")
    server.serve_forever()

if __name__ == "__main__":
    run_server()