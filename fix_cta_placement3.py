#!/usr/bin/env python3
"""Fix mid-article CTA placement - remove duplicate </ul>"""

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
    
    # Remove duplicate </ul> after the mid-article CTA box
    # Pattern: </ul>\n\n<div class="cta-box" style="background: #fff3cd...">\n...\n        </div>\n\n</ul>
    html = re.sub(
        r'(</ul>)\s*\n\s*(<div class="cta-box" style="background: #fff3cd; border-color: #ffc107;">.*?</div>)\s*\n\s*(</ul>)',
        r'\1\n\n\2',
        html,
        flags=re.DOTALL
    )
    
    write_file(path, html)
    print(f"Fixed: {article}")

print("Done!")