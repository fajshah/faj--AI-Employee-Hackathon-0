"""
Test script to verify the enhanced Comms_Agent functionality
"""

from Agents.Comms_Agent import Comms_Agent
import json
from pathlib import Path

def test_comms_agent():
    print("[COMMS] Testing enhanced Comms_Agent functionality...")
    
    # Initialize the Comms_Agent
    comms_agent = Comms_Agent()
    
    # Test 1: Safe email task
    print("\n[TEST] Testing safe email task...")
    safe_email_task = {
        "task_id": "safe_email_001",
        "type": "send_email",
        "description": "Send meeting reminder to team",
        "sensitive": False,
        "data": {
            "to_emails": ["team@company.com"],
            "subject": "Meeting Reminder",
            "body": "Hi team, just a reminder about our meeting tomorrow at 10 AM."
        },
        "expected_outcome": "Team receives meeting reminder"
    }
    
    result = comms_agent.execute_task(safe_email_task)
    print(f"  Result: {result['status']}")
    print(f"  Approval required: {result['approval_required']}")
    print(f"  Plan created: {result['plan_created']}")
    
    # Test 2: Sensitive email task
    print("\n[TEST] Testing sensitive email task...")
    sensitive_email_task = {
        "task_id": "sensitive_email_001",
        "type": "send_email",
        "description": "Send salary information to employee",
        "sensitive": False,  # Even if marked as not sensitive, content should trigger approval
        "data": {
            "to_emails": ["employee@gmail.com"],  # External domain
            "subject": "Salary Information",
            "body": "Dear employee, attached is your confidential salary information for this month."
        },
        "expected_outcome": "Employee receives salary information securely"
    }
    
    result = comms_agent.execute_task(sensitive_email_task)
    print(f"  Result: {result['status']}")
    print(f"  Approval required: {result['approval_required']}")
    print(f"  Plan created: {result['plan_created']}")
    if 'approval_file' in result:
        print(f"  Approval file: {result['approval_file']}")
    
    # Test 3: WhatsApp message
    print("\n[TEST] Testing WhatsApp message task...")
    whatsapp_task = {
        "task_id": "whatsapp_001",
        "type": "send_whatsapp",
        "description": "Send appointment reminder via WhatsApp",
        "sensitive": False,
        "data": {
            "recipient_phone": "+1234567890",
            "message": "Hi, this is a reminder about your appointment tomorrow at 2 PM."
        },
        "expected_outcome": "Customer receives appointment reminder"
    }
    
    result = comms_agent.execute_task(whatsapp_task)
    print(f"  Result: {result['status']}")
    print(f"  Approval required: {result['approval_required']}")
    print(f"  Plan created: {result['plan_created']}")
    
    # Check if plan files were created
    print(f"\n[CHECK] Plan files in Plans directory:")
    plan_files = list(Path("Plans").glob("PLAN_*.md"))
    for plan_file in plan_files[-3:]:  # Show last 3 plan files
        print(f"  - {plan_file.name}")
    
    # Check if approval files were created
    print(f"\n[CHECK] Approval files in Pending_Approval directory:")
    approval_files = list(Path("Pending_Approval").glob("*approval.json"))
    for approval_file in approval_files:
        print(f"  - {approval_file.name}")

if __name__ == "__main__":
    test_comms_agent()