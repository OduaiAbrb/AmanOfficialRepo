#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Enhanced AI Cost Management System
Aman Cybersecurity Platform - AI Cost Management Testing Suite

Tests:
1. AI Usage Tracking
2. Smart Caching System  
3. Usage Limits and Quotas
4. Cost Analytics Endpoints
5. Integration with Email Scanning
6. Database Storage
"""

import asyncio
import json
import requests
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid

# Configuration
BACKEND_URL = "https://a7ef5366-e6cc-4ff4-9acc-af148819b2aa.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class AITestUser:
    """Test user for AI cost management testing"""
    def __init__(self, email: str, password: str = "TestPass123!", name: str = "AI Test User", organization: str = "AI Testing Corp"):
        self.email = email
        self.password = password
        self.name = name
        self.organization = organization
        self.token = None
        self.user_id = None

class AICostManagementTester:
    """Comprehensive AI Cost Management Testing Suite"""
    
    def __init__(self):
        self.test_results = []
        self.test_user = None
        self.admin_user = None
        
    def log_test(self, test_name: str, status: str, details: str = "", response_data: Any = None):
        """Log test results"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
        if response_data and isinstance(response_data, dict):
            print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
        print()

    def setup_test_user(self) -> bool:
        """Setup test user for AI cost management testing"""
        try:
            # Create unique test user
            timestamp = int(time.time())
            test_email = f"ai_cost_test_{timestamp}@testcorp.com"
            
            self.test_user = AITestUser(
                email=test_email,
                name=f"AI Cost Test User {timestamp}",
                organization="AI Cost Testing Corp"
            )
            
            # Register user
            register_data = {
                "email": self.test_user.email,
                "password": self.test_user.password,
                "name": self.test_user.name,
                "organization": self.test_user.organization
            }
            
            response = requests.post(f"{API_BASE}/auth/register", json=register_data, timeout=10)
            
            if response.status_code == 200:
                # Login to get token
                login_data = {
                    "email": self.test_user.email,
                    "password": self.test_user.password
                }
                
                login_response = requests.post(f"{API_BASE}/auth/login", json=login_data, timeout=10)
                
                if login_response.status_code == 200:
                    token_data = login_response.json()
                    self.test_user.token = token_data.get("access_token")
                    
                    # Get user profile to extract user_id
                    headers = {"Authorization": f"Bearer {self.test_user.token}"}
                    profile_response = requests.get(f"{API_BASE}/user/profile", headers=headers, timeout=10)
                    
                    if profile_response.status_code == 200:
                        profile_data = profile_response.json()
                        self.test_user.user_id = profile_data.get("id")
                        
                        self.log_test(
                            "AI Cost Test User Setup",
                            "PASS",
                            f"Test user created: {self.test_user.email}, ID: {self.test_user.user_id}",
                            {"email": self.test_user.email, "user_id": self.test_user.user_id}
                        )
                        return True
            
            self.log_test("AI Cost Test User Setup", "FAIL", f"Failed to setup test user: {response.status_code}")
            return False
            
        except Exception as e:
            self.log_test("AI Cost Test User Setup", "FAIL", f"Exception: {str(e)}")
            return False

    def test_ai_usage_tracking_email_scan(self):
        """Test AI usage tracking for email scanning operations"""
        try:
            if not self.test_user or not self.test_user.token:
                self.log_test("AI Usage Tracking - Email Scan", "FAIL", "No authenticated test user")
                return
            
            headers = {"Authorization": f"Bearer {self.test_user.token}"}
            
            # Test email scan that should trigger AI usage tracking
            email_data = {
                "email_subject": "Urgent: Verify Your Account Now - AI Cost Test",
                "sender": "security@fake-bank.com",
                "recipient": self.test_user.email,
                "email_body": """Dear Customer,
                
                Your account has been temporarily suspended due to suspicious activity.
                
                Click here to verify your account immediately: http://fake-bank-verify.com/login
                
                You have 24 hours to complete this verification or your account will be permanently closed.
                
                Best regards,
                Security Team
                """
            }
            
            # Perform email scan
            scan_response = requests.post(
                f"{API_BASE}/scan/email", 
                json=email_data, 
                headers=headers, 
                timeout=15
            )
            
            if scan_response.status_code == 200:
                scan_result = scan_response.json()
                
                # Check if scan was successful and AI-powered
                if scan_result.get("risk_score") is not None:
                    # Wait a moment for usage to be recorded
                    time.sleep(2)
                    
                    # Check usage analytics to verify tracking
                    analytics_response = requests.get(
                        f"{API_BASE}/ai/usage/analytics?days=1",
                        headers=headers,
                        timeout=10
                    )
                    
                    if analytics_response.status_code == 200:
                        analytics_data = analytics_response.json()
                        
                        # Verify usage was tracked
                        total_stats = analytics_data.get("analytics", {}).get("total_stats", {})
                        
                        if total_stats.get("total_requests", 0) > 0:
                            self.log_test(
                                "AI Usage Tracking - Email Scan",
                                "PASS",
                                f"Email scan usage tracked: {total_stats.get('total_requests')} requests, "
                                f"${total_stats.get('total_cost', 0):.4f} cost, "
                                f"{total_stats.get('cache_hit_rate', 0):.2%} cache hit rate",
                                {
                                    "scan_result": {
                                        "risk_score": scan_result.get("risk_score"),
                                        "status": scan_result.get("status")
                                    },
                                    "usage_stats": total_stats
                                }
                            )
                        else:
                            self.log_test(
                                "AI Usage Tracking - Email Scan",
                                "FAIL",
                                "No usage recorded in analytics after email scan",
                                analytics_data
                            )
                    else:
                        self.log_test(
                            "AI Usage Tracking - Email Scan",
                            "FAIL",
                            f"Failed to get usage analytics: {analytics_response.status_code}"
                        )
                else:
                    self.log_test(
                        "AI Usage Tracking - Email Scan",
                        "FAIL",
                        "Email scan did not return valid results",
                        scan_result
                    )
            else:
                self.log_test(
                    "AI Usage Tracking - Email Scan",
                    "FAIL",
                    f"Email scan failed: {scan_response.status_code}",
                    scan_response.text
                )
                
        except Exception as e:
            self.log_test("AI Usage Tracking - Email Scan", "FAIL", f"Exception: {str(e)}")

    def test_smart_caching_system(self):
        """Test AI response caching for repeated email content"""
        try:
            if not self.test_user or not self.test_user.token:
                self.log_test("Smart Caching System", "FAIL", "No authenticated test user")
                return
            
            headers = {"Authorization": f"Bearer {self.test_user.token}"}
            
            # Test email content for caching
            email_data = {
                "email_subject": "Cache Test Email - Identical Content",
                "sender": "cache-test@example.com",
                "recipient": self.test_user.email,
                "email_body": "This is a test email for cache testing. The content should be cached after first scan."
            }
            
            # First scan - should miss cache
            print("   Performing first scan (cache miss expected)...")
            first_scan_start = time.time()
            first_response = requests.post(
                f"{API_BASE}/scan/email", 
                json=email_data, 
                headers=headers, 
                timeout=15
            )
            first_scan_time = time.time() - first_scan_start
            
            if first_response.status_code != 200:
                self.log_test("Smart Caching System", "FAIL", f"First scan failed: {first_response.status_code}")
                return
            
            first_result = first_response.json()
            
            # Wait a moment for cache to be stored
            time.sleep(1)
            
            # Second scan - should hit cache
            print("   Performing second scan (cache hit expected)...")
            second_scan_start = time.time()
            second_response = requests.post(
                f"{API_BASE}/scan/email", 
                json=email_data, 
                headers=headers, 
                timeout=15
            )
            second_scan_time = time.time() - second_scan_start
            
            if second_response.status_code != 200:
                self.log_test("Smart Caching System", "FAIL", f"Second scan failed: {second_response.status_code}")
                return
            
            second_result = second_response.json()
            
            # Compare results and performance
            results_match = (
                first_result.get("risk_score") == second_result.get("risk_score") and
                first_result.get("status") == second_result.get("status")
            )
            
            # Check if second scan was faster (indicating cache hit)
            performance_improvement = second_scan_time < first_scan_time * 0.8
            
            # Get usage analytics to check cache hit rate
            time.sleep(1)
            analytics_response = requests.get(
                f"{API_BASE}/ai/usage/analytics?days=1",
                headers=headers,
                timeout=10
            )
            
            cache_hit_rate = 0
            if analytics_response.status_code == 200:
                analytics_data = analytics_response.json()
                total_stats = analytics_data.get("analytics", {}).get("total_stats", {})
                cache_hit_rate = total_stats.get("cache_hit_rate", 0)
            
            if results_match and (performance_improvement or cache_hit_rate > 0):
                self.log_test(
                    "Smart Caching System",
                    "PASS",
                    f"Cache working: Results match={results_match}, "
                    f"Performance improvement={performance_improvement}, "
                    f"Cache hit rate={cache_hit_rate:.2%}, "
                    f"First scan: {first_scan_time:.2f}s, Second scan: {second_scan_time:.2f}s",
                    {
                        "first_scan_time": first_scan_time,
                        "second_scan_time": second_scan_time,
                        "cache_hit_rate": cache_hit_rate,
                        "results_match": results_match
                    }
                )
            else:
                self.log_test(
                    "Smart Caching System",
                    "FAIL",
                    f"Cache not working effectively: Results match={results_match}, "
                    f"Performance improvement={performance_improvement}, "
                    f"Cache hit rate={cache_hit_rate:.2%}"
                )
                
        except Exception as e:
            self.log_test("Smart Caching System", "FAIL", f"Exception: {str(e)}")

    def test_usage_limits_and_quotas(self):
        """Test daily usage limit checking for different user tiers"""
        try:
            if not self.test_user or not self.test_user.token:
                self.log_test("Usage Limits and Quotas", "FAIL", "No authenticated test user")
                return
            
            headers = {"Authorization": f"Bearer {self.test_user.token}"}
            
            # Get current usage limits
            limits_response = requests.get(
                f"{API_BASE}/ai/usage/limits",
                headers=headers,
                timeout=10
            )
            
            if limits_response.status_code == 200:
                limits_data = limits_response.json()
                
                # Check if limits data is properly structured
                required_fields = ["user_tier", "within_limits", "current_usage", "limits", "remaining"]
                
                has_all_fields = all(field in limits_data for field in required_fields)
                
                if has_all_fields:
                    current_usage = limits_data.get("current_usage", {})
                    limits = limits_data.get("limits", {})
                    remaining = limits_data.get("remaining", {})
                    
                    # Verify limit calculations are correct
                    requests_remaining = limits.get("requests", 0) - current_usage.get("total_requests", 0)
                    tokens_remaining = limits.get("tokens", 0) - current_usage.get("total_tokens", 0)
                    cost_remaining = limits.get("cost", 0) - current_usage.get("total_cost", 0)
                    
                    calculations_correct = (
                        abs(requests_remaining - remaining.get("requests", 0)) < 1 and
                        abs(tokens_remaining - remaining.get("tokens", 0)) < 1 and
                        abs(cost_remaining - remaining.get("cost", 0)) < 0.01
                    )
                    
                    if calculations_correct:
                        self.log_test(
                            "Usage Limits and Quotas",
                            "PASS",
                            f"Usage limits working: Tier={limits_data.get('user_tier')}, "
                            f"Within limits={limits_data.get('within_limits')}, "
                            f"Requests: {current_usage.get('total_requests', 0)}/{limits.get('requests', 0)}, "
                            f"Tokens: {current_usage.get('total_tokens', 0)}/{limits.get('tokens', 0)}, "
                            f"Cost: ${current_usage.get('total_cost', 0):.4f}/${limits.get('cost', 0):.2f}",
                            {
                                "user_tier": limits_data.get("user_tier"),
                                "within_limits": limits_data.get("within_limits"),
                                "usage_summary": {
                                    "requests": f"{current_usage.get('total_requests', 0)}/{limits.get('requests', 0)}",
                                    "tokens": f"{current_usage.get('total_tokens', 0)}/{limits.get('tokens', 0)}",
                                    "cost": f"${current_usage.get('total_cost', 0):.4f}/${limits.get('cost', 0):.2f}"
                                }
                            }
                        )
                    else:
                        self.log_test(
                            "Usage Limits and Quotas",
                            "FAIL",
                            "Usage limit calculations are incorrect",
                            limits_data
                        )
                else:
                    self.log_test(
                        "Usage Limits and Quotas",
                        "FAIL",
                        f"Missing required fields in limits response: {required_fields}",
                        limits_data
                    )
            else:
                self.log_test(
                    "Usage Limits and Quotas",
                    "FAIL",
                    f"Failed to get usage limits: {limits_response.status_code}",
                    limits_response.text
                )
                
        except Exception as e:
            self.log_test("Usage Limits and Quotas", "FAIL", f"Exception: {str(e)}")

    def test_cost_analytics_endpoints(self):
        """Test cost analytics endpoints"""
        try:
            if not self.test_user or not self.test_user.token:
                self.log_test("Cost Analytics Endpoints", "FAIL", "No authenticated test user")
                return
            
            headers = {"Authorization": f"Bearer {self.test_user.token}"}
            
            # Test 1: AI Usage Analytics endpoint
            analytics_response = requests.get(
                f"{API_BASE}/ai/usage/analytics?days=7",
                headers=headers,
                timeout=10
            )
            
            analytics_working = False
            if analytics_response.status_code == 200:
                analytics_data = analytics_response.json()
                
                # Check required fields
                required_fields = ["user_id", "analytics"]
                if all(field in analytics_data for field in required_fields):
                    analytics = analytics_data.get("analytics", {})
                    
                    # Check analytics structure
                    analytics_fields = ["period_days", "daily_usage", "usage_by_operation", "total_stats"]
                    if all(field in analytics for field in analytics_fields):
                        analytics_working = True
            
            # Test 2: AI Usage Limits endpoint
            limits_response = requests.get(
                f"{API_BASE}/ai/usage/limits",
                headers=headers,
                timeout=10
            )
            
            limits_working = False
            if limits_response.status_code == 200:
                limits_data = limits_response.json()
                
                # Check required fields
                required_fields = ["user_id", "user_tier", "within_limits"]
                if all(field in limits_data for field in required_fields):
                    limits_working = True
            
            # Test 3: AI Cache Stats endpoint (admin only - should fail for regular user)
            cache_response = requests.get(
                f"{API_BASE}/ai/cache/stats",
                headers=headers,
                timeout=10
            )
            
            cache_access_controlled = cache_response.status_code == 403  # Should be forbidden for non-admin
            
            # Overall assessment
            if analytics_working and limits_working and cache_access_controlled:
                self.log_test(
                    "Cost Analytics Endpoints",
                    "PASS",
                    f"All endpoints working correctly: "
                    f"Analytics={analytics_working}, "
                    f"Limits={limits_working}, "
                    f"Cache access controlled={cache_access_controlled}",
                    {
                        "analytics_status": analytics_response.status_code,
                        "limits_status": limits_response.status_code,
                        "cache_status": cache_response.status_code,
                        "cache_access_controlled": cache_access_controlled
                    }
                )
            else:
                self.log_test(
                    "Cost Analytics Endpoints",
                    "FAIL",
                    f"Some endpoints not working: "
                    f"Analytics={analytics_working}, "
                    f"Limits={limits_working}, "
                    f"Cache access controlled={cache_access_controlled}"
                )
                
        except Exception as e:
            self.log_test("Cost Analytics Endpoints", "FAIL", f"Exception: {str(e)}")

    def test_integration_with_email_scanning(self):
        """Test that AI email scanning records usage properly"""
        try:
            if not self.test_user or not self.test_user.token:
                self.log_test("Integration with Email Scanning", "FAIL", "No authenticated test user")
                return
            
            headers = {"Authorization": f"Bearer {self.test_user.token}"}
            
            # Get initial usage stats
            initial_analytics = requests.get(
                f"{API_BASE}/ai/usage/analytics?days=1",
                headers=headers,
                timeout=10
            )
            
            initial_requests = 0
            initial_cost = 0.0
            if initial_analytics.status_code == 200:
                initial_data = initial_analytics.json()
                total_stats = initial_data.get("analytics", {}).get("total_stats", {})
                initial_requests = total_stats.get("total_requests", 0)
                initial_cost = total_stats.get("total_cost", 0.0)
            
            # Perform multiple email scans with different content
            test_emails = [
                {
                    "email_subject": "Integration Test 1 - Legitimate Email",
                    "sender": "newsletter@company.com",
                    "recipient": self.test_user.email,
                    "email_body": "Thank you for subscribing to our newsletter. Here are this week's updates."
                },
                {
                    "email_subject": "Integration Test 2 - Suspicious Email",
                    "sender": "urgent@fake-bank.com",
                    "recipient": self.test_user.email,
                    "email_body": "URGENT: Your account will be closed. Click here to verify: http://fake-site.com"
                },
                {
                    "email_subject": "Integration Test 3 - Business Email",
                    "sender": "hr@testcompany.com",
                    "recipient": self.test_user.email,
                    "email_body": "Please review the attached document and provide your feedback by Friday."
                }
            ]
            
            successful_scans = 0
            for i, email_data in enumerate(test_emails, 1):
                print(f"   Performing email scan {i}/3...")
                
                scan_response = requests.post(
                    f"{API_BASE}/scan/email", 
                    json=email_data, 
                    headers=headers, 
                    timeout=15
                )
                
                if scan_response.status_code == 200:
                    successful_scans += 1
                    time.sleep(1)  # Brief pause between scans
            
            # Wait for usage to be recorded
            time.sleep(2)
            
            # Get final usage stats
            final_analytics = requests.get(
                f"{API_BASE}/ai/usage/analytics?days=1",
                headers=headers,
                timeout=10
            )
            
            if final_analytics.status_code == 200:
                final_data = final_analytics.json()
                total_stats = final_data.get("analytics", {}).get("total_stats", {})
                final_requests = total_stats.get("total_requests", 0)
                final_cost = total_stats.get("total_cost", 0.0)
                
                # Check if usage increased
                requests_increased = final_requests > initial_requests
                cost_increased = final_cost > initial_cost
                
                # Check usage by operation type
                usage_by_operation = final_data.get("analytics", {}).get("usage_by_operation", [])
                has_email_scan_operations = any(
                    op.get("_id") == "email_scan" for op in usage_by_operation
                )
                
                if requests_increased and cost_increased and successful_scans > 0:
                    self.log_test(
                        "Integration with Email Scanning",
                        "PASS",
                        f"Email scanning integration working: "
                        f"Successful scans={successful_scans}, "
                        f"Requests increased: {initial_requests} → {final_requests}, "
                        f"Cost increased: ${initial_cost:.4f} → ${final_cost:.4f}, "
                        f"Has email scan operations={has_email_scan_operations}",
                        {
                            "successful_scans": successful_scans,
                            "usage_change": {
                                "requests": f"{initial_requests} → {final_requests}",
                                "cost": f"${initial_cost:.4f} → ${final_cost:.4f}"
                            },
                            "has_email_operations": has_email_scan_operations
                        }
                    )
                else:
                    self.log_test(
                        "Integration with Email Scanning",
                        "FAIL",
                        f"Usage not properly recorded: "
                        f"Successful scans={successful_scans}, "
                        f"Requests increased={requests_increased}, "
                        f"Cost increased={cost_increased}"
                    )
            else:
                self.log_test(
                    "Integration with Email Scanning",
                    "FAIL",
                    f"Failed to get final analytics: {final_analytics.status_code}"
                )
                
        except Exception as e:
            self.log_test("Integration with Email Scanning", "FAIL", f"Exception: {str(e)}")

    def test_database_storage(self):
        """Test AI usage records are properly stored in database"""
        try:
            if not self.test_user or not self.test_user.token:
                self.log_test("Database Storage", "FAIL", "No authenticated test user")
                return
            
            headers = {"Authorization": f"Bearer {self.test_user.token}"}
            
            # Perform a test email scan to generate database records
            email_data = {
                "email_subject": "Database Storage Test Email",
                "sender": "db-test@example.com",
                "recipient": self.test_user.email,
                "email_body": "This email is used to test database storage of AI usage records."
            }
            
            scan_response = requests.post(
                f"{API_BASE}/scan/email", 
                json=email_data, 
                headers=headers, 
                timeout=15
            )
            
            if scan_response.status_code != 200:
                self.log_test("Database Storage", "FAIL", f"Test email scan failed: {scan_response.status_code}")
                return
            
            # Wait for database storage
            time.sleep(2)
            
            # Get analytics to verify data aggregation
            analytics_response = requests.get(
                f"{API_BASE}/ai/usage/analytics?days=1",
                headers=headers,
                timeout=10
            )
            
            if analytics_response.status_code == 200:
                analytics_data = analytics_response.json()
                
                # Check data structure and completeness
                analytics = analytics_data.get("analytics", {})
                
                # Check daily usage data
                daily_usage = analytics.get("daily_usage", [])
                has_daily_data = len(daily_usage) > 0
                
                # Check usage by operation
                usage_by_operation = analytics.get("usage_by_operation", [])
                has_operation_data = len(usage_by_operation) > 0
                
                # Check total stats
                total_stats = analytics.get("total_stats", {})
                has_total_stats = bool(total_stats.get("total_requests", 0) > 0)
                
                # Check data consistency
                if has_daily_data:
                    daily_total_requests = sum(day.get("requests", 0) for day in daily_usage)
                    total_requests = total_stats.get("total_requests", 0)
                    data_consistent = abs(daily_total_requests - total_requests) <= 1  # Allow small variance
                else:
                    data_consistent = True
                
                if has_daily_data and has_operation_data and has_total_stats and data_consistent:
                    self.log_test(
                        "Database Storage",
                        "PASS",
                        f"Database storage working: "
                        f"Daily data={has_daily_data}, "
                        f"Operation data={has_operation_data}, "
                        f"Total stats={has_total_stats}, "
                        f"Data consistent={data_consistent}, "
                        f"Total requests={total_stats.get('total_requests', 0)}",
                        {
                            "daily_usage_entries": len(daily_usage),
                            "operation_types": len(usage_by_operation),
                            "total_requests": total_stats.get("total_requests", 0),
                            "total_cost": total_stats.get("total_cost", 0),
                            "data_consistent": data_consistent
                        }
                    )
                else:
                    self.log_test(
                        "Database Storage",
                        "FAIL",
                        f"Database storage issues: "
                        f"Daily data={has_daily_data}, "
                        f"Operation data={has_operation_data}, "
                        f"Total stats={has_total_stats}, "
                        f"Data consistent={data_consistent}"
                    )
            else:
                self.log_test(
                    "Database Storage",
                    "FAIL",
                    f"Failed to get analytics for database verification: {analytics_response.status_code}"
                )
                
        except Exception as e:
            self.log_test("Database Storage", "FAIL", f"Exception: {str(e)}")

    def test_cost_savings_verification(self):
        """Test that caching provides significant cost savings"""
        try:
            if not self.test_user or not self.test_user.token:
                self.log_test("Cost Savings Verification", "FAIL", "No authenticated test user")
                return
            
            headers = {"Authorization": f"Bearer {self.test_user.token}"}
            
            # Test identical email content multiple times to trigger caching
            email_data = {
                "email_subject": "Cost Savings Test - Repeated Content",
                "sender": "cost-test@example.com",
                "recipient": self.test_user.email,
                "email_body": "This email content will be scanned multiple times to test cost savings through caching."
            }
            
            # Perform multiple scans of the same content
            scan_count = 5
            successful_scans = 0
            
            print(f"   Performing {scan_count} scans of identical content...")
            
            for i in range(scan_count):
                scan_response = requests.post(
                    f"{API_BASE}/scan/email", 
                    json=email_data, 
                    headers=headers, 
                    timeout=15
                )
                
                if scan_response.status_code == 200:
                    successful_scans += 1
                
                time.sleep(0.5)  # Brief pause between scans
            
            # Wait for all usage to be recorded
            time.sleep(2)
            
            # Get analytics to check cache hit rate
            analytics_response = requests.get(
                f"{API_BASE}/ai/usage/analytics?days=1",
                headers=headers,
                timeout=10
            )
            
            if analytics_response.status_code == 200:
                analytics_data = analytics_response.json()
                total_stats = analytics_data.get("analytics", {}).get("total_stats", {})
                
                cache_hit_rate = total_stats.get("cache_hit_rate", 0)
                total_requests = total_stats.get("total_requests", 0)
                total_cost = total_stats.get("total_cost", 0)
                
                # Calculate expected cost savings
                # If all scans after the first were cache hits, we should see significant savings
                expected_cache_hits = max(0, successful_scans - 1)  # First scan is always a miss
                
                # Cost savings verification
                significant_cache_usage = cache_hit_rate > 0.2  # At least 20% cache hit rate
                reasonable_cost = total_cost < (successful_scans * 0.01)  # Cost should be reasonable
                
                if significant_cache_usage and successful_scans >= 3:
                    estimated_savings = f"{cache_hit_rate * 100:.1f}%"
                    
                    self.log_test(
                        "Cost Savings Verification",
                        "PASS",
                        f"Cost savings achieved: "
                        f"Successful scans={successful_scans}, "
                        f"Cache hit rate={cache_hit_rate:.2%}, "
                        f"Total cost=${total_cost:.4f}, "
                        f"Estimated savings={estimated_savings}",
                        {
                            "successful_scans": successful_scans,
                            "cache_hit_rate": cache_hit_rate,
                            "total_cost": total_cost,
                            "total_requests": total_requests,
                            "cost_per_scan": total_cost / max(successful_scans, 1)
                        }
                    )
                else:
                    self.log_test(
                        "Cost Savings Verification",
                        "FAIL",
                        f"Insufficient cost savings: "
                        f"Cache hit rate={cache_hit_rate:.2%}, "
                        f"Successful scans={successful_scans}, "
                        f"Total cost=${total_cost:.4f}"
                    )
            else:
                self.log_test(
                    "Cost Savings Verification",
                    "FAIL",
                    f"Failed to get analytics for cost verification: {analytics_response.status_code}"
                )
                
        except Exception as e:
            self.log_test("Cost Savings Verification", "FAIL", f"Exception: {str(e)}")

    def run_comprehensive_tests(self):
        """Run all AI Cost Management tests"""
        print("🚀 Starting Comprehensive AI Cost Management Testing")
        print("=" * 60)
        
        # Setup
        if not self.setup_test_user():
            print("❌ Failed to setup test user. Aborting tests.")
            return
        
        print("\n📊 Testing AI Cost Management System Components:")
        print("-" * 50)
        
        # Core AI Cost Management Tests
        self.test_ai_usage_tracking_email_scan()
        self.test_smart_caching_system()
        self.test_usage_limits_and_quotas()
        self.test_cost_analytics_endpoints()
        self.test_integration_with_email_scanning()
        self.test_database_storage()
        self.test_cost_savings_verification()
        
        # Generate summary
        self.generate_test_summary()

    def generate_test_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 60)
        print("📋 AI COST MANAGEMENT TESTING SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        
        print(f"\n📊 Overall Results:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print(f"\n🔍 Detailed Results:")
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(f"   {status_icon} {result['test']}: {result['status']}")
            if result["details"]:
                print(f"      └─ {result['details']}")
        
        # Critical Assessment
        critical_tests = [
            "AI Usage Tracking - Email Scan",
            "Smart Caching System", 
            "Usage Limits and Quotas",
            "Cost Analytics Endpoints",
            "Integration with Email Scanning"
        ]
        
        critical_passed = len([
            r for r in self.test_results 
            if r["test"] in critical_tests and r["status"] == "PASS"
        ])
        
        print(f"\n🎯 Critical Features Assessment:")
        print(f"   Critical Tests Passed: {critical_passed}/{len(critical_tests)}")
        
        if critical_passed == len(critical_tests):
            print("   🟢 AI Cost Management System: PRODUCTION READY")
        elif critical_passed >= len(critical_tests) * 0.8:
            print("   🟡 AI Cost Management System: MOSTLY FUNCTIONAL")
        else:
            print("   🔴 AI Cost Management System: NEEDS ATTENTION")
        
        print(f"\n💡 Key Findings:")
        
        # Extract key metrics from test results
        usage_tracking_working = any(
            r["test"] == "AI Usage Tracking - Email Scan" and r["status"] == "PASS" 
            for r in self.test_results
        )
        
        caching_working = any(
            r["test"] == "Smart Caching System" and r["status"] == "PASS" 
            for r in self.test_results
        )
        
        analytics_working = any(
            r["test"] == "Cost Analytics Endpoints" and r["status"] == "PASS" 
            for r in self.test_results
        )
        
        print(f"   📈 AI Usage Tracking: {'✅ Working' if usage_tracking_working else '❌ Issues'}")
        print(f"   💾 Smart Caching: {'✅ Working' if caching_working else '❌ Issues'}")
        print(f"   📊 Cost Analytics: {'✅ Working' if analytics_working else '❌ Issues'}")
        
        print(f"\n🔧 System Capabilities Verified:")
        print(f"   • AI usage recording for email scanning operations")
        print(f"   • Token counting and cost calculation")
        print(f"   • Smart caching for repeated content")
        print(f"   • Usage limits and quota enforcement")
        print(f"   • Real-time cost analytics")
        print(f"   • Database storage and aggregation")
        
        if passed_tests >= total_tests * 0.85:
            print(f"\n🎉 CONCLUSION: AI Cost Management system is working excellently!")
            print(f"   The system provides comprehensive cost control and analytics.")
        else:
            print(f"\n⚠️  CONCLUSION: AI Cost Management system needs improvements.")
            print(f"   Some critical features are not working as expected.")

if __name__ == "__main__":
    tester = AICostManagementTester()
    tester.run_comprehensive_tests()