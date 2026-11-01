#!/usr/bin/env python3
"""Fix mid-article CTA placement properly"""

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
    "runpod-vs-vast-lambda.html",
]

def read_file(path):
    return path.read_text(encoding='utf-8')

def write_file(path, content):
    path.write_text(content, encoding='utf-8')

for article in article_files:
    path = SITE_DIR / article
    if not path.exists():
        # Try with correct filename
        alt = article.replace("runpod-vs-vast-lambda.html", "runpod-vs-vast-vs-lambda.html")
        path = SITE_DIR / alt
        if not path.exists():
            continue
    
    html = read_file(path)
    
    # Fix 1: Close the <ul> properly before the CTA box
    # Pattern: last </li>\n        </ul>\n        <div class="cta-box" 
    # The issue is </li> and </ul> are on separate lines but CTA is between them
    
    # Find: </li>\n        \n        <div class="cta-box" style="background: #fff3cd...
    # Replace with: </li>\n        </ul>\n\n        <div class="cta-box"...
    
    html = re.sub(
        r'(</li>)\s*\n\s*(<div class="cta-box" style="background: #fff3cd; border-color: #ffc107;">.*?</div>)\s*\n\s*(</ul>)',
        r'\1\n        </ul>\n\n\2\n\n\3',
        html,
        flags=re.DOTALL
    )
    
    # Also handle case where </ul> is after the CTA
    html = re.sub(
        r'(</li>)\s*\n\s*(<div class="cta-box" style="background: #fff3cd; border-color: #ffc107;">.*?</div>)\s*\n\s*(<h2>)',
        r'\1\n        </ul>\n\n\2\n\n\3',
        html,
        flags=re.DOTALL
    )
    
    write_file(path, html)
    print(f"Fixed: {article}")

print("Done!")