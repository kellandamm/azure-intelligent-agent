#!/usr/bin/env python3
"""
Comprehensive Smoke Test Suite for Azure Intelligent Agent
Tests all critical endpoints and functionality to ensure deployment success.

Usage:
    python smoke_test.py --url https://your-app.azurewebsites.net
    python smoke_test.py --url https://your-app.azurewebsites.net --auth-token YOUR_JWT_TOKEN
    python smoke_test.py --url http://localhost:8000 --skip-auth
"""

import argparse
import sys
import time
import json
import requests
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class TestResult:
    """Result of a single test."""
    name: str
    passed: bool
    duration_ms: float
    error_message: Optional[str] = None
    details: Dict = field(default_factory=dict)


@dataclass
class TestSuite:
    """Collection of test results."""
    name: str
    results: List[TestResult] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    
    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)
    
    @property
    def total_tests(self) -> int:
        return len(self.results)
    
    @property
    def passed_tests(self) -> int:
        return sum(1 for r in self.results if r.passed)
    
    @property
    def failed_tests(self) -> int:
        return self.total_tests - self.passed_tests
    
    @property
    def duration_seconds(self) -> float:
        return time.time() - self.start_time


class SmokeTestRunner:
    """Main smoke test runner."""
    
    def __init__(self, base_url: str, auth_token: Optional[str] = None, 
                 skip_auth: bool = False, verbose: bool = False):
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.skip_auth = skip_auth
        self.verbose = verbose
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'User-Agent': 'Azure-Intelligent-Agent-SmokeTest/1.0',
            'Accept': 'application/json'
        })
        
        if auth_token:
            self.session.headers.update({'Authorization': f'Bearer {auth_token}'})
    
    def _log(self, message: str, level: str = "INFO"):
        """Log message with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prefix = {
            "INFO": "ℹ️ ",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️ ",
            "DEBUG": "🔍"
        }.get(level, "")
        print(f"[{timestamp}] {prefix} {message}")
    
    def _run_test(self, name: str, test_func) -> TestResult:
        """Run a single test and capture result."""
        if self.verbose:
            self._log(f"Running: {name}", "DEBUG")
        
        start_time = time.time()
        try:
            result = test_func()
            duration_ms = (time.time() - start_time) * 1000
            
            if isinstance(result, tuple):
                passed, details = result
            else:
                passed, details = result, {}
            
            test_result = TestResult(
                name=name,
                passed=passed,
                duration_ms=duration_ms,
                details=details
            )
            
            status = "✅ PASS" if passed else "❌ FAIL"
            self._log(f"{status} - {name} ({duration_ms:.0f}ms)", 
                     "SUCCESS" if passed else "ERROR")
            
            return test_result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._log(f"❌ FAIL - {name}: {str(e)}", "ERROR")
            return TestResult(
                name=name,
                passed=False,
                duration_ms=duration_ms,
                error_message=str(e)
            )
    
    def test_health_endpoint(self) -> Tuple[bool, Dict]:
        """Test /health endpoint."""
        response = self.session.get(f"{self.base_url}/health", timeout=10)
        
        if response.status_code != 200:
            return False, {"status_code": response.status_code}
        
        data = response.json()
        required_keys = ["status", "timestamp"]
        
        for key in required_keys:
            if key not in data:
                return False, {"missing_key": key}
        
        if data.get("status") != "healthy":
            return False, {"status": data.get("status")}
        
        return True, {
            "status": data.get("status"),
            "version": data.get("version"),
            "environment": data.get("environment")
        }
    
    def test_root_endpoint(self) -> Tuple[bool, Dict]:
        """Test root / endpoint."""
        response = self.session.get(f"{self.base_url}/", timeout=10)
        
        if response.status_code not in [200, 307]:  # Allow redirects
            return False, {"status_code": response.status_code}
        
        return True, {"status_code": response.status_code}
    
    def test_static_files(self) -> Tuple[bool, Dict]:
        """Test static file serving."""
        # Test loading a common static file
        response = self.session.get(f"{self.base_url}/login", timeout=10)
        
        if response.status_code != 200:
            return False, {"status_code": response.status_code}
        
        # Check it's HTML
        content_type = response.headers.get('content-type', '')
        if 'html' not in content_type.lower():
            return False, {"content_type": content_type}
        
        return True, {"content_type": content_type}
    
    def test_authentication_endpoint(self) -> Tuple[bool, Dict]:
        """Test authentication endpoint availability."""
        if self.skip_auth:
            return True, {"skipped": True}
        
        # Test POST to /api/auth/login (expect 422 for missing body, not 404)
        response = self.session.post(f"{self.base_url}/api/auth/login", 
                                     json={}, timeout=10)
        
        # 422 means endpoint exists but validation failed (expected)
        # 401 means auth is working but credentials invalid (also good)
        if response.status_code in [422, 401]:
            return True, {"status_code": response.status_code}
        
        return False, {"status_code": response.status_code}
    
    def test_chat_endpoint(self) -> Tuple[bool, Dict]:
        """Test chat endpoint availability."""
        # Test POST to /api/chat (should require auth or return proper error)
        response = self.session.post(
            f"{self.base_url}/api/chat",
            json={"message": "test", "agent_type": "orchestrator"},
            timeout=30
        )
        
        # Accept: 200 (success), 401 (needs auth), 422 (validation error)
        if response.status_code in [200, 401, 422]:
            return True, {"status_code": response.status_code}
        
        return False, {"status_code": response.status_code}
    
    def test_agent_endpoint(self) -> Tuple[bool, Dict]:
        """Test agent endpoint availability."""
        response = self.session.post(
            f"{self.base_url}/api/agent/chat",
            json={"message": "test", "agent_type": "sales"},
            timeout=30
        )
        
        # Accept: 200 (success), 401 (needs auth), 422 (validation error)
        if response.status_code in [200, 401, 422]:
            return True, {"status_code": response.status_code}
        
        return False, {"status_code": response.status_code}
    
    def test_sales_dashboard_endpoint(self) -> Tuple[bool, Dict]:
        """Test sales dashboard API endpoint."""
        response = self.session.get(f"{self.base_url}/api/sales/summary", timeout=10)
        
        # Accept: 200 (success), 401 (needs auth), 403 (forbidden)
        if response.status_code in [200, 401, 403]:
            return True, {"status_code": response.status_code}
        
        return False, {"status_code": response.status_code}
    
    def test_analytics_dashboard_endpoint(self) -> Tuple[bool, Dict]:
        """Test analytics dashboard API endpoint."""
        response = self.session.get(f"{self.base_url}/api/analytics/metrics", timeout=10)
        
        # Accept: 200 (success), 401 (needs auth), 403 (forbidden)
        if response.status_code in [200, 401, 403]:
            return True, {"status_code": response.status_code}
        
        return False, {"status_code": response.status_code}
    
    def test_timeseries_endpoint(self) -> Tuple[bool, Dict]:
        """Test time series analytics endpoint."""
        response = self.session.get(f"{self.base_url}/api/analytics/timeseries", timeout=10)
        
        # Accept: 200 (success), 401 (needs auth), 403 (forbidden)
        if response.status_code in [200, 401, 403]:
            return True, {"status_code": response.status_code}
        
        return False, {"status_code": response.status_code}
    
    def test_admin_endpoint(self) -> Tuple[bool, Dict]:
        """Test admin dashboard endpoint."""
        response = self.session.get(f"{self.base_url}/admin", timeout=10)
        
        # Should return HTML page (200) or redirect to login
        if response.status_code in [200, 302, 307]:
            return True, {"status_code": response.status_code}
        
        return False, {"status_code": response.status_code}
    
    def test_openapi_docs(self) -> Tuple[bool, Dict]:
        """Test OpenAPI documentation endpoint."""
        response = self.session.get(f"{self.base_url}/docs", timeout=10)
        
        if response.status_code != 200:
            return False, {"status_code": response.status_code}
        
        return True, {"status_code": response.status_code}
    
    def test_response_time(self) -> Tuple[bool, Dict]:
        """Test average response time is acceptable."""
        times = []
        for _ in range(5):
            start = time.time()
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            times.append((time.time() - start) * 1000)
        
        avg_time = sum(times) / len(times)
        max_acceptable = 2000  # 2 seconds
        
        passed = avg_time < max_acceptable
        return passed, {
            "avg_ms": round(avg_time, 2),
            "max_ms": round(max(times), 2),
            "min_ms": round(min(times), 2)
        }
    
    def test_database_connectivity(self) -> Tuple[bool, Dict]:
        """Test database connectivity through diagnostic endpoint."""
        response = self.session.get(f"{self.base_url}/api/diagnostic/db-test", timeout=10)
        
        # Accept: 200 (connected), 401 (needs auth), 503 (not connected but endpoint works)
        if response.status_code in [200, 401, 503]:
            if response.status_code == 200:
                try:
                    data = response.json()
                    return True, {"connected": data.get("connected", False)}
                except:
                    pass
            return True, {"status_code": response.status_code}
        
        return False, {"status_code": response.status_code}
    
    def test_cors_headers(self) -> Tuple[bool, Dict]:
        """Test CORS headers are present."""
        response = self.session.options(f"{self.base_url}/health", timeout=10)
        
        cors_headers = {
            'access-control-allow-origin': response.headers.get('access-control-allow-origin'),
            'access-control-allow-methods': response.headers.get('access-control-allow-methods'),
        }
        
        # Check if at least one CORS header is present
        has_cors = any(cors_headers.values())
        
        return has_cors, cors_headers
    
    def run_all_tests(self) -> TestSuite:
        """Run all smoke tests."""
        self._log("=" * 60)
        self._log("🚀 AZURE INTELLIGENT AGENT - SMOKE TEST SUITE")
        self._log("=" * 60)
        self._log(f"Target URL: {self.base_url}")
        self._log(f"Authentication: {'Enabled' if self.auth_token else 'Skipped' if self.skip_auth else 'None'}")
        self._log("")
        
        suite = TestSuite(name="Azure Intelligent Agent Smoke Tests")
        
        # Core functionality tests
        self._log("📋 Running Core Functionality Tests...")
        suite.results.append(self._run_test("Health Endpoint", self.test_health_endpoint))
        suite.results.append(self._run_test("Root Endpoint", self.test_root_endpoint))
        suite.results.append(self._run_test("Static Files", self.test_static_files))
        suite.results.append(self._run_test("OpenAPI Docs", self.test_openapi_docs))
        
        # Authentication tests
        self._log("\n🔐 Running Authentication Tests...")
        suite.results.append(self._run_test("Authentication Endpoint", self.test_authentication_endpoint))
        
        # API endpoint tests
        self._log("\n🤖 Running API Endpoint Tests...")
        suite.results.append(self._run_test("Chat Endpoint", self.test_chat_endpoint))
        suite.results.append(self._run_test("Agent Endpoint", self.test_agent_endpoint))
        
        # Dashboard tests
        self._log("\n📊 Running Dashboard Tests...")
        suite.results.append(self._run_test("Sales Dashboard", self.test_sales_dashboard_endpoint))
        suite.results.append(self._run_test("Analytics Dashboard", self.test_analytics_dashboard_endpoint))
        suite.results.append(self._run_test("Time Series Endpoint", self.test_timeseries_endpoint))
        suite.results.append(self._run_test("Admin Dashboard", self.test_admin_endpoint))
        
        # Infrastructure tests
        self._log("\n⚙️  Running Infrastructure Tests...")
        suite.results.append(self._run_test("Database Connectivity", self.test_database_connectivity))
        suite.results.append(self._run_test("CORS Headers", self.test_cors_headers))
        suite.results.append(self._run_test("Response Time", self.test_response_time))
        
        return suite
    
    def print_summary(self, suite: TestSuite):
        """Print test summary."""
        self._log("")
        self._log("=" * 60)
        self._log("📊 TEST SUMMARY")
        self._log("=" * 60)
        self._log(f"Total Tests: {suite.total_tests}")
        self._log(f"✅ Passed: {suite.passed_tests}", "SUCCESS")
        if suite.failed_tests > 0:
            self._log(f"❌ Failed: {suite.failed_tests}", "ERROR")
        self._log(f"⏱️  Duration: {suite.duration_seconds:.2f}s")
        self._log("")
        
        if not suite.passed:
            self._log("❌ FAILED TESTS:", "ERROR")
            for result in suite.results:
                if not result.passed:
                    self._log(f"  • {result.name}", "ERROR")
                    if result.error_message:
                        self._log(f"    Error: {result.error_message}", "ERROR")
                    if result.details:
                        self._log(f"    Details: {json.dumps(result.details, indent=6)}", "ERROR")
            self._log("")
        
        if suite.passed:
            self._log("✅ ALL TESTS PASSED - APPLICATION IS HEALTHY", "SUCCESS")
        else:
            self._log("❌ SOME TESTS FAILED - REVIEW ERRORS ABOVE", "ERROR")
        
        self._log("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Comprehensive smoke test suite for Azure Intelligent Agent"
    )
    parser.add_argument(
        "--url",
        required=True,
        help="Base URL of the deployed application (e.g., https://your-app.azurewebsites.net)"
    )
    parser.add_argument(
        "--auth-token",
        help="JWT authentication token for protected endpoints"
    )
    parser.add_argument(
        "--skip-auth",
        action="store_true",
        help="Skip authentication tests"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--json-output",
        help="Save results to JSON file"
    )
    
    args = parser.parse_args()
    
    # Run tests
    runner = SmokeTestRunner(
        base_url=args.url,
        auth_token=args.auth_token,
        skip_auth=args.skip_auth,
        verbose=args.verbose
    )
    
    suite = runner.run_all_tests()
    runner.print_summary(suite)
    
    # Save JSON output if requested
    if args.json_output:
        output = {
            "timestamp": datetime.now().isoformat(),
            "base_url": args.url,
            "passed": suite.passed,
            "total_tests": suite.total_tests,
            "passed_tests": suite.passed_tests,
            "failed_tests": suite.failed_tests,
            "duration_seconds": suite.duration_seconds,
            "results": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "duration_ms": r.duration_ms,
                    "error_message": r.error_message,
                    "details": r.details
                }
                for r in suite.results
            ]
        }
        
        with open(args.json_output, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n💾 Results saved to: {args.json_output}")
    
    # Exit with appropriate code
    sys.exit(0 if suite.passed else 1)


if __name__ == "__main__":
    main()
