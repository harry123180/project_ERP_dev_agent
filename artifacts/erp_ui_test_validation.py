#!/usr/bin/env python3
"""
ERP UI Test Validation Script
================================

This script demonstrates comprehensive UI testing capabilities for the ERP system
using various testing approaches including API testing, security validation,
and UI automation frameworks.

Author: Quinn, Test Architect & Quality Advisor
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ERPTestValidator:
    """Comprehensive ERP Test Validation Class"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.frontend_url = "http://localhost:5173"
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_test_result(self, test_name: str, success: bool, message: str, data: Any = None):
        """Log test result with timestamp"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        self.test_results.append(result)
        
        if success:
            logger.info(f"✅ {test_name}: {message}")
        else:
            logger.error(f"❌ {test_name}: {message}")
    
    def test_backend_connectivity(self) -> bool:
        """Test backend API connectivity"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            success = response.status_code == 200
            
            self.log_test_result(
                "Backend Connectivity",
                success,
                f"Status: {response.status_code}, Response: {response.text[:100]}"
            )
            return success
            
        except Exception as e:
            self.log_test_result("Backend Connectivity", False, f"Connection error: {str(e)}")
            return False
    
    def test_frontend_accessibility(self) -> bool:
        """Test frontend accessibility"""
        try:
            response = self.session.get(self.frontend_url, timeout=10)
            success = response.status_code == 200 and "ERP 系統" in response.text
            
            self.log_test_result(
                "Frontend Accessibility",
                success,
                f"Status: {response.status_code}, Contains ERP title: {'ERP 系統' in response.text}"
            )
            return success
            
        except Exception as e:
            self.log_test_result("Frontend Accessibility", False, f"Connection error: {str(e)}")
            return False
    
    def test_authentication_valid(self) -> bool:
        """Test valid authentication"""
        try:
            login_data = {"username": "admin", "password": "admin123"}
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                json=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                auth_data = response.json()
                self.auth_token = auth_data.get("access_token")
                success = self.auth_token is not None
                
                self.log_test_result(
                    "Valid Authentication",
                    success,
                    f"Login successful, token received: {self.auth_token[:20] if self.auth_token else 'None'}..."
                )
                return success
            else:
                self.log_test_result(
                    "Valid Authentication",
                    False,
                    f"Login failed with status: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test_result("Valid Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    def test_authentication_invalid(self) -> List[bool]:
        """Test invalid authentication scenarios"""
        test_cases = [
            {"username": "admin", "password": "wrongpassword", "expected": "Invalid password"},
            {"username": "wronguser", "password": "admin123", "expected": "Invalid username"},
            {"username": "", "password": "admin123", "expected": "Missing username"},
            {"username": "admin", "password": "", "expected": "Missing password"},
        ]
        
        results = []
        for i, case in enumerate(test_cases):
            try:
                response = self.session.post(
                    f"{self.base_url}/api/v1/auth/login",
                    json=case,
                    timeout=10
                )
                
                # Expecting non-200 status for invalid auth
                success = response.status_code != 200
                results.append(success)
                
                self.log_test_result(
                    f"Invalid Auth Test {i+1}",
                    success,
                    f"Expected failure, got status: {response.status_code} for {case['expected']}"
                )
                
            except Exception as e:
                results.append(False)
                self.log_test_result(f"Invalid Auth Test {i+1}", False, f"Error: {str(e)}")
        
        return results
    
    def test_protected_endpoints(self) -> List[bool]:
        """Test protected endpoints with authentication"""
        if not self.auth_token:
            self.log_test_result("Protected Endpoints", False, "No auth token available")
            return [False]
        
        endpoints = [
            ("/api/v1/auth/me", "User Profile"),
            ("/api/v1/users", "Users List"),
            ("/api/v1/suppliers", "Suppliers List"),
            ("/api/v1/inventory", "Inventory List"),
            ("/api/v1/po", "Purchase Orders"),
        ]
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        results = []
        
        for endpoint, name in endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", headers=headers, timeout=10)
                success = response.status_code == 200
                results.append(success)
                
                self.log_test_result(
                    f"Protected Endpoint: {name}",
                    success,
                    f"Status: {response.status_code}, Data length: {len(response.text)}"
                )
                
            except Exception as e:
                results.append(False)
                self.log_test_result(f"Protected Endpoint: {name}", False, f"Error: {str(e)}")
        
        return results
    
    def test_security_sql_injection(self) -> List[bool]:
        """Test SQL injection resistance"""
        if not self.auth_token:
            return [False]
        
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "1' UNION SELECT * FROM users --",
            "admin'--",
            "' OR 1=1 #"
        ]
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        results = []
        
        for payload in sql_payloads:
            try:
                # Test inventory search endpoint with SQL injection payloads
                response = self.session.get(
                    f"{self.base_url}/api/v1/inventory",
                    params={"name": payload},
                    headers=headers,
                    timeout=10
                )
                
                # Success means the system handled the malicious input properly
                success = response.status_code in [200, 400, 422]  # Should not crash
                results.append(success)
                
                self.log_test_result(
                    f"SQL Injection Test",
                    success,
                    f"Payload: {payload[:20]}..., Status: {response.status_code}"
                )
                
            except Exception as e:
                results.append(False)
                self.log_test_result("SQL Injection Test", False, f"Error with payload: {str(e)}")
        
        return results
    
    def test_unauthorized_access(self) -> List[bool]:
        """Test unauthorized access to protected resources"""
        endpoints = [
            "/api/v1/users",
            "/api/v1/suppliers",
            "/api/v1/inventory",
            "/api/v1/requisitions",
        ]
        
        results = []
        
        for endpoint in endpoints:
            try:
                # Request without authorization header
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                success = response.status_code == 401  # Expecting Unauthorized
                results.append(success)
                
                self.log_test_result(
                    f"Unauthorized Access: {endpoint}",
                    success,
                    f"Expected 401, got: {response.status_code}"
                )
                
            except Exception as e:
                results.append(False)
                self.log_test_result(f"Unauthorized Access: {endpoint}", False, f"Error: {str(e)}")
        
        return results
    
    def test_error_handling(self) -> List[bool]:
        """Test error handling for various scenarios"""
        if not self.auth_token:
            return [False]
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        test_cases = [
            ("/api/v1/nonexistent", 404, "Non-existent endpoint"),
            ("/api/v1/users/999999", 404, "Non-existent user ID"),
        ]
        
        results = []
        
        for endpoint, expected_status, description in test_cases:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", headers=headers, timeout=10)
                success = response.status_code == expected_status
                results.append(success)
                
                self.log_test_result(
                    f"Error Handling: {description}",
                    success,
                    f"Expected {expected_status}, got: {response.status_code}"
                )
                
            except Exception as e:
                results.append(False)
                self.log_test_result(f"Error Handling: {description}", False, f"Error: {str(e)}")
        
        return results
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test scenarios"""
        logger.info("🚀 Starting comprehensive ERP validation tests...")
        start_time = time.time()
        
        # Basic connectivity tests
        backend_ok = self.test_backend_connectivity()
        frontend_ok = self.test_frontend_accessibility()
        
        # Authentication tests
        auth_valid = self.test_authentication_valid()
        auth_invalid = self.test_authentication_invalid()
        
        # Protected endpoint tests
        protected_results = self.test_protected_endpoints()
        
        # Security tests
        sql_injection_results = self.test_security_sql_injection()
        unauthorized_results = self.test_unauthorized_access()
        error_handling_results = self.test_error_handling()
        
        # Calculate summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        summary = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
            "execution_time": round(time.time() - start_time, 2),
            "backend_connectivity": backend_ok,
            "frontend_accessibility": frontend_ok,
            "authentication_valid": auth_valid,
            "authentication_security": all(auth_invalid),
            "protected_endpoints": all(protected_results),
            "sql_injection_resistance": all(sql_injection_results),
            "unauthorized_access_protection": all(unauthorized_results),
            "error_handling": all(error_handling_results)
        }
        
        logger.info(f"📊 Test Summary: {passed_tests}/{total_tests} tests passed ({summary['success_rate']:.1f}%)")
        return summary
    
    def save_test_report(self, filename: str = None):
        """Save comprehensive test report"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"erp_test_report_{timestamp}.json"
        
        report = {
            "metadata": {
                "test_execution_time": datetime.now().isoformat(),
                "base_url": self.base_url,
                "frontend_url": self.frontend_url,
                "total_tests": len(self.test_results)
            },
            "summary": self.run_all_tests(),
            "detailed_results": self.test_results
        }
        
        filepath = f"D:/AWORKSPACE/Github/project_ERP_dev_agent/artifacts/{filename}"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📋 Test report saved to: {filepath}")
        return filepath

def main():
    """Main execution function"""
    validator = ERPTestValidator()
    
    # Run all tests
    summary = validator.run_all_tests()
    
    # Save detailed report
    report_file = validator.save_test_report()
    
    print("\n" + "="*80)
    print("🎯 ERP SYSTEM TEST VALIDATION COMPLETE")
    print("="*80)
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed']} ✅")
    print(f"Failed: {summary['failed']} ❌")
    print(f"Success Rate: {summary['success_rate']:.1f}%")
    print(f"Execution Time: {summary['execution_time']}s")
    print(f"Report Saved: {report_file}")
    print("="*80)
    
    return summary['success_rate'] >= 80  # Consider 80%+ as successful validation

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)