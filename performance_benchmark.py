#!/usr/bin/env python3
"""
ERP System Performance Benchmarking
Tests performance under various load conditions to validate production readiness
"""

import requests
import json
import time
import threading
import statistics
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

@dataclass
class PerformanceMetric:
    endpoint: str
    method: str
    response_times: List[float] = field(default_factory=list)
    status_codes: List[int] = field(default_factory=list)
    success_rate: float = 0.0
    avg_response_time: float = 0.0
    min_response_time: float = 0.0
    max_response_time: float = 0.0
    p95_response_time: float = 0.0
    throughput: float = 0.0

class ERPPerformanceBenchmark:
    def __init__(self, base_url: str = "http://127.0.0.1:5000/api/v1"):
        self.base_url = base_url
        self.token = None
        self.metrics: Dict[str, PerformanceMetric] = {}
        
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def authenticate(self) -> bool:
        """Authenticate with system"""
        try:
            response = requests.post(f"{self.base_url}/auth/login", 
                                   json={"username": "admin", "password": "admin123"})
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                return True
        except:
            pass
        return False
    
    def make_timed_request(self, method: str, endpoint: str, **kwargs) -> tuple:
        """Make a timed HTTP request"""
        if self.token:
            headers = kwargs.get('headers', {})
            headers['Authorization'] = f'Bearer {self.token}'
            kwargs['headers'] = headers
        
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            response = requests.request(method, url, timeout=10, **kwargs)
            response_time = time.time() - start_time
            return response_time, response.status_code, True
        except Exception:
            response_time = time.time() - start_time
            return response_time, 0, False
    
    def record_metric(self, endpoint: str, method: str, response_time: float, status_code: int):
        """Record performance metric"""
        key = f"{method} {endpoint}"
        if key not in self.metrics:
            self.metrics[key] = PerformanceMetric(endpoint=endpoint, method=method)
        
        self.metrics[key].response_times.append(response_time)
        self.metrics[key].status_codes.append(status_code)
    
    def calculate_metrics(self):
        """Calculate summary statistics for all metrics"""
        for key, metric in self.metrics.items():
            if metric.response_times:
                successful_requests = sum(1 for code in metric.status_codes if 200 <= code < 300)
                total_requests = len(metric.status_codes)
                
                metric.success_rate = (successful_requests / total_requests) * 100 if total_requests > 0 else 0
                metric.avg_response_time = statistics.mean(metric.response_times)
                metric.min_response_time = min(metric.response_times)
                metric.max_response_time = max(metric.response_times)
                
                if len(metric.response_times) >= 2:
                    metric.p95_response_time = statistics.quantiles(metric.response_times, n=20)[18]  # 95th percentile
                else:
                    metric.p95_response_time = metric.max_response_time
                    
                # Calculate throughput (requests per second)
                total_time = sum(metric.response_times)
                metric.throughput = total_requests / total_time if total_time > 0 else 0
    
    def test_single_endpoint_performance(self, method: str, endpoint: str, iterations: int = 50):
        """Test single endpoint performance"""
        self.log(f"Testing {method} {endpoint} performance ({iterations} iterations)")
        
        for i in range(iterations):
            response_time, status_code, _ = self.make_timed_request(method, endpoint)
            self.record_metric(endpoint, method, response_time, status_code)
            
            # Brief pause to avoid overwhelming server
            time.sleep(0.01)
    
    def test_concurrent_load(self, method: str, endpoint: str, concurrent_users: int = 10, requests_per_user: int = 5):
        """Test endpoint under concurrent load"""
        self.log(f"Testing {method} {endpoint} with {concurrent_users} concurrent users ({requests_per_user} req/user)")
        
        def make_requests(user_id: int):
            user_metrics = []
            for i in range(requests_per_user):
                response_time, status_code, _ = self.make_timed_request(method, endpoint)
                user_metrics.append((response_time, status_code))
                time.sleep(0.01)  # Small delay between requests
            return user_metrics
        
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(make_requests, i) for i in range(concurrent_users)]
            
            for future in as_completed(futures):
                user_metrics = future.result()
                for response_time, status_code in user_metrics:
                    self.record_metric(endpoint, method, response_time, status_code)
        
        total_time = time.time() - start_time
        total_requests = concurrent_users * requests_per_user
        self.log(f"Completed {total_requests} requests in {total_time:.2f}s (avg: {total_requests/total_time:.1f} req/s)")
    
    def test_database_performance(self):
        """Test database-intensive operations"""
        self.log("Testing Database Performance", "TEST")
        
        # Test read operations
        read_endpoints = [
            ('GET', '/requisitions'),
            ('GET', '/suppliers'),
            ('GET', '/inventory'),
            ('GET', '/po'),
            ('GET', '/users')
        ]
        
        for method, endpoint in read_endpoints:
            self.test_single_endpoint_performance(method, endpoint, 20)
    
    def test_api_response_times(self):
        """Test API response times for critical endpoints"""
        self.log("Testing API Response Times", "TEST")
        
        critical_endpoints = [
            ('POST', '/auth/login'),
            ('GET', '/requisitions'),
            ('GET', '/po/build-candidates'),
            ('GET', '/inventory'),
            ('GET', '/receiving'),
            ('GET', '/leadtime'),
            ('GET', '/ap/billing/candidates')
        ]
        
        for method, endpoint in critical_endpoints:
            self.test_single_endpoint_performance(method, endpoint, 30)
    
    def test_concurrent_users(self):
        """Test system under concurrent user load"""
        self.log("Testing Concurrent User Load", "TEST")
        
        # Test different user loads
        user_loads = [5, 10, 20]
        test_endpoint = '/requisitions'  # Common read operation
        
        for users in user_loads:
            self.log(f"Testing with {users} concurrent users")
            self.test_concurrent_load('GET', test_endpoint, users, 3)
    
    def test_memory_and_cpu_simulation(self):
        """Simulate memory and CPU intensive operations"""
        self.log("Testing Memory/CPU Intensive Operations", "TEST")
        
        # Test operations that might be resource intensive
        intensive_endpoints = [
            ('GET', '/po/build-candidates'),  # Potentially complex grouping
            ('GET', '/inventory?name=test'),  # Search operation
            ('GET', '/leadtime?visible_only=true'),  # Filtering operation
        ]
        
        for method, endpoint in intensive_endpoints:
            self.test_concurrent_load(method, endpoint, 5, 10)
    
    def run_all_performance_tests(self):
        """Execute complete performance test suite"""
        self.log("🚀 Starting ERP Performance Benchmarking", "INFO")
        self.log("=" * 70)
        
        if not self.authenticate():
            self.log("Authentication failed, using mock token", "WARN")
            self.token = "mock-token-for-testing"
        
        start_time = time.time()
        
        # Run all performance tests
        test_suites = [
            self.test_api_response_times,
            self.test_database_performance,
            self.test_concurrent_users,
            self.test_memory_and_cpu_simulation
        ]
        
        for test_suite in test_suites:
            try:
                test_suite()
            except Exception as e:
                self.log(f"Error in {test_suite.__name__}: {str(e)}", "ERROR")
        
        total_time = time.time() - start_time
        self.calculate_metrics()
        
        self.log(f"All performance tests completed in {total_time:.2f} seconds", "INFO")
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        self.calculate_metrics()
        
        # Overall system performance assessment
        all_response_times = []
        all_success_rates = []
        
        for metric in self.metrics.values():
            all_response_times.extend(metric.response_times)
            all_success_rates.append(metric.success_rate)
        
        overall_avg_response_time = statistics.mean(all_response_times) if all_response_times else 0
        overall_success_rate = statistics.mean(all_success_rates) if all_success_rates else 0
        
        # Performance thresholds (from architect requirements)
        target_response_time = 0.2  # 200ms target
        endpoints_meeting_target = sum(1 for m in self.metrics.values() 
                                     if m.avg_response_time <= target_response_time)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "performance_summary": {
                "overall_avg_response_time_ms": round(overall_avg_response_time * 1000, 2),
                "overall_success_rate": round(overall_success_rate, 2),
                "total_requests_made": sum(len(m.response_times) for m in self.metrics.values()),
                "endpoints_tested": len(self.metrics),
                "endpoints_meeting_200ms_target": endpoints_meeting_target,
                "target_compliance_rate": round((endpoints_meeting_target / len(self.metrics)) * 100, 2) if self.metrics else 0
            },
            "detailed_metrics": {
                endpoint: {
                    "endpoint": metric.endpoint,
                    "method": metric.method,
                    "avg_response_time_ms": round(metric.avg_response_time * 1000, 2),
                    "min_response_time_ms": round(metric.min_response_time * 1000, 2),
                    "max_response_time_ms": round(metric.max_response_time * 1000, 2),
                    "p95_response_time_ms": round(metric.p95_response_time * 1000, 2),
                    "success_rate": round(metric.success_rate, 2),
                    "throughput_req_per_sec": round(metric.throughput, 2),
                    "total_requests": len(metric.response_times),
                    "meets_200ms_target": metric.avg_response_time <= target_response_time
                }
                for endpoint, metric in self.metrics.items()
            },
            "performance_assessment": {
                "meets_architect_requirements": endpoints_meeting_target >= len(self.metrics) * 0.8,  # 80% compliance
                "suitable_for_production": overall_avg_response_time <= target_response_time and overall_success_rate >= 95,
                "scalability_concerns": any(m.avg_response_time > 1.0 for m in self.metrics.values()),  # Any endpoint over 1s
                "reliability_score": overall_success_rate,
                "performance_grade": self._calculate_performance_grade(overall_avg_response_time, overall_success_rate)
            },
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    def _calculate_performance_grade(self, avg_time: float, success_rate: float) -> str:
        """Calculate performance grade A-F"""
        if avg_time <= 0.1 and success_rate >= 99:
            return "A"
        elif avg_time <= 0.2 and success_rate >= 95:
            return "B"
        elif avg_time <= 0.5 and success_rate >= 90:
            return "C"
        elif avg_time <= 1.0 and success_rate >= 80:
            return "D"
        else:
            return "F"
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []
        
        # Check for slow endpoints
        slow_endpoints = [m for m in self.metrics.values() if m.avg_response_time > 0.5]
        if slow_endpoints:
            recommendations.append(f"Optimize {len(slow_endpoints)} slow endpoints (>500ms response time)")
        
        # Check for low success rates
        unreliable_endpoints = [m for m in self.metrics.values() if m.success_rate < 95]
        if unreliable_endpoints:
            recommendations.append(f"Improve reliability of {len(unreliable_endpoints)} endpoints (<95% success rate)")
        
        # Check overall performance
        if any(m.avg_response_time > 0.2 for m in self.metrics.values()):
            recommendations.append("Consider database query optimization and indexing")
            recommendations.append("Implement Redis caching for frequently accessed data")
        
        if any(m.throughput < 10 for m in self.metrics.values()):
            recommendations.append("Consider connection pooling and async processing")
        
        if not recommendations:
            recommendations.append("Performance meets production standards")
        
        return recommendations

def main():
    print("🚀 ERP System Performance Benchmarking")
    print("=" * 70)
    
    benchmark = ERPPerformanceBenchmark()
    
    try:
        benchmark.run_all_performance_tests()
        
        # Generate and save report
        report = benchmark.generate_performance_report()
        
        with open('performance_benchmark_results.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        summary = report['performance_summary']
        assessment = report['performance_assessment']
        
        print("\n" + "=" * 70)
        print("📊 PERFORMANCE BENCHMARK RESULTS")
        print("=" * 70)
        print(f"Overall Avg Response Time: {summary['overall_avg_response_time_ms']:.1f}ms")
        print(f"Overall Success Rate: {summary['overall_success_rate']:.1f}%")
        print(f"Total Requests Made: {summary['total_requests_made']}")
        print(f"Endpoints Tested: {summary['endpoints_tested']}")
        print(f"Endpoints Meeting 200ms Target: {summary['endpoints_meeting_200ms_target']}/{summary['endpoints_tested']}")
        print(f"Target Compliance Rate: {summary['target_compliance_rate']:.1f}%")
        
        print(f"\n🎯 PERFORMANCE ASSESSMENT:")
        print(f"  Performance Grade: {assessment['performance_grade']}")
        print(f"  Meets Architect Requirements: {'✅' if assessment['meets_architect_requirements'] else '❌'}")
        print(f"  Suitable for Production: {'✅' if assessment['suitable_for_production'] else '❌'}")
        print(f"  Scalability Concerns: {'⚠️' if assessment['scalability_concerns'] else '✅'}")
        print(f"  Reliability Score: {assessment['reliability_score']:.1f}%")
        
        if report['recommendations']:
            print(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"  {i}. {rec}")
        
        print(f"\n📄 Detailed results saved to: performance_benchmark_results.json")
        
        # Show top 5 slowest endpoints
        slow_endpoints = sorted(report['detailed_metrics'].items(), 
                              key=lambda x: x[1]['avg_response_time_ms'], reverse=True)[:5]
        if slow_endpoints:
            print(f"\n🐌 SLOWEST ENDPOINTS:")
            for endpoint, metrics in slow_endpoints:
                print(f"  {metrics['method']} {metrics['endpoint']}: {metrics['avg_response_time_ms']}ms")
        
        return 0 if assessment['suitable_for_production'] else 1
        
    except Exception as e:
        print(f"\n💥 Critical error during performance benchmarking: {str(e)}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())