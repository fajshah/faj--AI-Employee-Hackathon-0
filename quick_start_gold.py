"""
Gold Tier - Quick Start Script
Run this to set up and start the Gold Tier system

Usage:
    python quick_start_gold.py          # Full setup and start
    python quick_start_gold.py --setup  # Setup only
    python quick_start_gold.py --start  # Start only (after setup)
"""

import os
import sys
import subprocess
import time
from pathlib import Path


def print_banner():
    """Print Gold Tier banner"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     🏆  GOLD TIER AUTONOMOUS AI EMPLOYEE  🏆             ║
║                                                           ║
║     Complete Setup & Launch Script                       ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_python_version():
    """Check Python version"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python 3.8+ required, found {version.major}.{version.minor}")
        return False


def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    
    requirements_file = Path('requirements_gold.txt')
    if requirements_file.exists():
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)])
            print("   ✅ Dependencies installed")
            return True
        except subprocess.CalledProcessError:
            print("   ❌ Failed to install dependencies")
            return False
    else:
        print("   ⚠️  requirements_gold.txt not found, installing basic packages...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'flask', 'requests', 'python-dotenv', 'schedule'])
            print("   ✅ Basic packages installed")
            return True
        except subprocess.CalledProcessError:
            print("   ❌ Failed to install basic packages")
            return False


def create_directories():
    """Create required directories"""
    print("\n📁 Creating directories...")
    
    dirs = [
        'Inbox', 'Needs_Action', 'Plans', 'Done', 'Logs',
        'Pending_Approval', 'Approved', 'Error', 'Accounting',
        'Scheduled_Tasks', 'Gmail_Inbox', 'WhatsApp_Inbox',
        'LinkedIn_Posts', 'tokens'
    ]
    
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"   ✅ {dir_name}/")
    
    return True


def create_env_file():
    """Create .env.gold file if it doesn't exist"""
    print("\n⚙️  Checking environment configuration...")
    
    env_file = Path('.env.gold')
    if env_file.exists():
        print(f"   ✅ .env.gold exists")
        return True
    else:
        print(f"   ⚠️  .env.gold not found, creating template...")
        
        env_content = """# ===========================================
# GOLD TIER API CREDENTIALS
# ===========================================

# -------------------------------------------
# GMAIL API (OAuth 2.0)
# -------------------------------------------
GMAIL_TOKEN_FILE=tokens/gmail_token.json

# -------------------------------------------
# LINKEDIN API
# -------------------------------------------
LINKEDIN_ACCESS_TOKEN=your_linkedin_access_token_here
LINKEDIN_PERSON_ID=your_linkedin_person_id_here

# -------------------------------------------
# WHATSAPP BUSINESS API
# -------------------------------------------
WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token_here
WHATSAPP_PHONE_NUMBER_ID=your_whatsapp_phone_number_id_here
WHATSAPP_API_VERSION=v18.0

# -------------------------------------------
# ODOO ERP
# -------------------------------------------
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USER=admin
ODOO_PASSWORD=admin

# -------------------------------------------
# SYSTEM CONFIGURATION
# -------------------------------------------
MCP_SERVER_URL=http://localhost:5001
ADMIN_EMAIL=admin@example.com

# -------------------------------------------
# SCHEDULER CONFIGURATION
# -------------------------------------------
GMAIL_SCAN_INTERVAL=10
WHATSAPP_SCAN_INTERVAL=15
INBOX_SCAN_INTERVAL=5
LINKEDIN_POST_TIME=09:00
CEO_BRIEFING_DAY=monday
CEO_BRIEFING_TIME=08:00
"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print(f"   ✅ .env.gold created - PLEASE EDIT WITH YOUR CREDENTIALS")
        return True


def authenticate_gmail():
    """Run Gmail authentication"""
    print("\n🔐 Gmail Authentication...")
    
    auth_script = Path('authenticate_gmail.py')
    if auth_script.exists():
        print("   Running Gmail OAuth authentication...")
        print("   ℹ️  A browser window will open for authentication")
        
        response = input("   Proceed with Gmail authentication? (y/n): ")
        if response.lower() == 'y':
            subprocess.run([sys.executable, str(auth_script)])
            print("   ✅ Gmail authentication complete")
        else:
            print("   ⚠️  Skipping Gmail authentication")
    else:
        print("   ⚠️  authenticate_gmail.py not found")
    
    return True


def start_services():
    """Start all Gold Tier services"""
    print("\n🚀 Starting Gold Tier Services...")
    
    services = [
        ("MCP Server", "MCP_Server_Gold_Enhanced.py"),
        ("Orchestrator", "Agents/FTE_Orchestrator_Gold.py"),
        ("Scheduler", "Scheduler_Gold.py"),
        ("Gold Agent", "Gold_Tier_Agent.py")
    ]
    
    processes = []
    
    for service_name, script_path in services:
        script = Path(script_path)
        if script.exists():
            print(f"   Starting {service_name}...")
            try:
                # Start in background
                process = subprocess.Popen(
                    [sys.executable, str(script)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                processes.append((service_name, process))
                time.sleep(2)  # Wait for service to start
                print(f"   ✅ {service_name} started")
            except Exception as e:
                print(f"   ❌ Failed to start {service_name}: {e}")
        else:
            print(f"   ⚠️  {script_path} not found")
    
    return processes


def wait_for_services():
    """Wait for services to be ready"""
    print("\n⏳ Waiting for services to initialize...")
    time.sleep(5)
    
    # Check MCP Server health
    try:
        import requests
        response = requests.get('http://localhost:5001/health', timeout=10)
        if response.status_code == 200:
            print("   ✅ MCP Server is healthy")
        else:
            print("   ⚠️  MCP Server returned unhealthy status")
    except Exception as e:
        print(f"   ⚠️  Could not connect to MCP Server: {e}")


def print_status():
    """Print final status"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     ✅  GOLD TIER SYSTEM READY  ✅                       ║
║                                                           ║
║     Services Running:                                     ║
║     • MCP Server (port 5001)                             ║
║     • Orchestrator                                        ║
║     • Scheduler                                           ║
║     • Gold Agent                                          ║
║                                                           ║
║     Next Steps:                                           ║
║     1. Edit .env.gold with your API credentials          ║
║     2. Run: python authenticate_gmail.py                 ║
║     3. Create tasks in Needs_Action/                     ║
║     4. Monitor logs in Logs/                             ║
║                                                           ║
║     Press Ctrl+C to stop all services                    ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)


def main():
    """Main setup and launch function"""
    print_banner()
    
    import argparse
    parser = argparse.ArgumentParser(description='Gold Tier Quick Start')
    parser.add_argument('--setup', action='store_true', help='Setup only')
    parser.add_argument('--start', action='store_true', help='Start only')
    args = parser.parse_args()
    
    # Check Python version
    if not check_python_version():
        print("\n❌ Python version check failed. Please upgrade to Python 3.8+")
        return
    
    # Setup phase
    if not args.start:
        print("\n" + "=" * 60)
        print("  SETUP PHASE")
        print("=" * 60)
        
        install_dependencies()
        create_directories()
        create_env_file()
        
        if not args.setup:
            authenticate_gmail()
    
    # Start phase
    if not args.setup:
        print("\n" + "=" * 60)
        print("  START PHASE")
        print("=" * 60)
        
        processes = start_services()
        wait_for_services()
        print_status()
        
        # Keep running
        try:
            while True:
                time.sleep(1)
                
                # Check if processes are still running
                for name, process in processes:
                    if process.poll() is not None:
                        print(f"\n⚠️  {name} has stopped")
                        
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping Gold Tier services...")
            
            for name, process in processes:
                try:
                    process.terminate()
                    print(f"   Stopped {name}")
                except:
                    pass
            
            print("\n✅ All services stopped.")


if __name__ == "__main__":
    main()
