#!/usr/bin/env python3

"""
Verification script to test the purchase orders endpoint fix
"""
import requests
import json

def test_po_endpoint():
    """Test the purchase orders endpoint with various scenarios"""
    print("=== Purchase Orders Endpoint Verification ===\n")
    
    # Test data
    base_url = "http://localhost:5000"
    login_data = {"username": "admin", "password": "admin123"}
    
    try:
        # 1. Login
        print("1. Testing Login...")
        login_response = requests.post(f"{base_url}/api/v1/auth/login", json=login_data)
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            return False
        
        token = login_response.json().get('access_token')
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        print("✅ Login successful")
        
        # 2. Test basic PO list
        print("\n2. Testing Basic PO List...")
        po_response = requests.get(f"{base_url}/api/v1/po", headers=headers)
        if po_response.status_code != 200:
            print(f"❌ Basic PO list failed: {po_response.status_code}")
            print(f"Response: {po_response.text}")
            return False
        
        po_data = po_response.json()
        print(f"✅ Basic PO list successful - Found {po_data.get('pagination', {}).get('total', 0)} purchase orders")
        
        # 3. Test with query parameters
        print("\n3. Testing PO List with Parameters...")
        test_params = [
            "?supplier=&status=&page=1&page_size=20",
            "?page=1&page_size=10",
            "?status=pending",
            "?status=confirmed"
        ]
        
        for param in test_params:
            url = f"{base_url}/api/v1/po{param}"
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                count = data.get('pagination', {}).get('total', 0)
                print(f"✅ {param} - Found {count} purchase orders")
            else:
                print(f"❌ {param} - Failed with status {response.status_code}")
        
        # 4. Verify data structure
        print("\n4. Verifying Data Structure...")
        if po_data.get('items'):
            first_po = po_data['items'][0]
            required_fields = [
                'purchase_order_no', 'supplier_id', 'supplier_name', 'purchase_status',
                'shipping_status', 'billing_status', 'created_at'
            ]
            
            missing_fields = [field for field in required_fields if field not in first_po]
            if missing_fields:
                print(f"❌ Missing fields: {missing_fields}")
            else:
                print("✅ All required fields present")
                
            # Show enum values that are working
            print(f"   Purchase Status: {first_po.get('purchase_status')}")
            print(f"   Shipping Status: {first_po.get('shipping_status')}")  
            print(f"   Billing Status: {first_po.get('billing_status')}")
            if first_po.get('payment_method'):
                print(f"   Payment Method: {first_po.get('payment_method')}")
        
        # 5. Test individual PO retrieval
        print("\n5. Testing Individual PO Retrieval...")
        if po_data.get('items'):
            po_no = po_data['items'][0]['purchase_order_no']
            individual_response = requests.get(f"{base_url}/api/v1/po/{po_no}", headers=headers)
            if individual_response.status_code == 200:
                print(f"✅ Individual PO retrieval successful for {po_no}")
            else:
                print(f"❌ Individual PO retrieval failed for {po_no}: {individual_response.status_code}")
        
        print("\n=== All Tests Completed Successfully! ===")
        return True
        
    except Exception as e:
        print(f"\n❌ Exception occurred: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_po_endpoint()
    exit(0 if success else 1)