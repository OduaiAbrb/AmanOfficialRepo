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
        self.refresh_token = None  # Store refresh token
        self.test_user_data = {
            "name": "Security Test User",
            "email": f"sectest_{int(time.time())}@cybersec.com",
            "password": "SecurePass123!",
            "organization": "Cybersecurity Test Org"
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
    
    def get_auth_headers(self):
        """Get authorization headers for authenticated requests"""
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        return {}

    def test_enhanced_health_check(self):
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
            response = requests.post(
                f"{self.backend_url}/auth/register",
                json=self.test_user_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and 'data' in data:
                    self.log_result("User Registration", True, f"User registered: {self.test_user_data['email']}")
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
                    # Store tokens for authenticated requests
                    self.auth_token = data['access_token']
                    self.refresh_token = data['refresh_token']
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
            if not self.refresh_token:
                self.log_result("Token Refresh", False, "No refresh token available")
                return False
            
            refresh_data = {"refresh_token": self.refresh_token}
            response = requests.post(
                f"{self.backend_url}/auth/refresh",
                json=refresh_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'access_token' in data and 'refresh_token' in data:
                    # Update tokens
                    self.auth_token = data['access_token']
                    self.refresh_token = data['refresh_token']
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

    def test_protected_dashboard_stats(self):
        """Test GET /api/dashboard/stats endpoint (protected)"""
        try:
            headers = self.get_auth_headers()
            response = requests.get(f"{self.backend_url}/dashboard/stats", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['phishing_caught', 'safe_emails', 'potential_phishing', 'total_scans', 'accuracy_rate']
                
                if all(field in data for field in required_fields):
                    # Verify data types
                    numeric_fields = ['phishing_caught', 'safe_emails', 'potential_phishing', 'total_scans']
                    if all(isinstance(data[field], int) for field in numeric_fields):
                        self.log_result("Protected Dashboard Stats", True, 
                                      f"Stats - Phishing: {data['phishing_caught']}, Safe: {data['safe_emails']}, Accuracy: {data['accuracy_rate']}%")
                        return True
                    else:
                        self.log_result("Protected Dashboard Stats", False, "Invalid data types in response")
                        return False
                else:
                    self.log_result("Protected Dashboard Stats", False, f"Missing required fields: {required_fields}")
                    return False
            elif response.status_code == 401:
                self.log_result("Protected Dashboard Stats", False, "Authentication required (401)")
                return False
            else:
                self.log_result("Protected Dashboard Stats", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Protected Dashboard Stats", False, f"Request failed: {str(e)}")
            return False

    def test_protected_recent_emails(self):
        """Test GET /api/dashboard/recent-emails endpoint (protected)"""
        try:
            headers = self.get_auth_headers()
            response = requests.get(f"{self.backend_url}/dashboard/recent-emails", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'emails' in data and isinstance(data['emails'], list):
                    emails = data['emails']
                    if len(emails) > 0:
                        # Check first email structure
                        first_email = emails[0]
                        required_fields = ['id', 'subject', 'sender', 'time', 'status', 'risk_score']
                        
                        if all(field in first_email for field in required_fields):
                            # Verify status values are valid
                            valid_statuses = ['safe', 'phishing', 'potential_phishing']
                            statuses = [email.get('status') for email in emails]
                            
                            if all(status in valid_statuses for status in statuses):
                                self.log_result("Protected Recent Emails", True, 
                                              f"Retrieved {len(emails)} emails with valid structure")
                                return True
                            else:
                                invalid_statuses = [s for s in statuses if s not in valid_statuses]
                                self.log_result("Protected Recent Emails", False, f"Invalid status values: {invalid_statuses}")
                                return False
                        else:
                            missing_fields = [f for f in required_fields if f not in first_email]
                            self.log_result("Protected Recent Emails", False, f"Missing fields in email: {missing_fields}")
                            return False
                    else:
                        self.log_result("Protected Recent Emails", True, "Empty email list returned (valid)")
                        return True
                else:
                    self.log_result("Protected Recent Emails", False, "Response missing 'emails' array")
                    return False
            elif response.status_code == 401:
                self.log_result("Protected Recent Emails", False, "Authentication required (401)")
                return False
            else:
                self.log_result("Protected Recent Emails", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Protected Recent Emails", False, f"Request failed: {str(e)}")
            return False

    def test_email_scanning(self):
        """Test POST /api/scan/email endpoint (protected)"""
        try:
            headers = self.get_auth_headers()
            scan_data = {
                "email_subject": "Urgent: Verify Your Account Now!",
                "sender": "noreply@suspicious-bank.com",
                "recipient": self.test_user_data["email"],
                "email_body": "Click here to verify your account immediately or it will be suspended!"
            }
            
            response = requests.post(
                f"{self.backend_url}/scan/email",
                json=scan_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['id', 'status', 'risk_score', 'explanation', 'recommendations']
                
                if all(field in data for field in required_fields):
                    valid_statuses = ['safe', 'phishing', 'potential_phishing']
                    if data['status'] in valid_statuses:
                        self.log_result("Email Scanning", True, 
                                      f"Scan result: {data['status']} (risk: {data['risk_score']})")
                        return True
                    else:
                        self.log_result("Email Scanning", False, f"Invalid status: {data['status']}")
                        return False
                else:
                    self.log_result("Email Scanning", False, f"Missing required fields: {required_fields}")
                    return False
            elif response.status_code == 401:
                self.log_result("Email Scanning", False, "Authentication required (401)")
                return False
            else:
                self.log_result("Email Scanning", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Email Scanning", False, f"Request failed: {str(e)}")
            return False

    def test_link_scanning(self):
        """Test POST /api/scan/link endpoint (protected)"""
        try:
            headers = self.get_auth_headers()
            link_data = {
                "url": "https://bit.ly/suspicious-link"
            }
            
            response = requests.post(
                f"{self.backend_url}/scan/link",
                json=link_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['url', 'status', 'risk_score', 'explanation', 'is_shortened']
                
                if all(field in data for field in required_fields):
                    valid_statuses = ['safe', 'phishing', 'potential_phishing']
                    if data['status'] in valid_statuses:
                        self.log_result("Link Scanning", True, 
                                      f"Link scan: {data['status']} (risk: {data['risk_score']}, shortened: {data['is_shortened']})")
                        return True
                    else:
                        self.log_result("Link Scanning", False, f"Invalid status: {data['status']}")
                        return False
                else:
                    self.log_result("Link Scanning", False, f"Missing required fields: {required_fields}")
                    return False
            elif response.status_code == 401:
                self.log_result("Link Scanning", False, "Authentication required (401)")
                return False
            else:
                self.log_result("Link Scanning", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Link Scanning", False, f"Request failed: {str(e)}")
            return False

    def test_user_settings(self):
        """Test GET/PUT /api/user/settings endpoints (protected)"""
        try:
            headers = self.get_auth_headers()
            
            # Test GET settings
            response = requests.get(f"{self.backend_url}/user/settings", headers=headers, timeout=10)
            
            if response.status_code == 200:
                settings_data = response.json()
                
                # Test PUT settings
                updated_settings = {
                    "email_notifications": True,
                    "security_alerts": True,
                    "scan_frequency": "real_time",
                    "language": "en",
                    "theme": "light"
                }
                
                put_response = requests.put(
                    f"{self.backend_url}/user/settings",
                    json=updated_settings,
                    headers=headers,
                    timeout=10
                )
                
                if put_response.status_code == 200:
                    self.log_result("User Settings", True, "GET and PUT settings both working")
                    return True
                else:
                    self.log_result("User Settings", False, f"PUT failed: HTTP {put_response.status_code}")
                    return False
            elif response.status_code == 401:
                self.log_result("User Settings", False, "Authentication required (401)")
                return False
            else:
                self.log_result("User Settings", False, f"GET failed: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("User Settings", False, f"Request failed: {str(e)}")
            return False

    def test_authentication_required(self):
        """Test that protected endpoints require authentication"""
        try:
            # Test accessing protected endpoint without token
            response = requests.get(f"{self.backend_url}/user/profile", timeout=10)
            
            if response.status_code == 401:
                self.log_result("Authentication Required", True, "Protected endpoints properly require authentication")
                return True
            else:
                self.log_result("Authentication Required", False, f"Expected 401, got {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Authentication Required", False, f"Request failed: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all Phase 6 security tests"""
        print("=" * 80)
        print("🚀 AMAN CYBERSECURITY PLATFORM - PHASE 6 SECURITY TESTING")
        print("=" * 80)
        
        # Test sequence for Phase 6 security features
        tests = [
            ("Enhanced Health Check", self.test_enhanced_health_check),
            ("Rate Limiting", self.test_rate_limiting),
            ("User Registration", self.test_user_registration),
            ("User Login", self.test_user_login),
            ("Token Refresh", self.test_token_refresh),
            ("Authentication Required", self.test_authentication_required),
            ("Protected User Profile", self.test_protected_user_profile),
            ("Protected Dashboard Stats", self.test_protected_dashboard_stats),
            ("Protected Recent Emails", self.test_protected_recent_emails),
            ("Email Scanning", self.test_email_scanning),
            ("Link Scanning", self.test_link_scanning),
            ("User Settings", self.test_user_settings),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running: {test_name}")
            if test_func():
                passed += 1
            time.sleep(0.5)  # Small delay between tests
        
        print("\n" + "=" * 80)
        print(f"📊 PHASE 6 SECURITY TEST SUMMARY: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL SECURITY TESTS PASSED! Backend is production-ready with maximum security.")
            return True
        else:
            print(f"⚠️  {total - passed} test(s) failed. Security implementation needs attention.")
            return False
    
    def save_results(self):
        """Save test results to file"""
        try:
            with open('/app/backend_phase6_test_results.json', 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'backend_url': self.backend_url,
                    'phase': 'Phase 6 - Secure Backend API Development',
                    'results': self.results,
                    'summary': {
                        'total_tests': len(self.results),
                        'passed': sum(1 for r in self.results if r['success']),
                        'failed': sum(1 for r in self.results if not r['success'])
                    }
                }, f, indent=2)
            print(f"📄 Phase 6 test results saved to /app/backend_phase6_test_results.json")
        except Exception as e:
            print(f"❌ Error saving results: {e}")

if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_all_tests()
    tester.save_results()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)