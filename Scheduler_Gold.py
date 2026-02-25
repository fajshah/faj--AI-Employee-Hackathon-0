"""
Gold Tier Scheduler - Comprehensive Automation
Handles all scheduled tasks and recurring operations

Features:
- Gmail scanning every 10 minutes
- WhatsApp scanning every 15 minutes
- LinkedIn posting daily at 09:00
- Accounting sync weekly
- CEO briefing generation weekly
- System health checks
- Custom scheduled tasks
"""

import os
import json
import logging
import time
import schedule
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Configure logging with UTF-8 encoding
class Utf8StreamHandler(logging.StreamHandler):
    """Stream handler that handles UTF-8 encoding for Windows console"""
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            # Handle Windows console encoding
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/scheduler_gold.log', encoding='utf-8'),
        Utf8StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class GoldTierScheduler:
    """
    Gold Tier Comprehensive Scheduler
    Manages all automated tasks and recurring operations
    """

    def __init__(self):
        self.dirs = {
            'needs_action': Path('Needs_Action'),
            'scheduled_tasks': Path('Scheduled_Tasks'),
            'logs': Path('Logs'),
            'accounting': Path('Accounting'),
            'done': Path('Done')
        }

        # Create directories
        for dir_path in self.dirs.values():
            dir_path.mkdir(exist_ok=True)

        # Configuration
        self.scan_intervals = {
            'gmail': int(os.getenv('GMAIL_SCAN_INTERVAL', 10)),  # minutes
            'whatsapp': int(os.getenv('WHATSAPP_SCAN_INTERVAL', 15)),  # minutes
            'inbox': int(os.getenv('INBOX_SCAN_INTERVAL', 5)),  # minutes
            'health': int(os.getenv('HEALTH_CHECK_INTERVAL', 30))  # minutes
        }

        self.posting_schedule = {
            'linkedin_time': os.getenv('LINKEDIN_POST_TIME', '09:00'),
            'facebook_time': os.getenv('FACEBOOK_POST_TIME', '10:00'),
            'twitter_time': os.getenv('TWITTER_POST_TIME', '11:00')
        }

        self.report_schedule = {
            'ceo_briefing_day': os.getenv('CEO_BRIEFING_DAY', 'monday'),
            'ceo_briefing_time': os.getenv('CEO_BRIEFING_TIME', '08:00'),
            'accounting_sync_day': os.getenv('ACCOUNTING_SYNC_DAY', 'friday'),
            'accounting_sync_time': os.getenv('ACCOUNTING_SYNC_TIME', '17:00')
        }

        # MCP Server endpoint
        self.mcp_server_url = os.getenv('MCP_SERVER_URL', 'http://localhost:5001')

        # Scheduler stats
        self.stats = {
            'tasks_created': 0,
            'last_gmail_scan': None,
            'last_whatsapp_scan': None,
            'last_linkedin_post': None,
            'last_ceo_briefing': None
        }

        logger.info("Gold Tier Scheduler initialized")

    def schedule_all(self):
        """Schedule all automated tasks"""
        logger.info("Setting up all scheduled tasks...")

        # Regular scans
        schedule.every(self.scan_intervals['gmail']).minutes.do(self.scan_gmail)
        schedule.every(self.scan_intervals['whatsapp']).minutes.do(self.scan_whatsapp)
        schedule.every(self.scan_intervals['inbox']).minutes.do(self.scan_inbox)
        schedule.every(self.scan_intervals['health']).minutes.do(self.health_check)

        # Daily social media posting
        schedule.every().day.at(self.posting_schedule['linkedin_time']).do(self.create_linkedin_post)
        schedule.every().day.at(self.posting_schedule['facebook_time']).do(self.create_facebook_post)
        schedule.every().day.at(self.posting_schedule['twitter_time']).do(self.create_twitter_post)

        # Weekly reports
        schedule.every().monday.at(self.report_schedule['ceo_briefing_time']).do(self.generate_ceo_briefing)
        schedule.every().friday.at(self.report_schedule['accounting_sync_time']).do(self.sync_accounting)

        # Daily summary
        schedule.every().day.at('18:00').do(self.create_daily_summary)

        logger.info("✅ All scheduled tasks configured")

    def scan_gmail(self):
        """Scan Gmail inbox for new messages"""
        logger.info("📧 Running scheduled Gmail scan...")
        
        try:
            # Create a Gmail scan task
            task_id = f"gmail_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            task_content = {
                "task_id": task_id,
                "task_type": "gmail_scan",
                "priority": "LOW",
                "title": "Gmail Inbox Scan",
                "description": "Check Gmail inbox for new messages",
                "assigned_to": "Monitoring_Agent",
                "action_type": "scan",
                "details": {
                    "scan_type": "gmail",
                    "max_results": 10
                },
                "created_at": datetime.now().isoformat(),
                "source": "scheduler_gmail_scan"
            }

            # Save task
            task_file = self.dirs['needs_action'] / f"{task_id}.json"
            with open(task_file, 'w', encoding='utf-8') as f:
                json.dump(task_content, f, indent=2)

            self.stats['tasks_created'] += 1
            self.stats['last_gmail_scan'] = datetime.now().isoformat()

            logger.info(f"✅ Gmail scan task created: {task_id}")

        except Exception as e:
            logger.error(f"❌ Gmail scan error: {str(e)}")

    def scan_whatsapp(self):
        """Scan WhatsApp inbox for new messages"""
        logger.info("💬 Running scheduled WhatsApp scan...")

        try:
            task_id = f"whatsapp_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            task_content = {
                "task_id": task_id,
                "task_type": "whatsapp_scan",
                "priority": "LOW",
                "title": "WhatsApp Inbox Scan",
                "description": "Check WhatsApp for new messages",
                "assigned_to": "Monitoring_Agent",
                "action_type": "scan",
                "details": {
                    "scan_type": "whatsapp",
                    "max_results": 10
                },
                "created_at": datetime.now().isoformat(),
                "source": "scheduler_whatsapp_scan"
            }

            task_file = self.dirs['needs_action'] / f"{task_id}.json"
            with open(task_file, 'w', encoding='utf-8') as f:
                json.dump(task_content, f, indent=2)

            self.stats['tasks_created'] += 1
            self.stats['last_whatsapp_scan'] = datetime.now().isoformat()

            logger.info(f"✅ WhatsApp scan task created: {task_id}")

        except Exception as e:
            logger.error(f"❌ WhatsApp scan error: {str(e)}")

    def scan_inbox(self):
        """Scan general inbox for new files"""
        logger.debug("📥 Running scheduled inbox scan...")

        try:
            inbox_path = Path('Inbox')
            if not inbox_path.exists():
                return

            files = list(inbox_path.glob('*'))
            if files:
                logger.info(f"📥 Found {len(files)} file(s) in Inbox")

                for file_path in files:
                    # Move to Needs_Action for processing
                    dest_path = self.dirs['needs_action'] / file_path.name
                    if not dest_path.exists():
                        # Create task from file
                        self._create_task_from_file(file_path)

        except Exception as e:
            logger.error(f"❌ Inbox scan error: {str(e)}")

    def _create_task_from_file(self, file_path: Path):
        """Create a task from a file in Inbox"""
        try:
            task_id = f"inbox_task_{file_path.stem}_{int(time.time())}"

            # Read file content
            if file_path.suffix == '.json':
                with open(file_path, 'r') as f:
                    content = json.load(f)
            else:
                with open(file_path, 'r') as f:
                    content = {"content": f.read()}

            task_content = {
                "task_id": task_id,
                "task_type": "inbox_item",
                "priority": "MEDIUM",
                "title": f"Inbox Item: {file_path.name}",
                "description": f"Process file from inbox: {file_path.name}",
                "assigned_to": "Action_Agent",
                "details": content,
                "source_file": str(file_path),
                "created_at": datetime.now().isoformat(),
                "source": "scheduler_inbox_scan"
            }

            # Save task
            task_file = self.dirs['needs_action'] / f"{task_id}.json"
            with open(task_file, 'w', encoding='utf-8') as f:
                json.dump(task_content, f, indent=2)

            self.stats['tasks_created'] += 1

            # Archive original file
            archive_dir = Path('Gmail_Archive')
            archive_dir.mkdir(exist_ok=True)
            file_path.rename(archive_dir / file_path.name)

            logger.info(f"✅ Task created from inbox file: {task_id}")

        except Exception as e:
            logger.error(f"❌ Error creating task from file: {str(e)}")

    def create_linkedin_post(self):
        """Create daily LinkedIn post task"""
        logger.info("💼 Creating daily LinkedIn post...")

        try:
            task_id = f"linkedin_daily_{datetime.now().strftime('%Y%m%d')}"

            # Generate post content
            post_templates = [
                {
                    "title": "Industry Insights",
                    "content": "Exciting developments in our industry! Innovation continues to drive transformation. What trends are you watching? #Innovation #Business",
                    "hashtags": ["Innovation", "Business", "Leadership", "IndustryTrends"]
                },
                {
                    "title": "Professional Growth",
                    "content": "Continuous learning is the key to professional success. Investing in skills development pays dividends. #ProfessionalDevelopment #Learning",
                    "hashtags": ["ProfessionalDevelopment", "Learning", "CareerGrowth"]
                },
                {
                    "title": "Business Excellence",
                    "content": "Excellence is not a destination but a continuous journey. Striving for better every day! #Excellence #Business #Growth",
                    "hashtags": ["Excellence", "Business", "Growth", "Mindset"]
                }
            ]

            import random
            post = random.choice(post_templates)

            task_content = {
                "task_id": task_id,
                "task_type": "linkedin_post",
                "action_type": "post_linkedin",
                "priority": "MEDIUM",
                "title": f"Daily LinkedIn Post: {post['title']}",
                "description": f"Post to LinkedIn: {post['content'][:50]}...",
                "assigned_to": "Comms_Agent",
                "platform": "linkedin",
                "post_content": post['content'],
                "hashtags": post['hashtags'],
                "visibility": "PUBLIC",
                "sensitive": False,
                "details": {
                    "post_type": "daily_business_update",
                    "scheduled_time": self.posting_schedule['linkedin_time']
                },
                "created_at": datetime.now().isoformat(),
                "source": "scheduler_linkedin"
            }

            task_file = self.dirs['needs_action'] / f"{task_id}.json"
            with open(task_file, 'w', encoding='utf-8') as f:
                json.dump(task_content, f, indent=2)

            self.stats['tasks_created'] += 1
            self.stats['last_linkedin_post'] = datetime.now().isoformat()

            logger.info(f"✅ LinkedIn post created: {task_id}")

        except Exception as e:
            logger.error(f"❌ LinkedIn post error: {str(e)}")

    def create_facebook_post(self):
        """Create Facebook post task"""
        logger.info("📘 Creating Facebook post...")

        try:
            task_id = f"facebook_daily_{datetime.now().strftime('%Y%m%d')}"

            task_content = {
                "task_id": task_id,
                "task_type": "facebook_post",
                "action_type": "post_social",
                "priority": "MEDIUM",
                "title": "Daily Facebook Post",
                "description": "Post to Facebook",
                "assigned_to": "Comms_Agent",
                "platform": "facebook",
                "post_content": "Daily business update from our team! #Business #Updates",
                "sensitive": False,
                "created_at": datetime.now().isoformat(),
                "source": "scheduler_facebook"
            }

            task_file = self.dirs['needs_action'] / f"{task_id}.json"
            with open(task_file, 'w', encoding='utf-8') as f:
                json.dump(task_content, f, indent=2)

            self.stats['tasks_created'] += 1
            logger.info(f"✅ Facebook post created: {task_id}")

        except Exception as e:
            logger.error(f"❌ Facebook post error: {str(e)}")

    def create_twitter_post(self):
        """Create Twitter/X post task"""
        logger.info("🐦 Creating Twitter post...")

        try:
            task_id = f"twitter_daily_{datetime.now().strftime('%Y%m%d')}"

            task_content = {
                "task_id": task_id,
                "task_type": "twitter_post",
                "action_type": "post_social",
                "priority": "MEDIUM",
                "title": "Daily Twitter Post",
                "description": "Post to Twitter/X",
                "assigned_to": "Comms_Agent",
                "platform": "twitter",
                "post_content": "Daily insights and updates from our team! #Business #AI #Innovation",
                "hashtags": ["Business", "AI", "Innovation"],
                "sensitive": False,
                "created_at": datetime.now().isoformat(),
                "source": "scheduler_twitter"
            }

            task_file = self.dirs['needs_action'] / f"{task_id}.json"
            with open(task_file, 'w', encoding='utf-8') as f:
                json.dump(task_content, f, indent=2)

            self.stats['tasks_created'] += 1
            logger.info(f"✅ Twitter post created: {task_id}")

        except Exception as e:
            logger.error(f"❌ Twitter post error: {str(e)}")

    def generate_ceo_briefing(self):
        """Generate weekly CEO briefing report"""
        logger.info("📊 Generating weekly CEO briefing...")

        try:
            task_id = f"ceo_briefing_{datetime.now().strftime('%Y%m%d')}"

            # Calculate date range for weekly report
            today = datetime.now()
            last_week = today - timedelta(days=7)

            task_content = {
                "task_id": task_id,
                "task_type": "ceo_briefing",
                "action_type": "generate_report",
                "priority": "HIGH",
                "title": f"Weekly CEO Briefing - {today.strftime('%Y-%m-%d')}",
                "description": "Generate weekly executive summary report",
                "assigned_to": "Action_Agent",
                "report_type": "ceo_briefing",
                "period": {
                    "start": last_week.isoformat(),
                    "end": today.isoformat()
                },
                "sections": [
                    "Tasks Completed This Week",
                    "Key Metrics & KPIs",
                    "Financial Summary",
                    "Communication Activity",
                    "Social Media Performance",
                    "Issues & Resolutions",
                    "Next Week's Priorities"
                ],
                "sensitive": True,
                "details": {
                    "report_format": "markdown",
                    "include_charts": True,
                    "distribution": ["ceo@company.com"]
                },
                "created_at": datetime.now().isoformat(),
                "source": "scheduler_ceo_briefing"
            }

            task_file = self.dirs['needs_action'] / f"{task_id}.json"
            with open(task_file, 'w', encoding='utf-8') as f:
                json.dump(task_content, f, indent=2)

            self.stats['tasks_created'] += 1
            self.stats['last_ceo_briefing'] = datetime.now().isoformat()

            logger.info(f"✅ CEO briefing task created: {task_id}")

        except Exception as e:
            logger.error(f"❌ CEO briefing error: {str(e)}")

    def sync_accounting(self):
        """Weekly accounting sync with Odoo"""
        logger.info("📊 Running weekly accounting sync...")

        try:
            task_id = f"accounting_sync_{datetime.now().strftime('%Y%m%d')}"

            task_content = {
                "task_id": task_id,
                "task_type": "accounting_sync",
                "action_type": "odoo_sync",
                "priority": "HIGH",
                "title": f"Weekly Accounting Sync - {datetime.now().strftime('%Y-%m-%d')}",
                "description": "Sync accounting data with Odoo ERP",
                "assigned_to": "Finance_Agent",
                "sync_operations": [
                    "Sync invoices",
                    "Sync expenses",
                    "Sync payments",
                    "Generate trial balance",
                    "Update accounts receivable",
                    "Update accounts payable"
                ],
                "sensitive": True,
                "details": {
                    "odoo_url": os.getenv('ODOO_URL'),
                    "sync_type": "full",
                    "create_backup": True
                },
                "created_at": datetime.now().isoformat(),
                "source": "scheduler_accounting"
            }

            task_file = self.dirs['needs_action'] / f"{task_id}.json"
            with open(task_file, 'w', encoding='utf-8') as f:
                json.dump(task_content, f, indent=2)

            self.stats['tasks_created'] += 1
            logger.info(f"✅ Accounting sync task created: {task_id}")

        except Exception as e:
            logger.error(f"❌ Accounting sync error: {str(e)}")

    def create_daily_summary(self):
        """Create daily summary report"""
        logger.info("📝 Creating daily summary...")

        try:
            task_id = f"daily_summary_{datetime.now().strftime('%Y%m%d')}"

            task_content = {
                "task_id": task_id,
                "task_type": "daily_summary",
                "action_type": "generate_report",
                "priority": "MEDIUM",
                "title": f"Daily Summary - {datetime.now().strftime('%Y-%m-%d')}",
                "description": "Generate daily activity summary",
                "assigned_to": "Monitoring_Agent",
                "report_sections": [
                    "Tasks completed today",
                    "Emails sent",
                    "Social media posts",
                    "WhatsApp messages",
                    "System health status"
                ],
                "sensitive": False,
                "created_at": datetime.now().isoformat(),
                "source": "scheduler_daily_summary"
            }

            task_file = self.dirs['needs_action'] / f"{task_id}.json"
            with open(task_file, 'w', encoding='utf-8') as f:
                json.dump(task_content, f, indent=2)

            self.stats['tasks_created'] += 1
            logger.info(f"✅ Daily summary task created: {task_id}")

        except Exception as e:
            logger.error(f"❌ Daily summary error: {str(e)}")

    def health_check(self):
        """Run system health check"""
        logger.debug("🏥 Running system health check...")

        try:
            # Check MCP Server health
            try:
                response = requests.get(f"{self.mcp_server_url}/health", timeout=5)
                if response.status_code == 200:
                    logger.debug("✅ MCP Server: Healthy")
                else:
                    logger.warning("⚠️  MCP Server: Unhealthy")
            except Exception:
                logger.warning("❌ MCP Server: Unreachable")

            # Check directory counts
            for dir_name, dir_path in self.dirs.items():
                if dir_path.exists():
                    count = len(list(dir_path.glob('*.json')))
                    logger.debug(f"📁 {dir_name}: {count} files")

        except Exception as e:
            logger.error(f"❌ Health check error: {str(e)}")

    def get_scheduler_stats(self) -> Dict:
        """Get scheduler statistics"""
        return {
            "stats": self.stats,
            "schedule_info": {
                "next_gmail_scan": f"Every {self.scan_intervals['gmail']} minutes",
                "next_whatsapp_scan": f"Every {self.scan_intervals['whatsapp']} minutes",
                "next_linkedin_post": f"Daily at {self.posting_schedule['linkedin_time']}",
                "next_ceo_briefing": f"Weekly on {self.report_schedule['ceo_briefing_day']} at {self.report_schedule['ceo_briefing_time']}"
            },
            "timestamp": datetime.now().isoformat()
        }

    def run(self):
        """Run the scheduler"""
        logger.info("🚀 Gold Tier Scheduler starting...")

        print(f"""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     📅  GOLD TIER SCHEDULER  📅                          ║
║                                                           ║
║     Scheduled Tasks:                                      ║
║     • Gmail Scan: Every {self.scan_intervals['gmail']} minutes
║     • WhatsApp Scan: Every {self.scan_intervals['whatsapp']} minutes
║     • Inbox Scan: Every {self.scan_intervals['inbox']} minutes
║     • LinkedIn Post: Daily at {self.posting_schedule['linkedin_time']}
║     • Facebook Post: Daily at {self.posting_schedule['facebook_time']}
║     • Twitter Post: Daily at {self.posting_schedule['twitter_time']}
║     • CEO Briefing: Weekly on {self.report_schedule['ceo_briefing_day']} at {self.report_schedule['ceo_briefing_time']}
║     • Accounting Sync: Weekly on {self.report_schedule['accounting_sync_day']}
║     • Daily Summary: Daily at 18:00
║     • Health Check: Every {self.scan_intervals['health']} minutes
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
        """)

        # Set up all schedules
        self.schedule_all()

        logger.info("Scheduler is running...")
        print("\n✅ Scheduler is running. Press Ctrl+C to stop.\n")

        try:
            while True:
                schedule.run_pending()
                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            print("\n🛑 Scheduler stopped.")


def main():
    """Main entry point"""
    scheduler = GoldTierScheduler()
    scheduler.run()


if __name__ == "__main__":
    main()
