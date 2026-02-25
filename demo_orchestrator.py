"""
Demo script to showcase the FTE_Orchestrator workflow
"""

import json
import os
from datetime import datetime
from pathlib import Path

# Import our agents
from Agents.FTE_Orchestrator import FTE_Orchestrator
from Agents.Comms_Agent import Comms_Agent
from Agents.Finance_Agent import Finance_Agent
from Agents.Action_Agent import Action_Agent
from Agents.Agent_Coordinator import AgentCoordinator

def demo_workflow():
    print("[START] Starting FTE_Orchestrator Demo")
    print("="*50)
    
    # Initialize the orchestrator
    orchestrator = FTE_Orchestrator()
    
    # Initialize agents
    comms_agent = Comms_Agent()
    finance_agent = Finance_Agent()
    action_agent = Action_Agent()
    
    # Register agents with the orchestrator
    orchestrator.register_agent("Comms_Agent", comms_agent)
    orchestrator.register_agent("Finance_Agent", finance_agent)
    orchestrator.register_agent("Action_Agent", action_agent)
    
    print("[DONE] Agents registered with orchestrator")
    
    # Show initial system status
    print("\n[INFO] Initial System Status:")
    status = orchestrator.get_system_status()
    print(json.dumps(status, indent=2))
    
    # Move the sample task from Inbox to Needs_Action
    inbox_path = Path("Inbox") / "sample_task.json"
    needs_action_path = Path("Needs_Action") / "sample_task.json"
    
    if inbox_path.exists():
        os.rename(str(inbox_path), str(needs_action_path))
        print(f"\n[MOVE] Moved sample task from Inbox to Needs_Action")
    
    # Process the task
    print(f"\n[PROC] Processing tasks in Needs_Action...")
    orchestrator.process_needs_action()
    
    # Show updated system status
    print("\n[INFO] Updated System Status:")
    status = orchestrator.get_system_status()
    print(json.dumps(status, indent=2))
    
    # Run autonomous cycle (though there won't be any more tasks)
    print(f"\n[AUTO] Starting autonomous processing cycle...")
    orchestrator.run_autonomous_cycle()
    
    print(f"\n[DONE] Demo completed successfully!")
    
    # Show final status
    print("\n[INFO] Final System Status:")
    status = orchestrator.get_system_status()
    print(json.dumps(status, indent=2))

def create_more_sample_tasks():
    """Create additional sample tasks to demonstrate different workflows"""
    
    # Create a finance task
    finance_task = {
        "task_id": "finance_001",
        "type": "invoice",
        "description": "Create invoice for client",
        "sensitive": False,
        "data": {
            "customer_name": "Acme Corp",
            "customer_email": "billing@acme.com",
            "amount": "2500.00",
            "due_date": "2026-03-12T00:00:00Z",
            "items": [
                {"item": "Software Development", "quantity": 10, "price": "250.00"}
            ]
        },
        "expected_outcome": "Invoice created and sent to client",
        "priority": "high",
        "created_at": "2026-02-12T11:00:00Z"
    }
    
    # Create a sensitive task
    sensitive_task = {
        "task_id": "sensitive_001",
        "type": "system",
        "description": "Restart production server",
        "sensitive": True,
        "data": {
            "command": "sudo systemctl restart production-service",
            "server": "prod-001"
        },
        "expected_outcome": "Production server restarted",
        "priority": "critical",
        "created_at": "2026-02-12T12:00:00Z"
    }
    
    # Write tasks to Needs_Action directory
    with open("Needs_Action/finance_task.json", "w") as f:
        json.dump(finance_task, f, indent=2)
    
    with open("Needs_Action/sensitive_task.json", "w") as f:
        json.dump(sensitive_task, f, indent=2)
    
    print("[DONE] Created additional sample tasks in Needs_Action directory")

if __name__ == "__main__":
    # Create additional sample tasks
    create_more_sample_tasks()
    
    # Run the demo
    demo_workflow()