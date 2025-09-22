#!/usr/bin/env python
"""Check all registered routes in the Flask app"""
from app import create_app

app = create_app('development')

print("=== ALL REGISTERED ROUTES ===\n")

# Get all routes
routes = []
for rule in app.url_map.iter_rules():
    methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
    if methods:
        routes.append({
            'endpoint': rule.endpoint,
            'methods': methods,
            'url': rule.rule
        })

# Sort by URL
routes.sort(key=lambda x: x['url'])

# Print all routes
for route in routes:
    print(f"{route['methods']:8} {route['url']}")

# Check specifically for consolidation routes
print("\n=== DELIVERY ROUTES ===")
for route in routes:
    if 'delivery' in route['url']:
        print(f"{route['methods']:8} {route['url']}")