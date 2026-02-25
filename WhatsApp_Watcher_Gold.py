"""
WhatsApp Watcher - Gold Tier
Monitors WhatsApp and sends REAL messages via WhatsApp Business API

Gold Tier Enhancements:
- Real WhatsApp Business API integration
- Link detection and automatic opening
- Message template support
- Comprehensive logging with verification
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
        logging.FileHandler('Logs/whatsapp_watcher_gold.log'),
        logging.StreamHandler()
    ]
)

class GoldTierWhatsAppWatcher:
    """Gold Tier WhatsApp Watcher with real messaging capabilities"""

    def __init__(self):
        self.whatsapp_inbox_dir = "WhatsApp_Inbox"
        self.needs_action_dir = "Needs_Action"
        self.logs_dir = Path("Logs")
        self.logs_dir.mkdir(exist_ok=True)

        # MCP Server endpoint
        self.mcp_server_url = os.getenv('MCP_SERVER_URL', 'http://localhost:5001')

        # Create directories
        self._create_directories()

        logging.info("Gold Tier WhatsApp Watcher initialized")

    def _create_directories(self):
        """Create required directories"""
        for dir_path in [self.whatsapp_inbox_dir, self.needs_action_dir]:
            Path(dir_path).mkdir(exist_ok=True)

    def detect_urls_in_content(self, content: str) -> list:
        """Detect URLs in message content"""
        import re
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return re.findall(url_pattern, content)

    def send_real_whatsapp(self, task_data: dict) -> dict:
        """Send real WhatsApp message via MCP Server / WhatsApp Business API"""
        try:
            payload = {
                "task_id": task_data.get('task_id'),
                "to": task_data.get('recipient_phone'),
                "message": task_data.get('message', ''),
                "type": task_data.get('message_type', 'text')
            }

            response = requests.post(
                f"{self.mcp_server_url}/api/whatsapp/send",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                logging.info(f"WhatsApp message sent: {result}")
                return {"status": "success", "result": result}
            else:
                error = response.json()
                logging.error(f"WhatsApp send failed: {error}")
                return {"status": "error", "error": error}

        except requests.exceptions.RequestException as e:
            logging.error(f"Request error sending WhatsApp: {str(e)}")
            return {"status": "error", "error": str(e)}
        except Exception as e:
            logging.error(f"Error sending WhatsApp: {str(e)}")
            return {"status": "error", "error": str(e)}

    def open_detected_links(self, content: str, task_id: str):
        """Open detected URLs in browser"""
        urls = self.detect_urls_in_content(content)

        for url in urls:
            logging.info(f"Detected URL in WhatsApp task {task_id}: {url}")
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

    def process_whatsapp_task(self, task_path: str) -> bool:
        """Process a WhatsApp task and send real message"""
        try:
            filename = os.path.basename(task_path)
            logging.info(f"Processing WhatsApp task: {filename}")

            with open(task_path, 'r', encoding='utf-8') as f:
                task_data = json.load(f)

            task_id = task_data.get('task_id', filename)

            # Check if this is an outbound WhatsApp message task
            if (task_data.get('action_type') == 'send_whatsapp' or
                task_data.get('recipient_phone')):

                # Check approval status
                if task_data.get('sensitive', False):
                    logging.info(f"Task {task_id} is sensitive - waiting for approval")
                    return False

                # Send real WhatsApp message
                result = self.send_real_whatsapp(task_data)

                if result['status'] == 'success':
                    # Log success
                    self._log_action(task_id, "whatsapp_sent", "success", result)

                    # Move to Done
                    done_path = Path("Done") / f"sent_{filename}"
                    shutil.move(task_path, done_path)

                    logging.info(f"WhatsApp task completed: {task_id}")
                    return True
                else:
                    # Log error
                    self._log_action(task_id, "whatsapp_send_failed", "error", result)

                    # Move to Error
                    error_path = Path("Error") / f"failed_{filename}"
                    shutil.move(task_path, error_path)

                    return False
            else:
                # Not a WhatsApp send task, process normally
                logging.info(f"Task {task_id} is not a WhatsApp send task")

                # Check for URLs to open
                content = json.dumps(task_data)
                self.open_detected_links(content, task_id)

                # Move to appropriate folder
                done_path = Path("Done") / filename
                shutil.move(task_path, done_path)

                return True

        except Exception as e:
            logging.error(f"Error processing WhatsApp task: {str(e)}")
            return False

    def _log_action(self, task_id: str, action: str, status: str, details: dict):
        """Log action with timestamp"""
        log_entry = {
            "task_id": task_id,
            "action": action,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "component": "whatsapp_watcher_gold"
        }

        log_file = self.logs_dir / f"whatsapp_action_{task_id}_{int(time.time())}.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, indent=2)

    def scan_and_process(self):
        """Scan Needs_Action for WhatsApp tasks and process them"""
        needs_action_path = Path(self.needs_action_dir)
        task_files = list(needs_action_path.glob("*.json"))

        processed = 0
        for task_file in task_files:
            try:
                with open(task_file, 'r') as f:
                    task_data = json.load(f)

                # Check if it's a WhatsApp-related task
                if (task_data.get('type') == 'whatsapp' or
                    task_data.get('source') == 'whatsapp' or
                    task_data.get('action_type') == 'send_whatsapp' or
                    task_data.get('recipient_phone')):

                    if self.process_whatsapp_task(str(task_file)):
                        processed += 1

            except Exception as e:
                logging.error(f"Error scanning task {task_file}: {str(e)}")

        if processed > 0:
            logging.info(f"Processed {processed} WhatsApp task(s)")

        return processed

    def create_response_task(self, sender: str, message: str, task_id: str = None):
        """Create a WhatsApp response task"""
        import hashlib
        if not task_id:
            task_id = f"whatsapp_response_{int(time.time())}_{hashlib.md5(sender.encode()).hexdigest()[:4]}"

        task_content = {
            "task_id": task_id,
            "action_type": "send_whatsapp",
            "recipient_phone": sender,
            "message": f"Thank you for your message: {message[:100]}...",
            "message_type": "text",
            "priority": "MEDIUM",
            "title": f"WhatsApp Response to {sender}",
            "description": f"Reply to WhatsApp message from {sender}",
            "assigned_to": "Comms_Agent",
            "deadline": datetime.now().strftime('%Y-%m-%d'),
            "status": "pending",
            "sensitive": False,
            "details": {
                "original_sender": sender,
                "original_message": message,
                "response_type": "acknowledgment"
            },
            "created_at": datetime.now().isoformat(),
            "source": "whatsapp_watcher_gold"
        }

        # Save task to Needs_Action
        task_file = Path(self.needs_action_dir) / f"{task_id}.json"
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(task_content, f, indent=2)

        logging.info(f"Created WhatsApp response task: {task_id}")
        return str(task_file)

    def run(self, interval_seconds=10):
        """Main monitoring loop"""
        print("💬 Gold Tier WhatsApp Watcher is running...")
        print(f"Monitoring every {interval_seconds} seconds")
        print("Press Ctrl+C to stop")

        try:
            while True:
                self.scan_and_process()
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\nWhatsApp Watcher stopped.")
        except Exception as e:
            logging.error(f"Watcher error: {str(e)}")


def main():
    watcher = GoldTierWhatsAppWatcher()
    watcher.run()


if __name__ == "__main__":
    main()
