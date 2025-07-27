#!/usr/bin/env python3
"""
Error Handling and String Response Testing for Aman Cybersecurity Platform
Focus on testing error responses to ensure they return string messages instead of validation objects
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

class ErrorHandlingTester:
    def __init__(self):
        self.backend_url = get_backend_url()
        if not self.backend_url:
            print("❌ Could not determine backend URL from frontend/.env")
            sys.exit(1)
        
        # Ensure URL ends with /api for proper routing
        if not self.backend_url.endswith('/api'):
            self.backend_url = f"{self.backend_url}/api"
            
        print(f"🔗 Testing backend error handling at: {self.backend_url}")
        self.results = []
        self.auth_token = None
        self.test_user_data = {
            "name": "Error Test User",
            "email": f"errortest_{int(time.time())}@cybersec.com",
            "password": "SecurePass123!",
            "organization": "Error Test Organization"
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

    def setup_authentication(self):
        """Setup authentication for protected endpoint tests"""
        try:
            # Register user
            registration_data = {
                "name": self.test_user_data["name"],
                "email": self.test_user_data["email"],
                "password": self.test_user_data["password"],
                "organization": self.test_user_data["organization"]
            }
            
            reg_response = requests.post(
                f"{self.backend_url}/auth/register",
                json=registration_data,
                timeout=10
            )
            
            if reg_response.status_code != 200:
                print(f"❌ Registration failed: {reg_response.status_code}")
                return False
            
            # Login to get token
            login_data = {
                "email": self.test_user_data["email"],
                "password": self.test_user_data["password"]
            }
            
            login_response = requests.post(
                f"{self.backend_url}/auth/login",
                json=login_data,
                timeout=10
            )
            
            if login_response.status_code == 200:
                data = login_response.json()
                self.auth_token = data.get('access_token')
                return True
            else:
                print(f"❌ Login failed: {login_response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication setup failed: {e}")
            return False

    def get_auth_headers(self):
        """Get authorization headers for authenticated requests"""
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        return {}

    def test_basic_health_check(self):
        """Test basic health check endpoint"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['status', 'service', 'version', 'timestamp', 'checks']
                
                if all(field in data for field in required_fields):
                    checks = data.get('checks', {})
                    if 'database' in checks and 'api' in checks:
                        self.log_result("Basic Health Check", True, 
                                      f"Status: {data['status']}, DB: {checks['database']}, API: {checks['api']}")
                        return True
                    else:
                        self.log_result("Basic Health Check", False, "Missing system checks in response")
                        return False
                else:
                    self.log_result("Basic Health Check", False, f"Missing required fields: {required_fields}")
                    return False
            else:
                self.log_result("Basic Health Check", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Basic Health Check", False, f"Request failed: {str(e)}")
            return False

    def test_authentication_error_responses(self):
        """Test authentication endpoints return string error messages"""
        try:
            # Test invalid login
            invalid_login_data = {
                "email": "nonexistent@example.com",
                "password": "wrongpassword"
            }
            
            response = requests.post(
                f"{self.backend_url}/auth/login",
                json=invalid_login_data,
                timeout=10
            )
            
            if response.status_code == 401:
                try:
                    error_data = response.json()
                    # Check if error response contains string messages, not validation objects
                    if 'detail' in error_data:
                        detail = error_data['detail']
                        if isinstance(detail, str):
                            self.log_result("Authentication Error String Response", True, 
                                          f"Error properly returned as string: '{detail}'")
                            return True
                        else:
                            self.log_result("Authentication Error String Response", False, 
                                          f"Error returned as object instead of string: {type(detail)}")
                            return False
                    else:
                        self.log_result("Authentication Error String Response", False, 
                                      "No 'detail' field in error response")
                        return False
                except json.JSONDecodeError:
                    self.log_result("Authentication Error String Response", False, 
                                  "Error response is not valid JSON")
                    return False
            else:
                self.log_result("Authentication Error String Response", False, 
                              f"Expected 401, got {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Authentication Error String Response", False, f"Request failed: {str(e)}")
            return False

    def test_validation_error_responses(self):
        """Test validation errors return string messages instead of objects"""
        try:
            # Test email scanning with invalid data
            headers = self.get_auth_headers()
            invalid_email_data = {
                "email_subject": "A" * 300,  # Very long subject
                "email_body": "B" * 60000,   # Exceeds 50KB limit
                "sender": "invalid-email-format",
                "recipient": "invalid-recipient"
            }
            
            response = requests.post(
                f"{self.backend_url}/scan/email",
                json=invalid_email_data,
                headers=headers,
                timeout=15
            )
            
            # Should return 400 or 422 for validation error
            if response.status_code in [400, 422]:
                try:
                    error_data = response.json()
                    # Check if error response contains string messages
                    if 'detail' in error_data:
                        detail = error_data['detail']
                        if isinstance(detail, str):
                            self.log_result("Validation Error String Response", True, 
                                          f"Validation error properly returned as string: '{detail}'")
                            return True
                        else:
                            self.log_result("Validation Error String Response", False, 
                                          f"Validation error returned as object: {type(detail)} - {detail}")
                            return False
                    elif 'error' in error_data:
                        error = error_data['error']
                        if isinstance(error, str):
                            self.log_result("Validation Error String Response", True, 
                                          f"Validation error properly returned as string: '{error}'")
                            return True
                        else:
                            self.log_result("Validation Error String Response", False, 
                                          f"Validation error returned as object: {type(error)} - {error}")
                            return False
                    else:
                        self.log_result("Validation Error String Response", False, 
                                      "No error field in validation response")
                        return False
                except json.JSONDecodeError:
                    self.log_result("Validation Error String Response", False, 
                                  "Validation error response is not valid JSON")
                    return False
            else:
                self.log_result("Validation Error String Response", False, 
                              f"Expected 400/422, got {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Validation Error String Response", False, f"Request failed: {str(e)}")
            return False

    def test_cache_stats_endpoint_error_handling(self):
        """Test the failing cache stats endpoint - should return 403 for non-admin users, not 500"""
        try:
            headers = self.get_auth_headers()
            
            response = requests.get(f"{self.backend_url}/ai/cache/stats", headers=headers, timeout=10)
            
            # Should return 403 for non-admin users, not 500
            if response.status_code == 403:
                try:
                    error_data = response.json()
                    if 'detail' in error_data:
                        detail = error_data['detail']
                        if isinstance(detail, str) and 'admin' in detail.lower():
                            self.log_result("Cache Stats Access Control", True, 
                                          f"Properly denied non-admin access with string message: '{detail}'")
                            return True
                        else:
                            self.log_result("Cache Stats Access Control", False, 
                                          f"Error message format incorrect: {type(detail)} - {detail}")
                            return False
                    else:
                        self.log_result("Cache Stats Access Control", False, 
                                      "No detail field in 403 response")
                        return False
                except json.JSONDecodeError:
                    self.log_result("Cache Stats Access Control", False, 
                                  "403 response is not valid JSON")
                    return False
            elif response.status_code == 500:
                self.log_result("Cache Stats Access Control", False, 
                              "Endpoint returning 500 error instead of 403 for non-admin users - THIS IS THE BUG")
                return False
            else:
                self.log_result("Cache Stats Access Control", False, 
                              f"Unexpected status code: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Cache Stats Access Control", False, f"Request failed: {str(e)}")
            return False

    def test_dashboard_apis(self):
        """Test dashboard APIs return proper data"""
        try:
            headers = self.get_auth_headers()
            
            # Test dashboard stats
            stats_response = requests.get(f"{self.backend_url}/dashboard/stats", headers=headers, timeout=10)
            
            if stats_response.status_code == 200:
                stats_data = stats_response.json()
                required_fields = ['phishing_caught', 'safe_emails', 'potential_phishing', 'total_scans', 'accuracy_rate']
                
                if all(field in stats_data for field in required_fields):
                    # Test recent emails
                    emails_response = requests.get(f"{self.backend_url}/dashboard/recent-emails", headers=headers, timeout=10)
                    
                    if emails_response.status_code == 200:
                        emails_data = emails_response.json()
                        if 'emails' in emails_data and isinstance(emails_data['emails'], list):
                            self.log_result("Dashboard APIs", True, 
                                          f"Dashboard stats and recent emails working correctly")
                            return True
                        else:
                            self.log_result("Dashboard APIs", False, "Recent emails response format incorrect")
                            return False
                    else:
                        self.log_result("Dashboard APIs", False, f"Recent emails failed: {emails_response.status_code}")
                        return False
                else:
                    missing_fields = [f for f in required_fields if f not in stats_data]
                    self.log_result("Dashboard APIs", False, f"Missing stats fields: {missing_fields}")
                    return False
            else:
                self.log_result("Dashboard APIs", False, f"Dashboard stats failed: {stats_response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Dashboard APIs", False, f"Request failed: {str(e)}")
            return False

    def test_ai_integration_endpoints(self):
        """Test AI integration endpoints work properly"""
        try:
            headers = self.get_auth_headers()
            
            # Test email scanning with AI
            email_data = {
                "email_subject": "Test AI Integration Email",
                "email_body": "This is a test email to verify AI integration is working properly.",
                "sender": "test@example.com",
                "recipient": self.test_user_data["email"]
            }
            
            response = requests.post(
                f"{self.backend_url}/scan/email",
                json=email_data,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['id', 'status', 'risk_score', 'explanation', 'threat_sources', 'detected_threats', 'recommendations']
                
                if all(field in data for field in required_fields):
                    # Test link scanning
                    link_data = {
                        "url": "https://www.google.com",
                        "context": "Test link for AI integration"
                    }
                    
                    link_response = requests.post(
                        f"{self.backend_url}/scan/link",
                        json=link_data,
                        headers=headers,
                        timeout=15
                    )
                    
                    if link_response.status_code == 200:
                        link_data = link_response.json()
                        link_required_fields = ['url', 'status', 'risk_score', 'explanation', 'threat_categories', 'redirect_chain', 'is_shortened']
                        
                        if all(field in link_data for field in link_required_fields):
                            self.log_result("AI Integration Endpoints", True, 
                                          f"Email and link scanning AI integration working")
                            return True
                        else:
                            missing_fields = [f for f in link_required_fields if f not in link_data]
                            self.log_result("AI Integration Endpoints", False, f"Missing link fields: {missing_fields}")
                            return False
                    else:
                        self.log_result("AI Integration Endpoints", False, f"Link scanning failed: {link_response.status_code}")
                        return False
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_result("AI Integration Endpoints", False, f"Missing email fields: {missing_fields}")
                    return False
            else:
                self.log_result("AI Integration Endpoints", False, f"Email scanning failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("AI Integration Endpoints", False, f"Request failed: {str(e)}")
            return False

    def test_database_connectivity(self):
        """Test database connectivity through health endpoint"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                checks = data.get('checks', {})
                db_status = checks.get('database', 'unknown')
                
                if db_status == 'healthy':
                    self.log_result("Database Connectivity", True, 
                                  f"Database connection healthy")
                    return True
                else:
                    self.log_result("Database Connectivity", False, 
                                  f"Database status: {db_status}")
                    return False
            else:
                self.log_result("Database Connectivity", False, f"Health check failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Database Connectivity", False, f"Request failed: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all error handling and backend functionality tests"""
        print("=" * 80)
        print("🔍 AMAN CYBERSECURITY PLATFORM - ERROR HANDLING & BACKEND FUNCTIONALITY TESTS")
        print("=" * 80)
        
        # Setup authentication first
        if not self.setup_authentication():
            print("❌ Failed to setup authentication - cannot run protected endpoint tests")
            return
        
        # Run tests
        tests = [
            self.test_basic_health_check,
            self.test_database_connectivity,
            self.test_authentication_error_responses,
            self.test_validation_error_responses,
            self.test_cache_stats_endpoint_error_handling,
            self.test_dashboard_apis,
            self.test_ai_integration_endpoints,
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                self.log_result(test.__name__, False, f"Test exception: {str(e)}")
        
        print("\n" + "=" * 80)
        print("📊 ERROR HANDLING TEST RESULTS SUMMARY")
        print("=" * 80)
        
        success_rate = (passed / total) * 100 if total > 0 else 0
        print(f"✅ Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        
        if passed == total:
            print("🎉 ALL ERROR HANDLING TESTS PASSED!")
        else:
            print(f"⚠️  {total - passed} tests failed - check error handling implementation")
        
        # Print detailed results
        print("\n📋 Detailed Results:")
        for result in self.results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        return success_rate

if __name__ == "__main__":
    tester = ErrorHandlingTester()
    success_rate = tester.run_all_tests()
    
    if success_rate is not None and success_rate >= 85:
        print(f"\n🎯 Backend error handling is working well ({success_rate:.1f}% success rate)")
        sys.exit(0)
    else:
        rate_display = f"{success_rate:.1f}%" if success_rate is not None else "N/A"
        print(f"\n⚠️  Backend error handling needs attention ({rate_display} success rate)")
        sys.exit(1)