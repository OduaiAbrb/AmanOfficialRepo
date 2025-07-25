#!/usr/bin/env python3
"""
Backend API Testing Suite for Aman Cybersecurity Platform
Tests all backend endpoints to ensure proper functionality
"""

import requests
import json
import sys
import os
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

class BackendTester:
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
    
    def test_health_endpoint(self):
        """Test GET /api/health endpoint"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'status' in data and data['status'] == 'healthy':
                    self.log_result("Health Check", True, f"Status: {data.get('status')}, Service: {data.get('service', 'N/A')}")
                    return True
                else:
                    self.log_result("Health Check", False, f"Invalid response format: {data}")
                    return False
            else:
                self.log_result("Health Check", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Health Check", False, f"Request failed: {str(e)}")
            return False
    
    def test_dashboard_stats(self):
        """Test GET /api/dashboard/stats endpoint"""
        try:
            response = requests.get(f"{self.backend_url}/dashboard/stats", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['phishing_caught', 'safe_emails', 'potential_phishing']
                
                if all(field in data for field in required_fields):
                    # Verify data types are integers
                    if all(isinstance(data[field], int) for field in required_fields):
                        self.log_result("Dashboard Stats", True, 
                                      f"Phishing: {data['phishing_caught']}, Safe: {data['safe_emails']}, Potential: {data['potential_phishing']}")
                        return True
                    else:
                        self.log_result("Dashboard Stats", False, "Invalid data types in response")
                        return False
                else:
                    self.log_result("Dashboard Stats", False, f"Missing required fields. Got: {list(data.keys())}")
                    return False
            else:
                self.log_result("Dashboard Stats", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Dashboard Stats", False, f"Request failed: {str(e)}")
            return False
    
    def test_recent_emails(self):
        """Test GET /api/dashboard/recent-emails endpoint"""
        try:
            response = requests.get(f"{self.backend_url}/dashboard/recent-emails", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'emails' in data and isinstance(data['emails'], list):
                    emails = data['emails']
                    if len(emails) > 0:
                        # Check first email structure
                        first_email = emails[0]
                        required_fields = ['id', 'subject', 'sender', 'time', 'status']
                        
                        if all(field in first_email for field in required_fields):
                            # Verify status values are valid
                            valid_statuses = ['safe', 'phishing', 'potential_phishing']
                            statuses = [email.get('status') for email in emails]
                            
                            if all(status in valid_statuses for status in statuses):
                                self.log_result("Recent Emails", True, 
                                              f"Retrieved {len(emails)} emails with valid structure")
                                return True
                            else:
                                invalid_statuses = [s for s in statuses if s not in valid_statuses]
                                self.log_result("Recent Emails", False, f"Invalid status values: {invalid_statuses}")
                                return False
                        else:
                            missing_fields = [f for f in required_fields if f not in first_email]
                            self.log_result("Recent Emails", False, f"Missing fields in email: {missing_fields}")
                            return False
                    else:
                        self.log_result("Recent Emails", True, "Empty email list returned (valid)")
                        return True
                else:
                    self.log_result("Recent Emails", False, "Response missing 'emails' array")
                    return False
            else:
                self.log_result("Recent Emails", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Recent Emails", False, f"Request failed: {str(e)}")
            return False
    
    def test_user_profile(self):
        """Test GET /api/user/profile endpoint"""
        try:
            response = requests.get(f"{self.backend_url}/user/profile", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['id', 'name', 'email', 'organization', 'joined', 'role']
                
                if all(field in data for field in required_fields):
                    # Basic validation of email format
                    email = data.get('email', '')
                    if '@' in email and '.' in email:
                        self.log_result("User Profile", True, 
                                      f"User: {data['name']} ({data['email']}) at {data['organization']}")
                        return True
                    else:
                        self.log_result("User Profile", False, f"Invalid email format: {email}")
                        return False
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_result("User Profile", False, f"Missing fields: {missing_fields}")
                    return False
            else:
                self.log_result("User Profile", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("User Profile", False, f"Request failed: {str(e)}")
            return False
    
    def test_mongodb_connection(self):
        """Test if MongoDB connection is working by checking backend logs"""
        try:
            # Check supervisor logs for MongoDB connection status
            import subprocess
            result = subprocess.run(['tail', '-n', '50', '/var/log/supervisor/backend.out.log'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                log_content = result.stdout
                if "✅ MongoDB connection successful" in log_content:
                    self.log_result("MongoDB Connection", True, "Connection confirmed in backend logs")
                    return True
                elif "❌ MongoDB connection failed" in log_content:
                    self.log_result("MongoDB Connection", False, "Connection failure found in backend logs")
                    return False
                else:
                    self.log_result("MongoDB Connection", True, "No explicit connection errors found")
                    return True
            else:
                self.log_result("MongoDB Connection", False, "Could not read backend logs")
                return False
                
        except Exception as e:
            self.log_result("MongoDB Connection", False, f"Error checking logs: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("=" * 60)
        print("🚀 AMAN CYBERSECURITY PLATFORM - BACKEND API TESTS")
        print("=" * 60)
        
        tests = [
            self.test_health_endpoint,
            self.test_dashboard_stats,
            self.test_recent_emails,
            self.test_user_profile,
            self.test_mongodb_connection
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
            print()  # Add spacing between tests
        
        print("=" * 60)
        print(f"📊 TEST SUMMARY: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! Backend is working correctly.")
            return True
        else:
            print(f"⚠️  {total - passed} test(s) failed. Check details above.")
            return False
    
    def save_results(self):
        """Save test results to file"""
        try:
            with open('/app/backend_test_results.json', 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'backend_url': self.backend_url,
                    'results': self.results,
                    'summary': {
                        'total_tests': len(self.results),
                        'passed': sum(1 for r in self.results if r['success']),
                        'failed': sum(1 for r in self.results if not r['success'])
                    }
                }, f, indent=2)
            print(f"📄 Test results saved to /app/backend_test_results.json")
        except Exception as e:
            print(f"❌ Error saving results: {e}")

if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_all_tests()
    tester.save_results()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)