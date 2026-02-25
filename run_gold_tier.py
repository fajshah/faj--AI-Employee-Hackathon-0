"""
Gold Tier AI Employee System - Main Launcher
Starts all components of the Gold Tier system
"""

import subprocess
import sys
import time
from pathlib import Path


def start_component(name, script):
    """Start a component in a new process"""
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
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     🏆  GOLD TIER AI EMPLOYEE SYSTEM  🏆                 ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    processes = []
    
    # Start MCP Server
    p = start_component("MCP Server", "MCP_Server_Gold_Enhanced.py")
    if p:
        processes.append(p)
    
    # Start Orchestrator
    p = start_component("Orchestrator", "Agents/FTE_Orchestrator_Gold.py")
    if p:
        processes.append(p)
    
    # Start Scheduler
    p = start_component("Scheduler", "Scheduler_Gold.py")
    if p:
        processes.append(p)
    
    print("\n✅ All components started!")
    print("Press Ctrl+C to stop all\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping all components...")
        for p in processes:
            p.terminate()
        print("All components stopped.")


if __name__ == "__main__":
    main()
