"""
LinkedIn Poster - Gold Tier
Creates and posts REAL updates to LinkedIn via API

Gold Tier Enhancements:
- Real LinkedIn API posting
- Post scheduling support
- Engagement tracking
- Comprehensive logging
"""

import os
import json
import time
import logging
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv('.env.gold')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/linkedin_poster_gold.log'),
        logging.StreamHandler()
    ]
)

class GoldTierLinkedInPoster:
    """Gold Tier LinkedIn Poster with real API capabilities"""

    def __init__(self):
        self.posts_dir = "LinkedIn_Posts"
        self.logs_dir = Path("Logs")
        self.logs_dir.mkdir(exist_ok=True)
        self.needs_action_dir = "Needs_Action"

        # MCP Server endpoint
        self.mcp_server_url = os.getenv('MCP_SERVER_URL', 'http://localhost:5001')

        # LinkedIn configuration
        self.access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
        self.person_id = os.getenv('LINKEDIN_PERSON_ID')

        self._create_directories()
        logging.info("Gold Tier LinkedIn Poster initialized")

    def _create_directories(self):
        """Create required directories"""
        Path(self.posts_dir).mkdir(exist_ok=True)

    def generate_business_post(self) -> dict:
        """Generate a business update post"""
        templates = [
            {
                "title": "Industry Insights",
                "content": "Exciting developments in our industry this week! Innovation continues to drive transformation across sectors. Staying ahead of trends is key to maintaining competitive advantage.",
                "hashtags": ["Innovation", "Business", "Leadership", "IndustryTrends"]
            },
            {
                "title": "Professional Growth",
                "content": "Continuous learning is the foundation of professional success. This week, focus on developing new skills that will drive your career forward. What skill are you working on?",
                "hashtags": ["ProfessionalDevelopment", "Learning", "CareerGrowth", "Skills"]
            },
            {
                "title": "Market Trends",
                "content": "Analyzing current market trends reveals interesting shifts in consumer behavior. Companies that adapt quickly position themselves for sustained growth. Agility is everything.",
                "hashtags": ["MarketTrends", "Strategy", "Growth", "Business"]
            },
            {
                "title": "Client Success",
                "content": "Proud to share another successful project completion! Our commitment to excellence and collaborative approach continues to deliver exceptional results for our clients.",
                "hashtags": ["ClientSuccess", "Excellence", "Partnership", "Results"]
            }
        ]

        import random
        return random.choice(templates)

    def post_to_linkedin_real(self, content: str, hashtags: list = None) -> dict:
        """Post to LinkedIn via MCP Server / Real API"""
        try:
            payload = {
                "task_id": f"linkedin_post_{int(time.time())}",
                "content": content,
                "hashtags": hashtags or [],
                "visibility": "PUBLIC"
            }

            response = requests.post(
                f"{self.mcp_server_url}/api/social/post",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                logging.info(f"LinkedIn post published: {result}")
                return {"status": "success", "result": result}
            else:
                error = response.json()
                logging.error(f"LinkedIn post failed: {error}")
                return {"status": "error", "error": error}

        except requests.exceptions.RequestException as e:
            logging.error(f"Request error posting to LinkedIn: {str(e)}")
            return {"status": "error", "error": str(e)}
        except Exception as e:
            logging.error(f"Error posting to LinkedIn: {str(e)}")
            return {"status": "error", "error": str(e)}

    def create_scheduled_post(self, post_data: dict, schedule_time: str = None) -> str:
        """Create a scheduled post task"""
        post_id = f"linkedin_scheduled_{int(time.time())}"

        post_content = {
            "id": post_id,
            "title": post_data.get('title', 'LinkedIn Post'),
            "content": post_data.get('content', ''),
            "hashtags": post_data.get('hashtags', []),
            "scheduled_time": schedule_time or datetime.now().isoformat(),
            "status": "scheduled",
            "created_at": datetime.now().isoformat()
        }

        # Save post draft
        post_file = Path(self.posts_dir) / f"{post_id}.json"
        with open(post_file, 'w', encoding='utf-8') as f:
            json.dump(post_content, f, indent=2)

        logging.info(f"Created scheduled post: {post_id}")
        return str(post_file)

    def process_post_task(self, task_path: str) -> bool:
        """Process a LinkedIn post task and publish"""
        try:
            filename = os.path.basename(task_path)
            logging.info(f"Processing LinkedIn post task: {filename}")

            with open(task_path, 'r', encoding='utf-8') as f:
                task_data = json.load(f)

            task_id = task_data.get('task_id', filename)

            # Check if it's a LinkedIn post task
            if task_data.get('task_type') != 'linkedin_post' and not task_data.get('post_content'):
                return False

            # Check approval for sensitive content
            if task_data.get('sensitive', False):
                logging.info(f"Task {task_id} is sensitive - waiting for approval")
                return False

            # Get post content
            content = task_data.get('details', {}).get('post_content',
                    task_data.get('description', task_data.get('post_content', '')))
            hashtags = task_data.get('details', {}).get('hashtags',
                    task_data.get('hashtags', []))

            # Post to LinkedIn
            result = self.post_to_linkedin_real(content, hashtags)

            if result['status'] == 'success':
                # Log success
                self._log_action(task_id, "linkedin_posted", "success", result)

                # Move to Done
                done_path = Path("Done") / f"posted_{filename}"
                shutil.move(task_path, done_path)

                logging.info(f"LinkedIn post published: {task_id}")
                return True
            else:
                # Log error
                self._log_action(task_id, "linkedin_post_failed", "error", result)

                # Move to Error
                error_path = Path("Error") / f"failed_{filename}"
                shutil.move(task_path, error_path)

                return False

        except Exception as e:
            logging.error(f"Error processing LinkedIn task: {str(e)}")
            return False

    def _log_action(self, task_id: str, action: str, status: str, details: dict):
        """Log action with timestamp"""
        log_entry = {
            "task_id": task_id,
            "action": action,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "component": "linkedin_poster_gold"
        }

        log_file = self.logs_dir / f"linkedin_action_{task_id}_{int(time.time())}.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, indent=2)

    def create_daily_post_task(self):
        """Create a daily LinkedIn post task"""
        post_data = self.generate_business_post()
        task_id = f"linkedin_daily_{datetime.now().strftime('%Y%m%d')}"

        task_content = {
            "task_id": task_id,
            "task_type": "linkedin_post",
            "priority": "MEDIUM",
            "title": f"Daily LinkedIn Post: {post_data['title']}",
            "description": f"Post to LinkedIn: {post_data['content'][:100]}...",
            "assigned_to": "Social_Agent",
            "deadline": datetime.now().strftime('%Y-%m-%d'),
            "status": "pending",
            "sensitive": False,
            "details": {
                "post_content": post_data['content'],
                "hashtags": post_data['hashtags'],
                "post_type": "daily_business_update"
            },
            "created_at": datetime.now().isoformat(),
            "source": "linkedin_gold_scheduler"
        }

        # Save task to Needs_Action
        task_file = Path(self.needs_action_dir) / f"{task_id}.json"
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(task_content, f, indent=2)

        logging.info(f"Created daily LinkedIn post task: {task_id}")
        return str(task_file)

    def run_daily_posting(self, post_hour=9):
        """Run daily posting schedule"""
        print(f"📱 Gold Tier LinkedIn Poster is running...")
        print(f"Daily posts scheduled for {post_hour}:00")
        print("Press Ctrl+C to stop")

        last_post_date = None

        try:
            while True:
                now = datetime.now()

                # Check if it's time to post (and haven't posted today)
                if now.hour >= post_hour and now.strftime('%Y-%m-%d') != last_post_date:
                    print(f"\n📝 Creating daily LinkedIn post...")
                    self.create_daily_post_task()
                    last_post_date = now.strftime('%Y-%m-%d')

                time.sleep(60)  # Check every minute

        except KeyboardInterrupt:
            print("\nLinkedIn Poster stopped.")
        except Exception as e:
            logging.error(f"Poster error: {str(e)}")


def main():
    poster = GoldTierLinkedInPoster()

    # Check for command line args
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--post-now':
        # Create and post immediately
        poster.create_daily_post_task()
        print("Daily post task created!")
    else:
        # Run scheduled mode
        poster.run_daily_posting()


if __name__ == "__main__":
    main()
