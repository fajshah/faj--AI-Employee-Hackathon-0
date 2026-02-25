#!/usr/bin/env python3
"""
test_approval_workflow.py
Test script to verify the approval workflow functionality.
"""

import json
import os
import tempfile
from pathlib import Path
import subprocess
import sys


def create_test_task(task_name, content, sensitive_keywords=None):
    """
    Create a test task file with specified content.
    
    Args:
        task_name (str): Name of the task file
        content (dict): Content of the task
        sensitive_keywords (list): List of keywords to add to make task sensitive
    """
    needs_action_dir = Path("Needs_Action")
    needs_action_dir.mkdir(exist_ok=True)
    
    if sensitive_keywords:
        # Add sensitive keywords to the content
        for keyword in sensitive_keywords:
            if 'description' in content:
                content['description'] += f" {keyword}"
            elif 'title' in content:
                content['title'] += f" {keyword}"
            else:
                content['description'] = keyword
    
    task_path = needs_action_dir / f"{task_name}.json"
    
    with open(task_path, 'w', encoding='utf-8') as f:
        json.dump(content, f, indent=2)
    
    return str(task_path)


def test_approval_workflow():
    """
    Test the approval workflow functionality.
    """
    print("Testing Approval Workflow...")
    
    # Clean up any existing test files
    pending_dir = Path("Pending_Approval")
    approved_dir = Path("Approved")
    done_dir = Path("Done")
    
    pending_dir.mkdir(exist_ok=True)
    approved_dir.mkdir(exist_ok=True)
    done_dir.mkdir(exist_ok=True)
    
    # Clear test directories
    for dir_path in [pending_dir, approved_dir, done_dir]:
        for file_path in dir_path.glob("*.json"):
            file_path.unlink()
    
    # Test 1: Create a task with sensitive keywords
    print("\n1. Testing task with sensitive keywords...")
    sensitive_task = {
        "task_id": "test_payment_task",
        "title": "Process Payment",
        "description": "Need to process monthly payment for client",
        "type": "finance",
        "priority": "high"
    }
    
    task_path = create_test_task("test_payment_task", sensitive_task, ["payment"])
    
    # Run the approval workflow on this task
    result = subprocess.run([
        sys.executable,
        str(Path("Skills") / "approval_workflow.skill"),
        str(task_path)
    ], capture_output=True, text=True, cwd=os.getcwd())
    
    print(f"Command output: {result.stdout}")
    if result.stderr:
        print(f"Command errors: {result.stderr}")
    
    # Check if approval file was created
    approval_files = list(pending_dir.glob("*test_payment_task*"))
    if approval_files:
        print("+ Approval file created successfully")
        approval_file = approval_files[0]
        
        # Read and verify the approval file content
        with open(approval_file, 'r', encoding='utf-8') as f:
            approval_content = json.load(f)
        
        required_fields = ["task_id", "reason_for_approval", "summary", "proposed_action", "status"]
        missing_fields = [field for field in required_fields if field not in approval_content]
        
        if not missing_fields:
            print("+ All required fields present in approval file")
        else:
            print(f"- Missing fields: {missing_fields}")
        
        if approval_content["status"] == "waiting":
            print("+ Status is 'waiting' as expected")
        else:
            print(f"- Status is '{approval_content['status']}', expected 'waiting'")
            
        if "payment" in approval_content["reason_for_approval"]:
            print("+ Reason for approval correctly identifies the keyword")
        else:
            print(f"- Reason for approval incorrect: {approval_content['reason_for_approval']}")
    else:
        print("- Approval file was not created")
    
    # Test 2: Create a non-sensitive task
    print("\n2. Testing task without sensitive keywords...")
    normal_task = {
        "task_id": "test_normal_task",
        "title": "Send Regular Update",
        "description": "Send weekly status update to team",
        "type": "communication",
        "priority": "medium"
    }
    
    task_path2 = create_test_task("test_normal_task", normal_task)
    
    # Run the approval workflow on this task
    result2 = subprocess.run([
        sys.executable,
        str(Path("Skills") / "approval_workflow.skill"),
        str(task_path2)
    ], capture_output=True, text=True, cwd=os.getcwd())
    
    print(f"Command output: {result2.stdout}")
    if result2.stderr:
        print(f"Command errors: {result2.stderr}")
    
    # The task should not require approval
    approval_result = json.loads(result2.stdout)
    if not approval_result.get("approval_required"):
        print("+ Normal task correctly does not require approval")
    else:
        print("- Normal task incorrectly requires approval")
    
    # Test 3: Run the approval manager to process tasks
    print("\n3. Testing approval manager...")
    result3 = subprocess.run([
        sys.executable,
        str(Path("Skills") / "approval_manager.skill")
    ], capture_output=True, text=True, cwd=os.getcwd())
    
    print(f"Manager output: {result3.stdout}")
    if result3.stderr:
        print(f"Manager errors: {result3.stderr}")
    
    # Test 4: Check logging functionality
    print("\n4. Testing logging functionality...")
    result4 = subprocess.run([
        sys.executable,
        str(Path("Skills") / "log_approval_action.skill"),
        "test_task_123",
        "approval_required",
        "Test task requires approval for payment processing"
    ], capture_output=True, text=True, cwd=os.getcwd())
    
    if result4.returncode == 0:
        print("+ Logging functionality works")
    else:
        print(f"- Logging failed: {result4.stderr}")
    
    # Check if log file was created
    logs_dir = Path("Logs")
    log_files = list(logs_dir.glob("approval_log_test_task_123_*"))
    if log_files:
        print("+ Log file created successfully")
    else:
        print("- Log file was not created")
    
    print("\nApproval workflow testing completed!")


if __name__ == "__main__":
    test_approval_workflow()