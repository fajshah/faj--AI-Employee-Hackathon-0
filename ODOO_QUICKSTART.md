# 🚀 Quick Start: Odoo ↔ AI Employee Integration

## Option 1: Standalone Version (Recommended - No MCP Server Required)

### Step 1: Install Dependencies

```bash
pip install -r requirements-odoo.txt
```

### Step 2: Configure Environment

Edit `.env.gold` and set:

```bash
# Webhook Security (generate a secure secret)
ODOO_WEBHOOK_SECRET=your-secure-random-string-here
ODOO_WEBHOOK_PORT=5050

# Gmail (OAuth or SMTP)
GMAIL_CLIENT_ID=your-client-id
GMAIL_CLIENT_SECRET=your-client-secret
GMAIL_TOKEN_FILE=tokens/gmail_token.json

# OR SMTP Fallback
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# WhatsApp Business API
WHATSAPP_ACCESS_TOKEN=your-whatsapp-token
WHATSAPP_PHONE_NUMBER_ID=+1234567890

# LinkedIn API
LINKEDIN_ACCESS_TOKEN=your-linkedin-token
LINKEDIN_PERSON_ID=urn:li:person:YOUR_ID
```

### Step 3: Authenticate Gmail (First Time Only)

```bash
python authenticate_gmail.py
```

### Step 4: Run the Standalone Webhook Handler

```bash
python odoo_webhook_standalone.py
```

### Step 5: Test the Integration

```bash
python test_odoo_webhook.py
```

---

## Option 2: Docker Deployment

### Build and Run

```bash
docker-compose -f docker-compose-odoo.yml up -d
```

### View Logs

```bash
docker-compose logs -f ai_employee_webhook
```

### Health Check

```bash
curl http://localhost:5050/health
```

---

## Odoo Configuration

### 1. Enable Developer Mode

- Go to **Settings**
- Scroll to bottom
- Click **Activate Developer Mode**

### 2. Create Automated Actions

Navigate to: **Settings → Technical → Automation → Automated Actions**

#### Action 1: New Lead (CRM)

| Field | Value |
|-------|-------|
| Name | AI Employee: New Lead Webhook |
| Model | CRM Lead (crm.lead) |
| Trigger | On Creation |
| Action To Do | Execute Python Code |

**Python Code:**
```python
WEBHOOK_URL = "http://host.docker.internal:5050/odoo_webhook"
WEBHOOK_SECRET = "your-secure-random-string-here"

import urllib.request, urllib.error, json, logging
_logger = logging.getLogger(__name__)

if not record:
    _logger.warning("No record provided")
    return

base_url = env['ir.config_parameter'].sudo().get_param('web.base.url')

lead_data = {
    "id": record.id,
    "partner_name": record.partner_name or "",
    "contact_name": record.contact_name or (record.partner_id.name if record.partner_id else ""),
    "email": record.email_from or (record.partner_id.email if record.partner_id else ""),
    "phone": record.phone or (record.partner_id.phone if record.partner_id else ""),
    "company_name": record.partner_id.name if record.partner_id else "",
    "opportunity_type": record.type if record.type else "",
    "priority": record.priority or "Normal",
    "stage": record.stage_id.name if record.stage_id else "New",
    "expected_revenue": record.expected_revenue or 0,
    "description": record.description or "",
    "source": record.source_id.name if record.source_id else "Direct",
    "tags": [tag.name for tag in record.tag_ids] if record.tag_ids else [],
    "created_at": record.create_date.isoformat(),
    "odoo_url": f"{base_url}/web#id={record.id}&model=crm.lead&view_type=form"
}

payload = {"event_type": "new_lead", "secret": WEBHOOK_SECRET, "data": lead_data}
headers = {'Content-Type': 'application/json', 'User-Agent': 'Odoo-Automation/1.0'}

try:
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(WEBHOOK_URL, data=data, headers=headers, method='POST')
    with urllib.request.urlopen(req, timeout=30) as response:
        result = json.loads(response.read().decode('utf-8'))
        record.message_post(body=f"✅ AI Employee notified")
except Exception as e:
    record.message_post(body=f"⚠️ Webhook failed: {str(e)}")
```

#### Action 2: Sale Confirmed

| Field | Value |
|-------|-------|
| Name | AI Employee: Sale Confirmed Webhook |
| Model | Sales Order (sale.order) |
| Trigger | On Update |
| Trigger Fields | state |
| Domain | [('state', '=', 'sale')] |
| Action To Do | Execute Python Code |

**Use the same code pattern, change event_type to "sale_confirmed"**

#### Action 3: Invoice Created

| Field | Value |
|-------|-------|
| Name | AI Employee: Invoice Created Webhook |
| Model | Invoice (account.move) |
| Trigger | On Creation |
| Domain | [('move_type', 'in', ['out_invoice', 'out_refund'])] |
| Action To Do | Execute Python Code |

**Use the same code pattern, change event_type to "invoice_created"**

---

## Testing

### Test Health

```bash
curl http://localhost:5050/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "odoo_webhook_standalone",
  "services": {
    "gmail": "enabled",
    "whatsapp": "enabled",
    "linkedin": "enabled"
  }
}
```

### Test new_lead Event

```bash
curl -X POST http://localhost:5050/odoo_webhook \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "new_lead",
    "secret": "your-secure-random-string-here",
    "data": {
      "id": "TEST001",
      "contact_name": "John Doe",
      "email": "john@example.com",
      "phone": "+1234567890",
      "company_name": "Test Company",
      "opportunity_type": "Service Inquiry"
    }
  }'
```

### Check Logs

```bash
# View webhook logs
tail -f Logs/odoo_webhook_standalone.log

# View event logs
ls -la Logs/odoo_events/
```

---

## Troubleshooting

### Connection Refused on Port 5001

**Problem:** Webhook handler tries to connect to MCP Server that isn't running.

**Solution:** Use the standalone version instead:
```bash
python odoo_webhook_standalone.py
```

### Gmail Authentication Failed

**Problem:** Token expired or not configured.

**Solution:**
```bash
python authenticate_gmail.py
```

### Webhook Secret Mismatch

**Problem:** 401 Unauthorized response.

**Solution:** Ensure `WEBHOOK_SECRET` in `.env.gold` matches the secret in Odoo automated actions.

### Docker Networking Issues

**Problem:** Odoo can't reach webhook handler.

**Solution:**
- For Odoo on host: Use `http://host.docker.internal:5050`
- For Odoo in Docker: Add both to same network, use service name

### WhatsApp/LinkedIn Not Sending

**Problem:** API tokens not configured or expired.

**Solution:**
1. Check tokens in `.env.gold`
2. Verify tokens are valid in Meta/LinkedIn developer portals
3. Check logs for specific error messages

---

## File Structure

```
hackthone-0/
├── odoo_webhook_standalone.py   # Standalone webhook handler (RECOMMENDED)
├── odoo_webhook_handler.py      # MCP Server dependent version
├── odoo_automated_actions.py    # Odoo Python code templates
├── test_odoo_webhook.py         # Test suite
├── requirements-odoo.txt        # Dependencies
├── docker-compose-odoo.yml      # Docker config
├── .env.gold                    # Environment config
├── Logs/
│   ├── odoo_webhook_standalone.log
│   └── odoo_events/             # Event logs
└── LinkedIn_Drafts/             # Draft posts
```

---

## Production Checklist

- [ ] Set secure `ODOO_WEBHOOK_SECRET` (32+ random characters)
- [ ] Enable HTTPS (use nginx reverse proxy)
- [ ] Configure firewall rules (allow port 5050)
- [ ] Set up log rotation
- [ ] Configure monitoring/alerting
- [ ] Backup API tokens securely
- [ ] Test all event types in production-like environment
- [ ] Document webhook URLs and credentials

---

## Next Steps

1. **Run the standalone handler:** `python odoo_webhook_standalone.py`
2. **Test with curl:** Verify all endpoints work
3. **Configure Odoo:** Set up automated actions
4. **Monitor logs:** Check `Logs/odoo_webhook_standalone.log`
5. **Go live:** Deploy to production server

For full documentation, see `ODOO_INTEGRATION_README.md`.
