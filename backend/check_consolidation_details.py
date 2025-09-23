#!/usr/bin/env python
"""Test getting consolidation details via API"""
import requests
import json

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

# Get list of consolidations
print("\n2. Getting consolidation list...")
response = requests.get(
    f"{base_url}/api/v1/delivery/consolidation-list",
    headers=headers
)

if response.status_code == 200:
    data = response.json()
    consolidations = data.get('data', [])
    print(f"Found {len(consolidations)} consolidations")

    if consolidations:
        # Get details for the first consolidation
        first_consol = consolidations[0]
        consol_id = first_consol['consolidation_id']

        print(f"\n3. Getting details for consolidation: {consol_id}")

        detail_response = requests.get(
            f"{base_url}/api/v1/delivery/consolidation/{consol_id}",
            headers=headers
        )

        if detail_response.status_code == 200:
            details = detail_response.json()['data']
            print(f"✓ Consolidation details retrieved successfully")
            print(f"\nConsolidation: {details['consolidation_id']}")
            print(f"  Name: {details['consolidation_name']}")
            print(f"  Status: {details['logistics_status']}")
            print(f"  Carrier: {details.get('carrier', 'N/A')}")
            print(f"  Tracking: {details.get('tracking_number', 'N/A')}")
            print(f"  PO Count: {details['po_count']}")
            print(f"  Total Items: {details.get('total_items', 0)}")
            print(f"\n  Purchase Orders:")
            for po in details.get('purchase_orders', []):
                print(f"    - {po['purchase_order_no']}: {po['supplier_name']}")
                print(f"      Status: {po['delivery_status']}")
                print(f"      Items: {po.get('item_count', 0)}")
        else:
            print(f"Failed to get details: {detail_response.status_code}")
            print(detail_response.text)
    else:
        print("No consolidations found to test")
else:
    print(f"Failed to get consolidation list: {response.status_code}")
    print(response.text)