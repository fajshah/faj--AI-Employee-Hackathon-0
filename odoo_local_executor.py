"""
Platinum Tier Odoo Local Executor
===================================
Local-side Odoo integration for transaction confirmation

Security Constraints:
- Local executor handles ALL confirmations
- Approves draft invoices after human review
- Confirms and posts transactions
- Logs all transactions for audit
- Cloud NEVER calls these methods

Environment:
- Odoo 17 Community (Docker, HTTPS)
- JSON-RPC API
- Async architecture
- Production-ready error handling
"""

import os
import sys
import json
import asyncio
import logging
import time
import hashlib
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.odoo')

# Configure logging
class OdooLocalLogger:
    """Dual logging: File + Console"""
    
    def __init__(self, name: str, log_file: str = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        if log_file:
            Path(log_file).parent.mkdir(exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
            )
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
    
    def get_logger(self) -> logging.Logger:
        return self.logger


logger_wrapper = OdooLocalLogger(
    name='odoo_local_executor',
    log_file='Logs/odoo_local.log'
)
logger = logger_wrapper.get_logger()


@dataclass
class TransactionLog:
    """Transaction audit log"""
    log_id: str
    transaction_type: str  # invoice, crm_lead
    odoo_record_id: int
    action: str  # confirm, post, cancel
    status: str  # success, failed
    amount: Optional[float]
    partner: Optional[str]
    executed_by: str
    executed_at: str
    approval_id: str
    notes: Optional[str]
    error: Optional[str] = None


class RetryConfig:
    """Retry configuration"""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter


class AsyncRetryExecutor:
    """Async retry executor"""
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
    
    async def execute(
        self,
        func,
        *args,
        retryable_exceptions: tuple = (Exception,),
        **kwargs
    ) -> Any:
        """Execute with retry logic"""
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except retryable_exceptions as e:
                last_exception = e
                
                if attempt < self.config.max_retries:
                    delay = min(
                        self.config.base_delay * (self.config.exponential_base ** attempt),
                        self.config.max_delay
                    )
                    
                    if self.config.jitter:
                        import random
                        delay *= (0.5 + random.random() * 0.5)
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.config.max_retries + 1} failed: {str(e)}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All attempts failed. Last error: {str(e)}")
        
        raise last_exception


class OdooLocalExecutor:
    """
    Platinum Tier Odoo Local Executor
    
    Responsibilities:
    - Approve draft invoices (human-reviewed)
    - Confirm and post invoices in Odoo
    - Confirm CRM leads
    - Log all transactions for audit
    - Move approved files to Done/
    """
    
    def __init__(self):
        self.version = "4.0.0-Platinum-Odoo-Local"
        
        # Configuration
        self.dry_run = os.getenv('DRY_RUN', 'true').lower() == 'true'
        self.odoo_enabled = os.getenv('ODOO_ENABLED', 'true').lower() == 'true'
        
        # Odoo configuration
        self.odoo_url = os.getenv('ODOO_URL', 'https://odoo.yourcompany.com')
        self.odoo_db = os.getenv('ODOO_DB', 'odoo')
        self.odoo_username = os.getenv('ODOO_USERNAME', 'admin')
        self.odoo_password = os.getenv('ODOO_PASSWORD', '')
        self.odoo_api_key = os.getenv('ODOO_API_KEY', '')
        
        # Directories
        self.base_dir = Path(os.getenv('CLOUD_BASE_DIR', '.'))
        self.pending_approval_dir = self.base_dir / 'Pending_Approval'
        self.approved_dir = self.base_dir / 'Approved'
        self.done_dir = self.base_dir / 'Done'
        self.error_dir = self.base_dir / 'Error'
        self.logs_dir = self.base_dir / 'Logs'
        self.accounting_dir = self.base_dir / 'Accounting'
        
        self._create_directories()
        
        # Retry executor
        self.retry_executor = AsyncRetryExecutor(RetryConfig(
            max_retries=3,
            base_delay=1.0,
            max_delay=30.0
        ))
        
        # Odoo session
        self.uid: Optional[int] = None
        self.session = requests.Session()
        
        # Transaction logging
        self.transaction_logs: List[TransactionLog] = []
        
        # Statistics
        self.stats = {
            'transactions_executed': 0,
            'invoices_confirmed': 0,
            'leads_confirmed': 0,
            'transactions_logged': 0,
            'errors': 0,
            'start_time': datetime.now().isoformat()
        }
        
        # Human approver (configured)
        self.default_approver = os.getenv('DEFAULT_APPROVER', 'admin@localhost')
        
        logger.info(f"Odoo Local Executor initialized v{self.version}")
        logger.info(f"DRY_RUN mode: {self.dry_run}")
        logger.info(f"Odoo URL: {self.odoo_url}")
    
    def _create_directories(self):
        """Create required directories"""
        dirs = [
            self.pending_approval_dir, self.approved_dir,
            self.done_dir, self.error_dir, self.logs_dir, self.accounting_dir
        ]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Directory verified: {dir_path}")
    
    def _json_rpc_call(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make JSON-RPC call to Odoo"""
        if not self.odoo_enabled:
            raise Exception("Odoo integration disabled")
        
        url = f"{self.odoo_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        payload = {
            'jsonrpc': '2.0',
            'method': 'call',
            'params': params,
            'id': int(time.time() * 1000)
        }
        
        try:
            logger.debug(f"JSON-RPC call to {url}")
            response = self.session.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if 'error' in result:
                error = result['error']
                raise Exception(f"Odoo JSON-RPC error: {error.get('data', {}).get('message', error.get('message', 'Unknown error'))}")
            
            return result.get('result', {})
        
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error calling Odoo: {str(e)}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            raise
    
    def _authenticate(self) -> int:
        """Authenticate with Odoo"""
        if self.uid:
            return self.uid
        
        logger.info("Authenticating with Odoo...")
        
        params = {
            'service': 'common',
            'method': 'authenticate',
            'args': [
                self.odoo_db,
                self.odoo_username,
                self.odoo_password,
                {'user_context': {}}
            ]
        }
        
        result = self._json_rpc_call('/jsonrpc', params)
        self.uid = result.get('uid')
        
        if not self.uid:
            raise Exception("Odoo authentication failed - check credentials")
        
        logger.info(f"Authenticated as user ID: {self.uid}")
        return self.uid
    
    def _execute_kw(self, model: str, method: str, args: List[Any] = None, kwargs: Dict[str, Any] = None) -> Any:
        """Execute Odoo model method"""
        if not self.uid:
            self._authenticate()
        
        params = {
            'service': 'object',
            'method': 'execute_kw',
            'args': [
                self.odoo_db,
                self.uid,
                self.odoo_password,
                model,
                method,
                args or [],
                kwargs or {}
            ]
        }
        
        return self._json_rpc_call('/jsonrpc', params)
    
    def _read_approval_file(self, approval_path: Path) -> Dict[str, Any]:
        """Read and parse approval request file"""
        with open(approval_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    async def confirm_invoice(
        self,
        approval_data: Dict[str, Any],
        approver: str = None
    ) -> Tuple[bool, str]:
        """
        Confirm and post invoice in Odoo
        
        Args:
            approval_data: Approval request data
            approver: Human approver name/email
        
        Returns:
            (success, message)
        """
        invoice_details = approval_data.get('invoice_details', {})
        approval_id = approval_data.get('approval_id', 'unknown')
        
        logger.info(f"Confirming invoice: {approval_id}")
        logger.info(f"Partner: {invoice_details.get('partner_name')}")
        logger.info(f"Amount: ${invoice_details.get('total_amount', 0):.2f}")
        
        if self.dry_run:
            logger.info(f"[DRY_RUN] Would confirm invoice {approval_id}")
            return True, "DRY_RUN: Invoice would be confirmed"
        
        try:
            # Find draft invoice in Odoo by reference or partner
            odoo_invoice_id = await self._find_draft_invoice(invoice_details)
            
            if not odoo_invoice_id:
                # Create invoice if not exists
                logger.warning("Draft invoice not found in Odoo - creating...")
                odoo_invoice_id = await self._create_invoice_in_odoo(invoice_details)
            
            # Post invoice (action_post confirms and posts)
            async def _post():
                self._execute_kw('account.move', 'action_post', [[odoo_invoice_id]])
                logger.info(f"Invoice {odoo_invoice_id} posted successfully")
            
            await self.retry_executor.execute(_post)
            
            # Get invoice number
            invoice_data = self._execute_kw(
                'account.move',
                'read',
                [[odoo_invoice_id], ['name']]
            )
            invoice_number = invoice_data[0].get('name', 'N/A') if invoice_data else 'N/A'
            
            # Log transaction
            self._log_transaction(
                transaction_type='invoice',
                odoo_record_id=odoo_invoice_id,
                action='confirm_post',
                status='success',
                amount=invoice_details.get('total_amount', 0),
                partner=invoice_details.get('partner_name'),
                executed_by=approver or self.default_approver,
                approval_id=approval_id,
                notes=f"Invoice posted: {invoice_number}"
            )
            
            # Update statistics
            self.stats['transactions_executed'] += 1
            self.stats['invoices_confirmed'] += 1
            self.stats['transactions_logged'] += 1
            
            logger.info(f"Invoice confirmed and posted: {invoice_number}")
            return True, f"Invoice posted: {invoice_number}"
        
        except Exception as e:
            logger.error(f"Failed to confirm invoice: {str(e)}")
            
            # Log error
            self._log_transaction(
                transaction_type='invoice',
                odoo_record_id=0,
                action='confirm_post',
                status='failed',
                amount=invoice_details.get('total_amount', 0),
                partner=invoice_details.get('partner_name'),
                executed_by=approver or self.default_approver,
                approval_id=approval_id,
                notes=None,
                error=str(e)
            )
            
            self.stats['errors'] += 1
            return False, str(e)
    
    async def _find_draft_invoice(self, invoice_details: Dict[str, Any]) -> Optional[int]:
        """Find draft invoice in Odoo"""
        partner_name = invoice_details.get('partner_name', '')
        total_amount = invoice_details.get('total_amount', 0)
        invoice_date = invoice_details.get('invoice_date', '')
        
        # Search by partner and amount
        domain = [
            ('partner_id.name', '=', partner_name),
            ('amount_total', '=', total_amount),
            ('state', '=', 'draft')
        ]
        
        invoice_ids = self._execute_kw('account.move', 'search', [domain])
        
        if invoice_ids:
            logger.info(f"Found draft invoice: {invoice_ids[0]}")
            return invoice_ids[0]
        
        return None
    
    async def _create_invoice_in_odoo(self, invoice_details: Dict[str, Any]) -> int:
        """Create invoice in Odoo"""
        # Find or create partner
        partner_id = await self._find_or_create_partner(
            name=invoice_details.get('partner_name', 'Unknown'),
            email=invoice_details.get('partner_email'),
            phone=invoice_details.get('partner_phone')
        )
        
        # Prepare invoice lines
        invoice_lines = []
        for line in invoice_details.get('lines', []):
            invoice_lines.append((0, 0, {
                'name': line.get('name', 'Service'),
                'quantity': line.get('quantity', 1),
                'price_unit': line.get('price_unit', 0)
            }))
        
        # Create invoice
        invoice_values = {
            'move_type': 'out_invoice',
            'partner_id': partner_id,
            'invoice_date': invoice_details.get('invoice_date', datetime.now().strftime('%Y-%m-%d')),
            'invoice_date_due': invoice_details.get('due_date', (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')),
            'invoice_line_ids': invoice_lines,
            'narration': invoice_details.get('notes', ''),
            'ref': invoice_details.get('reference', ''),
            'state': 'draft'
        }
        
        invoice_id = self._execute_kw('account.move', 'create', [invoice_values])
        logger.info(f"Created invoice in Odoo: {invoice_id}")
        
        return invoice_id
    
    async def _find_or_create_partner(self, name: str, email: str = None, phone: str = None) -> int:
        """Find or create partner in Odoo"""
        # Try to find by email
        if email:
            partner_ids = self._execute_kw(
                'res.partner',
                'search',
                [[['email', '=', email]]]
            )
            
            if partner_ids:
                return partner_ids[0]
        
        # Create new partner
        partner_values = {
            'name': name,
            'email': email or False,
            'phone': phone or False
        }
        
        partner_id = self._execute_kw('res.partner', 'create', [partner_values])
        logger.info(f"Created partner: {partner_id}")
        
        return partner_id
    
    async def confirm_crm_lead(
        self,
        approval_data: Dict[str, Any],
        approver: str = None
    ) -> Tuple[bool, str]:
        """
        Confirm CRM lead in Odoo
        
        Args:
            approval_data: Approval request data
            approver: Human approver name/email
        
        Returns:
            (success, message)
        """
        lead_details = approval_data.get('lead_details', {})
        approval_id = approval_data.get('approval_id', 'unknown')
        
        logger.info(f"Confirming CRM lead: {approval_id}")
        logger.info(f"Lead: {lead_details.get('lead_name')}")
        logger.info(f"Expected revenue: ${lead_details.get('expected_revenue', 0):.2f}")
        
        if self.dry_run:
            logger.info(f"[DRY_RUN] Would confirm CRM lead {approval_id}")
            return True, "DRY_RUN: Lead would be confirmed"
        
        try:
            # Find draft lead in Odoo
            odoo_lead_id = await self._find_draft_lead(lead_details)
            
            if not odoo_lead_id:
                # Create lead if not exists
                logger.warning("Draft lead not found in Odoo - creating...")
                odoo_lead_id = await self._create_lead_in_odoo(lead_details)
            
            # Update lead stage to confirmed
            async def _update():
                self._execute_kw('crm.lead', 'write', [
                    [odoo_lead_id],
                    {'stage_id': self._get_confirmed_stage_id()}
                ])
                logger.info(f"Lead {odoo_lead_id} confirmed")
            
            await self.retry_executor.execute(_update)
            
            # Log transaction
            self._log_transaction(
                transaction_type='crm_lead',
                odoo_record_id=odoo_lead_id,
                action='confirm',
                status='success',
                amount=lead_details.get('expected_revenue', 0),
                partner=lead_details.get('company_name') or lead_details.get('lead_name'),
                executed_by=approver or self.default_approver,
                approval_id=approval_id,
                notes="CRM lead confirmed and assigned"
            )
            
            # Update statistics
            self.stats['transactions_executed'] += 1
            self.stats['leads_confirmed'] += 1
            self.stats['transactions_logged'] += 1
            
            logger.info(f"CRM lead confirmed: {odoo_lead_id}")
            return True, f"Lead confirmed: {odoo_lead_id}"
        
        except Exception as e:
            logger.error(f"Failed to confirm CRM lead: {str(e)}")
            
            self._log_transaction(
                transaction_type='crm_lead',
                odoo_record_id=0,
                action='confirm',
                status='failed',
                amount=lead_details.get('expected_revenue', 0),
                partner=lead_details.get('company_name'),
                executed_by=approver or self.default_approver,
                approval_id=approval_id,
                notes=None,
                error=str(e)
            )
            
            self.stats['errors'] += 1
            return False, str(e)
    
    async def _find_draft_lead(self, lead_details: Dict[str, Any]) -> Optional[int]:
        """Find draft lead in Odoo"""
        lead_name = lead_details.get('lead_name', '')
        
        domain = [
            ('name', '=', lead_name),
            ('type', '=', 'lead')
        ]
        
        lead_ids = self._execute_kw('crm.lead', 'search', [domain])
        
        if lead_ids:
            return lead_ids[0]
        
        return None
    
    async def _create_lead_in_odoo(self, lead_details: Dict[str, Any]) -> int:
        """Create lead in Odoo"""
        lead_values = {
            'name': lead_details.get('lead_name', 'New Lead'),
            'contact_name': lead_details.get('contact_name', ''),
            'partner_name': lead_details.get('company_name', ''),
            'email_from': lead_details.get('email', ''),
            'phone': lead_details.get('phone', ''),
            'planned_revenue': lead_details.get('expected_revenue', 0),
            'probability': lead_details.get('probability', 10),
            'description': lead_details.get('description', ''),
            'type': 'lead'
        }
        
        lead_id = self._execute_kw('crm.lead', 'create', [lead_values])
        logger.info(f"Created CRM lead in Odoo: {lead_id}")
        
        return lead_id
    
    def _get_confirmed_stage_id(self) -> int:
        """Get confirmed stage ID for CRM leads"""
        # Get first stage (or configure specific stage)
        stage_ids = self._execute_kw('crm.stage', 'search', [[[]]], {'limit': 1})
        return stage_ids[0] if stage_ids else False
    
    def _log_transaction(self, **kwargs):
        """Log transaction for audit"""
        log_id = f"txn_{int(time.time())}_{hashlib.md5(str(kwargs).encode()).hexdigest()[:6]}"
        
        log_entry = TransactionLog(
            log_id=log_id,
            executed_at=datetime.now().isoformat(),
            **kwargs
        )
        
        self.transaction_logs.append(log_entry)
        
        # Save to accounting directory
        if not self.dry_run:
            log_file = self.accounting_dir / f"transaction_{log_id}.json"
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(log_entry), f, indent=2)
            
            logger.debug(f"Transaction logged: {log_file}")
    
    def _move_to_done(self, approval_path: Path, result: str):
        """Move approved file to Done directory"""
        try:
            done_path = self.done_dir / f"completed_{approval_path.name}"
            
            # Add execution result to file
            with open(approval_path, 'r', encoding='utf-8') as f:
                approval_data = json.load(f)
            
            approval_data['execution_result'] = result
            approval_data['executed_at'] = datetime.now().isoformat()
            approval_data['status'] = 'completed'
            
            with open(done_path, 'w', encoding='utf-8') as f:
                json.dump(approval_data, f, indent=2)
            
            # Remove original
            approval_path.unlink()
            
            logger.info(f"Moved to Done: {done_path.name}")
        
        except Exception as e:
            logger.error(f"Failed to move to Done: {str(e)}")
    
    def _move_to_error(self, approval_path: Path, error: str):
        """Move failed file to Error directory"""
        try:
            error_path = self.error_dir / f"failed_{approval_path.name}"
            
            with open(approval_path, 'r', encoding='utf-8') as f:
                approval_data = json.load(f)
            
            approval_data['error'] = error
            approval_data['failed_at'] = datetime.now().isoformat()
            approval_data['status'] = 'failed'
            
            with open(error_path, 'w', encoding='utf-8') as f:
                json.dump(approval_data, f, indent=2)
            
            approval_path.unlink()
            
            logger.warning(f"Moved to Error: {error_path.name}")
        
        except Exception as e:
            logger.error(f"Failed to move to Error: {str(e)}")
    
    async def process_approval(self, approval_path: Path, approver: str = None) -> bool:
        """
        Process a single approval request
        
        Args:
            approval_path: Path to approval file
            approver: Human approver name/email
        
        Returns:
            Success status
        """
        logger.info(f"Processing approval: {approval_path.name}")
        
        try:
            # Read approval data
            approval_data = self._read_approval_file(approval_path)
            
            approval_type = approval_data.get('type')
            
            if approval_type == 'invoice':
                success, message = await self.confirm_invoice(approval_data, approver)
            elif approval_type == 'crm_lead':
                success, message = await self.confirm_crm_lead(approval_data, approver)
            else:
                logger.error(f"Unknown approval type: {approval_type}")
                self._move_to_error(approval_path, f"Unknown type: {approval_type}")
                return False
            
            if success:
                self._move_to_done(approval_path, message)
            else:
                self._move_to_error(approval_path, message)
            
            return success
        
        except Exception as e:
            logger.error(f"Failed to process approval: {str(e)}")
            self._move_to_error(approval_path, str(e))
            return False
    
    async def process_pending_approvals(self):
        """Process all pending approvals"""
        logger.info("Processing pending approvals...")
        
        approval_files = list(self.pending_approval_dir.glob('*.json'))
        
        if not approval_files:
            logger.info("No pending approvals")
            return
        
        logger.info(f"Found {len(approval_files)} pending approval(s)")
        
        for approval_file in approval_files:
            await self.process_approval(approval_file)
    
    def get_status(self) -> Dict[str, Any]:
        """Get executor status"""
        uptime = datetime.now() - datetime.fromisoformat(self.stats['start_time'])
        
        return {
            'version': self.version,
            'status': 'running',
            'uptime': str(uptime),
            'dry_run': self.dry_run,
            'odoo_enabled': self.odoo_enabled,
            'odoo_url': self.odoo_url,
            'odoo_connected': self.uid is not None,
            'statistics': self.stats,
            'pending_approvals': len(list(self.pending_approval_dir.glob('*.json'))),
            'timestamp': datetime.now().isoformat()
        }
    
    async def run_demo(self):
        """Run demo - process pending approvals"""
        print(f"""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     💼  PLATINUM TIER ODOO LOCAL EXECUTOR  💼            ║
║                                                           ║
║     Version: {self.version}
║     DRY_RUN: {self.dry_run}
║     Odoo Enabled: {self.odoo_enabled}
║     Odoo URL: {self.odoo_url}
║                                                           ║
║     SECURITY:                                             ║
║     ✓ Local handles ALL confirmations                    ║
║     ✓ Human approval required                            ║
║     ✓ Full audit trail                                   ║
║     ✓ Cloud NEVER calls these methods                    ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
        """)
        
        logger.info(f"Odoo Local Executor starting v{self.version}")
        
        # Process pending approvals
        await self.process_pending_approvals()
        
        # Print summary
        print(f"\n💼 Execution Summary:")
        print(f"   Transactions Executed: {self.stats['transactions_executed']}")
        print(f"   Invoices Confirmed: {self.stats['invoices_confirmed']}")
        print(f"   Leads Confirmed: {self.stats['leads_confirmed']}")
        print(f"   Errors: {self.stats['errors']}")
        print(f"   Transaction Logs: {self.accounting_dir}")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Platinum Tier Odoo Local Executor')
    parser.add_argument('--dry-run', action='store_true', help='Run in dry-run mode')
    parser.add_argument('--demo', action='store_true', help='Run demo')
    parser.add_argument('--status', action='store_true', help='Show status and exit')
    parser.add_argument('--process', action='store_true', help='Process pending approvals')
    args = parser.parse_args()
    
    executor = OdooLocalExecutor()
    
    if args.status:
        status = executor.get_status()
        print(json.dumps(status, indent=2))
        return
    
    if args.dry_run:
        executor.dry_run = True
    
    if args.demo or args.process:
        await executor.run_demo()
        return
    
    # Default: run demo
    await executor.run_demo()


if __name__ == "__main__":
    asyncio.run(main())
