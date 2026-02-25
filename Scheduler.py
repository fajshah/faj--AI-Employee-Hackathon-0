"""
Scheduling System - Silver Tier Component
Implements task scheduling for recurring operations
"""

import os
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
import threading
import schedule

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/scheduler.log'),
        logging.StreamHandler()
    ]
)

class SilverTierScheduler:
    def __init__(self):
        self.scheduled_tasks_dir = "Scheduled_Tasks"
        self.logs_dir = "Logs"
        self.needs_action_dir = "Needs_Action"
        
        # Create directories if they don't exist
        self._create_directories()
        
        # Initialize scheduler
        self.jobs = []
        
        logging.info("Silver Tier Scheduler initialized")
    
    def _create_directories(self):
        """Create required directories if they don't exist"""
        dirs_to_create = [
            self.scheduled_tasks_dir,
            self.logs_dir,
            self.needs_action_dir
        ]
        
        for dir_path in dirs_to_create:
            path = Path(dir_path)
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                logging.info(f"Created directory: {dir_path}")
    
    def schedule_inbox_scan(self, interval_minutes=5):
        """Schedule regular inbox scanning"""
        def scan_inbox():
            logging.info("Scheduled inbox scan initiated")
            
            # This would normally call the file watcher logic
            # For now, we'll just log that it ran
            logging.info("Inbox scan completed")
        
        job = schedule.every(interval_minutes).minutes.do(scan_inbox)
        self.jobs.append(job)
        logging.info(f"Scheduled inbox scan every {interval_minutes} minutes")
    
    def schedule_linkedin_posting(self, hour=9, minute=0):
        """Schedule daily LinkedIn posting"""
        def create_linkedin_post():
            logging.info("Scheduled LinkedIn post creation initiated")
            
            # Create a sample LinkedIn post task
            task_id = f"linkedin_daily_post_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            task_content = {
                "task_id": task_id,
                "task_type": "linkedin_post",
                "priority": "MEDIUM",
                "title": f"Daily LinkedIn Post {datetime.now().strftime('%Y-%m-%d')}",
                "description": "Automated daily LinkedIn business update",
                "assigned_to": "Social_Agent",
                "deadline": datetime.now().strftime('%Y-%m-%d'),
                "status": "pending",
                "sensitive": False,
                "details": {
                    "post_content": "Here's an insightful update about industry trends and innovations that are shaping our business landscape. Stay tuned for more updates!",
                    "hashtags": ["#Business", "#Innovation", "#IndustryInsights"],
                    "post_type": "daily_update"
                },
                "created_at": datetime.now().isoformat(),
                "source": "scheduler_daily_linkedin"
            }
            
            # Save the task to Needs_Action
            task_filename = f"{task_id}.json"
            task_path = os.path.join(self.needs_action_dir, task_filename)
            
            with open(task_path, 'w', encoding='utf-8') as f:
                json.dump(task_content, f, indent=2)
            
            logging.info(f"Created scheduled LinkedIn post task: {task_filename}")
        
        job = schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(create_linkedin_post)
        self.jobs.append(job)
        logging.info(f"Scheduled LinkedIn posting daily at {hour:02d}:{minute:02d}")
    
    def schedule_gmail_check(self, interval_minutes=10):
        """Schedule regular Gmail checking"""
        def check_gmail():
            logging.info("Scheduled Gmail check initiated")
            
            # This would normally call the Gmail watcher logic
            # For now, we'll just log that it ran
            logging.info("Gmail check completed")
        
        job = schedule.every(interval_minutes).minutes.do(check_gmail)
        self.jobs.append(job)
        logging.info(f"Scheduled Gmail check every {interval_minutes} minutes")
    
    def schedule_whatsapp_check(self, interval_minutes=15):
        """Schedule regular WhatsApp checking"""
        def check_whatsapp():
            logging.info("Scheduled WhatsApp check initiated")
            
            # This would normally call the WhatsApp watcher logic
            # For now, we'll just log that it ran
            logging.info("WhatsApp check completed")
        
        job = schedule.every(interval_minutes).minutes.do(check_whatsapp)
        self.jobs.append(job)
        logging.info(f"Scheduled WhatsApp check every {interval_minutes} minutes")
    
    def schedule_system_health_check(self, interval_minutes=30):
        """Schedule regular system health checks"""
        def check_system_health():
            logging.info("Scheduled system health check initiated")
            
            # Perform system health checks
            from Agents.FTE_Orchestrator_Silver import FTE_Orchestrator
            orchestrator = FTE_Orchestrator()
            status = orchestrator.get_system_status()
            
            # Log system status
            logging.info(f"System health check - Agents: {len(status['agents'])}, Tasks queued: {status['tasks']['queued']}")
        
        job = schedule.every(interval_minutes).minutes.do(check_system_health)
        self.jobs.append(job)
        logging.info(f"Scheduled system health check every {interval_minutes} minutes")
    
    def schedule_weekly_report(self, day='monday', hour=9, minute=0):
        """Schedule weekly reports"""
        def generate_weekly_report():
            logging.info("Scheduled weekly report generation initiated")
            
            # Create a sample report task
            task_id = f"weekly_report_{datetime.now().strftime('%Y%m%d')}"
            
            # Calculate the week range
            today = datetime.now()
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            
            task_content = {
                "task_id": task_id,
                "task_type": "report_generation",
                "priority": "LOW",
                "title": f"Weekly Report {start_of_week.strftime('%Y-%m-%d')} to {end_of_week.strftime('%Y-%m-%d')}",
                "description": f"Weekly activity report from {start_of_week.strftime('%Y-%m-%d')} to {end_of_week.strftime('%Y-%m-%d')}",
                "assigned_to": "Action_Agent",
                "deadline": datetime.now().strftime('%Y-%m-%d'),
                "status": "pending",
                "sensitive": False,
                "details": {
                    "report_type": "weekly_summary",
                    "period_start": start_of_week.isoformat(),
                    "period_end": end_of_week.isoformat(),
                    "metrics": ["tasks_processed", "emails_handled", "social_posts", "system_uptime"]
                },
                "created_at": datetime.now().isoformat(),
                "source": "scheduler_weekly_report"
            }
            
            # Save the task to Needs_Action
            task_filename = f"{task_id}.json"
            task_path = os.path.join(self.needs_action_dir, task_filename)
            
            with open(task_path, 'w', encoding='utf-8') as f:
                json.dump(task_content, f, indent=2)
            
            logging.info(f"Created scheduled weekly report task: {task_filename}")
        
        job = schedule.every().monday.at(f"{hour:02d}:{minute:02d}").do(generate_weekly_report)
        self.jobs.append(job)
        logging.info(f"Scheduled weekly reports every {day.capitalize()} at {hour:02d}:{minute:02d}")
    
    def run_scheduler(self):
        """Run the scheduler continuously"""
        logging.info("Starting Silver Tier Scheduler")
        
        # Set up default schedules
        self.schedule_inbox_scan(5)  # Every 5 minutes
        self.schedule_gmail_check(10)  # Every 10 minutes
        self.schedule_whatsapp_check(15)  # Every 15 minutes
        self.schedule_linkedin_posting(9, 0)  # Daily at 9 AM
        self.schedule_system_health_check(30)  # Every 30 minutes
        self.schedule_weekly_report('monday', 9, 0)  # Weekly on Monday at 9 AM
        
        print("Silver Tier Scheduler is running...")
        print("Managing scheduled tasks and recurring operations...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)  # Check every second
        except KeyboardInterrupt:
            logging.info("Scheduler stopped by user")
            print("\nScheduler stopped.")
        except Exception as e:
            error_msg = f"Error in scheduler: {str(e)}"
            logging.error(error_msg)
            print(f"\nError: {error_msg}")

def create_windows_task_scheduler_script():
    """Create a Windows Task Scheduler script for the scheduler"""
    script_content = '''@echo off
REM Silver Tier Scheduler Windows Task Setup
REM Run this with admin privileges to schedule the Silver Tier tasks

echo Setting up Silver Tier scheduled tasks...

REM Daily LinkedIn posting at 9 AM
schtasks /create /tn "SilverTier_LinkedIn_Post" /tr "python \\"%~dp0\\LinkedIn_Poster.py\\" " /sc daily /st 09:00 /f

REM System health check every 30 minutes during business hours
schtasks /create /tn "SilverTier_System_Check" /tr "python \\"%~dp0\\ai_employee_system.py\\" " /sc hourly /mo 1 /f

REM Weekly report generation every Monday at 9 AM
schtasks /create /tn "SilverTier_Weekly_Report" /tr "python \\"%~dp0\\ai_employee_system.py\\" " /sc weekly /d MON /st 09:00 /f

echo Scheduled tasks created successfully!
pause
'''
    
    with open('setup_windows_tasks.bat', 'w') as f:
        f.write(script_content)
    
    logging.info("Windows Task Scheduler setup script created: setup_windows_tasks.bat")

def create_cron_script():
    """Create a Linux cron script for the scheduler"""
    script_content = '''#!/bin/bash
# Silver Tier Scheduler Cron Setup
# Add these lines to your crontab using 'crontab -e'

# Daily LinkedIn posting at 9 AM
0 9 * * * cd /path/to/hackthone-0 && python LinkedIn_Poster.py

# System health check every 30 minutes during business hours (9AM-5PM)
*/30 9-17 * * * cd /path/to/hackthone-0 && python ai_employee_system.py

# Weekly report generation every Monday at 9 AM
0 9 * * 1 cd /path/to/hackthone-0 && python ai_employee_system.py

# Gmail check every 10 minutes
*/10 * * * * cd /path/to/hackthone-0 && python Gmail_Watcher.py

# WhatsApp check every 15 minutes
*/15 * * * * cd /path/to/hackthone-0 && python WhatsApp_Watcher.py
'''
    
    with open('setup_cron_jobs.sh', 'w') as f:
        f.write(script_content)
    
    # Make the script executable
    os.chmod('setup_cron_jobs.sh', 0o755)
    
    logging.info("Cron jobs setup script created: setup_cron_jobs.sh")

def main():
    # Create scheduler instance
    scheduler = SilverTierScheduler()
    
    # Create OS-specific scheduling setup scripts
    create_windows_task_scheduler_script()
    create_cron_script()
    
    # Run the scheduler
    scheduler.run_scheduler()

if __name__ == "__main__":
    main()