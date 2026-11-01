#!/usr/bin/env python3
import tracking

data = tracking.get_dashboard_data()
print('=== DASHBOARD DATA ===')
print(f"Total clicks: {sum(c['clicks'] for c in data['clicks_by_program'])}")
print(f"Clicks by program: {data['clicks_by_program']}")
print(f"Conversions: {data['conversions_by_program']}")
print(f"Daily stats (last 7): {len(data['daily_stats'])} days")
for d in data['daily_stats']:
    print(f"  {d['date']}: views={d.get('page_views',0)}, visitors={d.get('unique_visitors',0)}, clicks={d.get('total_clicks',0)}, affiliate_clicks={d.get('affiliate_clicks',0)}, conversions={d.get('conversions',0)}, revenue={d.get('commission_eur',0)}€")