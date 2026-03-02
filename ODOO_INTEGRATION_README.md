# Odoo ↔ AI Employee Integration
## Production-Ready Webhook Integration System

Complete integration between Odoo ERP and AI Employee automation system for automated customer communications.

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Features](#features)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Docker Networking](#docker-networking)
7. [Odoo Setup](#odoo-setup)
8. [Testing](#testing)
9. [Troubleshooting](#troubleshooting)
10. [API Reference](#api-reference)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ODOO ERP (Docker)                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │
│  │   CRM Lead  │  │ Sale Order  │  │   Invoice   │                     │
│  │  (Created)  │  │ (Confirmed) │  │  (Created)  │                     │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                     │
│         │                │                │                              │
│         └────────────────┴────────────────┘                              │
│                          │                                               │
│                          ▼                                               │
│              ┌───────────────────────┐                                  │
│              │   Automated Actions   │                                  │
│              │   (Python Code)       │                                  │
│              └───────────┬───────────┘                                  │
└──────────────────────────┼──────────────────────────────────────────────┘
                           │ HTTP POST Webhook
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    AI EMPLOYEE SYSTEM (Port 5050)                       │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Odoo Webhook Handler                          │   │
│  │  Route: /odoo_webhook (POST)                                    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                          │                                              │
│         ┌────────────────┼────────────────┐                            │
│         ▼                ▼                ▼                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                    │
│  │   Gmail     │  │  WhatsApp   │  │  LinkedIn   │                    │
│  │    API      │  │ Business API│  │    API      │                    │
│  └─────────────┘  └─────────────┘  └─────────────┘                    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      Event Processors                            │   │
│  │  • new_lead → WhatsApp + Email + LinkedIn Draft                 │   │
│  │  • sale_confirmed → Thank-you WhatsApp + LinkedIn Post          │   │
│  │  • invoice_created → Payment Email + WhatsApp Reminder          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

### Event Handling

| Event | Trigger | Actions |
|-------|---------|---------|
| `new_lead` | CRM Lead Created | WhatsApp greeting, Email follow-up, LinkedIn draft |
| `sale_confirmed` | Sale Order Confirmed | Thank-you WhatsApp, LinkedIn success story (optional) |
| `invoice_created` | Invoice Created | Payment reminder email, WhatsApp reminder (high-value) |

### Production Features

- ✅ **Secure Webhooks** - HMAC secret validation
- ✅ **Error Handling** - Comprehensive try/catch with logging
- ✅ **Retry Logic** - Automatic retry on transient failures
- ✅ **Structured Logging** - JSON logs with timestamps
- ✅ **Health Checks** - `/health` endpoint for monitoring
- ✅ **Docker Ready** - Complete Docker Compose configuration
- ✅ **SSL Support** - Nginx reverse proxy configuration

---

## 📦 Prerequisites

### Software Requirements

- Python 3.11+
- Docker & Docker Compose (optional)
- Odoo 16.0+ (running in Docker or locally)
- Node.js 18+ (for MCP Server)

### API Credentials

| Service | Required Credentials |
|---------|---------------------|
| Gmail | OAuth 2.0 Client ID, Client Secret, Token |
| WhatsApp Business | Access Token, Phone Number ID |
| LinkedIn | Access Token, Person ID |

---

## 🚀 Installation

### Option 1: Direct Python Installation

```bash
# 1. Install dependencies
pip install -r requirements-odoo.txt

# 2. Copy environment file
cp .env.example .env.gold

# 3. Edit .env.gold with your credentials
# Required variables:
#   ODOO_WEBHOOK_SECRET=your-secret-key
#   GMAIL_CLIENT_ID=your-client-id
#   WHATSAPP_ACCESS_TOKEN=your-token
#   LINKEDIN_ACCESS_TOKEN=your-token

# 4. Run the webhook handler
python odoo_webhook_handler.py
```

### Option 2: Docker Installation

```bash
# 1. Build and start containers
docker-compose -f docker-compose-odoo.yml up -d

# 2. View logs
docker-compose -f docker-compose-odoo.yml logs -f ai_employee_webhook

# 3. Check health
curl http://localhost:5050/health
```

---

## ⚙️ Configuration

### Environment Variables (.env.gold)

```bash
# ===========================================
# WEBHOOK CONFIGURATION
# ===========================================
ODOO_WEBHOOK_SECRET=change-this-to-secure-random-string
ODOO_WEBHOOK_PORT=5050

# ===========================================
# MCP SERVER
# ===========================================
MCP_SERVER_URL=http://localhost:5001

# ===========================================
# GMAIL API (OAuth 2.0)
# ===========================================
GMAIL_CLIENT_ID=your_gmail_client_id
GMAIL_CLIENT_SECRET=your_gmail_client_secret
GMAIL_TOKEN_FILE=tokens/gmail_token.json

# ===========================================
# WHATSAPP BUSINESS API
# ===========================================
WHATSAPP_ACCESS_TOKEN=your_whatsapp_token
WHATSAPP_PHONE_NUMBER_ID=+1234567890

# ===========================================
# LINKEDIN API
# ===========================================
LINKEDIN_ACCESS_TOKEN=your_linkedin_token
LINKEDIN_PERSON_ID=urn:li:person:YOUR_ID

# ===========================================
# LOGGING
# ===========================================
LOG_LEVEL=INFO
FLASK_DEBUG=false
```

### Generate Secure Webhook Secret

```bash
# Generate a secure random secret
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 🌐 Docker Networking

### Scenario 1: Odoo on Host, AI Employee in Docker

```yaml
# In docker-compose-odoo.yml
services:
  ai_employee_webhook:
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

**Odoo Webhook URL:** `http://host.docker.internal:5050/odoo_webhook`

### Scenario 2: Both in Same Docker Network

```yaml
# Add Odoo to the same network
networks:
  ai_employee_network:
    external: true
```

**Odoo Webhook URL:** `http://ai_employee_webhook:5050/odoo_webhook`

### Scenario 3: Production with SSL

```bash
# Using Nginx reverse proxy
# Webhook URL: https://your-domain.com/odoo_webhook
```

See `nginx/nginx.conf` for SSL configuration.

### Windows Firewall Rules

```powershell
# Run as Administrator

# Allow inbound webhook traffic
New-NetFirewallRule -DisplayName "AI Employee Webhook" `
    -Direction Inbound `
    -LocalPort 5050 `
    -Protocol TCP `
    -Action Allow

# Allow outbound to MCP Server
New-NetFirewallRule -DisplayName "AI Employee to MCP" `
    -Direction Outbound `
    -RemotePort 5001 `
    -Protocol TCP `
    -Action Allow
```

---

## 🔧 Odoo Setup

### Step 1: Enable Developer Mode

1. Go to **Settings**
2. Scroll to bottom
3. Click **Activate Developer Mode**

### Step 2: Create Automated Actions

Navigate to: **Settings → Technical → Automation → Automated Actions**

#### Action 1: New Lead Webhook

| Field | Value |
|-------|-------|
| Name | AI Employee: New Lead Webhook |
| Model | CRM Lead (crm.lead) |
| Trigger | On Creation |
| Action To Do | Execute Python Code |

**Python Code:**
```python
# Copy from odoo_automated_actions.py → on_lead_created()
```

#### Action 2: Sale Confirmed Webhook

| Field | Value |
|-------|-------|
| Name | AI Employee: Sale Confirmed Webhook |
| Model | Sales Order (sale.order) |
| Trigger | On Update |
| Trigger Fields | state |
| Domain | [('state', '=', 'sale')] |
| Action To Do | Execute Python Code |

**Python Code:**
```python
# Copy from odoo_automated_actions.py → on_sale_confirmed()
```

#### Action 3: Invoice Created Webhook

| Field | Value |
|-------|-------|
| Name | AI Employee: Invoice Created Webhook |
| Model | Invoice (account.move) |
| Trigger | On Creation |
| Domain | [('move_type', 'in', ['out_invoice', 'out_refund'])] |
| Action To Do | Execute Python Code |

**Python Code:**
```python
# Copy from odoo_automated_actions.py → on_invoice_created()
```

### Step 3: Configure Webhook URL

In each automated action's Python code, update:

```python
WEBHOOK_URL = "http://host.docker.internal:5050/odoo_webhook"
WEBHOOK_SECRET = "your-secret-key"  # Must match .env.gold
```

---

## 🧪 Testing

### Test Webhook Endpoint

```bash
# Health check
curl http://localhost:5050/health

# Expected response:
# {
#   "status": "healthy",
#   "service": "odoo_webhook_handler",
#   "version": "1.0.0"
# }
```

### Test with Sample Payload

```bash
# Test new_lead event
curl -X POST http://localhost:5050/odoo_webhook \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "new_lead",
    "secret": "your-secret-key",
    "data": {
      "id": "TEST001",
      "partner_name": "Test Company",
      "contact_name": "John Doe",
      "email": "john@example.com",
      "phone": "+1234567890",
      "opportunity_type": "Service Inquiry",
      "priority": "High",
      "expected_revenue": 5000
    }
  }'
```

### Test Sale Confirmed

```bash
curl -X POST http://localhost:5050/odoo_webhook \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "sale_confirmed",
    "secret": "your-secret-key",
    "data": {
      "id": "SO001",
      "name": "S0001",
      "partner_name": "Test Customer",
      "partner_email": "customer@example.com",
      "partner_phone": "+1234567890",
      "amount_total": 1500.00,
      "currency": "USD",
      "order_lines": [
        {"name": "Product A", "quantity": 2, "price_unit": 750}
      ]
    }
  }'
```

### Test Invoice Created

```bash
curl -X POST http://localhost:5050/odoo_webhook \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "invoice_created",
    "secret": "your-secret-key",
    "data": {
      "id": "INV001",
      "number": "INV/2024/001",
      "partner_name": "Test Customer",
      "partner_email": "customer@example.com",
      "amount_total": 1500.00,
      "amount_due": 1500.00,
      "currency": "USD",
      "invoice_date_due": "2024-04-01",
      "payment_state": "not_paid"
    }
  }'
```

---

## 🔍 Troubleshooting

### Webhook Not Receiving Events

```bash
# 1. Check if webhook handler is running
curl http://localhost:5050/health

# 2. Check logs
docker-compose logs ai_employee_webhook

# 3. Verify firewall rules
netstat -an | findstr 5050

# 4. Test network connectivity
ping host.docker.internal
```

### Authentication Errors

| Error | Solution |
|-------|----------|
| Invalid webhook secret | Verify `WEBHOOK_SECRET` matches in Odoo and .env.gold |
| Gmail API error | Run `python authenticate_gmail.py` to refresh token |
| WhatsApp API error | Check access token validity in Meta Developer Portal |
| LinkedIn API error | Verify token hasn't expired (60-day validity) |

### Docker Networking Issues

```bash
# Check container network
docker network inspect ai_employee_network

# Test connectivity from container
docker exec -it ai_employee_webhook ping host.docker.internal

# Restart network
docker-compose down
docker network prune
docker-compose up -d
```

### Log Analysis

```bash
# View recent errors
docker-compose logs ai_employee_webhook | grep ERROR

# View event processing
docker-compose logs ai_employee_webhook | grep "Processing"

# Export logs
docker-compose logs ai_employee_webhook > webhook_logs.txt
```

---

## 📖 API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/odoo_webhook` | Main webhook endpoint |
| GET | `/api/status` | API status and configuration |

### Webhook Payload Structure

```json
{
  "event_type": "new_lead | sale_confirmed | invoice_created",
  "secret": "your-webhook-secret",
  "data": {
    // Event-specific data
  }
}
```

### Response Format

**Success:**
```json
{
  "status": "success",
  "event_type": "new_lead",
  "lead_id": "123",
  "timestamp": "2024-01-15T10:30:00",
  "actions": {
    "whatsapp": {"status": "success", "message_id": "msg_123"},
    "email": {"status": "success", "message_id": "msg_456"},
    "linkedin": {"status": "draft_created", "file": "path/to/draft"}
  }
}
```

**Error:**
```json
{
  "status": "error",
  "error": "Error description"
}
```

---

## 📁 File Structure

```
hackthone-0/
├── odoo_webhook_handler.py      # Main webhook handler
├── odoo_automated_actions.py    # Odoo server-side code
├── docker-compose-odoo.yml      # Docker configuration
├── Dockerfile.webhook           # Webhook container
├── requirements-odoo.txt        # Python dependencies
├── ODOO_INTEGRATION_README.md   # This documentation
├── .env.gold                    # Environment configuration
├── Logs/                        # Application logs
│   └── odoo_webhook.log
├── tokens/                      # API tokens
│   └── gmail_token.json
└── LinkedIn_Drafts/             # LinkedIn draft posts
```

---

## 🔐 Security Considerations

1. **Webhook Secret**: Use a strong, randomly generated secret
2. **HTTPS**: Use SSL/TLS in production (see nginx configuration)
3. **Firewall**: Restrict access to webhook port
4. **Token Storage**: Store API tokens securely, not in code
5. **Rate Limiting**: Implement rate limiting for production use
6. **Input Validation**: All incoming data is validated

---

## 📞 Support

For issues or questions:

1. Check logs in `Logs/odoo_webhook.log`
2. Review troubleshooting section above
3. Verify all API credentials are valid
4. Test with curl commands before Odoo integration

---

## 📄 License

Internal use only - Company Proprietary
