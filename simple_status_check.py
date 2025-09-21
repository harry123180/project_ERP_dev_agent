#!/usr/bin/env python3
"""
Simple API test to check REQ20250909001 status
"""

import requests
import json

# Test configuration
BACKEND_URL = "http://localhost:5000"

def check_backend_status():
    """Check if backend is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return True
    except:
        return False

def test_with_procurement_user():
    """Test with procurement user credentials"""
    print("=== TESTING WITH PROCUREMENT USER ===")
    
    try:
        # Try with procurement manager credentials
        login_response = requests.post(f"{BACKEND_URL}/api/v1/auth/login", 
                                     json={
                                         "username": "procurement_mgr",
                                         "password": "123456"
                                     })
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            token = token_data.get('token')
            print(f"Login successful as procurement_mgr")
            
            # Get requisitions list
            headers = {"Authorization": f"Bearer {token}"}
            list_response = requests.get(f"{BACKEND_URL}/api/v1/requisitions", 
                                       headers=headers)
            
            if list_response.status_code == 200:
                requisitions_data = list_response.json()
                print(f"Retrieved {len(requisitions_data.get('items', []))} requisitions")
                
                # Look for REQ20250909001
                for req in requisitions_data.get('items', []):
                    if req['request_order_no'] == 'REQ20250909001':
                        print(f"✓ FOUND REQ20250909001")
                        print(f"  Status: {req['order_status']}")
                        print(f"  Requester: {req['requester_name']}")
                        print(f"  Summary: {req.get('summary', {})}")
                        return req['order_status'] == 'reviewed'
                
                print("REQ20250909001 not found in procurement user's view")
                return False
            else:
                print(f"Failed to get requisitions: {list_response.status_code}")
                return False
        else:
            print(f"Login failed: {login_response.status_code} - {login_response.text}")
            return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_direct_database_check():
    """Direct database check via simple API call"""
    print("\n=== DIRECT DATABASE CHECK ===")
    
    try:
        # Try a simple GET request to requisitions endpoint without auth first
        response = requests.get(f"{BACKEND_URL}/api/v1/requisitions/REQ20250909001")
        print(f"Direct GET response: {response.status_code}")
        
        if response.status_code == 401:
            print("Authentication required (expected)")
        elif response.status_code == 404:
            print("Requisition not found")
        else:
            print(f"Unexpected response: {response.text}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

def main():
    print("SIMPLE STATUS CHECK FOR REQ20250909001")
    print("=" * 40)
    
    # Check backend status
    if not check_backend_status():
        print("❌ Backend is not running or not accessible")
        return False
    
    print("✓ Backend is running")
    
    # Test with different users
    success = test_with_procurement_user()
    test_direct_database_check()
    
    print(f"\n=== RESULT ===")
    if success:
        print("✓ REQ20250909001 STATUS VERIFIED AS 'REVIEWED'")
        print("🎉 BUG FIX SUCCESSFUL!")
    else:
        print("❌ Could not verify status or still showing as 'submitted'")
    
    return success

if __name__ == '__main__':
    main()