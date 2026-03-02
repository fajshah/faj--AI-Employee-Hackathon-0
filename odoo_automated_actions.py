"""
Odoo Automated Actions - Server-Side Python Code
=================================================
This code is to be used in Odoo's Automated Actions (Settings → Technical → Automation → Automated Actions)

Setup Instructions:
1. Enable Developer Mode in Odoo (Settings → Activate Developer Mode)
2. Go to Settings → Technical → Automation → Automated Actions
3. Create new actions for each event type
4. Copy the corresponding Python code below

Events Covered:
- CRM Lead Creation → new_lead webhook
- Sale Order Confirmation → sale_confirmed webhook
- Invoice Creation → invoice_created webhook
"""

# ===========================================
# CONFIGURATION - Update these values
# ===========================================

WEBHOOK_URL = "http://host.docker.internal:5050/odoo_webhook"  # Use host.docker.internal for Docker networking
WEBHOOK_SECRET = "change-this-in-production"  # Must match ODOO_WEBHOOK_SECRET in .env.gold

# ===========================================
# UTILITY FUNCTIONS
# ===========================================

def send_webhook(event_type, record_data, env):
    """
    Send webhook to AI Employee system
    
    Args:
        event_type: Type of event (new_lead, sale_confirmed, invoice_created)
        record_data: Dictionary containing record data
        env: Odoo environment
    
    Returns:
        dict: Response from webhook handler
    """
    import urllib.request
    import urllib.error
    import json
    import logging
    
    _logger = logging.getLogger(__name__)
    
    payload = {
        "event_type": event_type,
        "secret": WEBHOOK_SECRET,
        "data": record_data
    }
    
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Odoo-Automation/1.0'
    }
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(WEBHOOK_URL, data=data, headers=headers, method='POST')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            _logger.info(f"Webhook sent successfully for {event_type}: {result}")
            return result
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else str(e)
        _logger.error(f"HTTP Error sending webhook: {e.code} - {error_body}")
        return {"status": "error", "http_code": e.code, "error": error_body}
        
    except urllib.error.URLError as e:
        _logger.error(f"URL Error sending webhook: {str(e.reason)}")
        return {"status": "error", "error": str(e.reason)}
        
    except Exception as e:
        _logger.error(f"Error sending webhook: {str(e)}")
        return {"status": "error", "error": str(e)}


def get_base_url(env):
    """Get the Odoo base URL for generating record links"""
    return env['ir.config_parameter'].sudo().get_param('web.base.url')


# ===========================================
# EVENT 1: NEW LEAD (CRM)
# ===========================================
# Automated Action Configuration:
# - Model: crm.lead
# - Trigger: On Creation
# - Action To Do: Execute Python Code
# - Copy the code below into the Python Code field

def on_lead_created():
    """
    Triggered when a new CRM lead is created.
    Sends lead data to AI Employee webhook.
    """
    import logging
    _logger = logging.getLogger(__name__)
    
    # 'record' is automatically provided by Odoo's automated action context
    if not record:
        _logger.warning("No record provided to webhook handler")
        return
    
    base_url = get_base_url(env)
    
    # Build lead data payload
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
    
    # Send webhook
    result = send_webhook("new_lead", lead_data, env)
    
    # Optionally log result on the lead
    if result.get('status') == 'success':
        record.message_post(body=f"✅ AI Employee notified: Lead data sent to automation system")
    else:
        record.message_post(body=f"⚠️ AI Employee notification failed: {result.get('error', 'Unknown error')}")
    
    return result


# ===========================================
# EVENT 2: SALE ORDER CONFIRMED
# ===========================================
# Automated Action Configuration:
# - Model: sale.order
# - Trigger: On Update
# - Update Fields: state
# - Additional Domain: [('state', '=', 'sale')]
# - Action To Do: Execute Python Code

def on_sale_confirmed():
    """
    Triggered when a sale order is confirmed.
    Sends sale data to AI Employee webhook.
    """
    import logging
    _logger = logging.getLogger(__name__)
    
    if not record:
        _logger.warning("No record provided to webhook handler")
        return
    
    # Only trigger on confirmed sales
    if record.state != 'sale':
        return
    
    base_url = get_base_url(env)
    
    # Build order lines data
    order_lines = []
    for line in record.order_line:
        order_lines.append({
            "product_id": line.product_id.id,
            "name": line.product_id.name or line.name,
            "quantity": line.product_uom_qty,
            "price_unit": line.price_unit,
            "subtotal": line.price_subtotal
        })
    
    # Build sale data payload
    sale_data = {
        "id": record.id,
        "name": record.name or "",
        "partner_name": record.partner_id.name if record.partner_id else "",
        "partner_email": record.partner_id.email if record.partner_id else "",
        "partner_phone": record.partner_id.phone if record.partner_id else "",
        "company_name": record.company_id.name if record.company_id else "",
        "amount_total": record.amount_total or 0,
        "currency": record.currency_id.name if record.currency_id else "USD",
        "payment_state": record.payment_state if hasattr(record, 'payment_state') else "pending",
        "date_order": record.date_order.isoformat() if record.date_order else "",
        "expected_date": record.expected_date.isoformat() if record.expected_date else "",
        "order_lines": order_lines,
        "salesperson": record.user_id.name if record.user_id else "",
        "post_linkedin": True,  # Set to False to skip LinkedIn posting for this sale
        "odoo_url": f"{base_url}/web#id={record.id}&model=sale.order&view_type=form"
    }
    
    # Send webhook
    result = send_webhook("sale_confirmed", sale_data, env)
    
    # Log result on the sale order
    if result.get('status') == 'success':
        record.message_post(body=f"✅ AI Employee notified: Sale confirmation sent to automation system")
    else:
        record.message_post(body=f"⚠️ AI Employee notification failed: {result.get('error', 'Unknown error')}")
    
    return result


# ===========================================
# EVENT 3: INVOICE CREATED
# ===========================================
# Automated Action Configuration:
# - Model: account.move
# - Trigger: On Creation
# - Additional Domain: [('move_type', 'in', ['out_invoice', 'out_refund'])]
# - Action To Do: Execute Python Code

def on_invoice_created():
    """
    Triggered when a new customer invoice is created.
    Sends invoice data to AI Employee webhook.
    """
    import logging
    _logger = logging.getLogger(__name__)
    
    if not record:
        _logger.warning("No record provided to webhook handler")
        return
    
    # Only process customer invoices
    if record.move_type not in ['out_invoice', 'out_refund']:
        return
    
    base_url = get_base_url(env)
    
    # Build invoice data payload
    invoice_data = {
        "id": record.id,
        "number": record.name or record.invoice_origin or "",
        "partner_name": record.partner_id.name if record.partner_id else "",
        "partner_email": record.partner_id.email if record.partner_id else "",
        "partner_phone": record.partner_id.phone if record.partner_id else "",
        "company_name": record.company_id.name if record.company_id else "",
        "amount_total": record.amount_total or 0,
        "amount_due": record.amount_residual or 0,
        "currency": record.currency_id.name if record.currency_id else "USD",
        "invoice_date_due": record.invoice_date_due.isoformat() if record.invoice_date_due else "",
        "invoice_date": record.invoice_date.isoformat() if record.invoice_date else "",
        "payment_state": record.payment_state or "not_paid",
        "odoo_url": f"{base_url}/web#id={record.id}&model=account.move&view_type=form"
    }
    
    # Send webhook
    result = send_webhook("invoice_created", invoice_data, env)
    
    # Log result on the invoice
    if result.get('status') == 'success':
        record.message_post(body=f"✅ AI Employee notified: Invoice data sent to automation system")
    else:
        record.message_post(body=f"⚠️ AI Employee notification failed: {result.get('error', 'Unknown error')}")
    
    return result


# ===========================================
# EVENT 4: PAYMENT RECEIVED (Bonus)
# ===========================================
# Automated Action Configuration:
# - Model: account.payment
# - Trigger: On Creation
# - Action To Do: Execute Python Code

def on_payment_received():
    """
    Triggered when a payment is received.
    Sends payment notification to AI Employee webhook.
    """
    import logging
    _logger = logging.getLogger(__name__)
    
    if not record:
        _logger.warning("No record provided to webhook handler")
        return
    
    base_url = get_base_url(env)
    
    # Build payment data payload
    payment_data = {
        "id": record.id,
        "name": record.name or "",
        "partner_name": record.partner_id.name if record.partner_id else "",
        "partner_email": record.partner_id.email if record.partner_id else "",
        "amount": record.amount or 0,
        "currency": record.currency_id.name if record.currency_id else "USD",
        "payment_date": record.date.isoformat() if record.date else "",
        "payment_type": record.payment_type or "",
        "payment_method": record.payment_method_line_id.name if record.payment_method_line_id else "",
        "odoo_url": f"{base_url}/web#id={record.id}&model=account.payment&view_type=form"
    }
    
    # Send webhook with custom event type
    result = send_webhook("payment_received", payment_data, env)
    
    return result


# ===========================================
# SETUP SCRIPT - Run once to create automated actions
# ===========================================
# Run this in Odoo's Python console or as a server action
# Settings → Technical → Automation → Server Actions → Create → Execute Python Code

def setup_automated_actions():
    """
    Create automated actions for Odoo webhook integration.
    Run this once to set up all required automated actions.
    """
    _logger = logging.getLogger(__name__)
    Actions = env['ir.actions.server']
    
    # Get the Python code for each action
    lead_code = """
# New Lead Webhook
record = record  # Provided by Odoo
result = on_lead_created()
"""
    
    sale_code = """
# Sale Confirmed Webhook
record = record  # Provided by Odoo
result = on_sale_confirmed()
"""
    
    invoice_code = """
# Invoice Created Webhook
record = record  # Provided by Odoo
result = on_invoice_created()
"""
    
    # Create automated actions
    actions_data = [
        {
            "name": "AI Employee: New Lead Webhook",
            "model_id": env.ref('crm.model_crm_lead').id,
            "state": 'code',
            "code": lead_code,
            "trigger": 'on_create',
        },
        {
            "name": "AI Employee: Sale Confirmed Webhook",
            "model_id": env.ref('sale.model_sale_order').id,
            "state": 'code',
            "code": sale_code,
            "trigger": 'on_write',
            "trigger_field_ids": [(6, 0, [env.ref('sale.field_sale_order__state').id])],
        },
        {
            "name": "AI Employee: Invoice Created Webhook",
            "model_id": env.ref('account.model_account_move').id,
            "state": 'code',
            "code": invoice_code,
            "trigger": 'on_create',
        },
    ]
    
    created_actions = []
    for action_data in actions_data:
        try:
            action = Actions.create(action_data)
            created_actions.append(action.name)
            _logger.info(f"Created automated action: {action.name}")
        except Exception as e:
            _logger.error(f"Failed to create action {action_data['name']}: {str(e)}")
    
    return {
        "status": "success",
        "created_actions": created_actions,
        "message": f"Created {len(created_actions)} automated actions"
    }
