import os
import json
import time
from datetime import datetime
import shutil
import glob

class TaskAgent:
    def __init__(self):
        self.needs_action_dir = "Needs_Action"
        self.plans_dir = "Plans"
        self.done_dir = "Done"
        self.pending_approval_dir = "Pending_Approval"
        self.approved_dir = "Approved"
        self.logs_dir = "Logs"
        
    def log_action(self, task_id, action, status, details=""):
        """Log actions to a timestamped log file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_entry = {
            "timestamp": timestamp,
            "task_id": task_id,
            "action": action,
            "status": status,
            "details": details
        }
        
        log_filename = f"{self.logs_dir}/log_{timestamp}.json"
        with open(log_filename, 'w') as f:
            json.dump(log_entry, f, indent=2)
    
    def create_plan(self, task_title, task_details):
        """Create a step-by-step plan for the task"""
        plan_filename = f"{self.plans_dir}/{task_title.replace(' ', '_')}_plan.md"
        
        # Extract task info for the plan
        title = task_details.get('title', 'Unknown')
        task_type = task_details.get('type', 'Unknown')
        sensitive = task_details.get('sensitive', 'no')
        
        plan_content = f"""# Plan: {title}

## Task Details
- Title: {title}
- Type: {task_type}
- Sensitive: {sensitive}

## Steps to Complete
- [ ] Review task requirements
- [ ] Execute task according to specifications
- [ ] Verify completion
- [ ] Move task to Done folder

## Notes
"""
        if sensitive.lower() == 'yes':
            plan_content += "- [ ] Note: This task is sensitive and requires approval before processing\n"
        else:
            plan_content += "- [ ] Execute task as specified\n"
            
        with open(plan_filename, 'w') as f:
            f.write(plan_content)
        
        return plan_filename
    
    def parse_task_file(self, filepath):
        """Parse a markdown task file and extract key-value pairs"""
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Simple parsing for key-value pairs in markdown
        lines = content.strip().split('\n')
        task_details = {}
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                task_details[key.strip()] = value.strip()
        
        return task_details
    
    def process_task(self, task_filepath):
        """Process a single task file"""
        task_filename = os.path.basename(task_filepath)
        task_details = self.parse_task_file(task_filepath)
        
        # Create a plan for the task
        plan_path = self.create_plan(task_details['title'], task_details)
        
        # Check if task is sensitive
        if task_details.get('sensitive', 'no').lower() == 'yes':
            # Move to pending approval
            dest_path = os.path.join(self.pending_approval_dir, task_filename)
            shutil.move(task_filepath, dest_path)
            
            self.log_action(
                task_details['title'].replace(' ', '_'),
                'move_to_pending_approval',
                'success',
                f'Task moved to {self.pending_approval_dir} due to sensitive flag'
            )
            
            print(f"Task '{task_details['title']}' is sensitive. Moved to Pending Approval.")
        else:
            # Process non-sensitive task
            dest_path = os.path.join(self.done_dir, task_filename)
            shutil.move(task_filepath, dest_path)
            
            self.log_action(
                task_details['title'].replace(' ', '_'),
                'move_to_done',
                'success',
                'Non-sensitive task completed'
            )
            
            print(f"Task '{task_details['title']}' completed and moved to Done.")
    
    def check_approved_tasks(self):
        """Check for approved tasks and process them"""
        approved_files = glob.glob(os.path.join(self.approved_dir, "*.md"))
        
        for approved_file in approved_files:
            filename = os.path.basename(approved_file)
            
            # Find the corresponding pending approval file
            pending_file = os.path.join(self.pending_approval_dir, filename)
            
            if os.path.exists(pending_file):
                # Move the original file to Done
                done_path = os.path.join(self.done_dir, filename)
                
                # Copy the approved file to done (since it contains the approval)
                shutil.copy(approved_file, done_path)
                
                # Remove the pending approval file
                os.remove(pending_file)
                
                # Parse the task details for logging
                task_details = self.parse_task_file(approved_file)
                
                self.log_action(
                    task_details.get('title', filename).replace(' ', '_'),
                    'approved_and_moved_to_done',
                    'success',
                    'Sensitive task approved and moved to Done'
                )
                
                print(f"Approved task '{filename}' moved to Done.")
                
                # Optionally remove the approved file if it's just a copy
                os.remove(approved_file)
    
    def run(self):
        """Main loop to process tasks"""
        print("Starting Task Agent...")
        
        while True:
            # Check for new tasks in Needs_Action
            needs_action_files = glob.glob(os.path.join(self.needs_action_dir, "*.md"))
            
            if needs_action_files:
                print(f"Found {len(needs_action_files)} new task(s)")
                for task_file in needs_action_files:
                    self.process_task(task_file)
            
            # Check for approved tasks
            self.check_approved_tasks()
            
            # Wait before checking again
            time.sleep(5)  # Check every 5 seconds
            
            # For demonstration purposes, we'll break after one cycle
            # In a real implementation, this would run continuously
            break

if __name__ == "__main__":
    agent = TaskAgent()
    agent.run()