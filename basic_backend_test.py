#!/usr/bin/env python3
"""
Basic Backend API Testing for Aman Cybersecurity Platform
Tests basic endpoints that should work without complex middleware
"""

import requests
import json
import sys
import os
import time
from datetime import datetime

# Get backend URL from frontend environment
def get_backend_url():
    """Get the backend URL from frontend .env file"""
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except Exception as e:
        print(f"❌ Error reading frontend .env: {e}")
        return None
    return None

class BasicBackendTester:
    def __init__(self):
        self.backend_url = get_backend_url()
        if not self.backend_url:
            print("❌ Could not determine backend URL from frontend/.env")
            sys.exit(1)
        
        # Ensure URL ends with /api for proper routing
        if not self.backend_url.endswith('/api'):
            self.backend_url = f"{self.backend_url}/api"
            
        print(f"🔗 Testing backend at: {self.backend_url}")
        self.results = []
        
    def log_result(self, test_name, success, details):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        
        self.results.append({
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })

    def test_basic_health_check(self):
        """Test basic connectivity to backend"""
        try:
            # Try a simple request to see if backend is responding
            response = requests.get(f"{self.backend_url.replace('/api', '')}/", timeout=10)
            
            if response.status_code in [200, 404]:  # 404 is fine, means server is responding
                self.log_result("Basic Connectivity", True, f"Backend server is responding (HTTP {response.status_code})")
                return True
            else:
                self.log_result("Basic Connectivity", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Basic Connectivity", False, f"Request failed: {str(e)}")
            return False

    def test_old_endpoints(self):
        """Test the old working endpoints that should still work"""
        old_endpoints = [
            ("/dashboard/stats", "Dashboard Stats"),
            ("/dashboard/recent-emails", "Recent Emails"),
            ("/user/profile", "User Profile")
        ]
        
        results = []
        for endpoint, name in old_endpoints:
            try:
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=10)
                
                if response.status_code == 200:
                    self.log_result(f"Old {name}", True, "Endpoint responding correctly")
                    results.append(True)
                else:
                    self.log_result(f"Old {name}", False, f"HTTP {response.status_code}")
                    results.append(False)
                    
            except requests.exceptions.RequestException as e:
                self.log_result(f"Old {name}", False, f"Request failed: {str(e)}")
                results.append(False)
        
        return all(results)

    def run_basic_tests(self):
        """Run basic connectivity tests"""
        print("=" * 60)
        print("🔍 BASIC BACKEND CONNECTIVITY TESTS")
        print("=" * 60)
        
        tests = [
            self.test_basic_health_check,
            self.test_old_endpoints
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
            print()
        
        print("=" * 60)
        print(f"📊 BASIC TEST SUMMARY: {passed}/{total} tests passed")
        
        return passed == total

if __name__ == "__main__":
    tester = BasicBackendTester()
    success = tester.run_basic_tests()
    
    if success:
        print("✅ Basic connectivity working - backend server is responding")
    else:
        print("❌ Basic connectivity issues detected")
    
    sys.exit(0 if success else 1)