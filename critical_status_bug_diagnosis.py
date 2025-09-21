#!/usr/bin/env python3
"""
CRITICAL STATUS TRANSITION BUG DIAGNOSIS
=========================================

This script diagnoses the critical bug where:
1. Requisitions revert from 'submitted' to 'draft' after submission
2. After approval, status goes to 'submitted' instead of 'reviewed'

Root Cause Analysis:
The update_status_after_review() method in RequestOrder model has a critical
transaction management bug (lines 105-113) where it calls db.session.commit()
directly inside the model method, causing conflicts with API endpoint transactions.
"""

import json
import time
import requests
from datetime import datetime

BASE_URL = 'http://localhost:5000'
API_BASE = f'{BASE_URL}/api/v1'

class CriticalBugDiagnosis:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.token = None
        
    def authenticate(self):
        """Authenticate as procurement user"""
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
        print(f"[{step}] {status}: {details}")

    def create_test_requisition(self):
        """Create a test requisition"""
        try:
            requisition_data = {
                'usage_type': 'daily',
                'items': [{
                    'item_name': 'Critical Bug Test Item',
                    'item_quantity': 1,
                    'item_unit': 'piece',
                    'item_description': 'Testing critical status transition bug'
                }]
            }
            
            response = self.session.post(f'{API_BASE}/requisitions', json=requisition_data)
            
            if response.status_code == 201:
                req_no = response.json()['request_order_no']
                self.log_result('CREATE_REQUISITION', 'SUCCESS', f'Created {req_no}')
                return req_no
            else:
                self.log_result('CREATE_REQUISITION', 'FAILED', f'HTTP {response.status_code}: {response.text}')
                return None
                
        except Exception as e:
            self.log_result('CREATE_REQUISITION', 'ERROR', str(e))
            return None

    def submit_requisition(self, req_no):
        """Submit requisition and check for status bug"""
        try:
            # Check initial status
            response = self.session.get(f'{API_BASE}/requisitions/{req_no}')
            if response.status_code == 200:
                initial_status = response.json()['order_status']
                self.log_result('INITIAL_STATUS', 'SUCCESS', f'{req_no} status: {initial_status}')
                
                if initial_status != 'draft':
                    self.log_result('INITIAL_STATUS', 'BUG_DETECTED', f'Expected draft but got {initial_status}')
            
            # Submit the requisition
            response = self.session.post(f'{API_BASE}/requisitions/{req_no}/submit')
            
            if response.status_code == 200:
                submitted_status = response.json()['order_status']
                self.log_result('SUBMIT_REQUISITION', 'SUCCESS', f'{req_no} submitted with status: {submitted_status}')
                
                if submitted_status != 'submitted':
                    self.log_result('SUBMIT_STATUS_BUG', 'CRITICAL_BUG', f'Status should be "submitted" but is "{submitted_status}"')
                    return False
                
                # Wait a moment and check again for status revert
                time.sleep(1)
                response = self.session.get(f'{API_BASE}/requisitions/{req_no}')
                if response.status_code == 200:
                    current_status = response.json()['order_status']
                    if current_status != 'submitted':
                        self.log_result('SUBMIT_REVERT_BUG', 'CRITICAL_BUG', f'Status reverted from submitted to {current_status}')
                        return False
                
                return True
            else:
                self.log_result('SUBMIT_REQUISITION', 'FAILED', f'HTTP {response.status_code}: {response.text}')
                return False
                
        except Exception as e:
            self.log_result('SUBMIT_REQUISITION', 'ERROR', str(e))
            return False

    def approve_requisition_item(self, req_no):
        """Approve requisition item and check for status transition bug"""
        try:
            # Get requisition details to find item detail_id
            response = self.session.get(f'{API_BASE}/requisitions/{req_no}')
            if response.status_code != 200:
                self.log_result('GET_REQ_DETAILS', 'FAILED', f'Cannot get requisition details')
                return False
            
            items = response.json()['items']
            if not items:
                self.log_result('NO_ITEMS', 'FAILED', f'No items found in requisition')
                return False
            
            detail_id = items[0]['detail_id']
            
            # Approve the item
            approval_data = {
                'supplier_id': 'T001',
                'unit_price': 100.00,
                'note': 'Critical bug test approval'
            }
            
            response = self.session.post(
                f'{API_BASE}/requisitions/{req_no}/lines/{detail_id}/approve',
                json=approval_data
            )
            
            if response.status_code == 200:
                self.log_result('APPROVE_ITEM', 'SUCCESS', f'Approved item {detail_id}')
                
                # Check requisition status after approval
                time.sleep(1)  # Allow for status update
                response = self.session.get(f'{API_BASE}/requisitions/{req_no}')
                if response.status_code == 200:
                    final_status = response.json()['order_status']
                    summary = response.json()['summary']
                    
                    self.log_result('FINAL_STATUS_CHECK', 'INFO', f'Status: {final_status}, Summary: {summary}')
                    
                    # Check for the critical bug
                    if summary['pending_items'] == 0 and final_status != 'reviewed':
                        self.log_result('APPROVAL_STATUS_BUG', 'CRITICAL_BUG', f'All items approved but status is "{final_status}" instead of "reviewed"')
                        return False
                    elif final_status == 'reviewed':
                        self.log_result('APPROVAL_STATUS_CORRECT', 'SUCCESS', f'Status correctly updated to "reviewed"')
                        return True
                    else:
                        self.log_result('APPROVAL_PENDING', 'INFO', f'Status update pending - {summary["pending_items"]} items still pending')
                        return True
                else:
                    self.log_result('FINAL_STATUS_CHECK', 'FAILED', 'Cannot check final status')
                    return False
            else:
                self.log_result('APPROVE_ITEM', 'FAILED', f'HTTP {response.status_code}: {response.text}')
                return False
                
        except Exception as e:
            self.log_result('APPROVE_ITEM', 'ERROR', str(e))
            return False

    def test_status_fix_endpoint(self, req_no):
        """Test the manual status fix endpoint"""
        try:
            response = self.session.post(f'{API_BASE}/requisitions/{req_no}/fix-status')
            
            if response.status_code == 200:
                result = response.json()
                self.log_result('STATUS_FIX_ENDPOINT', 'SUCCESS', f'Fix attempted: {result}')
                return True
            else:
                self.log_result('STATUS_FIX_ENDPOINT', 'FAILED', f'HTTP {response.status_code}: {response.text}')
                return False
                
        except Exception as e:
            self.log_result('STATUS_FIX_ENDPOINT', 'ERROR', str(e))
            return False

    def run_diagnosis(self):
        """Run complete critical bug diagnosis"""
        print("=" * 60)
        print("CRITICAL STATUS TRANSITION BUG DIAGNOSIS")
        print("=" * 60)
        
        if not self.authenticate():
            print("Cannot authenticate - aborting diagnosis")
            return
        
        # Create and test requisition
        req_no = self.create_test_requisition()
        if not req_no:
            print("Cannot create test requisition - aborting")
            return
        
        # Test submission bug
        if not self.submit_requisition(req_no):
            print(f"CRITICAL BUG DETECTED during submission of {req_no}")
        
        # Test approval workflow bug
        if not self.approve_requisition_item(req_no):
            print(f"CRITICAL BUG DETECTED during approval of {req_no}")
        
        # Test manual fix endpoint
        self.test_status_fix_endpoint(req_no)
        
        # Save results
        report_file = f'critical_bug_diagnosis_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'diagnosis_time': datetime.now().isoformat(),
                'test_requisition': req_no,
                'results': self.test_results,
                'summary': self.generate_summary()
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\nDiagnosis complete. Report saved to: {report_file}")
        print(self.generate_summary())

    def generate_summary(self):
        """Generate diagnosis summary"""
        bugs_detected = [r for r in self.test_results if 'BUG' in r['status']]
        errors = [r for r in self.test_results if r['status'] == 'ERROR']
        
        summary = f"""
DIAGNOSIS SUMMARY:
- Total tests: {len(self.test_results)}
- Bugs detected: {len(bugs_detected)}
- Errors: {len(errors)}

CRITICAL ISSUES:
"""
        for bug in bugs_detected:
            summary += f"- {bug['step']}: {bug['details']}\n"
        
        if bugs_detected:
            summary += "\nRECOMMENDED FIX: Remove db.session.commit() from RequestOrder.update_status_after_review() method"
        
        return summary

if __name__ == '__main__':
    diagnosis = CriticalBugDiagnosis()
    diagnosis.run_diagnosis()