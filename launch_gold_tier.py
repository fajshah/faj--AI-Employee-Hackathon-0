"""
Gold Tier System Launcher
Starts all Gold Tier components with a single command

Usage:
    python launch_gold_tier.py              # Start all components
    python launch_gold_tier.py --mcp        # Start only MCP Server
    python launch_gold_tier.py --orch       # Start only Orchestrator
    python launch_gold_tier.py --watchers   # Start only watchers
"""

import os
import sys
import subprocess
import threading
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv('.env.gold')

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_banner():
    """Print Gold Tier banner"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     🏆  GOLD TIER AI EMPLOYEE SYSTEM  🏆                 ║
║                                                           ║
║     Real External Actions • API Integration              ║
║     Gmail • LinkedIn • WhatsApp • Link Opening           ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """
    print(Colors.OKCYAN + banner + Colors.ENDC)

def check_prerequisites():
    """Check if prerequisites are met"""
    print(Colors.OKBLUE + "Checking prerequisites..." + Colors.ENDC)

    issues = []

    # Check .env.gold exists
    if not os.path.exists('.env.gold'):
        issues.append("❌ .env.gold not found. Please configure credentials.")
    else:
        print("✅ .env.gold found")

    # Check tokens directory for Gmail
    token_file = os.getenv('GMAIL_TOKEN_FILE', 'tokens/gmail_token.json')
    if not os.path.exists(token_file):
        issues.append(f"⚠️  Gmail token not found. Run: python authenticate_gmail.py")
    else:
        print("✅ Gmail token found")

    # Check required directories
    required_dirs = ['Logs', 'Needs_Action', 'Plans', 'Pending_Approval', 'Approved', 'Done', 'Error']
    for dir_name in required_dirs:
        Path(dir_name).mkdir(exist_ok=True)
    print("✅ Directories created/verified")

    if issues:
        print(Colors.WARNING + "\nPrerequisites Warnings:" + Colors.ENDC)
        for issue in issues:
            print(f"  {issue}")
        print()

    return len([i for i in issues if '❌' in i]) == 0

def start_mcp_server():
    """Start Gold Tier MCP Server"""
    print(Colors.OKGREEN + "\n📡 Starting Gold Tier MCP Server..." + Colors.ENDC)
    try:
        process = subprocess.Popen(
            [sys.executable, 'MCP_Server_Gold.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        time.sleep(2)  # Wait for server to start
        print("✅ MCP Server started on http://localhost:5001")
        return process
    except Exception as e:
        print(Colors.FAIL + f"❌ Failed to start MCP Server: {e}" + Colors.ENDC)
        return None

def start_orchestrator():
    """Start Gold Tier Orchestrator"""
    print(Colors.OKGREEN + "\n🤖 Starting Gold Tier Orchestrator..." + Colors.ENDC)
    try:
        process = subprocess.Popen(
            [sys.executable, 'Orchestrator_Gold.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print("✅ Orchestrator started")
        return process
    except Exception as e:
        print(Colors.FAIL + f"❌ Failed to start Orchestrator: {e}" + Colors.ENDC)
        return None

def start_watchers():
    """Start Gold Tier Watchers"""
    processes = []

    # Gmail Watcher
    if os.path.exists('Gmail_Watcher_Gold.py'):
        print(Colors.OKGREEN + "\n📧 Starting Gmail Watcher..." + Colors.ENDC)
        try:
            p = subprocess.Popen([sys.executable, 'Gmail_Watcher_Gold.py'])
            processes.append(('Gmail Watcher', p))
        except Exception as e:
            print(Colors.FAIL + f"❌ Failed to start Gmail Watcher: {e}" + Colors.ENDC)

    # LinkedIn Poster
    if os.path.exists('LinkedIn_Poster_Gold.py'):
        print(Colors.OKGREEN + "\n💼 Starting LinkedIn Poster..." + Colors.ENDC)
        try:
            p = subprocess.Popen([sys.executable, 'LinkedIn_Poster_Gold.py'])
            processes.append(('LinkedIn Poster', p))
        except Exception as e:
            print(Colors.FAIL + f"❌ Failed to start LinkedIn Poster: {e}" + Colors.ENDC)

    # WhatsApp Watcher
    if os.path.exists('WhatsApp_Watcher_Gold.py'):
        print(Colors.OKGREEN + "\n💬 Starting WhatsApp Watcher..." + Colors.ENDC)
        try:
            p = subprocess.Popen([sys.executable, 'WhatsApp_Watcher_Gold.py'])
            processes.append(('WhatsApp Watcher', p))
        except Exception as e:
            print(Colors.FAIL + f"❌ Failed to start WhatsApp Watcher: {e}" + Colors.ENDC)

    return processes

def run_component(component):
    """Run a single component in foreground"""
    try:
        subprocess.run([sys.executable, component], check=True)
    except KeyboardInterrupt:
        print(f"\n{component} stopped.")
    except Exception as e:
        print(f"Error running {component}: {e}")

def main():
    """Main launcher function"""
    print_banner()

    # Parse command line arguments
    mode = 'all'
    if len(sys.argv) > 1:
        if '--mcp' in sys.argv:
            mode = 'mcp'
        elif '--orch' in sys.argv:
            mode = 'orch'
        elif '--watchers' in sys.argv:
            mode = 'watchers'
        elif '--auth' in sys.argv:
            # Just run authentication
            print(Colors.OKBLUE + "Running Gmail authentication..." + Colors.ENDC)
            os.system(f'{sys.executable} authenticate_gmail.py')
            return

    # Check prerequisites
    if not check_prerequisites():
        print(Colors.FAIL + "\n❌ Prerequisites not met. Please fix issues and try again." + Colors.ENDC)
        return

    print(Colors.OKBLUE + "\nStarting Gold Tier components..." + Colors.ENDC)

    processes = []

    if mode == 'all' or mode == 'mcp':
        # Start MCP Server
        mcp_process = start_mcp_server()
        if mcp_process:
            processes.append(('MCP Server', mcp_process))

    if mode == 'all' or mode == 'orch':
        # Start Orchestrator
        orch_process = start_orchestrator()
        if orch_process:
            processes.append(('Orchestrator', orch_process))

    if mode == 'all' or mode == 'watchers':
        # Start Watchers
        watcher_processes = start_watchers()
        processes.extend(watcher_processes)

    # Print status
    print(Colors.OKCYAN + "\n" + "=" * 60 + Colors.ENDC)
    print(Colors.OKGREEN + "✅ Gold Tier System is running!" + Colors.ENDC)
    print(Colors.OKCYAN + "=" * 60 + Colors.ENDC)

    print(f"\n📊 Active Components ({len(processes)}):")
    for name, _ in processes:
        print(f"  • {name}")

    print("\n" + Colors.WARNING + "Press Ctrl+C to stop all components" + Colors.ENDC)

    # Wait for processes
    try:
        while True:
            time.sleep(1)

            # Check if any process has died
            for name, process in processes:
                if process.poll() is not None:
                    print(Colors.WARNING + f"\n⚠️  {name} has stopped" + Colors.ENDC)

    except KeyboardInterrupt:
        print(Colors.OKCYAN + "\n\nStopping Gold Tier System..." + Colors.ENDC)

        # Terminate all processes
        for name, process in processes:
            try:
                process.terminate()
                print(f"  • Stopped {name}")
            except Exception:
                pass

        print(Colors.OKGREEN + "\n✅ Gold Tier System stopped." + Colors.ENDC)

if __name__ == "__main__":
    main()
