"""
Test script to verify the enhanced Action_Agent functionality
"""

from Agents.Action_Agent import Action_Agent
import json
from pathlib import Path

def test_action_agent():
    print("[ACTION] Testing enhanced Action_Agent functionality...")
    
    # Initialize the Action_Agent
    action_agent = Action_Agent()
    
    # Test 1: Email task execution
    print("\n[TEST] Testing email task execution...")
    email_task = {
        "task_id": "email_exec_001",
        "type": "send_email",
        "description": "Send welcome email to new employee",
        "data": {
            "to_emails": ["newemployee@company.com"],
            "subject": "Welcome to the Company!",
            "body": "Dear John, welcome to our team!"
        },
        "expected_outcome": "Email sent successfully"
    }
    
    result = action_agent.execute_task(email_task)
    print(f"  Result: {result['status']}")
    print(f"  Message: {result['message']}")
    
    # Test 2: Social media task execution
    print("\n[TEST] Testing social media task execution...")
    social_task = {
        "task_id": "social_exec_001",
        "type": "post_social",
        "description": "Post company update on LinkedIn",
        "data": {
            "platform": "LinkedIn",
            "content": "Excited to announce our new product launch!",
            "hashtags": ["#innovation", "#tech", "#productlaunch"]
        },
        "expected_outcome": "Post published successfully"
    }
    
    result = action_agent.execute_task(social_task)
    print(f"  Result: {result['status']}")
    print(f"  Message: {result['message']}")
    
    # Test 3: Invoice PDF generation task
    print("\n[TEST] Testing invoice PDF generation task...")
    invoice_task = {
        "task_id": "invoice_exec_001",
        "type": "generate_invoice_pdf",
        "description": "Generate invoice for client",
        "data": {
            "customer_name": "Acme Corp",
            "customer_email": "billing@acme.com",
            "amount": "2500.00",
            "due_date": "2026-03-15",
            "items": [
                {"item": "Software Development", "quantity": 10, "price": "250.00"}
            ]
        },
        "expected_outcome": "Invoice PDF generated successfully"
    }
    
    result = action_agent.execute_task(invoice_task)
    print(f"  Result: {result['status']}")
    print(f"  Message: {result['message']}")
    
    # Test 4: Calendar update task
    print("\n[TEST] Testing calendar update task...")
    calendar_task = {
        "task_id": "calendar_exec_001",
        "type": "update_calendar",
        "description": "Schedule team meeting",
        "data": {
            "title": "Team Sync Meeting",
            "start_time": "2026-02-15T10:00:00",
            "end_time": "2026-02-15T11:00:00",
            "attendees": ["team@company.com"],
            "description": "Weekly team synchronization meeting"
        },
        "expected_outcome": "Calendar event scheduled successfully"
    }
    
    result = action_agent.execute_task(calendar_task)
    print(f"  Result: {result['status']}")
    print(f"  Message: {result['message']}")
    
    # Test 5: Browser automation task
    print("\n[TEST] Testing browser automation task...")
    browser_task = {
        "task_id": "browser_exec_001",
        "type": "trigger_browser_automation",
        "description": "Automate data extraction from website",
        "data": {
            "url": "https://example.com/data",
            "actions": ["click_login", "enter_credentials", "extract_data"]
        },
        "expected_outcome": "Data extracted successfully"
    }
    
    result = action_agent.execute_task(browser_task)
    print(f"  Result: {result['status']}")
    print(f"  Message: {result['message']}")
    
    # Test 6: Shell command task (MCP action)
    print("\n[TEST] Testing shell command task...")
    shell_task = {
        "task_id": "shell_exec_001",
        "type": "shell_command",
        "description": "Check system status",
        "data": {
            "command": "echo System health check",
            "timeout": 10
        },
        "expected_outcome": "System status retrieved"
    }
    
    result = action_agent.execute_task(shell_task)
    print(f"  Result: {result['status']}")
    print(f"  Message: {result['message']}")
    
    # Check if execution logs were created
    print(f"\n[CHECK] Execution logs in Logs directory:")
    log_files = list(Path("Logs").glob("*_execution_log.json"))
    for log_file in log_files[-6:]:  # Show last 6 log files
        print(f"  - {log_file.name}")
    
    # Display content of one of the execution logs
    if log_files:
        print(f"\n[CONTENT] Sample execution log content:")
        with open(log_files[-1], 'r') as f:
            import json
            content = json.load(f)
            print(json.dumps(content, indent=2))

if __name__ == "__main__":
    test_action_agent()