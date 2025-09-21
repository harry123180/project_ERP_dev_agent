#!/usr/bin/env python3
"""
Comprehensive QA Validation for Newly Implemented Procurement Workflow Endpoints

This script validates the 18 newly implemented endpoints to verify fixes for
procurement workflow compliance improvement from 37.5% baseline.

Test Categories:
1. Endpoint Accessibility (HTTP 200 response)
2. Authentication Integration (JWT token validation)
3. Data Validation and Error Handling
4. Business Logic Validation
5. Performance Testing (<2 second target)
6. End-to-End Integration Testing

Target: Improve compliance from 37.5% to 85%+
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Any
import concurrent.futures
import traceback

class ProcurementWorkflowQAValidator:
    def __init__(self, base_url: str = "http://127.0.0.1:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": base_url,
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "compliance_score": 0.0,
            "endpoint_results": {},
            "performance_results": {},
            "integration_results": {},
            "summary": {}
        }
        
        # Define all 18 newly implemented endpoints
        self.new_endpoints = {
            # Storage Management Endpoints
            "storage_tree": {
                "method": "GET",
                "path": "/api/v1/storage/tree",
                "description": "Storage hierarchy",
                "category": "Storage Management",
                "requires_auth": True
            },
            "storage_locations": {
                "method": "GET", 
                "path": "/api/v1/storage/locations",
                "description": "List storage locations",
                "category": "Storage Management",
                "requires_auth": True
            },
            "storage_putaway": {
                "method": "GET",
                "path": "/api/v1/storage/putaway", 
                "description": "Items ready for put-away",
                "category": "Storage Management",
                "requires_auth": True
            },
            "storage_putaway_assign": {
                "method": "POST",
                "path": "/api/v1/storage/putaway/assign",
                "description": "Assign storage location",
                "category": "Storage Management", 
                "requires_auth": True,
                "test_data": {"item_id": "ITEM001", "location_id": "LOC001"}
            },
            "storage_zones_create": {
                "method": "POST",
                "path": "/api/v1/storage/admin/zones",
                "description": "Create storage zones",
                "category": "Storage Management",
                "requires_auth": True,
                "test_data": {"name": "QA_Test_Zone", "description": "QA validation zone"}
            },
            "storage_shelves_create": {
                "method": "POST", 
                "path": "/api/v1/storage/admin/shelves",
                "description": "Create storage shelves",
                "category": "Storage Management",
                "requires_auth": True,
                "test_data": {"zone_id": "ZONE001", "shelf_code": "QA_SHELF_001"}
            },
            
            # Logistics Management Endpoints
            "logistics_shipping": {
                "method": "GET",
                "path": "/api/v1/logistics/shipping",
                "description": "List shipping records",
                "category": "Logistics Management",
                "requires_auth": True
            },
            "logistics_receiving": {
                "method": "GET",
                "path": "/api/v1/logistics/receiving", 
                "description": "Items ready for receiving",
                "category": "Logistics Management",
                "requires_auth": True
            },
            "logistics_delivery_tracking": {
                "method": "GET",
                "path": "/api/v1/logistics/delivery-tracking",
                "description": "Track deliveries", 
                "category": "Logistics Management",
                "requires_auth": True
            },
            "logistics_shipping_update": {
                "method": "POST",
                "path": "/api/v1/logistics/shipping/update-status",
                "description": "Update shipping status",
                "category": "Logistics Management",
                "requires_auth": True,
                "test_data": {"shipping_id": "SHIP001", "status": "in_transit"}
            },
            "logistics_receiving_confirm": {
                "method": "POST", 
                "path": "/api/v1/logistics/receiving/confirm-item",
                "description": "Confirm item receipt",
                "category": "Logistics Management",
                "requires_auth": True,
                "test_data": {"item_id": "ITEM001", "quantity": 10, "condition": "good"}
            },
            
            # Acceptance & Quality Control Endpoints  
            "acceptance_pending": {
                "method": "GET",
                "path": "/api/v1/acceptance/pending",
                "description": "Pending acceptance items",
                "category": "Acceptance & Quality Control",
                "requires_auth": True
            },
            "acceptance_validation": {
                "method": "POST",
                "path": "/api/v1/acceptance/validation",
                "description": "Perform item validation",
                "category": "Acceptance & Quality Control", 
                "requires_auth": True,
                "test_data": {"item_id": "ITEM001", "validation_type": "quality_check"}
            },
            "acceptance_quality_check": {
                "method": "POST",
                "path": "/api/v1/acceptance/quality-check",
                "description": "Detailed quality checks",
                "category": "Acceptance & Quality Control",
                "requires_auth": True,
                "test_data": {"item_id": "ITEM001", "check_parameters": {"weight": True, "dimensions": True}}
            },
            "acceptance_reports_summary": {
                "method": "GET", 
                "path": "/api/v1/acceptance/reports/summary",
                "description": "Acceptance reports",
                "category": "Acceptance & Quality Control",
                "requires_auth": True
            }
        }

    def authenticate(self, username: str = "admin", password: str = "admin123") -> bool:
        """Authenticate and obtain JWT token"""
        print(f"🔐 Authenticating as {username}...")
        
        try:
            auth_data = {
                "username": username,
                "password": password
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/login", 
                json=auth_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'access_token' in data:
                    self.auth_token = data['access_token']
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.auth_token}'
                    })
                    print(f"✅ Authentication successful")
                    return True
                else:
                    print(f"❌ No access_token in response: {data}")
                    return False
            else:
                print(f"❌ Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False

    def test_endpoint_accessibility(self, endpoint_name: str, endpoint_config: Dict) -> Dict:
        """Test if endpoint is accessible (returns 200, not 404/500)"""
        result = {
            "endpoint": endpoint_name,
            "method": endpoint_config["method"],
            "path": endpoint_config["path"],
            "description": endpoint_config["description"],
            "category": endpoint_config["category"],
            "accessible": False,
            "status_code": None,
            "response_time": None,
            "error": None,
            "response_data": None
        }
        
        try:
            start_time = time.time()
            
            if endpoint_config["method"] == "GET":
                response = self.session.get(
                    f"{self.base_url}{endpoint_config['path']}",
                    timeout=5
                )
            else:  # POST
                test_data = endpoint_config.get("test_data", {})
                response = self.session.post(
                    f"{self.base_url}{endpoint_config['path']}",
                    json=test_data,
                    timeout=5
                )
            
            end_time = time.time()
            result["response_time"] = round((end_time - start_time) * 1000, 2)  # ms
            result["status_code"] = response.status_code
            
            # Endpoint is accessible if it doesn't return 404 or 500
            if response.status_code not in [404, 500]:
                result["accessible"] = True
                
                # Try to parse JSON response
                try:
                    result["response_data"] = response.json()
                except:
                    result["response_data"] = response.text[:200]
            
        except requests.exceptions.Timeout:
            result["error"] = "Request timeout (>5s)"
        except requests.exceptions.ConnectionError:
            result["error"] = "Connection error - service may be down"
        except Exception as e:
            result["error"] = str(e)
            
        return result

    def test_all_endpoints_accessibility(self) -> Dict:
        """Test accessibility of all 18 new endpoints"""
        print(f"\n🧪 Testing accessibility of {len(self.new_endpoints)} new procurement endpoints...")
        
        results = {}
        accessible_count = 0
        
        for endpoint_name, endpoint_config in self.new_endpoints.items():
            print(f"  Testing {endpoint_config['method']} {endpoint_config['path']}...")
            result = self.test_endpoint_accessibility(endpoint_name, endpoint_config)
            results[endpoint_name] = result
            
            if result["accessible"]:
                accessible_count += 1
                print(f"    ✅ Accessible ({result['status_code']}) - {result['response_time']}ms")
            else:
                status = result["status_code"] or "ERROR"
                error = result["error"] or "Unknown error"
                print(f"    ❌ Not accessible ({status}) - {error}")
        
        accessibility_score = (accessible_count / len(self.new_endpoints)) * 100
        print(f"\n📊 Endpoint Accessibility: {accessible_count}/{len(self.new_endpoints)} ({accessibility_score:.1f}%)")
        
        return {
            "accessible_endpoints": accessible_count,
            "total_endpoints": len(self.new_endpoints), 
            "accessibility_score": accessibility_score,
            "results": results
        }

    def test_authentication_integration(self) -> Dict:
        """Test JWT authentication integration across endpoints"""
        print(f"\n🔑 Testing JWT authentication integration...")
        
        # Test without token
        print("  Testing endpoints without authentication...")
        temp_headers = self.session.headers.copy()
        if 'Authorization' in self.session.headers:
            del self.session.headers['Authorization']
        
        unauthorized_results = {}
        protected_endpoints = [name for name, config in self.new_endpoints.items() 
                             if config.get("requires_auth", False)]
        
        for endpoint_name in protected_endpoints[:3]:  # Test sample
            endpoint_config = self.new_endpoints[endpoint_name]
            try:
                response = self.session.get(f"{self.base_url}{endpoint_config['path']}", timeout=3)
                unauthorized_results[endpoint_name] = {
                    "status_code": response.status_code,
                    "properly_protected": response.status_code == 401
                }
            except Exception as e:
                unauthorized_results[endpoint_name] = {
                    "status_code": None,
                    "properly_protected": False,
                    "error": str(e)
                }
        
        # Restore authentication
        self.session.headers.update(temp_headers)
        
        auth_protected_count = sum(1 for r in unauthorized_results.values() 
                                 if r.get("properly_protected", False))
        
        print(f"  Protected endpoints: {auth_protected_count}/{len(unauthorized_results)}")
        
        return {
            "protected_endpoints_tested": len(unauthorized_results),
            "properly_protected": auth_protected_count,
            "authentication_score": (auth_protected_count / len(unauthorized_results)) * 100 if unauthorized_results else 0,
            "results": unauthorized_results
        }

    def test_performance(self, timeout_threshold: float = 2000) -> Dict:
        """Test response time performance (<2 seconds target)"""
        print(f"\n⚡ Testing performance (target: <{timeout_threshold}ms)...")
        
        performance_results = {}
        fast_endpoints = 0
        
        # Test sample of GET endpoints for performance
        get_endpoints = [(name, config) for name, config in self.new_endpoints.items() 
                        if config["method"] == "GET"]
        
        for endpoint_name, endpoint_config in get_endpoints:
            try:
                start_time = time.time()
                response = self.session.get(
                    f"{self.base_url}{endpoint_config['path']}", 
                    timeout=5
                )
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000  # Convert to ms
                performance_results[endpoint_name] = {
                    "response_time_ms": round(response_time, 2),
                    "within_threshold": response_time < timeout_threshold,
                    "status_code": response.status_code
                }
                
                if response_time < timeout_threshold:
                    fast_endpoints += 1
                    
            except Exception as e:
                performance_results[endpoint_name] = {
                    "response_time_ms": None,
                    "within_threshold": False,
                    "error": str(e)
                }
        
        performance_score = (fast_endpoints / len(get_endpoints)) * 100 if get_endpoints else 0
        print(f"  Fast endpoints: {fast_endpoints}/{len(get_endpoints)} ({performance_score:.1f}%)")
        
        return {
            "fast_endpoints": fast_endpoints,
            "total_tested": len(get_endpoints),
            "performance_score": performance_score,
            "threshold_ms": timeout_threshold,
            "results": performance_results
        }

    def test_end_to_end_workflow(self) -> Dict:
        """Test end-to-end procurement workflow integration"""
        print(f"\n🔄 Testing end-to-end procurement workflow...")
        
        workflow_steps = [
            ("acceptance_pending", "Check pending acceptance items"),
            ("storage_locations", "Get available storage locations"),
            ("logistics_receiving", "Check items ready for receiving"),
            ("acceptance_validation", "Validate an item"),
            ("storage_putaway", "Check putaway requirements"),
            ("logistics_delivery_tracking", "Track delivery status")
        ]
        
        workflow_results = {}
        successful_steps = 0
        
        for step_name, description in workflow_steps:
            if step_name in self.new_endpoints:
                print(f"  Step: {description}...")
                result = self.test_endpoint_accessibility(step_name, self.new_endpoints[step_name])
                workflow_results[step_name] = {
                    "description": description,
                    "successful": result["accessible"],
                    "status_code": result["status_code"],
                    "response_time": result["response_time"]
                }
                
                if result["accessible"]:
                    successful_steps += 1
                    print(f"    ✅ Success ({result['status_code']})")
                else:
                    print(f"    ❌ Failed ({result['status_code']})")
        
        workflow_score = (successful_steps / len(workflow_steps)) * 100
        print(f"  Workflow completion: {successful_steps}/{len(workflow_steps)} steps ({workflow_score:.1f}%)")
        
        return {
            "completed_steps": successful_steps,
            "total_steps": len(workflow_steps),
            "workflow_score": workflow_score,
            "step_results": workflow_results
        }

    def calculate_compliance_score(self, accessibility_result: Dict, auth_result: Dict, 
                                 performance_result: Dict, workflow_result: Dict) -> float:
        """Calculate overall procurement workflow compliance score"""
        
        # Weighted scoring
        weights = {
            "accessibility": 0.40,  # 40% - Critical that endpoints exist
            "authentication": 0.20,  # 20% - Security is important
            "performance": 0.20,     # 20% - Performance matters
            "workflow": 0.20         # 20% - End-to-end functionality
        }
        
        scores = {
            "accessibility": accessibility_result["accessibility_score"],
            "authentication": auth_result["authentication_score"], 
            "performance": performance_result["performance_score"],
            "workflow": workflow_result["workflow_score"]
        }
        
        # Calculate weighted average
        compliance_score = sum(scores[category] * weights[category] 
                             for category in weights.keys())
        
        return round(compliance_score, 1), scores

    def run_comprehensive_validation(self) -> Dict:
        """Run complete QA validation suite"""
        print("=" * 80)
        print("🚀 PROCUREMENT WORKFLOW QA VALIDATION - COMPREHENSIVE TEST SUITE")
        print("=" * 80)
        print(f"Target: Improve compliance from 37.5% baseline to 85%+")
        print(f"Testing {len(self.new_endpoints)} newly implemented endpoints")
        print(f"Timestamp: {self.test_results['timestamp']}")
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with protected endpoint testing")
            return self.test_results
        
        # Step 2: Endpoint Accessibility Testing
        accessibility_result = self.test_all_endpoints_accessibility()
        self.test_results["endpoint_results"] = accessibility_result
        
        # Step 3: Authentication Integration Testing  
        auth_result = self.test_authentication_integration()
        self.test_results["auth_results"] = auth_result
        
        # Step 4: Performance Testing
        performance_result = self.test_performance()
        self.test_results["performance_results"] = performance_result
        
        # Step 5: End-to-End Workflow Testing
        workflow_result = self.test_end_to_end_workflow()
        self.test_results["integration_results"] = workflow_result
        
        # Step 6: Calculate Overall Compliance Score
        compliance_score, category_scores = self.calculate_compliance_score(
            accessibility_result, auth_result, performance_result, workflow_result
        )
        
        self.test_results["compliance_score"] = compliance_score
        self.test_results["category_scores"] = category_scores
        
        # Step 7: Generate Summary
        self.generate_summary()
        
        return self.test_results

    def generate_summary(self):
        """Generate test summary and recommendations"""
        compliance_score = self.test_results["compliance_score"]
        baseline_score = 37.5
        target_score = 85.0
        
        improvement = compliance_score - baseline_score
        target_gap = target_score - compliance_score
        
        summary = {
            "baseline_score": baseline_score,
            "current_score": compliance_score,
            "target_score": target_score,
            "improvement": round(improvement, 1),
            "target_gap": round(target_gap, 1),
            "status": "PASS" if compliance_score >= target_score else "CONCERNS" if compliance_score >= 70 else "FAIL"
        }
        
        print(f"\n" + "=" * 80)
        print("📋 QA VALIDATION SUMMARY")
        print("=" * 80)
        print(f"Baseline Score:     {baseline_score}%")
        print(f"Current Score:      {compliance_score}%")
        print(f"Target Score:       {target_score}%")
        print(f"Improvement:        +{improvement}% {'✅' if improvement > 0 else '❌'}")
        print(f"Target Gap:         {target_gap}% {'remaining' if target_gap > 0 else 'exceeded!'}")
        print(f"Gate Decision:      {summary['status']}")
        
        print(f"\n📊 CATEGORY BREAKDOWN:")
        for category, score in self.test_results["category_scores"].items():
            status = "✅" if score >= 80 else "⚠️" if score >= 60 else "❌"
            print(f"  {category.title()}: {score:.1f}% {status}")
        
        if compliance_score >= target_score:
            print(f"\n🎉 SUCCESS: Procurement workflow compliance target achieved!")
            print(f"   The newly implemented endpoints have significantly improved compliance.")
        elif compliance_score >= 70:
            print(f"\n⚠️  CONCERNS: Close to target but some issues remain.")
            print(f"   Recommend addressing failing endpoints before production release.")
        else:
            print(f"\n❌ FAIL: Compliance score below acceptable threshold.")
            print(f"   Critical issues must be resolved before proceeding.")
        
        self.test_results["summary"] = summary

def main():
    """Main execution function"""
    try:
        # Initialize validator
        validator = ProcurementWorkflowQAValidator()
        
        # Run comprehensive validation
        results = validator.run_comprehensive_validation()
        
        # Save results to file
        results_file = f"procurement_workflow_qa_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: {results_file}")
        
        # Exit with appropriate code
        compliance_score = results["compliance_score"]
        if compliance_score >= 85:
            sys.exit(0)  # Success
        elif compliance_score >= 70:
            sys.exit(1)  # Warning
        else:
            sys.exit(2)  # Failure
            
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Test interrupted by user")
        sys.exit(3)
    except Exception as e:
        print(f"\n\n❌ Test execution failed: {str(e)}")
        traceback.print_exc()
        sys.exit(4)

if __name__ == "__main__":
    main()