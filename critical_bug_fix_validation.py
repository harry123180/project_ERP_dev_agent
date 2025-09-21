#!/usr/bin/env python3
"""
CRITICAL STATUS TRANSITION BUG FIX VALIDATION
==============================================

This script validates the fix for the critical status transition bug.
Tests the complete workflow to ensure:
1. Requisitions stay in 'submitted' status after submission  
2. Status correctly transitions to 'reviewed' after all items are approved
3. No unexpected status reversions occur

The fix removed db.session.commit() from RequestOrder.update_status_after_review() 
to prevent transaction conflicts with API endpoint transaction management.
"""

import json
import time
import requests
from datetime import datetime

BASE_URL = 'http://localhost:5000'
API_BASE = f'{BASE_URL}/api/v1'

class CriticalBugFixValidation:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.token = None
        
    def authenticate(self):
        """Authenticate as admin user"""
        try:
            response = self.session.post(f'{API_BASE}/auth/login', json={
                'username': 'admin',
                'password': 'admin123'
            })
            if response.status_code == 200:
                self.token = response.json()['access_token']
                self.session.headers.update({'Authorization': f'Bearer {self.token}'})
                return True
            return False
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False

    def log_result(self, step, status, details):
        """Log test result"""
        result = {
            'timestamp': datetime.now().isoformat(),
            'step': step,
            'status': status,
            'details': details
        }
        self.test_results.append(result)
        status_icon = "✓" if status == "SUCCESS" else "✗" if status == "FAILED" else "⚠" if status == "WARNING" else "ℹ"
        print(f"{status_icon} [{step}] {status}: {details}")

    def test_complete_approval_workflow(self):
        """Test complete approval workflow from creation to reviewed status"""
        try:
            # Step 1: Create requisition
            requisition_data = {
                'usage_type': 'daily',
                'items': [{
                    'item_name': 'Status Fix Validation Item',
                    'item_quantity': 2,
                    'item_unit': 'pcs',
                    'item_description': 'Testing critical status fix implementation'
                }]
            }
            
            response = self.session.post(f'{API_BASE}/requisitions', json=requisition_data)
            
            if response.status_code != 201:
                self.log_result('CREATE_REQUISITION', 'FAILED', f'HTTP {response.status_code}: {response.text}')
                return False
                
            req_no = response.json()['request_order_no']
            self.log_result('CREATE_REQUISITION', 'SUCCESS', f'Created {req_no}')
            
            # Step 2: Verify initial draft status
            response = self.session.get(f'{API_BASE}/requisitions/{req_no}')
            if response.status_code != 200:
                self.log_result('CHECK_INITIAL_STATUS', 'FAILED', f'Cannot retrieve requisition')
                return False
                
            initial_status = response.json()['order_status']
            if initial_status != 'draft':
                self.log_result('INITIAL_STATUS_CHECK', 'FAILED', f'Expected draft, got {initial_status}')
                return False
                
            self.log_result('INITIAL_STATUS_CHECK', 'SUCCESS', f'Initial status correctly set to draft')
            
            # Step 3: Submit requisition
            response = self.session.post(f'{API_BASE}/requisitions/{req_no}/submit')
            if response.status_code != 200:
                self.log_result('SUBMIT_REQUISITION', 'FAILED', f'HTTP {response.status_code}: {response.text}')
                return False
                
            submitted_status = response.json()['order_status']
            if submitted_status != 'submitted':
                self.log_result('SUBMIT_STATUS_CHECK', 'FAILED', f'Expected submitted, got {submitted_status}')
                return False
                
            self.log_result('SUBMIT_STATUS_CHECK', 'SUCCESS', f'Status correctly set to submitted')
            
            # Step 4: Wait and verify status doesn't revert
            time.sleep(2)
            response = self.session.get(f'{API_BASE}/requisitions/{req_no}')
            if response.status_code != 200:
                self.log_result('STATUS_STABILITY_CHECK', 'FAILED', f'Cannot retrieve requisition')
                return False
                
            stable_status = response.json()['order_status']
            if stable_status != 'submitted':
                self.log_result('STATUS_STABILITY_CHECK', 'FAILED', f'Status reverted to {stable_status}')
                return False
                
            self.log_result('STATUS_STABILITY_CHECK', 'SUCCESS', f'Status remains stable at submitted')
            
            # Step 5: Get item details for approval
            items = response.json()['items']
            if not items:
                self.log_result('GET_ITEMS', 'FAILED', f'No items found')
                return False
                
            detail_id = items[0]['detail_id']
            self.log_result('GET_ITEMS', 'SUCCESS', f'Found item {detail_id}')
            
            # Step 6: Approve the item
            approval_data = {
                'supplier_id': 'T001',
                'unit_price': 150.00,
                'note': 'Approved after critical fix validation'
            }
            
            response = self.session.post(
                f'{API_BASE}/requisitions/{req_no}/lines/{detail_id}/approve',
                json=approval_data
            )
            
            if response.status_code != 200:
                self.log_result('APPROVE_ITEM', 'FAILED', f'HTTP {response.status_code}: {response.text}')
                return False
                
            self.log_result('APPROVE_ITEM', 'SUCCESS', f'Item {detail_id} approved successfully')
            
            # Step 7: Verify status transition to reviewed
            time.sleep(1)  # Allow for status processing
            response = self.session.get(f'{API_BASE}/requisitions/{req_no}')
            if response.status_code != 200:
                self.log_result('FINAL_STATUS_CHECK', 'FAILED', f'Cannot retrieve final status')
                return False
                
            final_status = response.json()['order_status']
            summary = response.json()['summary']
            
            self.log_result('FINAL_STATUS_DETAILS', 'INFO', f'Status: {final_status}, Summary: {summary}')
            
            # Critical validation: Status should be 'reviewed' when all items are approved
            if summary['pending_items'] == 0 and summary['approved_items'] > 0:
                if final_status == 'reviewed':
                    self.log_result('CRITICAL_FIX_VALIDATION', 'SUCCESS', f'✓ STATUS BUG FIXED! Correctly transitioned to reviewed')
                    return True
                else:
                    self.log_result('CRITICAL_FIX_VALIDATION', 'FAILED', f'✗ BUG STILL EXISTS! Expected reviewed, got {final_status}')
                    return False
            else:
                self.log_result('INCOMPLETE_APPROVAL', 'WARNING', f'Not all items approved yet')
                return False
                
        except Exception as e:
            self.log_result('WORKFLOW_TEST', 'ERROR', str(e))
            return False

    def test_multiple_items_workflow(self):
        """Test workflow with multiple items to ensure status updates correctly"""
        try:
            # Create requisition with multiple items
            requisition_data = {
                'usage_type': 'project',
                'items': [
                    {
                        'item_name': 'Multi-Item Test Part A',
                        'item_quantity': 3,
                        'item_unit': 'pcs',
                        'item_description': 'First item in multi-item test'
                    },
                    {
                        'item_name': 'Multi-Item Test Part B', 
                        'item_quantity': 1,
                        'item_unit': 'set',
                        'item_description': 'Second item in multi-item test'
                    }
                ]
            }
            
            response = self.session.post(f'{API_BASE}/requisitions', json=requisition_data)
            if response.status_code != 201:
                self.log_result('CREATE_MULTI_ITEM_REQ', 'FAILED', f'HTTP {response.status_code}')
                return False
                
            req_no = response.json()['request_order_no']
            self.log_result('CREATE_MULTI_ITEM_REQ', 'SUCCESS', f'Created multi-item requisition {req_no}')
            
            # Submit requisition
            response = self.session.post(f'{API_BASE}/requisitions/{req_no}/submit')
            if response.status_code != 200:
                self.log_result('SUBMIT_MULTI_ITEM', 'FAILED', f'Submit failed')
                return False
                
            self.log_result('SUBMIT_MULTI_ITEM', 'SUCCESS', f'Multi-item requisition submitted')
            
            # Get items
            response = self.session.get(f'{API_BASE}/requisitions/{req_no}')
            items = response.json()['items']
            
            if len(items) != 2:
                self.log_result('VERIFY_ITEM_COUNT', 'FAILED', f'Expected 2 items, got {len(items)}')
                return False
                
            self.log_result('VERIFY_ITEM_COUNT', 'SUCCESS', f'Confirmed 2 items in requisition')
            
            # Approve first item only
            approval_data = {'supplier_id': 'T001', 'unit_price': 75.00, 'note': 'Partial approval test'}
            response = self.session.post(
                f'{API_BASE}/requisitions/{req_no}/lines/{items[0]["detail_id"]}/approve',
                json=approval_data
            )
            
            if response.status_code != 200:
                self.log_result('APPROVE_FIRST_ITEM', 'FAILED', f'HTTP {response.status_code}')
                return False
                
            self.log_result('APPROVE_FIRST_ITEM', 'SUCCESS', f'First item approved')
            
            # Check status - should still be submitted
            time.sleep(1)
            response = self.session.get(f'{API_BASE}/requisitions/{req_no}')
            status_after_partial = response.json()['order_status']
            summary_partial = response.json()['summary']
            
            if status_after_partial != 'submitted':
                self.log_result('PARTIAL_APPROVAL_STATUS', 'FAILED', f'Expected submitted, got {status_after_partial}')
                return False
                
            self.log_result('PARTIAL_APPROVAL_STATUS', 'SUCCESS', f'Status correctly remains submitted after partial approval')
            
            # Approve second item 
            response = self.session.post(
                f'{API_BASE}/requisitions/{req_no}/lines/{items[1]["detail_id"]}/approve',
                json=approval_data
            )
            
            if response.status_code != 200:
                self.log_result('APPROVE_SECOND_ITEM', 'FAILED', f'HTTP {response.status_code}')
                return False
                
            self.log_result('APPROVE_SECOND_ITEM', 'SUCCESS', f'Second item approved')
            
            # Check final status - should now be reviewed
            time.sleep(1)
            response = self.session.get(f'{API_BASE}/requisitions/{req_no}')
            final_status = response.json()['order_status']
            final_summary = response.json()['summary']
            
            if final_summary['pending_items'] == 0 and final_status == 'reviewed':
                self.log_result('MULTI_ITEM_FINAL_STATUS', 'SUCCESS', f'✓ Multi-item workflow correct: {final_status}')
                return True
            else:
                self.log_result('MULTI_ITEM_FINAL_STATUS', 'FAILED', f'Expected reviewed, got {final_status}, summary: {final_summary}')
                return False
                
        except Exception as e:
            self.log_result('MULTI_ITEM_TEST', 'ERROR', str(e))
            return False

    def run_validation(self):
        """Run complete validation of critical bug fix"""
        print("=" * 70)
        print("🔧 CRITICAL STATUS TRANSITION BUG FIX VALIDATION")
        print("=" * 70)
        print("Testing fix: Removed db.session.commit() from update_status_after_review()")
        print("-" * 70)
        
        if not self.authenticate():
            print("❌ Cannot authenticate - aborting validation")
            return
        
        # Test 1: Single item workflow
        print("\n📋 TEST 1: Single Item Approval Workflow")
        print("-" * 40)
        success1 = self.test_complete_approval_workflow()
        
        # Test 2: Multiple items workflow  
        print("\n📋 TEST 2: Multiple Items Approval Workflow")
        print("-" * 40)
        success2 = self.test_multiple_items_workflow()
        
        # Generate final report
        report_file = f'critical_bug_fix_validation_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'validation_time': datetime.now().isoformat(),
                'fix_description': 'Removed db.session.commit() from RequestOrder.update_status_after_review()',
                'test_results': self.test_results,
                'validation_summary': self.generate_validation_summary(success1, success2),
                'overall_result': 'PASSED' if (success1 and success2) else 'FAILED'
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Validation report saved: {report_file}")
        print(self.generate_validation_summary(success1, success2))

    def generate_validation_summary(self, test1_result, test2_result):
        """Generate validation summary"""
        overall_success = test1_result and test2_result
        
        summary = f"""
{"=" * 70}
🎯 CRITICAL BUG FIX VALIDATION SUMMARY
{"=" * 70}

🔧 FIX IMPLEMENTED: 
   Removed db.session.commit() from RequestOrder.update_status_after_review()
   to prevent transaction conflicts with API endpoint transaction management.

📊 TEST RESULTS:
   ✓ Single Item Workflow:     {"PASSED" if test1_result else "FAILED"}
   ✓ Multiple Items Workflow:  {"PASSED" if test2_result else "FAILED"}

🎯 OVERALL RESULT: {"🟢 VALIDATION PASSED" if overall_success else "🔴 VALIDATION FAILED"}

"""
        
        if overall_success:
            summary += """✅ CRITICAL STATUS TRANSITION BUG IS FIXED!
   - Requisitions correctly transition from 'submitted' to 'reviewed'  
   - No unwanted status reversions occur
   - Multi-item approval workflows work correctly
   - Transaction management is now handled properly by API endpoints

🚀 The ERP system status transitions are now working as expected."""
        else:
            summary += """❌ CRITICAL BUG STILL EXISTS!
   - Status transitions are not working correctly
   - Further investigation and fixes required"""
        
        return summary

if __name__ == '__main__':
    validator = CriticalBugFixValidation()
    validator.run_validation()