#!/usr/bin/env python3
"""Remove duplicate mid-article CTAs"""

import re
from pathlib import Path

SITE_DIR = Path(__file__).parent

article_files = [
    "mixo-review.html",
    "elevenlabs-review.html", 
    "runpod-review.html",
    "surfer-seo-review.html",
    "mixo-vs-carrd-vs-wix.html",
    "elevenlabs-vs-speechify.html",
    "runpod-vs-vast-vs-lambda.html",
]

def read_file(path):
    return path.read_text(encoding='utf-8')

def write_file(path, content):
    path.write_text(content, encoding='utf-8')

for article in article_files:
    path = SITE_DIR / article
    if not path.exists():
        continue
    
    html = read_file(path)
    
    # Remove duplicate mid-article CTA boxes (keep only the first one after first </ul>)
    # Pattern: find ALL mid-article CTAs, keep only first
    cta_pattern = r'(<div class="cta-box" style="background: #fff3cd; border-color: #ffc107;">.*?</div>)'
    matches = list(re.finditer(cta_pattern, html, re.DOTALL))
    
    if len(matches) > 1:
        # Remove all but the first
        for match in reversed(matches[1:]):
            html = html[:match.start()] + html[match.end():]
        print(f"  Removed {len(matches)-1} duplicate CTAs from {article}")
    
    # Fix indentation of the remaining mid-article CTA
    html = re.sub(
        r'(</ul>)\s*\n(<div class="cta-box" style="background: #fff3cd; border-color: #ffc107;">)',
        r'\1\n\n        \2',
        html
    )
    
    write_file(path, html)

print("Done!")