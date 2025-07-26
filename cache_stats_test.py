#!/usr/bin/env python3
"""
Test the specific cache stats endpoint issue mentioned in test_result.md
"""

import requests
import json
import time

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

def test_cache_stats_endpoint():
    """Test the cache stats endpoint for non-admin users"""
    backend_url = get_backend_url()
    if not backend_url:
        print("❌ Could not determine backend URL")
        return False
    
    if not backend_url.endswith('/api'):
        backend_url = f"{backend_url}/api"
    
    print(f"🔗 Testing cache stats endpoint at: {backend_url}")
    
    # Register and login a regular user
    test_user_data = {
        "name": "Cache Test User",
        "email": f"cachetest.{int(time.time())}@example.com",
        "password": "TestPass123!",
        "organization": "Test Org"
    }
    
    # Register user
    reg_response = requests.post(
        f"{backend_url}/auth/register",
        json=test_user_data,
        timeout=10
    )
    
    if reg_response.status_code != 200:
        print(f"❌ Registration failed: {reg_response.status_code}")
        return False
    
    # Login user
    login_data = {
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    }
    
    login_response = requests.post(
        f"{backend_url}/auth/login",
        json=login_data,
        timeout=10
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return False
    
    token = login_response.json().get('access_token')
    if not token:
        print("❌ No access token received")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test cache stats endpoint
    cache_response = requests.get(
        f"{backend_url}/ai/cache/stats",
        headers=headers,
        timeout=10
    )
    
    print(f"📊 Cache stats endpoint response: HTTP {cache_response.status_code}")
    
    if cache_response.status_code == 403:
        print("✅ PASS - Cache stats endpoint correctly returns 403 for non-admin users")
        return True
    elif cache_response.status_code == 500:
        print("❌ FAIL - Cache stats endpoint returns 500 error instead of 403 for non-admin users")
        try:
            error_data = cache_response.json()
            print(f"   Error details: {error_data}")
        except:
            print(f"   Error text: {cache_response.text}")
        return False
    else:
        print(f"❌ UNEXPECTED - Cache stats endpoint returns HTTP {cache_response.status_code}")
        try:
            response_data = cache_response.json()
            print(f"   Response: {response_data}")
        except:
            print(f"   Response text: {cache_response.text}")
        return False

if __name__ == "__main__":
    success = test_cache_stats_endpoint()
    exit(0 if success else 1)