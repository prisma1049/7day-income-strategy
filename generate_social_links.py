#!/usr/bin/env python3
"""Generate tracked affiliate links for social media posting."""

import sys
sys.path.insert(0, '/root/7day-income-site')
import tracking

platforms = ['reddit', 'twitter', 'linkedin', 'indiehackers', 'hackernews']
article_slug = 'runpod_vast_lambda_comparison'

print("=== TRACKED AFFILIATE LINKS FOR SOCIAL MEDIA ===\n")

for platform in platforms:
    print(f"=== {platform.upper()} ===")
    # RunPod link
    runpod_url = tracking.generate_affiliate_url(
        'runpod', article_slug, 
        utm_source=platform, 
        utm_medium='social', 
        utm_campaign='7day_sprint', 
        utm_content=f'{platform}_gpu_comparison'
    )
    print(f'RunPod: {runpod_url}')
    # Vast.ai link
    vast_url = tracking.generate_affiliate_url(
        'vast_ai', article_slug, 
        utm_source=platform, 
        utm_medium='social', 
        utm_campaign='7day_sprint', 
        utm_content=f'{platform}_gpu_comparison'
    )
    print(f'Vast.ai: {vast_url}')
    print()

# Also article URL with tracking
article_base = "https://florian.github.io/7day-income-strategy/runpod-vs-vast-vs-lambda.html"
print("=== ARTICLE URLS WITH UTM ===")
for platform in platforms:
    from urllib.parse import urlencode
    utm_params = {
        "utm_source": platform,
        "utm_medium": "social",
        "utm_campaign": "7day_sprint",
        "utm_content": f"{platform}_gpu_comparison"
    }
    query = urlencode(utm_params)
    print(f"{platform}: {article_base}?{query}")