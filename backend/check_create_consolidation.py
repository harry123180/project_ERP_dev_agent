#!/usr/bin/env python
"""Test creating consolidation via API"""
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

# First get available POs to consolidate
print("\n2. Getting available POs...")
response = requests.get(
    f"{base_url}/api/v1/delivery/maintenance-list?supplier_region=international&status=shipped",
    headers=headers
)

if response.status_code == 200:
    data = response.json()
    eligible_pos = [po for po in data.get('data', []) if po.get('can_be_consolidated')]
    print(f"Found {len(eligible_pos)} eligible POs for consolidation")

    if eligible_pos:
        # Take first 2 POs for test
        test_pos = eligible_pos[:2]
        po_numbers = [po['purchase_order_no'] for po in test_pos]

        print(f"\n3. Creating consolidation with POs: {po_numbers}")

        consolidation_data = {
            "consolidation_name": f"Test Consolidation {datetime.now().strftime('%H:%M:%S')}",
            "purchase_order_nos": po_numbers,
            "expected_delivery_date": "2025-10-01",
            "carrier": "DHL",
            "tracking_number": "DHL123456789",
            "logistics_notes": "Test consolidation"
        }

        response = requests.post(
            f"{base_url}/api/v1/delivery/consolidations",
            headers=headers,
            json=consolidation_data
        )

        if response.status_code == 201:
            result = response.json()
            print(f"✓ Consolidation created: {result['data']['consolidation_id']}")

            # Now get the consolidation details
            consol_id = result['data']['consolidation_id']
            print(f"\n4. Getting consolidation details for {consol_id}...")

            detail_response = requests.get(
                f"{base_url}/api/v1/delivery/consolidation/{consol_id}",
                headers=headers
            )

            if detail_response.status_code == 200:
                details = detail_response.json()['data']
                print(f"✓ Consolidation details retrieved")
                print(f"   Name: {details['consolidation_name']}")
                print(f"   Status: {details['logistics_status']}")
                print(f"   PO Count: {details['po_count']}")
                print(f"   Purchase Orders:")
                for po in details.get('purchase_orders', []):
                    print(f"     - {po['purchase_order_no']}: {po['supplier_name']}")
            else:
                print(f"Failed to get details: {detail_response.text}")

        else:
            print(f"Failed to create consolidation: {response.status_code}")
            print(response.text)
    else:
        print("No eligible POs found for consolidation")
        print("Need international POs with 'shipped' status that aren't already consolidated")
else:
    print(f"Failed to get PO list: {response.status_code}")
    print(response.text)