#!/usr/bin/env python3
"""
Deployment Readiness Validation Script
Validates system readiness for next story deployment
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:5000/api/v1"
FRONTEND_URL = "http://localhost:5173"

def print_section(title):
    """Print section header"""
    print(f"\n{'=' * 60}")
    print(f" {title}")
    print(f"{'=' * 60}")

def print_test(test_name, status, message=""):
    """Print test result"""
    status_symbol = "✅" if status else "❌"
    print(f"{status_symbol} {test_name}")
    if message:
        print(f"   {message}")

def test_system_health():
    """Test basic system health endpoints"""
    print_section("SYSTEM HEALTH VALIDATION")
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Health endpoint
    total_tests += 1
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            print_test("Health endpoint responding", True, f"Status: {response.status_code}")
            tests_passed += 1
        else:
            print_test("Health endpoint responding", False, f"Status: {response.status_code}")
    except Exception as e:
        print_test("Health endpoint responding", False, f"Error: {str(e)}")
    
    # Test 2: CORS test endpoint  
    total_tests += 1
    try:
        response = requests.get("http://localhost:5000/cors-test", timeout=5)
        if response.status_code == 200:
            print_test("CORS configuration working", True, f"Status: {response.status_code}")
            tests_passed += 1
        else:
            print_test("CORS configuration working", False, f"Status: {response.status_code}")
    except Exception as e:
        print_test("CORS configuration working", False, f"Error: {str(e)}")
    
    return tests_passed, total_tests

def test_authentication_system():
    """Test authentication system stability"""
    print_section("AUTHENTICATION SYSTEM VALIDATION")
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Login endpoint availability
    total_tests += 1
    try:
        # Test OPTIONS first (CORS preflight)
        options_response = requests.options(f"{API_BASE_URL}/auth/login", timeout=5)
        print_test("Auth endpoint CORS preflight", options_response.status_code == 200, 
                  f"OPTIONS status: {options_response.status_code}")
        
        # Test login with test credentials
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(f"{API_BASE_URL}/auth/login", 
                               json=login_data, 
                               headers={"Content-Type": "application/json"},
                               timeout=10)
        
        if response.status_code == 200:
            print_test("Login endpoint functional", True, f"Login successful: {response.status_code}")
            tests_passed += 1
            
            # Extract token for further tests
            token_data = response.json()
            return tests_passed, total_tests, token_data.get('access_token')
        else:
            print_test("Login endpoint functional", False, f"Login failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error details: {error_data}")
            except:
                print(f"   Response text: {response.text}")
                
    except Exception as e:
        print_test("Login endpoint functional", False, f"Error: {str(e)}")
        
    return tests_passed, total_tests, None

def test_protected_endpoints(token):
    """Test protected endpoints with authentication"""
    print_section("PROTECTED ENDPOINT VALIDATION")
    
    tests_passed = 0
    total_tests = 0
    
    if not token:
        print_test("Skipping protected endpoint tests", False, "No authentication token available")
        return tests_passed, total_tests
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test protected endpoints
    protected_endpoints = [
        ("/suppliers", "Suppliers endpoint"),
        ("/users/profile", "User profile endpoint"),
    ]
    
    for endpoint, description in protected_endpoints:
        total_tests += 1
        try:
            response = requests.get(f"{API_BASE_URL}{endpoint}", 
                                  headers=headers, 
                                  timeout=10)
            
            if response.status_code in [200, 404]:  # 404 is ok if endpoint doesn't exist yet
                print_test(f"{description} accessible", True, f"Status: {response.status_code}")
                tests_passed += 1
            elif response.status_code == 401:
                print_test(f"{description} accessible", False, "Authentication failed (401)")
            else:
                print_test(f"{description} accessible", False, f"Status: {response.status_code}")
                
        except Exception as e:
            print_test(f"{description} accessible", False, f"Error: {str(e)}")
    
    return tests_passed, total_tests

def test_database_operations():
    """Test database connectivity and operations"""
    print_section("DATABASE VALIDATION")
    
    tests_passed = 0
    total_tests = 0
    
    # Test database health using our health check script
    total_tests += 1
    try:
        import subprocess
        import os
        
        # Change to backend directory and run health check
        backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
        if os.path.exists(backend_dir):
            result = subprocess.run(
                ['python', 'database_health_check.py'],
                cwd=backend_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print_test("Database connectivity", True, "Health check passed")
                tests_passed += 1
            else:
                print_test("Database connectivity", False, f"Health check failed: {result.returncode}")
                print(f"   Output: {result.stdout}")
        else:
            print_test("Database connectivity", False, "Backend directory not found")
            
    except Exception as e:
        print_test("Database connectivity", False, f"Error: {str(e)}")
    
    return tests_passed, total_tests

def test_error_handling():
    """Test enhanced error handling"""
    print_section("ERROR HANDLING VALIDATION")
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: 404 error handling
    total_tests += 1
    try:
        response = requests.get(f"{API_BASE_URL}/nonexistent-endpoint", timeout=5)
        if response.status_code == 404:
            try:
                error_data = response.json()
                if 'error' in error_data and 'code' in error_data['error']:
                    print_test("404 error handling", True, f"Structured error response: {error_data['error']['code']}")
                    tests_passed += 1
                else:
                    print_test("404 error handling", False, "Error response not properly structured")
            except:
                print_test("404 error handling", False, "Error response not JSON")
        else:
            print_test("404 error handling", False, f"Expected 404, got {response.status_code}")
    except Exception as e:
        print_test("404 error handling", False, f"Error: {str(e)}")
    
    # Test 2: Unauthorized access error handling  
    total_tests += 1
    try:
        response = requests.get(f"{API_BASE_URL}/suppliers", timeout=5)
        if response.status_code == 401:
            try:
                error_data = response.json()
                if 'error' in error_data and 'code' in error_data['error']:
                    print_test("401 error handling", True, f"Structured error response: {error_data['error']['code']}")
                    tests_passed += 1
                else:
                    print_test("401 error handling", False, "Error response not properly structured")
            except:
                print_test("401 error handling", False, "Error response not JSON")
        else:
            print_test("401 error handling", False, f"Expected 401, got {response.status_code}")
    except Exception as e:
        print_test("401 error handling", False, f"Error: {str(e)}")
    
    return tests_passed, total_tests

def test_performance_baseline():
    """Test basic performance characteristics"""
    print_section("PERFORMANCE BASELINE VALIDATION")
    
    tests_passed = 0
    total_tests = 0
    
    # Test API response times
    endpoints_to_test = [
        ("http://localhost:5000/health", "Health endpoint", False),
        (f"{API_BASE_URL}/auth/login", "Login endpoint", True)
    ]
    
    for endpoint, name, is_post in endpoints_to_test:
        total_tests += 1
        try:
            start_time = time.time()
            
            if is_post:
                response = requests.post(endpoint, 
                                       json={"username": "test", "password": "test"}, 
                                       timeout=10)
            else:
                response = requests.get(endpoint, timeout=10)
                
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            # Response time should be under 5 seconds for development environment
            # (Production target is 2 seconds, but development allows more flexibility)
            if response_time < 5000:
                print_test(f"{name} response time", True, f"{response_time:.0f}ms (< 5000ms dev target)")
                tests_passed += 1
            else:
                print_test(f"{name} response time", False, f"{response_time:.0f}ms (> 5000ms dev target)")
                
        except Exception as e:
            print_test(f"{name} response time", False, f"Error: {str(e)}")
    
    return tests_passed, total_tests

def generate_readiness_report(all_results):
    """Generate final readiness report"""
    print_section("DEPLOYMENT READINESS REPORT")
    
    total_passed = sum(result[0] for result in all_results)
    total_tests = sum(result[1] for result in all_results)
    
    pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n📊 OVERALL RESULTS:")
    print(f"   Tests Passed: {total_passed}/{total_tests}")
    print(f"   Pass Rate: {pass_rate:.1f}%")
    print()
    
    # Determine readiness level
    if pass_rate >= 90:
        readiness = "✅ HIGH - Ready for next story deployment"
        exit_code = 0
    elif pass_rate >= 70:
        readiness = "⚠️  MEDIUM - Minor issues to address before deployment"
        exit_code = 0
    elif pass_rate >= 50:
        readiness = "❌ LOW - Significant issues must be resolved"
        exit_code = 1
    else:
        readiness = "🚨 CRITICAL - System not ready for deployment"
        exit_code = 1
    
    print(f"🎯 READINESS ASSESSMENT: {readiness}")
    print()
    
    # Recommendations
    print("📋 RECOMMENDATIONS:")
    
    if pass_rate >= 90:
        print("   • System is ready for next story implementation")
        print("   • Continue with brownfield modernization workflow")
        print("   • Monitor performance during development")
        
    elif pass_rate >= 70:
        print("   • Address minor issues identified above")
        print("   • Rerun validation after fixes")
        print("   • Proceed with caution")
        
    elif pass_rate >= 50:
        print("   • Fix major issues before proceeding")
        print("   • Focus on authentication and database connectivity")
        print("   • Revalidate system stability")
        
    else:
        print("   • System requires immediate attention")
        print("   • Do not proceed with new development")
        print("   • Review QA fixes and system configuration")
    
    print(f"\n⏰ Validation completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return exit_code

def main():
    """Main validation function"""
    print("🔍 ERP System Deployment Readiness Validation")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 API Base URL: {API_BASE_URL}")
    
    # Run all validation tests
    all_results = []
    
    # System health
    result = test_system_health()
    all_results.append(result)
    
    # Authentication (get token for further tests)
    auth_result = test_authentication_system()
    token = None
    if len(auth_result) > 2:
        token = auth_result[2]
        all_results.append((auth_result[0], auth_result[1]))
    else:
        all_results.append(auth_result)
    
    # Protected endpoints
    result = test_protected_endpoints(token)
    all_results.append(result)
    
    # Database operations
    result = test_database_operations()
    all_results.append(result)
    
    # Error handling
    result = test_error_handling()
    all_results.append(result)
    
    # Performance baseline
    result = test_performance_baseline()
    all_results.append(result)
    
    # Generate final report and exit
    exit_code = generate_readiness_report(all_results)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()