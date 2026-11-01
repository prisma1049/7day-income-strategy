#!/usr/bin/env python3
import tracking
import json

data = tracking.get_dashboard_data()
print(json.dumps(data, indent=2))