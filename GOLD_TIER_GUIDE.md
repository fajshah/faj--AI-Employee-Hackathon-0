# Gold Tier AI Employee System - Complete Guide

## System Overview

The Gold Tier AI Employee is an autonomous system that:
- Monitors Gmail, WhatsApp, and LinkedIn
- Creates tasks automatically
- Generates detailed plans using Claude reasoning
- Requires human approval for sensitive tasks
- Executes actions via MCP Server
- Integrates with Odoo for accounting
- Generates weekly CEO briefings

## Architecture

```
Watchers → Needs_Action → Orchestrator → Plans
                                    ↓
                            Approval Check
                                    ↓
                    ┌───────────────┴───────────────┐
                    │                               │
              Pending_Approval                  MCP Server
                    │                               │
              [Human Approval]              Gmail/LinkedIn/
                    │                       WhatsApp/Odoo
                    └───────────────┬───────────────┘
                                    ↓
                                Done/
```

## Setup Steps

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Edit `.env` with your API credentials.

### 3. Authenticate Gmail
```bash
python authenticate_gmail.py
```

### 4. Start System
```bash
python run_gold_tier.py
```

## Testing

### Test Email
```bash
curl -X POST http://localhost:5001/api/email/send \
  -H "Content-Type: application/json" \
  -d '{"to":"test@example.com","subject":"Test","body":"Hello"}'
```

### Test LinkedIn Post
```bash
curl -X POST http://localhost:5001/api/social/post \
  -H "Content-Type: application/json" \
  -d '{"platform":"linkedin","content":"Test post! #AI"}'
```

### Test Odoo Invoice
```bash
curl -X POST http://localhost:5001/api/odoo/action \
  -H "Content-Type: application/json" \
  -d '{"action_type":"create_invoice","data":{"client":"Test","amount":100}}'
```

## Troubleshooting

- Check Logs/ for errors
- Verify .env credentials
- Ensure MCP Server is running
- Check port 5001 is available
