"""
Gmail Watcher - Monitors Gmail and creates tasks
"""

import os
import json
import logging
import time
from datetime import datetime
from pathlib import Path
import shutil

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/gmail_watcher.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class GmailWatcher:
    """Gmail Watcher"""
    
    def __init__(self):
        self.gmail_inbox = Path('Gmail_Inbox')
        self.needs_action = Path('Needs_Action')
        self.gmail_archive = Path('Gmail_Archive')
        
        for dir_path in [self.gmail_inbox, self.needs_action, self.gmail_archive]:
            dir_path.mkdir(exist_ok=True)
        
        logger.info("Gmail Watcher initialized")
    
    def scan_inbox(self):
        """Scan Gmail inbox"""
        if not self.gmail_inbox.exists():
            return
        
        files = list(self.gmail_inbox.glob('*.json')) + list(self.gmail_inbox.glob('*.txt'))
        
        for file_path in files:
            self._process_email(file_path)
    
    def _process_email(self, file_path: Path):
        """Process email and create task"""
        try:
            logger.info(f"Processing email: {file_path.name}")
            
            # Read email content
            if file_path.suffix == '.json':
                with open(file_path, 'r') as f:
                    email_data = json.load(f)
            else:
                with open(file_path, 'r') as f:
                    email_data = {"content": f.read()}
            
            # Create task
            task_id = f"gmail_{int(datetime.now().timestamp())}"
            task = {
                "task_id": task_id,
                "task_type": "email",
                "source": "gmail",
                "title": f"Gmail: {email_data.get('subject', 'No Subject')}",
                "description": f"Process email from {email_data.get('from', 'Unknown')}",
                "details": email_data,
                "created_at": datetime.now().isoformat()
            }
            
            # Save task
            task_file = self.needs_action / f"{task_id}.json"
            with open(task_file, 'w') as f:
                json.dump(task, f, indent=2)
            
            # Archive email
            archive_path = self.gmail_archive / f"archived_{file_path.name}"
            shutil.move(str(file_path), str(archive_path))
            
            logger.info(f"Created task: {task_id}")
            
        except Exception as e:
            logger.error(f"Error processing email: {e}")
    
    def run(self, interval_seconds=10):
        """Main watcher loop"""
        logger.info(f"Gmail Watcher running (interval: {interval_seconds}s)")
        
        try:
            while True:
                self.scan_inbox()
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            logger.info("Gmail Watcher stopped")


def main():
    watcher = GmailWatcher()
    watcher.run()


if __name__ == "__main__":
    main()
