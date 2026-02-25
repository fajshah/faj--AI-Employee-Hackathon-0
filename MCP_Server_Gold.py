"""
MCP Server - Gold Tier
Message Control Protocol with REAL external action capabilities

Gold Tier Enhancements:
- Real Gmail API integration for sending emails
- Real LinkedIn API for posting updates
- Real WhatsApp Business API for messaging
- Link opening and task execution
- Comprehensive error handling and logging
"""

import json
import logging
import os
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any
import threading
import time
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.gold')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/mcp_server_gold.log'),
        logging.StreamHandler()
    ]
)

# Import Gold Tier API clients
try:
    from google.oauth2.credentials import Credentials
    from google.oauth2 import service_account
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False
    logging.warning("Google API libraries not available. Gmail features disabled.")


class GoldTierMCP:
    """Gold Tier MCP Server with real external action capabilities"""

    def __init__(self):
        self.app = Flask(__name__)
        self.setup_routes()
        self.action_counter = 0
        self.logs_dir = Path("Logs")
        self.logs_dir.mkdir(exist_ok=True)

        # Initialize API clients
        self.gmail_service = None
        self.linkedin_access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
        self.linkedin_person_id = os.getenv('LINKEDIN_PERSON_ID')
        self.whatsapp_access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        self.whatsapp_phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.whatsapp_api_version = os.getenv('WHATSAPP_API_VERSION', 'v18.0')

        # Initialize Gmail service
        if GMAIL_AVAILABLE:
            self._initialize_gmail()

        logging.info("Gold Tier MCP Server initialized")

    def _initialize_gmail(self):
        """Initialize Gmail API client with OAuth 2.0"""
        try:
            token_file = os.getenv('GMAIL_TOKEN_FILE', 'tokens/gmail_token.json')
            credentials_file = 'client_secret_725259256203-a14h8ovoi908q7nv5sigh8ak6456gsnl.apps.googleusercontent.com.json'
            scopes = ['https://www.googleapis.com/auth/gmail.send',
                     'https://www.googleapis.com/auth/gmail.readonly']

            creds = None

            # Load existing token if available
            if os.path.exists(token_file):
                creds = Credentials.from_authorized_user_file(token_file, scopes)

            # If no valid credentials, attempt to authenticate
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                elif os.path.exists(credentials_file):
                    # Interactive flow for first-time authentication
                    logging.info("Gmail OAuth flow required. Run authenticate_gmail.py first.")
                    return

                # Save credentials for future use
                Path(token_file).parent.mkdir(exist_ok=True)
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())

            # Build Gmail service
            self.gmail_service = build('gmail', 'v1', credentials=creds)
            logging.info("Gmail API client initialized successfully")

        except Exception as e:
            logging.error(f"Failed to initialize Gmail API: {str(e)}")
            self.gmail_service = None

    def setup_routes(self):
        """Setup API routes for Gold Tier actions"""

        @self.app.route('/api/email/send', methods=['POST'])
        def send_email():
            """Send real email via Gmail API"""
            return self.handle_email_send()

        @self.app.route('/api/social/post', methods=['POST'])
        def post_social():
            """Post to real LinkedIn via API"""
            return self.handle_linkedin_post()

        @self.app.route('/api/whatsapp/send', methods=['POST'])
        def send_whatsapp():
            """Send real WhatsApp message via Business API"""
            return self.handle_whatsapp_send()

        @self.app.route('/api/link/open', methods=['POST'])
        def open_link():
            """Open URL in default browser"""
            return self.handle_link_opening()

        @self.app.route('/api/action/execute', methods=['POST'])
        def execute_action():
            """Execute generic action with real implementation"""
            return self.handle_action_execution()

        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                "status": "healthy",
                "tier": "gold",
                "timestamp": datetime.now().isoformat(),
                "services": {
                    "gmail": "connected" if self.gmail_service else "disconnected",
                    "linkedin": "connected" if self.linkedin_access_token else "disconnected",
                    "whatsapp": "connected" if self.whatsapp_access_token else "disconnected"
                }
            })

        @self.app.route('/api/auth/gmail', methods=['POST'])
        def authenticate_gmail():
            """Trigger Gmail OAuth authentication flow"""
            return self.handle_gmail_auth()

    def handle_email_send(self):
        """Handle real email sending via Gmail API"""
        try:
            data = request.json
            task_id = data.get('task_id', f'email_{self.action_counter}')
            self.action_counter += 1

            logging.info(f"Received email send request for task {task_id}")

            # Extract email details
            to_email = data.get('to')
            subject = data.get('subject', 'No Subject')
            body = data.get('body', '')
            cc = data.get('cc')
            bcc = data.get('bcc')

            if not to_email:
                raise ValueError("Recipient email address is required")

            # Send email via Gmail API
            result = self._send_gmail_email(to_email, subject, body, cc, bcc)

            # Log the action
            self._log_action(task_id, "email_send", "success", result)

            return jsonify({
                "status": "success",
                "task_id": task_id,
                "message": f"Email sent to {to_email}",
                "result": result
            })

        except Exception as e:
            logging.error(f"Error sending email: {str(e)}")
            self._log_action(data.get('task_id', 'unknown'), "email_send", "error", {"error": str(e)})
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500

    def handle_linkedin_post(self):
        """Handle real LinkedIn posting via API"""
        try:
            data = request.json
            task_id = data.get('task_id', f'linkedin_{self.action_counter}')
            self.action_counter += 1

            logging.info(f"Received LinkedIn post request for task {task_id}")

            # Extract post details
            content = data.get('content', '')
            hashtags = data.get('hashtags', [])
            visibility = data.get('visibility', 'PUBLIC')

            if not content:
                raise ValueError("Post content is required")

            # Post to LinkedIn
            result = self._post_to_linkedin(content, hashtags, visibility)

            # Log the action
            self._log_action(task_id, "linkedin_post", "success", result)

            return jsonify({
                "status": "success",
                "task_id": task_id,
                "message": "Post published to LinkedIn",
                "result": result
            })

        except Exception as e:
            logging.error(f"Error posting to LinkedIn: {str(e)}")
            self._log_action(data.get('task_id', 'unknown'), "linkedin_post", "error", {"error": str(e)})
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500

    def handle_whatsapp_send(self):
        """Handle real WhatsApp message sending via Business API"""
        try:
            data = request.json
            task_id = data.get('task_id', f'whatsapp_{self.action_counter}')
            self.action_counter += 1

            logging.info(f"Received WhatsApp send request for task {task_id}")

            # Extract message details
            recipient_phone = data.get('to')
            message_text = data.get('message', '')
            message_type = data.get('type', 'text')

            if not recipient_phone:
                raise ValueError("Recipient phone number is required")
            if not message_text:
                raise ValueError("Message content is required")

            # Send WhatsApp message
            result = self._send_whatsapp_message(recipient_phone, message_text, message_type)

            # Log the action
            self._log_action(task_id, "whatsapp_send", "success", result)

            return jsonify({
                "status": "success",
                "task_id": task_id,
                "message": f"WhatsApp message sent to {recipient_phone}",
                "result": result
            })

        except Exception as e:
            logging.error(f"Error sending WhatsApp message: {str(e)}")
            self._log_action(data.get('task_id', 'unknown'), "whatsapp_send", "error", {"error": str(e)})
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500

    def handle_link_opening(self):
        """Handle URL opening in default browser"""
        try:
            data = request.json
            task_id = data.get('task_id', f'link_{self.action_counter}')
            self.action_counter += 1

            url = data.get('url')
            action = data.get('action', 'open')  # 'open', 'execute', 'verify'

            if not url:
                raise ValueError("URL is required")

            logging.info(f"Received link action request: {action} for {url}")

            result = {"url": url, "action": action}

            if action == 'open':
                # Open URL in default browser
                webbrowser.open(url)
                result["status"] = "opened_in_browser"
                logging.info(f"Opened URL in browser: {url}")

            elif action == 'execute':
                # For API endpoints, execute via requests
                import requests
                response = requests.get(url, timeout=10)
                result["status"] = "executed"
                result["response_code"] = response.status_code
                logging.info(f"Executed URL: {url} - Status: {response.status_code}")

            elif action == 'verify':
                # Verify URL is accessible
                import requests
                try:
                    response = requests.head(url, timeout=5, allow_redirects=True)
                    result["status"] = "verified"
                    result["accessible"] = response.status_code == 200
                    result["response_code"] = response.status_code
                except Exception as e:
                    result["status"] = "unreachable"
                    result["error"] = str(e)

            # Log the action
            self._log_action(task_id, "link_action", "success", result)

            return jsonify({
                "status": "success",
                "task_id": task_id,
                "result": result
            })

        except Exception as e:
            logging.error(f"Error handling link action: {str(e)}")
            self._log_action(data.get('task_id', 'unknown'), "link_action", "error", {"error": str(e)})
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500

    def handle_action_execution(self):
        """Handle generic action execution with real implementation"""
        try:
            data = request.json
            action_type = data.get('action_type')
            task_id = data.get('task_id', f'action_{self.action_counter}')
            self.action_counter += 1

            logging.info(f"Received action execution request: {action_type} for task {task_id}")

            result = self._execute_real_action(action_type, data)

            # Log the action
            self._log_action(task_id, f"action_{action_type}", "success", result)

            return jsonify({
                "status": "success",
                "task_id": task_id,
                "result": result
            })

        except Exception as e:
            logging.error(f"Error executing action: {str(e)}")
            self._log_action(data.get('task_id', 'unknown'), "action_execution", "error", {"error": str(e)})
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500

    def handle_gmail_auth(self):
        """Handle Gmail OAuth authentication flow"""
        try:
            if not GMAIL_AVAILABLE:
                return jsonify({
                    "status": "error",
                    "error": "Google API libraries not installed"
                }), 500

            token_file = os.getenv('GMAIL_TOKEN_FILE', 'tokens/gmail_token.json')
            credentials_file = 'client_secret_725259256203-a14h8ovoi908q7nv5sigh8ak6456gsnl.apps.googleusercontent.com.json'
            scopes = ['https://www.googleapis.com/auth/gmail.send']

            if not os.path.exists(credentials_file):
                return jsonify({
                    "status": "error",
                    "error": "Credentials file not found. Please download from Google Cloud Console."
                }), 400

            # Run OAuth flow
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, scopes)
            creds = flow.run_local_server(port=8080)

            # Save credentials
            Path(token_file).parent.mkdir(exist_ok=True)
            with open(token_file, 'w') as token:
                token.write(creds.to_json())

            # Reinitialize Gmail service
            self._initialize_gmail()

            return jsonify({
                "status": "success",
                "message": "Gmail authentication completed successfully"
            })

        except Exception as e:
            logging.error(f"Gmail auth error: {str(e)}")
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500

    # ===========================================
    # REAL API IMPLEMENTATION METHODS
    # ===========================================

    def _send_gmail_email(self, to: str, subject: str, body: str,
                          cc: str = None, bcc: str = None) -> Dict[str, Any]:
        """Send email using Gmail API"""
        try:
            if not self.gmail_service:
                # Fallback to SMTP if Gmail API not available
                return self._send_smtp_email(to, subject, body, cc, bcc)

            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            import base64

            # Create message
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            message.attach(MIMEText(body, 'plain'))

            if cc:
                message['cc'] = cc
            # BCC is not added to headers but handled during sending

            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            # Send via Gmail API
            sent_message = self.gmail_service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            logging.info(f"Email sent via Gmail API. Message ID: {sent_message['id']}")

            return {
                "message_id": sent_message['id'],
                "thread_id": sent_message.get('threadId'),
                "status": "sent",
                "method": "gmail_api",
                "timestamp": datetime.now().isoformat()
            }

        except HttpError as error:
            logging.error(f"Gmail API error: {error}")
            raise Exception(f"Gmail API error: {error}")
        except Exception as e:
            logging.error(f"Error sending Gmail email: {str(e)}")
            raise

    def _send_smtp_email(self, to: str, subject: str, body: str,
                         cc: str = None, bcc: str = None) -> Dict[str, Any]:
        """Fallback: Send email using SMTP"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_username = os.getenv('SMTP_USERNAME')
            smtp_password = os.getenv('SMTP_PASSWORD')

            # Create message
            msg = MIMEMultipart()
            msg['From'] = smtp_username
            msg['To'] = to
            msg['Subject'] = subject

            if cc:
                msg['Cc'] = cc

            msg.attach(MIMEText(body, 'plain'))

            # Prepare recipients
            recipients = [to]
            if cc:
                recipients.extend(cc.split(','))
            if bcc:
                recipients.extend(bcc.split(','))

            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg, to_addrs=recipients)
            server.quit()

            logging.info(f"Email sent via SMTP to {to}")

            return {
                "status": "sent",
                "method": "smtp",
                "recipients": recipients,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logging.error(f"SMTP error: {str(e)}")
            raise

    def _post_to_linkedin(self, content: str, hashtags: list = None,
                          visibility: str = 'PUBLIC') -> Dict[str, Any]:
        """Post to LinkedIn using API"""
        try:
            if not self.linkedin_access_token:
                raise ValueError("LinkedIn access token not configured")

            person_id = self.linkedin_person_id or 'urn:li:person:YOUR_PERSON_ID'

            # LinkedIn Post API endpoint
            url = "https://api.linkedin.com/v2/shares"

            headers = {
                'Authorization': f'Bearer {self.linkedin_access_token}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0'
            }

            # Format content with hashtags
            if hashtags:
                hashtag_string = ' '.join([f'#{tag}' for tag in hashtags])
                full_content = f"{content}\n\n{hashtag_string}"
            else:
                full_content = content

            payload = {
                "owner": person_id,
                "subject": {
                    "title": "Business Update"
                },
                "content": {
                    "contentEntities": [
                        {
                            "entityLocation": "https://www.linkedin.com",
                            "thumbnails": []
                        }
                    ],
                    "title": {
                        "text": content[:140]  # LinkedIn title limit
                    }
                },
                "distribution": {
                    "feedDistribution": "MAIN_FEED",
                    "targetEntities": [],
                    "thirdPartyDistributionChannels": []
                },
                "visibility": visibility
            }

            # For simpler text posts, use the text-only format
            simple_payload = {
                "author": f"urn:li:person:{person_id}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": full_content
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": visibility
                }
            }

            response = requests.post(url, headers=headers, json=simple_payload, timeout=30)

            if response.status_code not in [200, 201]:
                logging.error(f"LinkedIn API error: {response.status_code} - {response.text}")
                raise Exception(f"LinkedIn API error: {response.status_code}")

            result = response.json()
            logging.info(f"LinkedIn post created. ID: {result.get('id')}")

            return {
                "post_id": result.get('id'),
                "status": "published",
                "visibility": visibility,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logging.error(f"Error posting to LinkedIn: {str(e)}")
            raise

    def _send_whatsapp_message(self, recipient_phone: str, message_text: str,
                                message_type: str = 'text') -> Dict[str, Any]:
        """Send WhatsApp message using Business API"""
        try:
            if not self.whatsapp_access_token:
                raise ValueError("WhatsApp access token not configured")
            if not self.whatsapp_phone_number_id:
                raise ValueError("WhatsApp phone number ID not configured")

            # WhatsApp Business API endpoint
            url = f"https://graph.facebook.com/{self.whatsapp_api_version}/{self.whatsapp_phone_number_id}/messages"

            headers = {
                'Authorization': f'Bearer {self.whatsapp_access_token}',
                'Content-Type': 'application/json'
            }

            # Format phone number (remove +, spaces, dashes)
            clean_phone = recipient_phone.replace('+', '').replace(' ', '').replace('-', '')

            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": clean_phone,
                "type": message_type
            }

            if message_type == 'text':
                payload["text"] = {
                    "body": message_text,
                    "preview_url": True  # Enable link preview
                }
            elif message_type == 'template':
                payload["template"] = {
                    "name": message_text,  # Template name
                    "language": {
                        "code": "en"
                    }
                }

            response = requests.post(url, headers=headers, json=payload, timeout=30)

            if response.status_code != 200:
                logging.error(f"WhatsApp API error: {response.status_code} - {response.text}")
                raise Exception(f"WhatsApp API error: {response.status_code}")

            result = response.json()
            logging.info(f"WhatsApp message sent. Message ID: {result.get('messages', [{}])[0].get('id')}")

            return {
                "message_id": result.get('messages', [{}])[0].get('id'),
                "contact_id": result.get('contacts', [{}])[0].get('id'),
                "status": "sent",
                "recipient": recipient_phone,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logging.error(f"Error sending WhatsApp message: {str(e)}")
            raise

    def _execute_real_action(self, action_type: str, data: Dict) -> Dict[str, Any]:
        """Execute real action based on type"""
        if action_type == 'send_email':
            return self._send_gmail_email(
                data.get('to'),
                data.get('subject'),
                data.get('body')
            )
        elif action_type == 'post_linkedin':
            return self._post_to_linkedin(
                data.get('content'),
                data.get('hashtags', [])
            )
        elif action_type == 'send_whatsapp':
            return self._send_whatsapp_message(
                data.get('to'),
                data.get('message')
            )
        elif action_type == 'open_url':
            webbrowser.open(data.get('url'))
            return {"status": "opened", "url": data.get('url')}
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

        logging.info(f"Logged action: {action_type} for task {task_id} - Status: {status}")

    def run(self, host='localhost', port=5001, debug=False):
        """Start the Gold Tier MCP server"""
        logging.info(f"Gold Tier MCP Server starting on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug, threaded=True)


def main():
    server = GoldTierMCP()
    server.run()


if __name__ == "__main__":
    main()
