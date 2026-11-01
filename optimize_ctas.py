#!/usr/bin/env python3
"""
CTA/Copy Optimization for 7-Day Income Strategy
Applies conversion-rate optimization best practices to all article CTAs
"""

import re
from pathlib import Path

SITE_DIR = Path(__file__).parent

# Article-specific optimized CTA configurations
CTA_OPTIMIZATIONS = {
    "mixo-review.html": {
        "cta_box_headline": "Landingpage in 5 Min live – kein Code nötig",
        "cta_primary_text": "Mixo kostenlos testen →",
        "cta_secondary_text": "Erst Review lesen",
        "email_hook": "Mixo-Setup-Checkliste (PDF) gratis",
    },
    "elevenlabs-review.html": {
        "cta_box_headline": "Professionelle KI-Stimmen für deine Inhalte",
        "cta_primary_text": "ElevenLabs kostenlos testen →",
        "cta_secondary_text": "Review lesen",
        "email_hook": "Audio-Content-Workflow (Notion) gratis",
    },
    "runpod-review.html": {
        "cta_box_headline": "GPU-Power ab $0.34/Std – per Sekunde abgerechnet",
        "cta_primary_text": "RunPod $10 Credit sichern →",
        "cta_secondary_text": "Vast.ai vergleichen",
        "email_hook": "GPU-Kostenrechner (Sheet) gratis",
    },
    "surfer-seo-review.html": {
        "cta_box_headline": "Content, der rankt – datenbasiert statt geraten",
        "cta_primary_text": "Surfer SEO 7 Tage testen →",
        "cta_secondary_text": "Review lesen",
        "email_hook": "SEO-Content-Checkliste (PDF) gratis",
    },
    "mixo-vs-carrd-vs-wix.html": {
        "cta_box_headline": "Das richtige Tool für dein Projekt wählen",
        "cta_primary_text": "Mixo testen (beste Affiliate-Konditionen) →",
        "cta_secondary_text": "Carrd testen (günstigster Einstieg)",
        "email_hook": "Website-Bauer-Entscheidungsmatrix (PDF) gratis",
    },
    "elevenlabs-vs-speechify.html": {
        "cta_box_headline": "Qualität (ElevenLabs) vs. Menge (Speechify)",
        "cta_primary_text": "ElevenLabs für Pros testen →",
        "cta_secondary_text": "Speechify für Vielleser testen",
        "email_hook": "TTS-Tool-Vergleichstabelle (Notion) gratis",
    },
    "runpod-vs-vast-vs-lambda.html": {
        "cta_box_headline": "Maximale GPU-Power für minimales Budget",
        "cta_primary_text": "RunPod $10 Credit sichern →",
        "cta_secondary_text": "Vast.ai Preise checken",
        "email_hook": "GPU-Cloud-Kostenrechner (Sheet) gratis",
    },
}

# Mid-article CTA configurations (inserted after first major section)
MID_ARTICLE_CTAS = {
    "mixo-review.html": {
        "headline": "Schnellstart: Deine erste KI-Website in 3 Minuten",
        "text": "Keine Kreditkarte nötig. Idee eingeben → Live-URL erhalten.",
        "button": "Jetzt starten (kostenlos)",
        "program": "mixo",
        "utm_content": "mixo-review_mid",
    },
    "elevenlabs-review.html": {
        "headline": "Hör dir die Qualität selbst an",
        "text": "10.000 Zeichen gratis. Deutsche Stimmen, Voice Cloning, API-Zugang.",
        "button": "Kostenlos testen",
        "program": "elevenlabs",
        "utm_content": "elevenlabs-review_mid",
    },
    "runpod-review.html": {
        "headline": "Deine erste GPU-Instance in 60 Sekunden",
        "text": "$10 Startguthaben. RTX 4090, A100, H100 – per Sekunde abgerechnet.",
        "button": "Credit einlösen",
        "program": "runpod",
        "utm_content": "runpod-review_mid",
    },
    "surfer-seo-review.html": {
        "headline": "Optimiere deinen ersten Artikel in 10 Minuten",
        "text": "Content Editor + SERP Analyzer 7 Tage kostenlos. Keine Kreditkarte.",
        "button": "Jetzt optimieren",
        "program": "surfer_seo",
        "utm_content": "surfer-seo-review_mid",
    },
}

def read_file(path):
    return path.read_text(encoding='utf-8')

def write_file(path, content):
    path.write_text(content, encoding='utf-8')

def optimize_cta_box(html, article_file):
    """Replace the main CTA box with optimized version"""
    config = CTA_OPTIMIZATIONS.get(article_file)
    if not config:
        return html
    
    # Pattern to find the CTA box
    cta_box_pattern = r'(<div class="cta-box">.*?</div>)'
    
    # Build optimized CTA box
    new_cta_box = f'''<div class="cta-box">
            <p style="margin-bottom: 15px; font-weight: 600;">{config["cta_box_headline"]}</p>
            <a class="cta-button" 
               href="{get_affiliate_url(article_file)}"
               target="_blank" rel="nofollow sponsored" 
               data-affiliate="{get_program_key(article_file)}" data-article="{article_file.replace('.html', '')}" 
               data-utm-source="organic" data-utm-medium="article" data-utm-campaign="7day_sprint" data-utm-content="{article_file.replace('.html', '')}_main">{config["cta_primary_text"]}</a>
            <a class="cta-button secondary" href="{article_file}">{config["cta_secondary_text"]}</a>
        </div>'''
    
    # Replace first occurrence only (main CTA box)
    html = re.sub(cta_box_pattern, new_cta_box, html, count=1, flags=re.DOTALL)
    return html

def optimize_email_capture(html, article_file):
    """Replace email capture with article-specific hook"""
    config = CTA_OPTIMIZATIONS.get(article_file)
    if not config:
        return html
    
    # Pattern to find email capture section
    email_pattern = r'(<!-- Email Capture in Article -->.*?</section>)'
    
    article_slug = article_file.replace('.html', '')
    new_email = f'''<!-- Email Capture in Article -->
        <section class="email-capture-article" style="background: #f8f9fa; border: 1px solid #e0e0e0; border-radius: 8px; padding: 30px; margin: 40px 0; text-align: center;">
            <h3 style="margin: 0 0 10px; color: #1a1a1a;">📧 {config["email_hook"]}</h3>
            <p style="margin: 0 0 20px; color: #555;">Exklusiv für Leser dieses Artikels – direkt ins Postfach.</p>
            <form id="email-form-article" style="display: flex; gap: 10px; max-width: 400px; margin: 0 auto; flex-wrap: wrap; justify-content: center;">
                <input type="email" name="email" placeholder="deine@email.de" required autocomplete="email" style="flex: 1; min-width: 200px; padding: 12px 16px; border: 2px solid #e0e0e0; border-radius: 6px; font-size: 1rem;">
                <button type="submit" class="cta-button" style="padding: 12px 24px;">Gratis sichern</button>
            </form>
            <p id="email-message-article" style="margin: 12px 0 0; font-size: 0.85rem; min-height: 20px;"></p>
            <p style="margin: 12px 0 0; font-size: 0.75rem; color: #888;">Kein Spam. Jederzeit abmeldbar. <a href="/lead-magnet/" style="color: #007bff;">Guide auch ohne Anmeldung lesen</a></p>
        </section>'''
    
    html = re.sub(email_pattern, new_email, html, count=1, flags=re.DOTALL)
    return html

def add_mid_article_cta(html, article_file):
    """Insert mid-article CTA after first h2 section"""
    config = MID_ARTICLE_CTAS.get(article_file)
    if not config:
        return html
    
    # Find position after first </ul> following an h2 (end of first major section)
    # Insert before the next h2
    mid_cta_html = f'''
        <div class="cta-box" style="background: #fff3cd; border-color: #ffc107;">
            <p style="margin-bottom: 10px; font-weight: 600;">{config["headline"]}</p>
            <p style="margin-bottom: 15px; color: #555;">{config["text"]}</p>
            <a class="cta-button" 
               href="{get_affiliate_url(article_file, config["utm_content"])}"
               target="_blank" rel="nofollow sponsored" 
               data-affiliate="{config["program"]}" data-article="{article_file.replace('.html', '')}" 
               data-utm-source="organic" data-utm-medium="article" data-utm-campaign="7day_sprint" data-utm-content="{config["utm_content"]}">{config["button"]}</a>
        </div>
'''
    
    # Insert after first major content section (after first </ul> that's followed by <h2>)
    pattern = r'(</ul>\s*<h2)'
    html = re.sub(pattern, f'{mid_cta_html}\\1', html, count=1)
    return html

def get_program_key(article_file):
    mapping = {
        "mixo-review.html": "mixo",
        "elevenlabs-review.html": "elevenlabs",
        "runpod-review.html": "runpod",
        "surfer-seo-review.html": "surfer_seo",
        "mixo-vs-carrd-vs-wix.html": "mixo",
        "elevenlabs-vs-speechify.html": "elevenlabs",
        "runpod-vs-vast-vs-lambda.html": "runpod",
    }
    return mapping.get(article_file, "mixo")

def get_affiliate_url(article_file, utm_content=None):
    program = get_program_key(article_file)
    base_urls = {
        "mixo": "https://mixo.io",
        "elevenlabs": "https://elevenlabs.io",
        "runpod": "https://runpod.io",
        "surfer_seo": "https://surferseo.com",
        "carrd": "https://carrd.co",
        "vast_ai": "https://vast.ai",
    }
    params = {
        "mixo": "ref",
        "elevenlabs": "via",
        "runpod": "ref",
        "surfer_seo": "ref",
        "carrd": "ref",
        "vast_ai": "ref",
    }
    base = base_urls.get(program, "https://mixo.io")
    param = params.get(program, "ref")
    content = utm_content or article_file.replace('.html', '')
    return f"{base}?{param}=7day_sprint&utm_source=organic&utm_medium=article&utm_campaign=7day_sprint&utm_content={content}"

def optimize_index_ctas(html):
    """Optimize index page CTAs"""
    # Update hero email capture
    hero_pattern = r'(<section class="email-capture" id="email-capture".*?</section>)'
    new_hero = '''<section class="email-capture" id="email-capture" style="background: linear-gradient(135deg, #007bff 0%, #0056b3 100%); color: white; padding: 40px; border-radius: 12px; margin: 30px 0; text-align: center;">
        <h2 style="margin: 0 0 15px; color: white; font-size: 1.5rem;">📧 Zero-Capital Guide: 7 Tage, 0€, echte Ergebnisse</h2>
        <p style="margin: 0 0 25px; opacity: 0.9; font-size: 1.05rem;">Tägliche Checkliste, 5 Erfolgsfaktoren, 0€ Tool-Stack, Content-Templates – nur für Abonnenten.</p>
        <form id="email-form" style="display: flex; gap: 10px; max-width: 400px; margin: 0 auto; flex-wrap: wrap; justify-content: center;">
            <input type="email" name="email" placeholder="deine@email.de" required autocomplete="email" style="flex: 1; min-width: 200px; padding: 14px 16px; border: none; border-radius: 8px; font-size: 1rem;">
            <button type="submit" style="background: #ffc107; color: #1a1a1a; padding: 14px 28px; border: none; border-radius: 8px; font-size: 1rem; font-weight: 700; cursor: pointer; transition: background 0.2s;">Guide jetzt sichern</button>
        </form>
        <p id="email-message" style="margin: 15px 0 0; font-size: 0.9rem; min-height: 20px;"></p>
        <p style="margin: 15px 0 0; font-size: 0.8rem; opacity: 0.8;">Kein Spam. Jederzeit abmeldbar. <a href="/lead-magnet/" style="color: #ffc107; text-decoration: underline;">Guide auch ohne Anmeldung lesen</a></p>
    </section>'''
    html = re.sub(hero_pattern, new_hero, html, count=1, flags=re.DOTALL)
    
    # Update post card CTAs to be more specific
    # Mixo card
    html = html.replace(
        'Zu Mixo (50% Provision)</a>',
        'Mixo kostenlos testen →</a>'
    )
    # ElevenLabs card
    html = html.replace(
        'Zu ElevenLabs (50% recurring)</a>',
        'ElvenLabs 10k Zeichen gratis →</a>'
    )
    # RunPod card (index)
    html = html.replace(
        'Zu RunPod (recurring)</a>',
        'RunPod $10 Credit holen →</a>'
    )
    # GPU comparison card
    html = html.replace(
        'RunPod testen (20% recurring)</a>',
        'RunPod $10 Credit sichern →</a>'
    )
    
    return html

def main():
    article_files = [
        "mixo-review.html",
        "elevenlabs-review.html", 
        "runpod-review.html",
        "surfer-seo-review.html",
        "mixo-vs-carrd-vs-wix.html",
        "elevenlabs-vs-speechify.html",
        "runpod-vs-vast-vs-lambda.html",
    ]
    
    print("Optimizing article CTAs...")
    for article in article_files:
        path = SITE_DIR / article
        if not path.exists():
            print(f"  SKIP: {article} not found")
            continue
        
        html = read_file(path)
        original = html
        
        # Apply optimizations
        html = optimize_cta_box(html, article)
        html = optimize_email_capture(html, article)
        html = add_mid_article_cta(html, article)
        
        if html != original:
            write_file(path, html)
            print(f"  ✓ {article} optimized")
        else:
            print(f"  = {article} no changes")
    
    # Optimize index
    index_path = SITE_DIR / "index.html"
    if index_path.exists():
        html = read_file(index_path)
        html = optimize_index_ctas(html)
        write_file(index_path, html)
        print(f"  ✓ index.html optimized")
    
    print("\nDone! All CTAs optimized with:")
    print("  - Benefit-driven headlines")
    print("  - Article-specific email hooks")
    print("  - Mid-article CTAs for higher conversion")
    print("  - Unique UTM content for A/B tracking")

if __name__ == "__main__":
    main()