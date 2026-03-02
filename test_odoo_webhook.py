"""
Odoo Webhook Integration Test Script
=====================================
Test the Odoo webhook handler with sample payloads

Usage: python test_odoo_webhook.py
"""

import requests
import json
import time
from datetime import datetime

# Configuration
WEBHOOK_URL = "http://localhost:5050/odoo_webhook"
HEALTH_URL = "http://localhost:5050/health"
STATUS_URL = "http://localhost:5050/api/status"
WEBHOOK_SECRET = "change-this-in-production"  # Update to match your .env.gold

# Note: The standalone version (odoo_webhook_standalone.py) sends directly via APIs
# without requiring the MCP Server on port 5001.


def print_response(title: str, response: requests.Response):
    """Pretty print response"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    print(f"Response Time: {response.elapsed.total_seconds():.3f}s")
    print(f"\nResponse Body:")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
    print()


def test_health():
    """Test health endpoint"""
    print("\n🔍 Testing Health Endpoint...")
    try:
        response = requests.get(HEALTH_URL, timeout=10)
        print_response("Health Check", response)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - Is the webhook handler running?")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def test_status():
    """Test status endpoint"""
    print("\n🔍 Testing Status Endpoint...")
    try:
        response = requests.get(STATUS_URL, timeout=10)
        print_response("API Status", response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def test_new_lead():
    """Test new_lead event"""
    print("\n🔍 Testing new_lead Event...")
    
    payload = {
        "event_type": "new_lead",
        "secret": WEBHOOK_SECRET,
        "data": {
            "id": "TEST_LEAD_001",
            "partner_name": "Test Company Inc.",
            "contact_name": "John Smith",
            "email": "john.smith@testcompany.com",
            "phone": "+1234567890",
            "company_name": "Test Company Inc.",
            "opportunity_type": "Product Inquiry",
            "priority": "High",
            "stage": "New",
            "expected_revenue": 5000.00,
            "description": "Interested in enterprise solution",
            "source": "Website",
            "tags": ["Enterprise", "Hot Lead"],
            "created_at": datetime.now().isoformat(),
            "odoo_url": "http://localhost:8069/web#id=123"
        }
    }
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=30)
        print_response("new_lead Event", response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def test_sale_confirmed():
    """Test sale_confirmed event"""
    print("\n🔍 Testing sale_confirmed Event...")
    
    payload = {
        "event_type": "sale_confirmed",
        "secret": WEBHOOK_SECRET,
        "data": {
            "id": "TEST_SALE_001",
            "name": "S00001",
            "partner_name": "Happy Customer LLC",
            "partner_email": "customer@happy.com",
            "partner_phone": "+1987654321",
            "company_name": "Happy Customer LLC",
            "amount_total": 2500.00,
            "currency": "USD",
            "payment_state": "pending",
            "date_order": datetime.now().isoformat(),
            "expected_date": "2024-04-01",
            "order_lines": [
                {"name": "Premium Package", "quantity": 1, "price_unit": 2000},
                {"name": "Support Add-on", "quantity": 1, "price_unit": 500}
            ],
            "salesperson": "Jane Doe",
            "post_linkedin": True,
            "odoo_url": "http://localhost:8069/web#id=456"
        }
    }
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=30)
        print_response("sale_confirmed Event", response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def test_invoice_created():
    """Test invoice_created event"""
    print("\n🔍 Testing invoice_created Event...")
    
    payload = {
        "event_type": "invoice_created",
        "secret": WEBHOOK_SECRET,
        "data": {
            "id": "TEST_INV_001",
            "number": "INV/2024/0001",
            "partner_name": "Happy Customer LLC",
            "partner_email": "billing@happy.com",
            "partner_phone": "+1987654321",
            "company_name": "Happy Customer LLC",
            "amount_total": 2500.00,
            "amount_due": 2500.00,
            "currency": "USD",
            "invoice_date_due": "2024-04-15",
            "invoice_date": datetime.now().isoformat(),
            "payment_state": "not_paid",
            "odoo_url": "http://localhost:8069/web#id=789"
        }
    }
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=30)
        print_response("invoice_created Event", response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def test_invalid_secret():
    """Test with invalid secret (should fail)"""
    print("\n🔍 Testing Invalid Secret (Security Check)...")
    
    payload = {
        "event_type": "new_lead",
        "secret": "wrong-secret",
        "data": {"id": "TEST"}
    }
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        print_response("Invalid Secret Test", response)
        # Should return 401
        return response.status_code == 401
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def test_invalid_event_type():
    """Test with invalid event type"""
    print("\n🔍 Testing Invalid Event Type...")
    
    payload = {
        "event_type": "unknown_event",
        "secret": WEBHOOK_SECRET,
        "data": {}
    }
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        print_response("Invalid Event Type Test", response)
        return response.status_code == 400
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def run_all_tests():
    """Run all tests"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     🧪 ODOO WEBHOOK INTEGRATION TEST SUITE               ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    results = {
        "Health Check": test_health(),
        "API Status": test_status(),
        "new_lead Event": test_new_lead(),
        "sale_confirmed Event": test_sale_confirmed(),
        "invoice_created Event": test_invoice_created(),
        "Invalid Secret (Security)": test_invalid_secret(),
        "Invalid Event Type": test_invalid_event_type()
    }
    
    # Summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    return passed == total


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
