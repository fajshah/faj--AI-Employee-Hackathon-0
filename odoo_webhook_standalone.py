"""
Standalone Odoo Webhook Handler - Direct API Integration
=========================================================
Production webhook handler with DIRECT API calls (no MCP Server dependency)

Features:
- Direct Gmail API integration
- Direct WhatsApp Business API
- Direct LinkedIn API
- Local file-based draft system
- Comprehensive error handling
- Production-safe logging
"""

import os
import sys
import json
import hmac
import hashlib
import logging
import time
import base64
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
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

# Direct API Configuration
GMAIL_CLIENT_ID = os.getenv('GMAIL_CLIENT_ID')
GMAIL_CLIENT_SECRET = os.getenv('GMAIL_CLIENT_SECRET')
GMAIL_TOKEN_FILE = os.getenv('GMAIL_TOKEN_FILE', 'tokens/gmail_token.json')

WHATSAPP_ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
WHATSAPP_API_VERSION = os.getenv('WHATSAPP_API_VERSION', 'v18.0')

LINKEDIN_ACCESS_TOKEN = os.getenv('LINKEDIN_ACCESS_TOKEN')
LINKEDIN_PERSON_ID = os.getenv('LINKEDIN_PERSON_ID')

# SMTP Fallback
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

# Feature flags
GMAIL_DIRECT_ENABLED = GMAIL_CLIENT_ID is not None
WHATSAPP_DIRECT_ENABLED = WHATSAPP_ACCESS_TOKEN is not None
LINKEDIN_DIRECT_ENABLED = LINKEDIN_ACCESS_TOKEN is not None
SMTP_ENABLED = SMTP_USERNAME is not None

# ===========================================
# Logging Setup
# ===========================================

class WebhookLogger:
    """Dual logging: File + Console with structured JSON logs"""

    def __init__(self, name: str, log_file: str = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
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
    name='odoo_webhook_standalone',
    log_file='Logs/odoo_webhook_standalone.log'
)
logger = logger_wrapper.get_logger()


# ===========================================
# Data Classes
# ===========================================

@dataclass
class LeadData:
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


# ===========================================
# Direct API Clients
# ===========================================

class GmailClient:
    """Direct Gmail API client with OAuth 2.0"""

    def __init__(self):
        self.service = None
        self._initialized = False
        self._init_gmail()

    def _init_gmail(self):
        """Initialize Gmail API with OAuth 2.0"""
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build

            scopes = ['https://www.googleapis.com/auth/gmail.send']
            credentials_file = 'client_secret_725259256203-a14h8ovoi908q7nv5sigh8ak6456gsnl.apps.googleusercontent.com.json'

            creds = None
            if os.path.exists(GMAIL_TOKEN_FILE):
                creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_FILE, scopes)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                elif os.path.exists(credentials_file):
                    logger.warning("Gmail token expired. Run authenticate_gmail.py to refresh.")
                    return

            self.service = build('gmail', 'v1', credentials=creds)
            self._initialized = True
            logger.info("Gmail API client initialized")

        except ImportError:
            logger.warning("Google API libraries not installed. Gmail features disabled.")
        except Exception as e:
            logger.error(f"Failed to initialize Gmail API: {str(e)}")

    def send_email(self, to: str, subject: str, body: str,
                   cc: str = None, bcc: str = None) -> Dict[str, Any]:
        """Send email via Gmail API"""
        if not self._initialized:
            logger.warning("Gmail API not initialized, falling back to SMTP")
            return self._send_smtp(to, subject, body, cc, bcc)

        try:
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            message.attach(MIMEText(body, 'plain'))

            if cc:
                message['cc'] = cc

            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            sent_message = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            logger.info(f"Email sent via Gmail API. Message ID: {sent_message['id']}")
            return {
                "status": "success",
                "message_id": sent_message['id'],
                "thread_id": sent_message.get('threadId'),
                "method": "gmail_api"
            }

        except Exception as e:
            logger.error(f"Gmail API error: {str(e)}")
            return self._send_smtp(to, subject, body, cc, bcc)

    def _send_smtp(self, to: str, subject: str, body: str,
                   cc: str = None, bcc: str = None) -> Dict[str, Any]:
        """Fallback: Send via SMTP"""
        if not SMTP_ENABLED:
            logger.error("SMTP not configured")
            return {"status": "error", "error": "No email service available"}

        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart()
            msg['From'] = SMTP_USERNAME
            msg['To'] = to
            msg['Subject'] = subject

            if cc:
                msg['Cc'] = cc

            msg.attach(MIMEText(body, 'plain'))

            recipients = [to]
            if cc:
                recipients.extend(cc.split(','))
            if bcc:
                recipients.extend(bcc.split(','))

            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg, to_addrs=recipients)
            server.quit()

            logger.info(f"Email sent via SMTP to {to}")
            return {
                "status": "success",
                "method": "smtp",
                "recipients": recipients
            }

        except Exception as e:
            logger.error(f"SMTP error: {str(e)}")
            return {"status": "error", "error": str(e)}


class WhatsAppClient:
    """Direct WhatsApp Business API client"""

    def __init__(self):
        self.access_token = WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = WHATSAPP_PHONE_NUMBER_ID
        self.api_version = WHATSAPP_API_VERSION
        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"

    def send_message(self, to: str, message: str,
                     message_type: str = "text") -> Dict[str, Any]:
        """Send WhatsApp message via Business API"""
        if not self.access_token or not self.phone_number_id:
            logger.warning("WhatsApp not configured")
            return {"status": "skipped", "reason": "WhatsApp not configured"}

        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }

            clean_phone = to.replace('+', '').replace(' ', '').replace('-', '')

            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": clean_phone,
                "type": message_type
            }

            if message_type == 'text':
                payload["text"] = {"body": message, "preview_url": True}

            response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)

            if response.status_code != 200:
                logger.error(f"WhatsApp API error: {response.status_code} - {response.text}")
                return {"status": "error", "http_code": response.status_code, "error": response.text}

            result = response.json()
            message_id = result.get('messages', [{}])[0].get('id', 'unknown')

            logger.info(f"WhatsApp sent to {to}. Message ID: {message_id}")
            return {
                "status": "success",
                "message_id": message_id,
                "contact_id": result.get('contacts', [{}])[0].get('id'),
                "method": "whatsapp_api"
            }

        except Exception as e:
            logger.error(f"WhatsApp error: {str(e)}")
            return {"status": "error", "error": str(e)}


class LinkedInClient:
    """Direct LinkedIn API client"""

    def __init__(self):
        self.access_token = LINKEDIN_ACCESS_TOKEN
        self.person_id = LINKEDIN_PERSON_ID

    def post(self, content: str, hashtags: List[str] = None,
             visibility: str = "PUBLIC") -> Dict[str, Any]:
        """Post to LinkedIn API"""
        if not self.access_token:
            logger.warning("LinkedIn not configured")
            return {"status": "skipped", "reason": "LinkedIn not configured"}

        try:
            url = "https://api.linkedin.com/v2/ugcPosts"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0'
            }

            if hashtags:
                hashtag_string = ' '.join([f'#{tag}' for tag in hashtags])
                full_content = f"{content}\n\n{hashtag_string}"
            else:
                full_content = content

            payload = {
                "author": f"urn:li:person:{self.person_id}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": full_content},
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": visibility
                }
            }

            response = requests.post(url, headers=headers, json=payload, timeout=30)

            if response.status_code not in [200, 201]:
                logger.error(f"LinkedIn API error: {response.status_code} - {response.text}")
                return {"status": "error", "http_code": response.status_code, "error": response.text}

            result = response.json()
            post_id = result.get('id', 'unknown')

            logger.info(f"LinkedIn post created. ID: {post_id}")
            return {
                "status": "success",
                "post_id": post_id,
                "method": "linkedin_api"
            }

        except Exception as e:
            logger.error(f"LinkedIn error: {str(e)}")
            return {"status": "error", "error": str(e)}

    def create_draft(self, content: str, hashtags: List[str] = None,
                     task_id: str = None) -> Dict[str, Any]:
        """Create LinkedIn draft (saved locally for review)"""
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
# Event Processor
# ===========================================

class OdooEventProcessor:
    """Process Odoo webhook events with direct API calls"""

    def __init__(self):
        self.gmail = GmailClient()
        self.whatsapp = WhatsAppClient()
        self.linkedin = LinkedInClient()
        self.logs_dir = Path("Logs/odoo_events")
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def process_new_lead(self, lead_data: LeadData) -> Dict[str, Any]:
        """Process new_lead: WhatsApp + Email + LinkedIn Draft"""
        logger.info(f"Processing new lead: {lead_data.lead_id} - {lead_data.contact_name}")

        results = {
            "event_type": "new_lead",
            "lead_id": lead_data.lead_id,
            "timestamp": datetime.now().isoformat(),
            "actions": {}
        }

        # 1. WhatsApp greeting
        if lead_data.phone:
            msg = self._generate_lead_whatsapp(lead_data)
            results["actions"]["whatsapp"] = self.whatsapp.send_message(lead_data.phone, msg)
        else:
            results["actions"]["whatsapp"] = {"status": "skipped", "reason": "No phone"}

        # 2. Email follow-up
        if lead_data.email:
            subject, body = self._generate_lead_email(lead_data)
            results["actions"]["email"] = self.gmail.send_email(lead_data.email, subject, body)
        else:
            results["actions"]["email"] = {"status": "skipped", "reason": "No email"}

        # 3. LinkedIn draft
        content = self._generate_lead_linkedin(lead_data)
        results["actions"]["linkedin"] = self.linkedin.create_draft(
            content, ["NewClient", "BusinessGrowth"],
            f"lead_linkedin_{lead_data.lead_id}"
        )

        self._log_event("new_lead", lead_data.lead_id, results)
        return results

    def process_sale_confirmed(self, sale_data: SaleData,
                                post_linkedin: bool = True) -> Dict[str, Any]:
        """Process sale_confirmed: Thank-you WhatsApp + LinkedIn Post"""
        logger.info(f"Processing confirmed sale: {sale_data.sale_id} - {sale_data.partner_name}")

        results = {
            "event_type": "sale_confirmed",
            "sale_id": sale_data.sale_id,
            "timestamp": datetime.now().isoformat(),
            "actions": {}
        }

        # 1. Thank-you WhatsApp
        if sale_data.partner_phone:
            msg = self._generate_sale_whatsapp(sale_data)
            results["actions"]["whatsapp"] = self.whatsapp.send_message(sale_data.partner_phone, msg)
        else:
            results["actions"]["whatsapp"] = {"status": "skipped", "reason": "No phone"}

        # 2. LinkedIn success story
        if post_linkedin:
            content = self._generate_sale_linkedin(sale_data)
            results["actions"]["linkedin"] = self.linkedin.post(
                content, ["ClientSuccess", "BusinessGrowth", "Partnership"]
            )
        else:
            results["actions"]["linkedin"] = {"status": "skipped", "reason": "post_linkedin=False"}

        self._log_event("sale_confirmed", sale_data.sale_id, results)
        return results

    def process_invoice_created(self, invoice_data: InvoiceData) -> Dict[str, Any]:
        """Process invoice_created: Email + WhatsApp reminder (high-value)"""
        logger.info(f"Processing new invoice: {invoice_data.invoice_id} - {invoice_data.partner_name}")

        results = {
            "event_type": "invoice_created",
            "invoice_id": invoice_data.invoice_id,
            "timestamp": datetime.now().isoformat(),
            "actions": {}
        }

        # 1. Email notification
        if invoice_data.partner_email:
            subject, body = self._generate_invoice_email(invoice_data)
            results["actions"]["email"] = self.gmail.send_email(
                invoice_data.partner_email, subject, body
            )
        else:
            results["actions"]["email"] = {"status": "skipped", "reason": "No email"}

        # 2. WhatsApp reminder for high-value invoices
        if invoice_data.partner_phone and invoice_data.total_amount >= 1000:
            msg = self._generate_invoice_whatsapp(invoice_data)
            results["actions"]["whatsapp_reminder"] = self.whatsapp.send_message(
                invoice_data.partner_phone, msg
            )
        else:
            results["actions"]["whatsapp_reminder"] = {
                "status": "skipped",
                "reason": "No phone or amount < $1000"
            }

        self._log_event("invoice_created", invoice_data.invoice_id, results)
        return results

    # Message generators
    def _generate_lead_whatsapp(self, lead: LeadData) -> str:
        return f"""Hello {lead.contact_name}! 👋

Thank you for your interest in {lead.company_name or 'our services'}.

We've received your inquiry about {lead.opportunity_type or 'our products/services'} and will be in touch shortly.

Best regards,
{lead.company_name or 'Our Team'}"""

    def _generate_lead_email(self, lead: LeadData) -> Tuple[str, str]:
        subject = f"Welcome {lead.contact_name} - Thank you for your interest!"
        body = f"""Dear {lead.contact_name},

Thank you for reaching out! We're excited to learn more about your needs.

LEAD DETAILS:
• Inquiry: {lead.opportunity_type or 'General'}
• Priority: {lead.priority or 'Normal'}
• Expected Revenue: {lead.expected_revenue or 'TBD'}

NEXT STEPS:
1. Review your requirements
2. Schedule a call
3. Send customized proposal

Response within 24 hours.

Best regards,
The Team at {lead.company_name or 'Our Company'}

Reference: Lead #{lead.lead_id}"""
        return subject, body

    def _generate_lead_linkedin(self, lead: LeadData) -> str:
        return f"""🤝 New Partnership Opportunity

Excited to connect with {lead.partner_name or lead.contact_name} from {lead.company_name or 'an innovative company'}.

#NewClient #BusinessGrowth #Partnership"""

    def _generate_sale_whatsapp(self, sale: SaleData) -> str:
        return f"""🎉 Thank you for your order, {sale.partner_name}!

Order #{sale.order_name} confirmed.

SUMMARY:
• Total: {sale.currency} {sale.total_amount:,.2f}
• Expected: {sale.expected_date or 'TBD'}

Detailed confirmation email coming shortly.

Thank you! 🙏"""

    def _generate_sale_linkedin(self, sale: SaleData) -> str:
        return f"""🎉 New Partnership Announced!

Thrilled to partner with {sale.partner_name or sale.company_name}!

Looking forward to achieving great results together. 🚀

#ClientSuccess #BusinessGrowth #Partnership"""

    def _generate_invoice_email(self, invoice: InvoiceData) -> Tuple[str, str]:
        subject = f"Invoice {invoice.invoice_number} from {invoice.company_name}"
        body = f"""Dear {invoice.partner_name},

Thank you for your business!

INVOICE DETAILS:
• Invoice: {invoice.invoice_number}
• Date: {invoice.invoice_date}
• Due: {invoice.due_date}
• Total: {invoice.currency} {invoice.total_amount:,.2f}
• Due: {invoice.currency} {invoice.amount_due:,.2f}
• Status: {invoice.payment_state}

Please arrange payment by the due date.

Best regards,
Accounts - {invoice.company_name}

Reference: {invoice.odoo_url}"""
        return subject, body

    def _generate_invoice_whatsapp(self, invoice: InvoiceData) -> str:
        return f"""📄 Invoice Reminder

Dear {invoice.partner_name},

Reminder: Invoice {invoice.invoice_number}
Amount: {invoice.currency} {invoice.total_amount:,.2f}
Due: {invoice.due_date}

Thank you!"""

    def _log_event(self, event_type: str, record_id: str, results: Dict[str, Any]):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.logs_dir / f"{event_type}_{record_id}_{timestamp}.json"

        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump({
                "event_type": event_type,
                "record_id": record_id,
                "timestamp": datetime.now().isoformat(),
                "results": results
            }, f, indent=2, default=str)


# ===========================================
# Flask Application
# ===========================================

def create_app() -> Flask:
    app = Flask(__name__)
    processor = OdooEventProcessor()

    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({
            "status": "healthy",
            "service": "odoo_webhook_standalone",
            "version": "2.0.0",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "gmail": "enabled" if GMAIL_DIRECT_ENABLED or SMTP_ENABLED else "disabled",
                "whatsapp": "enabled" if WHATSAPP_DIRECT_ENABLED else "disabled",
                "linkedin": "enabled" if LINKEDIN_DIRECT_ENABLED else "disabled"
            }
        })

    @app.route('/odoo_webhook', methods=['POST'])
    def odoo_webhook():
        try:
            if not request.is_json:
                return jsonify({"status": "error", "error": "Content-Type must be application/json"}), 400

            payload = request.get_json()
            received_secret = payload.get('secret', '')

            if not hmac.compare_digest(received_secret, WEBHOOK_SECRET):
                logger.warning("Invalid webhook secret")
                return jsonify({"status": "error", "error": "Invalid webhook secret"}), 401

            event_type = payload.get('event_type')
            if not event_type:
                return jsonify({"status": "error", "error": "Missing event_type"}), 400

            logger.info(f"Received Odoo event: {event_type}")

            if event_type == 'new_lead':
                result = handle_new_lead(payload.get('data', {}), processor)
            elif event_type == 'sale_confirmed':
                result = handle_sale_confirmed(payload.get('data', {}), processor)
            elif event_type == 'invoice_created':
                result = handle_invoice_created(payload.get('data', {}), processor)
            else:
                return jsonify({"status": "error", "error": f"Unknown event_type: {event_type}"}), 400

            return jsonify(result)

        except json.JSONDecodeError:
            return jsonify({"status": "error", "error": "Invalid JSON"}), 400
        except Exception as e:
            logger.error(f"Webhook error: {str(e)}", exc_info=True)
            return jsonify({"status": "error", "error": str(e)}), 500

    def handle_new_lead(data, processor):
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
            logger.error(f"Error in new_lead: {str(e)}", exc_info=True)
            return {"status": "error", "error": str(e)}

    def handle_sale_confirmed(data, processor):
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
            post_linkedin = data.get('post_linkedin', True)
            result = processor.process_sale_confirmed(sale, post_linkedin)
            result["status"] = "success"
            return result
        except Exception as e:
            logger.error(f"Error in sale_confirmed: {str(e)}", exc_info=True)
            return {"status": "error", "error": str(e)}

    def handle_invoice_created(data, processor):
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
            logger.error(f"Error in invoice_created: {str(e)}", exc_info=True)
            return {"status": "error", "error": str(e)}

    @app.route('/api/status', methods=['GET'])
    def api_status():
        return jsonify({
            "service": "odoo_webhook_standalone",
            "version": "2.0.0",
            "endpoints": ["/health", "/odoo_webhook", "/api/status"],
            "supported_events": ["new_lead", "sale_confirmed", "invoice_created"],
            "services": {
                "gmail": "enabled" if GMAIL_DIRECT_ENABLED or SMTP_ENABLED else "disabled",
                "whatsapp": "enabled" if WHATSAPP_DIRECT_ENABLED else "disabled",
                "linkedin": "enabled" if LINKEDIN_DIRECT_ENABLED else "disabled"
            },
            "timestamp": datetime.now().isoformat()
        })

    return app


# ===========================================
# Main
# ===========================================

def main():
    app = create_app()

    print("""
╔═══════════════════════════════════════════════════════════╗
║  🔄 ODOO WEBHOOK HANDLER - STANDALONE (DIRECT API)       ║
║                                                           ║
║  Version: 2.0.0-Standalone                                ║
║  Port: {}                                                 ║
║                                                           ║
║  Services:                                                ║
║  • Gmail: {}                                              ║
║  • WhatsApp: {}                                           ║
║  • LinkedIn: {}                                           ║
║                                                           ║
║  Endpoints:                                               ║
║  • GET  /health                                           ║
║  • POST /odoo_webhook                                     ║
║  • GET  /api/status                                       ║
╚═══════════════════════════════════════════════════════════╝
    """.format(
        WEBHOOK_PORT,
        "✅ Enabled" if GMAIL_DIRECT_ENABLED or SMTP_ENABLED else "❌ Disabled",
        "✅ Enabled" if WHATSAPP_DIRECT_ENABLED else "❌ Disabled",
        "✅ Enabled" if LINKEDIN_DIRECT_ENABLED else "❌ Disabled"
    ))

    logger.info(f"Starting Standalone Odoo Webhook Handler on port {WEBHOOK_PORT}")

    app.run(host='0.0.0.0', port=WEBHOOK_PORT, debug=False, threaded=True)


if __name__ == "__main__":
    main()
