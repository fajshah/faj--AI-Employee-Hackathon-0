"""
Gold Tier System Test Script
Tests all MCP servers and endpoints

Usage: python test_system.py
"""

import requests
import json
from datetime import datetime


def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def test_health(server_name, url):
    """Test health endpoint"""
    print(f"\nTesting {server_name} health...")
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"  [OK] {server_name} is healthy")
            print(f"  Response: {response.json()}")
            return True
        else:
            print(f"  [ERROR] {server_name} returned {response.status_code}")
            return False
    except Exception as e:
        print(f"  [ERROR] Cannot connect to {server_name}: {e}")
        return False


def test_email_endpoint():
    """Test email sending endpoint"""
    print_header("Testing Email Endpoint")
    
    url = "http://localhost:5001/api/email/send"
    data = {
        "task_id": f"test_email_{int(datetime.now().timestamp())}",
        "to": "test@example.com",
        "subject": "Gold Tier Test",
        "body": "This is a test email from Gold Tier AI Employee System"
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            print("  [OK] Email endpoint working")
            print(f"  Response: {response.json()}")
            return True
        else:
            print(f"  [ERROR] Email endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print(f"  [ERROR] Email endpoint error: {e}")
        return False


def test_social_endpoint():
    """Test social media posting endpoint"""
    print_header("Testing Social Media Endpoint")
    
    url = "http://localhost:5002/api/social/post"
    data = {
        "task_id": f"test_social_{int(datetime.now().timestamp())}",
        "platform": "linkedin",
        "content": "Testing Gold Tier AI Employee System! #AI #Automation",
        "hashtags": ["AI", "Automation", "Testing"]
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            print("  [OK] Social endpoint working")
            print(f"  Response: {response.json()}")
            return True
        else:
            print(f"  [ERROR] Social endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print(f"  [ERROR] Social endpoint error: {e}")
        return False


def test_odoo_endpoint():
    """Test Odoo action endpoint"""
    print_header("Testing Odoo Endpoint")
    
    url = "http://localhost:5003/api/odoo/action"
    data = {
        "task_id": f"test_odoo_{int(datetime.now().timestamp())}",
        "action_type": "create_invoice",
        "data": {
            "client": "Test Client",
            "amount": 100.00,
            "description": "Test Invoice"
        }
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            print("  [OK] Odoo endpoint working")
            print(f"  Response: {response.json()}")
            return True
        else:
            print(f"  [ERROR] Odoo endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print(f"  [ERROR] Odoo endpoint error: {e}")
        return False


def main():
    """Run all tests"""
    print("""
+============================================================+
|                                                            |
|     GOLD TIER SYSTEM TEST                                  |
|                                                            |
+============================================================+
    """)
    
    results = {
        "MCP Comms (5001)": False,
        "MCP Social (5002)": False,
        "MCP Finance (5003)": False,
        "Email Endpoint": False,
        "Social Endpoint": False,
        "Odoo Endpoint": False
    }
    
    # Test health endpoints
    results["MCP Comms (5001)"] = test_health("MCP Comms", "http://localhost:5001/health")
    results["MCP Social (5002)"] = test_health("MCP Social", "http://localhost:5002/health")
    results["MCP Finance (5003)"] = test_health("MCP Finance", "http://localhost:5003/health")
    
    # Test API endpoints
    results["Email Endpoint"] = test_email_endpoint()
    results["Social Endpoint"] = test_social_endpoint()
    results["Odoo Endpoint"] = test_odoo_endpoint()
    
    # Print summary
    print_header("Test Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test, result in results.items():
        status = "[OK]" if result else "[FAIL]"
        print(f"  {status} {test}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n  All systems operational!")
    else:
        print("\n  Some services need attention.")
        print("  Make sure MCP servers are running:")
        print("    - python MCP_Servers/MCP_Comms_Server.py")
        print("    - python MCP_Servers/MCP_Social_Server.py")
        print("    - python MCP_Servers/MCP_Finance_Server.py")


if __name__ == "__main__":
    main()
