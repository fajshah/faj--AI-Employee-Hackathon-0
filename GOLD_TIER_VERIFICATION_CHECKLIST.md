# GOLD TIER AI EMPLOYEE SYSTEM - VERIFICATION CHECKLIST

Complete verification for all Bronze, Silver, and Gold Tier requirements.

---

## PHASE 1: ENVIRONMENT & STRUCTURE

### Folder Structure
- [ ] Inbox/
- [ ] Needs_Action/
- [ ] WhatsApp_Inbox/
- [ ] Gmail_Inbox/
- [ ] LinkedIn_Posts/
- [ ] Facebook_Posts/
- [ ] Instagram_Posts/
- [ ] Twitter_Posts/
- [ ] Plans/
- [ ] Done/
- [ ] Logs/
- [ ] Logs/Errors/
- [ ] Pending_Approval/
- [ ] Approved/
- [ ] Accounting/
- [ ] Skills/
- [ ] Agents/
- [ ] Scheduler/
- [ ] MCP_Servers/
- [ ] Reports/

### Environment
- [ ] Python 3.13+ installed
- [ ] pip installed
- [ ] Requirements installed: `pip install -r requirements.txt`
- [ ] .env file configured with credentials

---

## PHASE 2: AGENTS & SKILLS

### Agents (6 Total)
- [ ] Agents/Orchestrator_Agent.py
- [ ] Agents/Monitoring_Agent.py
- [ ] Agents/Comms_Agent.py
- [ ] Agents/Social_Agent.py
- [ ] Agents/Finance_Agent.py
- [ ] Agents/Audit_Agent.py

### Skills (14 Total)
- [ ] Skills/__init__.py
- [ ] Skills/comms_skills.py (send_email, send_whatsapp)
- [ ] Skills/social_skills.py (post_linkedin, post_facebook, post_instagram, post_twitter)
- [ ] Skills/finance_skills.py (create_invoice_odoo, log_expense_odoo, generate_accounting_summary)
- [ ] Skills/orchestrator_skills.py (analyze_task, create_plan_md, route_task, multi_step_execution, retry_failed_task)
- [ ] Skills/audit_skills.py (generate_weekly_ceo_brief, error_recovery, audit_log_writer)

---

## PHASE 3: WATCHERS

- [ ] Gmail_Watcher.py - Monitors Gmail_Inbox/
- [ ] WhatsApp_Watcher.py - Monitors WhatsApp_Inbox/
- [ ] LinkedIn_Watcher.py - Monitors LinkedIn_Posts/

All watchers:
- [ ] Log activity in Logs/
- [ ] Create tasks in Needs_Action/
- [ ] Move processed files to archive

---

## PHASE 4: REASONING LOOP

For every task:
- [ ] Orchestrator analyzes task
- [ ] Plans/<task_id>_Plan.md created
- [ ] Plan includes step-by-step execution
- [ ] Plan includes approval requirement
- [ ] Plan includes status checkboxes
- [ ] Creation logged in Logs/

---

## PHASE 5: HUMAN-IN-THE-LOOP

For sensitive tasks:
- [ ] Pending_Approval/<task_id>_approval.json created
- [ ] Contains: task_id, summary, proposed_action, reason, status="waiting"
- [ ] System waits for approval
- [ ] Approval by status="approved" or move to Approved/
- [ ] After approval, moves to Needs_Action/

---

## PHASE 6: MCP SERVERS

### MCP_Comms_Server (Port 5001)
- [ ] Running on localhost:5001
- [ ] Route: /api/email/send
- [ ] Route: /api/whatsapp/send
- [ ] Logs to Logs/mcp_comms_*.json

### MCP_Social_Server (Port 5002)
- [ ] Running on localhost:5002
- [ ] Route: /api/social/post
- [ ] Logs to Logs/mcp_social_*.json

### MCP_Finance_Server (Port 5003)
- [ ] Running on localhost:5003
- [ ] Route: /api/odoo/action
- [ ] Logs to Logs/mcp_finance_*.json

All servers:
- [ ] Have retry logic
- [ ] Have error handling
- [ ] Return JSON status

---

## PHASE 7: ODOO INTEGRATION

- [ ] ODOO_URL configured in .env
- [ ] Finance_Agent can create invoices
- [ ] Finance_Agent can log expenses
- [ ] Finance_Agent can generate reports
- [ ] All actions logged in Accounting/

---

## PHASE 8: SCHEDULER

### Automations
- [ ] Gmail scan every 10 minutes
- [ ] WhatsApp scan every 15 minutes
- [ ] LinkedIn post daily at 09:00
- [ ] Facebook post daily at 10:00
- [ ] Instagram post daily at 11:00
- [ ] Twitter post daily at 12:00
- [ ] Accounting sync Monday 08:00
- [ ] CEO Brief Sunday 18:00

### Scheduler Script
- [ ] Scheduler/Gold_Tier_Scheduler.py exists
- [ ] Uses schedule module
- [ ] Windows Task Scheduler instructions provided

---

## PHASE 9: RALPH WIGGUM LOOP

- [ ] Multi-step execution implemented
- [ ] Executes step 1
- [ ] Analyzes result
- [ ] Adjusts plan
- [ ] Executes next step
- [ ] Logs reasoning trace

---

## PHASE 10: ERROR RECOVERY

- [ ] Retry 3 times on failure
- [ ] Errors logged in Logs/Errors/
- [ ] Audit_Agent notified
- [ ] System continues other tasks
- [ ] Graceful degradation when API down

---

## PHASE 11: WEEKLY CEO BRIEFING

- [ ] Reports/CEO_Weekly_Brief.md generated
- [ ] Includes total tasks completed
- [ ] Includes emails sent
- [ ] Includes social posts summary
- [ ] Includes sales summary
- [ ] Includes expenses summary
- [ ] Includes errors encountered
- [ ] Includes recommendations

---

## PHASE 12: TASK FLOW VERIFICATION

### Complete Workflow
- [ ] Watcher detects task
- [ ] Task in Needs_Action/
- [ ] Plan.md created in Plans/
- [ ] Approval checked (if sensitive)
- [ ] MCP Server executes
- [ ] Task moves to Done/
- [ ] Audit logs created
- [ ] Weekly CEO Brief includes task

### Verification
- [ ] All tasks end in Done/
- [ ] Plans exist for all tasks
- [ ] Logs exist for all actions
- [ ] Approval workflow respected
- [ ] Scheduler active

---

## TESTING COMMANDS

### Health Checks
```bash
curl http://localhost:5001/health
curl http://localhost:5002/health
curl http://localhost:5003/health
```

### Test Email
```bash
curl -X POST http://localhost:5001/api/email/send ^
  -H "Content-Type: application/json" ^
  -d "{\"to\":\"test@example.com\",\"subject\":\"Test\",\"body\":\"Hello\"}"
```

### Test LinkedIn Post
```bash
curl -X POST http://localhost:5002/api/social/post ^
  -H "Content-Type: application/json" ^
  -d "{\"platform\":\"linkedin\",\"content\":\"Test post! #AI\",\"hashtags\":[\"AI\"]}"
```

### Test Odoo Invoice
```bash
curl -X POST http://localhost:5003/api/odoo/action ^
  -H "Content-Type: application/json" ^
  -d "{\"action_type\":\"create_invoice\",\"data\":{\"client\":\"Test\",\"amount\":100}}"
```

---

## FINAL SYSTEM CHECK

### Bronze Tier Requirements
- [ ] Gmail/Inbox watcher operational
- [ ] Basic task management working
- [ ] Obsidian vault integration (if applicable)

### Silver Tier Requirements
- [ ] Two or more watchers (Gmail + WhatsApp + LinkedIn)
- [ ] MCP Server for external actions
- [ ] Human-in-the-loop approval
- [ ] Scheduler for automated tasks
- [ ] Claude reasoning loop with Plan.md

### Gold Tier Requirements
- [ ] Odoo Accounting integration
- [ ] Weekly CEO Briefing
- [ ] Full multi-domain workflow
- [ ] Error recovery and graceful degradation
- [ ] All AI functionality as Agent Skills

---

## SYSTEM STATUS

| Component | Status | Notes |
|-----------|--------|-------|
| Folders | | |
| Agents | | |
| Skills | | |
| Watchers | | |
| MCP Servers | | |
| Scheduler | | |
| ODOO | | |
| Error Recovery | | |
| CEO Briefing | | |
| Documentation | | |

**Overall System Status**: [ ] READY [ ] NEEDS WORK

---

*Gold Tier AI Employee System - Complete Verification Checklist*
