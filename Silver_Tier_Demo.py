"""
Silver Tier Demo - Complete Workflow Demonstration
Demonstrates the full workflow: Gmail → Plan → Approval → Done
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/demo_workflow.log'),
        logging.StreamHandler()
    ]
)

def create_demo_workflow():
    """Create a complete demo workflow showing Silver Tier capabilities"""
    
    print("=== Silver Tier Demo: Complete Workflow ===")
    print("Demonstrating: Gmail -> Plan -> Approval -> Done")
    print()
    
    # Step 1: Create a sample email task (simulating Gmail Watcher)
    print("Step 1: Creating sample email task (simulating Gmail Watcher detection)")
    
    task_id = f"gmail_demo_task_{int(time.time())}"
    
    email_task_content = {
        "task_id": task_id,
        "task_type": "email_response",
        "priority": "HIGH",
        "title": "Gmail: Urgent Payment Request from Client",
        "description": "Respond to urgent payment inquiry from important client",
        "assigned_to": "Comms_Agent",
        "deadline": (datetime.now().date().strftime('%Y-%m-%d')),
        "status": "pending",
        "sensitive": True,  # This makes it go through approval workflow
        "details": {
            "email_from": "important.client@bigcorp.com",
            "email_to": "info@yourcompany.com",
            "email_subject": "URGENT: Payment Status Inquiry",
            "email_body": "Dear Team, I need immediate confirmation on the status of our invoice #INV-2023-001. This is affecting our cash flow and needs urgent attention. Please respond ASAP.",
            "email_date": datetime.now().isoformat(),
            "email_id": f"email_{int(time.time())}"
        },
        "created_at": datetime.now().isoformat(),
        "source": "gmail_watcher_demo"
    }
    
    # Save the task to Needs_Action
    needs_action_dir = "Needs_Action"
    Path(needs_action_dir).mkdir(exist_ok=True)
    
    task_filename = f"{task_id}.json"
    task_path = os.path.join(needs_action_dir, task_filename)
    
    with open(task_path, 'w', encoding='utf-8') as f:
        json.dump(email_task_content, f, indent=2)
    
    logging.info(f"Created demo email task: {task_filename}")
    print(f"   [OK] Created task file: {task_filename}")
    print(f"   [OK] Task marked as sensitive (requires approval)")
    print()
    
    # Step 2: Run the orchestrator to create a plan (simulating reasoning loop)
    print("Step 2: Running orchestrator to create detailed plan (reasoning loop)")
    
    from Agents.FTE_Orchestrator_Silver import FTE_Orchestrator
    
    orchestrator = FTE_Orchestrator()
    
    # Process the task to create a plan
    # Since we're simulating, we'll manually trigger plan creation
    plans_dir = "Plans"
    Path(plans_dir).mkdir(exist_ok=True)
    
    plan_content = f"""# Detailed Task Plan: {task_id}

## Original Task
```json
{json.dumps(email_task_content, indent=2)}
```

## Task Analysis
- **Type**: Email Response (Sensitive)
- **Priority**: HIGH
- **Assigned Agent**: Comms_Agent
- **Deadline**: {email_task_content['deadline']}
- **Requires Approval**: YES (due to sensitive nature)

## Action Steps
1. **Analyze Email Content**
   - Extract sender information: {email_task_content['details']['email_from']}
   - Understand email subject: {email_task_content['details']['email_subject']}
   - Identify urgency level: HIGH
   - Recognize sensitivity: Payment-related inquiry

2. **Formulate Response Strategy**
   - Determine appropriate tone: Professional and reassuring
   - Identify required information to address: Invoice status
   - Check for sensitive information requiring approval: YES

3. **Draft Response**
   - Create professional, concise response
   - Include all requested information about invoice status
   - Follow company communication guidelines
   - Emphasize commitment to resolving the matter

4. **Submit for Approval**
   - Route to appropriate authority for review
   - Ensure compliance with financial communication protocols
   - Verify all sensitive information is handled properly

5. **Execute Delivery (after approval)**
   - Send via MCP server
   - Confirm delivery
   - Log completion

## Responsible Agent
- **Primary**: Comms_Agent
- **Secondary**: Finance_Agent (for invoice details)
- **Approval Required**: Yes

## Expected Outcome
Professional email response delivered to sender addressing payment inquiry with appropriate authorization.

## Created At
{datetime.now().isoformat()}

## Status Tracking
- [x] Task analyzed
- [x] Response strategy formulated
- [x] Response drafted
- [ ] Awaiting approval
- [ ] Response to be sent
- [ ] Confirmation to be received
"""
    
    plan_path = os.path.join(plans_dir, f"{task_id}_Plan.md")
    with open(plan_path, 'w', encoding='utf-8') as f:
        f.write(plan_content)
    
    logging.info(f"Created detailed plan for task: {task_id}")
    print(f"   [OK] Created detailed plan: {task_id}_Plan.md")
    print(f"   [OK] Plan includes all required steps and approval workflow")
    print()
    
    # Step 3: Since the task is sensitive, move it to Pending Approval
    print("Step 3: Moving sensitive task to Pending Approval (human-in-the-loop)")
    
    pending_approval_dir = "Pending_Approval"
    Path(pending_approval_dir).mkdir(exist_ok=True)
    
    approval_content = f"""# Sensitive Task Approval Required: {task_id}

## Task Details
```json
{json.dumps(email_task_content, indent=2)}
```

## Approval Status
- Status: PENDING
- Approved By:
- Approved At:
- Comments: Urgent payment inquiry requiring management review

## Created At
{datetime.now().isoformat()}
"""
    
    approval_path = os.path.join(pending_approval_dir, f"{task_id}_approval.json")
    with open(approval_path, 'w', encoding='utf-8') as f:
        f.write(approval_content)
    
    # Move the original task file to pending approval
    pending_task_path = os.path.join(pending_approval_dir, task_filename)
    os.rename(task_path, pending_task_path)
    
    logging.info(f"Moved sensitive task to pending approval: {task_filename}")
    print(f"   [OK] Task moved to Pending_Approval/: {task_filename}")
    print(f"   [OK] Approval file created: {task_id}_approval.json")
    print()
    
    # Step 4: Simulate human approval
    print("Step 4: Simulating human approval decision")
    
    # In a real system, this would be done through the Human Approval Workflow
    # For demo, we'll simulate the approval
    
    approved_dir = "Approved"
    Path(approved_dir).mkdir(exist_ok=True)
    
    # Create approved version
    approved_task_path = os.path.join(approved_dir, f"approved_{task_filename}")
    with open(approved_task_path, 'w', encoding='utf-8') as f:
        # Add approval information to the task
        email_task_content['approved_by'] = "Demo Manager"
        email_task_content['approved_at'] = datetime.now().isoformat()
        email_task_content['approval_comments'] = "Approved for response - standard payment inquiry protocol"
        json.dump(email_task_content, f, indent=2)
    
    # Also create approval record
    approval_record = {
        "task_id": task_id,
        "approved_by": "Demo Manager",
        "approved_at": datetime.now().isoformat(),
        "comments": "Approved for response - standard payment inquiry protocol",
        "status": "APPROVED"
    }
    
    approval_record_path = os.path.join(approved_dir, f"{task_id}_approval_record.json")
    with open(approval_record_path, 'w', encoding='utf-8') as f:
        json.dump(approval_record, f, indent=2)
    
    logging.info(f"Task approved: {task_id}")
    print(f"   [OK] Approval simulated: Task approved by Demo Manager")
    print(f"   [OK] Approved task moved to Approved/: approved_{task_filename}")
    print()
    
    # Step 5: Move approved task back to Needs_Action for processing
    print("Step 5: Moving approved task back to Needs_Action for processing")
    
    final_task_path = os.path.join(needs_action_dir, f"approved_{task_filename}")
    os.rename(approved_task_path, final_task_path)
    
    logging.info(f"Approved task returned to Needs_Action for processing: approved_{task_filename}")
    print(f"   [OK] Task moved to Needs_Action/: approved_{task_filename}")
    print()
    
    # Step 6: Final processing - move to Done
    print("Step 6: Final processing - moving task to Done")
    
    done_dir = "Done"
    Path(done_dir).mkdir(exist_ok=True)
    
    final_done_path = os.path.join(done_dir, f"processed_{task_filename}")
    os.rename(final_task_path, final_done_path)
    
    # Clean up approval file
    if os.path.exists(approval_path):
        os.remove(approval_path)
    
    logging.info(f"Task completed and moved to Done: processed_{task_filename}")
    print(f"   [OK] Task completed and moved to Done/: processed_{task_filename}")
    print(f"   [OK] Approval workflow completed successfully")
    print()
    
    # Step 7: Summary
    print("Step 7: Workflow Summary")
    print("   [OK] Gmail Watcher detected sensitive email")
    print("   [OK] Orchestrator created detailed plan with reasoning loop")
    print("   [OK] Task identified as sensitive, routed to approval workflow")
    print("   [OK] Human approver authorized the response")
    print("   [OK] Task processed and completed")
    print()
    
    print("=== Silver Tier Demo Complete ===")
    print("The complete workflow has been demonstrated:")
    print("Gmail -> Plan -> Approval -> Done")
    print()
    print("Key Silver Tier features showcased:")
    print("- Multiple watchers (Gmail Watcher)")
    print("- Enhanced reasoning loop (detailed planning)")
    print("- Human-in-the-loop approval workflow")
    print("- MCP server integration (simulated)")
    print("- Comprehensive logging")
    print("- Proper task routing and status tracking")

def run_demo():
    """Run the complete demo workflow"""
    try:
        create_demo_workflow()
    except Exception as e:
        logging.error(f"Error in demo workflow: {str(e)}")
        print(f"Error in demo workflow: {str(e)}")

if __name__ == "__main__":
    run_demo()