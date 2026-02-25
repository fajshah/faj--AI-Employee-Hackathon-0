"""
Run All Gold Tier Components
Starts all servers, agents, and watchers
"""

import subprocess
import sys
import time
from pathlib import Path


def start_component(name, script):
    """Start component"""
    if Path(script).exists():
        print(f"Starting {name}...")
        process = subprocess.Popen([sys.executable, script])
        time.sleep(2)
        return process
    else:
        print(f"Script not found: {script}")
        return None


def main():
    print("""
+======================================================================+
|                                                                      |
|     GOLD TIER AI EMPLOYEE SYSTEM - STARTING                         |
|                                                                      |
+======================================================================+
    """)
    
    processes = []
    
    # MCP Servers
    processes.append(start_component("MCP Comms", "MCP_Servers/MCP_Comms_Server.py"))
    processes.append(start_component("MCP Social", "MCP_Servers/MCP_Social_Server.py"))
    processes.append(start_component("MCP Finance", "MCP_Servers/MCP_Finance_Server.py"))
    
    # Agents
    processes.append(start_component("Orchestrator", "Agents/Orchestrator_Agent.py"))
    
    # Scheduler
    processes.append(start_component("Scheduler", "Scheduler/Gold_Tier_Scheduler.py"))
    
    # Watchers
    processes.append(start_component("Gmail Watcher", "Gmail_Watcher.py"))
    processes.append(start_component("WhatsApp Watcher", "WhatsApp_Watcher.py"))
    processes.append(start_component("LinkedIn Watcher", "LinkedIn_Watcher.py"))
    
    print("\n✅ All components started!")
    print("Press Ctrl+C to stop all\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping all components...")
        for p in processes:
            if p:
                p.terminate()
        print("All components stopped.")


if __name__ == "__main__":
    main()
