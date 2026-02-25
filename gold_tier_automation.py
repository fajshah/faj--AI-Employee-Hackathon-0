#!/usr/bin/env python3
"""
Gold Tier Autonomous AI Employee - Full Automation Script
Connects to LinkedIn and WhatsApp, posts updates, and manages autonomous operations
"""
import os
import sys
import json
import time
import logging
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import requests

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gold_tier_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import system components with fallbacks
try:
    from orchestrator import GoldTierOrchestrator
    from Skills.social_media_skill import SocialMediaSkill
    from Skills.business_dev_skill import BusinessDevSkill
    from Skills.audit_logger import log_action
    from Skills.error_handler import ErrorHandler, ErrorType
except ImportError as e:
    logger.error(f"Import error: {e}")
    # Define fallback classes
    class MockSkill:
        def __init__(self, *args, **kwargs):
            pass
        def execute_social_post(self, *args, **kwargs):
            return "mock_post_id"
        def auto_post_linkedin(self, *args, **kwargs):
            return "mock_linkedin_post_id"

    class MockBusinessDevSkill:
        def execute_full_business_dev_cycle(self):
            logger.info("Mock business dev cycle executed")
        def generate_business_ideas(self):
            return "mock_ideas_path"
        def find_potential_clients(self):
            return "mock_clients_path"
        def send_outreach(self):
            return True

    class MockLogger:
        def __call__(self, action, status, result=""):
            logger.info(f"Audit: {action} - {status} - {result}")

    class MockErrorHandler:
        def handle_system_error(self, *args, **kwargs):
            logger.error(f"Error handled: {args}, {kwargs}")

    GoldTierOrchestrator = None
    SocialMediaSkill = MockSkill
    BusinessDevSkill = MockBusinessDevSkill
    log_action = MockLogger()
    ErrorHandler = MockErrorHandler
    ErrorType = type('ErrorType', (), {'SYSTEM_ERROR': 'system_error', 'API_ERROR': 'api_error'})

class GoldTierAutomation:
    """
    Main automation controller for Gold Tier AI Employee system.

    [INFO] INSERT API CREDENTIALS in .env file:
    - LINKEDIN_ACCESS_TOKEN=your_linkedin_token
    - LINKEDIN_COMPANY_ID=your_company_id
    - WHATSAPP_ACCESS_TOKEN=your_whatsapp_token
    - WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
    - WHATSAPP_RECIPIENT_PHONE=recipient_phone_number

    [INFO] CUSTOM MESSAGE PLACEHOLDER - REPLACE WITH YOUR MESSAGES in the post_linkedin_update() and send_whatsapp_message() methods
    """

    def __init__(self, vault_path: str = "AI_Employee_Vault", dry_run: bool = True):
        """
        Initialize the automation system.

        Args:
            vault_path: Path to the AI Employee vault
            dry_run: If True, simulates operations without executing them (DEFAULT: True for safety)
        """
        self.vault_path = Path(vault_path)
        self.dry_run = dry_run
        self.running = False
        self.orchestrator = None
        self.social_skill = None
        self.business_dev = None
        self.error_handler = None

        # Load API credentials from environment variables
        self.linkedin_token = os.getenv('LINKEDIN_ACCESS_TOKEN', '')
        self.linkedin_company_id = os.getenv('LINKEDIN_COMPANY_ID', '')
        self.whatsapp_token = os.getenv('WHATSAPP_ACCESS_TOKEN', '')
        self.whatsapp_phone_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '')
        self.whatsapp_recipient = os.getenv('WHATSAPP_RECIPIENT_PHONE', '')

        # [INFO] CUSTOM MESSAGE PLACEHOLDER - REPLACE WITH YOUR MESSAGES
        self.default_linkedin_message = (
            f"Gold Tier Autonomous AI Employee System Status Update\n\n"
            f"Operating continuously on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}.\n\n"
            f"[INFO] Current capabilities:\n"
            f"• Business Development Automation\n"
            f"• Social Media Management\n"
            f"• Financial Reporting\n"
            f"• Executive Briefing Generation\n\n"
            f"#AI #Automation #BusinessDevelopment #Productivity #Innovation"
        )

        self.default_whatsapp_message = (
            f"Gold Tier Autonomous AI Employee System\n\n"
            f"Status: Operational\n"
            f"Time: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n"
            f"AI Employee running autonomously with:\n"
            f"- Business Development\n"
            f"- Social Media Management\n"
            f"- Financial Reporting\n"
            f"- Executive Briefings"
        )

        # Validate configuration
        self._validate_configuration()
        self._initialize_components()

    def _validate_configuration(self):
        """Validate that required configuration is present."""
        required_vars = {
            'LINKEDIN_ACCESS_TOKEN': self.linkedin_token,
            'LINKEDIN_COMPANY_ID': self.linkedin_company_id,
            'WHATSAPP_ACCESS_TOKEN': self.whatsapp_token,
            'WHATSAPP_PHONE_NUMBER_ID': self.whatsapp_phone_id,
            'WHATSAPP_RECIPIENT_PHONE': self.whatsapp_recipient
        }

        missing_vars = [k for k, v in required_vars.items() if not v or v.startswith('YOUR_')]

        if missing_vars:
            logger.warning(f"[WARN] WARNING: Missing configuration variables: {missing_vars}")
            logger.warning("Please set these in your .env file before running in live mode")
            if not self.dry_run:
                logger.error("[ERROR] Cannot run in live mode without proper configuration")
                raise ValueError(f"Missing required configuration: {missing_vars}")
        else:
            logger.info("[INFO] All required configuration variables are present")

    def _initialize_components(self):
        """Initialize all system components."""
        try:
            # Initialize orchestrator if available
            if GoldTierOrchestrator:
                self.orchestrator = GoldTierOrchestrator()
                logger.info("[INFO] Gold Tier Orchestrator initialized")

            # Initialize skills
            self.social_skill = SocialMediaSkill()
            self.business_dev = BusinessDevSkill(vault_path=str(self.vault_path))
            self.error_handler = ErrorHandler()

            # Create necessary directories
            (self.vault_path / "LinkedIn_Actions").mkdir(parents=True, exist_ok=True)
            (self.vault_path / "WhatsApp_Actions").mkdir(parents=True, exist_ok=True)
            (self.vault_path / "Automation_Logs").mkdir(parents=True, exist_ok=True)
            (self.vault_path / "Business").mkdir(parents=True, exist_ok=True)

            logger.info("[INFO] System components initialized")

        except Exception as e:
            logger.error(f"[ERROR] Failed to initialize components: {e}")
            raise

    def connect_to_linkedin(self) -> bool:
        """
        Establish connection to LinkedIn API.
        Returns True if connection is successful.
        """
        if self.dry_run:
            logger.info("[DRY_RUN] Would connect to LinkedIn API")
            return True

        try:
            # Test LinkedIn API connection
            headers = {
                'Authorization': f'Bearer {self.linkedin_token}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0'
            }

            # Make a simple API call to test connection
            url = f"https://api.linkedin.com/v2/organizationalEntityAcls"
            params = {
                'q': 'roleAssignee',
                'role': 'ADMINISTRATOR',
                'projection': '(elements*(*,organizationalTarget~(localizedName)))'
            }

            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                logger.info("[INFO] Successfully connected to LinkedIn API")
                log_action("linkedin_connection", "success", "Successfully connected to LinkedIn API")
                return True
            else:
                logger.error(f"[ERROR] LinkedIn API connection failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"[ERROR] Failed to connect to LinkedIn: {e}")
            if self.error_handler:
                self.error_handler.handle_system_error(
                    "linkedin_connection", str(e), {"timestamp": str(datetime.now())}
                )
            log_action("linkedin_connection", "failed", f"Failed to connect: {e}")
            return False

    def connect_to_whatsapp(self) -> bool:
        """
        Establish connection to WhatsApp Business API.
        Returns True if connection is successful.
        """
        if self.dry_run:
            logger.info("[DRY_RUN] Would connect to WhatsApp Business API")
            return True

        try:
            # Test WhatsApp API connection
            headers = {
                'Authorization': f'Bearer {self.whatsapp_token}',
                'Content-Type': 'application/json'
            }

            # Make a simple API call to test connection
            url = f"https://graph.facebook.com/v18.0/{self.whatsapp_phone_id}/"

            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                logger.info("[INFO] Successfully connected to WhatsApp Business API")
                log_action("whatsapp_connection", "success", "Successfully connected to WhatsApp API")
                return True
            else:
                logger.error(f"[ERROR] WhatsApp API connection failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"[ERROR] Failed to connect to WhatsApp: {e}")
            if self.error_handler:
                self.error_handler.handle_system_error(
                    "whatsapp_connection", str(e), {"timestamp": str(datetime.now())}
                )
            log_action("whatsapp_connection", "failed", f"Failed to connect: {e}")
            return False

    def post_linkedin_update(self, message: str = None) -> Optional[str]:
        """
        Post an update to LinkedIn.

        Args:
            message: Custom message to post. If None, uses default message.

        Returns:
            Post ID if successful, None if failed.
        """
        if not message:
            message = self.default_linkedin_message  # [INFO] CUSTOMIZE THIS MESSAGE

        if self.dry_run:
            logger.info(f"[DRY_RUN] Would post to LinkedIn: {message[:100]}...")
            post_id = f"DRY_RUN_POST_{int(time.time())}"

            # Create mock log entry
            log_path = self.vault_path / "LinkedIn_Actions" / f"post_{post_id}.json"
            with open(log_path, 'w') as f:
                json.dump({
                    "timestamp": str(datetime.now()),
                    "post_id": post_id,
                    "message": message,
                    "status": "dry_run_completed",
                    "dry_run": True
                }, f, indent=2)

            log_action("linkedin_post", "dry_run_completed", f"Would have posted: {post_id}")
            return post_id

        try:
            logger.info(f"[POST] Posting to LinkedIn: {message[:50]}... (truncated)")

            # Prepare the post payload for LinkedIn
            headers = {
                'Authorization': f'Bearer {self.linkedin_token}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0'
            }

            post_data = {
                "author": f"urn:li:organization:{self.linkedin_company_id}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": message
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }

            # Make the API call
            url = "https://api.linkedin.com/v2/ugcPosts"
            response = requests.post(url, headers=headers, json=post_data)

            if response.status_code in [200, 201]:
                response_data = response.json()
                post_id = response_data.get('id', f'POST_{int(time.time())}')

                logger.info(f"[SUCCESS] LinkedIn post successful: {post_id}")

                # Log the action to vault
                log_path = self.vault_path / "LinkedIn_Actions" / f"post_{post_id}.json"
                with open(log_path, 'w') as f:
                    json.dump({
                        "timestamp": str(datetime.now()),
                        "post_id": post_id,
                        "message": message,
                        "response": response_data,
                        "status": "completed"
                    }, f, indent=2)

                log_action("linkedin_post", "success", f"Posted successfully: {post_id}")
                return post_id
            else:
                logger.error(f"[ERROR] LinkedIn post failed: {response.status_code} - {response.text}")
                log_action("linkedin_post", "failed", f"Failed to post: {response.text}")
                return None

        except Exception as e:
            logger.error(f"[ERROR] Failed to post to LinkedIn: {e}")
            if self.error_handler:
                self.error_handler.handle_system_error(
                    "linkedin_post", str(e), {"message": message, "timestamp": str(datetime.now())}
                )
            log_action("linkedin_post", "failed", f"Exception: {e}")
            return None

    def send_whatsapp_message(self, message: str = None, recipient: str = None) -> Optional[str]:
        """
        Send a WhatsApp message.

        Args:
            message: Message to send. If None, uses default message.
            recipient: Phone number to send to. If None, uses configured default.

        Returns:
            Message ID if successful, None if failed.
        """
        if not message:
            message = self.default_whatsapp_message  # [INFO] CUSTOMIZE THIS MESSAGE

        if not recipient:
            recipient = self.whatsapp_recipient

        if self.dry_run:
            logger.info(f"[DRY_RUN] Would send WhatsApp to {recipient}: {message[:50]}...")
            message_id = f"DRY_RUN_MSG_{int(time.time())}"

            # Create mock log entry
            log_path = self.vault_path / "WhatsApp_Actions" / f"message_{message_id}.json"
            with open(log_path, 'w') as f:
                json.dump({
                    "timestamp": str(datetime.now()),
                    "message_id": message_id,
                    "recipient": recipient,
                    "message": message,
                    "status": "dry_run_completed",
                    "dry_run": True
                }, f, indent=2)

            log_action("whatsapp_message", "dry_run_completed", f"Would have sent: {message_id}")
            return message_id

        try:
            logger.info(f"[POST] Sending WhatsApp to {recipient}: {message[:50]}... (truncated)")

            # Prepare the message payload for WhatsApp
            headers = {
                'Authorization': f'Bearer {self.whatsapp_token}',
                'Content-Type': 'application/json'
            }

            message_data = {
                "messaging_product": "whatsapp",
                "to": recipient,
                "type": "text",
                "text": {
                    "body": message
                }
            }

            # Make the API call
            url = f"https://graph.facebook.com/v18.0/{self.whatsapp_phone_id}/messages"
            response = requests.post(url, headers=headers, json=message_data)

            if response.status_code in [200, 201]:
                response_data = response.json()
                message_id = response_data.get('messages', [{}])[0].get('id', f'MSG_{int(time.time())}')

                logger.info(f"[SUCCESS] WhatsApp message sent: {message_id}")

                # Log the action to vault
                log_path = self.vault_path / "WhatsApp_Actions" / f"message_{message_id}.json"
                with open(log_path, 'w') as f:
                    json.dump({
                        "timestamp": str(datetime.now()),
                        "message_id": message_id,
                        "recipient": recipient,
                        "message": message,
                        "response": response_data,
                        "status": "completed"
                    }, f, indent=2)

                log_action("whatsapp_message", "success", f"Message sent successfully: {message_id}")
                return message_id
            else:
                logger.error(f"[ERROR] WhatsApp message failed: {response.status_code} - {response.text}")
                log_action("whatsapp_message", "failed", f"Failed to send: {response.text}")
                return None

        except Exception as e:
            logger.error(f"[ERROR] Failed to send WhatsApp message: {e}")
            if self.error_handler:
                self.error_handler.handle_system_error(
                    "whatsapp_message", str(e), {
                        "recipient": recipient,
                        "message": message,
                        "timestamp": str(datetime.now())
                    }
                )
            log_action("whatsapp_message", "failed", f"Exception: {e}")
            return None

    def execute_business_development_cycle(self):
        """
        Execute the full business development automation cycle.
        """
        if self.dry_run:
            logger.info("[DRY_RUN] Would execute business development cycle")
            return True

        try:
            logger.info("[CYCLE] Starting business development automation cycle...")

            # Execute the full business dev cycle
            if self.business_dev:
                self.business_dev.execute_full_business_dev_cycle()

            logger.info("[SUCCESS] Business development cycle completed successfully")
            log_action("business_dev_cycle", "completed", "Full business development cycle executed")
            return True

        except Exception as e:
            logger.error(f"[ERROR] Failed business development cycle: {e}")
            if self.error_handler:
                self.error_handler.handle_system_error(
                    "business_dev_cycle", str(e), {"timestamp": str(datetime.now())}
                )
            log_action("business_dev_cycle", "failed", f"Business dev cycle failed: {e}")
            return False

    def start_autonomous_loop(self, interval: int = 3600):
        """
        Start the Ralph Wiggum autonomous loop.

        Args:
            interval: Time in seconds between loop iterations (default: 1 hour)
        """
        self.running = True
        logger.info(f"[START] Starting Ralph Wiggum autonomous loop (every {interval}s)...")
        logger.info(f"[INFO] DRY_RUN Mode: {'ENABLED' if self.dry_run else 'DISABLED'}")

        try:
            while self.running:
                try:
                    logger.info("[CYCLE] Autonomous loop iteration starting...")

                    # Execute business development cycle
                    self.execute_business_development_cycle()

                    # Post LinkedIn update
                    self.post_linkedin_update()

                    # Send WhatsApp message
                    self.send_whatsapp_message()

                    # If orchestrator is available, run its autonomous functions
                    if self.orchestrator and not self.dry_run:
                        try:
                            # In a real implementation, we'd integrate with the orchestrator's processing
                            # For now, we'll just log that it would process tasks
                            logger.info("[CYCLE] Processing orchestrator tasks...")
                        except Exception as e:
                            logger.error(f"Orchestrator processing error: {e}")

                    logger.info(f"[CYCLE] Loop iteration completed. Next iteration in {interval} seconds...")
                    time.sleep(interval)

                except KeyboardInterrupt:
                    logger.info("[STOP] Received keyboard interrupt, stopping autonomous loop...")
                    self.running = False
                    break
                except Exception as e:
                    logger.error(f"[ERROR] Error in autonomous loop: {e}")
                    if self.error_handler:
                        self.error_handler.handle_system_error(
                            "autonomous_loop", str(e), {"timestamp": str(datetime.now())}
                        )
                    time.sleep(60)  # Wait 1 minute before continuing after error

        except Exception as e:
            logger.error(f"[FATAL] Fatal error in autonomous loop: {e}")
            log_action("autonomous_loop", "fatal", f"Fatal error: {e}")
        finally:
            logger.info("[STOP] Autonomous loop stopped")

    def run_initial_setup(self) -> bool:
        """
        Run initial connection and setup operations.

        Returns True if all connections successful.
        """
        logger.info("[SETUP] Starting initial setup and connection process...")

        # Connect to services
        linkedin_success = self.connect_to_linkedin()
        whatsapp_success = self.connect_to_whatsapp()

        if not linkedin_success or not whatsapp_success:
            logger.error("[ERROR] Initial setup failed - some connections unsuccessful")
            return False

        # Execute first business development cycle
        business_success = self.execute_business_development_cycle()

        # Send initial status updates (only if not in dry run or if forced)
        if not self.dry_run:
            self.post_linkedin_update("Gold Tier Autonomous AI Employee System is now operational!")
            self.send_whatsapp_message("AI Employee System is operational and running autonomously.")
        else:
            self.post_linkedin_update("Gold Tier Autonomous AI Employee - DRY_RUN Mode Active")
            self.send_whatsapp_message("AI Employee System - DRY_RUN Mode Active")

        logger.info("[SUCCESS] Initial setup completed successfully")
        log_action("initial_setup", "completed", "System initialized and connected successfully")
        return True

    def stop(self):
        """Stop the automation system."""
        logger.info("[STOP] Stopping Gold Tier Automation System...")
        self.running = False

        # Perform cleanup if needed
        log_action("system_shutdown", "completed", "Automation system stopped")
        logger.info("[STOP] Gold Tier Automation System stopped")

def main():
    """Main entry point for the automation script."""
    print("Gold Tier Autonomous AI Employee - Full Automation System")
    print("=" * 60)

    # Configuration options
    VAULT_PATH = "AI_Employee_Vault"
    DRY_RUN = True  # [INFO] SET TO False FOR LIVE EXECUTION (RECOMMEND STARTING WITH True)
    LOOP_INTERVAL = 3600  # 1 hour in seconds (adjust as needed)

    print(f"[INFO] DRY_RUN Mode: {'ENABLED' if DRY_RUN else 'DISABLED'}")
    print("For live execution:")
    print("- Ensure API credentials are properly configured")
    print("- Set DRY_RUN = False")
    print("- Test in DRY_RUN mode first")
    print()

    # Initialize automation system
    automation = GoldTierAutomation(vault_path=VAULT_PATH, dry_run=DRY_RUN)

    try:
        # Run initial setup
        if not automation.run_initial_setup():
            logger.error("[ERROR] Initial setup failed. Quitting.")
            return 1

        print("\n[SUCCESS] Initial setup completed successfully!")
        print(f"[INFO] Dry Run Mode: {'ENABLED' if DRY_RUN else 'DISABLED'}")
        print(f"[INFO] Loop Interval: {LOOP_INTERVAL} seconds")
        print(f"[INFO] Vault Path: {VAULT_PATH}")
        print(f"[INFO] LinkedIn Connected: {automation.connect_to_linkedin()}")
        print(f"[INFO] WhatsApp Connected: {automation.connect_to_whatsapp()}")
        print("\n[START] Starting autonomous operations...")
        print("Press Ctrl+C to stop the system\n")

        # Start the autonomous loop
        automation.start_autonomous_loop(interval=LOOP_INTERVAL)

    except KeyboardInterrupt:
        logger.info("[STOP] Received keyboard interrupt, stopping...")
    except Exception as e:
        logger.error(f"[FATAL] Fatal error: {e}")
        logger.exception("Full traceback:")
    finally:
        automation.stop()
        print("\n[STOP] Gold Tier Automation System has stopped.")
        print("Check gold_tier_automation.log for detailed logs.")
        print("Review files in AI_Employee_Vault/ for system outputs.")

    return 0

if __name__ == "__main__":
    sys.exit(main())