#!/usr/bin/env python3
"""
Add affiliate CTA buttons with tracked links to all articles
"""

from pathlib import Path

SITE_DIR = Path(__file__).parent

ARTICLE_AFFILIATES = {
    "mixo-review.html": ["mixo"],
    "elevenlabs-review.html": ["elevenlabs"],
    "runpod-review.html": ["runpod", "vast_ai"],
    "surfer-seo-review.html": ["surfer_seo"],
    "mixo-vs-carrd-vs-wix.html": ["mixo", "carrd"],
    "elevenlabs-vs-speechify.html": ["elevenlabs"],
}

AFFILIATE_NAMES = {
    "mixo": "Mixo",
    "elevenlabs": "ElevenLabs",
    "runpod": "RunPod",
    "surfer_seo": "Surfer SEO",
    "carrd": "Carrd",
    "vast_ai": "Vast.ai",
}

def get_article_slug(filename):
    return filename.replace('.html', '')

def build_tracked_url(program, article_slug):
    return f"/go/{program}/{article_slug}"

def generate_cta_section(affiliates, article_slug):
    """Generate CTA button section for affiliate links."""
    cta_html = '\n        <h2>Jetzt testen</h2>\n        <div style="display: flex; flex-wrap: wrap; gap: 12px; margin: 20px 0;">\n'
    for prog in affiliates:
        name = AFFILIATE_NAMES.get(prog, prog)
        url = build_tracked_url(prog, article_slug)
        cta_html += f'            <a href="{url}" style="display: inline-block; background: #007bff; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: 600; transition: background 0.2s;">{name} ausprobieren →</a>\n'
    cta_html += '        </div>\n'
    return cta_html

def update_article(filepath, affiliates):
    content = filepath.read_text(encoding='utf-8')
    article_slug = get_article_slug(filepath.name)
    
    # Generate CTA section
    cta_section = generate_cta_section(affiliates, article_slug)
    
    # Insert CTA before the disclosure div
    if '<div class="disclosure">' in content:
        content = content.replace('<div class="disclosure">', cta_section + '<div class="disclosure">')
    elif '<div class="disclosure">' in content.replace('class="disclosure"', 'class="disclosure"'):
        # Try alternative
        content = content.replace('class="disclosure"', cta_section + 'class="disclosure"', 1)
    else:
        # Fallback: insert before closing article tag
        content = content.replace('</article>', cta_section + '</article>')
    
    filepath.write_text(content, encoding='utf-8')
    print(f"Added CTA to {filepath.name} for: {', '.join(affiliates)}")

def main():
    for filename, affiliates in ARTICLE_AFFILIATES.items():
        filepath = SITE_DIR / filename
        if filepath.exists():
            update_article(filepath, affiliates)
        else:
            print(f"File not found: {filename}")
    
    print("\nAll articles updated with CTA buttons!")

if __name__ == "__main__":
    main()