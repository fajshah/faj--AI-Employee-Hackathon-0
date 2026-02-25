"""
Human-in-the-loop Approval Workflow
Manages sensitive tasks that require human approval before execution
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
import shutil
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/approval_workflow.log'),
        logging.StreamHandler()
    ]
)

class ApprovalWorkflow:
    def __init__(self):
        self.needs_action_dir = "Needs_Action"
        self.pending_approval_dir = "Pending_Approval"
        self.approved_dir = "Approved"
        self.done_dir = "Done"
        self.logs_dir = "Logs"
        self.dashboard_path = "Dashboard.md"
        
        # Keywords that trigger approval requirement
        self.approval_keywords = [
            'payment', 'money', 'financial', 'salary', 'confidential', 
            'private', 'urgent', 'important', 'contract', 'agreement',
            'send email', 'external communication', 'client reply',
            'transfer', 'invoice', 'bill', 'bank', 'account'
        ]
        
        logging.info("Approval Workflow initialized")
    
    def create_dashboard_if_missing(self):
        """Create Dashboard.md with required sections if it doesn't exist"""
        if not os.path.exists(self.dashboard_path):
            dashboard_content = """# AI Employee Dashboard

## Today's Tasks
- **Pending:** 0 tasks
- **In Progress:** 0 tasks
- **Completed:** 0 tasks

## Recent Activity
- System initialized

## System Status
- **Status:** Active
- **Last Check:** {current_time}
- **Uptime:** 0 days, 0 hours, 0 minutes

""".format(current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            with open(self.dashboard_path, 'w', encoding='utf-8') as f:
                f.write(dashboard_content)
            
            logging.info("Created new Dashboard.md")
    
    def log_action(self, action):
        """Log action to the activity log file with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"\n## {timestamp}\n- {action}\n"
        
        log_path = os.path.join(self.logs_dir, "approval_activity.md")
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        logging.info(action)
    
    def update_dashboard(self):
        """Update the dashboard with current system status"""
        self.create_dashboard_if_missing()
        
        # Count files in each directory
        needs_action_count = len([f for f in os.listdir(self.needs_action_dir) if os.path.isfile(os.path.join(self.needs_action_dir, f))])
        pending_approval_count = len([f for f in os.listdir(self.pending_approval_dir) if os.path.isfile(os.path.join(self.pending_approval_dir, f))])
        approved_count = len([f for f in os.listdir(self.approved_dir) if os.path.isfile(os.path.join(self.approved_dir, f))])
        done_count = len([f for f in os.listdir(self.done_dir) if os.path.isfile(os.path.join(self.done_dir, f))])
        
        # Read current dashboard
        with open(self.dashboard_path, 'r', encoding='utf-8') as f:
            dashboard_content = f.read()
        
        # Update the dashboard content based on the existing format
        updated_content = dashboard_content.replace(
            "### 📥 Needs_Action/\nTasks waiting to be processed\n- Current count: 0",
            f"### 📥 Needs_Action/\nTasks waiting to be processed\n- Current count: {needs_action_count}"
        )
        
        # Update other counts as well
        updated_content = updated_content.replace(
            "- Current count: 25",
            f"- Current count: {done_count}"
        ) if f"- Current count: 25" in updated_content else updated_content
        
        updated_content = updated_content.replace(
            "- Current count: 11",
            f"- Current count: {pending_approval_count}"
        ) if f"- Current count: 11" in updated_content else updated_content
        
        updated_content = updated_content.replace(
            "- Current count: 64",
            f"- Current count: {len(os.listdir(self.logs_dir)) if os.path.exists(self.logs_dir) else 0}"
        ) if f"- Current count: 64" in updated_content else updated_content
        
        updated_content = updated_content.replace(
            "- Total processed: 25 tasks",
            f"- Total processed: {done_count} tasks"
        ) if f"- Total processed: 25 tasks" in updated_content else updated_content
        
        updated_content = updated_content.replace(
            "- Active tasks: 0 (needs processing)",
            f"- Active tasks: {needs_action_count} (needs processing)"
        ) if f"- Active tasks: 0 (needs processing)" in updated_content else updated_content
        
        updated_content = updated_content.replace(
            "- Sensitive tasks: 11 pending approval",
            f"- Sensitive tasks: {pending_approval_count} pending approval"
        ) if f"- Sensitive tasks: 11 pending approval" in updated_content else updated_content
        
        # Update the last update date
        updated_content = updated_content.replace(
            "## System Overview\n- **Agent Type:** Bronze Tier AI Employee\n- **Status:** Monitoring\n- **Last Update:** February 13, 2026",
            f"## System Overview\n- **Agent Type:** Bronze Tier AI Employee\n- **Status:** Monitoring\n- **Last Update:** {datetime.now().strftime('%B %d, %Y')}"
        )
        
        # Write updated dashboard
        with open(self.dashboard_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        self.log_action(f"Dashboard updated - Needs Action: {needs_action_count}, Pending Approval: {pending_approval_count}")
    
    def requires_approval(self, task_content):
        """Check if a task requires human approval based on keywords"""
        # Convert task content to string for keyword search
        task_text = json.dumps(task_content).lower()
        
        # Check for approval keywords
        for keyword in self.approval_keywords:
            if keyword.lower() in task_text:
                return True, keyword
        
        return False, None
    
    def create_approval_file(self, task_path, task_content):
        """Create an approval file for a task that requires approval"""
        task_filename = os.path.basename(task_path)
        task_id = task_content.get('task_id', task_filename.replace('.json', ''))
        
        # Determine reason for approval
        requires_approval, keyword_found = self.requires_approval(task_content)
        
        approval_content = {
            "task_id": task_id,
            "original_task_file": task_filename,
            "reason_for_approval": f"Contains keyword: '{keyword_found}'" if keyword_found else "Flagged as sensitive",
            "summary": task_content.get('title', 'Task summary not available'),
            "proposed_action": task_content.get('description', 'Action not specified'),
            "status": "waiting",
            "created_at": datetime.now().isoformat(),
            "task_details": task_content
        }
        
        # Create approval file in Pending_Approval directory
        approval_filename = f"{task_id}_approval.json"
        approval_path = os.path.join(self.pending_approval_dir, approval_filename)
        
        with open(approval_path, 'w', encoding='utf-8') as f:
            json.dump(approval_content, f, indent=2)
        
        logging.info(f"Created approval file: {approval_filename}")
        self.log_action(f"Approval required for task: {task_id} (reason: {approval_content['reason_for_approval']})")
        
        return approval_path
    
    def process_needs_action_tasks(self):
        """Process tasks in Needs_Action to check if they need approval"""
        needs_action_path = Path(self.needs_action_dir)
        task_files = list(needs_action_path.glob("*.json"))
        
        for task_file in task_files:
            task_path = str(task_file)
            
            # Load task content
            with open(task_path, 'r', encoding='utf-8') as f:
                try:
                    task_content = json.load(f)
                except json.JSONDecodeError:
                    logging.error(f"Invalid JSON in task file: {task_file}")
                    continue
            
            # Check if task requires approval
            requires_approval, keyword_found = self.requires_approval(task_content)
            
            if requires_approval:
                # Create approval file
                approval_path = self.create_approval_file(task_path, task_content)
                
                # Log waiting for approval
                task_id = task_content.get('task_id', task_file.stem)
                self.log_action(f"Waiting for human approval for task: {task_id}")
                
                # Remove the original task file from Needs_Action
                os.remove(task_path)
                
                logging.info(f"Task {task_file.name} moved to approval workflow")
            else:
                # Task doesn't require approval, leave it in Needs_Action for normal processing
                logging.info(f"Task {task_file.name} does not require approval, leaving in Needs_Action")
    
    def process_approved_tasks(self):
        """Process tasks that have been approved"""
        approved_path = Path(self.approved_dir)
        approved_files = list(approved_path.glob("*.json"))
        
        for approved_file in approved_files:
            approved_file_path = str(approved_file)
            
            # Load the approved task content
            with open(approved_file_path, 'r', encoding='utf-8') as f:
                try:
                    approved_content = json.load(f)
                except json.JSONDecodeError:
                    logging.error(f"Invalid JSON in approved file: {approved_file}")
                    continue
            
            # Extract the original task content
            original_task_content = approved_content.get('task_details', {})
            task_id = approved_content.get('task_id', approved_file.stem.replace('_approval', ''))
            
            # Log that approval was granted
            self.log_action(f"Approved and executing task: {task_id}")
            
            # Move the approved task back to Needs_Action for execution
            # (or directly to Done if we want to simulate execution)
            # For this implementation, we'll move it to Done to simulate execution
            done_filename = f"approved_{task_id}.json"
            done_path = os.path.join(self.done_dir, done_filename)
            
            # If the original task details exist, save them to Done
            if original_task_content:
                with open(done_path, 'w', encoding='utf-8') as f:
                    json.dump(original_task_content, f, indent=2)
            
            # Remove the approval file from Approved directory
            os.remove(approved_file_path)
            
            logging.info(f"Approved task {task_id} moved to Done")
    
    def run_monitoring_cycle(self):
        """Run a single cycle of monitoring and processing"""
        logging.info("Running approval workflow monitoring cycle")
        
        # Process tasks in Needs_Action to check for approval requirements
        self.process_needs_action_tasks()
        
        # Process approved tasks
        self.process_approved_tasks()
        
        # Update dashboard
        self.update_dashboard()
    
    def run(self, interval_seconds=10):
        """Main loop to continuously monitor for approval requirements"""
        self.create_dashboard_if_missing()
        self.log_action("Approval Workflow started")
        self.update_dashboard()
        
        print("Approval Workflow is running...")
        print("Monitoring for tasks requiring human approval...")
        print(f"Checking every {interval_seconds} seconds...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                self.run_monitoring_cycle()
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            self.log_action("Approval Workflow stopped by user")
            print("\nApproval Workflow stopped.")
        except Exception as e:
            error_msg = f"Error in Approval Workflow: {str(e)}"
            self.log_action(error_msg)
            logging.error(error_msg)

def main():
    workflow = ApprovalWorkflow()
    workflow.run()

if __name__ == "__main__":
    main()