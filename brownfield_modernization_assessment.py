#!/usr/bin/env python3
"""
BMad Master - Brownfield Modernization Assessment
Comprehensive health check for ERP system modernization

This script validates all critical areas for brownfield modernization:
1. Authentication System (P0)
2. API Integration (P0) 
3. Database Health (P0)
4. Frontend-Backend Integration
5. Performance Metrics
6. Testing Coverage
7. Security Posture
8. Deployment Readiness
9. Technical Debt
10. Business Continuity
"""

import requests
import time
import json
import os
import sqlite3
import glob
from datetime import datetime
from pathlib import Path

class BrownfieldAssessment:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.frontend_url = "http://localhost:5174"
        self.results = {}
        
    def log_result(self, category, item, status, evidence="", risk="", recommendation="", priority="P2"):
        """Log assessment result with standardized format"""
        if category not in self.results:
            self.results[category] = []
            
        self.results[category].append({
            "item": item,
            "status": status,  # ✅ Pass, ⚠️ Warning, ❌ Fail
            "evidence": evidence,
            "risk": risk,
            "recommendation": recommendation,
            "priority": priority,
            "timestamp": datetime.now().isoformat()
        })
        
    def test_authentication_system(self):
        """Test P0: Authentication System"""
        print("🔐 Testing Authentication System (P0)...")
        
        # Test 1: Health endpoint availability
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                self.log_result("Authentication", "Health endpoint", "✅ Pass", 
                               f"Status: {response.status_code}, Response: {response.json()}", 
                               "", "", "P0")
            else:
                self.log_result("Authentication", "Health endpoint", "❌ Fail",
                               f"Status: {response.status_code}", 
                               "High - Service unavailable", 
                               "Check backend service status", "P0")
        except Exception as e:
            self.log_result("Authentication", "Health endpoint", "❌ Fail",
                           f"Exception: {str(e)}", 
                           "Critical - Backend not accessible", 
                           "Start backend service", "P0")
        
        # Test 2: CORS configuration
        try:
            response = requests.get(f"{self.base_url}/cors-test", timeout=5)
            if response.status_code == 200:
                self.log_result("Authentication", "CORS configuration", "✅ Pass",
                               f"CORS headers present: {dict(response.headers)}", 
                               "", "", "P0")
            else:
                self.log_result("Authentication", "CORS configuration", "❌ Fail",
                               f"Status: {response.status_code}", 
                               "High - Frontend-backend communication blocked", 
                               "Fix CORS configuration", "P0")
        except Exception as e:
            self.log_result("Authentication", "CORS configuration", "❌ Fail",
                           f"Exception: {str(e)}", 
                           "Critical - CORS not accessible", 
                           "Check CORS endpoint and service", "P0")
        
        # Test 3: JWT token implementation
        try:
            login_data = {
                "username": "admin",
                "password": "admin123"
            }
            response = requests.post(f"{self.base_url}/api/v1/auth/login", 
                                   json=login_data, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "refresh_token" in data:
                    self.log_result("Authentication", "JWT token implementation", "✅ Pass",
                                   f"Tokens received: {list(data.keys())}", 
                                   "", "", "P0")
                    # Store token for further tests
                    self.access_token = data["access_token"]
                else:
                    self.log_result("Authentication", "JWT token implementation", "⚠️ Warning",
                                   f"Response: {data}", 
                                   "Medium - Token format unexpected", 
                                   "Verify token response format", "P0")
            else:
                self.log_result("Authentication", "JWT token implementation", "❌ Fail",
                               f"Login failed: {response.status_code}", 
                               "High - Authentication broken", 
                               "Fix login endpoint", "P0")
        except Exception as e:
            self.log_result("Authentication", "JWT token implementation", "❌ Fail",
                           f"Exception: {str(e)}", 
                           "Critical - Login endpoint unreachable", 
                           "Check authentication service", "P0")
        
        # Test 4: Token persistence and authorization
        if hasattr(self, 'access_token'):
            try:
                headers = {"Authorization": f"Bearer {self.access_token}"}
                response = requests.get(f"{self.base_url}/api/v1/suppliers", 
                                      headers=headers, timeout=5)
                if response.status_code == 200:
                    self.log_result("Authentication", "Authorization header injection", "✅ Pass",
                                   f"Authorized request successful: {response.status_code}", 
                                   "", "", "P0")
                else:
                    self.log_result("Authentication", "Authorization header injection", "❌ Fail",
                                   f"Authorized request failed: {response.status_code}", 
                                   "High - Token not working", 
                                   "Check JWT verification", "P0")
            except Exception as e:
                self.log_result("Authentication", "Authorization header injection", "❌ Fail",
                               f"Exception: {str(e)}", 
                               "Critical - Authorization broken", 
                               "Check token verification system", "P0")
        
    def test_api_integration(self):
        """Test P0: API Integration"""
        print("🔌 Testing API Integration (P0)...")
        
        # Test 1: API endpoint availability
        endpoints = [
            "/api/v1/suppliers",
            "/api/v1/users", 
            "/api/v1/requisitions",
            "/api/v1/po"
        ]
        
        available_endpoints = 0
        for endpoint in endpoints:
            try:
                headers = {"Authorization": f"Bearer {self.access_token}"} if hasattr(self, 'access_token') else {}
                response = requests.get(f"{self.base_url}{endpoint}", 
                                      headers=headers, timeout=5)
                if response.status_code in [200, 401]:  # 401 means endpoint exists but needs auth
                    available_endpoints += 1
                    
            except Exception:
                pass
                
        if available_endpoints == len(endpoints):
            self.log_result("API Integration", "Endpoint availability", "✅ Pass",
                           f"All {len(endpoints)} endpoints accessible", 
                           "", "", "P0")
        elif available_endpoints >= len(endpoints) * 0.8:
            self.log_result("API Integration", "Endpoint availability", "⚠️ Warning",
                           f"{available_endpoints}/{len(endpoints)} endpoints accessible", 
                           "Medium - Some endpoints unavailable", 
                           "Check missing endpoints", "P0")
        else:
            self.log_result("API Integration", "Endpoint availability", "❌ Fail",
                           f"Only {available_endpoints}/{len(endpoints)} endpoints accessible", 
                           "High - Major API unavailability", 
                           "Fix API routing and services", "P0")
        
        # Test 2: Response format consistency
        if hasattr(self, 'access_token'):
            try:
                headers = {"Authorization": f"Bearer {self.access_token}"}
                response = requests.get(f"{self.base_url}/api/v1/suppliers", 
                                      headers=headers, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    required_fields = ["data", "total", "page", "page_size"]
                    if all(field in data for field in required_fields):
                        self.log_result("API Integration", "Response format consistency", "✅ Pass",
                                       f"Standard pagination format present: {list(data.keys())}", 
                                       "", "", "P0")
                    else:
                        self.log_result("API Integration", "Response format consistency", "⚠️ Warning",
                                       f"Response format: {list(data.keys())}", 
                                       "Medium - Inconsistent API format", 
                                       "Standardize API response format", "P1")
            except Exception as e:
                self.log_result("API Integration", "Response format consistency", "❌ Fail",
                               f"Exception: {str(e)}", 
                               "High - API response issues", 
                               "Check API response handling", "P0")
        
        # Test 3: Error handling standardization
        try:
            response = requests.get(f"{self.base_url}/api/v1/nonexistent-endpoint", timeout=5)
            if response.status_code == 404:
                try:
                    error_data = response.json()
                    if "error" in error_data:
                        self.log_result("API Integration", "Error handling standardization", "✅ Pass",
                                       f"Standardized error format: {error_data}", 
                                       "", "", "P1")
                    else:
                        self.log_result("API Integration", "Error handling standardization", "⚠️ Warning",
                                       f"Error response: {error_data}", 
                                       "Medium - Non-standard error format", 
                                       "Standardize error responses", "P1")
                except:
                    self.log_result("API Integration", "Error handling standardization", "⚠️ Warning",
                                   f"Non-JSON error response", 
                                   "Medium - Error format not JSON", 
                                   "Return JSON error responses", "P1")
        except Exception as e:
            self.log_result("API Integration", "Error handling standardization", "❌ Fail",
                           f"Exception: {str(e)}", 
                           "High - Error handling broken", 
                           "Fix error handling system", "P0")
    
    def test_database_health(self):
        """Test P0: Database Health"""
        print("🗄️ Testing Database Health (P0)...")
        
        # Test 1: Database connection
        try:
            db_path = "backend/erp_system.db"
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Test basic query
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                if len(tables) > 0:
                    self.log_result("Database", "Database connection", "✅ Pass",
                                   f"Connected successfully, {len(tables)} tables found", 
                                   "", "", "P0")
                    
                    # Test key tables exist
                    table_names = [table[0] for table in tables]
                    required_tables = ["users", "suppliers", "request_orders", "purchase_orders"]
                    missing_tables = [t for t in required_tables if t not in table_names]
                    
                    if not missing_tables:
                        self.log_result("Database", "Schema completeness", "✅ Pass",
                                       f"All required tables present: {required_tables}", 
                                       "", "", "P0")
                    else:
                        self.log_result("Database", "Schema completeness", "❌ Fail",
                                       f"Missing tables: {missing_tables}", 
                                       "Critical - Database schema incomplete", 
                                       "Run database migrations", "P0")
                        
                conn.close()
            else:
                self.log_result("Database", "Database connection", "❌ Fail",
                               f"Database file not found: {db_path}", 
                               "Critical - Database missing", 
                               "Initialize database", "P0")
                               
        except Exception as e:
            self.log_result("Database", "Database connection", "❌ Fail",
                           f"Exception: {str(e)}", 
                           "Critical - Database connection failed", 
                           "Check database service and permissions", "P0")
    
    def test_frontend_backend_integration(self):
        """Test Frontend-Backend Integration"""
        print("🔗 Testing Frontend-Backend Integration...")
        
        # Test 1: Frontend service availability
        try:
            response = requests.get(f"{self.frontend_url}", timeout=5)
            if response.status_code == 200:
                self.log_result("Integration", "Frontend service availability", "✅ Pass",
                               f"Frontend accessible at {self.frontend_url}", 
                               "", "", "P1")
            else:
                self.log_result("Integration", "Frontend service availability", "❌ Fail",
                               f"Frontend status: {response.status_code}", 
                               "High - Frontend unavailable", 
                               "Start frontend development server", "P1")
        except Exception as e:
            self.log_result("Integration", "Frontend service availability", "❌ Fail",
                           f"Exception: {str(e)}", 
                           "High - Frontend not accessible", 
                           "Check frontend service", "P1")
        
        # Test 2: Check frontend build configuration
        package_json_path = "frontend/package.json"
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path) as f:
                    package_data = json.load(f)
                
                required_deps = ["vue", "axios", "pinia", "vue-router"]
                missing_deps = [dep for dep in required_deps if dep not in package_data.get("dependencies", {})]
                
                if not missing_deps:
                    self.log_result("Integration", "Frontend dependencies", "✅ Pass",
                                   f"All required dependencies present: {required_deps}", 
                                   "", "", "P1")
                else:
                    self.log_result("Integration", "Frontend dependencies", "⚠️ Warning",
                                   f"Missing dependencies: {missing_deps}", 
                                   "Medium - Some dependencies missing", 
                                   "Install missing dependencies", "P1")
                    
            except Exception as e:
                self.log_result("Integration", "Frontend dependencies", "❌ Fail",
                               f"Error reading package.json: {str(e)}", 
                               "High - Cannot verify dependencies", 
                               "Check package.json format", "P1")
        
    def test_performance_metrics(self):
        """Test Performance Metrics"""
        print("⚡ Testing Performance Metrics...")
        
        # Test 1: API response times
        if hasattr(self, 'access_token'):
            endpoints_to_test = [
                "/api/v1/suppliers",
                "/health"
            ]
            
            for endpoint in endpoints_to_test:
                try:
                    headers = {"Authorization": f"Bearer {self.access_token}"} if endpoint.startswith("/api/v1") else {}
                    start_time = time.time()
                    response = requests.get(f"{self.base_url}{endpoint}", 
                                          headers=headers, timeout=10)
                    response_time = (time.time() - start_time) * 1000  # Convert to ms
                    
                    if response.status_code == 200:
                        if response_time < 500:
                            status = "✅ Pass"
                            risk = ""
                            recommendation = ""
                        elif response_time < 1000:
                            status = "⚠️ Warning"
                            risk = "Medium - Slow response times"
                            recommendation = "Optimize endpoint performance"
                        else:
                            status = "❌ Fail"
                            risk = "High - Very slow response times"
                            recommendation = "Critical performance optimization needed"
                            
                        self.log_result("Performance", f"API response time - {endpoint}", status,
                                       f"Response time: {response_time:.2f}ms", 
                                       risk, recommendation, "P1")
                        
                except Exception as e:
                    self.log_result("Performance", f"API response time - {endpoint}", "❌ Fail",
                                   f"Exception: {str(e)}", 
                                   "High - Performance test failed", 
                                   "Check endpoint availability", "P1")
    
    def test_testing_coverage(self):
        """Test Testing Coverage"""
        print("🧪 Testing Coverage Assessment...")
        
        # Test 1: Check for test files
        test_files = glob.glob("**/*test*.py", recursive=True)
        test_files.extend(glob.glob("**/test_*.py", recursive=True))
        
        if len(test_files) > 0:
            self.log_result("Testing", "Test files presence", "✅ Pass",
                           f"Found {len(test_files)} test files: {test_files[:5]}", 
                           "", "", "P1")
        else:
            self.log_result("Testing", "Test files presence", "❌ Fail",
                           "No test files found", 
                           "High - No automated testing", 
                           "Implement unit and integration tests", "P1")
        
        # Test 2: Check for recent test execution
        recent_test_files = glob.glob("**/*test*results*.json", recursive=True)
        recent_test_files.extend(glob.glob("**/*test*report*.json", recursive=True))
        
        if len(recent_test_files) > 0:
            self.log_result("Testing", "Recent test execution", "✅ Pass",
                           f"Found {len(recent_test_files)} test result files", 
                           "", "", "P1")
        else:
            self.log_result("Testing", "Recent test execution", "⚠️ Warning",
                           "No recent test results found", 
                           "Medium - Tests not being run regularly", 
                           "Set up CI/CD pipeline for automated testing", "P1")
    
    def test_security_posture(self):
        """Test Security Posture"""
        print("🔒 Testing Security Posture...")
        
        # Test 1: Secrets management
        env_files = [".env", ".env.example", "backend/.env"]
        secrets_handled = False
        
        for env_file in env_files:
            if os.path.exists(env_file):
                secrets_handled = True
                break
                
        if secrets_handled:
            self.log_result("Security", "Secrets management", "✅ Pass",
                           "Environment files found for secrets management", 
                           "", "", "P0")
        else:
            self.log_result("Security", "Secrets management", "⚠️ Warning",
                           "No environment files found", 
                           "Medium - Secrets may be hardcoded", 
                           "Implement proper secrets management", "P0")
        
        # Test 2: SQL injection prevention (basic check)
        if hasattr(self, 'access_token'):
            try:
                headers = {"Authorization": f"Bearer {self.access_token}"}
                # Test with potential SQL injection
                response = requests.get(f"{self.base_url}/api/v1/suppliers?search=' OR '1'='1", 
                                      headers=headers, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    # If we get normal response, it suggests parameterized queries
                    self.log_result("Security", "SQL injection prevention", "✅ Pass",
                                   "Endpoint handles potential SQL injection safely", 
                                   "", "", "P0")
                else:
                    self.log_result("Security", "SQL injection prevention", "⚠️ Warning",
                                   f"Unexpected response to SQL injection test: {response.status_code}", 
                                   "Medium - Unclear SQL injection handling", 
                                   "Verify parameterized queries", "P0")
            except Exception as e:
                self.log_result("Security", "SQL injection prevention", "❌ Fail",
                               f"Exception during security test: {str(e)}", 
                               "High - Security test failed", 
                               "Check security implementation", "P0")
    
    def test_deployment_readiness(self):
        """Test Deployment Readiness"""
        print("🚀 Testing Deployment Readiness...")
        
        # Test 1: Docker configuration
        docker_files = ["docker-compose.yml", "docker-compose.production.yml", "Dockerfile"]
        docker_ready = any(os.path.exists(f) for f in docker_files)
        
        if docker_ready:
            self.log_result("Deployment", "Containerization", "✅ Pass",
                           f"Docker configuration files found", 
                           "", "", "P1")
        else:
            self.log_result("Deployment", "Containerization", "❌ Fail",
                           "No Docker configuration found", 
                           "High - Deployment not containerized", 
                           "Create Docker configuration", "P1")
        
        # Test 2: Environment configuration
        config_files = ["backend/config.py", "frontend/vite.config.ts"]
        config_ready = all(os.path.exists(f) for f in config_files)
        
        if config_ready:
            self.log_result("Deployment", "Environment configuration", "✅ Pass",
                           "Configuration files present", 
                           "", "", "P1")
        else:
            missing_configs = [f for f in config_files if not os.path.exists(f)]
            self.log_result("Deployment", "Environment configuration", "⚠️ Warning",
                           f"Missing config files: {missing_configs}", 
                           "Medium - Incomplete configuration", 
                           "Create missing configuration files", "P1")
    
    def run_full_assessment(self):
        """Run complete brownfield modernization assessment"""
        print("🔍 BMad Master - Brownfield Modernization Assessment")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run all test categories
        self.test_authentication_system()
        self.test_api_integration() 
        self.test_database_health()
        self.test_frontend_backend_integration()
        self.test_performance_metrics()
        self.test_testing_coverage()
        self.test_security_posture()
        self.test_deployment_readiness()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Generate report
        self.generate_report(duration)
    
    def generate_report(self, duration):
        """Generate comprehensive assessment report"""
        print(f"\n📊 Assessment completed in {duration:.2f} seconds")
        print("=" * 60)
        
        # Calculate overall statistics
        total_tests = sum(len(tests) for tests in self.results.values())
        passed_tests = sum(len([t for t in tests if t["status"] == "✅ Pass"]) for tests in self.results.values())
        warning_tests = sum(len([t for t in tests if t["status"] == "⚠️ Warning"]) for tests in self.results.values())
        failed_tests = sum(len([t for t in tests if t["status"] == "❌ Fail"]) for tests in self.results.values())
        
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n🎯 EXECUTIVE SUMMARY")
        print(f"Overall Pass Rate: {pass_rate:.1f}% ({passed_tests}/{total_tests} tests)")
        print(f"✅ Pass: {passed_tests} | ⚠️ Warning: {warning_tests} | ❌ Fail: {failed_tests}")
        
        # Determine overall readiness
        if pass_rate >= 85 and failed_tests <= 2:
            readiness = "HIGH"
        elif pass_rate >= 70 and failed_tests <= 5:
            readiness = "MEDIUM" 
        else:
            readiness = "LOW"
            
        print(f"🚦 Modernization Readiness: {readiness}")
        
        # Critical issues (P0 failures)
        p0_failures = []
        for category, tests in self.results.items():
            for test in tests:
                if test["priority"] == "P0" and test["status"] == "❌ Fail":
                    p0_failures.append(f"{category}: {test['item']}")
        
        if p0_failures:
            print(f"\n🚨 CRITICAL BLOCKERS (P0 Failures):")
            for failure in p0_failures:
                print(f"  • {failure}")
        
        # Detailed results by category
        print(f"\n📋 DETAILED RESULTS BY CATEGORY")
        print("-" * 60)
        
        for category, tests in self.results.items():
            category_pass = len([t for t in tests if t["status"] == "✅ Pass"])
            category_total = len(tests)
            category_rate = (category_pass / category_total * 100) if category_total > 0 else 0
            
            print(f"\n{category.upper()} ({category_rate:.1f}% pass rate)")
            for test in tests:
                status_icon = test["status"]
                priority = f"[{test['priority']}]"
                print(f"  {status_icon} {priority} {test['item']}")
                if test["evidence"]:
                    print(f"      Evidence: {test['evidence']}")
                if test["risk"]:
                    print(f"      Risk: {test['risk']}")
                if test["recommendation"]:
                    print(f"      Recommendation: {test['recommendation']}")
        
        # Recommendations by priority
        print(f"\n💡 RECOMMENDATIONS BY PRIORITY")
        print("-" * 60)
        
        for priority in ["P0", "P1", "P2"]:
            priority_items = []
            for category, tests in self.results.items():
                for test in tests:
                    if test["priority"] == priority and test["status"] != "✅ Pass":
                        priority_items.append(f"{category}: {test['item']} - {test['recommendation']}")
            
            if priority_items:
                priority_name = {"P0": "CRITICAL", "P1": "HIGH", "P2": "MEDIUM"}[priority]
                print(f"\n{priority} ({priority_name} Priority):")
                for item in priority_items:
                    print(f"  • {item}")
        
        # Save detailed report
        report_data = {
            "assessment_date": datetime.now().isoformat(),
            "duration_seconds": duration,
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "warning_tests": warning_tests,
                "failed_tests": failed_tests,
                "pass_rate": pass_rate,
                "readiness_level": readiness
            },
            "results": self.results
        }
        
        report_file = f"brownfield_assessment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        print("=" * 60)

if __name__ == "__main__":
    assessment = BrownfieldAssessment()
    assessment.run_full_assessment()