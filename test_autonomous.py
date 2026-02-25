"""
Test the autonomous cycle functionality of FTE_Orchestrator
"""

from Agents.FTE_Orchestrator import FTE_Orchestrator
from Agents.Comms_Agent import Comms_Agent
from Agents.Finance_Agent import Finance_Agent
from Agents.Action_Agent import Action_Agent
import json
from pathlib import Path

def test_autonomous_cycle():
    print("[AUTO] Testing autonomous cycle functionality...")
    
    # Initialize orchestrator and agents
    orchestrator = FTE_Orchestrator()
    comms_agent = Comms_Agent()
    finance_agent = Finance_Agent()
    action_agent = Action_Agent()

    # Register agents
    orchestrator.register_agent('Comms_Agent', comms_agent)
    orchestrator.register_agent('Finance_Agent', finance_agent)
    orchestrator.register_agent('Action_Agent', action_agent)

    # Create a new task in Needs_Action to test the autonomous cycle
    test_task = {
        "task_id": "autotest_001",
        "type": "shell_command",
        "description": "Autonomous cycle test - list directory",
        "sensitive": False,
        "data": {
            "command": "dir" if os.name == 'nt' else "ls -la",
            "timeout": 10
        },
        "expected_outcome": "Directory listing retrieved",
        "priority": "low",
        "created_at": "2026-02-12T17:00:00Z"
    }
    
    # Write the task to Needs_Action
    with open("Needs_Action/autotest_task.json", "w") as f:
        json.dump(test_task, f, indent=2)
    
    print("[AUTO] Created test task in Needs_Action")
    
    # Run the autonomous cycle
    print("[AUTO] Starting autonomous processing cycle...")
    orchestrator.run_autonomous_cycle()
    
    print("[AUTO] Autonomous cycle completed.")
    
    # Check results
    done_count = len(list(Path("Done").glob("*.json")))
    error_count = len(list(Path("Error").glob("*.json")))
    needs_action_count = len(list(Path("Needs_Action").glob("*.json")))
    
    print(f"[AUTO] Results: {done_count} done, {error_count} error, {needs_action_count} remaining in Needs_Action")

if __name__ == "__main__":
    import os
    test_autonomous_cycle()