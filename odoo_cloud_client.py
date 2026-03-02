"""
Platinum Tier Odoo Cloud Client
================================
Cloud-side Odoo integration for draft creation only

Security Constraints:
- Cloud creates DRAFTS only (invoices, CRM leads)
- Cloud NEVER confirms or posts transactions
- Cloud writes approval requests to Pending_Approval
- Local executor handles confirmation after approval

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
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.odoo')

# Configure logging
class OdooCloudLogger:
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


logger_wrapper = OdooCloudLogger(
    name='odoo_cloud_client',
    log_file='Logs/odoo_cloud.log'
)
logger = logger_wrapper.get_logger()


@dataclass
class DraftInvoice:
    """Draft invoice data structure"""
    draft_id: str
    partner_name: str
    partner_email: Optional[str]
    partner_phone: Optional[str]
    invoice_date: str
    due_date: str
    invoice_lines: List[Dict[str, Any]]
    total_amount: float
    currency: str
    notes: Optional[str]
    reference: Optional[str]
    source: str
    created_at: str
    requires_approval: bool
    approval_reason: str
    status: str = 'draft'


@dataclass
class DraftCRMLead:
    """Draft CRM lead data structure"""
    draft_id: str
    lead_name: str
    company_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    expected_revenue: float
    probability: int
    stage: str
    description: Optional[str]
    tags: List[str]
    source: str
    created_at: str
    requires_approval: bool
    status: str = 'draft'


class RetryConfig:
    """Retry configuration with exponential backoff"""
    
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


class OdooCloudClient:
    """
    Platinum Tier Odoo Cloud Client
    
    Responsibilities:
    - Create draft invoices in Odoo (state='draft')
    - Create draft CRM leads
    - Write approval requests to Pending_Approval
    - NEVER confirm or post transactions
    """
    
    def __init__(self):
        self.version = "4.0.0-Platinum-Odoo-Cloud"
        
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
        self.logs_dir = self.base_dir / 'Logs'
        
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
        
        # Statistics
        self.stats = {
            'drafts_created': 0,
            'invoices': 0,
            'crm_leads': 0,
            'approval_requests': 0,
            'errors': 0,
            'start_time': datetime.now().isoformat()
        }
        
        logger.info(f"Odoo Cloud Client initialized v{self.version}")
        logger.info(f"DRY_RUN mode: {self.dry_run}")
        logger.info(f"Odoo URL: {self.odoo_url}")
    
    def _create_directories(self):
        """Create required directories"""
        dirs = [self.pending_approval_dir, self.logs_dir]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Directory verified: {dir_path}")
    
    def _json_rpc_call(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make JSON-RPC call to Odoo
        
        Args:
            endpoint: Odoo endpoint (e.g., '/jsonrpc')
            params: JSON-RPC params
        
        Returns:
            JSON-RPC response
        """
        if not self.odoo_enabled:
            raise Exception("Odoo integration disabled")
        
        url = f"{self.odoo_url}{endpoint}"
        
        headers = {
            'Content-Type': 'application/json'
        }
        
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
        """
        Authenticate with Odoo
        
        Returns:
            User ID (uid)
        """
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
        """
        Execute Odoo model method
        
        Args:
            model: Odoo model name (e.g., 'account.move')
            method: Method to call (e.g., 'create')
            args: Method arguments
            kwargs: Method keyword arguments
        
        Returns:
            Method result
        """
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
    
    async def _create_draft_invoice_odoo(self, invoice_data: Dict[str, Any]) -> int:
        """
        Create draft invoice in Odoo
        
        Args:
            invoice_data: Invoice data dictionary
        
        Returns:
            Invoice ID
        """
        # Prepare invoice lines
        invoice_lines = []
        for line in invoice_data.get('invoice_lines', []):
            invoice_lines.append((0, 0, {
                'name': line.get('name', 'Service'),
                'quantity': line.get('quantity', 1),
                'price_unit': line.get('price_unit', 0),
                'account_id': line.get('account_id', False),  # Optional: specific account
                'tax_ids': line.get('tax_ids', [])  # Optional: tax IDs
            }))
        
        # Create invoice record
        invoice_values = {
            'move_type': invoice_data.get('move_type', 'out_invoice'),  # out_invoice, in_invoice, etc.
            'partner_id': invoice_data.get('partner_id', False),  # Partner ID or create new
            'invoice_date': invoice_data.get('invoice_date', datetime.now().strftime('%Y-%m-%d')),
            'invoice_date_due': invoice_data.get('due_date', (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')),
            'currency_id': invoice_data.get('currency_id', False),
            'invoice_line_ids': invoice_lines,
            'narration': invoice_data.get('notes', ''),
            'ref': invoice_data.get('reference', ''),
            'state': 'draft'  # CRITICAL: Always create as draft
        }
        
        # If partner not provided, create partner first
        if not invoice_values['partner_id']:
            partner_id = await self._create_or_find_partner(
                name=invoice_data.get('partner_name', 'Unknown'),
                email=invoice_data.get('partner_email'),
                phone=invoice_data.get('partner_phone')
            )
            invoice_values['partner_id'] = partner_id
        
        # Create invoice
        invoice_id = self._execute_kw('account.move', 'create', [invoice_values])
        logger.info(f"Draft invoice created in Odoo: ID={invoice_id}")
        
        return invoice_id
    
    async def _create_or_find_partner(self, name: str, email: str = None, phone: str = None) -> int:
        """
        Create or find partner in Odoo
        
        Args:
            name: Partner name
            email: Partner email
            phone: Partner phone
        
        Returns:
            Partner ID
        """
        # Try to find existing partner by email
        if email:
            partner_ids = self._execute_kw(
                'res.partner',
                'search',
                [[['email', '=', email]]]
            )
            
            if partner_ids:
                logger.info(f"Found existing partner: {partner_ids[0]}")
                return partner_ids[0]
        
        # Create new partner
        partner_values = {
            'name': name,
            'email': email or False,
            'phone': phone or False,
            'company_type': 'person' if '@' in (email or '') else 'company'
        }
        
        partner_id = self._execute_kw('res.partner', 'create', [partner_values])
        logger.info(f"Created new partner: ID={partner_id}")
        
        return partner_id
    
    async def _create_draft_crm_lead_odoo(self, lead_data: Dict[str, Any]) -> int:
        """
        Create draft CRM lead in Odoo
        
        Args:
            lead_data: Lead data dictionary
        
        Returns:
            Lead ID
        """
        lead_values = {
            'name': lead_data.get('lead_name', 'New Lead'),
            'contact_name': lead_data.get('contact_name', ''),
            'partner_name': lead_data.get('company_name', ''),
            'email_from': lead_data.get('email', ''),
            'phone': lead_data.get('phone', ''),
            'planned_revenue': lead_data.get('expected_revenue', 0),
            'probability': lead_data.get('probability', 10),
            'stage_id': lead_data.get('stage_id', False),
            'description': lead_data.get('description', ''),
            'tag_ids': lead_data.get('tag_ids', []),
            'type': 'lead'  # 'lead' or 'opportunity'
        }
        
        lead_id = self._execute_kw('crm.lead', 'create', [lead_values])
        logger.info(f"Draft CRM lead created in Odoo: ID={lead_id}")
        
        return lead_id
    
    async def create_draft_invoice(
        self,
        partner_name: str,
        invoice_lines: List[Dict[str, Any]],
        partner_email: str = None,
        partner_phone: str = None,
        invoice_date: str = None,
        due_date: str = None,
        currency: str = 'USD',
        notes: str = None,
        reference: str = None,
        source: str = 'cloud'
    ) -> DraftInvoice:
        """
        Create draft invoice and approval request
        
        Args:
            partner_name: Customer name
            invoice_lines: List of line items [{name, quantity, price_unit}]
            partner_email: Customer email
            partner_phone: Customer phone
            invoice_date: Invoice date (YYYY-MM-DD)
            due_date: Due date (YYYY-MM-DD)
            currency: Currency code
            notes: Additional notes
            reference: Reference number
            source: Source system
        
        Returns:
            DraftInvoice object
        """
        logger.info(f"Creating draft invoice for {partner_name}")
        
        # Calculate total
        total_amount = sum(
            line.get('quantity', 1) * line.get('price_unit', 0)
            for line in invoice_lines
        )
        
        # Generate draft ID
        draft_id = f"inv_draft_{int(time.time())}_{hashlib.md5(partner_name.encode()).hexdigest()[:6]}"
        
        # Set dates
        now = datetime.now()
        invoice_date = invoice_date or now.strftime('%Y-%m-%d')
        due_date = due_date or (now + timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Create draft invoice object
        draft_invoice = DraftInvoice(
            draft_id=draft_id,
            partner_name=partner_name,
            partner_email=partner_email,
            partner_phone=partner_phone,
            invoice_date=invoice_date,
            due_date=due_date,
            invoice_lines=invoice_lines,
            total_amount=total_amount,
            currency=currency,
            notes=notes,
            reference=reference,
            source=source,
            created_at=now.isoformat(),
            requires_approval=True,
            approval_reason="Financial transaction requires human approval",
            status='draft'
        )
        
        if self.dry_run:
            logger.info(f"[DRY_RUN] Would create draft invoice: {draft_id}")
            logger.info(f"[DRY_RUN] Amount: ${total_amount:.2f}")
            return draft_invoice
        
        if self.odoo_enabled:
            try:
                # Create draft in Odoo
                async def _create():
                    return await self._create_draft_invoice_odoo({
                        'partner_name': partner_name,
                        'partner_email': partner_email,
                        'partner_phone': partner_phone,
                        'invoice_lines': invoice_lines,
                        'invoice_date': invoice_date,
                        'due_date': due_date,
                        'currency_id': False,  # Use default
                        'notes': notes,
                        'reference': reference
                    })
                
                odoo_invoice_id = await self.retry_executor.execute(_create)
                logger.info(f"Draft invoice created in Odoo: {odoo_invoice_id}")
                
            except Exception as e:
                logger.error(f"Failed to create Odoo invoice: {str(e)}")
                # Continue with approval request even if Odoo fails
        
        # Create approval request
        await self._create_approval_request(draft_invoice)
        
        # Update statistics
        self.stats['drafts_created'] += 1
        self.stats['invoices'] += 1
        self.stats['approval_requests'] += 1
        
        return draft_invoice
    
    async def create_draft_crm_lead(
        self,
        lead_name: str,
        expected_revenue: float,
        company_name: str = None,
        email: str = None,
        phone: str = None,
        probability: int = 10,
        description: str = None,
        tags: List[str] = None,
        source: str = 'cloud'
    ) -> DraftCRMLead:
        """
        Create draft CRM lead and approval request
        
        Args:
            lead_name: Lead title
            expected_revenue: Expected revenue amount
            company_name: Company name
            email: Contact email
            phone: Contact phone
            probability: Success probability (0-100)
            description: Lead description
            tags: List of tags
            source: Source system
        
        Returns:
            DraftCRMLead object
        """
        logger.info(f"Creating draft CRM lead: {lead_name}")
        
        # Generate draft ID
        draft_id = f"crm_draft_{int(time.time())}_{hashlib.md5(lead_name.encode()).hexdigest()[:6]}"
        
        # Create draft lead object
        draft_lead = DraftCRMLead(
            draft_id=draft_id,
            lead_name=lead_name,
            company_name=company_name,
            email=email,
            phone=phone,
            expected_revenue=expected_revenue,
            probability=probability,
            stage='new',  # Default to new stage
            description=description,
            tags=tags or [],
            source=source,
            created_at=datetime.now().isoformat(),
            requires_approval=True,
            status='draft'
        )
        
        if self.dry_run:
            logger.info(f"[DRY_RUN] Would create draft CRM lead: {draft_id}")
            return draft_lead
        
        if self.odoo_enabled:
            try:
                async def _create():
                    return await self._create_draft_crm_lead_odoo({
                        'lead_name': lead_name,
                        'company_name': company_name,
                        'email': email,
                        'phone': phone,
                        'expected_revenue': expected_revenue,
                        'probability': probability,
                        'description': description,
                        'tag_ids': []
                    })
                
                odoo_lead_id = await self.retry_executor.execute(_create)
                logger.info(f"Draft CRM lead created in Odoo: {odoo_lead_id}")
                
            except Exception as e:
                logger.error(f"Failed to create Odoo lead: {str(e)}")
        
        # Create approval request
        await self._create_approval_request(draft_lead)
        
        # Update statistics
        self.stats['drafts_created'] += 1
        self.stats['crm_leads'] += 1
        self.stats['approval_requests'] += 1
        
        return draft_lead
    
    async def _create_approval_request(self, draft: Any):
        """
        Create approval request file in Pending_Approval
        
        Args:
            draft: DraftInvoice or DraftCRMLead object
        """
        if isinstance(draft, DraftInvoice):
            approval_data = self._format_invoice_approval(draft)
            filename = f"approval_invoice_{draft.draft_id}.json"
        else:
            approval_data = self._format_crm_approval(draft)
            filename = f"approval_crm_{draft.draft_id}.json"
        
        filepath = self.pending_approval_dir / filename
        
        if self.dry_run:
            logger.info(f"[DRY_RUN] Would create approval request: {filepath}")
            return
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(approval_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Approval request created: {filepath}")
            
            # Also create markdown summary
            await self._create_approval_markdown(draft, filepath)
        
        except Exception as e:
            logger.error(f"Failed to create approval request: {str(e)}")
            self.stats['errors'] += 1
            raise
    
    def _format_invoice_approval(self, draft: DraftInvoice) -> Dict[str, Any]:
        """Format invoice draft as approval request"""
        return {
            'approval_id': f"approval_{draft.draft_id}",
            'type': 'invoice',
            'draft_id': draft.draft_id,
            'title': f"Invoice Draft: {draft.partner_name}",
            'description': f"Invoice for ${draft.total_amount:.2f} due {draft.due_date}",
            'priority': 'HIGH',
            'requires_approval': True,
            'approval_reason': draft.approval_reason,
            'invoice_details': {
                'partner_name': draft.partner_name,
                'partner_email': draft.partner_email,
                'partner_phone': draft.partner_phone,
                'invoice_date': draft.invoice_date,
                'due_date': draft.due_date,
                'currency': draft.currency,
                'lines': draft.invoice_lines,
                'total_amount': draft.total_amount,
                'notes': draft.notes,
                'reference': draft.reference
            },
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
                'source': draft.source,
                'created_at': draft.created_at,
                'generator': f"Odoo Cloud Client v{self.version}"
            },
            'status': 'pending_approval'
        }
    
    def _format_crm_approval(self, draft: DraftCRMLead) -> Dict[str, Any]:
        """Format CRM lead draft as approval request"""
        return {
            'approval_id': f"approval_{draft.draft_id}",
            'type': 'crm_lead',
            'draft_id': draft.draft_id,
            'title': f"CRM Lead: {draft.lead_name}",
            'description': f"Lead with expected revenue ${draft.expected_revenue:.2f}",
            'priority': 'MEDIUM',
            'requires_approval': True,
            'approval_reason': "New CRM lead requires review",
            'lead_details': asdict(draft),
            'actions': {
                'approve': {
                    'action': 'confirm_lead',
                    'description': 'Confirm and assign lead'
                },
                'reject': {
                    'action': 'cancel_lead',
                    'description': 'Reject lead'
                }
            },
            'metadata': {
                'source': draft.source,
                'created_at': draft.created_at,
                'generator': f"Odoo Cloud Client v{self.version}"
            },
            'status': 'pending_approval'
        }
    
    async def _create_approval_markdown(self, draft: Any, json_path: Path):
        """Create markdown summary for approval request"""
        if isinstance(draft, DraftInvoice):
            md_content = f"""# Invoice Approval Request

## Invoice Details
- **Draft ID**: {draft.draft_id}
- **Partner**: {draft.partner_name}
- **Email**: {draft.partner_email or 'N/A'}
- **Phone**: {draft.partner_phone or 'N/A'}
- **Invoice Date**: {draft.invoice_date}
- **Due Date**: {draft.due_date}
- **Currency**: {draft.currency}

## Invoice Lines
| Description | Quantity | Unit Price | Total |
|-------------|----------|------------|-------|
{chr(10).join(f"| {line.get('name', 'Service')} | {line.get('quantity', 1)} | ${line.get('price_unit', 0):.2f} | ${line.get('quantity', 1) * line.get('price_unit', 0):.2f} |" for line in draft.invoice_lines)}

## Total Amount: ${draft.total_amount:.2f}

## Notes
{draft.notes or 'No additional notes'}

## Approval Actions
- **Approve**: Confirm and post invoice in Odoo
- **Reject**: Cancel draft invoice
- **Edit**: Modify draft before confirming

---
*Generated by Odoo Cloud Client v{self.version}*
*Approval file: {json_path.name}*
"""
        else:
            md_content = f"""# CRM Lead Approval Request

## Lead Details
- **Draft ID**: {draft.draft_id}
- **Lead Name**: {draft.lead_name}
- **Company**: {draft.company_name or 'N/A'}
- **Email**: {draft.email or 'N/A'}
- **Phone**: {draft.phone or 'N/A'}
- **Expected Revenue**: ${draft.expected_revenue:.2f}
- **Probability**: {draft.probability}%
- **Stage**: {draft.stage}

## Description
{draft.description or 'No description provided'}

## Tags
{', '.join(draft.tags) if draft.tags else 'None'}

## Approval Actions
- **Approve**: Confirm and assign lead
- **Reject**: Reject lead

---
*Generated by Odoo Cloud Client v{self.version}*
*Approval file: {json_path.name}*
"""
        
        md_path = json_path.with_suffix('.md')
        
        if not self.dry_run:
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            logger.debug(f"Markdown summary created: {md_path}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get client status"""
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
            'timestamp': datetime.now().isoformat()
        }
    
    async def run_demo(self):
        """Run demo invoice and lead creation"""
        print(f"""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     💼  PLATINUM TIER ODOO CLOUD CLIENT  💼              ║
║                                                           ║
║     Version: {self.version}
║     DRY_RUN: {self.dry_run}
║     Odoo Enabled: {self.odoo_enabled}
║     Odoo URL: {self.odoo_url}
║                                                           ║
║     SECURITY CONSTRAINTS:                                 ║
║     ✓ Cloud creates DRAFTS only                          ║
║     ✗ Cloud NEVER confirms transactions                  ║
║     ✓ Approval requests to Pending_Approval              ║
║     ✓ Local executor handles confirmation                ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
        """)
        
        logger.info(f"Odoo Cloud Client starting v{self.version}")
        
        # Demo: Create draft invoice
        logger.info("Creating demo draft invoice...")
        draft_invoice = await self.create_draft_invoice(
            partner_name="Demo Customer Inc.",
            partner_email="customer@demo.com",
            partner_phone="+1-555-0123",
            invoice_lines=[
                {'name': 'Consulting Services', 'quantity': 10, 'price_unit': 150.00},
                {'name': 'Software License', 'quantity': 1, 'price_unit': 500.00}
            ],
            invoice_date=datetime.now().strftime('%Y-%m-%d'),
            due_date=(datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            currency='USD',
            notes="Thank you for your business!",
            reference="DEMO-001"
        )
        
        logger.info(f"Draft invoice created: {draft_invoice.draft_id}")
        logger.info(f"Total amount: ${draft_invoice.total_amount:.2f}")
        
        # Demo: Create CRM lead
        logger.info("Creating demo CRM lead...")
        draft_lead = await self.create_draft_crm_lead(
            lead_name="Enterprise Opportunity - Acme Corp",
            expected_revenue=50000.00,
            company_name="Acme Corporation",
            email="contact@acme.com",
            phone="+1-555-0456",
            probability=60,
            description="Large enterprise deal for annual subscription",
            tags=['enterprise', 'high-value', 'q1-2025']
        )
        
        logger.info(f"Draft CRM lead created: {draft_lead.draft_id}")
        logger.info(f"Expected revenue: ${draft_lead.expected_revenue:.2f}")
        
        # Print summary
        print(f"\n💼 Demo Completed!")
        print(f"   Draft Invoice: {draft_invoice.draft_id} (${draft_invoice.total_amount:.2f})")
        print(f"   CRM Lead: {draft_lead.draft_id} (${draft_lead.expected_revenue:.2f})")
        print(f"   Approval requests created in: {self.pending_approval_dir}")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Platinum Tier Odoo Cloud Client')
    parser.add_argument('--dry-run', action='store_true', help='Run in dry-run mode')
    parser.add_argument('--demo', action='store_true', help='Run demo')
    parser.add_argument('--status', action='store_true', help='Show status and exit')
    args = parser.parse_args()
    
    client = OdooCloudClient()
    
    if args.status:
        status = client.get_status()
        print(json.dumps(status, indent=2))
        return
    
    if args.dry_run:
        client.dry_run = True
    
    if args.demo:
        await client.run_demo()
        return
    
    # Default: run demo
    await client.run_demo()


if __name__ == "__main__":
    asyncio.run(main())
