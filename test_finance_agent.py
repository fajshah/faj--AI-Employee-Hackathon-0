"""
Test script to verify the enhanced Finance_Agent functionality
"""

from Agents.Finance_Agent import Finance_Agent
import json
from pathlib import Path

def test_finance_agent():
    print("[FINANCE] Testing enhanced Finance_Agent functionality...")
    
    # Initialize the Finance_Agent
    finance_agent = Finance_Agent()
    
    # Test 1: Small, safe transaction (should not require approval)
    print("\n[TEST] Testing small, safe transaction...")
    safe_transaction = {
        "task_id": "safe_trans_001",
        "type": "record_transaction",
        "description": "Office supplies purchase",
        "sensitive": False,
        "data": {
            "amount": "45.99",
            "transaction_type": "debit",
            "description": "Purchase of office supplies",
            "account_from": "business",
            "account_to": "office_supplies_vendor",
            "customer_email": "supplies@vendor.com"
        },
        "expected_outcome": "Transaction recorded successfully"
    }
    
    result = finance_agent.execute_task(safe_transaction)
    print(f"  Result: {result['status']}")
    print(f"  Approval required: {result['approval_required']}")
    print(f"  Plan created: {result['plan_created']}")
    
    # Test 2: Large payment (should require approval)
    print("\n[TEST] Testing large payment (> $100)...")
    large_payment = {
        "task_id": "large_pay_001",
        "type": "process_payment",
        "description": "Quarterly software license payment",
        "sensitive": False,
        "data": {
            "amount": "1250.00",
            "processor": "stripe",
            "customer_email": "billing@software.com",
            "description": "Quarterly software license renewal"
        },
        "expected_outcome": "Payment processed after approval"
    }
    
    result = finance_agent.execute_task(large_payment)
    print(f"  Result: {result['status']}")
    print(f"  Approval required: {result['approval_required']}")
    print(f"  Plan created: {result['plan_created']}")
    if 'approval_file' in result:
        print(f"  Approval file: {result['approval_file']}")
    
    # Test 3: New payee (should require approval)
    print("\n[TEST] Testing transaction with new payee...")
    new_payee_transaction = {
        "task_id": "new_payee_001",
        "type": "create_invoice",
        "description": "Invoice for new client",
        "sensitive": False,
        "data": {
            "customer_name": "New Client Inc.",
            "customer_email": "newclient@newdomain.com",  # This should be a new payee
            "amount": "750.00",
            "due_date": "2026-03-15",
            "items": [
                {"item": "Consulting Services", "quantity": 5, "price": "150.00"}
            ]
        },
        "expected_outcome": "Invoice created after approval"
    }
    
    result = finance_agent.execute_task(new_payee_transaction)
    print(f"  Result: {result['status']}")
    print(f"  Approval required: {result['approval_required']}")
    print(f"  Plan created: {result['plan_created']}")
    if 'approval_file' in result:
        print(f"  Approval file: {result['approval_file']}")
    
    # Test 4: Unusual spending pattern (should require approval)
    print("\n[TEST] Testing unusual spending pattern...")
    unusual_spending = {
        "task_id": "unusual_001",
        "type": "record_transaction",
        "description": "Emergency equipment purchase",
        "sensitive": False,
        "data": {
            "amount": "850.00",
            "transaction_type": "debit",
            "description": "Emergency rush delivery of critical equipment",
            "account_from": "business",
            "account_to": "equipment_vendor",
            "customer_email": "vendor@existing.com"  # Existing vendor but unusual description
        },
        "expected_outcome": "Transaction recorded after approval"
    }
    
    result = finance_agent.execute_task(unusual_spending)
    print(f"  Result: {result['status']}")
    print(f"  Approval required: {result['approval_required']}")
    print(f"  Plan created: {result['plan_created']}")
    if 'approval_file' in result:
        print(f"  Approval file: {result['approval_file']}")
    
    # Check if plan files were created
    print(f"\n[CHECK] Financial plan files in Plans directory:")
    plan_files = list(Path("Plans").glob("FINANCIAL_PLAN_*.md"))
    for plan_file in plan_files[-4:]:  # Show last 4 plan files
        print(f"  - {plan_file.name}")
    
    # Check if approval files were created
    print(f"\n[CHECK] Approval files in Pending_Approval directory:")
    approval_files = list(Path("Pending_Approval").glob("*financial_approval.json"))
    for approval_file in approval_files:
        print(f"  - {approval_file.name}")
    
    # Display content of one of the financial plans
    if plan_files:
        print(f"\n[CONTENT] Sample financial plan content:")
        with open(plan_files[-1], 'r') as f:
            content = f.read()
            # Print first 500 characters
            print(content[:500] + "..." if len(content) > 500 else content)

if __name__ == "__main__":
    test_finance_agent()