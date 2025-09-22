#!/usr/bin/env python
"""Debug consolidation creation"""
import requests
import json
from datetime import datetime

# API endpoint
base_url = "http://localhost:5000"
login_url = f"{base_url}/api/v1/auth/login"
consolidation_url = f"{base_url}/api/v1/delivery/consolidations"
maintenance_url = f"{base_url}/api/v1/delivery/maintenance-list"

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
    if not token:
        print(f"Unexpected response structure: {json.dumps(response_json, indent=2)}")
        exit(1)

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
print("✓ Login successful")

# Get international POs that are shipped
print("\n2. Getting international POs with 'shipped' status...")
response = requests.get(
    f"{maintenance_url}?supplier_region=international",
    headers=headers
)

if response.status_code != 200:
    print(f"Failed to get PO list: {response.text}")
    exit(1)

po_data = response.json()
shipped_pos = []

if 'data' in po_data:
    for po in po_data['data']:
        # Check if PO is shipped and not already in a consolidation
        if (po.get('delivery_status') == 'shipped' and
            not po.get('consolidation_id')):
            shipped_pos.append(po['purchase_order_no'])
            print(f"   - {po['purchase_order_no']}: {po['supplier_name']} (Status: {po['delivery_status']})")

if not shipped_pos:
    print("   No eligible POs found for consolidation")
    print("   Requirements: International POs with 'shipped' status and no existing consolidation")
    exit(0)

# Test consolidation creation
print(f"\n3. Creating consolidation with {len(shipped_pos)} POs...")
consolidation_data = {
    "po_numbers": shipped_pos[:2],  # Use first 2 POs for testing
    "name": f"TEST-CONSOL-{datetime.now().strftime('%Y%m%d%H%M%S')}"
}

print(f"   Request URL: {consolidation_url}")
print(f"   Request data: {json.dumps(consolidation_data, indent=2)}")

response = requests.post(consolidation_url, json=consolidation_data, headers=headers)
print(f"   Response status: {response.status_code}")

if response.status_code == 201:
    print("   ✓ Consolidation created successfully!")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
elif response.status_code == 404:
    print("   ✗ 404 Error: Route not found")
    print("   Checking available routes...")

    # Try to list all delivery routes
    test_routes = [
        '/api/v1/delivery/maintenance-list',
        '/api/v1/delivery/consolidations',
        '/api/v1/delivery/consolidation-list'
    ]

    for route in test_routes:
        test_response = requests.options(f"{base_url}{route}", headers=headers)
        print(f"      {route}: {test_response.status_code}")
else:
    print(f"   ✗ Error: {response.text}")