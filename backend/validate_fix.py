#!/usr/bin/env python3

import requests
import json

def test_api_endpoints():
    """Test API endpoints to verify data is accessible"""
    base_url = "http://localhost:5000/api/v1"
    
    print("=== API Endpoint Validation ===")
    
    # Test health endpoint
    try:
        response = requests.get("http://localhost:5000/health")
        if response.status_code == 200:
            print("✓ Health endpoint working")
        else:
            print(f"✗ Health endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Health endpoint error: {e}")
        return False
    
    # Test authentication
    try:
        auth_data = {
            "username": "admin",
            "password": "admin123"
        }
        response = requests.post(f"{base_url}/auth/login", json=auth_data)
        if response.status_code == 200:
            token = response.json().get('access_token')
            print("✓ Authentication successful")
            headers = {"Authorization": f"Bearer {token}"}
        else:
            print(f"✗ Authentication failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Authentication error: {e}")
        return False
    
    # Test suppliers endpoint (should have data)
    try:
        response = requests.get(f"{base_url}/suppliers", headers=headers)
        if response.status_code == 200:
            data = response.json()
            supplier_count = len(data.get('items', []))
            print(f"✓ Suppliers endpoint: {supplier_count} suppliers found")
        else:
            print(f"✗ Suppliers endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Suppliers endpoint error: {e}")
    
    # Test requisitions endpoint (should now have data)
    try:
        response = requests.get(f"{base_url}/requisitions", headers=headers)
        if response.status_code == 200:
            data = response.json()
            req_count = len(data.get('items', []))
            print(f"✓ Requisitions endpoint: {req_count} requisitions found")
        else:
            print(f"✗ Requisitions endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Requisitions endpoint error: {e}")
    
    # Test purchase orders endpoint (should now have data)
    try:
        response = requests.get(f"{base_url}/po", headers=headers)
        if response.status_code == 200:
            data = response.json()
            po_count = len(data.get('items', []))
            print(f"✓ Purchase Orders endpoint: {po_count} purchase orders found")
        else:
            print(f"✗ Purchase Orders endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Purchase Orders endpoint error: {e}")
    
    print("\n🎉 API validation completed!")
    return True

if __name__ == "__main__":
    test_api_endpoints()