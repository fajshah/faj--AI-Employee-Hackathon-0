# Gold Tier AI Employee System - Quick Start

## Start All Components

### Terminal 1 - MCP Comms Server
```bash
python MCP_Servers/MCP_Comms_Server.py
```

### Terminal 2 - MCP Social Server
```bash
python MCP_Servers/MCP_Social_Server.py
```

### Terminal 3 - MCP Finance Server
```bash
python MCP_Servers/MCP_Finance_Server.py
```

### Terminal 4 - Orchestrator
```bash
python Agents/Orchestrator_Agent.py
```

### Terminal 5 - Scheduler
```bash
python Scheduler/Gold_Tier_Scheduler.py
```

### Terminal 6 - Watchers
```bash
python Gmail_Watcher.py
python WhatsApp_Watcher.py
python LinkedIn_Watcher.py
```

## Test System

```bash
curl http://localhost:5001/health
curl http://localhost:5002/health
curl http://localhost:5003/health
```

## Test Email
```bash
curl -X POST http://localhost:5001/api/email/send \
  -H "Content-Type: application/json" \
  -d '{"to":"test@example.com","subject":"Test","body":"Hello"}'
```

## Test Social Post
```bash
curl -X POST http://localhost:5002/api/social/post \
  -H "Content-Type: application/json" \
  -d '{"platform":"linkedin","content":"Test post! #AI"}'
```

## Test Odoo
```bash
curl -X POST http://localhost:5003/api/odoo/action \
  -H "Content-Type: application/json" \
  -d '{"action_type":"create_invoice","data":{"client":"Test","amount":100}}'
```
