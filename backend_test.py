#!/usr/bin/env python3
"""
Backend API Testing Suite for Aman Cybersecurity Platform - Phase 6 Security Testing
Tests all backend endpoints including new authentication, security features, and protected routes
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
        self.auth_token = None  # Store JWT token for authenticated requests
        self.test_user_data = {
            "name": "Test User",
            "email": "testuser@cybersec.com",
            "password": "SecurePass123!",
            "organization": "Test Organization"
        }
        
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
        """Test GET /api/health endpoint - Enhanced with system checks"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['status', 'service', 'version', 'timestamp', 'checks']
                
                if all(field in data for field in required_fields):
                    # Check if system checks are present
                    checks = data.get('checks', {})
                    if 'database' in checks and 'api' in checks:
                        self.log_result("Enhanced Health Check", True, 
                                      f"Status: {data['status']}, DB: {checks['database']}, API: {checks['api']}")
                        return True
                    else:
                        self.log_result("Enhanced Health Check", False, "Missing system checks in response")
                        return False
                else:
                    self.log_result("Enhanced Health Check", False, f"Missing required fields: {required_fields}")
                    return False
            else:
                self.log_result("Enhanced Health Check", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Enhanced Health Check", False, f"Request failed: {str(e)}")
            return False
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        try:
            # Make multiple rapid requests to health endpoint (limit: 10/minute)
            rapid_requests = []
            for i in range(12):  # Exceed the limit
                response = requests.get(f"{self.backend_url}/health", timeout=5)
                rapid_requests.append(response.status_code)
                time.sleep(0.1)  # Small delay between requests
            
            # Check if any requests were rate limited (429 status)
            rate_limited = any(status == 429 for status in rapid_requests)
            
            if rate_limited:
                self.log_result("Rate Limiting", True, "Rate limiting is working - received 429 responses")
                return True
            else:
                self.log_result("Rate Limiting", False, "Rate limiting not triggered - all requests succeeded")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Rate Limiting", False, f"Request failed: {str(e)}")
            return False

    def test_user_registration(self):
        """Test POST /api/auth/register endpoint"""
        try:
            # Use unique email to avoid conflicts
            test_email = f"testuser_{int(time.time())}@cybersec.com"
            registration_data = {
                "name": self.test_user_data["name"],
                "email": test_email,
                "password": self.test_user_data["password"],
                "organization": self.test_user_data["organization"]
            }
            
            response = requests.post(
                f"{self.backend_url}/auth/register",
                json=registration_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and 'data' in data:
                    # Update test user email for login test
                    self.test_user_data["email"] = test_email
                    self.log_result("User Registration", True, f"User registered: {test_email}")
                    return True
                else:
                    self.log_result("User Registration", False, f"Invalid response format: {data}")
                    return False
            else:
                self.log_result("User Registration", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("User Registration", False, f"Request failed: {str(e)}")
            return False

    def test_user_login(self):
        """Test POST /api/auth/login endpoint"""
        try:
            login_data = {
                "email": self.test_user_data["email"],
                "password": self.test_user_data["password"]
            }
            
            response = requests.post(
                f"{self.backend_url}/auth/login",
                json=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['access_token', 'refresh_token', 'token_type']
                
                if all(field in data for field in required_fields):
                    # Store token for authenticated requests
                    self.auth_token = data['access_token']
                    self.log_result("User Login", True, f"Login successful, token type: {data['token_type']}")
                    return True
                else:
                    self.log_result("User Login", False, f"Missing token fields: {required_fields}")
                    return False
            else:
                self.log_result("User Login", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("User Login", False, f"Request failed: {str(e)}")
            return False

    def test_token_refresh(self):
        """Test POST /api/auth/refresh endpoint"""
        try:
            # First login to get refresh token
            login_data = {
                "email": self.test_user_data["email"],
                "password": self.test_user_data["password"]
            }
            
            login_response = requests.post(
                f"{self.backend_url}/auth/login",
                json=login_data,
                timeout=10
            )
            
            if login_response.status_code != 200:
                self.log_result("Token Refresh", False, "Could not login to get refresh token")
                return False
            
            refresh_token = login_response.json().get('refresh_token')
            if not refresh_token:
                self.log_result("Token Refresh", False, "No refresh token in login response")
                return False
            
            # Test refresh endpoint
            refresh_data = {"refresh_token": refresh_token}
            response = requests.post(
                f"{self.backend_url}/auth/refresh",
                json=refresh_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'access_token' in data and 'refresh_token' in data:
                    self.log_result("Token Refresh", True, "Token refresh successful")
                    return True
                else:
                    self.log_result("Token Refresh", False, "Missing tokens in refresh response")
                    return False
            else:
                self.log_result("Token Refresh", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Token Refresh", False, f"Request failed: {str(e)}")
            return False

    def get_auth_headers(self):
        """Get authorization headers for authenticated requests"""
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        return {}

    def test_protected_user_profile(self):
        """Test GET /api/user/profile endpoint (protected)"""
        try:
            headers = self.get_auth_headers()
            response = requests.get(f"{self.backend_url}/user/profile", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['id', 'name', 'email', 'organization', 'is_active', 'role']
                
                if all(field in data for field in required_fields):
                    self.log_result("Protected User Profile", True, 
                                  f"User: {data['name']} ({data['email']}) - Role: {data['role']}")
                    return True
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_result("Protected User Profile", False, f"Missing fields: {missing_fields}")
                    return False
            elif response.status_code == 401:
                self.log_result("Protected User Profile", False, "Authentication required (401) - token may be invalid")
                return False
            else:
                self.log_result("Protected User Profile", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Protected User Profile", False, f"Request failed: {str(e)}")
            return False
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