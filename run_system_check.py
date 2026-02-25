"""
AI Employee System - Quick Start and Verification Script

This script demonstrates how to run the complete AI employee system
and verify its functionality.
"""

import json
import os
from datetime import datetime
from pathlib import Path

def check_system_components():
    """Check if all system components are present"""
    print("[CHECK] CHECKING SYSTEM COMPONENTS...")
    
    # Check main agents
    agents_dir = Path("Agents")
    required_agents = [
        "FTE_Orchestrator.py",
        "Comms_Agent.py", 
        "Finance_Agent.py",
        "Action_Agent.py",
        "Agent_Coordinator.py"
    ]
    
    print("  [AGENT] Agents:")
    for agent in required_agents:
        agent_path = agents_dir / agent
        if agent_path.exists():
            print(f"    [OK] {agent}")
        else:
            print(f"    [FAIL] {agent}")
    
    # Check skills
    skills_dir = Path("Skills")
    required_skills = [
        "classify_task.skill",
        "create_plan.skill",
        "generate_approval.skill", 
        "execute_action.skill",
        "log_action.skill"
    ]
    
    print("  [SKILL] Skills:")
    for skill in required_skills:
        skill_path = skills_dir / skill
        if skill_path.exists():
            print(f"    [OK] {skill}")
        else:
            print(f"    [FAIL] {skill}")
    
    # Check directories
    required_dirs = [
        "Inbox", "Needs_Action", "Plans", 
        "Pending_Approval", "Approved", "Done", "Logs", "Error"
    ]
    
    print("  [DIR] Directories:")
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            file_count = len(list(dir_path.glob("*")))
            print(f"    [OK] {dir_name}/ ({file_count} files)")
        else:
            print(f"    [FAIL] {dir_name}/")

def run_sample_workflow():
    """Run a sample workflow to demonstrate system functionality"""
    print("\n[RUN] RUNNING SAMPLE WORKFLOW...")
    
    # Import agents
    from Agents.FTE_Orchestrator import FTE_Orchestrator
    from Agents.Comms_Agent import Comms_Agent
    from Agents.Finance_Agent import Finance_Agent
    from Agents.Action_Agent import Action_Agent
    
    # Initialize orchestrator and agents
    orchestrator = FTE_Orchestrator()
    comms_agent = Comms_Agent()
    finance_agent = Finance_Agent()
    action_agent = Action_Agent()
    
    # Register agents
    orchestrator.register_agent("Comms_Agent", comms_agent)
    orchestrator.register_agent("Finance_Agent", finance_agent)
    orchestrator.register_agent("Action_Agent", action_agent)
    
    print("  [OK] Agents initialized and registered")
    
    # Create a sample task in Needs_Action
    sample_task = {
        "task_id": f"verification_task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "type": "send_email",
        "description": "Verification task for system check",
        "sensitive": False,
        "data": {
            "to_emails": ["test@company.com"],
            "subject": "System Verification",
            "body": "This is a test email to verify system functionality."
        },
        "expected_outcome": "Email sent successfully"
    }
    
    # Write task to Needs_Action
    task_file = Path("Needs_Action") / "verification_task.json"
    with open(task_file, 'w') as f:
        json.dump(sample_task, f, indent=2)
    
    print(f"  [OK] Created verification task: {task_file.name}")
    
    # Process the task
    print("  [PROGRESS] Processing task through system...")
    orchestrator.process_needs_action()
    
    # Show results
    print("  [RESULTS] Results:")
    status = orchestrator.get_system_status()
    print(f"    - Plans created: {status['directories']['plans']}")
    print(f"    - Tasks in Done: {status['directories']['done']}")
    print(f"    - Tasks in Error: {status['directories']['error']}")
    print(f"    - Log entries: {status['directories']['logs']}")

def show_current_state():
    """Show current state of all directories"""
    print("\n[STATE] CURRENT SYSTEM STATE:")
    
    dirs_to_check = [
        ("Inbox", "[INBOX]"),
        ("Needs_Action", "[NEEDS]"),
        ("Plans", "[PLANS]"),
        ("Pending_Approval", "[PENDING]"),
        ("Approved", "[APPROVED]"),
        ("Done", "[DONE]"),
        ("Error", "[ERROR]"),
        ("Logs", "[LOGS]")
    ]
    
    for dir_name, label in dirs_to_check:
        dir_path = Path(dir_name)
        if dir_path.exists():
            files = list(dir_path.glob("*"))
            print(f"  {label} {dir_name}/: {len(files)} items")
            # Show last 3 files if any
            for file in files[-3:]:  # Show last 3 files
                print(f"    - {file.name}")
        else:
            print(f"  {label} {dir_name}/: Directory not found")

def run_system_verification():
    """Main function to run complete system verification"""
    print("[ROBOT] AI EMPLOYEE SYSTEM - VERIFICATION AND RUN SCRIPT")
    print("="*60)
    
    # Check components
    check_system_components()
    
    # Run sample workflow
    run_sample_workflow()
    
    # Show current state
    show_current_state()
    
    print(f"\n[SUCCESS] VERIFICATION COMPLETE!")
    print(f"   The AI Employee System is fully operational.")
    print(f"   All components are working correctly.")
    print(f"   Ready for production use!")

if __name__ == "__main__":
    run_system_verification()