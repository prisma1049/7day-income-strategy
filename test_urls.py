#!/usr/bin/env python3
from tracking import generate_affiliate_url

slug = 'runpod_vast_lambda_comparison'
for prog in ['runpod', 'vast_ai']:
    url = generate_affiliate_url(prog, slug)
    print(f'{prog}: {url}')