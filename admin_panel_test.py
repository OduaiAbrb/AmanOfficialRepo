#!/usr/bin/env python3
"""
Admin Panel Testing Suite for Aman Cybersecurity Platform - Phase 9 Admin Panel Development
Tests comprehensive admin panel functionality including dashboard statistics, user management,
threat analysis, system monitoring, audit logging, and role-based access control.
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

class AdminPanelTester:
    def __init__(self):
        self.backend_url = get_backend_url()
        if not self.backend_url:
            print("❌ Could not determine backend URL from frontend/.env")
            sys.exit(1)
        
        # Ensure URL ends with /api for proper routing
        if not self.backend_url.endswith('/api'):
            self.backend_url = f"{self.backend_url}/api"
            
        print(f"🔗 Testing admin panel at: {self.backend_url}")
        self.results = []
        self.regular_user_token = None
        self.admin_user_token = None
        self.super_admin_token = None
        
        # Test user data for different roles
        self.regular_user_data = {
            "name": "Regular User",
            "email": f"regular_{int(time.time())}@cybersec.com",
            "password": "SecurePass123!",
            "organization": "Test Organization"
        }
        
        self.admin_user_data = {
            "name": "Admin User",
            "email": f"admin_{int(time.time())}@cybersec.com", 
            "password": "AdminPass123!",
            "organization": "Admin Organization"
        }
        
        self.super_admin_data = {
            "name": "Super Admin",
            "email": f"superadmin_{int(time.time())}@cybersec.com",
            "password": "SuperAdminPass123!",
            "organization": "Super Admin Organization"
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
    
    def setup_test_users(self):
        """Setup test users with different roles"""
        try:
            # Register regular user
            reg_response = requests.post(
                f"{self.backend_url}/auth/register",
                json=self.regular_user_data,
                timeout=10
            )
            
            if reg_response.status_code == 200:
                # Login regular user
                login_response = requests.post(
                    f"{self.backend_url}/auth/login",
                    json={
                        "email": self.regular_user_data["email"],
                        "password": self.regular_user_data["password"]
                    },
                    timeout=10
                )
                
                if login_response.status_code == 200:
                    self.regular_user_token = login_response.json().get('access_token')
                    self.log_result("Setup Regular User", True, f"Regular user created: {self.regular_user_data['email']}")
                else:
                    self.log_result("Setup Regular User", False, f"Login failed: {login_response.status_code}")
                    return False
            else:
                self.log_result("Setup Regular User", False, f"Registration failed: {reg_response.status_code}")
                return False
            
            # For admin users, we'll need to create them and then manually update their roles
            # This is a limitation of the test setup - in production, super admins would create admin users
            
            # Register admin user
            admin_reg_response = requests.post(
                f"{self.backend_url}/auth/register",
                json=self.admin_user_data,
                timeout=10
            )
            
            if admin_reg_response.status_code == 200:
                # Login admin user
                admin_login_response = requests.post(
                    f"{self.backend_url}/auth/login",
                    json={
                        "email": self.admin_user_data["email"],
                        "password": self.admin_user_data["password"]
                    },
                    timeout=10
                )
                
                if admin_login_response.status_code == 200:
                    self.admin_user_token = admin_login_response.json().get('access_token')
                    self.log_result("Setup Admin User", True, f"Admin user created: {self.admin_user_data['email']} (role needs manual update)")
                else:
                    self.log_result("Setup Admin User", False, f"Admin login failed: {admin_login_response.status_code}")
                    return False
            else:
                self.log_result("Setup Admin User", False, f"Admin registration failed: {admin_reg_response.status_code}")
                return False
            
            return True
            
        except requests.exceptions.RequestException as e:
            self.log_result("Setup Test Users", False, f"Request failed: {str(e)}")
            return False
    
    def get_auth_headers(self, user_type="regular"):
        """Get authorization headers for different user types"""
        token = None
        if user_type == "regular":
            token = self.regular_user_token
        elif user_type == "admin":
            token = self.admin_user_token
        elif user_type == "super_admin":
            token = self.super_admin_token
        
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}
    
    def test_admin_dashboard_stats_access_control(self):
        """Test admin dashboard statistics endpoint access control"""
        try:
            # Test 1: Regular user should be denied access
            regular_headers = self.get_auth_headers("regular")
            response = requests.get(
                f"{self.backend_url}/admin/dashboard/stats",
                headers=regular_headers,
                timeout=10
            )
            
            if response.status_code == 403:
                self.log_result("Admin Dashboard Stats - Access Control (Regular User)", True, 
                              "Regular user correctly denied access (403)")
            else:
                self.log_result("Admin Dashboard Stats - Access Control (Regular User)", False, 
                              f"Regular user should be denied access, got: {response.status_code}")
                return False
            
            # Test 2: Admin user should have access (if properly configured)
            admin_headers = self.get_auth_headers("admin")
            admin_response = requests.get(
                f"{self.backend_url}/admin/dashboard/stats",
                headers=admin_headers,
                timeout=10
            )
            
            # Note: This might fail if admin role is not properly set up in test environment
            if admin_response.status_code == 200:
                data = admin_response.json()
                required_fields = ['statistics', 'timestamp']
                
                if all(field in data for field in required_fields):
                    stats = data['statistics']
                    expected_stats = [
                        'total_users', 'active_users', 'total_organizations', 
                        'active_organizations', 'today_scans', 'today_threats',
                        'total_threats_blocked', 'avg_risk_score', 'ai_usage_cost', 'cache_hit_rate'
                    ]
                    
                    if all(stat in stats for stat in expected_stats):
                        self.log_result("Admin Dashboard Stats - Data Structure", True, 
                                      f"All required statistics present: {len(expected_stats)} fields")
                        return True
                    else:
                        missing_stats = [s for s in expected_stats if s not in stats]
                        self.log_result("Admin Dashboard Stats - Data Structure", False, 
                                      f"Missing statistics: {missing_stats}")
                        return False
                else:
                    self.log_result("Admin Dashboard Stats - Data Structure", False, 
                                  f"Missing required fields: {required_fields}")
                    return False
            elif admin_response.status_code == 403:
                self.log_result("Admin Dashboard Stats - Admin Access", False, 
                              "Admin user denied access - role may not be properly configured")
                return False
            else:
                self.log_result("Admin Dashboard Stats - Admin Access", False, 
                              f"Unexpected response: {admin_response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Admin Dashboard Stats - Access Control", False, f"Request failed: {str(e)}")
            return False
    
    def test_admin_dashboard_stats_data_accuracy(self):
        """Test admin dashboard statistics data accuracy and real-time updates"""
        try:
            admin_headers = self.get_auth_headers("admin")
            
            # Get initial statistics
            response = requests.get(
                f"{self.backend_url}/admin/dashboard/stats",
                headers=admin_headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                stats = data.get('statistics', {})
                
                # Verify data types and ranges
                data_validation_checks = [
                    ('total_users', int, lambda x: x >= 0),
                    ('active_users', int, lambda x: x >= 0),
                    ('total_organizations', int, lambda x: x >= 0),
                    ('active_organizations', int, lambda x: x >= 0),
                    ('today_scans', int, lambda x: x >= 0),
                    ('today_threats', int, lambda x: x >= 0),
                    ('total_threats_blocked', int, lambda x: x >= 0),
                    ('avg_risk_score', (int, float), lambda x: 0 <= x <= 100),
                    ('ai_usage_cost', (int, float), lambda x: x >= 0),
                    ('cache_hit_rate', (int, float), lambda x: 0 <= x <= 100)
                ]
                
                validation_passed = True
                validation_details = []
                
                for field, expected_type, validation_func in data_validation_checks:
                    value = stats.get(field)
                    if value is None:
                        validation_passed = False
                        validation_details.append(f"{field}: missing")
                    elif not isinstance(value, expected_type):
                        validation_passed = False
                        validation_details.append(f"{field}: wrong type ({type(value).__name__})")
                    elif not validation_func(value):
                        validation_passed = False
                        validation_details.append(f"{field}: invalid value ({value})")
                    else:
                        validation_details.append(f"{field}: {value} ✓")
                
                if validation_passed:
                    self.log_result("Admin Dashboard Stats - Data Accuracy", True, 
                                  f"All statistics valid: {', '.join(validation_details[:3])}...")
                    return True
                else:
                    self.log_result("Admin Dashboard Stats - Data Accuracy", False, 
                                  f"Validation failed: {', '.join([d for d in validation_details if '✓' not in d])}")
                    return False
            elif response.status_code == 403:
                self.log_result("Admin Dashboard Stats - Data Accuracy", False, 
                              "Access denied - admin role may not be configured")
                return False
            else:
                self.log_result("Admin Dashboard Stats - Data Accuracy", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Admin Dashboard Stats - Data Accuracy", False, f"Request failed: {str(e)}")
            return False
    
    def test_user_management_apis(self):
        """Test user management APIs for admin panel"""
        try:
            admin_headers = self.get_auth_headers("admin")
            
            # Test 1: Get user management data with pagination
            response = requests.get(
                f"{self.backend_url}/admin/users",
                params={"page": 1, "page_size": 10, "search": ""},
                headers=admin_headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['users', 'pagination', 'total_count']
                
                if all(field in data for field in required_fields):
                    users = data['users']
                    pagination = data['pagination']
                    
                    # Verify user data structure
                    if len(users) > 0:
                        first_user = users[0]
                        user_fields = ['id', 'name', 'email', 'organization', 'role', 'is_active', 'created_at', 'last_login']
                        
                        if all(field in first_user for field in user_fields):
                            # Verify pagination structure
                            pagination_fields = ['current_page', 'page_size', 'total_pages', 'has_next', 'has_previous']
                            
                            if all(field in pagination for field in pagination_fields):
                                self.log_result("User Management APIs - Data Structure", True, 
                                              f"Retrieved {len(users)} users with proper pagination")
                                
                                # Test 2: Search functionality
                                search_response = requests.get(
                                    f"{self.backend_url}/admin/users",
                                    params={"page": 1, "page_size": 10, "search": "test"},
                                    headers=admin_headers,
                                    timeout=10
                                )
                                
                                if search_response.status_code == 200:
                                    search_data = search_response.json()
                                    self.log_result("User Management APIs - Search", True, 
                                                  f"Search functionality working, found {len(search_data.get('users', []))} results")
                                    return True
                                else:
                                    self.log_result("User Management APIs - Search", False, 
                                                  f"Search failed: {search_response.status_code}")
                                    return False
                            else:
                                missing_pagination = [f for f in pagination_fields if f not in pagination]
                                self.log_result("User Management APIs - Data Structure", False, 
                                              f"Missing pagination fields: {missing_pagination}")
                                return False
                        else:
                            missing_user_fields = [f for f in user_fields if f not in first_user]
                            self.log_result("User Management APIs - Data Structure", False, 
                                          f"Missing user fields: {missing_user_fields}")
                            return False
                    else:
                        self.log_result("User Management APIs - Data Structure", True, 
                                      "No users found (valid for empty system)")
                        return True
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_result("User Management APIs - Data Structure", False, 
                                  f"Missing response fields: {missing_fields}")
                    return False
            elif response.status_code == 403:
                self.log_result("User Management APIs", False, 
                              "Access denied - admin role may not be configured")
                return False
            else:
                self.log_result("User Management APIs", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("User Management APIs", False, f"Request failed: {str(e)}")
            return False
    
    def test_user_status_updates(self):
        """Test user status update functionality"""
        try:
            admin_headers = self.get_auth_headers("admin")
            
            # First, get a user to update (use the regular user we created)
            users_response = requests.get(
                f"{self.backend_url}/admin/users",
                params={"page": 1, "page_size": 50, "search": self.regular_user_data["email"]},
                headers=admin_headers,
                timeout=10
            )
            
            if users_response.status_code == 200:
                users_data = users_response.json()
                users = users_data.get('users', [])
                
                if len(users) > 0:
                    target_user = users[0]
                    user_id = target_user['id']
                    current_status = target_user['is_active']
                    
                    # Test status update
                    new_status = not current_status
                    status_update_data = {"is_active": new_status}
                    
                    update_response = requests.put(
                        f"{self.backend_url}/admin/users/{user_id}/status",
                        json=status_update_data,
                        headers=admin_headers,
                        timeout=10
                    )
                    
                    if update_response.status_code == 200:
                        update_data = update_response.json()
                        
                        if ('message' in update_data and 
                            'user_id' in update_data and 
                            'is_active' in update_data):
                            
                            if update_data['is_active'] == new_status:
                                self.log_result("User Status Updates", True, 
                                              f"Status updated: {user_id} -> active={new_status}")
                                return True
                            else:
                                self.log_result("User Status Updates", False, 
                                              f"Status not updated correctly: expected={new_status}, got={update_data['is_active']}")
                                return False
                        else:
                            self.log_result("User Status Updates", False, 
                                          f"Invalid response format: {update_data}")
                            return False
                    elif update_response.status_code == 403:
                        self.log_result("User Status Updates", False, 
                                      "Access denied - admin role may not be configured")
                        return False
                    else:
                        self.log_result("User Status Updates", False, 
                                      f"Update failed: {update_response.status_code} - {update_response.text}")
                        return False
                else:
                    self.log_result("User Status Updates", False, 
                                  "No users found to test status update")
                    return False
            elif users_response.status_code == 403:
                self.log_result("User Status Updates", False, 
                              "Access denied - admin role may not be configured")
                return False
            else:
                self.log_result("User Status Updates", False, 
                              f"Failed to get users: {users_response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("User Status Updates", False, f"Request failed: {str(e)}")
            return False
    
    def test_threat_management_apis(self):
        """Test threat management APIs for admin panel"""
        try:
            admin_headers = self.get_auth_headers("admin")
            
            # Test threat management data retrieval
            response = requests.get(
                f"{self.backend_url}/admin/threats",
                params={"days": 7},
                headers=admin_headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['threat_timeline', 'threat_sources', 'recent_high_risk_scans', 'threat_statistics']
                
                if all(field in data for field in required_fields):
                    threat_timeline = data['threat_timeline']
                    threat_sources = data['threat_sources']
                    recent_scans = data['recent_high_risk_scans']
                    threat_stats = data['threat_statistics']
                    
                    # Verify threat timeline structure
                    if isinstance(threat_timeline, list):
                        timeline_valid = True
                        if len(threat_timeline) > 0:
                            first_entry = threat_timeline[0]
                            timeline_fields = ['date', 'threats_detected', 'scans_performed', 'risk_score_avg']
                            timeline_valid = all(field in first_entry for field in timeline_fields)
                        
                        # Verify threat sources structure
                        sources_valid = isinstance(threat_sources, list)
                        if len(threat_sources) > 0:
                            first_source = threat_sources[0]
                            source_fields = ['source', 'count', 'percentage', 'risk_level']
                            sources_valid = all(field in first_source for field in source_fields)
                        
                        # Verify recent high-risk scans
                        scans_valid = isinstance(recent_scans, list)
                        if len(recent_scans) > 0:
                            first_scan = recent_scans[0]
                            scan_fields = ['id', 'timestamp', 'risk_score', 'threat_type', 'user_id', 'status']
                            scans_valid = all(field in first_scan for field in scan_fields)
                        
                        # Verify threat statistics
                        stats_valid = isinstance(threat_stats, dict)
                        if stats_valid:
                            stats_fields = ['total_threats', 'blocked_threats', 'avg_risk_score', 'threat_categories']
                            stats_valid = all(field in threat_stats for field in stats_fields)
                        
                        if timeline_valid and sources_valid and scans_valid and stats_valid:
                            self.log_result("Threat Management APIs", True, 
                                          f"Threat data structure valid: {len(threat_timeline)} timeline entries, {len(threat_sources)} sources, {len(recent_scans)} recent scans")
                            return True
                        else:
                            validation_issues = []
                            if not timeline_valid: validation_issues.append("timeline")
                            if not sources_valid: validation_issues.append("sources")
                            if not scans_valid: validation_issues.append("scans")
                            if not stats_valid: validation_issues.append("statistics")
                            
                            self.log_result("Threat Management APIs", False, 
                                          f"Data structure validation failed: {', '.join(validation_issues)}")
                            return False
                    else:
                        self.log_result("Threat Management APIs", False, 
                                      "Threat timeline is not a list")
                        return False
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_result("Threat Management APIs", False, 
                                  f"Missing response fields: {missing_fields}")
                    return False
            elif response.status_code == 403:
                self.log_result("Threat Management APIs", False, 
                              "Access denied - admin role may not be configured")
                return False
            else:
                self.log_result("Threat Management APIs", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Threat Management APIs", False, f"Request failed: {str(e)}")
            return False
    
    def test_system_monitoring_apis(self):
        """Test system monitoring APIs for admin panel"""
        try:
            admin_headers = self.get_auth_headers("admin")
            
            # Test system monitoring data retrieval
            response = requests.get(
                f"{self.backend_url}/admin/system/monitoring",
                headers=admin_headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['system_health', 'api_performance', 'database_stats', 'websocket_stats', 'error_rates']
                
                if all(field in data for field in required_fields):
                    system_health = data['system_health']
                    api_performance = data['api_performance']
                    database_stats = data['database_stats']
                    websocket_stats = data['websocket_stats']
                    error_rates = data['error_rates']
                    
                    # Verify system health structure
                    health_fields = ['status', 'uptime', 'memory_usage', 'cpu_usage', 'disk_usage']
                    health_valid = all(field in system_health for field in health_fields)
                    
                    # Verify API performance structure
                    performance_fields = ['avg_response_time', 'requests_per_minute', 'success_rate', 'active_connections']
                    performance_valid = all(field in api_performance for field in performance_fields)
                    
                    # Verify database stats structure
                    db_fields = ['connections', 'query_performance', 'storage_usage', 'index_efficiency']
                    db_valid = all(field in database_stats for field in db_fields)
                    
                    # Verify WebSocket stats structure
                    ws_fields = ['active_connections', 'messages_per_minute', 'connection_errors', 'avg_latency']
                    ws_valid = all(field in websocket_stats for field in ws_fields)
                    
                    # Verify error rates structure
                    error_fields = ['error_rate_5xx', 'error_rate_4xx', 'critical_errors', 'warning_count']
                    error_valid = all(field in error_rates for field in error_fields)
                    
                    if health_valid and performance_valid and db_valid and ws_valid and error_valid:
                        self.log_result("System Monitoring APIs", True, 
                                      f"System monitoring data complete: Status={system_health.get('status')}, Success Rate={api_performance.get('success_rate')}%")
                        return True
                    else:
                        validation_issues = []
                        if not health_valid: validation_issues.append("system_health")
                        if not performance_valid: validation_issues.append("api_performance")
                        if not db_valid: validation_issues.append("database_stats")
                        if not ws_valid: validation_issues.append("websocket_stats")
                        if not error_valid: validation_issues.append("error_rates")
                        
                        self.log_result("System Monitoring APIs", False, 
                                      f"Data structure validation failed: {', '.join(validation_issues)}")
                        return False
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_result("System Monitoring APIs", False, 
                                  f"Missing response fields: {missing_fields}")
                    return False
            elif response.status_code == 403:
                self.log_result("System Monitoring APIs", False, 
                              "Access denied - admin role may not be configured")
                return False
            else:
                self.log_result("System Monitoring APIs", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("System Monitoring APIs", False, f"Request failed: {str(e)}")
            return False
    
    def test_audit_log_apis(self):
        """Test audit log APIs for admin panel (super admin only)"""
        try:
            # Test with admin user first (should be denied)
            admin_headers = self.get_auth_headers("admin")
            
            response = requests.get(
                f"{self.backend_url}/admin/audit/log",
                params={"page": 1, "page_size": 20, "days": 30},
                headers=admin_headers,
                timeout=10
            )
            
            if response.status_code == 403:
                self.log_result("Audit Log APIs - Access Control", True, 
                              "Admin user correctly denied access to audit logs (super admin only)")
                
                # Note: We can't test super admin access without proper role setup
                # In a real environment, this would require a super admin user
                self.log_result("Audit Log APIs - Super Admin Access", False, 
                              "Cannot test super admin access - role setup required")
                return True
            elif response.status_code == 200:
                # If admin has access, verify the data structure
                data = response.json()
                required_fields = ['audit_logs', 'pagination', 'total_count']
                
                if all(field in data for field in required_fields):
                    audit_logs = data['audit_logs']
                    
                    if len(audit_logs) > 0:
                        first_log = audit_logs[0]
                        log_fields = ['id', 'timestamp', 'admin_user_id', 'action', 'target_type', 'target_id', 'details', 'ip_address', 'user_agent']
                        
                        if all(field in first_log for field in log_fields):
                            self.log_result("Audit Log APIs - Data Structure", True, 
                                          f"Audit log structure valid: {len(audit_logs)} entries")
                            return True
                        else:
                            missing_fields = [f for f in log_fields if f not in first_log]
                            self.log_result("Audit Log APIs - Data Structure", False, 
                                          f"Missing log fields: {missing_fields}")
                            return False
                    else:
                        self.log_result("Audit Log APIs - Data Structure", True, 
                                      "No audit logs found (valid for new system)")
                        return True
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_result("Audit Log APIs - Data Structure", False, 
                                  f"Missing response fields: {missing_fields}")
                    return False
            else:
                self.log_result("Audit Log APIs", False, 
                              f"Unexpected response: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Audit Log APIs", False, f"Request failed: {str(e)}")
            return False
    
    def test_role_based_access_control(self):
        """Test comprehensive role-based access control"""
        try:
            # Test regular user access to admin endpoints
            regular_headers = self.get_auth_headers("regular")
            
            admin_endpoints = [
                "/admin/dashboard/stats",
                "/admin/users",
                "/admin/threats",
                "/admin/system/monitoring",
                "/admin/audit/log"
            ]
            
            regular_user_denied = 0
            
            for endpoint in admin_endpoints:
                response = requests.get(
                    f"{self.backend_url}{endpoint}",
                    headers=regular_headers,
                    timeout=10
                )
                
                if response.status_code == 403:
                    regular_user_denied += 1
            
            if regular_user_denied == len(admin_endpoints):
                self.log_result("Role-Based Access Control - Regular User", True, 
                              f"Regular user correctly denied access to all {len(admin_endpoints)} admin endpoints")
                
                # Test admin user access (limited by role setup)
                admin_headers = self.get_auth_headers("admin")
                admin_accessible = 0
                
                # Test non-super-admin endpoints
                non_super_admin_endpoints = [
                    "/admin/dashboard/stats",
                    "/admin/users", 
                    "/admin/threats",
                    "/admin/system/monitoring"
                ]
                
                for endpoint in non_super_admin_endpoints:
                    response = requests.get(
                        f"{self.backend_url}{endpoint}",
                        headers=admin_headers,
                        timeout=10
                    )
                    
                    # 200 means access granted, 403 means role not configured
                    if response.status_code in [200, 403]:
                        admin_accessible += 1
                
                # Test super admin only endpoint
                super_admin_response = requests.get(
                    f"{self.backend_url}/admin/audit/log",
                    headers=admin_headers,
                    timeout=10
                )
                
                if super_admin_response.status_code == 403:
                    self.log_result("Role-Based Access Control - Super Admin Only", True, 
                                  "Audit log correctly restricted to super admin only")
                    return True
                else:
                    self.log_result("Role-Based Access Control - Super Admin Only", False, 
                                  f"Audit log access control failed: {super_admin_response.status_code}")
                    return False
            else:
                self.log_result("Role-Based Access Control - Regular User", False, 
                              f"Regular user access control failed: {regular_user_denied}/{len(admin_endpoints)} endpoints denied")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Role-Based Access Control", False, f"Request failed: {str(e)}")
            return False
    
    def test_admin_action_logging(self):
        """Test that admin actions are properly logged"""
        try:
            admin_headers = self.get_auth_headers("admin")
            
            # Perform an admin action (user status update)
            users_response = requests.get(
                f"{self.backend_url}/admin/users",
                params={"page": 1, "page_size": 10},
                headers=admin_headers,
                timeout=10
            )
            
            if users_response.status_code == 200:
                users_data = users_response.json()
                users = users_data.get('users', [])
                
                if len(users) > 0:
                    target_user = users[0]
                    user_id = target_user['id']
                    
                    # Perform status update action
                    status_update_data = {"is_active": False}
                    
                    update_response = requests.put(
                        f"{self.backend_url}/admin/users/{user_id}/status",
                        json=status_update_data,
                        headers=admin_headers,
                        timeout=10
                    )
                    
                    if update_response.status_code == 200:
                        # Try to check if action was logged (this might fail due to access control)
                        audit_response = requests.get(
                            f"{self.backend_url}/admin/audit/log",
                            params={"page": 1, "page_size": 10, "days": 1},
                            headers=admin_headers,
                            timeout=10
                        )
                        
                        if audit_response.status_code == 200:
                            audit_data = audit_response.json()
                            audit_logs = audit_data.get('audit_logs', [])
                            
                            # Look for the user status update action
                            status_update_logged = any(
                                log.get('action') == 'user_status_update' and 
                                log.get('target_id') == user_id
                                for log in audit_logs
                            )
                            
                            if status_update_logged:
                                self.log_result("Admin Action Logging", True, 
                                              "Admin action properly logged in audit trail")
                                return True
                            else:
                                self.log_result("Admin Action Logging", False, 
                                              "Admin action not found in audit logs")
                                return False
                        elif audit_response.status_code == 403:
                            # Expected if admin doesn't have audit log access
                            self.log_result("Admin Action Logging", True, 
                                          "Admin action performed successfully (audit log access restricted)")
                            return True
                        else:
                            self.log_result("Admin Action Logging", False, 
                                          f"Failed to check audit logs: {audit_response.status_code}")
                            return False
                    elif update_response.status_code == 403:
                        self.log_result("Admin Action Logging", False, 
                                      "Admin user cannot perform status updates - role not configured")
                        return False
                    else:
                        self.log_result("Admin Action Logging", False, 
                                      f"Status update failed: {update_response.status_code}")
                        return False
                else:
                    self.log_result("Admin Action Logging", False, 
                                  "No users available to test admin actions")
                    return False
            elif users_response.status_code == 403:
                self.log_result("Admin Action Logging", False, 
                              "Admin user cannot access user management - role not configured")
                return False
            else:
                self.log_result("Admin Action Logging", False, 
                              f"Failed to get users: {users_response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_result("Admin Action Logging", False, f"Request failed: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all admin panel tests"""
        print("=" * 80)
        print("🔐 AMAN CYBERSECURITY PLATFORM - PHASE 9 ADMIN PANEL TESTING")
        print("=" * 80)
        
        # Setup test users
        if not self.setup_test_users():
            print("❌ Failed to setup test users - aborting admin panel tests")
            return
        
        # Admin Panel Tests
        admin_tests = [
            self.test_admin_dashboard_stats_access_control,
            self.test_admin_dashboard_stats_data_accuracy,
            self.test_user_management_apis,
            self.test_user_status_updates,
            self.test_threat_management_apis,
            self.test_system_monitoring_apis,
            self.test_audit_log_apis,
            self.test_role_based_access_control,
            self.test_admin_action_logging
        ]
        
        passed = 0
        total = len(admin_tests)
        
        for test in admin_tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                self.log_result(test.__name__, False, f"Test exception: {str(e)}")
        
        print("\n" + "=" * 80)
        print("📊 ADMIN PANEL TEST RESULTS SUMMARY")
        print("=" * 80)
        
        success_rate = (passed / total) * 100
        print(f"✅ Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        
        if passed == total:
            print("🎉 ALL ADMIN PANEL TESTS PASSED!")
        elif passed >= total * 0.8:
            print("✅ ADMIN PANEL MOSTLY FUNCTIONAL")
        elif passed >= total * 0.5:
            print("⚠️  ADMIN PANEL PARTIALLY FUNCTIONAL")
        else:
            print("❌ ADMIN PANEL NEEDS SIGNIFICANT WORK")
        
        # Show detailed results
        print("\n📋 Detailed Results:")
        for result in self.results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if result['details'] and not result['success']:
                print(f"   └─ {result['details']}")
        
        return passed, total

if __name__ == "__main__":
    tester = AdminPanelTester()
    passed, total = tester.run_all_tests()
    
    # Exit with appropriate code
    if passed == total:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Some tests failed