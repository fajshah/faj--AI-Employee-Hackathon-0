"""
Odoo Webhook Handler - Production Integration
=============================================
Receives webhooks from Odoo ERP and triggers AI Employee automations:
- new_lead → WhatsApp greeting + Email follow-up + LinkedIn draft
- sale_confirmed → Thank-you WhatsApp + LinkedIn success story (optional)
- invoice_created → Payment reminder workflow

Architecture:
Odoo (Docker) → Webhook → AI Employee (Port 5050) → 
    → Gmail API / SMTP
    → WhatsApp Business API
    → LinkedIn API
    → CRM Logs

Author: AI Employee System
Version: 1.0.0-Production
"""

import os
import sys
import json
import hmac
import hashlib
import logging
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from flask import Flask, request, jsonify, Response
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.gold')

# ===========================================
# Configuration
# ===========================================

WEBHOOK_SECRET = os.getenv('ODOO_WEBHOOK_SECRET', 'change-this-in-production')
WEBHOOK_PORT = int(os.getenv('ODOO_WEBHOOK_PORT', '5050'))
MCP_SERVER_URL = os.getenv('MCP_SERVER_URL', 'http://localhost:5001')

# External API Configuration
GMAIL_ENABLED = os.getenv('GMAIL_CLIENT_ID') is not None
WHATSAPP_ENABLED = os.getenv('WHATSAPP_ACCESS_TOKEN') is not None
LINKEDIN_ENABLED = os.getenv('LINKEDIN_ACCESS_TOKEN') is not None

# ===========================================
# Logging Setup
# ===========================================

class WebhookLogger:
    """Dual logging: File + Console with structured JSON logs"""

    def __init__(self, name: str, log_file: str = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Clear existing handlers
        self.logger.handlers = []

        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
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


logger_wrapper = WebhookLogger(
    name='odoo_webhook',
    log_file='Logs/odoo_webhook.log'
)
logger = logger_wrapper.get_logger()


# ===========================================
# Data Classes
# ===========================================

@dataclass
class LeadData:
    """Lead data from Odoo CRM"""
    lead_id: str
    partner_name: str
    contact_name: str
    email: str
    phone: str
    company_name: str
    opportunity_type: str
    priority: str
    stage: str
    expected_revenue: float
    description: str
    source: str
    tags: List[str]
    created_at: str
    odoo_url: str


@dataclass
class SaleData:
    """Sale order data from Odoo"""
    sale_id: str
    order_name: str
    partner_name: str
    partner_email: str
    partner_phone: str
    company_name: str
    total_amount: float
    currency: str
    payment_state: str
    order_date: str
    expected_date: str
    items: List[Dict[str, Any]]
    salesperson: str
    odoo_url: str


@dataclass
class InvoiceData:
    """Invoice data from Odoo"""
    invoice_id: str
    invoice_number: str
    partner_name: str
    partner_email: str
    partner_phone: str
    company_name: str
    total_amount: float
    amount_due: float
    currency: str
    due_date: str
    invoice_date: str
    payment_state: str
    odoo_url: str


@dataclass
class WebhookEvent:
    """Standardized webhook event"""
    event_id: str
    event_type: str  # new_lead, sale_confirmed, invoice_created
    timestamp: str
    data: Dict[str, Any]
    source: str = "odoo"
    processed: bool = False
    error: Optional[str] = None


# ===========================================
# API Client for MCP Server
# ===========================================

class MCPClient:
    """Client for communicating with MCP Server for external actions"""

    def __init__(self, base_url: str = MCP_SERVER_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        self.timeout = 30

    def send_email(self, to: str, subject: str, body: str,
                   cc: str = None, bcc: str = None, task_id: str = None) -> Dict[str, Any]:
        """Send email via MCP Server"""
        payload = {
            "task_id": task_id or f"email_{int(time.time())}",
            "to": to,
            "subject": subject,
            "body": body
        }
        if cc:
            payload["cc"] = cc
        if bcc:
            payload["bcc"] = bcc

        try:
            response = self.session.post(
                f"{self.base_url}/api/email/send",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            logger.info(f"Email sent to {to}: {result.get('status')}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send email: {str(e)}")
            return {"status": "error", "error": str(e)}

    def send_whatsapp(self, to: str, message: str,
                      message_type: str = "text", task_id: str = None) -> Dict[str, Any]:
        """Send WhatsApp message via MCP Server"""
        payload = {
            "task_id": task_id or f"whatsapp_{int(time.time())}",
            "to": to,
            "message": message,
            "type": message_type
        }

        try:
            response = self.session.post(
                f"{self.base_url}/api/whatsapp/send",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            logger.info(f"WhatsApp sent to {to}: {result.get('status')}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send WhatsApp: {str(e)}")
            return {"status": "error", "error": str(e)}

    def post_linkedin(self, content: str, hashtags: List[str] = None,
                      visibility: str = "PUBLIC", task_id: str = None) -> Dict[str, Any]:
        """Post to LinkedIn via MCP Server"""
        payload = {
            "task_id": task_id or f"linkedin_{int(time.time())}",
            "content": content,
            "hashtags": hashtags or [],
            "visibility": visibility
        }

        try:
            response = self.session.post(
                f"{self.base_url}/api/social/post",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            logger.info(f"LinkedIn post created: {result.get('status')}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to post to LinkedIn: {str(e)}")
            return {"status": "error", "error": str(e)}

    def create_linkedin_draft(self, content: str, hashtags: List[str] = None,
                               task_id: str = None) -> Dict[str, Any]:
        """Create LinkedIn draft (for review before posting)"""
        # For now, create as a draft task in the system
        draft_dir = Path("LinkedIn_Drafts")
        draft_dir.mkdir(exist_ok=True)

        draft_data = {
            "task_id": task_id or f"linkedin_draft_{int(time.time())}",
            "content": content,
            "hashtags": hashtags or [],
            "status": "draft",
            "created_at": datetime.now().isoformat()
        }

        draft_file = draft_dir / f"{draft_data['task_id']}.json"
        with open(draft_file, 'w', encoding='utf-8') as f:
            json.dump(draft_data, f, indent=2)

        logger.info(f"LinkedIn draft created: {draft_file}")
        return {"status": "draft_created", "file": str(draft_file)}


# ===========================================
# Event Processors
# ===========================================

class OdooEventProcessor:
    """Process Odoo webhook events and trigger automations"""

    def __init__(self):
        self.mcp = MCPClient()
        self.logs_dir = Path("Logs/odoo_events")
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def process_new_lead(self, lead_data: LeadData) -> Dict[str, Any]:
        """
        Process new_lead event:
        1. Send WhatsApp greeting
        2. Send Email follow-up
        3. Log to LinkedIn draft system
        """
        logger.info(f"Processing new lead: {lead_data.lead_id} - {lead_data.contact_name}")

        results = {
            "event_type": "new_lead",
            "lead_id": lead_data.lead_id,
            "timestamp": datetime.now().isoformat(),
            "actions": {}
        }

        # 1. Send WhatsApp greeting
        if WHATSAPP_ENABLED and lead_data.phone:
            whatsapp_msg = self._generate_lead_whatsapp_greeting(lead_data)
            results["actions"]["whatsapp"] = self.mcp.send_whatsapp(
                to=lead_data.phone,
                message=whatsapp_msg,
                task_id=f"lead_whatsapp_{lead_data.lead_id}"
            )
        else:
            results["actions"]["whatsapp"] = {"status": "skipped", "reason": "WhatsApp disabled or no phone"}

        # 2. Send Email follow-up
        if GMAIL_ENABLED and lead_data.email:
            email_subject, email_body = self._generate_lead_email_followup(lead_data)
            results["actions"]["email"] = self.mcp.send_email(
                to=lead_data.email,
                subject=email_subject,
                body=email_body,
                task_id=f"lead_email_{lead_data.lead_id}"
            )
        else:
            results["actions"]["email"] = {"status": "skipped", "reason": "Email disabled or no email"}

        # 3. Create LinkedIn draft (for potential success story later)
        if LINKEDIN_ENABLED:
            linkedin_content = self._generate_lead_linkedin_draft(lead_data)
            results["actions"]["linkedin"] = self.mcp.create_linkedin_draft(
                content=linkedin_content,
                hashtags=["NewClient", "BusinessGrowth", "Partnership"],
                task_id=f"lead_linkedin_{lead_data.lead_id}"
            )
        else:
            results["actions"]["linkedin"] = {"status": "skipped", "reason": "LinkedIn disabled"}

        # Log the event
        self._log_event("new_lead", lead_data.lead_id, results)

        return results

    def process_sale_confirmed(self, sale_data: SaleData,
                                post_linkedin: bool = True) -> Dict[str, Any]:
        """
        Process sale_confirmed event:
        1. Send thank-you WhatsApp
        2. Post LinkedIn success story (if flag is True)
        """
        logger.info(f"Processing confirmed sale: {sale_data.sale_id} - {sale_data.partner_name}")

        results = {
            "event_type": "sale_confirmed",
            "sale_id": sale_data.sale_id,
            "timestamp": datetime.now().isoformat(),
            "actions": {}
        }

        # 1. Send thank-you WhatsApp
        if WHATSAPP_ENABLED and sale_data.partner_phone:
            whatsapp_msg = self._generate_sale_thankyou_whatsapp(sale_data)
            results["actions"]["whatsapp"] = self.mcp.send_whatsapp(
                to=sale_data.partner_phone,
                message=whatsapp_msg,
                task_id=f"sale_whatsapp_{sale_data.sale_id}"
            )
        else:
            results["actions"]["whatsapp"] = {"status": "skipped", "reason": "WhatsApp disabled or no phone"}

        # 2. Post LinkedIn success story (optional)
        if post_linkedin and LINKEDIN_ENABLED:
            linkedin_content = self._generate_sale_linkedin_post(sale_data)
            results["actions"]["linkedin"] = self.mcp.post_linkedin(
                content=linkedin_content,
                hashtags=["ClientSuccess", "BusinessGrowth", "Partnership", "Milestone"],
                visibility="PUBLIC",
                task_id=f"sale_linkedin_{sale_data.sale_id}"
            )
        elif post_linkedin:
            results["actions"]["linkedin"] = {"status": "skipped", "reason": "LinkedIn disabled"}
        else:
            results["actions"]["linkedin"] = {"status": "skipped", "reason": "post_linkedin flag is False"}

        # Log the event
        self._log_event("sale_confirmed", sale_data.sale_id, results)

        return results

    def process_invoice_created(self, invoice_data: InvoiceData) -> Dict[str, Any]:
        """
        Process invoice_created event:
        1. Send payment reminder email
        2. Send WhatsApp reminder for high-value invoices
        """
        logger.info(f"Processing new invoice: {invoice_data.invoice_id} - {invoice_data.partner_name}")

        results = {
            "event_type": "invoice_created",
            "invoice_id": invoice_data.invoice_id,
            "timestamp": datetime.now().isoformat(),
            "actions": {}
        }

        # 1. Send payment reminder email
        if GMAIL_ENABLED and invoice_data.partner_email:
            email_subject, email_body = self._generate_invoice_email(invoice_data)
            results["actions"]["email"] = self.mcp.send_email(
                to=invoice_data.partner_email,
                subject=email_subject,
                body=email_body,
                task_id=f"invoice_email_{invoice_data.invoice_id}"
            )
        else:
            results["actions"]["email"] = {"status": "skipped", "reason": "Email disabled or no email"}

        # 2. Send WhatsApp reminder for high-value invoices (> $1000)
        if WHATSAPP_ENABLED and invoice_data.partner_phone:
            if invoice_data.total_amount >= 1000:
                whatsapp_msg = self._generate_invoice_whatsapp_reminder(invoice_data)
                results["actions"]["whatsapp_reminder"] = self.mcp.send_whatsapp(
                    to=invoice_data.partner_phone,
                    message=whatsapp_msg,
                    task_id=f"invoice_whatsapp_{invoice_data.invoice_id}"
                )
            else:
                results["actions"]["whatsapp_reminder"] = {"status": "skipped", "reason": "Invoice amount < $1000"}
        else:
            results["actions"]["whatsapp_reminder"] = {"status": "skipped", "reason": "WhatsApp disabled or no phone"}

        # Log the event
        self._log_event("invoice_created", invoice_data.invoice_id, results)

        return results

    # ===========================================
    # Message Generation Methods
    # ===========================================

    def _generate_lead_whatsapp_greeting(self, lead: LeadData) -> str:
        """Generate personalized WhatsApp greeting for new lead"""
        return f"""Hello {lead.contact_name}! 👋

Thank you for your interest in {lead.company_name or 'our services'}.

We've received your inquiry about {lead.opportunity_type or 'our products/services'} and one of our team members will be in touch shortly.

In the meantime, feel free to reach out if you have any questions!

Best regards,
{lead.company_name or 'Our Team'}"""

    def _generate_lead_email_followup(self, lead: LeadData) -> tuple:
        """Generate personalized email follow-up for new lead"""
        subject = f"Welcome {lead.contact_name} - Thank you for your interest!"

        body = f"""Dear {lead.contact_name},

Thank you for reaching out to us! We're excited to learn more about your needs.

LEAD DETAILS:
-------------
• Inquiry Type: {lead.opportunity_type or 'General inquiry'}
• Priority: {lead.priority or 'Normal'}
• Expected Revenue: {lead.expected_revenue or 'To be discussed'}

NEXT STEPS:
-----------
1. Our team will review your requirements
2. We'll schedule a call to discuss further
3. You'll receive a customized proposal

We typically respond within 24 hours during business days.

If you have any urgent questions, please don't hesitate to contact us.

Best regards,
The Team at {lead.company_name or 'Our Company'}

---
Reference: Lead #{lead.lead_id}
Source: {lead.source or 'Direct'}
"""
        return subject, body

    def _generate_lead_linkedin_draft(self, lead: LeadData) -> str:
        """Generate LinkedIn draft for potential future success story"""
        return f"""🤝 New Partnership Opportunity

We're excited to connect with {lead.partner_name or lead.contact_name} from {lead.company_name or 'an innovative company'}.

Looking forward to exploring how we can work together to achieve great results!

#NewClient #BusinessGrowth #Partnership #B2B"""

    def _generate_sale_thankyou_whatsapp(self, sale: SaleData) -> str:
        """Generate thank-you WhatsApp message for confirmed sale"""
        return f"""🎉 Thank you for your order, {sale.partner_name}!

We're thrilled to confirm your order #{sale.order_name}.

ORDER SUMMARY:
• Total: {sale.currency} {sale.total_amount:,.2f}
• Expected Delivery: {sale.expected_date or 'To be confirmed'}

Our team will keep you updated on the progress. You'll receive a detailed confirmation email shortly.

Thank you for choosing us! 🙏

Best regards,
{sale.company_name or 'Our Team'}"""

    def _generate_sale_linkedin_post(self, sale: SaleData) -> str:
        """Generate LinkedIn success story post"""
        return f"""🎉 Exciting News! Another Successful Partnership!

We're thrilled to announce our new partnership with {sale.partner_name or sale.company_name}!

This collaboration represents another milestone in our mission to deliver exceptional value to our clients. We're looking forward to achieving great results together.

💼 What we'll be working on:
{self._summarize_sale_items(sale.items)}

Here's to a successful partnership! 🚀

#ClientSuccess #BusinessGrowth #Partnership #Milestone #B2B"""

    def _summarize_sale_items(self, items: List[Dict[str, Any]]) -> str:
        """Summarize sale items for LinkedIn post"""
        if not items:
            return "Custom solutions tailored to client needs."

        item_names = [item.get('name', 'Product/Service') for item in items[:3]]
        if len(items) > 3:
            item_names.append(f"...and {len(items) - 3} more")

        return "• " + "\n• ".join(item_names)

    def _generate_invoice_email(self, invoice: InvoiceData) -> tuple:
        """Generate invoice notification email"""
        subject = f"Invoice {invoice.invoice_number} from {invoice.company_name or 'Our Company'}"

        body = f"""Dear {invoice.partner_name},

Thank you for your business! Please find your invoice details below.

INVOICE DETAILS:
----------------
• Invoice Number: {invoice.invoice_number}
• Invoice Date: {invoice.invoice_date}
• Due Date: {invoice.due_date}
• Total Amount: {invoice.currency} {invoice.total_amount:,.2f}
• Amount Due: {invoice.currency} {invoice.amount_due:,.2f}
• Payment Status: {invoice.payment_state}

PAYMENT INFORMATION:
--------------------
Please arrange payment by the due date to avoid any late fees.

If you have already made the payment, please disregard this reminder.

For any questions regarding this invoice, please contact our accounts team.

Best regards,
Accounts Department
{invoice.company_name or 'Our Company'}

---
Reference: Invoice #{invoice.invoice_id}
View in Portal: {invoice.odoo_url}
"""
        return subject, body

    def _generate_invoice_whatsapp_reminder(self, invoice: InvoiceData) -> str:
        """Generate WhatsApp reminder for high-value invoice"""
        return f"""📄 Invoice Reminder

Dear {invoice.partner_name},

A friendly reminder about your invoice:

• Invoice: {invoice.invoice_number}
• Amount: {invoice.currency} {invoice.total_amount:,.2f}
• Due Date: {invoice.due_date}

Please arrange payment at your earliest convenience.

Thank you! 🙏

{invoice.company_name or 'Our Team'}"""

    # ===========================================
    # Logging Methods
    # ===========================================

    def _log_event(self, event_type: str, record_id: str, results: Dict[str, Any]):
        """Log event results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.logs_dir / f"{event_type}_{record_id}_{timestamp}.json"

        log_entry = {
            "event_type": event_type,
            "record_id": record_id,
            "timestamp": datetime.now().isoformat(),
            "results": results
        }

        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, indent=2, default=str)

        logger.debug(f"Event logged: {log_file}")


# ===========================================
# Flask Webhook Server
# ===========================================

def create_app() -> Flask:
    """Create and configure the Flask webhook server"""
    app = Flask(__name__)
    processor = OdooEventProcessor()

    # ===========================================
    # Middleware
    # ===========================================

    @app.before_request
    def log_request():
        """Log incoming requests"""
        logger.debug(f"Incoming request: {request.method} {request.path}")
        logger.debug(f"Headers: {dict(request.headers)}")

    # ===========================================
    # Health Check
    # ===========================================

    @app.route('/health', methods=['GET'])
    def health_check() -> Response:
        """Health check endpoint"""
        return jsonify({
            "status": "healthy",
            "service": "odoo_webhook_handler",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "gmail": "enabled" if GMAIL_ENABLED else "disabled",
                "whatsapp": "enabled" if WHATSAPP_ENABLED else "disabled",
                "linkedin": "enabled" if LINKEDIN_ENABLED else "disabled"
            }
        })

    # ===========================================
    # Main Webhook Endpoint
    # ===========================================

    @app.route('/odoo_webhook', methods=['POST'])
    def odoo_webhook() -> Response:
        """
        Main webhook endpoint for Odoo events

        Expected payload structure:
        {
            "event_type": "new_lead" | "sale_confirmed" | "invoice_created",
            "secret": "webhook_secret",
            "data": { ... }
        }
        """
        try:
            # Validate content type
            if not request.is_json:
                logger.warning("Invalid content type - expected JSON")
                return jsonify({
                    "status": "error",
                    "error": "Content-Type must be application/json"
                }), 400

            payload = request.get_json()

            # Validate webhook secret
            received_secret = payload.get('secret', '')
            if not hmac.compare_digest(received_secret, WEBHOOK_SECRET):
                logger.warning("Invalid webhook secret")
                return jsonify({
                    "status": "error",
                    "error": "Invalid webhook secret"
                }), 401

            # Extract event type
            event_type = payload.get('event_type')
            if not event_type:
                return jsonify({
                    "status": "error",
                    "error": "Missing event_type"
                }), 400

            logger.info(f"Received Odoo event: {event_type}")

            # Route to appropriate handler
            if event_type == 'new_lead':
                result = handle_new_lead(payload.get('data', {}), processor)
            elif event_type == 'sale_confirmed':
                result = handle_sale_confirmed(payload.get('data', {}), processor)
            elif event_type == 'invoice_created':
                result = handle_invoice_created(payload.get('data', {}), processor)
            else:
                return jsonify({
                    "status": "error",
                    "error": f"Unknown event_type: {event_type}"
                }), 400

            return jsonify(result)

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {str(e)}")
            return jsonify({
                "status": "error",
                "error": "Invalid JSON payload"
            }), 400

        except Exception as e:
            logger.error(f"Webhook error: {str(e)}", exc_info=True)
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500

    # ===========================================
    # Event Handlers
    # ===========================================

    def handle_new_lead(data: Dict[str, Any], processor: OdooEventProcessor) -> Dict[str, Any]:
        """Handle new_lead event"""
        try:
            lead = LeadData(
                lead_id=str(data.get('id', '')),
                partner_name=data.get('partner_name', ''),
                contact_name=data.get('contact_name', ''),
                email=data.get('email', ''),
                phone=data.get('phone', ''),
                company_name=data.get('company_name', ''),
                opportunity_type=data.get('opportunity_type', ''),
                priority=data.get('priority', 'Normal'),
                stage=data.get('stage', 'New'),
                expected_revenue=float(data.get('expected_revenue', 0) or 0),
                description=data.get('description', ''),
                source=data.get('source', 'Direct'),
                tags=data.get('tags', []),
                created_at=data.get('created_at', datetime.now().isoformat()),
                odoo_url=data.get('odoo_url', '')
            )

            result = processor.process_new_lead(lead)
            result["status"] = "success"
            return result

        except Exception as e:
            logger.error(f"Error handling new_lead: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }

    def handle_sale_confirmed(data: Dict[str, Any], processor: OdooEventProcessor) -> Dict[str, Any]:
        """Handle sale_confirmed event"""
        try:
            sale = SaleData(
                sale_id=str(data.get('id', '')),
                order_name=data.get('name', ''),
                partner_name=data.get('partner_name', ''),
                partner_email=data.get('partner_email', ''),
                partner_phone=data.get('partner_phone', ''),
                company_name=data.get('company_name', ''),
                total_amount=float(data.get('amount_total', 0) or 0),
                currency=data.get('currency', 'USD'),
                payment_state=data.get('payment_state', 'pending'),
                order_date=data.get('date_order', ''),
                expected_date=data.get('expected_date', ''),
                items=data.get('order_lines', []),
                salesperson=data.get('salesperson', ''),
                odoo_url=data.get('odoo_url', '')
            )

            # Check if LinkedIn posting is enabled for this sale
            post_linkedin = data.get('post_linkedin', True)

            result = processor.process_sale_confirmed(sale, post_linkedin)
            result["status"] = "success"
            return result

        except Exception as e:
            logger.error(f"Error handling sale_confirmed: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }

    def handle_invoice_created(data: Dict[str, Any], processor: OdooEventProcessor) -> Dict[str, Any]:
        """Handle invoice_created event"""
        try:
            invoice = InvoiceData(
                invoice_id=str(data.get('id', '')),
                invoice_number=data.get('number', ''),
                partner_name=data.get('partner_name', ''),
                partner_email=data.get('partner_email', ''),
                partner_phone=data.get('partner_phone', ''),
                company_name=data.get('company_name', ''),
                total_amount=float(data.get('amount_total', 0) or 0),
                amount_due=float(data.get('amount_due', 0) or 0),
                currency=data.get('currency', 'USD'),
                due_date=data.get('invoice_date_due', ''),
                invoice_date=data.get('invoice_date', ''),
                payment_state=data.get('payment_state', 'not_paid'),
                odoo_url=data.get('odoo_url', '')
            )

            result = processor.process_invoice_created(invoice)
            result["status"] = "success"
            return result

        except Exception as e:
            logger.error(f"Error handling invoice_created: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }

    # ===========================================
    # Status Endpoint
    # ===========================================

    @app.route('/api/status', methods=['GET'])
    def api_status() -> Response:
        """Get API status and configuration"""
        return jsonify({
            "service": "odoo_webhook_handler",
            "version": "1.0.0",
            "endpoints": [
                "/health",
                "/odoo_webhook",
                "/api/status"
            ],
            "supported_events": [
                "new_lead",
                "sale_confirmed",
                "invoice_created"
            ],
            "services": {
                "gmail": "enabled" if GMAIL_ENABLED else "disabled",
                "whatsapp": "enabled" if WHATSAPP_ENABLED else "disabled",
                "linkedin": "enabled" if LINKEDIN_ENABLED else "disabled"
            },
            "timestamp": datetime.now().isoformat()
        })

    return app


# ===========================================
# Main Entry Point
# ===========================================

def main():
    """Main entry point"""
    app = create_app()

    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     🔄 ODOO WEBHOOK HANDLER - AI EMPLOYEE INTEGRATION    ║
║                                                           ║
║     Version: 1.0.0-Production                            ║
║     Port: {port}                                         ║
║                                                           ║
║     Supported Events:                                     ║
║     • new_lead                                            ║
║     • sale_confirmed                                      ║
║     • invoice_created                                     ║
║                                                           ║
║     External Services:                                    ║
║     • Gmail: {gmail}                                      ║
║     • WhatsApp: {whatsapp}                                ║
║     • LinkedIn: {linkedin}                                ║
║                                                           ║
║     Endpoints:                                            ║
║     • GET  /health       - Health check                   ║
║     • POST /odoo_webhook - Main webhook                   ║
║     • GET  /api/status   - API status                     ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """.format(
        port=WEBHOOK_PORT,
        gmail="✅ Enabled" if GMAIL_ENABLED else "❌ Disabled",
        whatsapp="✅ Enabled" if WHATSAPP_ENABLED else "❌ Disabled",
        linkedin="✅ Enabled" if LINKEDIN_ENABLED else "❌ Disabled"
    ))

    logger.info(f"Starting Odoo Webhook Handler on port {WEBHOOK_PORT}")

    # Run the Flask server
    app.run(
        host='0.0.0.0',
        port=WEBHOOK_PORT,
        debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true',
        threaded=True
    )


if __name__ == "__main__":
    main()
