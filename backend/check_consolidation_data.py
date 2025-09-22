#!/usr/bin/env python
"""Check consolidation data"""
import requests
import json
from datetime import datetime

# API endpoint
base_url = "http://localhost:5000"
login_url = f"{base_url}/api/v1/auth/login"

# Login first to get token
login_data = {
    "username": "harry123180",
    "password": "password123"
}

print("1. Logging in...")
login_response = requests.post(login_url, json=login_data)
if login_response.status_code != 200:
    print(f"Login failed: {login_response.text}")
    exit(1)

response_json = login_response.json()
if 'data' in response_json:
    token = response_json['data']['access_token']
else:
    token = response_json.get('access_token', response_json.get('token', None))

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
print("✓ Login successful")

# Get consolidation list
print("\n2. Getting consolidation list...")
response = requests.get(
    f"{base_url}/api/v1/delivery/consolidation-list",
    headers=headers
)

if response.status_code == 200:
    data = response.json()
    print(f"Found {len(data.get('data', []))} consolidations")

    for consol in data.get('data', []):
        print(f"\n=== Consolidation: {consol['consolidation_id']} ===")
        print(f"Name: {consol['consolidation_name']}")
        print(f"Status: {consol['logistics_status']}")
        print(f"PO Count: {consol['po_count']}")
        print(f"Purchase Orders: {len(consol.get('purchase_orders', []))}")

        if consol.get('purchase_orders'):
            print("Included POs:")
            for po in consol['purchase_orders']:
                print(f"  - {po['purchase_order_no']}: {po['supplier_name']}")
        else:
            print("No purchase orders linked!")

        # Check consolidation_pos table directly
        print("\n3. Checking consolidation_pos table for", consol['consolidation_id'])

else:
    print(f"Failed to get consolidation list: {response.status_code}")
    print(response.text)