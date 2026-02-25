"""
WhatsApp Watcher - Monitors WhatsApp and creates tasks
"""

import os
import json
import logging
import time
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/whatsapp_watcher.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class WhatsAppWatcher:
    """WhatsApp Watcher"""
    
    def __init__(self):
        self.whatsapp_inbox = Path('WhatsApp_Inbox')
        self.needs_action = Path('Needs_Action')
        
        for dir_path in [self.whatsapp_inbox, self.needs_action]:
            dir_path.mkdir(exist_ok=True)
        
        logger.info("WhatsApp Watcher initialized")
    
    def scan_inbox(self):
        """Scan WhatsApp inbox"""
        if not self.whatsapp_inbox.exists():
            return
        
        files = list(self.whatsapp_inbox.glob('*.json')) + list(self.whatsapp_inbox.glob('*.txt'))
        
        for file_path in files:
            self._process_message(file_path)
    
    def _process_message(self, file_path: Path):
        """Process message and create task"""
        try:
            logger.info(f"Processing WhatsApp: {file_path.name}")
            
            if file_path.suffix == '.json':
                with open(file_path, 'r') as f:
                    msg_data = json.load(f)
            else:
                with open(file_path, 'r') as f:
                    msg_data = {"content": f.read()}
            
            task_id = f"whatsapp_{int(datetime.now().timestamp())}"
            task = {
                "task_id": task_id,
                "task_type": "whatsapp",
                "source": "whatsapp",
                "title": f"WhatsApp Message",
                "description": "Process WhatsApp message",
                "details": msg_data,
                "created_at": datetime.now().isoformat()
            }
            
            task_file = self.needs_action / f"{task_id}.json"
            with open(task_file, 'w') as f:
                json.dump(task, f, indent=2)
            
            logger.info(f"Created task: {task_id}")
            
        except Exception as e:
            logger.error(f"Error processing WhatsApp: {e}")
    
    def run(self, interval_seconds=15):
        """Main watcher loop"""
        logger.info(f"WhatsApp Watcher running (interval: {interval_seconds}s)")
        
        try:
            while True:
                self.scan_inbox()
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            logger.info("WhatsApp Watcher stopped")


def main():
    watcher = WhatsAppWatcher()
    watcher.run()


if __name__ == "__main__":
    main()
