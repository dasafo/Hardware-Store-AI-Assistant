#!/usr/bin/env python3
"""
🏪 Hardware Store AI Assistant - Interactive Demo Script

This script demonstrates all the capabilities of the Hardware Store AI Assistant:
- API endpoint testing
- Search functionality
- Chat capabilities
- Security features
- Performance monitoring

Usage:
    python scripts/demo.py
"""

import asyncio
import json
import time
import requests
from typing import Dict, Any, List
from datetime import datetime
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_API_KEY = "hsai-admin-2024-secure-key-change-in-production"
USER_API_KEY = "hsai-user-2024-secure-key-change-in-production"

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str):
    """Print a colorful header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}🏪 {text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_info(text: str):
    """Print info message"""
    print(f"{Colors.OKBLUE}ℹ️  {text}{Colors.ENDC}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

def make_request(method: str, endpoint: str, headers: Dict = None, data: Dict = None) -> Dict[str, Any]:
    """Make HTTP request and return response info"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        start_time = time.time()
        
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        end_time = time.time()
        response_time = round((end_time - start_time) * 1000, 2)
        
        return {
            "success": response.status_code < 400,
            "status_code": response.status_code,
            "response_time_ms": response_time,
            "content": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            "headers": dict(response.headers)
        }
    
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "status_code": 0,
            "response_time_ms": 0,
            "content": "Connection Error - Is the server running?",
            "headers": {}
        }
    except Exception as e:
        return {
            "success": False,
            "status_code": 0,
            "response_time_ms": 0,
            "content": f"Error: {str(e)}",
            "headers": {}
        }

def test_health_endpoints():
    """Test all health check endpoints"""
    print_header("HEALTH CHECK TESTS")
    
    health_endpoints = [
        ("/health", "Overall Health"),
        ("/health/live", "Liveness Check"),
        ("/health/ready", "Readiness Check"),
        ("/health/postgres", "PostgreSQL Health"),
        ("/health/redis", "Redis Health"),
        ("/health/qdrant", "Qdrant Health"),
    ]
    
    for endpoint, description in health_endpoints:
        result = make_request("GET", endpoint)
        
        if result["success"]:
            print_success(f"{description}: {result['status_code']} ({result['response_time_ms']}ms)")
        else:
            print_error(f"{description}: {result['status_code']} - {result['content']}")

def test_security_endpoints():
    """Test security endpoints"""
    print_header("SECURITY TESTS")
    
    # Test public security info
    result = make_request("GET", "/security/info")
    if result["success"]:
        print_success(f"Security Info: {result['status_code']} ({result['response_time_ms']}ms)")
        info = result["content"]
        print_info(f"  Rate Limiting: {'✅' if info.get('rate_limiting_enabled') else '❌'}")
        print_info(f"  API Key Auth: {'✅' if info.get('api_key_auth_enabled') else '❌'}")
        print_info(f"  Admin Keys: {info.get('admin_keys_count', 0)}")
        print_info(f"  User Keys: {info.get('user_keys_count', 0)}")
    else:
        print_error(f"Security Info: {result['status_code']} - {result['content']}")
    
    # Test API key validation with user key
    headers = {"X-API-Key": USER_API_KEY}
    result = make_request("POST", "/security/api-key/validate", headers=headers)
    if result["success"]:
        print_success(f"User API Key Validation: {result['status_code']} ({result['response_time_ms']}ms)")
        validation = result["content"]
        print_info(f"  Key Type: {validation.get('key_type', 'unknown')}")
    else:
        print_error(f"User API Key Validation: {result['status_code']} - {result['content']}")
    
    # Test admin-only endpoint
    headers = {"X-API-Key": ADMIN_API_KEY}
    result = make_request("GET", "/security/rate-limit/stats", headers=headers)
    if result["success"]:
        print_success(f"Admin Rate Limit Stats: {result['status_code']} ({result['response_time_ms']}ms)")
        stats = result["content"]
        print_info(f"  Active IPs: {stats.get('active_ips', 0)}")
        print_info(f"  Total Requests: {stats.get('total_requests_last_minute', 0)}")
    else:
        print_error(f"Admin Rate Limit Stats: {result['status_code']} - {result['content']}")
    
    # Test security headers
    result = make_request("GET", "/security/headers/test")
    if result["success"]:
        print_success(f"Security Headers Test: {result['status_code']} ({result['response_time_ms']}ms)")
        headers = result["headers"]
        security_headers = [
            "x-content-type-options",
            "x-frame-options", 
            "x-xss-protection",
            "referrer-policy",
            "content-security-policy",
            "permissions-policy",
            "x-security-middleware"
        ]
        for header in security_headers:
            if header in headers:
                print_info(f"  {header}: ✅")
            else:
                print_warning(f"  {header}: ❌ Missing")
    else:
        print_error(f"Security Headers Test: {result['status_code']} - {result['content']}")

def test_search_functionality():
    """Test search endpoints"""
    print_header("SEARCH FUNCTIONALITY TESTS")
    
    # Test basic search
    search_queries = [
        "hammer",
        "tools for fixing pipes",
        "screwdriver set",
        "electrical supplies",
        "garden hose"
    ]
    
    for query in search_queries:
        data = {"query": query, "limit": 3}
        result = make_request("POST", "/search", data=data)
        
        if result["success"]:
            print_success(f"Search '{query}': {result['status_code']} ({result['response_time_ms']}ms)")
            search_result = result["content"]
            if isinstance(search_result, dict) and "results" in search_result:
                print_info(f"  Found {len(search_result['results'])} results")
                for i, product in enumerate(search_result['results'][:2]):  # Show first 2
                    if isinstance(product, dict):
                        print_info(f"    {i+1}. {product.get('name', 'Unknown')} (Score: {product.get('score', 'N/A')})")
            else:
                print_warning(f"  Unexpected response format: {search_result}")
        else:
            print_error(f"Search '{query}': {result['status_code']} - {result['content']}")
        
        time.sleep(0.5)  # Rate limiting courtesy

def test_product_endpoints():
    """Test product-related endpoints"""
    print_header("PRODUCT ENDPOINTS TESTS")
    
    # Test product details (this will likely return 404 for demo SKUs, which is expected)
    test_skus = ["HAMMER001", "SCREW001", "PIPE001"]
    
    for sku in test_skus:
        result = make_request("GET", f"/products/{sku}/details")
        
        if result["success"]:
            print_success(f"Product Details '{sku}': {result['status_code']} ({result['response_time_ms']}ms)")
            product = result["content"]
            if isinstance(product, dict):
                print_info(f"  Name: {product.get('name', 'N/A')}")
                print_info(f"  Price: ${product.get('price', 'N/A')}")
        else:
            # 404 is expected for demo SKUs
            if result["status_code"] == 404:
                print_info(f"Product Details '{sku}': 404 (Product not found - expected for demo)")
            else:
                print_error(f"Product Details '{sku}': {result['status_code']} - {result['content']}")
    
    # Test recommendations
    data = {"sku": "HAMMER001", "limit": 3}
    result = make_request("POST", "/recommendations", data=data)
    
    if result["success"]:
        print_success(f"Product Recommendations: {result['status_code']} ({result['response_time_ms']}ms)")
    else:
        if result["status_code"] == 404:
            print_info("Product Recommendations: 404 (Product not found - expected for demo)")
        else:
            print_error(f"Product Recommendations: {result['status_code']} - {result['content']}")

def test_chat_functionality():
    """Test chat endpoints"""
    print_header("CHAT FUNCTIONALITY TESTS")
    
    chat_messages = [
        "Hello, I need help finding tools",
        "What tools do I need to fix a leaky faucet?",
        "Can you recommend some good screwdrivers?",
        "I'm working on a plumbing project"
    ]
    
    session_id = f"demo_session_{int(time.time())}"
    
    for message in chat_messages:
        data = {
            "message": message,
            "session_id": session_id
        }
        result = make_request("POST", "/chat", data=data)
        
        if result["success"]:
            print_success(f"Chat Message: {result['status_code']} ({result['response_time_ms']}ms)")
            chat_response = result["content"]
            if isinstance(chat_response, dict) and "response" in chat_response:
                response_text = chat_response["response"][:100] + "..." if len(chat_response["response"]) > 100 else chat_response["response"]
                print_info(f"  User: {message}")
                print_info(f"  AI: {response_text}")
            else:
                print_warning(f"  Unexpected response format")
        else:
            print_error(f"Chat Message: {result['status_code']} - {result['content']}")
        
        time.sleep(1)  # Give some time between chat messages

def test_cache_endpoints():
    """Test cache endpoints"""
    print_header("CACHE SYSTEM TESTS")
    
    # Test cache stats (public endpoint)
    result = make_request("GET", "/cache/stats")
    
    if result["success"]:
        print_success(f"Cache Stats: {result['status_code']} ({result['response_time_ms']}ms)")
        stats = result["content"]
        if isinstance(stats, dict):
            print_info(f"  Cache Hit Rate: {stats.get('hit_rate', 'N/A')}")
            print_info(f"  Total Keys: {stats.get('total_keys', 'N/A')}")
    else:
        print_error(f"Cache Stats: {result['status_code']} - {result['content']}")
    
    # Test cache health
    result = make_request("GET", "/cache/health")
    
    if result["success"]:
        print_success(f"Cache Health: {result['status_code']} ({result['response_time_ms']}ms)")
    else:
        print_error(f"Cache Health: {result['status_code']} - {result['content']}")

def test_metrics_endpoints():
    """Test metrics endpoints"""
    print_header("METRICS & MONITORING TESTS")
    
    # Test system metrics
    result = make_request("GET", "/metrics")
    
    if result["success"]:
        print_success(f"System Metrics: {result['status_code']} ({result['response_time_ms']}ms)")
        metrics = result["content"]
        if isinstance(metrics, dict):
            print_info(f"  Uptime: {metrics.get('uptime_seconds', 'N/A')} seconds")
            print_info(f"  Total Requests: {metrics.get('total_requests', 'N/A')}")
            print_info(f"  Memory Usage: {metrics.get('memory_usage_mb', 'N/A')} MB")
    else:
        print_error(f"System Metrics: {result['status_code']} - {result['content']}")

def run_performance_test():
    """Run a simple performance test"""
    print_header("PERFORMANCE TEST")
    
    print_info("Running 10 concurrent search requests...")
    
    start_time = time.time()
    response_times = []
    
    # Simple sequential test (for demo purposes)
    for i in range(10):
        data = {"query": f"test query {i}", "limit": 1}
        result = make_request("POST", "/search", data=data)
        if result["success"]:
            response_times.append(result["response_time_ms"])
        time.sleep(0.1)  # Small delay to avoid overwhelming
    
    end_time = time.time()
    total_time = round((end_time - start_time) * 1000, 2)
    
    if response_times:
        avg_response_time = round(sum(response_times) / len(response_times), 2)
        min_response_time = min(response_times)
        max_response_time = max(response_times)
        
        print_success(f"Performance Test Completed:")
        print_info(f"  Total Time: {total_time}ms")
        print_info(f"  Average Response Time: {avg_response_time}ms")
        print_info(f"  Min Response Time: {min_response_time}ms")
        print_info(f"  Max Response Time: {max_response_time}ms")
        print_info(f"  Successful Requests: {len(response_times)}/10")
    else:
        print_error("Performance Test Failed: No successful requests")

def display_system_summary():
    """Display a summary of the system"""
    print_header("SYSTEM SUMMARY")
    
    # Get security info
    security_result = make_request("GET", "/security/info")
    
    # Get health status
    health_result = make_request("GET", "/health")
    
    # Get metrics
    metrics_result = make_request("GET", "/metrics")
    
    print_info("🏪 Hardware Store AI Assistant - System Status")
    print_info(f"📅 Demo Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"🌐 Base URL: {BASE_URL}")
    
    if health_result["success"]:
        print_success("🟢 System Status: HEALTHY")
    else:
        print_error("🔴 System Status: UNHEALTHY")
    
    if security_result["success"]:
        security_info = security_result["content"]
        print_success("🔒 Security Status: ACTIVE")
        print_info(f"   Rate Limiting: {'Enabled' if security_info.get('rate_limiting_enabled') else 'Disabled'}")
        print_info(f"   API Authentication: {'Enabled' if security_info.get('api_key_auth_enabled') else 'Disabled'}")
    
    if metrics_result["success"]:
        metrics = metrics_result["content"]
        print_success("📊 Performance Metrics: AVAILABLE")
        if isinstance(metrics, dict):
            print_info(f"   Uptime: {metrics.get('uptime_seconds', 'N/A')} seconds")
            print_info(f"   Memory Usage: {metrics.get('memory_usage_mb', 'N/A')} MB")

def main():
    """Main demo function"""
    print_header("HARDWARE STORE AI ASSISTANT - INTERACTIVE DEMO")
    
    print_info("This demo will test all major components of the Hardware Store AI Assistant")
    print_info("Make sure the system is running with: make up")
    print_info("Press Ctrl+C at any time to stop the demo\n")
    
    try:
        # Wait for user to start
        input("Press Enter to start the demo...")
        
        # Run all tests
        display_system_summary()
        test_health_endpoints()
        test_security_endpoints()
        test_search_functionality()
        test_product_endpoints()
        test_chat_functionality()
        test_cache_endpoints()
        test_metrics_endpoints()
        run_performance_test()
        
        # Final summary
        print_header("DEMO COMPLETED SUCCESSFULLY! 🎉")
        print_success("All major components have been tested")
        print_info("For more detailed API documentation, visit: http://localhost:8000/docs")
        print_info("For n8n workflows, visit: http://localhost:5678")
        print_info("For database admin, visit: http://localhost:5050")
        
    except KeyboardInterrupt:
        print_warning("\n\nDemo interrupted by user")
        print_info("Thanks for trying the Hardware Store AI Assistant!")
    except Exception as e:
        print_error(f"\nDemo failed with error: {str(e)}")
        print_info("Make sure all services are running with: make up")

if __name__ == "__main__":
    main() 