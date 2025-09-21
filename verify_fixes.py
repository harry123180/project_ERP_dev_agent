"""
Simple script to verify the two fixes:
1. Purchase order user fields display
2. Batch receiving functionality
"""
import requests
import json

BASE_URL = "http://localhost:5000/api/v1"

# Login first
login_response = requests.post(f"{BASE_URL}/auth/login", json={
    "username": "procurement",
    "password": "proc123"
})

if login_response.status_code == 200:
    token = login_response.json()['access_token']
    print("✅ Login successful")

    headers = {'Authorization': f'Bearer {token}'}

    # Test 1: Check if purchase orders show user details
    print("\n=== Test 1: Purchase Order User Fields ===")
    po_response = requests.get(f"{BASE_URL}/po/", headers=headers)

    if po_response.status_code == 200:
        data = po_response.json()

        if data and len(data) > 0:
            # Check first PO
            first_po = data[0]
            print(f"PO Number: {first_po.get('purchase_order_no')}")
            print(f"Status: {first_po.get('purchase_status')}")
            print(f"製單人 (output_person): {first_po.get('output_person')}")
            print(f"採購人 (confirm_purchaser): {first_po.get('confirm_purchaser')}")

            # Check if user details are present (not '-')
            if first_po.get('output_person') and first_po.get('output_person') != '-':
                print("✅ User fields are displaying correctly!")
            else:
                print("⚠️ User fields still showing '-' or missing")
        else:
            print("No purchase orders found in database")
    else:
        print(f"Error getting POs: {po_response.status_code}")

    # Test 2: Check batch receiving endpoint exists
    print("\n=== Test 2: Batch Receiving Endpoint ===")

    # First check if the endpoint exists (OPTIONS request)
    options_response = requests.options(f"{BASE_URL}/inventory/receiving/batch-confirm", headers=headers)

    if options_response.status_code == 200:
        print("✅ Batch receiving endpoint exists")

        # Try a test batch confirm with empty items to see if it handles gracefully
        test_data = {
            "items": [],
            "receiver": "Test User",
            "received_at": "2025-09-19T10:00:00Z",
            "notes": "Test batch receiving"
        }

        batch_response = requests.post(
            f"{BASE_URL}/inventory/receiving/batch-confirm",
            headers=headers,
            json=test_data
        )

        if batch_response.status_code == 200:
            print("✅ Batch receiving endpoint works (no 500 error)!")
            result = batch_response.json()
            print(f"Response: {result}")
        elif batch_response.status_code == 400:
            print("✅ Batch receiving endpoint validates input correctly")
            print(f"Response: {batch_response.json()}")
        else:
            print(f"⚠️ Unexpected status: {batch_response.status_code}")
            print(f"Response: {batch_response.text}")
    else:
        print(f"❌ Batch receiving endpoint not found: {options_response.status_code}")

else:
    print(f"Login failed: {login_response.status_code}")
    print(login_response.text)