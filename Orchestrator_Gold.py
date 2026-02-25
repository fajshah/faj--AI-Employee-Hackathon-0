"""
FTE Orchestrator - Gold Tier
Master controller with REAL external action execution

Gold Tier Enhancements:
- Real API execution for emails, LinkedIn, WhatsApp
- Link detection and automatic opening
- Enhanced approval workflow integration
- Comprehensive action logging
"""

import os
import sys
import json
import logging
import time
from datetime import datetime
from pathlib import Path
import shutil
import requests
from dotenv import load_dotenv

load_dotenv('.env.gold')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/orchestrator_gold.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class GoldTierOrchestrator:
    """Gold Tier Orchestrator with real action execution"""

    def __init__(self):
        self.version = "3.0.0-Gold"
        self.logs_dir = Path("Logs")
        self.logs_dir.mkdir(exist_ok=True)

        # Directory paths
        self.needs_action_dir = Path("Needs_Action")
        self.plans_dir = Path("Plans")
        self.pending_approval_dir = Path("Pending_Approval")
        self.approved_dir = Path("Approved")
        self.done_dir = Path("Done")
        self.error_dir = Path("Error")

        # MCP Server endpoint
        self.mcp_server_url = os.getenv('MCP_SERVER_URL', 'http://localhost:5001')

        # Create directories
        self._create_directories()

        logger.info(f"Gold Tier Orchestrator initialized v{self.version}")

    def _create_directories(self):
        """Create required directories"""
        for dir_path in [self.needs_action_dir, self.plans_dir,
                         self.pending_approval_dir, self.approved_dir,
                         self.done_dir, self.error_dir]:
            dir_path.mkdir(exist_ok=True)

    def detect_urls(self, content: str) -> list:
        """Detect URLs in content"""
        import re
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return re.findall(url_pattern, content)

    def open_urls(self, urls: list, task_id: str):
        """Open detected URLs via MCP Server"""
        for url in urls:
            try:
                payload = {
                    "task_id": f"{task_id}_link_{i}",
                    "url": url,
                    "action": "open"
                }
                requests.post(
                    f"{self.mcp_server_url}/api/link/open",
                    json=payload,
                    timeout=10
                )
                logger.info(f"Opened URL: {url}")
            except Exception as e:
                logger.error(f"Failed to open URL {url}: {str(e)}")

    def execute_email_action(self, task_data: dict, task_id: str) -> bool:
        """Execute email sending action via MCP"""
        try:
            payload = {
                "task_id": task_id,
                "to": task_data.get('recipient_email', task_data.get('to')),
                "subject": task_data.get('subject', 'No Subject'),
                "body": task_data.get('message', task_data.get('body', '')),
                "cc": task_data.get('cc'),
                "bcc": task_data.get('bcc')
            }

            response = requests.post(
                f"{self.mcp_server_url}/api/email/send",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"Email sent successfully: {result}")
                self._log_action(task_id, "email_sent", "success", result)
                return True
            else:
                error = response.json()
                logger.error(f"Email send failed: {error}")
                self._log_action(task_id, "email_send_failed", "error", error)
                return False

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            self._log_action(task_id, "email_send_error", "error", {"error": str(e)})
            return False

    def execute_linkedin_action(self, task_data: dict, task_id: str) -> bool:
        """Execute LinkedIn posting action via MCP"""
        try:
            content = task_data.get('post_content',
                    task_data.get('content',
                    task_data.get('description', '')))
            hashtags = task_data.get('hashtags',
                    task_data.get('details', {}).get('hashtags', []))

            payload = {
                "task_id": task_id,
                "content": content,
                "hashtags": hashtags,
                "visibility": "PUBLIC"
            }

            response = requests.post(
                f"{self.mcp_server_url}/api/social/post",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"LinkedIn post published: {result}")
                self._log_action(task_id, "linkedin_posted", "success", result)
                return True
            else:
                error = response.json()
                logger.error(f"LinkedIn post failed: {error}")
                self._log_action(task_id, "linkedin_post_failed", "error", error)
                return False

        except Exception as e:
            logger.error(f"Error posting to LinkedIn: {str(e)}")
            self._log_action(task_id, "linkedin_post_error", "error", {"error": str(e)})
            return False

    def execute_whatsapp_action(self, task_data: dict, task_id: str) -> bool:
        """Execute WhatsApp messaging action via MCP"""
        try:
            payload = {
                "task_id": task_id,
                "to": task_data.get('recipient_phone', task_data.get('to')),
                "message": task_data.get('message', task_data.get('body', '')),
                "type": task_data.get('message_type', 'text')
            }

            response = requests.post(
                f"{self.mcp_server_url}/api/whatsapp/send",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"WhatsApp message sent: {result}")
                self._log_action(task_id, "whatsapp_sent", "success", result)
                return True
            else:
                error = response.json()
                logger.error(f"WhatsApp send failed: {error}")
                self._log_action(task_id, "whatsapp_send_failed", "error", error)
                return False

        except Exception as e:
            logger.error(f"Error sending WhatsApp: {str(e)}")
            self._log_action(task_id, "whatsapp_send_error", "error", {"error": str(e)})
            return False

    def execute_task(self, task_data: dict, task_id: str) -> bool:
        """Execute a task based on its type"""
        task_type = task_data.get('task_type', task_data.get('type', 'general'))
        action_type = task_data.get('action_type')

        # Determine action based on task type
        if task_type == 'email' or action_type == 'send_email' or task_data.get('recipient_email'):
            return self.execute_email_action(task_data, task_id)

        elif task_type == 'linkedin_post' or action_type == 'post_linkedin' or task_data.get('post_content'):
            return self.execute_linkedin_action(task_data, task_id)

        elif task_type == 'whatsapp' or action_type == 'send_whatsapp' or task_data.get('recipient_phone'):
            return self.execute_whatsapp_action(task_data, task_id)

        else:
            # Generic task - check for URLs to open
            content = json.dumps(task_data)
            urls = self.detect_urls(content)
            if urls:
                self.open_urls(urls, task_id)
                logger.info(f"Opened {len(urls)} URL(s) for generic task {task_id}")

            return True

    def process_approved_tasks(self):
        """Process tasks that have been approved"""
        approved_files = list(self.approved_dir.glob("*.json"))

        for task_file in approved_files:
            try:
                with open(task_file, 'r') as f:
                    task_data = json.load(f)

                task_id = task_data.get('task_id', task_file.stem)

                logger.info(f"Processing approved task: {task_id}")

                # Execute the task
                success = self.execute_task(task_data, task_id)

                if success:
                    # Move to Done
                    done_path = self.done_dir / f"completed_{task_file.name}"
                    shutil.move(str(task_file), str(done_path))
                    logger.info(f"Task {task_id} completed and moved to Done")
                else:
                    # Move to Error
                    error_path = self.error_dir / f"failed_{task_file.name}"
                    shutil.move(str(task_file), str(error_path))
                    logger.warning(f"Task {task_id} failed and moved to Error")

            except Exception as e:
                logger.error(f"Error processing approved task {task_file}: {str(e)}")

    def process_needs_action(self):
        """Process tasks in Needs_Action directory"""
        task_files = list(self.needs_action_dir.glob("*.json"))

        for task_file in task_files:
            try:
                with open(task_file, 'r') as f:
                    task_data = json.load(f)

                task_id = task_data.get('task_id', task_file.stem)

                logger.info(f"Processing task: {task_id}")

                # Check if task requires approval
                is_sensitive = task_data.get('sensitive', False)
                sensitive_keywords = ['payment', 'salary', 'confidential', 'contract', 'agreement']

                if not is_sensitive:
                    content = json.dumps(task_data).lower()
                    is_sensitive = any(kw in content for kw in sensitive_keywords)

                if is_sensitive:
                    # Move to Pending_Approval
                    approval_path = self.pending_approval_dir / task_file.name
                    shutil.move(str(task_file), str(approval_path))
                    logger.info(f"Task {task_id} is sensitive - moved to Pending_Approval")
                    self._log_action(task_id, "moved_to_approval", "pending",
                                   {"reason": "sensitive_content"})
                else:
                    # Execute the task
                    success = self.execute_task(task_data, task_id)

                    if success:
                        # Move to Done
                        done_path = self.done_dir / f"completed_{task_file.name}"
                        shutil.move(str(task_file), str(done_path))
                        logger.info(f"Task {task_id} completed")
                    else:
                        # Move to Error
                        error_path = self.error_dir / f"failed_{task_file.name}"
                        shutil.move(str(task_file), str(error_path))
                        logger.warning(f"Task {task_id} failed")

            except Exception as e:
                logger.error(f"Error processing task {task_file}: {str(e)}")

    def _log_action(self, task_id: str, action: str, status: str, details: dict):
        """Log action with timestamp"""
        log_entry = {
            "task_id": task_id,
            "action": action,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "tier": "gold",
            "component": "orchestrator"
        }

        log_file = self.logs_dir / f"orchestrator_action_{task_id}_{int(time.time())}.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, indent=2)

    def run(self, interval_seconds=5):
        """Main orchestration loop"""
        print(f"🤖 Gold Tier Orchestrator v{self.version} is running...")
        print(f"Processing tasks every {interval_seconds} seconds")
        print("Press Ctrl+C to stop")

        try:
            while True:
                # Process non-sensitive tasks
                self.process_needs_action()

                # Process approved sensitive tasks
                self.process_approved_tasks()

                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            print("\nOrchestrator stopped.")
        except Exception as e:
            logger.error(f"Orchestrator error: {str(e)}")


def main():
    orchestrator = GoldTierOrchestrator()
    orchestrator.run()


if __name__ == "__main__":
    main()
