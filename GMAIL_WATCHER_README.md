# Gmail Watcher - Silver Tier Component

## Overview
The Gmail Watcher monitors the `Gmail_Inbox` folder for new emails and creates tasks in the `Needs_Action` folder. It integrates with the existing Silver-tier AI Employee system.

## Features
- Monitors `Gmail_Inbox` folder for new `.json` and `.txt` files
- Converts emails into structured task files
- Automatically moves tasks to `Needs_Action` for processing
- Triggers the reasoning loop to create Plan.md files
- Updates dashboard with current system status
- Logs all actions with timestamps
- Classifies tasks based on content using Agent Skills
- Archives processed email files

## File Format Support
The watcher supports two file formats:
1. **JSON format**: Structured emails with sender, subject, message, and timestamp
2. **TXT format**: Plain text emails (sender derived from filename)

### JSON Format Example:
```json
{
  "sender": "client@company.com",
  "subject": "Meeting Tomorrow",
  "message": "Hi, just confirming our meeting scheduled for tomorrow at 10am.",
  "timestamp": "2026-02-13T21:30:00Z"
}
```

### TXT Format Example:
Simply put the email content in a text file.

## How to Run

### Method 1: Direct Execution
```bash
python gmail_watcher.py
```

### Method 2: Background Execution
```bash
python gmail_watcher.py &
```

## Integration with Existing System

1. **Task Creation**: When a new email is detected, it creates a task in `Needs_Action/` with the following structure:
   ```json
   {
     "task_id": "gmail_task_[timestamp]_[hash]",
     "source": "gmail",
     "sender": "[sender_email]",
     "subject": "[email_subject]",
     "message": "[email_content]",
     "timestamp": "[timestamp]",
     "task_type": "[classified_type]",
     "priority": "[MEDIUM|HIGH]",
     "title": "[auto-generated]",
     "description": "[auto-generated]",
     "assigned_to": "Comms_Agent",
     "deadline": "[today]",
     "status": "pending",
     "sensitive": [true|false],
     "details": {
       "gmail_sender": "[sender]",
       "gmail_subject": "[subject]",
       "gmail_message": "[message_content]",
       "original_file": "[filename]"
     },
     "created_at": "[timestamp]",
     "source_type": "gmail_message"
   }
   ```

2. **FTE_Orchestrator Integration**: The created tasks automatically trigger the reasoning loop in the FTE_Orchestrator, which generates Plan.md files.

3. **Dashboard Updates**: The watcher updates the dashboard with current counts of tasks and system status.

4. **Logging**: All actions are logged in `Logs/gmail_activity.md`.

## Task Classification
The system automatically classifies tasks based on message content:
- `finance`: Payment, invoice, bill, money, transfer, bank
- `calendar`: Meeting, schedule, appointment, call
- `communication`: Email, contact, message, reply
- `task_management`: Task, todo, remind, remember
- `commerce`: Order, purchase, buy, shop
- `general`: All other messages

Sensitive messages containing keywords like 'payment', 'salary', 'confidential', 'private', 'urgent', 'important', 'contract', or 'agreement' are flagged with high priority and sensitive status.

## Sample Test File
A sample test file is included at `Gmail_Inbox/urgent_report_request.json` to demonstrate functionality.

## Troubleshooting
- Ensure the `Gmail_Inbox` folder exists
- Check `Logs/gmail_watcher.log` for detailed logs
- Verify that the `Needs_Action` folder is accessible
- Make sure the dashboard file path is correct