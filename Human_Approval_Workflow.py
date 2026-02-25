"""
Human Approval Workflow - Silver Tier Component
Manages the human-in-the-loop approval process for sensitive tasks
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/approval_workflow.log'),
        logging.StreamHandler()
    ]
)

class HumanApprovalWorkflow:
    def __init__(self):
        self.pending_approval_dir = "Pending_Approval"
        self.approved_dir = "Approved"
        self.needs_action_dir = "Needs_Action"
        self.done_dir = "Done"
        self.logs_dir = "Logs"
        self.approval_history_dir = "Approval_History"
        
        # Create directories if they don't exist
        self._create_directories()
        
        # Configuration for notifications
        self.notification_config = {
            'email_enabled': False,  # Set to True if email notifications are needed
            'admin_email': os.getenv('ADMIN_EMAIL', 'admin@example.com'),
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'smtp_username': os.getenv('SMTP_USERNAME', 'your_email@gmail.com'),
            'smtp_password': os.getenv('SMTP_PASSWORD', 'your_app_password')
        }
        
        logging.info("Human Approval Workflow initialized")
    
    def _create_directories(self):
        """Create required directories if they don't exist"""
        dirs_to_create = [
            self.pending_approval_dir,
            self.approved_dir,
            self.needs_action_dir,
            self.done_dir,
            self.logs_dir,
            self.approval_history_dir
        ]
        
        for dir_path in dirs_to_create:
            path = Path(dir_path)
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                logging.info(f"Created directory: {dir_path}")
    
    def notify_approver(self, task_id, task_details):
        """Notify the approver about pending tasks"""
        if not self.notification_config['email_enabled']:
            logging.info(f"Notification for task {task_id} skipped (email disabled)")
            return
        
        try:
            # Create email message
            msg = MIMEMultipart()
            msg['Subject'] = f"Action Required: Task Approval Needed - {task_id}"
            msg['From'] = self.notification_config['smtp_username']
            msg['To'] = self.notification_config['admin_email']
            
            body = f"""
A task requires your approval:

Task ID: {task_id}
Title: {task_details.get('title', 'N/A')}
Description: {task_details.get('description', 'N/A')}
Priority: {task_details.get('priority', 'N/A')}
Source: {task_details.get('source', 'N/A')}
Created: {task_details.get('created_at', 'N/A')}

Please review the task in the Pending_Approval folder and move it to Approved if acceptable.
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.notification_config['smtp_server'], self.notification_config['smtp_port'])
            server.starttls()
            server.login(self.notification_config['smtp_username'], self.notification_config['smtp_password'])
            server.send_message(msg)
            server.quit()
            
            logging.info(f"Approval notification sent for task {task_id}")
        except Exception as e:
            logging.error(f"Failed to send approval notification: {str(e)}")
    
    def check_pending_approvals(self):
        """Check for tasks that need approval"""
        pending_files = list(Path(self.pending_approval_dir).glob("*.json"))
        
        if not pending_files:
            logging.info("No tasks pending approval")
            return
        
        logging.info(f"Found {len(pending_files)} tasks pending approval")
        
        for file_path in pending_files:
            # Load task details
            with open(file_path, 'r', encoding='utf-8') as f:
                task_details = json.load(f)
            
            task_id = task_details.get('task_id', file_path.stem)
            
            # Log the pending approval
            self.log_approval_action(task_id, "pending", "Task awaiting approval")
            
            # Notify approver if not already notified recently
            self.notify_approver(task_id, task_details)
    
    def approve_task(self, task_id):
        """Approve a specific task"""
        # Find the task file in pending approval
        task_file = None
        for file_path in Path(self.pending_approval_dir).glob(f"*{task_id}*.json"):
            task_file = file_path
            break
        
        if not task_file:
            logging.error(f"Task {task_id} not found in pending approval")
            return False
        
        # Move to approved directory
        approved_path = os.path.join(self.approved_dir, os.path.basename(task_file))
        os.rename(str(task_file), approved_path)
        
        # Log the approval
        self.log_approval_action(task_id, "approved", "Task approved by human reviewer")
        
        # Move the original task from Needs_Action to Approved (if exists)
        original_task_file = None
        for orig_file in Path(self.needs_action_dir).glob(f"*{task_id}*.json"):
            original_task_file = orig_file
            break
        
        if original_task_file:
            # Move original task to approved
            approved_orig_path = os.path.join(self.approved_dir, f"approved_{os.path.basename(original_task_file)}")
            os.rename(str(original_task_file), approved_orig_path)
        
        logging.info(f"Task {task_id} approved and moved to Approved folder")
        return True
    
    def reject_task(self, task_id, reason="Rejected by human reviewer"):
        """Reject a specific task"""
        # Find the task file in pending approval
        task_file = None
        for file_path in Path(self.pending_approval_dir).glob(f"*{task_id}*.json"):
            task_file = file_path
            break
        
        if not task_file:
            logging.error(f"Task {task_id} not found in pending approval")
            return False
        
        # Log the rejection
        self.log_approval_action(task_id, "rejected", reason)
        
        # Move to done with rejection note
        rejected_path = os.path.join(self.done_dir, f"rejected_{os.path.basename(task_file)}")
        os.rename(str(task_file), rejected_path)
        
        logging.info(f"Task {task_id} rejected and moved to Done folder")
        return True
    
    def process_approved_tasks(self):
        """Process tasks that have been approved"""
        approved_files = list(Path(self.approved_dir).glob("*.json"))
        
        if not approved_files:
            logging.info("No approved tasks to process")
            return
        
        logging.info(f"Processing {len(approved_files)} approved tasks")
        
        for file_path in approved_files:
            # Load task details
            with open(file_path, 'r', encoding='utf-8') as f:
                task_details = json.load(f)
            
            task_id = task_details.get('task_id', file_path.stem)
            
            # Move to Needs_Action for processing by orchestrator
            needs_action_path = os.path.join(self.needs_action_dir, f"approved_{os.path.basename(file_path)}")
            os.rename(str(file_path), needs_action_path)
            
            # Log the processing
            self.log_approval_action(task_id, "processing", "Approved task moved to Needs_Action for processing")
            
            logging.info(f"Approved task {task_id} moved to Needs_Action for processing")
    
    def log_approval_action(self, task_id, action, details):
        """Log approval actions"""
        log_entry = {
            "task_id": task_id,
            "action": action,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        log_filename = f"{self.approval_history_dir}/approval_log_{task_id}_{int(time.time())}.json"
        with open(log_filename, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, indent=2)
    
    def create_approval_interface(self):
        """Create a simple text-based approval interface"""
        print("\n=== Human Approval Interface ===")
        print("Pending Approval Tasks:")
        
        pending_files = list(Path(self.pending_approval_dir).glob("*.json"))
        
        if not pending_files:
            print("No tasks pending approval.")
            return
        
        for i, file_path in enumerate(pending_files):
            with open(file_path, 'r', encoding='utf-8') as f:
                task_details = json.load(f)
            
            print(f"\n{i+1}. Task ID: {task_details.get('task_id', file_path.stem)}")
            print(f"   Title: {task_details.get('title', 'N/A')}")
            print(f"   Description: {task_details.get('description', 'N/A')[:100]}...")
            print(f"   Priority: {task_details.get('priority', 'N/A')}")
            print(f"   Source: {task_details.get('source', 'N/A')}")
        
        print(f"\nTotal pending tasks: {len(pending_files)}")
        
        # Interactive approval
        while True:
            try:
                choice = input("\nEnter task number to approve/reject, 'p' to process approved, or 'q' to quit: ").strip()
                
                if choice.lower() == 'q':
                    break
                elif choice.lower() == 'p':
                    self.process_approved_tasks()
                    break
                elif choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(pending_files):
                        task_file = pending_files[idx]
                        with open(task_file, 'r', encoding='utf-8') as f:
                            task_details = json.load(f)
                        
                        task_id = task_details.get('task_id', task_file.stem)
                        
                        action = input(f"Approve task {task_id}? (y/n/r for reject): ").strip().lower()
                        
                        if action == 'y':
                            self.approve_task(task_id)
                        elif action == 'r':
                            reason = input("Enter rejection reason: ").strip()
                            self.reject_task(task_id, reason)
                        else:
                            print("Task not processed.")
                    else:
                        print("Invalid task number.")
                else:
                    print("Invalid input.")
            except KeyboardInterrupt:
                print("\nApproval interface interrupted.")
                break
    
    def run_monitoring_cycle(self):
        """Run a single monitoring cycle"""
        logging.info("Running approval monitoring cycle")
        
        # Check for pending approvals
        self.check_pending_approvals()
        
        # Process any approved tasks
        self.process_approved_tasks()
    
    def run_continuous_monitoring(self, interval_minutes=5):
        """Continuously monitor for approvals"""
        logging.info(f"Starting continuous approval monitoring (checking every {interval_minutes} minutes)")
        
        print("Human Approval Workflow is running...")
        print("Monitoring for tasks requiring approval...")
        print(f"Checking every {interval_minutes} minutes...")
        print("Use the approval interface to approve/reject tasks")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                self.run_monitoring_cycle()
                time.sleep(interval_minutes * 60)  # Convert minutes to seconds
        except KeyboardInterrupt:
            logging.info("Approval monitoring stopped by user")
            print("\nApproval monitoring stopped.")
        except Exception as e:
            error_msg = f"Error in approval monitoring: {str(e)}"
            logging.error(error_msg)
            print(f"\nError: {error_msg}")

def main():
    workflow = HumanApprovalWorkflow()
    
    # Run in monitoring mode or interactive mode based on preference
    mode = input("Choose mode - (m)onitoring or (i)nteractive approval: ").strip().lower()
    
    if mode == 'i':
        workflow.create_approval_interface()
    else:
        workflow.run_continuous_monitoring()

if __name__ == "__main__":
    main()