#!/usr/bin/env python3
"""
Aman Cybersecurity Platform - End-to-End Integration Testing
Tests complete system workflows from user registration to threat detection
"""

import requests
import json
import time
import sys
from datetime import datetime

class EndToEndTester:
    def __init__(self):
        # Get backend URL from frontend environment
        self.backend_url = self._get_backend_url()
        if not self.backend_url.endswith('/api'):
            self.backend_url = f"{self.backend_url}/api"
        
        print(f"🔗 Testing end-to-end integration at: {self.backend_url}")
        
        # Test data
        self.test_user = {
            "name": "Integration Test User",
            "email": f"e2e_test_{int(time.time())}@amansec.com",
            "password": "E2ETestPass123!",
            "organization": "E2E Testing Org"
        }
        
        self.auth_token = None
        self.test_results = []
        
    def _get_backend_url(self):
        """Get backend URL from frontend .env file"""
        try:
            with open('/app/frontend/.env', 'r') as f:
                for line in f:
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        return line.split('=', 1)[1].strip()
        except Exception as e:
            print(f"❌ Error reading frontend .env: {e}")
            return "http://localhost:8001"
        return "http://localhost:8001"
    
    def log_result(self, test_name, success, details):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   📋 {details}")
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        
        return success
    
    def test_system_health(self):
        """Test 1: System Health Check"""
        print("\n🏥 TESTING SYSTEM HEALTH")
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                checks = data.get('checks', {})
                db_healthy = checks.get('database') == 'healthy'
                api_healthy = checks.get('api') == 'healthy'
                
                if db_healthy and api_healthy:
                    return self.log_result(
                        "System Health Check", 
                        True, 
                        f"All systems operational - DB: {checks['database']}, API: {checks['api']}"
                    )
                else:
                    return self.log_result(
                        "System Health Check", 
                        False, 
                        f"System issues detected - DB: {checks.get('database')}, API: {checks.get('api')}"
                    )
            else:
                return self.log_result(
                    "System Health Check", 
                    False, 
                    f"Health endpoint returned {response.status_code}"
                )
                
        except Exception as e:
            return self.log_result("System Health Check", False, f"Health check failed: {str(e)}")
    
    def test_user_registration(self):
        """Test 2: User Registration Flow"""
        print("\n👤 TESTING USER REGISTRATION")
        try:
            response = requests.post(
                f"{self.backend_url}/auth/register",
                json=self.test_user,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'data' in data:
                    return self.log_result(
                        "User Registration", 
                        True, 
                        f"User registered successfully: {self.test_user['email']}"
                    )
                else:
                    return self.log_result(
                        "User Registration", 
                        False, 
                        f"Registration response invalid: {data}"
                    )
            else:
                return self.log_result(
                    "User Registration", 
                    False, 
                    f"Registration failed with {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            return self.log_result("User Registration", False, f"Registration error: {str(e)}")
    
    def test_user_authentication(self):
        """Test 3: User Authentication Flow"""  
        print("\n🔐 TESTING USER AUTHENTICATION")
        try:
            login_data = {
                "email": self.test_user["email"],
                "password": self.test_user["password"]
            }
            
            response = requests.post(
                f"{self.backend_url}/auth/login",
                json=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'access_token' in data and 'refresh_token' in data:
                    self.auth_token = data['access_token']
                    return self.log_result(
                        "User Authentication", 
                        True, 
                        f"Login successful, token received (expires in {data.get('expires_in', 0)}s)"
                    )
                else:
                    return self.log_result(
                        "User Authentication", 
                        False, 
                        f"Login response missing tokens: {data}"
                    )
            else:
                return self.log_result(
                    "User Authentication", 
                    False, 
                    f"Login failed with {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            return self.log_result("User Authentication", False, f"Authentication error: {str(e)}")
    
    def test_protected_endpoints(self):
        """Test 4: Protected Endpoint Access"""
        print("\n🛡️ TESTING PROTECTED ENDPOINT ACCESS")
        
        if not self.auth_token:
            return self.log_result(
                "Protected Endpoint Access", 
                False, 
                "No auth token available - authentication test must pass first"
            )
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        endpoints_to_test = [
            ("/user/profile", "User Profile"),
            ("/dashboard/stats", "Dashboard Statistics"),
            ("/dashboard/recent-emails", "Recent Emails"),
            ("/user/settings", "User Settings")
        ]
        
        passed_tests = 0
        total_tests = len(endpoints_to_test)
        
        for endpoint, name in endpoints_to_test:
            try:
                response = requests.get(
                    f"{self.backend_url}{endpoint}",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    passed_tests += 1
                    print(f"   ✅ {name}: Working")
                else:
                    print(f"   ❌ {name}: Failed ({response.status_code})")
                    
            except Exception as e:
                print(f"   ❌ {name}: Error - {str(e)}")
        
        success_rate = (passed_tests / total_tests) * 100
        return self.log_result(
            "Protected Endpoint Access", 
            passed_tests >= 3,  # At least 3/4 should work
            f"{passed_tests}/{total_tests} endpoints working ({success_rate:.1f}% success rate)"
        )
    
    def test_email_scanning_workflow(self):
        """Test 5: Email Scanning Workflow"""
        print("\n📧 TESTING EMAIL SCANNING WORKFLOW")
        
        if not self.auth_token:
            return self.log_result(
                "Email Scanning Workflow", 
                False, 
                "No auth token available - authentication required"
            )
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test data for different threat levels
        test_emails = [
            {
                "name": "Safe Email",
                "data": {
                    "email_subject": "Weekly Team Meeting Reminder",
                    "sender": "team@company.com",
                    "recipient": self.test_user["email"],
                    "email_body": "Hi team, just a reminder about our weekly team meeting tomorrow at 2 PM. Please bring your project updates."
                },
                "expected_risk": "low"
            },
            {
                "name": "Suspicious Email", 
                "data": {
                    "email_subject": "Urgent: Verify Your Account Information",
                    "sender": "security@suspicious-domain.net",
                    "recipient": self.test_user["email"],
                    "email_body": "Your account will be suspended unless you verify your information immediately. Click here to verify account details."
                },
                "expected_risk": "medium"
            },
            {
                "name": "Phishing Email",
                "data": {
                    "email_subject": "URGENT: Claim Your Prize Now! Limited Time Offer!",
                    "sender": "prizes@win-now.fake",
                    "recipient": self.test_user["email"],
                    "email_body": "Congratulations! You've won $10,000! Click here immediately to claim your prize before it expires today. Verify account to proceed."
                },
                "expected_risk": "high"
            }
        ]
        
        successful_scans = 0
        total_scans = len(test_emails)
        
        for email_test in test_emails:
            try:
                response = requests.post(
                    f"{self.backend_url}/scan/email",
                    json=email_test["data"],
                    headers=headers,
                    timeout=15
                )
                
                if response.status_code == 200:
                    scan_result = response.json()
                    risk_score = scan_result.get('risk_score', 0)
                    status = scan_result.get('status', 'unknown')
                    
                    # Validate scan results make sense
                    if 'id' in scan_result and 'explanation' in scan_result:
                        successful_scans += 1
                        print(f"   ✅ {email_test['name']}: {status.upper()} (Risk: {risk_score}%)")
                    else:
                        print(f"   ❌ {email_test['name']}: Invalid scan result format")
                else:
                    print(f"   ❌ {email_test['name']}: Scan failed ({response.status_code})")
                    
            except Exception as e:
                print(f"   ❌ {email_test['name']}: Error - {str(e)}")
        
        success_rate = (successful_scans / total_scans) * 100
        return self.log_result(
            "Email Scanning Workflow", 
            successful_scans >= 2,  # At least 2/3 should work
            f"{successful_scans}/{total_scans} scans successful ({success_rate:.1f}% success rate)"
        )
    
    def test_link_scanning_workflow(self):
        """Test 6: Link Scanning Workflow"""
        print("\n🔗 TESTING LINK SCANNING WORKFLOW")
        
        if not self.auth_token:
            return self.log_result(
                "Link Scanning Workflow", 
                False, 
                "No auth token available - authentication required"
            )
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        test_links = [
            {
                "name": "Safe Link",
                "url": "https://www.google.com",
                "expected_safe": True
            },
            {
                "name": "Shortened Link (Suspicious)",
                "url": "https://bit.ly/suspicious-link",
                "expected_safe": False
            },
            {
                "name": "Legitimate Business Link",
                "url": "https://www.microsoft.com/security",
                "expected_safe": True
            }
        ]
        
        successful_scans = 0
        total_scans = len(test_links)
        
        for link_test in test_links:
            try:
                response = requests.post(
                    f"{self.backend_url}/scan/link",
                    json={"url": link_test["url"]},
                    headers=headers,
                    timeout=15
                )
                
                if response.status_code == 200:
                    scan_result = response.json()
                    risk_score = scan_result.get('risk_score', 0)
                    status = scan_result.get('status', 'unknown')
                    
                    if 'url' in scan_result and 'explanation' in scan_result:
                        successful_scans += 1
                        print(f"   ✅ {link_test['name']}: {status.upper()} (Risk: {risk_score}%)")
                    else:
                        print(f"   ❌ {link_test['name']}: Invalid scan result format")
                else:
                    print(f"   ❌ {link_test['name']}: Scan failed ({response.status_code})")
                    
            except Exception as e:
                print(f"   ❌ {link_test['name']}: Error - {str(e)}")
        
        success_rate = (successful_scans / total_scans) * 100
        return self.log_result(
            "Link Scanning Workflow", 
            successful_scans >= 2,  # At least 2/3 should work
            f"{successful_scans}/{total_scans} scans successful ({success_rate:.1f}% success rate)"
        )
    
    def test_dashboard_integration(self):
        """Test 7: Dashboard Data Integration"""
        print("\n📊 TESTING DASHBOARD INTEGRATION")
        
        if not self.auth_token:
            return self.log_result(
                "Dashboard Integration", 
                False, 
                "No auth token available - authentication required"
            )
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            # Test dashboard stats
            stats_response = requests.get(
                f"{self.backend_url}/dashboard/stats",
                headers=headers,
                timeout=10
            )
            
            # Test recent emails
            emails_response = requests.get(
                f"{self.backend_url}/dashboard/recent-emails",
                headers=headers,
                timeout=10
            )
            
            stats_working = stats_response.status_code == 200
            emails_working = emails_response.status_code == 200
            
            if stats_working and emails_working:
                stats_data = stats_response.json()
                emails_data = emails_response.json()
                
                # Validate data structure
                has_stats_fields = all(field in stats_data for field in ['phishing_caught', 'safe_emails', 'potential_phishing'])
                has_emails_array = 'emails' in emails_data and isinstance(emails_data['emails'], list)
                
                if has_stats_fields and has_emails_array:
                    total_scans = stats_data.get('total_scans', 0)
                    accuracy_rate = stats_data.get('accuracy_rate', 0)
                    return self.log_result(
                        "Dashboard Integration", 
                        True, 
                        f"Dashboard data integration working - Total scans: {total_scans}, Accuracy: {accuracy_rate}%"
                    )
                else:
                    return self.log_result(
                        "Dashboard Integration", 
                        False, 
                        "Dashboard data format invalid"
                    )
            else:
                return self.log_result(
                    "Dashboard Integration", 
                    False, 
                    f"Dashboard endpoints failed - Stats: {stats_response.status_code}, Emails: {emails_response.status_code}"
                )
                
        except Exception as e:
            return self.log_result("Dashboard Integration", False, f"Dashboard integration error: {str(e)}")
    
    def test_user_settings_persistence(self):
        """Test 8: User Settings Persistence"""
        print("\n⚙️ TESTING USER SETTINGS PERSISTENCE")
        
        if not self.auth_token:
            return self.log_result(
                "Settings Persistence", 
                False, 
                "No auth token available - authentication required"
            )
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        try:
            # Get current settings
            get_response = requests.get(
                f"{self.backend_url}/user/settings",
                headers=headers,
                timeout=10
            )
            
            if get_response.status_code != 200:
                return self.log_result(
                    "Settings Persistence", 
                    False, 
                    f"Failed to get settings: {get_response.status_code}"
                )
            
            # Update settings
            new_settings = {
                "email_notifications": False,
                "real_time_scanning": True,
                "block_suspicious_links": True,
                "scan_attachments": False,
                "share_threat_intelligence": True
            }
            
            put_response = requests.put(
                f"{self.backend_url}/user/settings",
                json=new_settings,
                headers=headers,
                timeout=10
            )
            
            if put_response.status_code != 200:
                return self.log_result(
                    "Settings Persistence", 
                    False, 
                    f"Failed to update settings: {put_response.status_code}"
                )
            
            # Verify settings were saved
            verify_response = requests.get(
                f"{self.backend_url}/user/settings",
                headers=headers,
                timeout=10
            )
            
            if verify_response.status_code == 200:
                saved_settings = verify_response.json()
                settings_match = all(
                    saved_settings.get(key) == value 
                    for key, value in new_settings.items()
                )
                
                if settings_match:
                    return self.log_result(
                        "Settings Persistence", 
                        True, 
                        "Settings successfully saved and retrieved"
                    )
                else:
                    return self.log_result(
                        "Settings Persistence", 
                        False, 
                        "Settings not saved correctly"
                    )
            else:
                return self.log_result(
                    "Settings Persistence", 
                    False, 
                    f"Failed to verify settings: {verify_response.status_code}"
                )
                
        except Exception as e:
            return self.log_result("Settings Persistence", False, f"Settings persistence error: {str(e)}")
    
    def run_all_tests(self):
        """Run all end-to-end tests"""
        print("🚀 STARTING END-TO-END INTEGRATION TESTING")
        print("=" * 60)
        
        # Run tests in logical order
        tests = [
            self.test_system_health,
            self.test_user_registration,
            self.test_user_authentication,
            self.test_protected_endpoints,
            self.test_email_scanning_workflow,
            self.test_link_scanning_workflow, 
            self.test_dashboard_integration,
            self.test_user_settings_persistence
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
            time.sleep(1)  # Brief pause between tests
        
        # Print summary
        print("\n" + "=" * 60)
        print("🏁 END-TO-END TESTING SUMMARY")
        print("=" * 60)
        
        success_rate = (passed / total) * 100
        print(f"📊 OVERALL RESULTS: {passed}/{total} tests passed ({success_rate:.1f}%)")
        
        if success_rate >= 85:
            print("🟢 RESULT: EXCELLENT - System ready for production")
            system_status = "PRODUCTION READY"
        elif success_rate >= 70:  
            print("🟡 RESULT: GOOD - Minor issues to address")
            system_status = "MOSTLY READY"
        elif success_rate >= 50:
            print("🟠 RESULT: FAIR - Several issues need fixing")
            system_status = "NEEDS WORK"
        else:
            print("🔴 RESULT: POOR - Major issues require attention")
            system_status = "NOT READY"
        
        print(f"🎯 SYSTEM STATUS: {system_status}")
        
        # Save detailed results
        results_summary = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": total,
            "passed_tests": passed,
            "success_rate": success_rate,
            "system_status": system_status,
            "detailed_results": self.test_results
        }
        
        with open('/app/e2e_test_results.json', 'w') as f:
            json.dump(results_summary, f, indent=2)
        
        print(f"📝 Detailed results saved to: /app/e2e_test_results.json")
        
        return success_rate >= 70  # Consider 70%+ as passing

if __name__ == "__main__":
    tester = EndToEndTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)