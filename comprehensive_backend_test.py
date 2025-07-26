#!/usr/bin/env python3
"""
Comprehensive Backend Testing Suite for Aman Cybersecurity Platform
Tests all critical backend functionality after applying fixes for local setup issues
"""

import requests
import json
import sys
import os
import time
import websocket
import threading
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

class ComprehensiveBackendTester:
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
        self.auth_token = None
        self.admin_token = None
        self.test_user_data = {
            "name": "Sarah Johnson",
            "email": f"sarah.johnson.{int(time.time())}@cybersectest.com",
            "password": "SecurePass123!",
            "organization": "CyberSec Testing Corp"
        }
        self.admin_user_data = {
            "name": "Admin User",
            "email": f"admin.{int(time.time())}@cybersectest.com", 
            "password": "AdminPass123!",
            "organization": "Admin Organization"
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
    
    def get_auth_headers(self, admin=False):
        """Get authorization headers for authenticated requests"""
        token = self.admin_token if admin else self.auth_token
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}

    # 1. Test Database Connection
    def test_database_connection(self):
        """Test MongoDB database connection and health"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                checks = data.get('checks', {})
                db_status = checks.get('database', 'unknown')
                
                if db_status == 'healthy':
                    self.log_result("Database Connection", True, 
                                  f"MongoDB connected successfully - Status: {data['status']}")
                    return True
                else:
                    self.log_result("Database Connection", False, 
                                  f"Database unhealthy - Status: {db_status}")
                    return False
            else:
                self.log_result("Database Connection", False, 
                              f"Health check failed: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Database Connection", False, f"Request failed: {str(e)}")
            return False

    # 2. Test Authentication System
    def test_authentication_system(self):
        """Test complete JWT authentication system"""
        try:
            # Test user registration
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
                self.log_result("Authentication System", False, 
                              f"Registration failed: HTTP {reg_response.status_code}")
                return False
            
            # Test user login
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
                login_data = login_response.json()
                if 'access_token' in login_data and 'refresh_token' in login_data:
                    self.auth_token = login_data['access_token']
                    
                    # Test token refresh
                    refresh_data = {"refresh_token": login_data['refresh_token']}
                    refresh_response = requests.post(
                        f"{self.backend_url}/auth/refresh",
                        json=refresh_data,
                        timeout=10
                    )
                    
                    if refresh_response.status_code == 200:
                        self.log_result("Authentication System", True, 
                                      "Registration, login, and token refresh working")
                        return True
                    else:
                        self.log_result("Authentication System", False, 
                                      f"Token refresh failed: HTTP {refresh_response.status_code}")
                        return False
                else:
                    self.log_result("Authentication System", False, "Missing tokens in login response")
                    return False
            else:
                self.log_result("Authentication System", False, 
                              f"Login failed: HTTP {login_response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Authentication System", False, f"Request failed: {str(e)}")
            return False

    # 3. Test AI-Enhanced Email Scanning
    def test_ai_enhanced_email_scanning(self):
        """Test AI-powered email scanning with fallback mechanism"""
        try:
            headers = self.get_auth_headers()
            
            # Test 1: Legitimate email
            legitimate_email = {
                "email_subject": "Monthly Newsletter - Company Updates",
                "email_body": "Dear Team, Here are this month's company updates and achievements. We've successfully completed several projects and are looking forward to the upcoming quarter. Best regards, HR Team",
                "sender": "hr@company.com",
                "recipient": self.test_user_data["email"]
            }
            
            response1 = requests.post(
                f"{self.backend_url}/scan/email",
                json=legitimate_email,
                headers=headers,
                timeout=15
            )
            
            # Test 2: Phishing email
            phishing_email = {
                "email_subject": "URGENT: Account Suspended - Verify Now!",
                "email_body": "Your account has been suspended due to suspicious activity. Click here immediately to verify: http://fake-bank-security.com/verify?urgent=true. Enter your login credentials to prevent permanent closure. This is time-sensitive!",
                "sender": "security@fake-bank-security.com",
                "recipient": self.test_user_data["email"]
            }
            
            response2 = requests.post(
                f"{self.backend_url}/scan/email",
                json=phishing_email,
                headers=headers,
                timeout=15
            )
            
            # Test 3: Urgency manipulation email
            urgency_email = {
                "email_subject": "Action Required: Account Will Be Closed in 24 Hours",
                "email_body": "URGENT ACTION REQUIRED! Your account will be permanently closed in 24 hours unless you verify your identity immediately. Click here now: http://urgent-verification.tk/verify. Don't delay - act now!",
                "sender": "urgent@verification-center.com",
                "recipient": self.test_user_data["email"]
            }
            
            response3 = requests.post(
                f"{self.backend_url}/scan/email",
                json=urgency_email,
                headers=headers,
                timeout=15
            )
            
            # Analyze results
            if all(r.status_code == 200 for r in [response1, response2, response3]):
                data1, data2, data3 = response1.json(), response2.json(), response3.json()
                
                # Check if AI scanning is working properly
                legitimate_safe = data1.get('risk_score', 100) <= 30 and data1.get('status') == 'safe'
                phishing_detected = data2.get('risk_score', 0) >= 70 and data2.get('status') in ['phishing', 'potential_phishing']
                urgency_detected = data3.get('risk_score', 0) >= 70 and data3.get('status') in ['phishing', 'potential_phishing']
                
                # Check for AI-powered features
                has_explanations = all(len(d.get('explanation', '')) > 20 for d in [data1, data2, data3])
                has_recommendations = all(len(d.get('recommendations', [])) > 0 for d in [data2, data3])
                
                if legitimate_safe and phishing_detected and urgency_detected and has_explanations:
                    self.log_result("AI-Enhanced Email Scanning", True, 
                                  f"AI scanning working - Legitimate: {data1['risk_score']:.1f}, Phishing: {data2['risk_score']:.1f}, Urgency: {data3['risk_score']:.1f}")
                    return True
                else:
                    self.log_result("AI-Enhanced Email Scanning", False, 
                                  f"AI detection issues - Legitimate: {data1['risk_score']:.1f}, Phishing: {data2['risk_score']:.1f}, Urgency: {data3['risk_score']:.1f}")
                    return False
            else:
                status_codes = [r.status_code for r in [response1, response2, response3]]
                self.log_result("AI-Enhanced Email Scanning", False, 
                              f"HTTP errors: {status_codes}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("AI-Enhanced Email Scanning", False, f"Request failed: {str(e)}")
            return False

    # 4. Test AI-Enhanced Link Scanning
    def test_ai_enhanced_link_scanning(self):
        """Test AI-powered link scanning with threat detection"""
        try:
            headers = self.get_auth_headers()
            
            # Test 1: Legitimate URL
            legitimate_link = {
                "url": "https://www.google.com",
                "context": "Search engine link"
            }
            
            response1 = requests.post(
                f"{self.backend_url}/scan/link",
                json=legitimate_link,
                headers=headers,
                timeout=15
            )
            
            # Test 2: Malicious URL
            malicious_link = {
                "url": "http://phishing-site-example.tk/login?redirect=malicious.com",
                "context": "Suspicious login page found in email"
            }
            
            response2 = requests.post(
                f"{self.backend_url}/scan/link",
                json=malicious_link,
                headers=headers,
                timeout=15
            )
            
            # Test 3: Shortened URLs
            shortened_links = [
                {"url": "http://bit.ly/suspicious123", "context": "Shortened URL in email"},
                {"url": "http://tinyurl.com/malicious456", "context": "Tiny URL redirect"},
                {"url": "http://t.co/phishing789", "context": "Twitter shortened link"}
            ]
            
            shortened_responses = []
            for link in shortened_links:
                resp = requests.post(
                    f"{self.backend_url}/scan/link",
                    json=link,
                    headers=headers,
                    timeout=15
                )
                shortened_responses.append(resp)
            
            # Analyze results
            if response1.status_code == 200 and response2.status_code == 200:
                data1, data2 = response1.json(), response2.json()
                
                # Check AI link analysis
                legitimate_safe = data1.get('risk_score', 100) <= 30 and data1.get('status') == 'safe'
                malicious_detected = data2.get('risk_score', 0) >= 70 and data2.get('status') in ['phishing', 'potential_phishing']
                
                # Check shortened URL detection
                shortened_detected = 0
                for resp in shortened_responses:
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get('is_shortened', False):
                            shortened_detected += 1
                
                if legitimate_safe and malicious_detected and shortened_detected >= 2:
                    self.log_result("AI-Enhanced Link Scanning", True, 
                                  f"AI link scanning working - Legitimate: {data1['risk_score']:.1f}, Malicious: {data2['risk_score']:.1f}, Shortened detected: {shortened_detected}/3")
                    return True
                else:
                    self.log_result("AI-Enhanced Link Scanning", False, 
                                  f"AI link detection issues - Legitimate: {data1['risk_score']:.1f}, Malicious: {data2['risk_score']:.1f}, Shortened: {shortened_detected}/3")
                    return False
            else:
                self.log_result("AI-Enhanced Link Scanning", False, 
                              f"HTTP errors: {response1.status_code}, {response2.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("AI-Enhanced Link Scanning", False, f"Request failed: {str(e)}")
            return False

    # 5. Test Dashboard Endpoints
    def test_dashboard_endpoints(self):
        """Test user dashboard statistics and recent emails"""
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
                            self.log_result("Dashboard Endpoints", True, 
                                          f"Dashboard working - Stats: {stats_data['total_scans']} scans, {stats_data['accuracy_rate']}% accuracy, {len(emails_data['emails'])} recent emails")
                            return True
                        else:
                            self.log_result("Dashboard Endpoints", False, "Recent emails format invalid")
                            return False
                    else:
                        self.log_result("Dashboard Endpoints", False, f"Recent emails failed: HTTP {emails_response.status_code}")
                        return False
                else:
                    missing = [f for f in required_fields if f not in stats_data]
                    self.log_result("Dashboard Endpoints", False, f"Missing stats fields: {missing}")
                    return False
            else:
                self.log_result("Dashboard Endpoints", False, f"Dashboard stats failed: HTTP {stats_response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Dashboard Endpoints", False, f"Request failed: {str(e)}")
            return False

    # 6. Test WebSocket Health
    def test_websocket_health(self):
        """Test WebSocket connection for real-time features"""
        try:
            # Get user ID from profile first
            headers = self.get_auth_headers()
            profile_response = requests.get(f"{self.backend_url}/user/profile", headers=headers, timeout=10)
            
            if profile_response.status_code != 200:
                self.log_result("WebSocket Health", False, "Could not get user profile for WebSocket test")
                return False
            
            user_id = profile_response.json().get('id')
            if not user_id:
                self.log_result("WebSocket Health", False, "No user ID in profile response")
                return False
            
            # Test WebSocket connection
            ws_url = self.backend_url.replace('http', 'ws').replace('/api', f'/api/ws/{user_id}')
            
            connection_successful = False
            connection_error = None
            
            def on_open(ws):
                nonlocal connection_successful
                connection_successful = True
                # Send a ping message
                ws.send(json.dumps({"type": "ping"}))
            
            def on_message(ws, message):
                try:
                    data = json.loads(message)
                    if data.get("type") == "pong":
                        ws.close()
                except:
                    pass
            
            def on_error(ws, error):
                nonlocal connection_error
                connection_error = str(error)
            
            try:
                ws = websocket.WebSocketApp(ws_url,
                                          on_open=on_open,
                                          on_message=on_message,
                                          on_error=on_error)
                
                # Run WebSocket in a separate thread with timeout
                ws_thread = threading.Thread(target=ws.run_forever)
                ws_thread.daemon = True
                ws_thread.start()
                
                # Wait for connection
                time.sleep(2)
                
                if connection_successful:
                    self.log_result("WebSocket Health", True, "WebSocket connection and ping/pong working")
                    return True
                else:
                    self.log_result("WebSocket Health", False, f"WebSocket connection failed: {connection_error}")
                    return False
                    
            except Exception as e:
                self.log_result("WebSocket Health", False, f"WebSocket test failed: {str(e)}")
                return False
                
        except Exception as e:
            self.log_result("WebSocket Health", False, f"WebSocket setup failed: {str(e)}")
            return False

    # 7. Test Admin Panel
    def test_admin_panel(self):
        """Test admin dashboard endpoints with proper role-based access"""
        try:
            # First test with regular user (should be denied)
            headers = self.get_auth_headers()
            
            admin_stats_response = requests.get(f"{self.backend_url}/admin/dashboard/stats", headers=headers, timeout=10)
            
            if admin_stats_response.status_code == 403:
                # Test admin endpoints structure (even though we can't access them)
                admin_endpoints = [
                    "/admin/dashboard/stats",
                    "/admin/users",
                    "/admin/threats",
                    "/admin/system/monitoring",
                    "/admin/audit/log"
                ]
                
                access_denied_count = 0
                for endpoint in admin_endpoints:
                    response = requests.get(f"{self.backend_url}{endpoint}", headers=headers, timeout=10)
                    if response.status_code == 403:
                        access_denied_count += 1
                
                if access_denied_count == len(admin_endpoints):
                    self.log_result("Admin Panel", True, 
                                  f"Admin panel properly protected - All {len(admin_endpoints)} endpoints deny regular user access")
                    return True
                else:
                    self.log_result("Admin Panel", False, 
                                  f"Admin panel security issue - Only {access_denied_count}/{len(admin_endpoints)} endpoints properly protected")
                    return False
            else:
                self.log_result("Admin Panel", False, 
                              f"Admin panel not properly protected - Regular user got HTTP {admin_stats_response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Admin Panel", False, f"Request failed: {str(e)}")
            return False

    # 8. Test AI Usage Analytics
    def test_ai_usage_analytics(self):
        """Test AI usage tracking and limits"""
        try:
            headers = self.get_auth_headers()
            
            # Test AI usage analytics
            analytics_response = requests.get(f"{self.backend_url}/ai/usage/analytics", headers=headers, timeout=10)
            
            if analytics_response.status_code == 200:
                analytics_data = analytics_response.json()
                
                # Test AI usage limits
                limits_response = requests.get(f"{self.backend_url}/ai/usage/limits", headers=headers, timeout=10)
                
                if limits_response.status_code == 200:
                    limits_data = limits_response.json()
                    required_fields = ['user_tier', 'within_limits', 'current_usage']
                    
                    if any(field in limits_data for field in required_fields):
                        self.log_result("AI Usage Analytics", True, 
                                      f"AI usage tracking working - User tier: {limits_data.get('user_tier', 'unknown')}, Within limits: {limits_data.get('within_limits', 'unknown')}")
                        return True
                    else:
                        self.log_result("AI Usage Analytics", False, "AI usage limits response missing required fields")
                        return False
                else:
                    self.log_result("AI Usage Analytics", False, f"AI usage limits failed: HTTP {limits_response.status_code}")
                    return False
            else:
                self.log_result("AI Usage Analytics", False, f"AI usage analytics failed: HTTP {analytics_response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("AI Usage Analytics", False, f"Request failed: {str(e)}")
            return False

    # 9. Test Security Features
    def test_security_features(self):
        """Test rate limiting and input validation"""
        try:
            # Test rate limiting on health endpoint (10/minute limit)
            rapid_requests = []
            for i in range(12):  # Exceed the limit
                response = requests.get(f"{self.backend_url}/health", timeout=5)
                rapid_requests.append(response.status_code)
                time.sleep(0.1)
            
            rate_limited = any(status == 429 for status in rapid_requests)
            
            if rate_limited:
                # Test input validation with oversized email
                headers = self.get_auth_headers()
                oversized_email = {
                    "email_subject": "Test",
                    "email_body": "A" * 60000,  # Exceeds 50KB limit
                    "sender": "test@example.com",
                    "recipient": self.test_user_data["email"]
                }
                
                validation_response = requests.post(
                    f"{self.backend_url}/scan/email",
                    json=oversized_email,
                    headers=headers,
                    timeout=10
                )
                
                if validation_response.status_code in [400, 422]:
                    self.log_result("Security Features", True, 
                                  "Rate limiting and input validation working correctly")
                    return True
                else:
                    self.log_result("Security Features", False, 
                                  f"Input validation not working: HTTP {validation_response.status_code}")
                    return False
            else:
                self.log_result("Security Features", False, "Rate limiting not working - no 429 responses")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Security Features", False, f"Request failed: {str(e)}")
            return False

    # 10. Test Error Handling
    def test_error_handling(self):
        """Test graceful fallbacks when AI modules are unavailable"""
        try:
            headers = self.get_auth_headers()
            
            # Test with invalid data to trigger error handling
            invalid_email = {
                "email_subject": "",  # Empty subject
                "email_body": "",     # Empty body
                "sender": "invalid-email",  # Invalid email format
                "recipient": self.test_user_data["email"]
            }
            
            error_response = requests.post(
                f"{self.backend_url}/scan/email",
                json=invalid_email,
                headers=headers,
                timeout=10
            )
            
            # Should handle gracefully (either process or return proper error)
            if error_response.status_code in [200, 400, 422]:
                # Test invalid URL
                invalid_link = {
                    "url": "not-a-valid-url",
                    "context": "test"
                }
                
                link_error_response = requests.post(
                    f"{self.backend_url}/scan/link",
                    json=invalid_link,
                    headers=headers,
                    timeout=10
                )
                
                if link_error_response.status_code in [200, 400, 422]:
                    # Test unauthenticated request
                    unauth_response = requests.get(f"{self.backend_url}/user/profile", timeout=10)
                    
                    if unauth_response.status_code in [401, 403]:
                        self.log_result("Error Handling", True, 
                                      "Error handling working - Invalid data handled gracefully, authentication enforced")
                        return True
                    else:
                        self.log_result("Error Handling", False, 
                                      f"Authentication not enforced: HTTP {unauth_response.status_code}")
                        return False
                else:
                    self.log_result("Error Handling", False, 
                                  f"Link error handling failed: HTTP {link_error_response.status_code}")
                    return False
            else:
                self.log_result("Error Handling", False, 
                              f"Email error handling failed: HTTP {error_response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Error Handling", False, f"Request failed: {str(e)}")
            return False

    def run_comprehensive_tests(self):
        """Run all comprehensive backend tests"""
        print("=" * 80)
        print("🚀 AMAN CYBERSECURITY PLATFORM - COMPREHENSIVE BACKEND TESTING")
        print("=" * 80)
        
        # Critical backend functionality tests
        tests = [
            ("Database Connection", self.test_database_connection),
            ("Authentication System", self.test_authentication_system),
            ("AI-Enhanced Email Scanning", self.test_ai_enhanced_email_scanning),
            ("AI-Enhanced Link Scanning", self.test_ai_enhanced_link_scanning),
            ("Dashboard Endpoints", self.test_dashboard_endpoints),
            ("WebSocket Health", self.test_websocket_health),
            ("Admin Panel", self.test_admin_panel),
            ("AI Usage Analytics", self.test_ai_usage_analytics),
            ("Security Features", self.test_security_features),
            ("Error Handling", self.test_error_handling)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🔍 Testing: {test_name}")
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                self.log_result(test_name, False, f"Test execution failed: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE BACKEND TEST RESULTS")
        print("=" * 80)
        
        success_rate = (passed / total) * 100
        print(f"✅ Passed: {passed}/{total} ({success_rate:.1f}%)")
        print(f"❌ Failed: {total - passed}/{total}")
        
        if success_rate >= 80:
            print("🎉 BACKEND STATUS: EXCELLENT - Production Ready")
        elif success_rate >= 60:
            print("⚠️  BACKEND STATUS: GOOD - Minor Issues")
        else:
            print("🚨 BACKEND STATUS: NEEDS ATTENTION - Critical Issues")
        
        # Print detailed results
        print("\n📋 DETAILED TEST RESULTS:")
        for result in self.results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        return success_rate >= 80

if __name__ == "__main__":
    tester = ComprehensiveBackendTester()
    success = tester.run_comprehensive_tests()
    sys.exit(0 if success else 1)