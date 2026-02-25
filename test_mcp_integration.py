#!/usr/bin/env python3
"""
test_mcp_integration.py
Test script to verify MCP server integration with the AI system.
"""

import json
import os
import subprocess
import time
from pathlib import Path
import requests


def test_mcp_server_running():
    """Test if MCP server is running."""
    try:
        response = requests.get('http://localhost:5001/health', timeout=5)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


def test_send_email_action():
    """Test the send_email action via MCP server."""
    payload = {
        "action_type": "email_send",
        "task_id": "test_email_001",
        "to": "test@example.com",
        "subject": "Test Email",
        "body": "This is a test email from MCP server."
    }
    
    try:
        response = requests.post('http://localhost:5001/api/action', json=payload, timeout=10)
        return response.status_code == 200, response.json() if response.status_code == 200 else response.text
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to MCP server"


def test_execute_action_skill():
    """Test the execute_action.skill with an email task."""
    # Create a temporary email task
    task_data = {
        "action_type": "send_email",
        "task_id": "test_skill_call",
        "to": "skill@example.com",
        "subject": "Skill Test",
        "body": "Test email from execute_action.skill"
    }
    
    # Write to a temporary file
    temp_file = Path("temp_test_task.json")
    with open(temp_file, 'w') as f:
        json.dump(task_data, f)
    
    try:
        # Call the execute_action.skill
        result = subprocess.run([
            'python', str(Path('Skills') / 'execute_action.skill'), str(temp_file)
        ], capture_output=True, text=True, timeout=30)
        
        # Clean up
        temp_file.unlink()
        
        return result.returncode == 0, result.stdout
    except subprocess.TimeoutExpired:
        # Clean up even if timeout occurs
        if temp_file.exists():
            temp_file.unlink()
        return False, "Timeout calling execute_action.skill"


def test_example_mcp_call_skill():
    """Test the example_mcp_call.skill."""
    try:
        # Call the example_mcp_call.skill
        result = subprocess.run([
            'python', str(Path('Skills') / 'example_mcp_call.skill'), 
            'send_email', 
            '{"to": "example@example.com", "subject": "Example", "body": "Test"}',
            'test_example_001'
        ], capture_output=True, text=True, timeout=30)
        
        return result.returncode == 0, result.stdout
    except subprocess.TimeoutExpired:
        return False, "Timeout calling example_mcp_call.skill"


def main():
    """Main test function."""
    print("Testing MCP Server Integration...")
    
    # Check if MCP server is running
    print("\n1. Checking if MCP server is running...")
    if test_mcp_server_running():
        print("+ MCP server is running")
    else:
        print("- MCP server is not running")
        print("  To start the server, run: python MCP_Server.py")
        return
    
    # Test send_email action
    print("\n2. Testing send_email action...")
    success, response = test_send_email_action()
    if success:
        print("+ send_email action executed successfully")
        print(f"  Response: {response}")
    else:
        print(f"- send_email action failed: {response}")
    
    # Test execute_action.skill
    print("\n3. Testing execute_action.skill...")
    success, output = test_execute_action_skill()
    if success:
        print("+ execute_action.skill executed successfully")
        print(f"  Output: {output}")
    else:
        print(f"- execute_action.skill failed: {output}")
    
    # Test example_mcp_call.skill
    print("\n4. Testing example_mcp_call.skill...")
    success, output = test_example_mcp_call_skill()
    if success:
        print("+ example_mcp_call.skill executed successfully")
        print(f"  Output: {output}")
    else:
        print(f"- example_mcp_call.skill failed: {output}")
    
    # Check if log files were created
    print("\n5. Checking for log files...")
    logs_dir = Path("Logs")
    if logs_dir.exists():
        log_files = list(logs_dir.glob("mcp_*.json")) + list(logs_dir.glob("mcp_server.log"))
        if log_files:
            print(f"+ Found {len(log_files)} log files in Logs directory")
            for log_file in log_files[:3]:  # Show first 3
                print(f"  - {log_file.name}")
        else:
            print("? No log files found in Logs directory")
    else:
        print("? Logs directory does not exist")
    
    print("\nMCP Server integration testing completed!")


if __name__ == "__main__":
    main()