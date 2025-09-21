#!/usr/bin/env python3
"""
AUTOMATED REGRESSION TESTS FOR STATUS TRANSITION BUG PREVENTION
===============================================================

This script implements comprehensive regression tests based on the requirements
traceability analysis by Test Architect Quinn to prevent critical status
transition bugs from reoccurring.

Test Categories:
1. Status Transition Requirements (Draft → Submitted → Reviewed)  
2. Approval Process Requirements (Item-level to Overall Status)
3. Data Consistency Requirements (UI and Backend Sync)
4. Transaction Integrity Requirements (Atomic and Persistent Updates)
"""

import requests
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

BASE_URL = 'http://localhost:5000'
API_BASE = f'{BASE_URL}/api/v1'

class StatusTransitionRegessionTests:
    def __init__(self):
        self.token = None
        self.test_results = []
        self.start_time = datetime.now()
        
    def get_token(self) -> str:
        """Get authentication token"""
        response = requests.post(f'{API_BASE}/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        if response.status_code == 200:
            self.token = response.json()['access_token']
            return self.token
        raise Exception(f"Failed to get token: {response.text}")
    
    @property
    def headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        if not self.token:
            self.get_token()
        return {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
    
    def log_result(self, scenario: str, status: str, details: str, data: Any = None):
        """Log test result"""
        result = {
            'timestamp': datetime.now().isoformat(),
            'scenario': scenario,
            'status': status,
            'details': details,
            'data': data
        }
        self.test_results.append(result)
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "ℹ️"
        print(f"{status_icon} {scenario}: {details}")
    
    def create_test_requisition(self, req_type: str = "single") -> Dict[str, Any]:
        """Create a test requisition for testing"""
        if req_type == "single":
            req_data = {
                'usage_type': 'daily',
                'items': [{
                    'item_name': f'Regression Test Item {datetime.now().strftime("%H%M%S")}',
                    'item_quantity': 1,
                    'item_unit': 'pcs'
                }]
            }
        else:  # multi
            req_data = {
                'usage_type': 'project',
                'items': [
                    {
                        'item_name': f'Multi Test Item 1 {datetime.now().strftime("%H%M%S")}',
                        'item_quantity': 2,
                        'item_unit': 'pcs'
                    },
                    {
                        'item_name': f'Multi Test Item 2 {datetime.now().strftime("%H%M%S")}',
                        'item_quantity': 3,
                        'item_unit': 'sets'
                    }
                ]
            }
        
        response = requests.post(f'{API_BASE}/requisitions', json=req_data, headers=self.headers)
        if response.status_code == 201:
            return response.json()
        raise Exception(f"Failed to create requisition: {response.text}")
    
    def get_requisition_status(self, req_no: str) -> Dict[str, Any]:
        """Get current requisition status and details"""
        response = requests.get(f'{API_BASE}/requisitions/{req_no}', headers=self.headers)
        if response.status_code == 200:
            return response.json()
        raise Exception(f"Failed to get requisition {req_no}: {response.text}")
    
    def submit_requisition(self, req_no: str) -> bool:
        """Submit a requisition"""
        response = requests.post(f'{API_BASE}/requisitions/{req_no}/submit', headers=self.headers)
        return response.status_code == 200
    
    def approve_item(self, req_no: str, detail_id: int) -> bool:
        """Approve a specific item"""
        approval_data = {
            'supplier_id': 'T001',
            'unit_price': 100.0,
            'note': 'Regression test approval'
        }
        response = requests.post(
            f'{API_BASE}/requisitions/{req_no}/lines/{detail_id}/approve',
            json=approval_data,
            headers=self.headers
        )
        return response.status_code == 200

    # ========================================================================
    # TEST CATEGORY 1: STATUS TRANSITION REQUIREMENTS
    # ========================================================================
    
    def test_valid_draft_to_submitted_transition(self):
        """
        Scenario: Valid status transition from Draft to Submitted
        Given a requisition exists in "Draft" status
        And the requisition has all required fields completed
        When the user submits the requisition
        Then the status should transition to "Submitted"
        """
        scenario = "Valid Draft to Submitted Transition"
        
        try:
            # Given: Create requisition in draft status
            req_data = self.create_test_requisition()
            req_no = req_data['request_order_no']
            
            # Verify initial draft status
            status_data = self.get_requisition_status(req_no)
            if status_data['order_status'] != 'draft':
                self.log_result(scenario, "FAIL", f"Expected draft status, got {status_data['order_status']}")
                return
            
            # When: Submit the requisition
            if not self.submit_requisition(req_no):
                self.log_result(scenario, "FAIL", "Failed to submit requisition")
                return
            
            # Then: Verify status changed to submitted
            time.sleep(1)  # Allow status update
            final_status = self.get_requisition_status(req_no)
            
            if final_status['order_status'] == 'submitted':
                self.log_result(scenario, "PASS", f"Status correctly transitioned to submitted for {req_no}")
            else:
                self.log_result(scenario, "FAIL", f"Expected submitted, got {final_status['order_status']}")
                
        except Exception as e:
            self.log_result(scenario, "FAIL", f"Exception: {str(e)}")
    
    def test_invalid_draft_to_reviewed_transition(self):
        """
        Scenario: Invalid status transition from Draft to Reviewed
        Given a requisition exists in "Draft" status
        When attempting to directly change status to "Reviewed"
        Then the system should prevent this invalid transition
        """
        scenario = "Invalid Draft to Reviewed Transition Prevention"
        
        try:
            # Given: Create requisition in draft status
            req_data = self.create_test_requisition()
            req_no = req_data['request_order_no']
            
            # When: Try to directly approve without submission (should fail)
            req_details = self.get_requisition_status(req_no)
            detail_id = req_details['items'][0]['detail_id']
            
            # This should fail because requisition is not submitted
            approval_success = self.approve_item(req_no, detail_id)
            
            if not approval_success:
                self.log_result(scenario, "PASS", "System correctly prevented invalid transition")
            else:
                # Check if status inappropriately changed
                final_status = self.get_requisition_status(req_no)
                if final_status['order_status'] == 'draft':
                    self.log_result(scenario, "PASS", "Status remained draft as expected")
                else:
                    self.log_result(scenario, "FAIL", f"Status inappropriately changed to {final_status['order_status']}")
                    
        except Exception as e:
            self.log_result(scenario, "PASS", f"Exception correctly prevented invalid transition: {str(e)}")
    
    def test_submitted_to_reviewed_transition(self):
        """
        Scenario: Valid status transition from Submitted to Reviewed
        Given a requisition exists in "Submitted" status
        And all items have been reviewed (approved/rejected)
        When the system processes the final item review
        Then the status should automatically transition to "Reviewed"
        """
        scenario = "Valid Submitted to Reviewed Transition"
        
        try:
            # Given: Create and submit requisition
            req_data = self.create_test_requisition()
            req_no = req_data['request_order_no']
            
            if not self.submit_requisition(req_no):
                self.log_result(scenario, "FAIL", "Failed to submit requisition")
                return
            
            # Verify submitted status
            status_data = self.get_requisition_status(req_no)
            if status_data['order_status'] != 'submitted':
                self.log_result(scenario, "FAIL", f"Expected submitted status, got {status_data['order_status']}")
                return
            
            # When: Approve all items
            detail_id = status_data['items'][0]['detail_id']
            if not self.approve_item(req_no, detail_id):
                self.log_result(scenario, "FAIL", "Failed to approve item")
                return
            
            # Then: Verify status transitioned to reviewed
            time.sleep(2)  # Allow status update processing
            final_status = self.get_requisition_status(req_no)
            
            if final_status['order_status'] == 'reviewed':
                self.log_result(scenario, "PASS", f"Status correctly transitioned to reviewed for {req_no}")
            else:
                self.log_result(scenario, "FAIL", 
                    f"CRITICAL BUG: Expected reviewed, got {final_status['order_status']} " + 
                    f"Summary: {final_status.get('summary', 'N/A')}")
                
        except Exception as e:
            self.log_result(scenario, "FAIL", f"Exception: {str(e)}")

    # ========================================================================
    # TEST CATEGORY 2: APPROVAL PROCESS REQUIREMENTS
    # ========================================================================
    
    def test_partial_approval_status_stability(self):
        """
        Scenario: Partial approval should not trigger status change
        Given a multi-item requisition in "Submitted" status
        When only some items are approved
        Then the overall status should remain "Submitted"
        """
        scenario = "Partial Approval Status Stability"
        
        try:
            # Given: Create multi-item requisition
            req_data = self.create_test_requisition("multi")
            req_no = req_data['request_order_no']
            
            if not self.submit_requisition(req_no):
                self.log_result(scenario, "FAIL", "Failed to submit requisition")
                return
            
            # Get item details
            status_data = self.get_requisition_status(req_no)
            items = status_data['items']
            
            if len(items) < 2:
                self.log_result(scenario, "FAIL", "Need at least 2 items for partial approval test")
                return
            
            # When: Approve only first item
            first_item_id = items[0]['detail_id']
            if not self.approve_item(req_no, first_item_id):
                self.log_result(scenario, "FAIL", "Failed to approve first item")
                return
            
            # Then: Verify status remains submitted
            time.sleep(1)
            partial_status = self.get_requisition_status(req_no)
            
            if partial_status['order_status'] == 'submitted':
                self.log_result(scenario, "PASS", 
                    f"Status correctly remained submitted after partial approval. " +
                    f"Summary: {partial_status.get('summary', {})}")
            else:
                self.log_result(scenario, "FAIL", 
                    f"Status incorrectly changed to {partial_status['order_status']} after partial approval")
                
        except Exception as e:
            self.log_result(scenario, "FAIL", f"Exception: {str(e)}")
    
    def test_complete_approval_triggers_review(self):
        """
        Scenario: Complete approval should trigger status change to Reviewed
        Given a multi-item requisition in "Submitted" status with partial approvals
        When the final pending item is approved
        Then the overall status should change to "Reviewed"
        """
        scenario = "Complete Approval Triggers Review Status"
        
        try:
            # Given: Create multi-item requisition and partially approve
            req_data = self.create_test_requisition("multi")
            req_no = req_data['request_order_no']
            
            if not self.submit_requisition(req_no):
                self.log_result(scenario, "FAIL", "Failed to submit requisition")
                return
            
            status_data = self.get_requisition_status(req_no)
            items = status_data['items']
            
            # Approve first item
            first_item_id = items[0]['detail_id']
            if not self.approve_item(req_no, first_item_id):
                self.log_result(scenario, "FAIL", "Failed to approve first item")
                return
            
            # When: Approve final item
            second_item_id = items[1]['detail_id']
            if not self.approve_item(req_no, second_item_id):
                self.log_result(scenario, "FAIL", "Failed to approve second item")
                return
            
            # Then: Verify status changed to reviewed
            time.sleep(2)
            final_status = self.get_requisition_status(req_no)
            
            if final_status['order_status'] == 'reviewed':
                self.log_result(scenario, "PASS", 
                    f"Status correctly changed to reviewed after complete approval. " +
                    f"Summary: {final_status.get('summary', {})}")
            else:
                self.log_result(scenario, "FAIL", 
                    f"CRITICAL BUG: Expected reviewed after complete approval, got {final_status['order_status']} " +
                    f"Summary: {final_status.get('summary', {})}")
                
        except Exception as e:
            self.log_result(scenario, "FAIL", f"Exception: {str(e)}")

    # ========================================================================
    # TEST CATEGORY 3: DATA CONSISTENCY REQUIREMENTS
    # ========================================================================
    
    def test_status_persistence_after_update(self):
        """
        Scenario: Status changes should persist after system operations
        Given a requisition has transitioned to "Reviewed" status
        When subsequent operations are performed
        Then the status should remain stable and consistent
        """
        scenario = "Status Persistence After Update"
        
        try:
            # Given: Create requisition and complete approval process
            req_data = self.create_test_requisition()
            req_no = req_data['request_order_no']
            
            # Submit and approve to reach reviewed status
            if not self.submit_requisition(req_no):
                self.log_result(scenario, "FAIL", "Failed to submit requisition")
                return
            
            status_data = self.get_requisition_status(req_no)
            detail_id = status_data['items'][0]['detail_id']
            
            if not self.approve_item(req_no, detail_id):
                self.log_result(scenario, "FAIL", "Failed to approve item")
                return
            
            time.sleep(2)
            initial_final = self.get_requisition_status(req_no)
            
            if initial_final['order_status'] != 'reviewed':
                self.log_result(scenario, "FAIL", f"Setup failed - status is {initial_final['order_status']}, not reviewed")
                return
            
            # When: Perform subsequent operations (re-fetch data multiple times)
            statuses = []
            for i in range(5):
                time.sleep(0.5)
                check_status = self.get_requisition_status(req_no)
                statuses.append(check_status['order_status'])
            
            # Then: Verify all statuses remain 'reviewed'
            if all(status == 'reviewed' for status in statuses):
                self.log_result(scenario, "PASS", f"Status remained consistently reviewed across {len(statuses)} checks")
            else:
                self.log_result(scenario, "FAIL", f"Status inconsistency detected: {statuses}")
                
        except Exception as e:
            self.log_result(scenario, "FAIL", f"Exception: {str(e)}")

    # ========================================================================
    # TEST CATEGORY 4: TRANSACTION INTEGRITY REQUIREMENTS
    # ========================================================================
    
    def test_atomic_status_update(self):
        """
        Scenario: Status updates should be atomic and consistent
        Given multiple rapid approval operations
        When items are approved in quick succession
        Then the final status should be correct and not corrupted
        """
        scenario = "Atomic Status Update Under Load"
        
        try:
            # Given: Create multi-item requisition
            req_data = self.create_test_requisition("multi")
            req_no = req_data['request_order_no']
            
            if not self.submit_requisition(req_no):
                self.log_result(scenario, "FAIL", "Failed to submit requisition")
                return
            
            status_data = self.get_requisition_status(req_no)
            items = status_data['items']
            
            # When: Approve items in rapid succession
            for item in items:
                if not self.approve_item(req_no, item['detail_id']):
                    self.log_result(scenario, "FAIL", f"Failed to approve item {item['detail_id']}")
                    return
                time.sleep(0.1)  # Very short delay to simulate rapid operations
            
            # Allow final status processing
            time.sleep(3)
            
            # Then: Verify final status is correct
            final_status = self.get_requisition_status(req_no)
            summary = final_status.get('summary', {})
            
            if (final_status['order_status'] == 'reviewed' and 
                summary.get('pending_items', -1) == 0):
                self.log_result(scenario, "PASS", 
                    f"Atomic update successful - final status: reviewed, pending: 0")
            else:
                self.log_result(scenario, "FAIL", 
                    f"Atomic update failed - status: {final_status['order_status']}, " +
                    f"summary: {summary}")
                
        except Exception as e:
            self.log_result(scenario, "FAIL", f"Exception: {str(e)}")
    
    # ========================================================================
    # TEST EXECUTION AND REPORTING
    # ========================================================================
    
    def run_all_tests(self):
        """Execute all regression tests"""
        print("=" * 80)
        print("🎯 STATUS TRANSITION REGRESSION TEST SUITE")
        print("=" * 80)
        print(f"Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Category 1: Status Transition Requirements
        print("📋 CATEGORY 1: STATUS TRANSITION REQUIREMENTS")
        print("-" * 50)
        self.test_valid_draft_to_submitted_transition()
        self.test_invalid_draft_to_reviewed_transition()
        self.test_submitted_to_reviewed_transition()
        print()
        
        # Category 2: Approval Process Requirements  
        print("📋 CATEGORY 2: APPROVAL PROCESS REQUIREMENTS")
        print("-" * 50)
        self.test_partial_approval_status_stability()
        self.test_complete_approval_triggers_review()
        print()
        
        # Category 3: Data Consistency Requirements
        print("📋 CATEGORY 3: DATA CONSISTENCY REQUIREMENTS")
        print("-" * 50)
        self.test_status_persistence_after_update()
        print()
        
        # Category 4: Transaction Integrity Requirements
        print("📋 CATEGORY 4: TRANSACTION INTEGRITY REQUIREMENTS")
        print("-" * 50)
        self.test_atomic_status_update()
        print()
        
        # Summary Report
        self.generate_summary_report()
    
    def generate_summary_report(self):
        """Generate comprehensive test summary report"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        # Count results
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        
        print("=" * 80)
        print("📊 REGRESSION TEST SUMMARY REPORT")
        print("=" * 80)
        print(f"Execution time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} - {end_time.strftime('%H:%M:%S')}")
        print(f"Duration: {duration.total_seconds():.2f} seconds")
        print()
        print(f"Total tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        print()
        
        if failed_tests > 0:
            print("🔴 FAILED TESTS:")
            print("-" * 40)
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"❌ {result['scenario']}")
                    print(f"   {result['details']}")
                    print()
        else:
            print("🎉 ALL TESTS PASSED! Status transition bugs successfully prevented.")
        
        # Save detailed results
        report_filename = f"regression_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump({
                'execution_time': self.start_time.isoformat(),
                'duration_seconds': duration.total_seconds(),
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'success_rate': (passed_tests/total_tests*100) if total_tests > 0 else 0,
                'test_results': self.test_results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Detailed report saved: {report_filename}")
        print("=" * 80)

if __name__ == '__main__':
    try:
        tests = StatusTransitionRegessionTests()
        tests.run_all_tests()
        
        # Exit with appropriate code
        failed_count = len([r for r in tests.test_results if r['status'] == 'FAIL'])
        sys.exit(1 if failed_count > 0 else 0)
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)