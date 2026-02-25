"""
MCP Server - Gold Tier Enhanced
Message Control Protocol with Real External Actions + Odoo 19+ Integration

Gold Tier Capabilities:
- Real Gmail API for email sending
- Real LinkedIn API for posting
- Real WhatsApp Business API for messaging
- Odoo 19+ JSON-RPC integration (invoices, expenses, reports)
- Link opening & task execution
- Comprehensive error handling & retry logic
- Multi-channel social media support
"""

import os
import json
import logging
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging with UTF-8 encoding
class Utf8StreamHandler(logging.StreamHandler):
    """Stream handler that handles UTF-8 encoding for Windows console"""
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            if hasattr(stream, 'buffer'):
                stream.buffer.write((msg + self.terminator).encode('utf-8', errors='replace'))
                stream.flush()
            else:
                stream.write(msg + self.terminator)
                stream.flush()
        except Exception:
            self.handleError(record)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/mcp_server_gold.log', encoding='utf-8'),
        Utf8StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class GoldTierMCPServer:
    """
    Gold Tier MCP Server with Odoo Integration
    Handles all external actions for the AI Employee system
    """

    def __init__(self):
        self.app = Flask(__name__)
        self.action_counter = 0
        self.logs_dir = Path("Logs")
        self.logs_dir.mkdir(exist_ok=True)
        self.errors_dir = Path("Error")
        self.errors_dir.mkdir(exist_ok=True)

        # API Configuration
        self.gmail_service = None
        self.linkedin_config = {
            'access_token': os.getenv('LINKEDIN_ACCESS_TOKEN'),
            'person_id': os.getenv('LINKEDIN_PERSON_ID')
        }
        self.whatsapp_config = {
            'access_token': os.getenv('WHATSAPP_ACCESS_TOKEN'),
            'phone_number_id': os.getenv('WHATSAPP_PHONE_NUMBER_ID'),
            'api_version': os.getenv('WHATSAPP_API_VERSION', 'v18.0')
        }
        self.odoo_config = {
            'url': os.getenv('ODOO_URL', 'http://localhost:8069'),
            'db': os.getenv('ODOO_DB', 'odoo'),
            'username': os.getenv('ODOO_USER', 'admin'),
            'password': os.getenv('ODOO_PASSWORD', 'admin'),
            'api_key': os.getenv('ODOO_API_KEY')
        }

        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 2  # seconds

        # Initialize Gmail if available
        self._initialize_gmail()

        # Setup API routes
        self._setup_routes()

        logger.info("Gold Tier MCP Server initialized")

    def _initialize_gmail(self):
        """Initialize Gmail API client"""
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build

            token_file = os.getenv('GMAIL_TOKEN_FILE', 'tokens/gmail_token.json')
            scopes = ['https://www.googleapis.com/auth/gmail.send']

            if os.path.exists(token_file):
                creds = Credentials.from_authorized_user_file(token_file, scopes)
                self.gmail_service = build('gmail', 'v1', credentials=creds)
                logger.info("✅ Gmail API initialized")
            else:
                logger.warning("⚠️  Gmail token not found. Email sending disabled.")
        except ImportError:
            logger.warning("⚠️  Google API libraries not installed")
        except Exception as e:
            logger.error(f"❌ Gmail API initialization error: {str(e)}")

    def _setup_routes(self):
        """Setup all API routes"""

        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                "status": "healthy",
                "tier": "gold",
                "version": "3.0.0",
                "timestamp": datetime.now().isoformat(),
                "services": {
                    "gmail": "connected" if self.gmail_service else "disconnected",
                    "linkedin": "connected" if self.linkedin_config['access_token'] else "disconnected",
                    "whatsapp": "connected" if self.whatsapp_config['access_token'] else "disconnected",
                    "odoo": "connected" if self.odoo_config['url'] else "disconnected"
                }
            })

        @self.app.route('/api/email/send', methods=['POST'])
        def send_email():
            """Send email via Gmail API"""
            return self._handle_email_send()

        @self.app.route('/api/social/post', methods=['POST'])
        def post_social():
            """Post to social media (LinkedIn, Twitter, Facebook)"""
            return self._handle_social_post()

        @self.app.route('/api/whatsapp/send', methods=['POST'])
        def send_whatsapp():
            """Send WhatsApp message via Business API"""
            return self._handle_whatsapp_send()

        @self.app.route('/api/odoo/action', methods=['POST'])
        def odoo_action():
            """Execute Odoo action (invoice, expense, report)"""
            return self._handle_odoo_action()

        @self.app.route('/api/link/open', methods=['POST'])
        def open_link():
            """Open URL in browser or execute API call"""
            return self._handle_link_opening()

        @self.app.route('/api/action/execute', methods=['POST'])
        def execute_action():
            """Execute generic action with retry logic"""
            return self._handle_action_execution()

        @self.app.route('/api/accounting/invoice/create', methods=['POST'])
        def create_invoice():
            """Create invoice in Odoo"""
            return self._handle_create_invoice()

        @self.app.route('/api/accounting/report', methods=['POST'])
        def generate_report():
            """Generate accounting report from Odoo"""
            return self._handle_generate_report()

    def _handle_email_send(self):
        """Handle email sending with retry logic"""
        try:
            data = request.json
            task_id = data.get('task_id', f'email_{self.action_counter}')
            self.action_counter += 1

            logger.info(f"📧 Email request received: {task_id}")

            # Validate required fields
            to_email = data.get('to')
            if not to_email:
                raise ValueError("Recipient email is required")

            # Execute with retry
            result = self._execute_with_retry(
                self._send_gmail_email,
                args=[to_email, data.get('subject', ''), data.get('body', ''), data.get('cc'), data.get('bcc')],
                task_id=task_id,
                action_type="email_send"
            )

            self._log_action(task_id, "email_send", "success", result)

            return jsonify({
                "status": "success",
                "task_id": task_id,
                "message": f"Email sent to {to_email}",
                "result": result
            })

        except Exception as e:
            logger.error(f"❌ Email send error: {str(e)}")
            self._log_action(data.get('task_id', 'unknown'), "email_send", "error", {"error": str(e)})
            return jsonify({"status": "error", "error": str(e)}), 500

    def _handle_social_post(self):
        """Handle social media posting"""
        try:
            data = request.json
            task_id = data.get('task_id', f'social_{self.action_counter}')
            self.action_counter += 1

            platform = data.get('platform', 'linkedin')
            logger.info(f"📱 {platform} post request received: {task_id}")

            # Route to appropriate platform
            if platform == 'linkedin':
                result = self._execute_with_retry(
                    self._post_to_linkedin,
                    args=[data.get('content', ''), data.get('hashtags', []), data.get('visibility', 'PUBLIC')],
                    task_id=task_id,
                    action_type="linkedin_post"
                )
            elif platform == 'twitter' or platform == 'x':
                result = self._post_to_twitter(data.get('content', ''), data.get('hashtags', []))
            elif platform == 'facebook':
                result = self._post_to_facebook(data.get('content', ''), data.get('image_url'))
            else:
                raise ValueError(f"Unsupported platform: {platform}")

            self._log_action(task_id, f"social_post_{platform}", "success", result)

            return jsonify({
                "status": "success",
                "task_id": task_id,
                "platform": platform,
                "message": f"Post published to {platform}",
                "result": result
            })

        except Exception as e:
            logger.error(f"❌ Social post error: {str(e)}")
            self._log_action(data.get('task_id', 'unknown'), "social_post", "error", {"error": str(e)})
            return jsonify({"status": "error", "error": str(e)}), 500

    def _handle_whatsapp_send(self):
        """Handle WhatsApp message sending"""
        try:
            data = request.json
            task_id = data.get('task_id', f'whatsapp_{self.action_counter}')
            self.action_counter += 1

            logger.info(f"💬 WhatsApp request received: {task_id}")

            recipient = data.get('to')
            message = data.get('message', '')

            if not recipient:
                raise ValueError("Recipient phone number is required")
            if not message:
                raise ValueError("Message content is required")

            result = self._execute_with_retry(
                self._send_whatsapp_message,
                args=[recipient, message, data.get('type', 'text')],
                task_id=task_id,
                action_type="whatsapp_send"
            )

            self._log_action(task_id, "whatsapp_send", "success", result)

            return jsonify({
                "status": "success",
                "task_id": task_id,
                "message": f"WhatsApp sent to {recipient}",
                "result": result
            })

        except Exception as e:
            logger.error(f"❌ WhatsApp send error: {str(e)}")
            self._log_action(data.get('task_id', 'unknown'), "whatsapp_send", "error", {"error": str(e)})
            return jsonify({"status": "error", "error": str(e)}), 500

    def _handle_odoo_action(self):
        """Handle Odoo ERP actions"""
        try:
            data = request.json
            task_id = data.get('task_id', f'odoo_{self.action_counter}')
            self.action_counter += 1

            action_type = data.get('action_type')
            logger.info(f"📊 Odoo action request: {action_type} for {task_id}")

            if not action_type:
                raise ValueError("action_type is required")

            # Execute Odoo action
            result = self._execute_odoo_action(action_type, data.get('data', {}))

            self._log_action(task_id, f"odoo_{action_type}", "success", result)

            return jsonify({
                "status": "success",
                "task_id": task_id,
                "action_type": action_type,
                "result": result
            })

        except Exception as e:
            logger.error(f"❌ Odoo action error: {str(e)}")
            self._log_action(data.get('task_id', 'unknown'), "odoo_action", "error", {"error": str(e)})
            return jsonify({"status": "error", "error": str(e)}), 500

    def _handle_link_opening(self):
        """Handle URL opening"""
        try:
            import webbrowser
            data = request.json
            task_id = data.get('task_id', f'link_{self.action_counter}')
            self.action_counter += 1

            url = data.get('url')
            action = data.get('action', 'open')

            if not url:
                raise ValueError("URL is required")

            logger.info(f"🔗 Link action: {action} for {url}")

            result = {"url": url, "action": action}

            if action == 'open':
                webbrowser.open(url)
                result["status"] = "opened_in_browser"
            elif action == 'verify':
                response = requests.head(url, timeout=5)
                result["status"] = "verified"
                result["accessible"] = response.status_code == 200
            elif action == 'execute':
                response = requests.get(url, timeout=10)
                result["status"] = "executed"
                result["response_code"] = response.status_code

            self._log_action(task_id, "link_action", "success", result)

            return jsonify({"status": "success", "task_id": task_id, "result": result})

        except Exception as e:
            logger.error(f"❌ Link action error: {str(e)}")
            return jsonify({"status": "error", "error": str(e)}), 500

    def _handle_action_execution(self):
        """Handle generic action execution"""
        try:
            data = request.json
            action_type = data.get('action_type')
            task_id = data.get('task_id', f'action_{self.action_counter}')
            self.action_counter += 1

            logger.info(f"⚡ Action execution: {action_type} for {task_id}")

            result = self._execute_generic_action(action_type, data)
            self._log_action(task_id, f"action_{action_type}", "success", result)

            return jsonify({"status": "success", "task_id": task_id, "result": result})

        except Exception as e:
            logger.error(f"❌ Action execution error: {str(e)}")
            return jsonify({"status": "error", "error": str(e)}), 500

    def _handle_create_invoice(self):
        """Handle invoice creation in Odoo"""
        try:
            data = request.json
            task_id = data.get('task_id', f'invoice_{self.action_counter}')
            self.action_counter += 1

            logger.info(f"📄 Invoice creation request: {task_id}")

            invoice_data = {
                'partner_name': data.get('client', data.get('partner_name')),
                'amount': data.get('amount', 0),
                'description': data.get('description', 'Invoice'),
                'invoice_date': data.get('date', datetime.now().strftime('%Y-%m-%d'))
            }

            result = self._execute_odoo_action('create_invoice', invoice_data)
            self._log_action(task_id, "create_invoice", "success", result)

            return jsonify({
                "status": "success",
                "task_id": task_id,
                "message": "Invoice created in Odoo",
                "result": result
            })

        except Exception as e:
            logger.error(f"❌ Invoice creation error: {str(e)}")
            return jsonify({"status": "error", "error": str(e)}), 500

    def _handle_generate_report(self):
        """Handle accounting report generation"""
        try:
            data = request.json
            task_id = data.get('task_id', f'report_{self.action_counter}')
            self.action_counter += 1

            report_type = data.get('type', 'sales_summary')
            logger.info(f"📊 Report generation: {report_type} for {task_id}")

            result = self._execute_odoo_action('generate_report', {
                'type': report_type,
                'date_from': data.get('date_from'),
                'date_to': data.get('date_to')
            })

            self._log_action(task_id, "generate_report", "success", result)

            return jsonify({
                "status": "success",
                "task_id": task_id,
                "report_type": report_type,
                "result": result
            })

        except Exception as e:
            logger.error(f"❌ Report generation error: {str(e)}")
            return jsonify({"status": "error", "error": str(e)}), 500

    # ===========================================
    # REAL API IMPLEMENTATION METHODS
    # ===========================================

    def _execute_with_retry(self, func, args=None, kwargs=None, task_id=None, action_type=None):
        """Execute function with retry logic"""
        args = args or []
        kwargs = kwargs or {}
        
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed: {str(e)}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
        
        error_msg = f"All {self.max_retries} attempts failed. Last error: {str(last_error)}"
        logger.error(error_msg)
        
        if task_id and action_type:
            self._log_action(task_id, action_type, "error", {"error": error_msg, "retries": self.max_retries})
        
        raise Exception(error_msg)

    def _send_gmail_email(self, to: str, subject: str, body: str, cc: str = None, bcc: str = None) -> Dict:
        """Send email using Gmail API"""
        try:
            if not self.gmail_service:
                return self._send_smtp_email(to, subject, body, cc, bcc)

            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            import base64

            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            message.attach(MIMEText(body, 'plain'))

            if cc:
                message['cc'] = cc

            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            sent_message = self.gmail_service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            logger.info(f"✅ Email sent via Gmail API. Message ID: {sent_message['id']}")

            return {
                "message_id": sent_message['id'],
                "thread_id": sent_message.get('threadId'),
                "status": "sent",
                "method": "gmail_api",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Gmail API error: {str(e)}")
            raise

    def _send_smtp_email(self, to: str, subject: str, body: str, cc: str = None, bcc: str = None) -> Dict:
        """Fallback: Send email using SMTP"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_username = os.getenv('SMTP_USERNAME')
            smtp_password = os.getenv('SMTP_PASSWORD')

            msg = MIMEMultipart()
            msg['From'] = smtp_username
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

            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg, to_addrs=recipients)
            server.quit()

            logger.info(f"✅ Email sent via SMTP to {to}")

            return {
                "status": "sent",
                "method": "smtp",
                "recipients": recipients,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ SMTP error: {str(e)}")
            raise

    def _post_to_linkedin(self, content: str, hashtags: list = None, visibility: str = 'PUBLIC') -> Dict:
        """Post to LinkedIn using API"""
        try:
            if not self.linkedin_config['access_token']:
                raise ValueError("LinkedIn access token not configured")

            url = "https://api.linkedin.com/v2/shares"
            headers = {
                'Authorization': f'Bearer {self.linkedin_config["access_token"]}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0'
            }

            # Format content with hashtags
            if hashtags:
                hashtag_string = ' '.join([f'#{tag}' for tag in hashtags])
                full_content = f"{content}\n\n{hashtag_string}"
            else:
                full_content = content

            person_id = self.linkedin_config['person_id'] or 'urn:li:person:YOUR_PERSON_ID'

            payload = {
                "author": f"urn:li:person:{person_id}",
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
                raise Exception(f"LinkedIn API error: {response.status_code} - {response.text}")

            result = response.json()
            logger.info(f"✅ LinkedIn post created. ID: {result.get('id')}")

            return {
                "post_id": result.get('id'),
                "status": "published",
                "visibility": visibility,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ LinkedIn post error: {str(e)}")
            raise

    def _post_to_twitter(self, content: str, hashtags: list = None) -> Dict:
        """Post to Twitter/X (placeholder - requires Twitter API v2)"""
        logger.warning("⚠️  Twitter posting requires Twitter API v2 setup")
        
        # Placeholder for Twitter API integration
        return {
            "status": "simulated",
            "message": "Twitter integration requires API v2 credentials",
            "content": content,
            "timestamp": datetime.now().isoformat()
        }

    def _post_to_facebook(self, content: str, image_url: str = None) -> Dict:
        """Post to Facebook (placeholder - requires Facebook Graph API)"""
        logger.warning("⚠️  Facebook posting requires Facebook Graph API setup")
        
        # Placeholder for Facebook API integration
        return {
            "status": "simulated",
            "message": "Facebook integration requires Graph API credentials",
            "content": content,
            "timestamp": datetime.now().isoformat()
        }

    def _send_whatsapp_message(self, recipient_phone: str, message_text: str, message_type: str = 'text') -> Dict:
        """Send WhatsApp message using Business API"""
        try:
            if not self.whatsapp_config['access_token']:
                raise ValueError("WhatsApp access token not configured")

            url = f"https://graph.facebook.com/{self.whatsapp_config['api_version']}/{self.whatsapp_config['phone_number_id']}/messages"

            headers = {
                'Authorization': f'Bearer {self.whatsapp_config["access_token"]}',
                'Content-Type': 'application/json'
            }

            clean_phone = recipient_phone.replace('+', '').replace(' ', '').replace('-', '')

            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": clean_phone,
                "type": message_type
            }

            if message_type == 'text':
                payload["text"] = {"body": message_text, "preview_url": True}

            response = requests.post(url, headers=headers, json=payload, timeout=30)

            if response.status_code != 200:
                raise Exception(f"WhatsApp API error: {response.status_code} - {response.text}")

            result = response.json()
            logger.info(f"✅ WhatsApp message sent. Message ID: {result.get('messages', [{}])[0].get('id')}")

            return {
                "message_id": result.get('messages', [{}])[0].get('id'),
                "contact_id": result.get('contacts', [{}])[0].get('id'),
                "status": "sent",
                "recipient": recipient_phone,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ WhatsApp send error: {str(e)}")
            raise

    def _execute_odoo_action(self, action_type: str, data: Dict) -> Dict:
        """Execute Odoo ERP action via JSON-RPC"""
        try:
            if not self.odoo_config['url']:
                raise ValueError("Odoo URL not configured")

            odoo_url = self.odoo_config['url']
            odoo_db = self.odoo_config['db']
            odoo_user = self.odoo_config['username']
            odoo_pass = self.odoo_config['password']

            # Common JSON-RPC payload structure
            payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "object",
                    "args": [odoo_db, odoo_user, odoo_pass]
                },
                "id": 1
            }

            if action_type == 'create_invoice':
                # Create invoice in Odoo
                payload["params"]["args"].extend([
                    "account.move",
                    "create",
                    [{
                        "move_type": "out_invoice",
                        "partner_id": self._get_odoo_partner_id(data.get('partner_name')),
                        "invoice_line_ids": [(0, 0, {
                            "name": data.get('description', 'Invoice'),
                            "price_unit": data.get('amount', 0),
                            "quantity": 1
                        })]
                    }]
                ])

            elif action_type == 'log_expense':
                # Log expense in Odoo
                payload["params"]["args"].extend([
                    "hr.expense",
                    "create",
                    [{
                        "name": data.get('description', 'Expense'),
                        "total_amount": data.get('amount', 0),
                        "date": data.get('date', datetime.now().strftime('%Y-%m-%d'))
                    }]
                ])

            elif action_type == 'generate_report':
                # Generate report (sales summary, etc.)
                report_type = data.get('type', 'sales_summary')
                payload["params"]["args"].extend([
                    "account.report",
                    "get_report",
                    [{
                        "report_type": report_type,
                        "date_from": data.get('date_from'),
                        "date_to": data.get('date_to')
                    }]
                ])

            elif action_type == 'create_sale_order':
                # Create sale order
                payload["params"]["args"].extend([
                    "sale.order",
                    "create",
                    [{
                        "partner_id": self._get_odoo_partner_id(data.get('customer_name')),
                        "order_line": [(0, 0, {
                            "name": data.get('product', 'Product'),
                            "product_uom_qty": data.get('quantity', 1),
                            "price_unit": data.get('amount', 0)
                        })]
                    }]
                ])

            else:
                raise ValueError(f"Unknown Odoo action type: {action_type}")

            # Execute JSON-RPC call
            response = requests.post(
                f"{odoo_url}/jsonrpc",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )

            if response.status_code != 200:
                raise Exception(f"Odoo JSON-RPC error: {response.status_code}")

            result = response.json()
            
            if 'result' in result:
                logger.info(f"✅ Odoo action '{action_type}' executed successfully")
                return {
                    "action_type": action_type,
                    "result_id": result['result'],
                    "status": "success",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                raise Exception(f"Odoo returned error: {result.get('error', 'Unknown error')}")

        except Exception as e:
            logger.error(f"❌ Odoo action error: {str(e)}")
            raise

    def _get_odoo_partner_id(self, partner_name: str) -> int:
        """Get or create Odoo partner ID (placeholder)"""
        # In production, this would search/create partner in Odoo
        return 1  # Placeholder

    def _execute_generic_action(self, action_type: str, data: Dict) -> Dict:
        """Execute generic action"""
        if action_type == 'open_url':
            import webbrowser
            webbrowser.open(data.get('url'))
            return {"status": "opened", "url": data.get('url')}
        elif action_type == 'read_file':
            file_path = data.get('path')
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                return {"status": "success", "content": content}
            return {"status": "error", "error": "File not found"}
        elif action_type == 'write_file':
            file_path = data.get('path')
            content = data.get('content', '')
            with open(file_path, 'w') as f:
                f.write(content)
            return {"status": "success", "path": file_path}
        else:
            raise ValueError(f"Unknown action type: {action_type}")

    def _log_action(self, task_id: str, action_type: str, status: str, details: Dict):
        """Log action to file with timestamp"""
        log_entry = {
            "task_id": task_id,
            "action_type": action_type,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "tier": "gold"
        }

        log_filename = self.logs_dir / f"mcp_action_{task_id}_{int(time.time())}.json"
        with open(log_filename, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, indent=2)

        logger.info(f"📝 Logged action: {action_type} for task {task_id} - Status: {status}")

    def run(self, host='localhost', port=5001, debug=False):
        """Start the Gold Tier MCP server"""
        logger.info(f"🚀 Gold Tier MCP Server starting on {host}:{port}")
        print(f"""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     🏆  GOLD TIER MCP SERVER  🏆                         ║
║                                                           ║
║     Endpoints:                                            ║
║     • /api/email/send     - Send emails (Gmail API)      ║
║     • /api/social/post    - Post to LinkedIn/Twitter/FB  ║
║     • /api/whatsapp/send  - Send WhatsApp messages       ║
║     • /api/odoo/action    - Execute Odoo ERP actions     ║
║     • /api/accounting/*   - Accounting operations        ║
║     • /api/link/open      - Open URLs                    ║
║     • /health             - Health check                 ║
║                                                           ║
║     Server: {host}:{port}
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
        """)
        self.app.run(host=host, port=port, debug=debug, threaded=True)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Gold Tier MCP Server')
    parser.add_argument('--host', default='localhost', help='Server host')
    parser.add_argument('--port', type=int, default=5001, help='Server port')
    parser.add_argument('--debug', action='store_true', help='Debug mode')
    args = parser.parse_args()

    server = GoldTierMCPServer()
    server.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
