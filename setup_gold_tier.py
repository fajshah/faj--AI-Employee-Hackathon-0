"""
Gold Tier AI Employee System - Complete Setup Script
Creates all folders, files, and configurations for a fully functional system

Usage: python setup_gold_tier.py
"""

import os
import json
from pathlib import Path
from datetime import datetime


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_success(text):
    """Print success message"""
    print(f"  [OK] {text}")


def print_info(text):
    """Print info message"""
    print(f"  [INFO] {text}")


def print_banner():
    """Print banner without Unicode box characters"""
    print("""
+===========================================================+
|                                                           |
|     GOLD TIER SETUP SCRIPT                                |
|                                                           |
+===========================================================+
    """)


def create_folders():
    """Create all required directories"""
    print_header("Creating Folder Structure")
    
    folders = [
        'Inbox',
        'Needs_Action',
        'WhatsApp_Inbox',
        'Gmail_Inbox',
        'LinkedIn_Posts',
        'Plans',
        'Done',
        'Logs',
        'Logs/Error',
        'Pending_Approval',
        'Approved',
        'Accounting',
        'Skills',
        'Agents',
        'Scheduled_Tasks',
        'Gmail_Archive',
        'Approval_History',
        'Error',
        'tokens'
    ]
    
    for folder in folders:
        path = Path(folder)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print_success(f"Created: {folder}/")
        else:
            print_success(f"Exists: {folder}/")
    
    return folders


def create_environment_file():
    """Create .env file with configuration"""
    print_header("Creating Environment Configuration")
    
    env_content = """# ===========================================
# GOLD TIER AI EMPLOYEE SYSTEM - ENVIRONMENT
# ===========================================

# -------------------------------------------
# GMAIL API (OAuth 2.0)
# -------------------------------------------
GMAIL_CLIENT_ID=your_gmail_client_id_here
GMAIL_CLIENT_SECRET=your_gmail_client_secret_here
GMAIL_REDIRECT_URI=http://localhost:8080/callback
GMAIL_TOKEN_FILE=tokens/gmail_token.json
GMAIL_SCOPES=https://www.googleapis.com/auth/gmail.send,https://www.googleapis.com/auth/gmail.readonly

# -------------------------------------------
# SMTP FALLBACK
# -------------------------------------------
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password_here

# -------------------------------------------
# LINKEDIN API
# -------------------------------------------
LINKEDIN_CLIENT_ID=your_linkedin_client_id_here
LINKEDIN_CLIENT_SECRET=your_linkedIn_client_secret_here
LINKEDIN_ACCESS_TOKEN=your_linkedin_access_token_here
LINKEDIN_PERSON_ID=your_linkedin_person_id_here
LINKEDIN_ORGANIZATION_ID=your_linkedin_organization_id_here

# -------------------------------------------
# WHATSAPP BUSINESS API
# -------------------------------------------
WHATSAPP_PHONE_NUMBER_ID=your_whatsapp_phone_number_id_here
WHATSAPP_BUSINESS_ACCOUNT_ID=your_whatsapp_business_account_id_here
WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token_here
WHATSAPP_API_VERSION=v18.0

# -------------------------------------------
# ODOO ERP
# -------------------------------------------
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USER=admin
ODOO_PASSWORD=admin
ODOO_API_KEY=your_odoo_api_key_here

# -------------------------------------------
# SYSTEM CONFIGURATION
# -------------------------------------------
ADMIN_EMAIL=admin@example.com
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=5001
MCP_SERVER_URL=http://localhost:5001
LOG_LEVEL=INFO

# -------------------------------------------
# SCHEDULER CONFIGURATION
# -------------------------------------------
GMAIL_SCAN_INTERVAL=10
WHATSAPP_SCAN_INTERVAL=15
INBOX_SCAN_INTERVAL=5
LINKEDIN_POST_TIME=09:00
CEO_BRIEFING_DAY=monday
CEO_BRIEFING_TIME=08:00
ACCOUNTING_SYNC_DAY=friday
ACCOUNTING_SYNC_TIME=17:00

# -------------------------------------------
# CLAUDE API (Optional for enhanced reasoning)
# -------------------------------------------
CLAUDE_API_KEY=your_claude_api_key_here
"""
    
    env_file = Path('.env')
    if not env_file.exists():
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print_success("Created: .env")
    else:
        print_info(".env already exists")
    
    # Create .env.example
    env_example = Path('.env.example')
    with open(env_example, 'w', encoding='utf-8') as f:
        f.write("# Copy this file to .env and fill in your actual credentials\n")
        f.write(env_content)
    print_success("Created: .env.example")


def create_requirements_file():
    """Create requirements.txt"""
    print_header("Creating Requirements File")
    
    requirements = """# Gold Tier AI Employee System - Dependencies

# Core
requests>=2.31.0
python-dotenv>=1.0.0
flask>=3.0.0

# Google API (Gmail)
google-auth>=2.25.0
google-auth-oauthlib>=1.2.0
google-auth-httplib2>=0.2.0
google-api-python-client>=2.110.0

# Scheduling
schedule>=1.2.0
APScheduler>=3.10.0

# Utilities
python-dateutil>=2.8.0
pytz>=2023.3

# Logging
colorlog>=6.8.0

# Testing
pytest>=7.4.0
pytest-cov>=4.1.0
"""
    
    req_file = Path('requirements.txt')
    with open(req_file, 'w', encoding='utf-8') as f:
        f.write(requirements)
    print_success("Created: requirements.txt")


def create_task_templates():
    """Create JSON task templates"""
    print_header("Creating Task Templates")
    
    # Gmail Email Task
    gmail_task = {
        "task_id": "gmail_email_001",
        "task_type": "email",
        "action_type": "send_email",
        "priority": "MEDIUM",
        "title": "Send Project Update to Client",
        "description": "Send weekly project status update",
        "assigned_to": "Comms_Agent",
        "deadline": datetime.now().strftime('%Y-%m-%d'),
        "status": "pending",
        "sensitive": False,
        "recipient_email": "client@example.com",
        "cc": "manager@company.com",
        "subject": "Weekly Project Status Update",
        "message": "Dear Client,\n\nHere is your weekly project update...\n\nBest regards,\nYour Team",
        "details": {
            "email_type": "status_update",
            "project_name": "Client Project"
        },
        "created_at": datetime.now().isoformat(),
        "source": "gmail_watcher"
    }
    
    with open('Needs_Action/send_email_task.json', 'w', encoding='utf-8') as f:
        json.dump(gmail_task, f, indent=2)
    print_success("Created: Needs_Action/send_email_task.json")
    
    # WhatsApp Task
    whatsapp_task = {
        "task_id": "whatsapp_001",
        "task_type": "whatsapp",
        "action_type": "send_whatsapp",
        "priority": "HIGH",
        "title": "WhatsApp Meeting Reminder",
        "description": "Send meeting reminder to team",
        "assigned_to": "Comms_Agent",
        "deadline": datetime.now().strftime('%Y-%m-%d'),
        "status": "pending",
        "sensitive": False,
        "recipient_phone": "+1234567890",
        "message": "Hi Team! Reminder: Meeting today at 2 PM EST.",
        "message_type": "text",
        "details": {
            "message_category": "meeting_reminder"
        },
        "created_at": datetime.now().isoformat(),
        "source": "whatsapp_watcher"
    }
    
    with open('WhatsApp_Inbox/whatsapp_task.json', 'w', encoding='utf-8') as f:
        json.dump(whatsapp_task, f, indent=2)
    print_success("Created: WhatsApp_Inbox/whatsapp_task.json")
    
    # LinkedIn Post Task
    linkedin_task = {
        "task_id": "linkedin_001",
        "task_type": "linkedin_post",
        "action_type": "post_linkedin",
        "priority": "MEDIUM",
        "title": "Business Post - Product Launch",
        "description": "Post about new product launch",
        "assigned_to": "Social_Agent",
        "deadline": datetime.now().strftime('%Y-%m-%d'),
        "status": "pending",
        "sensitive": False,
        "platform": "linkedin",
        "content": "Launching new AI Employee system today! #AI #Automation",
        "hashtags": ["AI", "Automation", "ProductLaunch"],
        "visibility": "PUBLIC",
        "details": {
            "post_type": "product_announcement"
        },
        "created_at": datetime.now().isoformat(),
        "source": "linkedin_watcher"
    }
    
    with open('LinkedIn_Posts/linkedin_task.json', 'w', encoding='utf-8') as f:
        json.dump(linkedin_task, f, indent=2)
    print_success("Created: LinkedIn_Posts/linkedin_task.json")
    
    # Odoo Invoice Task
    odoo_task = {
        "task_id": "odoo_invoice_001",
        "task_type": "finance",
        "action_type": "create_invoice",
        "priority": "HIGH",
        "title": "Create Invoice for ABC Corp",
        "description": "Create invoice for consulting services",
        "assigned_to": "Finance_Agent",
        "deadline": datetime.now().strftime('%Y-%m-%d'),
        "status": "pending",
        "sensitive": True,
        "client": "ABC Corp",
        "amount": 1500.00,
        "description_detail": "Consulting Services - January 2026",
        "details": {
            "invoice_type": "service",
            "payment_terms": "30 days"
        },
        "created_at": datetime.now().isoformat(),
        "source": "manual"
    }
    
    with open('Needs_Action/odoo_invoice_task.json', 'w', encoding='utf-8') as f:
        json.dump(odoo_task, f, indent=2)
    print_success("Created: Needs_Action/odoo_invoice_task.json")


def create_readme():
    """Create README.md"""
    print_header("Creating README")
    
    readme_content = """# 🏆 Gold Tier AI Employee System

Autonomous AI Employee with Gmail, WhatsApp, LinkedIn, and Odoo integration.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
# Edit .env with your API credentials

# Start system
python run_gold_tier.py
```

## Components

- **Watchers**: Gmail, WhatsApp, LinkedIn
- **Orchestrator**: Task coordination with Claude reasoning
- **MCP Server**: External API actions
- **Scheduler**: Automation
- **Agents**: Comms, Finance, Social, Action

## Documentation

See GOLD_TIER_GUIDE.md for complete setup instructions.
"""
    
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print_success("Created: README.md")


def create_system_files():
    """Create main system files"""
    print_header("Creating System Files")
    
    # Check for existing Gold Tier files
    gold_files = [
        'Gold_Tier_Agent.py',
        'MCP_Server_Gold_Enhanced.py',
        'Scheduler_Gold.py',
        'Gmail_Watcher_Gold.py',
        'WhatsApp_Watcher_Gold.py',
        'LinkedIn_Poster_Gold.py',
        'ceo_briefing_generator.py',
        'authenticate_gmail.py',
        'quick_start_gold.py',
        'utils.py'
    ]
    
    existing = []
    missing = []
    
    for file in gold_files:
        if Path(file).exists():
            existing.append(file)
        else:
            missing.append(file)
    
    if existing:
        print_info(f"Found {len(existing)} existing Gold Tier files:")
        for f in existing:
            print(f"    - {f}")
    
    if missing:
        print_info(f"Missing {len(missing)} files (create separately):")
        for f in missing:
            print(f"    - {f}")
    
    # Check Agents folder
    agent_files = ['FTE_Orchestrator_Gold.py']
    for file in agent_files:
        path = Path(f'Agents/{file}')
        if path.exists():
            print_success(f"Found: Agents/{file}")
        else:
            print_info(f"Missing: Agents/{file}")
    
    # Check Skills folder
    skills_files = ['skills.py']
    for file in skills_files:
        path = Path(f'Skills/{file}')
        if path.exists():
            print_success(f"Found: Skills/{file}")
        else:
            print_info(f"Missing: Skills/{file}")


def create_run_script():
    """Create run_gold_tier.py launcher"""
    print_header("Creating Run Script")
    
    run_content = '''"""
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
    
    print("\\n✅ All components started!")
    print("Press Ctrl+C to stop all\\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\\nStopping all components...")
        for p in processes:
            p.terminate()
        print("All components stopped.")


if __name__ == "__main__":
    main()
'''
    
    with open('run_gold_tier.py', 'w', encoding='utf-8') as f:
        f.write(run_content)
    print_success("Created: run_gold_tier.py")


def create_verification_checklist():
    """Create verification checklist"""
    print_header("Creating Verification Checklist")
    
    checklist = """# Gold Tier System Verification Checklist

## Folder Structure
- [ ] Inbox/
- [ ] Needs_Action/
- [ ] WhatsApp_Inbox/
- [ ] Gmail_Inbox/
- [ ] LinkedIn_Posts/
- [ ] Plans/
- [ ] Done/
- [ ] Logs/
- [ ] Pending_Approval/
- [ ] Approved/
- [ ] Accounting/
- [ ] Skills/
- [ ] Agents/

## System Components
- [ ] MCP Server running on port 5001
- [ ] Orchestrator processing tasks
- [ ] Scheduler running automations
- [ ] Gmail Watcher active
- [ ] WhatsApp Watcher active
- [ ] LinkedIn Poster active

## Task Workflow
- [ ] Tasks created in Needs_Action/
- [ ] Plan.md files generated in Plans/
- [ ] Sensitive tasks moved to Pending_Approval/
- [ ] Approved tasks executed
- [ ] Completed tasks in Done/
- [ ] Failed tasks in Error/

## API Endpoints
- [ ] GET /health returns healthy status
- [ ] POST /api/email/send works
- [ ] POST /api/social/post works
- [ ] POST /api/whatsapp/send works
- [ ] POST /api/odoo/action works

## Testing
- [ ] Email send test successful
- [ ] LinkedIn post test successful
- [ ] WhatsApp message test successful
- [ ] Odoo invoice test successful

## Logging
- [ ] Logs created in Logs/
- [ ] Error logs in Logs/Error/
- [ ] MCP action logs present
- [ ] Orchestrator logs present

## Automation
- [ ] Gmail scan every 10 min
- [ ] WhatsApp scan every 15 min
- [ ] LinkedIn post daily at 09:00
- [ ] CEO briefing weekly

## Documentation
- [ ] README.md present
- [ ] .env configured
- [ ] Task templates created
"""
    
    with open('VERIFICATION_CHECKLIST.md', 'w', encoding='utf-8') as f:
        f.write(checklist)
    print_success("Created: VERIFICATION_CHECKLIST.md")


def create_gold_tier_guide():
    """Create comprehensive Gold Tier guide"""
    print_header("Creating Gold Tier Guide")
    
    guide_content = """# Gold Tier AI Employee System - Complete Guide

## System Overview

The Gold Tier AI Employee is an autonomous system that:
- Monitors Gmail, WhatsApp, and LinkedIn
- Creates tasks automatically
- Generates detailed plans using Claude reasoning
- Requires human approval for sensitive tasks
- Executes actions via MCP Server
- Integrates with Odoo for accounting
- Generates weekly CEO briefings

## Architecture

```
Watchers → Needs_Action → Orchestrator → Plans
                                    ↓
                            Approval Check
                                    ↓
                    ┌───────────────┴───────────────┐
                    │                               │
              Pending_Approval                  MCP Server
                    │                               │
              [Human Approval]              Gmail/LinkedIn/
                    │                       WhatsApp/Odoo
                    └───────────────┬───────────────┘
                                    ↓
                                Done/
```

## Setup Steps

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Edit `.env` with your API credentials.

### 3. Authenticate Gmail
```bash
python authenticate_gmail.py
```

### 4. Start System
```bash
python run_gold_tier.py
```

## Testing

### Test Email
```bash
curl -X POST http://localhost:5001/api/email/send \\
  -H "Content-Type: application/json" \\
  -d '{"to":"test@example.com","subject":"Test","body":"Hello"}'
```

### Test LinkedIn Post
```bash
curl -X POST http://localhost:5001/api/social/post \\
  -H "Content-Type: application/json" \\
  -d '{"platform":"linkedin","content":"Test post! #AI"}'
```

### Test Odoo Invoice
```bash
curl -X POST http://localhost:5001/api/odoo/action \\
  -H "Content-Type: application/json" \\
  -d '{"action_type":"create_invoice","data":{"client":"Test","amount":100}}'
```

## Troubleshooting

- Check Logs/ for errors
- Verify .env credentials
- Ensure MCP Server is running
- Check port 5001 is available
"""
    
    with open('GOLD_TIER_GUIDE.md', 'w', encoding='utf-8') as f:
        f.write(guide_content)
    print_success("Created: GOLD_TIER_GUIDE.md")


def print_summary():
    """Print setup summary"""
    print_header("Setup Complete!")
    
    print("""
  Gold Tier AI Employee System has been set up!
  
  Next Steps:
  
  1. Edit .env with your API credentials
  2. Install dependencies:
     pip install -r requirements.txt
  3. Authenticate Gmail:
     python authenticate_gmail.py
  4. Start the system:
     python run_gold_tier.py
  
  Documentation:
  - README.md
  - GOLD_TIER_GUIDE.md
  - VERIFICATION_CHECKLIST.md
  
  Task Templates Created:
  - Needs_Action/send_email_task.json
  - WhatsApp_Inbox/whatsapp_task.json
  - LinkedIn_Posts/linkedin_task.json
  - Needs_Action/odoo_invoice_task.json
    """)


def main():
    """Main setup function"""
    print_banner()

    create_folders()
    create_environment_file()
    create_requirements_file()
    create_task_templates()
    create_readme()
    create_system_files()
    create_run_script()
    create_verification_checklist()
    create_gold_tier_guide()
    print_summary()


if __name__ == "__main__":
    main()
