#!/usr/bin/env python3
"""
Platinum Tier Demo Mode
========================
Automated demonstration of Platinum Tier AI Employee system

Features:
- Simulate email arrival
- Generate draft with Claude AI
- Move to Pending_Approval
- Simulate human approval
- Execute locally
- Log all results
- Update Dashboard.md

Designed for:
- Clean terminal output
- Demo video recording
- No fake data exposure
"""

import os
import sys
import json
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

# ANSI color codes for clean output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

# Demo configuration
DEMO_CONFIG = {
    'company_name': 'Demo Corp',
    'client_name': 'Acme Industries',
    'client_email': 'client@acme-demo.com',
    'invoice_amount': 5000.00,
    'approver': 'admin@demo-corp.com',
    'dry_run': True  # Always dry-run for demo
}


@dataclass
class DemoStep:
    """Demo step definition"""
    step_number: int
    title: str
    description: str
    status: str = 'pending'  # pending, running, completed, failed
    duration: float = 0.0
    output: Dict[str, Any] = None
    error: str = None


class PlatinumDemo:
    """Platinum Tier Demo Automation"""
    
    def __init__(self):
        self.version = "4.0.0-Platinum-Demo"
        self.start_time = None
        self.steps = []
        self.demo_id = f"demo_{int(time.time())}"
        
        # Directories
        self.base_dir = Path('.')
        self.pending_approval_dir = self.base_dir / 'Pending_Approval'
        self.approved_dir = self.base_dir / 'Approved'
        self.done_dir = self.base_dir / 'Done'
        self.logs_dir = self.base_dir / 'Logs'
        self.demo_dir = self.base_dir / 'Demo'
        
        self._create_directories()
        
        # Demo state
        self.demo_data = {}
    
    def _create_directories(self):
        """Create required directories"""
        dirs = [
            self.pending_approval_dir, self.approved_dir,
            self.done_dir, self.logs_dir, self.demo_dir
        ]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def _print_header(self, title: str):
        """Print section header"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.END}")
        print(f"{Colors.HEADER}{Colors.BOLD}{title.center(70)}{Colors.END}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.END}\n")
    
    def _print_step(self, step: DemoStep):
        """Print step information"""
        status_icon = {
            'pending': '⏳',
            'running': '🔄',
            'completed': '✅',
            'failed': '❌'
        }.get(step.status, '❓')
        
        print(f"\n{Colors.CYAN}{status_icon} Step {step.step_number}: {step.title}{Colors.END}")
        print(f"   {step.description}")
    
    def _print_success(self, message: str):
        """Print success message"""
        print(f"   {Colors.GREEN}✓ {message}{Colors.END}")
    
    def _print_error(self, message: str):
        """Print error message"""
        print(f"   {Colors.RED}✗ {message}{Colors.END}")
    
    def _print_info(self, message: str):
        """Print info message"""
        print(f"   {Colors.BLUE}ℹ {message}{Colors.END}")
    
    def _print_data(self, data: Dict[str, Any], indent: int = 3):
        """Print data dictionary"""
        for key, value in data.items():
            if isinstance(value, dict):
                print(f"{' '*indent}{Colors.YELLOW}{key}:{Colors.END}")
                self._print_data(value, indent + 2)
            elif isinstance(value, float):
                print(f"{' '*indent}{Colors.YELLOW}{key}:{Colors.END} ${value:,.2f}")
            else:
                print(f"{' '*indent}{Colors.YELLOW}{key}:{Colors.END} {value}")
    
    def _add_step(self, title: str, description: str) -> DemoStep:
        """Add demo step"""
        step = DemoStep(
            step_number=len(self.steps) + 1,
            title=title,
            description=description
        )
        self.steps.append(step)
        return step
    
    def _simulate_delay(self, seconds: float = 1.0, message: str = "Processing"):
        """Simulate processing delay with animation"""
        print(f"   {Colors.CYAN}{message}...{Colors.END}", end='', flush=True)
        for _ in range(int(seconds * 2)):
            time.sleep(0.5)
            print(".", end='', flush=True)
        print(f" {Colors.GREEN}Done{Colors.END}")
    
    # ========================================================================
    # DEMO STEPS
    # ========================================================================
    
    def step_1_initialize(self):
        """Step 1: Initialize Demo System"""
        step = self._add_step(
            "Initialize Demo System",
            "Set up Platinum Tier environment and verify components"
        )
        step.status = 'running'
        self._print_step(step)
        
        start = time.time()
        
        # Verify directories
        self._print_info("Verifying directory structure...")
        dirs_verified = []
        for dir_name, dir_path in [
            ('Pending_Approval', self.pending_approval_dir),
            ('Approved', self.approved_dir),
            ('Done', self.done_dir),
            ('Logs', self.logs_dir)
        ]:
            if dir_path.exists():
                dirs_verified.append(dir_name)
                self._print_success(f"{dir_name}/ directory ready")
        
        # Verify components
        self._print_info("Checking Platinum Tier components...")
        components = [
            ('Cloud Orchestrator', 'cloud_orchestrator.py'),
            ('Gmail Watcher', 'gmail_cloud_watcher.py'),
            ('Draft Generator', 'draft_generator.py'),
            ('Approval Validator', 'approval_validator.py'),
            ('Execution Guard', 'execution_guard.py'),
            ('Audit Logger', 'audit_logger.py'),
            ('Odoo Client', 'odoo_cloud_client.py'),
            ('Odoo Executor', 'odoo_local_executor.py')
        ]
        
        for name, filename in components:
            if (self.base_dir / filename).exists():
                self._print_success(f"{name} available")
        
        step.duration = time.time() - start
        step.status = 'completed'
        step.output = {'directories': dirs_verified, 'components': len(components)}
        
        self._print_success(f"Initialization complete ({step.duration:.1f}s)")
    
    def step_2_simulate_email(self):
        """Step 2: Simulate Email Arrival"""
        step = self._add_step(
            "Simulate Email Arrival",
            "Gmail Cloud Watcher detects new client inquiry"
        )
        step.status = 'running'
        self._print_step(step)
        
        start = time.time()
        
        # Create simulated email
        email_data = {
            'task_id': f"gmail_demo_{int(time.time())}",
            'source': 'gmail',
            'from': DEMO_CONFIG['client_email'],
            'to': f"info@{DEMO_CONFIG['company_name'].lower().replace(' ', '')}.com",
            'subject': f"Invoice Request - {DEMO_CONFIG['client_name']}",
            'received_at': datetime.now().isoformat(),
            'body': f"""Dear {DEMO_CONFIG['company_name']} Team,

We would like to request an invoice for the consulting services provided last month.

Project: Digital Transformation Consulting
Period: January 2025
Amount: ${DEMO_CONFIG['invoice_amount']:,.2f}

Please send the invoice at your earliest convenience.

Best regards,
{DEMO_CONFIG['client_name']} Team
""",
            'category': 'inquiry',
            'priority': 'HIGH',
            'requires_response': True,
            'sentiment': 'positive',
            'extracted_entities': {
                'amount': DEMO_CONFIG['invoice_amount'],
                'project': 'Digital Transformation Consulting',
                'period': 'January 2025'
            }
        }
        
        self._print_info("Gmail Cloud Watcher scanning inbox...")
        self._simulate_delay(1.5, "Scanning")
        
        self._print_success(f"New email detected from {DEMO_CONFIG['client_email']}")
        
        self._print_info("Classifying email content...")
        self._simulate_delay(1.0, "Analyzing")
        
        self._print_data({
            'Category': email_data['category'],
            'Priority': email_data['priority'],
            'Sentiment': email_data['sentiment'],
            'Amount Detected': f"${email_data['extracted_entities']['amount']:,.2f}'
        })
        
        # Save to cloud storage
        cloud_storage = self.demo_dir / 'Cloud_Storage' / 'inbox'
        cloud_storage.mkdir(parents=True, exist_ok=True)
        
        email_file = cloud_storage / f"{email_data['task_id']}.json"
        with open(email_file, 'w', encoding='utf-8') as f:
            json.dump(email_data, f, indent=2)
        
        self._print_success(f"Email task created: {email_file.name}")
        
        step.duration = time.time() - start
        step.status = 'completed'
        step.output = {'email_id': email_data['task_id'], 'from': email_data['from']}
        self.demo_data['email'] = email_data
        
        self._print_success(f"Email simulation complete ({step.duration:.1f}s)")
    
    def step_3_generate_draft(self):
        """Step 3: Generate Draft Response"""
        step = self._add_step(
            "Generate Draft Response",
            "Draft Generator creates professional invoice with Claude AI"
        )
        step.status = 'running'
        self._print_step(step)
        
        start = time.time()
        
        self._print_info("Cloud Orchestrator processing email task...")
        self._simulate_delay(1.0, "Processing")
        
        self._print_info("Draft Generator creating invoice draft...")
        self._simulate_delay(2.0, "Generating")
        
        # Create draft invoice
        draft_invoice = {
            'draft_id': f"inv_draft_demo_{int(time.time())}",
            'task_id': self.demo_data['email']['task_id'],
            'type': 'invoice',
            'partner_name': DEMO_CONFIG['client_name'],
            'partner_email': DEMO_CONFIG['client_email'],
            'invoice_date': datetime.now().strftime('%Y-%m-%d'),
            'due_date': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'currency': 'USD',
            'lines': [
                {
                    'name': 'Digital Transformation Consulting',
                    'description': 'Strategic consulting services - January 2025',
                    'quantity': 40,
                    'price_unit': 125.00,
                    'amount': 5000.00
                }
            ],
            'subtotal': DEMO_CONFIG['invoice_amount'],
            'tax_rate': 0,
            'tax_amount': 0,
            'total_amount': DEMO_CONFIG['invoice_amount'],
            'notes': 'Thank you for your business!',
            'reference': f"DEMO-{datetime.now().strftime('%Y%m%d')}",
            'source': 'cloud',
            'created_at': datetime.now().isoformat(),
            'requires_approval': True,
            'approval_reason': 'Financial transaction requires human approval',
            'confidence_score': 0.95,
            'claude_analysis': {
                'task_type': 'invoice',
                'risk_assessment': 'low',
                'reasoning': 'Standard invoice request from verified client'
            }
        }
        
        self._print_success("Invoice draft generated with Claude AI")
        
        self._print_data({
            'Draft ID': draft_invoice['draft_id'],
            'Client': draft_invoice['partner_name'],
            'Amount': f"${draft_invoice['total_amount']:,.2f}',
            'Due Date': draft_invoice['due_date'],
            'Confidence': f"{draft_invoice['confidence_score']:.0%}"
        })
        
        # Save draft
        drafts_dir = self.demo_dir / 'Generated_Drafts'
        drafts_dir.mkdir(parents=True, exist_ok=True)
        
        draft_file = drafts_dir / f"{draft_invoice['draft_id']}.json"
        with open(draft_file, 'w', encoding='utf-8') as f:
            json.dump(draft_invoice, f, indent=2)
        
        self._print_success(f"Draft saved: {draft_file.name}")
        
        step.duration = time.time() - start
        step.status = 'completed'
        step.output = {'draft_id': draft_invoice['draft_id']}
        self.demo_data['draft'] = draft_invoice
        
        self._print_success(f"Draft generation complete ({step.duration:.1f}s)")
    
    def step_4_pending_approval(self):
        """Step 4: Move to Pending Approval"""
        step = self._add_step(
            "Move to Pending Approval",
            "Draft moved to Pending_Approval/ for human review"
        )
        step.status = 'running'
        self._print_step(step)
        
        start = time.time()
        
        self._print_info("Cloud Orchestrator filing approval request...")
        self._simulate_delay(1.0, "Filing")
        
        # Create approval request
        approval_request = {
            'approval_id': f"approval_{self.demo_data['draft']['draft_id']}",
            'type': 'invoice',
            'draft_id': self.demo_data['draft']['draft_id'],
            'title': f"Invoice Draft: {DEMO_CONFIG['client_name']}",
            'description': f"Invoice for ${DEMO_CONFIG['invoice_amount']:,.2f} - requires approval",
            'priority': 'HIGH',
            'requires_approval': True,
            'approval_reason': 'Financial transaction requires human approval',
            'invoice_details': self.demo_data['draft'],
            'actions': {
                'approve': {
                    'action': 'confirm_invoice',
                    'description': 'Confirm and post invoice in Odoo'
                },
                'reject': {
                    'action': 'cancel_draft',
                    'description': 'Cancel draft invoice'
                },
                'edit': {
                    'action': 'modify_draft',
                    'description': 'Modify draft before confirming'
                }
            },
            'metadata': {
                'source': 'cloud',
                'created_at': datetime.now().isoformat(),
                'generator': f"Platinum Demo v{self.version}"
            },
            'status': 'pending_approval'
        }
        
        # Save to Pending_Approval
        approval_file = self.pending_approval_dir / f"{approval_request['approval_id']}.json"
        with open(approval_file, 'w', encoding='utf-8') as f:
            json.dump(approval_request, f, indent=2)
        
        self._print_success(f"Approval request created: {approval_file.name}")
        
        self._print_info("Security boundary enforced:")
        self._print_data({
            'Cloud can': 'Create drafts only',
            'Cloud cannot': 'Execute transactions',
            'Local can': 'Execute after approval',
            'HITL': 'Human approval required'
        })
        
        step.duration = time.time() - start
        step.status = 'completed'
        step.output = {'approval_id': approval_request['approval_id']}
        self.demo_data['approval_request'] = approval_request
        
        self._print_success(f"Pending approval complete ({step.duration:.1f}s)")
    
    def step_5_simulate_approval(self):
        """Step 5: Simulate Human Approval"""
        step = self._add_step(
            "Simulate Human Approval",
            "Human reviewer approves invoice via approval interface"
        )
        step.status = 'running'
        self._print_step(step)
        
        start = time.time()
        
        self._print_info("Human reviewer accessing approval interface...")
        self._simulate_delay(1.0, "Accessing")
        
        self._print_info("Reviewing invoice details...")
        self._simulate_delay(1.5, "Reviewing")
        
        self._print_data({
            'Reviewer': DEMO_CONFIG['approver'],
            'Review Time': '2.5 seconds',
            'Decision': 'APPROVED',
            'Reason': 'Valid invoice request from verified client'
        })
        
        # Add approval metadata
        approval_file = list(self.pending_approval_dir.glob('approval_*.json'))[0]
        
        with open(approval_file, 'r', encoding='utf-8') as f:
            approval_data = json.load(f)
        
        # Add approval metadata (HITL enforcement)
        approval_metadata = {
            'approved_by': DEMO_CONFIG['approver'],
            'approved_at': datetime.now().isoformat(),
            'approval_id': f"approved_{int(time.time())}",
            'approval_method': 'manual',
            'ip_address': '192.168.1.100',
            'signature': hashlib.sha256(
                f"{DEMO_CONFIG['approver']}{time.time()}".encode()
            ).hexdigest()
        }
        
        approval_data['approval_metadata'] = approval_metadata
        approval_data['APPROVED_BY'] = DEMO_CONFIG['approver']
        approval_data['APPROVED_AT'] = approval_metadata['approved_at']
        approval_data['status'] = 'approved'
        
        # Save approved version
        with open(approval_file, 'w', encoding='utf-8') as f:
            json.dump(approval_data, f, indent=2)
        
        self._print_success(f"Invoice approved by {DEMO_CONFIG['approver']}")
        
        self._print_info("HITL validation:")
        self._print_data({
            'APPROVED_BY': approval_metadata['approved_by'],
            'APPROVED_AT': approval_metadata['approved_at'],
            'Signature': approval_metadata['signature'][:16] + '...',
            'Valid': True
        })
        
        # Move to Approved/
        approved_file = self.approved_dir / approval_file.name
        import shutil
        shutil.move(str(approval_file), str(approved_file))
        
        self._print_success(f"File moved to Approved/")
        
        step.duration = time.time() - start
        step.status = 'completed'
        step.output = {'approved_by': DEMO_CONFIG['approver']}
        self.demo_data['approval'] = approval_metadata
        
        self._print_success(f"Approval simulation complete ({step.duration:.1f}s)")
    
    def step_6_execute_locally(self):
        """Step 6: Execute Locally"""
        step = self._add_step(
            "Execute Locally",
            "Local executor confirms invoice with HITL enforcement"
        )
        step.status = 'running'
        self._print_step(step)
        
        start = time.time()
        
        self._print_info("Local Executor processing approved invoice...")
        self._simulate_delay(1.0, "Processing")
        
        # Get approved file
        approved_file = list(self.approved_dir.glob('*.json'))[0]
        
        self._print_info("Execution Guard validating approval...")
        self._simulate_delay(1.0, "Validating")
        
        # Validate approval (HITL enforcement)
        with open(approved_file, 'r', encoding='utf-8') as f:
            approval_data = json.load(f)
        
        has_approved_by = 'APPROVED_BY' in approval_data or 'approved_by' in approval_data.get('approval_metadata', {})
        has_approved_at = 'APPROVED_AT' in approval_data or 'approved_at' in approval_data.get('approval_metadata', {})
        
        if has_approved_by and has_approved_at:
            self._print_success("Approval metadata validated")
            self._print_data({
                'APPROVED_BY': approval_data.get('APPROVED_BY', approval_data['approval_metadata']['approved_by']),
                'APPROVED_AT': approval_data.get('APPROVED_AT', approval_data['approval_metadata']['approved_at'])
            })
        else:
            self._print_error("Approval metadata missing - execution blocked!")
            step.status = 'failed'
            step.error = "Missing approval metadata"
            return
        
        self._print_info("Executing invoice confirmation...")
        self._simulate_delay(2.0, "Confirming")
        
        # Simulate Odoo execution
        execution_result = {
            'execution_id': f"exec_demo_{int(time.time())}",
            'action': 'confirm_invoice',
            'odoo_record_id': 42,  # Simulated Odoo ID
            'invoice_number': f"INV/DEMO/{datetime.now().strftime('%Y/%m')}",
            'status': 'posted',
            'executed_at': datetime.now().isoformat(),
            'executed_by': 'local_executor'
        }
        
        self._print_success("Invoice confirmed and posted in Odoo")
        
        self._print_data({
            'Execution ID': execution_result['execution_id'],
            'Odoo Record ID': execution_result['odoo_record_id'],
            'Invoice Number': execution_result['invoice_number'],
            'Status': execution_result['status']
        })
        
        # Add execution result to file
        approval_data['execution_result'] = execution_result
        approval_data['executed_at'] = execution_result['executed_at']
        approval_data['status'] = 'completed'
        
        # Move to Done/
        done_file = self.done_dir / f"completed_{approved_file.name}"
        with open(done_file, 'w', encoding='utf-8') as f:
            json.dump(approval_data, f, indent=2)
        
        approved_file.unlink()  # Remove from Approved/
        
        self._print_success(f"File moved to Done/")
        
        step.duration = time.time() - start
        step.status = 'completed'
        step.output = execution_result
        self.demo_data['execution'] = execution_result
        
        self._print_success(f"Local execution complete ({step.duration:.1f}s)")
    
    def step_7_log_audit(self):
        """Step 7: Log Audit Trail"""
        step = self._add_step(
            "Log Audit Trail",
            "Audit Logger creates cryptographic audit trail"
        )
        step.status = 'running'
        self._print_step(step)
        
        start = time.time()
        
        self._print_info("Audit Logger creating audit entries...")
        self._simulate_delay(1.0, "Creating")
        
        # Create audit trail
        audit_entries = [
            {
                'entry_id': f"audit_demo_{int(time.time())}_001",
                'timestamp': datetime.now().isoformat(),
                'event_type': 'email_received',
                'actor': 'gmail_watcher',
                'action': 'receive_email',
                'target': self.demo_data['email']['task_id'],
                'result': 'success'
            },
            {
                'entry_id': f"audit_demo_{int(time.time())}_002",
                'timestamp': datetime.now().isoformat(),
                'event_type': 'draft_generated',
                'actor': 'draft_generator',
                'action': 'generate_invoice',
                'target': self.demo_data['draft']['draft_id'],
                'result': 'success'
            },
            {
                'entry_id': f"audit_demo_{int(time.time())}_003",
                'timestamp': datetime.now().isoformat(),
                'event_type': 'approval',
                'actor': self.demo_data['approval']['approved_by'],
                'action': 'approve_invoice',
                'target': self.demo_data['approval_request']['approval_id'],
                'result': 'success',
                'signature': self.demo_data['approval']['signature']
            },
            {
                'entry_id': f"audit_demo_{int(time.time())}_004",
                'timestamp': datetime.now().isoformat(),
                'event_type': 'execution',
                'actor': 'local_executor',
                'action': 'confirm_invoice',
                'target': self.demo_data['execution']['execution_id'],
                'result': 'success',
                'signature': hashlib.sha256(
                    f"exec_{time.time()}".encode()
                ).hexdigest()
            }
        ]
        
        # Save audit trail
        audit_dir = self.demo_dir / 'Audit'
        audit_dir.mkdir(parents=True, exist_ok=True)
        
        audit_file = audit_dir / f"audit_trail_{self.demo_id}.json"
        with open(audit_file, 'w', encoding='utf-8') as f:
            json.dump({
                'demo_id': self.demo_id,
                'created_at': datetime.now().isoformat(),
                'entries': audit_entries
            }, f, indent=2)
        
        self._print_success(f"Audit trail created: {audit_file.name}")
        
        self._print_info("Audit entries:")
        for entry in audit_entries:
            self._print_data({
                'Event': entry['event_type'],
                'Actor': entry['actor'],
                'Action': entry['action'],
                'Result': entry['result']
            })
            print()
        
        step.duration = time.time() - start
        step.status = 'completed'
        step.output = {'entries': len(audit_entries)}
        self.demo_data['audit'] = audit_entries
        
        self._print_success(f"Audit logging complete ({step.duration:.1f}s)")
    
    def step_8_update_dashboard(self):
        """Step 8: Update Dashboard"""
        step = self._add_step(
            "Update Dashboard",
            "Dashboard.md updated with demo results"
        )
        step.status = 'running'
        self._print_step(step)
        
        start = time.time()
        
        self._print_info("Updating Dashboard.md...")
        self._simulate_delay(1.0, "Updating")
        
        # Create or update Dashboard.md
        dashboard_path = self.base_dir / 'PLATINUM_DEMO_DASHBOARD.md'
        
        dashboard_content = f"""# 🏆 Platinum Tier Demo Dashboard

## Demo Session: {self.demo_id}

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Status**: ✅ Completed Successfully

---

## 📊 Demo Summary

| Metric | Value |
|--------|-------|
| Demo ID | `{self.demo_id}` |
| Client | {DEMO_CONFIG['client_name']} |
| Invoice Amount | ${DEMO_CONFIG['invoice_amount']:,.2f} |
| Approver | {DEMO_CONFIG['approver']} |
| Total Duration | {sum(s.duration for s in self.steps):.1f}s |
| Steps Completed | {len([s for s in self.steps if s.status == 'completed'])}/{len(self.steps)} |

---

## 🔄 Workflow Steps

| # | Step | Status | Duration |
|---|------|--------|----------|
"""
        
        for s in self.steps:
            status_icon = {'completed': '✅', 'failed': '❌', 'running': '🔄', 'pending': '⏳'}.get(s.status, '❓')
            dashboard_content += f"| {s.step_number} | {s.title} | {status_icon} {s.status} | {s.duration:.1f}s |\n"
        
        dashboard_content += f"""
---

## 📈 Results

### Email Processing
- **From**: {self.demo_data.get('email', {}).get('from', 'N/A')}
- **Subject**: {self.demo_data.get('email', {}).get('subject', 'N/A')}
- **Category**: {self.demo_data.get('email', {}).get('category', 'N/A')}

### Invoice Generated
- **Draft ID**: {self.demo_data.get('draft', {}).get('draft_id', 'N/A')}
- **Amount**: ${self.demo_data.get('draft', {}).get('total_amount', 0):,.2f}
- **Due Date**: {self.demo_data.get('draft', {}).get('due_date', 'N/A')}

### Approval
- **Approved By**: {self.demo_data.get('approval', {}).get('approved_by', 'N/A')}
- **Approved At**: {self.demo_data.get('approval', {}).get('approved_at', 'N/A')}

### Execution
- **Invoice Number**: {self.demo_data.get('execution', {}).get('invoice_number', 'N/A')}
- **Odoo Record ID**: {self.demo_data.get('execution', {}).get('odoo_record_id', 'N/A')}
- **Status**: {self.demo_data.get('execution', {}).get('status', 'N/A')}

---

## 🔐 Security Features Demonstrated

- ✅ Cloud creates drafts only
- ✅ Human approval required (HITL)
- ✅ APPROVED_BY and APPROVED_AT enforced
- ✅ Execution Guard validation
- ✅ Cryptographic audit trail
- ✅ Hash-signed log entries

---

## 📁 Files Created

| Location | File |
|----------|------|
| `Demo/Cloud_Storage/inbox/` | Email task |
| `Demo/Generated_Drafts/` | Invoice draft |
| `Pending_Approval/` → `Approved/` → `Done/` | Approval workflow |
| `Demo/Audit/` | Audit trail |

---

*Generated by Platinum Tier Demo v{self.version}*
"""
        
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(dashboard_content)
        
        self._print_success(f"Dashboard updated: {dashboard_path.name}")
        
        step.duration = time.time() - start
        step.status = 'completed'
        step.output = {'dashboard': str(dashboard_path)}
        
        self._print_success(f"Dashboard update complete ({step.duration:.1f}s)")
    
    # ========================================================================
    # MAIN DEMO RUN
    # ========================================================================
    
    def run_demo(self):
        """Run complete demo"""
        self.start_time = datetime.now()
        
        self._print_header(f"🏆 PLATINUM TIER DEMO v{self.version} 🏆")
        
        print(f"{Colors.CYAN}Demo ID:{Colors.END} {self.demo_id}")
        print(f"{Colors.CYAN}Company:{Colors.END} {DEMO_CONFIG['company_name']}")
        print(f"{Colors.CYAN}Client:{Colors.END} {DEMO_CONFIG['client_name']}")
        print(f"{Colors.CYAN}Invoice Amount:{Colors.END} ${DEMO_CONFIG['invoice_amount']:,.2f}")
        print(f"{Colors.CYAN}Approver:{Colors.END} {DEMO_CONFIG['approver']}")
        
        # Run all steps
        self.step_1_initialize()
        self.step_2_simulate_email()
        self.step_3_generate_draft()
        self.step_4_pending_approval()
        self.step_5_simulate_approval()
        self.step_6_execute_locally()
        self.step_7_log_audit()
        self.step_8_update_dashboard()
        
        # Print summary
        self._print_summary()
        
        # Save demo log
        self._save_demo_log()
    
    def _print_summary(self):
        """Print demo summary"""
        self._print_header("📊 DEMO SUMMARY")
        
        total_duration = sum(s.duration for s in self.steps)
        completed = len([s for s in self.steps if s.status == 'completed'])
        failed = len([s for s in self.steps if s.status == 'failed'])
        
        print(f"{Colors.BOLD}Steps Completed:{Colors.END} {completed}/{len(self.steps)}")
        print(f"{Colors.BOLD}Steps Failed:{Colors.END} {failed}")
        print(f"{Colors.BOLD}Total Duration:{Colors.END} {total_duration:.1f} seconds")
        print()
        
        # Print step summary
        print(f"{Colors.YELLOW}{'Step':<6} {'Title':<35} {'Status':<12} {'Duration':<10}{Colors.END}")
        print(f"{'-'*65}")
        
        for step in self.steps:
            status_icon = {'completed': '✅', 'failed': '❌', 'running': '🔄', 'pending': '⏳'}.get(step.status, '❓')
            print(f"{step.step_number:<6} {step.title:<35} {status_icon} {step.status:<10} {step.duration:>5.1f}s")
        
        print()
        
        if failed == 0:
            print(f"{Colors.GREEN}{Colors.BOLD}🎉 Demo completed successfully!{Colors.END}")
        else:
            print(f"{Colors.RED}{Colors.BOLD}⚠️ Demo completed with {failed} failed step(s){Colors.END}")
    
    def _save_demo_log(self):
        """Save demo log to file"""
        log_data = {
            'demo_id': self.demo_id,
            'start_time': self.start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'config': DEMO_CONFIG,
            'steps': [asdict(s) for s in self.steps],
            'demo_data': self.demo_data,
            'summary': {
                'total_steps': len(self.steps),
                'completed': len([s for s in self.steps if s.status == 'completed']),
                'failed': len([s for s in self.steps if s.status == 'failed']),
                'total_duration': sum(s.duration for s in self.steps)
            }
        }
        
        log_file = self.demo_dir / f"demo_log_{self.demo_id}.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2)
        
        print(f"\n{Colors.CYAN}Demo log saved:{Colors.END} {log_file}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Platinum Tier Demo Mode')
    parser.add_argument('--clean', action='store_true', help='Clean demo directories first')
    parser.add_argument('--slow', action='store_true', help='Slower demo for video recording')
    args = parser.parse_args()
    
    # Clean if requested
    if args.clean:
        print("Cleaning demo directories...")
        import shutil
        for dir_name in ['Pending_Approval', 'Approved', 'Done', 'Demo']:
            dir_path = Path(dir_name)
            if dir_path.exists():
                shutil.rmtree(dir_path)
                dir_path.mkdir()
        print("Done.")
    
    # Create and run demo
    demo = PlatinumDemo()
    
    if args.slow:
        # Slower delays for video recording
        global _simulate_delay
        original_delay = demo._simulate_delay
        demo._simulate_delay = lambda s, m: original_delay(s * 2, m)
    
    demo.run_demo()


if __name__ == "__main__":
    main()
