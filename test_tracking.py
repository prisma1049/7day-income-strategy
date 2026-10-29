import tracking
print('Testing click logging...')
click_id = tracking.log_click('mixo', 'mixo-review', 'twitter', 'social', '7day_sprint', 'mixo-review')
print(f'Click logged with ID: {click_id}')

print('Testing dashboard data...')
data = tracking.get_dashboard_data()
print(f'Total clicks: {sum(c["clicks"] for c in data["clicks_by_program"])}')
print(f'Programs with clicks: {data["clicks_by_program"]}')

# Test conversion logging
print('Testing conversion logging...')
tracking.log_conversion('mixo', click_id, 29.00, 14.50, 'confirmed', 'Test conversion')
data2 = tracking.get_dashboard_data()
print(f'Conversions: {data2["conversions_by_program"]}')
print(f'Total commission: {sum(c["total_commission"] for c in data2["conversions_by_program"])}')