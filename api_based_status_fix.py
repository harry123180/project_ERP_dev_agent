#!/usr/bin/env python3
"""
API-Based Status Update Fix
Fix the critical issue through API calls and identify the root cause
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

def analyze_requisition_problem(token, req_no):
    """Analyze a specific requisition's problem"""
    print(f"\n📋 ANALYZING {req_no}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/requisitions/{req_no}", 
                              headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            order_status = data.get('order_status')
            summary = data.get('summary', {})
            items = data.get('items', [])
            
            print(f"Order Status: {order_status}")
            print(f"Summary: {summary}")
            print(f"Items: {len(items)}")
            
            # Check each item
            for item in items:
                print(f"  Item {item.get('detail_id')}: {item.get('item_name')} - Status: {item.get('item_status')}")
            
            # Determine if there's a status mismatch
            total_items = summary.get('total_items', 0)
            pending_items = summary.get('pending_items', 0)
            approved_items = summary.get('approved_items', 0)
            rejected_items = summary.get('rejected_items', 0)
            
            print(f"Status Analysis:")
            print(f"  Total: {total_items}, Pending: {pending_items}")
            print(f"  Approved: {approved_items}, Rejected: {rejected_items}")
            
            # Check for problem
            if order_status == 'submitted' and pending_items == 0 and total_items > 0:
                print(f"🚨 STATUS MISMATCH DETECTED!")
                print(f"   All items reviewed but order status is still 'submitted'")
                print(f"   Should be: 'reviewed'")
                
                return {
                    'has_problem': True,
                    'current_status': order_status,
                    'expected_status': 'reviewed',
                    'data': data
                }
            else:
                print(f"✅ Status is correct")
                return {'has_problem': False, 'data': data}
        
        else:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Analysis error: {e}")
    
    return {'has_problem': False}

def find_all_problem_requisitions(token):
    """Find all requisitions with status update problems"""
    print(f"\n🔍 SCANNING ALL REQUISITIONS FOR PROBLEMS")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/requisitions", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            requisitions = data.get('items', [])
            
            print(f"Found {len(requisitions)} total requisitions")
            
            problem_reqs = []
            
            for req in requisitions:
                req_no = req.get('request_order_no')
                order_status = req.get('order_status')
                summary = req.get('summary', {})
                
                # Quick check for potential problems
                if (order_status == 'submitted' and 
                    summary.get('pending_items', 0) == 0 and 
                    summary.get('total_items', 0) > 0):
                    
                    print(f"🚨 Potential problem: {req_no}")
                    
                    # Do detailed analysis
                    analysis = analyze_requisition_problem(token, req_no)
                    if analysis.get('has_problem'):
                        problem_reqs.append({
                            'requisition_number': req_no,
                            'current_status': order_status,
                            'expected_status': 'reviewed',
                            'summary': summary
                        })
            
            return problem_reqs
            
    except Exception as e:
        print(f"❌ Scan error: {e}")
    
    return []

def attempt_api_fix(token, req_no):
    """Attempt to trigger status update through API"""
    print(f"\n🔧 ATTEMPTING API-BASED FIX FOR {req_no}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # First get the requisition details
    try:
        response = requests.get(f"{BASE_URL}/api/v1/requisitions/{req_no}", 
                              headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            
            if items:
                first_item = items[0]
                detail_id = first_item.get('detail_id')
                
                # Try to "re-approve" the item to trigger status update
                if first_item.get('item_status') == 'approved':
                    print(f"Trying to re-trigger status update by re-approving item {detail_id}")
                    
                    approve_data = {
                        'supplier_id': first_item.get('supplier_id'),
                        'unit_price': first_item.get('unit_price'),
                        'note': 'Status update fix - re-approval to trigger status update'
                    }
                    
                    approve_response = requests.post(
                        f"{BASE_URL}/api/v1/requisitions/{req_no}/lines/{detail_id}/approve",
                        json=approve_data,
                        headers=headers
                    )
                    
                    print(f"Re-approval response: {approve_response.status_code}")
                    if approve_response.status_code == 200:
                        print(f"✅ Re-approval successful")
                        
                        # Check if status was updated
                        check_response = requests.get(f"{BASE_URL}/api/v1/requisitions/{req_no}", 
                                                    headers=headers)
                        if check_response.status_code == 200:
                            updated_data = check_response.json()
                            new_status = updated_data.get('order_status')
                            print(f"✅ New status: {new_status}")
                            
                            if new_status == 'reviewed':
                                print(f"🎉 SUCCESS! Status updated to 'reviewed'")
                                return True
                            else:
                                print(f"❌ Status still incorrect: {new_status}")
                        
                    else:
                        print(f"❌ Re-approval failed: {approve_response.text}")
        
    except Exception as e:
        print(f"❌ Fix attempt error: {e}")
    
    return False

def main():
    print("🚨 API-BASED STATUS UPDATE FIX")
    print(f"Timestamp: {datetime.now()}")
    print("="*50)
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("❌ Cannot proceed without auth token")
        return
    
    print("✅ Authentication successful")
    
    # Step 1: Analyze the specific problem with REQ20250909002
    print("\n" + "="*50)
    print("STEP 1: ANALYZE REQ20250909002")
    analysis = analyze_requisition_problem(token, "REQ20250909002")
    
    # Step 2: Find all similar problems
    print("\n" + "="*50)
    print("STEP 2: FIND ALL PROBLEM REQUISITIONS")
    problem_reqs = find_all_problem_requisitions(token)
    
    print(f"\n🎯 FOUND {len(problem_reqs)} REQUISITIONS WITH STATUS PROBLEMS:")
    for req in problem_reqs:
        print(f"  - {req['requisition_number']}: '{req['current_status']}' → should be '{req['expected_status']}'")
    
    # Step 3: Attempt to fix each problem requisition
    print("\n" + "="*50)
    print("STEP 3: ATTEMPT TO FIX PROBLEM REQUISITIONS")
    
    fixed_count = 0
    for req in problem_reqs:
        req_no = req['requisition_number']
        success = attempt_api_fix(token, req_no)
        if success:
            fixed_count += 1
    
    # Final report
    print("\n" + "="*50)
    print("📊 FINAL REPORT")
    print(f"Total problems found: {len(problem_reqs)}")
    print(f"Successfully fixed: {fixed_count}")
    print(f"Still broken: {len(problem_reqs) - fixed_count}")
    
    # Save detailed report
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_problems_found": len(problem_reqs),
        "successfully_fixed": fixed_count,
        "still_broken": len(problem_reqs) - fixed_count,
        "problem_requisitions": problem_reqs,
        "fix_method": "API re-approval to trigger status update"
    }
    
    with open("api_status_fix_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"📄 Detailed report saved to: api_status_fix_report.json")
    
    if fixed_count == len(problem_reqs):
        print("🎉 ALL PROBLEMS FIXED SUCCESSFULLY!")
    elif fixed_count > 0:
        print(f"⚠️  PARTIAL SUCCESS: {fixed_count}/{len(problem_reqs)} fixed")
    else:
        print("❌ NO PROBLEMS WERE FIXED - Root cause needs deeper investigation")

if __name__ == "__main__":
    main()