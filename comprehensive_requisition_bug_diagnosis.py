#!/usr/bin/env python3
"""
Comprehensive Requisition Status Bug Diagnosis
Investigates REQ20250909002 and related status update issues
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

def get_auth_token():
    """Get authentication token"""
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", 
                               json={"username": "admin", "password": "admin123"})
        if response.status_code == 200:
            return response.json().get('access_token')
        else:
            print(f"Auth failed with status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Auth error: {e}")
    return None

def investigate_requisition(token, req_number):
    """Investigate specific requisition"""
    print(f"\n=== INVESTIGATING {req_number} ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get requisition details
    try:
        response = requests.get(f"{BASE_URL}/api/v1/requisitions/{req_number}", 
                              headers=headers)
        if response.status_code == 200:
            req_data = response.json()
            print(f"Requisition Status: {req_data.get('status')}")
            print(f"Total Items: {len(req_data.get('items', []))}")
            
            # Count approved/rejected items
            approved_count = 0
            rejected_count = 0
            pending_count = 0
            
            for item in req_data.get('items', []):
                item_status = item.get('status', 'pending')
                print(f"  Item {item.get('id')}: {item.get('description')} - Status: {item_status}")
                
                if item_status == 'approved':
                    approved_count += 1
                elif item_status == 'rejected':
                    rejected_count += 1
                else:
                    pending_count += 1
            
            print(f"ACTUAL COUNTS - Approved: {approved_count}, Rejected: {rejected_count}, Pending: {pending_count}")
            
            # Get statistics endpoint
            stats_response = requests.get(f"{BASE_URL}/api/v1/requisitions/{req_number}/stats", 
                                        headers=headers)
            if stats_response.status_code == 200:
                stats = stats_response.json()
                print(f"API STATS - Total: {stats.get('total_items')}, Approved: {stats.get('approved_items')}, Rejected: {stats.get('rejected_items')}")
            
            return req_data, approved_count, rejected_count, pending_count
        else:
            print(f"Failed to get requisition: {response.status_code}")
    except Exception as e:
        print(f"Error investigating requisition: {e}")
    
    return None, 0, 0, 0

def check_all_requisitions(token):
    """Check all requisitions for similar issues"""
    print("\n=== CHECKING ALL REQUISITIONS ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/requisitions", headers=headers)
        if response.status_code == 200:
            requisitions = response.json()
            
            problem_reqs = []
            
            for req in requisitions:
                req_number = req.get('requisition_number')
                status = req.get('status')
                
                # Get detailed info
                _, approved, rejected, pending = investigate_requisition(token, req_number)
                
                # Check for status mismatch
                if approved > 0 and rejected == 0 and pending == 0 and status != 'approved':
                    problem_reqs.append({
                        'requisition_number': req_number,
                        'current_status': status,
                        'expected_status': 'approved',
                        'approved_items': approved,
                        'total_items': approved + rejected + pending
                    })
                    print(f"🚨 PROBLEM FOUND: {req_number} should be 'approved' but is '{status}'")
                
                elif approved > 0 and rejected > 0 and pending == 0 and status != 'reviewed':
                    problem_reqs.append({
                        'requisition_number': req_number,
                        'current_status': status,
                        'expected_status': 'reviewed',
                        'approved_items': approved,
                        'rejected_items': rejected,
                        'total_items': approved + rejected + pending
                    })
                    print(f"🚨 PROBLEM FOUND: {req_number} should be 'reviewed' but is '{status}'")
                
                elif (approved + rejected) == (approved + rejected + pending) and (approved + rejected) > 0 and status == 'submitted':
                    problem_reqs.append({
                        'requisition_number': req_number,
                        'current_status': status,
                        'expected_status': 'reviewed',
                        'approved_items': approved,
                        'rejected_items': rejected,
                        'total_items': approved + rejected + pending
                    })
                    print(f"🚨 PROBLEM FOUND: {req_number} has completed reviews but status is still 'submitted'")
            
            return problem_reqs
            
    except Exception as e:
        print(f"Error checking requisitions: {e}")
    
    return []

def test_status_update_api(token, req_number, item_id, new_status):
    """Test the status update API directly"""
    print(f"\n=== TESTING STATUS UPDATE API ===")
    print(f"Updating item {item_id} in {req_number} to {new_status}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Try the review endpoint
        response = requests.post(f"{BASE_URL}/api/v1/requisitions/{req_number}/items/{item_id}/review",
                               json={"status": new_status, "comment": "Test update"},
                               headers=headers)
        
        print(f"Review API Response: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
            
            # Check if requisition status was updated
            req_response = requests.get(f"{BASE_URL}/api/v1/requisitions/{req_number}", 
                                      headers=headers)
            if req_response.status_code == 200:
                updated_req = req_response.json()
                print(f"Updated Requisition Status: {updated_req.get('status')}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error testing status update: {e}")

def main():
    print("🔍 COMPREHENSIVE REQUISITION BUG DIAGNOSIS")
    print(f"Timestamp: {datetime.now()}")
    
    # Get auth token
    token = get_auth_token()
    if not token:
        print("❌ Failed to get auth token")
        return
    
    print("✅ Authentication successful")
    
    # Specifically investigate REQ20250909002
    investigate_requisition(token, "REQ20250909002")
    
    # Check all requisitions for problems
    problem_reqs = check_all_requisitions(token)
    
    # Summary report
    print(f"\n🎯 DIAGNOSIS SUMMARY:")
    print(f"Found {len(problem_reqs)} requisitions with status update issues")
    
    for prob in problem_reqs:
        print(f"  - {prob['requisition_number']}: '{prob['current_status']}' should be '{prob['expected_status']}'")
    
    # Save diagnostic report
    report = {
        "timestamp": datetime.now().isoformat(),
        "problem_requisitions": problem_reqs,
        "diagnostic_complete": True
    }
    
    with open('requisition_bug_diagnosis_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Report saved to: requisition_bug_diagnosis_report.json")

if __name__ == "__main__":
    main()