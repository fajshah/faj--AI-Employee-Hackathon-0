# WhatsApp Watcher - Silver Tier Component

## Overview
The WhatsApp Watcher monitors the `WhatsApp_Inbox` folder for new messages and creates tasks in the `Needs_Action` folder. It integrates with the existing Silver-tier AI Employee system.

## Features
- Monitors `WhatsApp_Inbox` folder for new `.json` and `.txt` files
- Converts WhatsApp messages into structured task files
- Automatically moves tasks to `Needs_Action` for processing
- Updates dashboard with current system status
- Logs all actions with timestamps
- Classifies tasks based on content using Agent Skills
- Integrates with FTE_Orchestrator for reasoning loop and Plan.md generation

## File Format Support
The watcher supports two file formats:
1. **JSON format**: Structured messages with sender, message, and timestamp
2. **TXT format**: Plain text messages (sender derived from filename)

### JSON Format Example:
```json
{
  "sender": "+1234567890",
  "message": "Hi, how are you doing?",
  "timestamp": "2026-02-13T21:30:00Z",
  "type": "text"
}
```

### TXT Format Example:
Simply put the message content in a text file.

## How to Run

### Method 1: Direct Execution
```bash
python whatsapp_watcher.py
```

### Method 2: Background Execution
```bash
python whatsapp_watcher.py &
```

## Integration with Existing System

1. **Task Creation**: When a new WhatsApp message is detected, it creates a task in `Needs_Action/` with the following structure:
   ```json
   {
     "task_id": "whatsapp_task_[timestamp]_[hash]",
     "source": "whatsapp",
     "sender": "[sender_id]",
     "message": "[message_content]",
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
       "whatsapp_sender": "[sender]",
       "whatsapp_message": "[message_content]",
       "original_file": "[filename]"
     },
     "created_at": "[timestamp]",
     "source_type": "whatsapp_message"
   }
   ```

2. **FTE_Orchestrator Integration**: The created tasks automatically trigger the reasoning loop in the FTE_Orchestrator, which generates Plan.md files.

3. **Dashboard Updates**: The watcher updates the dashboard with current counts of tasks and system status.

4. **Logging**: All actions are logged in `Logs/whatsapp_activity.md`.

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
A sample test file is included at `WhatsApp_Inbox/sample_whatsapp_message.json` to demonstrate functionality.

## Troubleshooting
- Ensure the `WhatsApp_Inbox` folder exists
- Check `Logs/whatsapp_watcher.log` for detailed logs
- Verify that the `Needs_Action` folder is accessible
- Make sure the dashboard file path is correct