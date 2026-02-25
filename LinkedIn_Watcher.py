"""
LinkedIn Watcher - Monitors and schedules LinkedIn posts
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
        logging.FileHandler('Logs/linkedin_watcher.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LinkedInWatcher:
    """LinkedIn Watcher"""
    
    def __init__(self):
        self.linkedin_posts = Path('LinkedIn_Posts')
        self.needs_action = Path('Needs_Action')
        
        for dir_path in [self.linkedin_posts, self.needs_action]:
            dir_path.mkdir(exist_ok=True)
        
        logger.info("LinkedIn Watcher initialized")
    
    def scan_posts(self):
        """Scan LinkedIn posts"""
        if not self.linkedin_posts.exists():
            return
        
        files = list(self.linkedin_posts.glob('*.json'))
        
        for file_path in files:
            self._process_post(file_path)
    
    def _process_post(self, file_path: Path):
        """Process post and create task"""
        try:
            logger.info(f"Processing LinkedIn post: {file_path.name}")
            
            with open(file_path, 'r') as f:
                post_data = json.load(f)
            
            task_id = f"linkedin_{int(datetime.now().timestamp())}"
            task = {
                "task_id": task_id,
                "task_type": "linkedin_post",
                "source": "linkedin",
                "platform": "linkedin",
                "title": "LinkedIn Post",
                "description": "Publish LinkedIn post",
                "content": post_data.get('content', ''),
                "hashtags": post_data.get('hashtags', []),
                "details": post_data,
                "created_at": datetime.now().isoformat()
            }
            
            task_file = self.needs_action / f"{task_id}.json"
            with open(task_file, 'w') as f:
                json.dump(task, f, indent=2)
            
            logger.info(f"Created task: {task_id}")
            
        except Exception as e:
            logger.error(f"Error processing LinkedIn post: {e}")
    
    def run(self, interval_seconds=60):
        """Main watcher loop"""
        logger.info(f"LinkedIn Watcher running (interval: {interval_seconds}s)")
        
        try:
            while True:
                self.scan_posts()
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            logger.info("LinkedIn Watcher stopped")


def main():
    watcher = LinkedInWatcher()
    watcher.run()


if __name__ == "__main__":
    main()
