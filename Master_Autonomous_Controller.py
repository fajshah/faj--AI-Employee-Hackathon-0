"""
Master Autonomous Controller

Central control system for the Gold Tier AI Employee.
Manages all components: MCP Servers, Agents, Ralph Wiggum Loop, and Scheduler.

Features:
- Start/stop all components
- Health monitoring
- Graceful shutdown
- Process management
- Status reporting

Usage:
    python Master_Autonomous_Controller.py start     # Start all components
    python Master_Autonomous_Controller.py stop      # Stop all components
    python Master_Autonomous_Controller.py status    # Show status
    python Master_Autonomous_Controller.py restart   # Restart all
"""

import os
import sys
import time
import signal
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

load_dotenv('.env.gold')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/master_controller.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MasterController")

# Get script directory
SCRIPT_DIR = Path(__file__).parent.absolute()
PYTHON_EXECUTABLE = sys.executable


class Component:
    """Represents a single component (server, agent, etc.)"""
    
    def __init__(self, name: str, script: str, port: int = None, args: List[str] = None):
        self.name = name
        self.script = script
        self.port = port
        self.args = args or []
        self.process: Optional[subprocess.Popen] = None
        self.started_at: Optional[datetime] = None
        self.status = "stopped"
    
    def start(self) -> bool:
        """Start the component"""
        if self.process is not None and self.process.poll() is None:
            logger.warning(f"{self.name} is already running")
            return True
        
        try:
            script_path = SCRIPT_DIR / self.script
            
            if not script_path.exists():
                logger.error(f"Script not found: {script_path}")
                self.status = "error"
                return False
            
            cmd = [PYTHON_EXECUTABLE, str(script_path)] + self.args
            
            logger.info(f"Starting {self.name}: {cmd}")
            
            self.process = subprocess.Popen(
                cmd,
                cwd=str(SCRIPT_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.started_at = datetime.now()
            self.status = "running"
            
            logger.info(f"{self.name} started with PID {self.process.pid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start {self.name}: {e}")
            self.status = "error"
            return False
    
    def stop(self) -> bool:
        """Stop the component"""
        if self.process is None:
            self.status = "stopped"
            return True
        
        try:
            logger.info(f"Stopping {self.name} (PID {self.process.pid})")
            
            # Send SIGTERM first
            self.process.terminate()
            
            # Wait for graceful shutdown
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # Force kill if not responding
                logger.warning(f"Force killing {self.name}")
                self.process.kill()
                self.process.wait()
            
            self.process = None
            self.started_at = None
            self.status = "stopped"
            
            logger.info(f"{self.name} stopped")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop {self.name}: {e}")
            return False
    
    def is_running(self) -> bool:
        """Check if component is running"""
        if self.process is None:
            return False
        
        return self.process.poll() is None
    
    def get_uptime(self) -> str:
        """Get uptime string"""
        if not self.started_at:
            return "N/A"
        
        delta = datetime.now() - self.started_at
        total_seconds = int(delta.total_seconds())
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class MasterAutonomousController:
    """
    Master controller for all AI Employee components.
    """
    
    def __init__(self):
        """Initialize the master controller"""
        self.components: Dict[str, Component] = {}
        self.running = False
        self.health_check_interval = 30  # seconds
        
        self._register_components()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Master Autonomous Controller initialized")

    def _register_components(self):
        """Register all components"""
        # MCP Servers
        self.components['mcp_comms'] = Component(
            name="MCP Comms Server",
            script="MCP_Servers/MCP_Comms_Server.py",
            port=5001
        )
        
        self.components['mcp_social'] = Component(
            name="MCP Social Server",
            script="MCP_Servers/MCP_Social_Server.py",
            port=5002
        )
        
        self.components['mcp_finance'] = Component(
            name="MCP Finance Server",
            script="MCP_Servers/MCP_Finance_Server.py",
            port=5003
        )
        
        # Agents
        self.components['monitoring_agent'] = Component(
            name="Monitoring Agent",
            script="Agents/Monitoring_Agent.py"
        )
        
        self.components['orchestrator'] = Component(
            name="Orchestrator",
            script="Orchestrator_Gold.py"
        )
        
        # Ralph Wiggum Loop
        self.components['ralph_loop'] = Component(
            name="Ralph Wiggum Loop",
            script=".claude/plugins/ralph_wiggum_loop.py"
        )

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.stop_all()
        sys.exit(0)

    def start_all(self) -> Dict[str, bool]:
        """
        Start all components.
        
        Returns:
            Dictionary of component names to success status
        """
        logger.info("="*60)
        logger.info("STARTING ALL COMPONENTS")
        logger.info("="*60)
        
        print("\n" + "="*60)
        print("  GOLD TIER AI EMPLOYEE - STARTING ALL COMPONENTS")
        print("="*60)
        
        results = {}
        
        # Start MCP servers first
        for component_name in ['mcp_comms', 'mcp_social', 'mcp_finance']:
            component = self.components[component_name]
            print(f"\n[{len(results)+1}/6] Starting {component.name}...")
            results[component_name] = component.start()
            time.sleep(2)  # Give servers time to start
        
        # Then start agents
        for component_name in ['monitoring_agent', 'orchestrator', 'ralph_loop']:
            component = self.components[component_name]
            print(f"\n[{len(results)+1}/6] Starting {component.name}...")
            results[component_name] = component.start()
            time.sleep(1)
        
        self.running = True
        
        # Print summary
        print("\n" + "="*60)
        print("  STARTUP COMPLETE")
        print("="*60)
        
        success_count = sum(1 for v in results.values() if v)
        print(f"  Started: {success_count}/{len(results)} components")
        print("="*60)
        
        return results

    def stop_all(self) -> Dict[str, bool]:
        """
        Stop all components.
        
        Returns:
            Dictionary of component names to success status
        """
        logger.info("="*60)
        logger.info("STOPPING ALL COMPONENTS")
        logger.info("="*60)
        
        print("\n" + "="*60)
        print("  GOLD TIER AI EMPLOYEE - STOPPING ALL COMPONENTS")
        print("="*60)
        
        results = {}
        
        # Stop all components
        for name, component in self.components.items():
            print(f"\n  Stopping {component.name}...")
            results[name] = component.stop()
        
        self.running = False
        
        # Print summary
        print("\n" + "="*60)
        print("  SHUTDOWN COMPLETE")
        print("="*60)
        
        success_count = sum(1 for v in results.values() if v)
        print(f"  Stopped: {success_count}/{len(results)} components")
        print("="*60)
        
        return results

    def restart_all(self) -> Dict[str, bool]:
        """Restart all components"""
        logger.info("RESTARTING ALL COMPONENTS")
        
        self.stop_all()
        time.sleep(3)
        return self.start_all()

    def get_status(self) -> Dict[str, Any]:
        """
        Get status of all components.
        
        Returns:
            Status dictionary
        """
        status = {
            "running": self.running,
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }
        
        for name, component in self.components.items():
            status["components"][name] = {
                "name": component.name,
                "status": "running" if component.is_running() else "stopped",
                "port": component.port,
                "uptime": component.get_uptime(),
                "started_at": component.started_at.isoformat() if component.started_at else None
            }
        
        return status

    def print_status(self):
        """Print formatted status to console"""
        status = self.get_status()
        
        print("\n" + "="*60)
        print("  GOLD TIER AI EMPLOYEE - SYSTEM STATUS")
        print("="*60)
        print(f"  Timestamp: {status['timestamp']}")
        print(f"  Controller Running: {status['running']}")
        print("="*60)
        
        for name, comp_status in status["components"].items():
            icon = "✅" if comp_status["status"] == "running" else "❌"
            port_info = f" (Port {comp_status['port']})" if comp_status['port'] else ""
            uptime_info = f" - Uptime: {comp_status['uptime']}" if comp_status['uptime'] != "N/A" else ""
            
            print(f"\n  {icon} {comp_status['name']}{port_info}")
            print(f"      Status: {comp_status['status']}{uptime_info}")
        
        print("\n" + "="*60)

    def health_check(self) -> Dict[str, bool]:
        """
        Perform health check on all running components.
        
        Returns:
            Dictionary of component health status
        """
        health = {}
        
        for name, component in self.components.items():
            if component.port:
                # Check HTTP health endpoint
                try:
                    import requests
                    response = requests.get(f"http://localhost:{component.port}/health", timeout=5)
                    health[name] = response.status_code == 200
                except:
                    health[name] = component.is_running()
            else:
                health[name] = component.is_running()
        
        return health

    def run_continuous(self):
        """Run controller continuously with health monitoring"""
        logger.info("Starting continuous controller mode")
        
        print("\n" + "="*60)
        print("  CONTINUOUS MONITORING MODE")
        print("="*60)
        print("  Press Ctrl+C to stop all components")
        print("="*60)
        
        self.running = True
        last_health_check = 0
        
        try:
            while self.running:
                current_time = time.time()
                
                # Periodic health check
                if current_time - last_health_check >= self.health_check_interval:
                    health = self.health_check()
                    
                    all_healthy = all(health.values())
                    
                    if not all_healthy:
                        logger.warning("Some components unhealthy, attempting restart")
                        
                        for name, is_healthy in health.items():
                            if not is_healthy:
                                logger.info(f"Restarting {self.components[name].name}")
                                self.components[name].stop()
                                time.sleep(2)
                                self.components[name].start()
                    
                    last_health_check = current_time
                
                time.sleep(5)
                
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            self.stop_all()


def main():
    """Main entry point"""
    controller = MasterAutonomousController()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "start":
            controller.start_all()
            print("\nComponents started. Use 'stop' command to shut down.")
            
        elif command == "stop":
            controller.stop_all()
            
        elif command == "restart":
            controller.restart_all()
            
        elif command == "status":
            controller.print_status()
            
        elif command == "run":
            controller.run_continuous()
            
        elif command == "help":
            print("""
Master Autonomous Controller - Gold Tier AI Employee

USAGE:
    python Master_Autonomous_Controller.py [COMMAND]

COMMANDS:
    start       Start all components
    stop        Stop all components
    restart     Restart all components
    status      Show current status
    run         Run in continuous monitoring mode
    help        Show this help

EXAMPLES:
    python Master_Autonomous_Controller.py start
    python Master_Autonomous_Controller.py status
    python Master_Autonomous_Controller.py run
""")
        else:
            print(f"Unknown command: {command}")
            print("Use 'help' for usage information.")
    else:
        # Interactive mode
        print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     GOLD TIER AI EMPLOYEE                                 ║
║     Master Autonomous Controller                          ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

Select an action:
  1. Start All Components
  2. Stop All Components
  3. Show Status
  4. Run Continuous Mode
  5. Exit

""")
        
        choice = input("Enter choice (1-5): ").strip()
        
        if choice == "1":
            controller.start_all()
        elif choice == "2":
            controller.stop_all()
        elif choice == "3":
            controller.print_status()
        elif choice == "4":
            controller.run_continuous()
        elif choice == "5":
            print("Exiting...")
        else:
            print("Invalid choice")


if __name__ == "__main__":
    main()
