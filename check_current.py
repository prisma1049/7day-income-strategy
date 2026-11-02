#!/usr/bin/env python3
import tracking
data = tracking.get_dashboard_data()
print('Clicks by program:', data['clicks_by_program'])
print('Daily stats:')
for d in data['daily_stats']:
    print(f"  {d['date']}: views={d.get('page_views',0)}, visitors={d.get('unique_visitors',0)}, clicks={d.get('total_clicks',0)}, affiliate_clicks={d.get('affiliate_clicks',0)}, conversions={d.get('conversions',0)}, revenue={d.get('commission_eur',0)}€")