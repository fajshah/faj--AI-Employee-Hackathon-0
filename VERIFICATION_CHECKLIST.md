# Gold Tier System Verification Checklist

## Folder Structure
- [ ] Inbox/
- [ ] Needs_Action/
- [ ] WhatsApp_Inbox/
- [ ] Gmail_Inbox/
- [ ] LinkedIn_Posts/
- [ ] Plans/
- [ ] Done/
- [ ] Logs/
- [ ] Pending_Approval/
- [ ] Approved/
- [ ] Accounting/
- [ ] Skills/
- [ ] Agents/

## System Components
- [ ] MCP Server running on port 5001
- [ ] Orchestrator processing tasks
- [ ] Scheduler running automations
- [ ] Gmail Watcher active
- [ ] WhatsApp Watcher active
- [ ] LinkedIn Poster active

## Task Workflow
- [ ] Tasks created in Needs_Action/
- [ ] Plan.md files generated in Plans/
- [ ] Sensitive tasks moved to Pending_Approval/
- [ ] Approved tasks executed
- [ ] Completed tasks in Done/
- [ ] Failed tasks in Error/

## API Endpoints
- [ ] GET /health returns healthy status
- [ ] POST /api/email/send works
- [ ] POST /api/social/post works
- [ ] POST /api/whatsapp/send works
- [ ] POST /api/odoo/action works

## Testing
- [ ] Email send test successful
- [ ] LinkedIn post test successful
- [ ] WhatsApp message test successful
- [ ] Odoo invoice test successful

## Logging
- [ ] Logs created in Logs/
- [ ] Error logs in Logs/Error/
- [ ] MCP action logs present
- [ ] Orchestrator logs present

## Automation
- [ ] Gmail scan every 10 min
- [ ] WhatsApp scan every 15 min
- [ ] LinkedIn post daily at 09:00
- [ ] CEO briefing weekly

## Documentation
- [ ] README.md present
- [ ] .env configured
- [ ] Task templates created
