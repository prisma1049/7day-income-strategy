#!/usr/bin/env python3
"""
Update all HTML articles with tracked affiliate links
"""

from pathlib import Path
import re

SITE_DIR = Path(__file__).parent

# Map article files to their primary affiliate programs
ARTICLE_AFFILIATES = {
    "mixo-review.html": ["mixo"],
    "elevenlabs-review.html": ["elevenlabs"],
    "runpod-review.html": ["runpod"],
    "surfer-seo-review.html": ["surfer_seo"],
    "mixo-vs-carrd-vs-wix.html": ["mixo", "carrd"],
    "elevenlabs-vs-speechify.html": ["elevenlabs"],
    "runpod-vs-vast-vs-lambda.html": ["runpod", "vast_ai"],
    "together-ai-review.html": ["together_ai"],
}

def get_article_slug(filename):
    return filename.replace('.html', '')

def build_tracked_url(program, article_slug):
    return f"/go/{program}/{article_slug}"

def update_article(filepath, affiliates):
    content = filepath.read_text(encoding='utf-8')
    article_slug = get_article_slug(filepath.name)
    
    # Replace external affiliate links with tracked versions
    # Pattern: https://program-domain.com/... with affiliate params
    for prog in affiliates:
        tracked_url = build_tracked_url(prog, article_slug)
        
        # Replace various link patterns
        if prog == "mixo":
            content = re.sub(
                r'href=["\']https?://mixo\.io[^"\']*["\']',
                f'href="{tracked_url}"',
                content
            )
        elif prog == "elevenlabs":
            content = re.sub(
                r'href=["\']https?://elevenlabs\.io[^"\']*["\']',
                f'href="{tracked_url}"',
                content
            )
        elif prog == "runpod":
            content = re.sub(
                r'href=["\']https?://runpod\.io[^"\']*["\']',
                f'href="{tracked_url}"',
                content
            )
        elif prog == "surfer_seo":
            content = re.sub(
                r'href=["\']https?://surferseo\.com[^"\']*["\']',
                f'href="{tracked_url}"',
                content
            )
        elif prog == "carrd":
            content = re.sub(
                r'href=["\']https?://carrd\.co[^"\']*["\']',
                f'href="{tracked_url}"',
                content
            )
        elif prog == "vast_ai":
            content = re.sub(
                r'href=["\']https?://vast\.ai[^"\']*["\']',
                f'href="{tracked_url}"',
                content
            )
        elif prog == "together_ai":
            content = re.sub(
                r'href=["\']https?://api\.together\.xyz[^"\']*["\']',
                f'href="{tracked_url}"',
                content
            )
            content = re.sub(
                r'href=["\']https?://together\.ai[^"\']*["\']',
                f'href="{tracked_url}"',
                content
            )
            content = re.sub(
                r'href=["\']https?://together\.xyz[^"\']*["\']',
                f'href="{tracked_url}"',
                content
            )
    
    # Also add tracking to any generic "Affiliate-Link" or CTA buttons
    content = re.sub(
        r'href=["\']([^"\']*(?:mixo|elevenlabs|runpod|surferseo|carrd|vast\.ai|together\.ai|together\.xyz|api\.together\.xyz)[^"\']*)["\']',
        lambda m: f'href="{build_tracked_url(m.group(1).split(".")[0].replace("https://", "").replace("http://", ""), article_slug)}"' if any(p in m.group(1) for p in affiliates) else m.group(0),
        content
    )
    
    filepath.write_text(content, encoding='utf-8')
    print(f"Updated {filepath.name} with tracked links for: {', '.join(affiliates)}")

def main():
    for filename, affiliates in ARTICLE_AFFILIATES.items():
        filepath = SITE_DIR / filename
        if filepath.exists():
            update_article(filepath, affiliates)
        else:
            print(f"File not found: {filename}")
    
    # Also update index.html to use tracked links for CTA buttons
    index_path = SITE_DIR / "index.html"
    if index_path.exists():
        content = index_path.read_text(encoding='utf-8')
        # Update any external affiliate links in index
        for prog in ["mixo", "elevenlabs", "runpod", "surfer_seo", "together_ai"]:
            tracked = build_tracked_url(prog, "index")
            content = re.sub(
                rf'href=["\']https?://{prog.replace("_", "")}\.[^"\']*["\']',
                f'href="{tracked}"',
                content
            )
        index_path.write_text(content, encoding='utf-8')
        print("Updated index.html")
    
    print("\nAll articles updated with tracked affiliate links!")

if __name__ == "__main__":
    main()