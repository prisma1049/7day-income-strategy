#!/usr/bin/env python3
"""Fix HTML structure issues in all articles"""

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
    
    # Fix 1: Ensure <h2> has proper indentation after mid-article CTA
    html = re.sub(
        r'(</div>)\s*\n(<h2>)',
        r'\1\n\n        \2',
        html
    )
    
    # Fix 2: Fix incomplete <li> items (missing </li> before </ul>)
    html = re.sub(
        r'(<li>[^<]*?)\s*\n\s*(</ul>)',
        r'\1</li>\n        \2',
        html
    )
    
    # Fix 3: Remove stray empty lines in <ul>
    html = re.sub(
        r'(<ul>)\s*\n\s*\n',
        r'\1\n',
        html
    )
    
    # Fix 4: Ensure consistent indentation for <ul> content
    html = re.sub(
        r'(<ul>)\s*\n(            <li>)',
        r'\1\n\2',
        html
    )
    
    write_file(path, html)
    print(f"Fixed: {article}")

print("Done!")