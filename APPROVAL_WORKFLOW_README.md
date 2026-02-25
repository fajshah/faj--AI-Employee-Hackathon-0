# Human-in-the-loop Approval Workflow

## Overview
The Approval Workflow monitors tasks in the `Needs_Action` folder and checks if they require human approval based on sensitive keywords. Tasks containing keywords like 'payment', 'money', 'financial', etc. are moved to the `Pending_Approval` folder until a human approves them.

## Features
- Monitors `Needs_Action` folder for new tasks
- Identifies sensitive tasks based on keywords
- Creates approval files in `Pending_Approval` folder
- Processes approved tasks from `Approved` folder
- Moves approved tasks to `Done` folder
- Updates dashboard with current status
- Logs all approval-related actions

## Keywords that Trigger Approval
The system checks for these keywords in task content:
- payment
- money
- financial
- salary
- confidential
- private
- urgent
- important
- contract
- agreement
- send email
- external communication
- client reply
- transfer
- invoice
- bill
- bank
- account

## How to Use

### 1. Automatic Approval Detection
When a task is placed in the `Needs_Action` folder, the system automatically checks if it contains any of the sensitive keywords. If it does, the task is moved to the `Pending_Approval` folder.

### 2. Manual Approval Process
To approve a task:
1. Go to the `Pending_Approval` folder
2. Review the `_approval.json` file for the task
3. Move the approval file to the `Approved` folder

### 3. Running the Approval Workflow
```bash
python approval_workflow.py
```

## Approval File Format
When a task requires approval, the system creates a file in `Pending_Approval/` with this structure:
```json
{
  "task_id": "unique_task_id",
  "original_task_file": "original_task_filename.json",
  "reason_for_approval": "Contains keyword: 'payment'",
  "summary": "Task summary",
  "proposed_action": "Description of proposed action",
  "status": "waiting",
  "created_at": "timestamp",
  "task_details": { ... original_task_content ... }
}
```

## Task Flow
1. Task enters `Needs_Action`
2. System checks for sensitive keywords
3. If sensitive: Task gets approval file in `Pending_Approval`
4. Human reviews and moves approval file to `Approved`
5. System processes approved task and moves to `Done`

## Integration with Existing System
- Works alongside Gmail and WhatsApp watchers
- Updates dashboard with approval counts
- Logs all actions in approval_activity.md
- Maintains compatibility with FTE_Orchestrator

## Sample Test File
A sample test file is included at `Needs_Action/payment_authorization_task.json` to demonstrate the approval workflow.