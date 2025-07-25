#!/usr/bin/env python3
"""
Backend API Testing Suite for Aman Cybersecurity Platform - Browser Extension Backend Integration Testing
Tests browser extension API integration, authentication flow, AI-powered scanning, and cross-platform compatibility
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
    def test_browser_extension_cors_headers(self):
        """Test CORS configuration allows browser extension requests"""
        try:
            # Simulate browser extension request with extension origin
            headers = {
                'Origin': 'chrome-extension://abcdefghijklmnopqrstuvwxyz123456',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'authorization,content-type'
            }
            
            # Test preflight request
            response = requests.options(f"{self.backend_url}/scan/email", headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Check CORS headers
                cors_headers = response.headers
                access_control_allow_origin = cors_headers.get('Access-Control-Allow-Origin', '')
                access_control_allow_methods = cors_headers.get('Access-Control-Allow-Methods', '')
                access_control_allow_headers = cors_headers.get('Access-Control-Allow-Headers', '')
                
                # Check if CORS is properly configured for extensions
                cors_configured = (
                    '*' in access_control_allow_origin or 'chrome-extension' in access_control_allow_origin and
                    'POST' in access_control_allow_methods and
                    'authorization' in access_control_allow_headers.lower()
                )
                
                if cors_configured:
                    self.log_result("Browser Extension CORS Headers", True, 
                                  f"CORS properly configured - Origin: {access_control_allow_origin}, Methods: {access_control_allow_methods}")
                    return True
                else:
                    self.log_result("Browser Extension CORS Headers", False, 
                                  f"CORS not configured for extensions - Origin: {access_control_allow_origin}")
                    return False
            else:
                self.log_result("Browser Extension CORS Headers", False, f"Preflight request failed: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Browser Extension CORS Headers", False, f"Request failed: {str(e)}")
            return False

    def test_extension_authentication_flow(self):
        """Test JWT authentication flow for browser extension"""
        try:
            # Simulate extension authentication with additional headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0.4472.124 Extension/1.0',
                'Origin': 'chrome-extension://test-extension-id',
                'Content-Type': 'application/json'
            }
            
            login_data = {
                "email": self.test_user_data["email"],
                "password": self.test_user_data["password"]
            }
            
            response = requests.post(
                f"{self.backend_url}/auth/login",
                json=login_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['access_token', 'refresh_token', 'token_type']
                
                if all(field in data for field in required_fields):
                    # Test if token works for extension API calls
                    auth_headers = {
                        **headers,
                        'Authorization': f"Bearer {data['access_token']}"
                    }
                    
                    # Test protected endpoint with extension headers
                    profile_response = requests.get(
                        f"{self.backend_url}/user/profile",
                        headers=auth_headers,
                        timeout=10
                    )
                    
                    if profile_response.status_code == 200:
                        self.log_result("Extension Authentication Flow", True, 
                                      f"Extension authentication successful, token works for API calls")
                        return True
                    else:
                        self.log_result("Extension Authentication Flow", False, 
                                      f"Token doesn't work for extension API calls: HTTP {profile_response.status_code}")
                        return False
                else:
                    self.log_result("Extension Authentication Flow", False, f"Missing token fields: {required_fields}")
                    return False
            else:
                self.log_result("Extension Authentication Flow", False, f"Extension login failed: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Extension Authentication Flow", False, f"Request failed: {str(e)}")
            return False

    def test_extension_email_scanning_integration(self):
        """Test email scanning API integration for browser extension"""
        try:
            headers = self.get_auth_headers()
            headers.update({
                'User-Agent': 'Mozilla/5.0 Chrome Extension',
                'Origin': 'chrome-extension://test-extension-id',
                'X-Extension-Version': '1.0.0'
            })
            
            # Test email scanning with extension-specific data format
            extension_email_data = {
                "email_subject": "Urgent: Account Security Alert - Action Required",
                "email_body": "Your account has been compromised. Click here to secure it: http://fake-bank-security.com/secure-login?token=malicious123. Enter your credentials immediately to prevent account closure.",
                "sender": "security@fake-bank-security.com",
                "recipient": self.test_user_data["email"],
                "extension_metadata": {
                    "platform": "gmail",
                    "timestamp": "2025-01-27T10:30:00Z",
                    "extension_id": "test-extension-id"
                }
            }
            
            response = requests.post(
                f"{self.backend_url}/scan/email",
                json=extension_email_data,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['id', 'status', 'risk_score', 'explanation', 'threat_sources', 'detected_threats', 'recommendations']
                
                if all(field in data for field in required_fields):
                    risk_score = data.get('risk_score', 0)
                    status = data.get('status')
                    explanation = data.get('explanation', '')
                    
                    # Verify AI-powered scanning works through extension
                    if (risk_score >= 70 and status in ['potential_phishing', 'phishing'] and 
                        len(explanation) > 50):
                        self.log_result("Extension Email Scanning Integration", True, 
                                      f"Extension email scanning working - Risk: {risk_score:.1f}, Status: {status}")
                        return True
                    else:
                        self.log_result("Extension Email Scanning Integration", False, 
                                      f"Extension scanning not detecting threats properly - Risk: {risk_score:.1f}")
                        return False
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_result("Extension Email Scanning Integration", False, f"Missing response fields: {missing_fields}")
                    return False
            elif response.status_code == 401 or response.status_code == 403:
                self.log_result("Extension Email Scanning Integration", False, "Extension authentication failed")
                return False
            else:
                self.log_result("Extension Email Scanning Integration", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Extension Email Scanning Integration", False, f"Request failed: {str(e)}")
            return False

    def test_extension_link_scanning_integration(self):
        """Test link scanning API integration for browser extension"""
        try:
            headers = self.get_auth_headers()
            headers.update({
                'User-Agent': 'Mozilla/5.0 Chrome Extension',
                'Origin': 'chrome-extension://test-extension-id',
                'X-Extension-Version': '1.0.0'
            })
            
            # Test link scanning with extension context
            extension_link_data = {
                "url": "http://phishing-site-example.tk/login?redirect=http://malicious.com",
                "context": "Click here to verify your account - found in suspicious email",
                "extension_metadata": {
                    "platform": "outlook",
                    "found_in": "email_body",
                    "surrounding_text": "urgent action required"
                }
            }
            
            response = requests.post(
                f"{self.backend_url}/scan/link",
                json=extension_link_data,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['url', 'status', 'risk_score', 'explanation', 'threat_categories', 'redirect_chain', 'is_shortened']
                
                if all(field in data for field in required_fields):
                    risk_score = data.get('risk_score', 0)
                    status = data.get('status')
                    explanation = data.get('explanation', '')
                    threat_categories = data.get('threat_categories', [])
                    
                    # Verify AI-powered link scanning works through extension
                    if (risk_score >= 60 and status in ['potential_phishing', 'phishing'] and 
                        len(explanation) > 30 and len(threat_categories) > 0):
                        self.log_result("Extension Link Scanning Integration", True, 
                                      f"Extension link scanning working - Risk: {risk_score:.1f}, Categories: {len(threat_categories)}")
                        return True
                    else:
                        self.log_result("Extension Link Scanning Integration", False, 
                                      f"Extension link scanning not detecting threats - Risk: {risk_score:.1f}")
                        return False
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_result("Extension Link Scanning Integration", False, f"Missing response fields: {missing_fields}")
                    return False
            elif response.status_code == 401 or response.status_code == 403:
                self.log_result("Extension Link Scanning Integration", False, "Extension authentication failed")
                return False
            else:
                self.log_result("Extension Link Scanning Integration", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Extension Link Scanning Integration", False, f"Request failed: {str(e)}")
            return False

    def test_extension_data_transformation(self):
        """Test API response transformation for extension format"""
        try:
            headers = self.get_auth_headers()
            headers.update({
                'User-Agent': 'Mozilla/5.0 Chrome Extension',
                'Accept': 'application/json',
                'X-Extension-Format': 'popup'
            })
            
            # Test dashboard stats for extension popup
            response = requests.get(f"{self.backend_url}/dashboard/stats", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['phishing_caught', 'safe_emails', 'potential_phishing', 'total_scans', 'accuracy_rate']
                
                if all(field in data for field in required_fields):
                    # Verify data is in format suitable for extension popup
                    stats_valid = (
                        isinstance(data['phishing_caught'], int) and
                        isinstance(data['safe_emails'], int) and
                        isinstance(data['potential_phishing'], int) and
                        isinstance(data['total_scans'], int) and
                        isinstance(data['accuracy_rate'], (int, float))
                    )
                    
                    if stats_valid:
                        # Test recent emails for extension format
                        emails_response = requests.get(f"{self.backend_url}/dashboard/recent-emails", headers=headers, timeout=10)
                        
                        if emails_response.status_code == 200:
                            emails_data = emails_response.json()
                            if 'emails' in emails_data and isinstance(emails_data['emails'], list):
                                self.log_result("Extension Data Transformation", True, 
                                              f"API responses properly formatted for extension - Stats and emails available")
                                return True
                            else:
                                self.log_result("Extension Data Transformation", False, "Emails data not properly formatted")
                                return False
                        else:
                            self.log_result("Extension Data Transformation", False, f"Recent emails failed: HTTP {emails_response.status_code}")
                            return False
                    else:
                        self.log_result("Extension Data Transformation", False, "Stats data types invalid for extension")
                        return False
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_result("Extension Data Transformation", False, f"Missing stats fields: {missing_fields}")
                    return False
            elif response.status_code == 401 or response.status_code == 403:
                self.log_result("Extension Data Transformation", False, "Extension authentication failed")
                return False
            else:
                self.log_result("Extension Data Transformation", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Extension Data Transformation", False, f"Request failed: {str(e)}")
            return False

    def test_extension_error_handling(self):
        """Test error handling and fallbacks for extension requests"""
        try:
            headers = self.get_auth_headers()
            headers.update({
                'User-Agent': 'Mozilla/5.0 Chrome Extension',
                'Origin': 'chrome-extension://test-extension-id'
            })
            
            # Test with invalid email data to trigger error handling
            invalid_email_data = {
                "email_subject": "A" * 300,  # Very long subject
                "email_body": "B" * 60000,   # Exceeds 50KB limit
                "sender": "invalid-email-format",
                "recipient": self.test_user_data["email"]
            }
            
            response = requests.post(
                f"{self.backend_url}/scan/email",
                json=invalid_email_data,
                headers=headers,
                timeout=15
            )
            
            # Should return 400 or 422 for validation error
            if response.status_code in [400, 422]:
                error_data = response.json()
                
                # Check if error response is properly formatted for extension
                if 'error' in error_data or 'detail' in error_data:
                    # Test with invalid URL to check link scanning error handling
                    invalid_link_data = {
                        "url": "not-a-valid-url-format",
                        "context": "test context"
                    }
                    
                    link_response = requests.post(
                        f"{self.backend_url}/scan/link",
                        json=invalid_link_data,
                        headers=headers,
                        timeout=10
                    )
                    
                    if link_response.status_code in [400, 422]:
                        link_error_data = link_response.json()
                        if 'error' in link_error_data or 'detail' in link_error_data:
                            self.log_result("Extension Error Handling", True, 
                                          "Error handling working properly for extension requests")
                            return True
                        else:
                            self.log_result("Extension Error Handling", False, "Link error response not properly formatted")
                            return False
                    else:
                        self.log_result("Extension Error Handling", False, f"Link validation not working: HTTP {link_response.status_code}")
                        return False
                else:
                    self.log_result("Extension Error Handling", False, "Email error response not properly formatted")
                    return False
            else:
                self.log_result("Extension Error Handling", False, f"Email validation not working: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Extension Error Handling", False, f"Request failed: {str(e)}")
            return False

    def test_extension_ai_fallback_mechanism(self):
        """Test AI fallback mechanisms when called from extension"""
        try:
            headers = self.get_auth_headers()
            headers.update({
                'User-Agent': 'Mozilla/5.0 Chrome Extension',
                'Origin': 'chrome-extension://test-extension-id',
                'X-Force-Fallback': 'true'  # Simulate AI unavailable
            })
            
            # Test email scanning with fallback
            fallback_email_data = {
                "email_subject": "Suspicious email for fallback testing",
                "email_body": "This email contains suspicious content for testing fallback mechanisms when AI is unavailable.",
                "sender": "test@suspicious-domain.com",
                "recipient": self.test_user_data["email"]
            }
            
            response = requests.post(
                f"{self.backend_url}/scan/email",
                json=fallback_email_data,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['id', 'status', 'risk_score', 'explanation']
                
                if all(field in data for field in required_fields):
                    risk_score = data.get('risk_score', 0)
                    status = data.get('status')
                    explanation = data.get('explanation', '')
                    
                    # Verify fallback mechanism provides reasonable results
                    fallback_working = (
                        isinstance(risk_score, (int, float)) and 0 <= risk_score <= 100 and
                        status in ['safe', 'potential_phishing', 'phishing'] and
                        len(explanation) > 10
                    )
                    
                    if fallback_working:
                        self.log_result("Extension AI Fallback Mechanism", True, 
                                      f"Fallback working for extension - Risk: {risk_score:.1f}, Status: {status}")
                        return True
                    else:
                        self.log_result("Extension AI Fallback Mechanism", False, 
                                      f"Fallback not working properly - Risk: {risk_score}, Status: {status}")
                        return False
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_result("Extension AI Fallback Mechanism", False, f"Missing response fields: {missing_fields}")
                    return False
            elif response.status_code == 401 or response.status_code == 403:
                self.log_result("Extension AI Fallback Mechanism", False, "Extension authentication failed")
                return False
            else:
                self.log_result("Extension AI Fallback Mechanism", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Extension AI Fallback Mechanism", False, f"Request failed: {str(e)}")
            return False

    def test_extension_cross_platform_compatibility(self):
        """Test API calls work from different browser extension contexts"""
        try:
            # Test different browser extension user agents
            browser_contexts = [
                {
                    'name': 'Chrome Extension',
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0.4472.124',
                    'origin': 'chrome-extension://test-chrome-extension'
                },
                {
                    'name': 'Firefox Extension',
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
                    'origin': 'moz-extension://test-firefox-extension'
                },
                {
                    'name': 'Edge Extension',
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Edge/91.0.864.59',
                    'origin': 'chrome-extension://test-edge-extension'
                }
            ]
            
            successful_contexts = 0
            
            for context in browser_contexts:
                headers = self.get_auth_headers()
                headers.update({
                    'User-Agent': context['user_agent'],
                    'Origin': context['origin']
                })
                
                # Test health endpoint from each browser context
                response = requests.get(f"{self.backend_url}/health", headers=headers, timeout=10)
                
                if response.status_code == 200:
                    successful_contexts += 1
                    
            if successful_contexts == len(browser_contexts):
                self.log_result("Extension Cross-Platform Compatibility", True, 
                              f"All {successful_contexts} browser contexts working correctly")
                return True
            elif successful_contexts > 0:
                self.log_result("Extension Cross-Platform Compatibility", False, 
                              f"Only {successful_contexts}/{len(browser_contexts)} browser contexts working")
                return False
            else:
                self.log_result("Extension Cross-Platform Compatibility", False, 
                              "No browser extension contexts working")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Extension Cross-Platform Compatibility", False, f"Request failed: {str(e)}")
            return False

    def test_rate_limiting(self):
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
                    if (isinstance(data['phishing_caught'], int) and 
                        isinstance(data['safe_emails'], int) and 
                        isinstance(data['potential_phishing'], int) and
                        isinstance(data['total_scans'], int) and
                        isinstance(data['accuracy_rate'], (int, float))):
                        self.log_result("Protected Dashboard Stats", True, 
                                      f"Stats: Phishing={data['phishing_caught']}, Safe={data['safe_emails']}, Potential={data['potential_phishing']}, Accuracy={data['accuracy_rate']}%")
                        return True
                    else:
                        self.log_result("Protected Dashboard Stats", False, "Invalid data types in response")
                        return False
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_result("Protected Dashboard Stats", False, f"Missing fields: {missing_fields}")
                    return False
            elif response.status_code == 401 or response.status_code == 403:
                self.log_result("Protected Dashboard Stats", False, "Authentication required - token may be invalid")
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
                                              f"Retrieved {len(emails)} emails with valid structure and risk scores")
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
                        self.log_result("Protected Recent Emails", True, "Empty email list returned (valid for new user)")
                        return True
                else:
                    self.log_result("Protected Recent Emails", False, "Response missing 'emails' array")
                    return False
            elif response.status_code == 401 or response.status_code == 403:
                self.log_result("Protected Recent Emails", False, "Authentication required - token may be invalid")
                return False
            else:
                self.log_result("Protected Recent Emails", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Protected Recent Emails", False, f"Request failed: {str(e)}")
            return False

    def test_advanced_email_scanning(self):
        """Test POST /api/scan/email endpoint with advanced scanning logic"""
        try:
            headers = self.get_auth_headers()
            
            # Test with sophisticated phishing email
            phishing_email_data = {
                "email_subject": "URGENT: Your account will be suspended - Verify immediately!",
                "email_body": "Dear Customer, Your account has been compromised and will be suspended in 24 hours. Click here to verify your identity: http://secure-bank-update.com/verify?token=abc123. Please provide your login credentials to prevent account closure. This is urgent and requires immediate action. Don't tell anyone about this email.",
                "sender": "security@secure-bank-update.com",
                "recipient": self.test_user_data["email"]
            }
            
            response = requests.post(
                f"{self.backend_url}/scan/email",
                json=phishing_email_data,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['id', 'status', 'risk_score', 'explanation', 'threat_sources', 'detected_threats', 'recommendations']
                
                if all(field in data for field in required_fields):
                    # Verify advanced scanning features
                    risk_score = data.get('risk_score', 0)
                    status = data.get('status')
                    explanation = data.get('explanation', '')
                    threat_sources = data.get('threat_sources', [])
                    detected_threats = data.get('detected_threats', [])
                    recommendations = data.get('recommendations', [])
                    
                    # Check if advanced scanning is working (not just placeholder)
                    advanced_features_present = (
                        isinstance(risk_score, (int, float)) and risk_score > 0 and
                        status in ['safe', 'potential_phishing', 'phishing'] and
                        len(explanation) > 20 and  # Detailed explanation
                        isinstance(threat_sources, list) and
                        isinstance(detected_threats, list) and
                        isinstance(recommendations, list) and len(recommendations) > 0
                    )
                    
                    if advanced_features_present:
                        # For this phishing email, we expect high risk
                        if risk_score >= 50 and status in ['potential_phishing', 'phishing']:
                            self.log_result("Advanced Email Scanning", True, 
                                          f"Phishing detected: Risk={risk_score:.1f}, Status={status}, Threats={len(detected_threats)}, Sources={len(threat_sources)}")
                            return True
                        else:
                            self.log_result("Advanced Email Scanning", False, 
                                          f"Failed to detect obvious phishing: Risk={risk_score:.1f}, Status={status}")
                            return False
                    else:
                        self.log_result("Advanced Email Scanning", False, "Advanced scanning features not working - appears to be placeholder logic")
                        return False
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_result("Advanced Email Scanning", False, f"Missing response fields: {missing_fields}")
                    return False
            elif response.status_code == 401 or response.status_code == 403:
                self.log_result("Advanced Email Scanning", False, "Authentication required - token may be invalid")
                return False
            else:
                self.log_result("Advanced Email Scanning", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Advanced Email Scanning", False, f"Request failed: {str(e)}")
            return False

    def test_enhanced_link_scanning(self):
        """Test POST /api/scan/link endpoint with enhanced scanning logic"""
        try:
            headers = self.get_auth_headers()
            
            # Test with suspicious link
            suspicious_link_data = {
                "url": "http://secure-bank-update.com/verify-account?token=suspicious123&redirect=http://malicious-site.tk",
                "context": "Click here to verify your account immediately"
            }
            
            response = requests.post(
                f"{self.backend_url}/scan/link",
                json=suspicious_link_data,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['url', 'status', 'risk_score', 'explanation', 'threat_categories', 'redirect_chain', 'is_shortened']
                
                if all(field in data for field in required_fields):
                    # Verify enhanced scanning features
                    risk_score = data.get('risk_score', 0)
                    status = data.get('status')
                    explanation = data.get('explanation', '')
                    threat_categories = data.get('threat_categories', [])
                    is_shortened = data.get('is_shortened', False)
                    
                    # Check if enhanced scanning is working
                    enhanced_features_present = (
                        isinstance(risk_score, (int, float)) and risk_score > 0 and
                        status in ['safe', 'potential_phishing', 'phishing'] and
                        len(explanation) > 20 and  # Detailed explanation
                        isinstance(threat_categories, list) and
                        isinstance(is_shortened, bool)
                    )
                    
                    if enhanced_features_present:
                        # For this suspicious link, we expect medium to high risk
                        if risk_score >= 30:
                            self.log_result("Enhanced Link Scanning", True, 
                                          f"Suspicious link detected: Risk={risk_score:.1f}, Status={status}, Categories={len(threat_categories)}")
                            return True
                        else:
                            self.log_result("Enhanced Link Scanning", False, 
                                          f"Failed to detect suspicious link: Risk={risk_score:.1f}, Status={status}")
                            return False
                    else:
                        self.log_result("Enhanced Link Scanning", False, "Enhanced scanning features not working - appears to be placeholder logic")
                        return False
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_result("Enhanced Link Scanning", False, f"Missing response fields: {missing_fields}")
                    return False
            elif response.status_code == 401 or response.status_code == 403:
                self.log_result("Enhanced Link Scanning", False, "Authentication required - token may be invalid")
                return False
            else:
                self.log_result("Enhanced Link Scanning", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Enhanced Link Scanning", False, f"Request failed: {str(e)}")
            return False

    def test_feedback_submission(self):
        """Test POST /api/feedback/scan endpoint"""
        try:
            headers = self.get_auth_headers()
            
            # First, perform a scan to get a scan_id
            email_data = {
                "email_subject": "Test email for feedback",
                "email_body": "This is a test email for feedback submission.",
                "sender": "test@example.com",
                "recipient": self.test_user_data["email"]
            }
            
            scan_response = requests.post(
                f"{self.backend_url}/scan/email",
                json=email_data,
                headers=headers,
                timeout=10
            )
            
            if scan_response.status_code != 200:
                self.log_result("Feedback Submission", False, "Could not perform initial scan for feedback test")
                return False
            
            scan_id = scan_response.json().get('id')
            if not scan_id:
                self.log_result("Feedback Submission", False, "No scan ID returned from email scan")
                return False
            
            # Submit feedback
            feedback_data = {
                "scan_id": scan_id,
                "is_correct": True,
                "user_comment": "The scan result was accurate and helpful"
            }
            
            response = requests.post(
                f"{self.backend_url}/feedback/scan",
                json=feedback_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'message' in data and 'data' in data:
                    feedback_id = data.get('data', {}).get('feedback_id')
                    if feedback_id:
                        self.log_result("Feedback Submission", True, f"Feedback submitted successfully: {feedback_id}")
                        return True
                    else:
                        self.log_result("Feedback Submission", False, "No feedback ID returned")
                        return False
                else:
                    self.log_result("Feedback Submission", False, f"Invalid response format: {data}")
                    return False
            elif response.status_code == 401 or response.status_code == 403:
                self.log_result("Feedback Submission", False, "Authentication required - token may be invalid")
                return False
            else:
                self.log_result("Feedback Submission", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Feedback Submission", False, f"Request failed: {str(e)}")
            return False

    def test_feedback_analytics(self):
        """Test GET /api/feedback/analytics endpoint"""
        try:
            headers = self.get_auth_headers()
            response = requests.get(f"{self.backend_url}/feedback/analytics", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['total_feedback', 'accuracy_rate', 'feedback_breakdown', 'recent_feedback']
                
                if all(field in data for field in required_fields):
                    # Verify data types
                    if (isinstance(data['total_feedback'], int) and 
                        isinstance(data['accuracy_rate'], (int, float)) and
                        isinstance(data['feedback_breakdown'], dict) and
                        isinstance(data['recent_feedback'], list)):
                        self.log_result("Feedback Analytics", True, 
                                      f"Analytics: Total={data['total_feedback']}, Accuracy={data['accuracy_rate']}%, Breakdown={len(data['feedback_breakdown'])} types")
                        return True
                    else:
                        self.log_result("Feedback Analytics", False, "Invalid data types in analytics response")
                        return False
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_result("Feedback Analytics", False, f"Missing fields: {missing_fields}")
                    return False
            elif response.status_code == 401 or response.status_code == 403:
                self.log_result("Feedback Analytics", False, "Authentication required - token may be invalid")
                return False
            else:
                self.log_result("Feedback Analytics", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Feedback Analytics", False, f"Request failed: {str(e)}")
            return False

    def test_domain_threat_intelligence(self):
        """Test GET /api/threat-intelligence/domain/{domain} endpoint"""
        try:
            headers = self.get_auth_headers()
            
            # Test with a suspicious domain
            test_domain = "secure-bank-update.com"
            response = requests.get(f"{self.backend_url}/threat-intelligence/domain/{test_domain}", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['target', 'risk_level', 'risk_score', 'category', 'severity', 'confidence', 'description', 'sources', 'indicators']
                
                if all(field in data for field in required_fields):
                    # Verify threat intelligence features
                    risk_level = data.get('risk_level')
                    risk_score = data.get('risk_score', 0)
                    category = data.get('category')
                    confidence = data.get('confidence', 0)
                    sources = data.get('sources', [])
                    indicators = data.get('indicators', [])
                    
                    # Check if threat intelligence is working properly
                    intelligence_working = (
                        risk_level in ['safe', 'potential_phishing', 'phishing'] and
                        isinstance(risk_score, (int, float)) and 0 <= risk_score <= 100 and
                        isinstance(confidence, (int, float)) and 0 <= confidence <= 1 and
                        isinstance(sources, list) and len(sources) > 0 and
                        isinstance(indicators, list)
                    )
                    
                    if intelligence_working:
                        self.log_result("Domain Threat Intelligence", True, 
                                      f"Domain analysis: {test_domain} -> Risk={risk_score:.1f}, Level={risk_level}, Category={category}, Sources={len(sources)}")
                        return True
                    else:
                        self.log_result("Domain Threat Intelligence", False, "Threat intelligence data format invalid")
                        return False
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_result("Domain Threat Intelligence", False, f"Missing fields: {missing_fields}")
                    return False
            elif response.status_code == 401 or response.status_code == 403:
                self.log_result("Domain Threat Intelligence", False, "Authentication required - token may be invalid")
                return False
            else:
                self.log_result("Domain Threat Intelligence", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Domain Threat Intelligence", False, f"Request failed: {str(e)}")
            return False

    def test_url_threat_intelligence(self):
        """Test GET /api/threat-intelligence/url endpoint"""
        try:
            headers = self.get_auth_headers()
            
            # Test with a suspicious URL
            test_url = "http://secure-bank-update.com/verify?token=suspicious"
            response = requests.get(f"{self.backend_url}/threat-intelligence/url", 
                                  params={"url": test_url}, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['target', 'risk_level', 'risk_score', 'category', 'severity', 'confidence', 'description', 'sources', 'indicators']
                
                if all(field in data for field in required_fields):
                    # Verify threat intelligence features
                    risk_level = data.get('risk_level')
                    risk_score = data.get('risk_score', 0)
                    category = data.get('category')
                    confidence = data.get('confidence', 0)
                    sources = data.get('sources', [])
                    indicators = data.get('indicators', [])
                    
                    # Check if URL threat intelligence is working properly
                    intelligence_working = (
                        risk_level in ['safe', 'potential_phishing', 'phishing'] and
                        isinstance(risk_score, (int, float)) and 0 <= risk_score <= 100 and
                        isinstance(confidence, (int, float)) and 0 <= confidence <= 1 and
                        isinstance(sources, list) and len(sources) > 0 and
                        isinstance(indicators, list)
                    )
                    
                    if intelligence_working:
                        self.log_result("URL Threat Intelligence", True, 
                                      f"URL analysis: Risk={risk_score:.1f}, Level={risk_level}, Category={category}, Sources={len(sources)}")
                        return True
                    else:
                        self.log_result("URL Threat Intelligence", False, "URL threat intelligence data format invalid")
                        return False
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_result("URL Threat Intelligence", False, f"Missing fields: {missing_fields}")
                    return False
            elif response.status_code == 401 or response.status_code == 403:
                self.log_result("URL Threat Intelligence", False, "Authentication required - token may be invalid")
                return False
            else:
                self.log_result("URL Threat Intelligence", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("URL Threat Intelligence", False, f"Request failed: {str(e)}")
            return False

    def test_user_settings(self):
        """Test GET/PUT /api/user/settings endpoints"""
        try:
            headers = self.get_auth_headers()
            
            # Test GET settings
            get_response = requests.get(f"{self.backend_url}/user/settings", headers=headers, timeout=10)
            
            if get_response.status_code == 200:
                settings_data = get_response.json()
                
                # Test PUT settings
                updated_settings = {
                    "email_notifications": True,
                    "scan_notifications": True,
                    "weekly_reports": False,
                    "language": "en",
                    "timezone": "UTC",
                    "scan_sensitivity": "medium",
                    "auto_quarantine": False,
                    "share_threat_intelligence": True
                }
                
                put_response = requests.put(
                    f"{self.backend_url}/user/settings",
                    json=updated_settings,
                    headers=headers,
                    timeout=10
                )
                
                if put_response.status_code == 200:
                    put_data = put_response.json()
                    if 'message' in put_data:
                        self.log_result("User Settings", True, "Settings GET/PUT operations working correctly")
                        return True
                    else:
                        self.log_result("User Settings", False, "Invalid PUT response format")
                        return False
                else:
                    self.log_result("User Settings", False, f"PUT failed: HTTP {put_response.status_code}")
                    return False
            elif get_response.status_code == 401 or get_response.status_code == 403:
                self.log_result("User Settings", False, "Authentication required - token may be invalid")
                return False
            else:
                self.log_result("User Settings", False, f"GET failed: HTTP {get_response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("User Settings", False, f"Request failed: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("=" * 80)
        print("🚀 AMAN CYBERSECURITY PLATFORM - BROWSER EXTENSION BACKEND INTEGRATION TESTS")
        print("=" * 80)
        
        # Browser Extension Backend Integration Tests
        extension_tests = [
            self.test_health_endpoint,
            self.test_user_registration,
            self.test_user_login,
            self.test_token_refresh,
            self.test_browser_extension_cors_headers,
            self.test_extension_authentication_flow,
            self.test_extension_email_scanning_integration,
            self.test_extension_link_scanning_integration,
            self.test_extension_data_transformation,
            self.test_extension_error_handling,
            self.test_extension_ai_fallback_mechanism,
            self.test_extension_cross_platform_compatibility,
            self.test_protected_user_profile,
            self.test_protected_dashboard_stats,
            self.test_protected_recent_emails,
            self.test_advanced_email_scanning,
            self.test_enhanced_link_scanning,
            self.test_user_settings,
            self.test_rate_limiting
        ]
        
        passed = 0
        total = len(extension_tests)
        
        for test in extension_tests:
            if test():
                passed += 1
            print()  # Add spacing between tests
        
        print("=" * 80)
        print(f"📊 BROWSER EXTENSION BACKEND INTEGRATION TEST SUMMARY: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL BROWSER EXTENSION BACKEND INTEGRATION TESTS PASSED!")
            print("✅ Extension can successfully connect to backend APIs")
            print("✅ JWT authentication works for extension requests")
            print("✅ AI-powered scanning works through extension calls")
            print("✅ Data transformation works for extension format")
            print("✅ Error handling and fallbacks work correctly")
            print("✅ Cross-platform compatibility verified")
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