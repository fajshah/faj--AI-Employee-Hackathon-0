"""
Gmail Watcher - Gold Tier
Monitors Gmail and sends REAL emails via Gmail API

Gold Tier Enhancements:
- Real email sending via Gmail API
- Link detection and automatic opening
- Enhanced logging with verification
"""

import os
import json
import time
import logging
import requests
from datetime import datetime
from pathlib import Path
import shutil
from dotenv import load_dotenv

load_dotenv('.env.gold')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/gmail_watcher_gold.log'),
        logging.StreamHandler()
    ]
)

class GoldTierGmailWatcher:
    """Gold Tier Gmail Watcher with real email capabilities"""

    def __init__(self):
        self.gmail_inbox_dir = "Gmail_Inbox"
        self.needs_action_dir = "Needs_Action"
        self.gmail_archive_dir = "Gmail_Archive"
        self.logs_dir = Path("Logs")
        self.logs_dir.mkdir(exist_ok=True)

        # MCP Server endpoint
        self.mcp_server_url = os.getenv('MCP_SERVER_URL', 'http://localhost:5001')

        # Create directories
        self._create_directories()

        logging.info("Gold Tier Gmail Watcher initialized")

    def _create_directories(self):
        """Create required directories"""
        for dir_path in [self.gmail_inbox_dir, self.needs_action_dir, self.gmail_archive_dir]:
            Path(dir_path).mkdir(exist_ok=True)

    def detect_urls_in_content(self, content: str) -> list:
        """Detect URLs in message content"""
        import re
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return re.findall(url_pattern, content)

    def send_real_email(self, task_data: dict) -> dict:
        """Send real email via MCP Server / Gmail API"""
        try:
            payload = {
                "task_id": task_data.get('task_id'),
                "to": task_data.get('recipient_email'),
                "subject": task_data.get('subject', 'No Subject'),
                "body": task_data.get('message', ''),
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
                logging.info(f"Email sent successfully: {result}")
                return {"status": "success", "result": result}
            else:
                error = response.json()
                logging.error(f"Email send failed: {error}")
                return {"status": "error", "error": error}

        except requests.exceptions.RequestException as e:
            logging.error(f"Request error sending email: {str(e)}")
            return {"status": "error", "error": str(e)}
        except Exception as e:
            logging.error(f"Error sending email: {str(e)}")
            return {"status": "error", "error": str(e)}

    def open_detected_links(self, content: str, task_id: str):
        """Open detected URLs in browser"""
        urls = self.detect_urls_in_content(content)

        for url in urls:
            logging.info(f"Detected URL in task {task_id}: {url}")
            try:
                payload = {
                    "task_id": f"{task_id}_link",
                    "url": url,
                    "action": "open"
                }
                requests.post(
                    f"{self.mcp_server_url}/api/link/open",
                    json=payload,
                    timeout=10
                )
                logging.info(f"Opened URL: {url}")
            except Exception as e:
                logging.error(f"Failed to open URL {url}: {str(e)}")

    def process_email_task(self, task_path: str):
        """Process an email task and send real email"""
        try:
            filename = os.path.basename(task_path)
            logging.info(f"Processing email task: {filename}")

            # Load task data
            with open(task_path, 'r', encoding='utf-8') as f:
                task_data = json.load(f)

            task_id = task_data.get('task_id', filename)

            # Check if this is an outbound email task
            if task_data.get('action_type') == 'send_email' or task_data.get('recipient_email'):
                # Check approval status
                if task_data.get('sensitive', False):
                    logging.info(f"Task {task_id} is sensitive - waiting for approval")
                    return False

                # Send real email
                result = self.send_real_email(task_data)

                if result['status'] == 'success':
                    # Log success
                    self._log_action(task_id, "email_sent", "success", result)

                    # Move to Done
                    done_path = Path("Done") / f"sent_{filename}"
                    shutil.move(task_path, done_path)

                    logging.info(f"Email task completed: {task_id}")
                    return True
                else:
                    # Log error
                    self._log_action(task_id, "email_send_failed", "error", result)

                    # Move to Error
                    error_path = Path("Error") / f"failed_{filename}"
                    shutil.move(task_path, error_path)

                    return False
            else:
                # Not an email send task, process normally
                logging.info(f"Task {task_id} is not an email send task")

                # Check for URLs to open
                content = json.dumps(task_data)
                self.open_detected_links(content, task_id)

                # Move to appropriate folder
                done_path = Path("Done") / filename
                shutil.move(task_path, done_path)

                return True

        except Exception as e:
            logging.error(f"Error processing email task: {str(e)}")
            return False

    def _log_action(self, task_id: str, action: str, status: str, details: dict):
        """Log action with timestamp"""
        log_entry = {
            "task_id": task_id,
            "action": action,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "component": "gmail_watcher_gold"
        }

        log_file = self.logs_dir / f"gmail_action_{task_id}_{int(time.time())}.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, indent=2)

    def scan_and_process(self):
        """Scan Needs_Action for email tasks and process them"""
        needs_action_path = Path(self.needs_action_dir)
        task_files = list(needs_action_path.glob("*.json"))

        processed = 0
        for task_file in task_files:
            task_data = {}
            try:
                with open(task_file, 'r') as f:
                    task_data = json.load(f)

                # Check if it's an email-related task
                if (task_data.get('type') == 'email' or
                    task_data.get('source') == 'gmail' or
                    task_data.get('action_type') == 'send_email' or
                    task_data.get('recipient_email')):

                    if self.process_email_task(str(task_file)):
                        processed += 1

            except Exception as e:
                logging.error(f"Error scanning task {task_file}: {str(e)}")

        if processed > 0:
            logging.info(f"Processed {processed} email task(s)")

        return processed

    def run(self, interval_seconds=10):
        """Main monitoring loop"""
        print("📧 Gold Tier Gmail Watcher is running...")
        print(f"Monitoring every {interval_seconds} seconds")
        print("Press Ctrl+C to stop")

        try:
            while True:
                self.scan_and_process()
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\nGmail Watcher stopped.")
        except Exception as e:
            logging.error(f"Watcher error: {str(e)}")


def main():
    watcher = GoldTierGmailWatcher()
    watcher.run()


if __name__ == "__main__":
    main()
