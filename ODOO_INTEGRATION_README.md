# Odoo Integration - Complete Guide

## Overview

This module provides comprehensive Odoo ERP integration with:
- **OdooClient**: Reusable XML-RPC client with error handling and validation
- **OdooSkills**: High-level skills for AI agent integration
- **FinanceAgent**: Task-based finance agent for autonomous operations

## Features

### Core Capabilities
- ✅ Connection management with automatic reconnection
- ✅ Comprehensive error handling and validation
- ✅ Full CRUD operations (Create, Read, Update, Delete, Search)
- ✅ Invoice creation and management
- ✅ Vendor bill processing
- ✅ Employee expense tracking
- ✅ Payment processing (customer & vendor)
- ✅ Journal entry creation
- ✅ Financial reporting (A/R, A/P)
- ✅ Data export (JSON, CSV)
- ✅ Context manager support

### Supported Odoo Models
- `account.move` (Invoices, Bills, Journal Entries)
- `account.payment` (Payments)
- `hr.expense` (Expenses)
- `res.partner` (Customers, Vendors)
- `product.product` (Products)
- And any custom model via generic CRUD

## Quick Start

### 1. Configure Environment

Add your Odoo credentials to `.env`:

```env
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USER=admin
ODOO_PASSWORD=admin
```

### 2. Test Connection

```bash
# Run the demo
python odoo_demo.py

# Run unit tests
python test_odoo_integration.py
```

### 3. Basic Usage

```python
from utils.odoo_client import get_odoo_client

# Get client and connect
client = get_odoo_client()
client.connect()

# Create an invoice
invoice_id = client.create_invoice(
    partner_id=1,
    invoice_type='out_invoice',
    lines=[
        {'name': 'Consulting Services', 'quantity': 10, 'price_unit': 150}
    ],
    invoice_date='2026-02-19'
)

# Post the invoice
client.post_invoice(invoice_id)

# Disconnect
client.disconnect()
```

### 4. Using Context Manager

```python
from utils.odoo_client import get_odoo_client

with get_odoo_client() as client:
    # Automatically connects
    invoice_id = client.create_invoice(...)
    # Automatically disconnects on exit
```

## API Reference

### OdooClient

#### Initialization

```python
client = OdooClient(
    url="http://localhost:8069",
    db="odoo",
    username="admin",
    password="admin",
    api_key=None,  # Optional
    timeout=30
)
```

#### Connection Methods

```python
client.connect()           # Connect to Odoo
client.disconnect()        # Disconnect
client.check_connection()  # Check if connected
client.get_server_version() # Get Odoo version
```

#### Generic CRUD

```python
# Create
id = client.create('res.partner', {'name': 'Customer', 'email': 'test@example.com'})

# Read
records = client.read('res.partner', [1, 2, 3])

# Update
client.update('res.partner', [1], {'phone': '+1-555-0100'})

# Delete
client.delete('res.partner', [1])

# Search
ids = client.search('res.partner', [('name', 'ilike', 'Acme')], limit=10)

# Search & Read
records = client.search_read(
    'res.partner',
    [('name', 'ilike', 'Acme')],
    fields=['id', 'name', 'email'],
    limit=10
)
```

#### Invoice Operations

```python
# Create customer invoice
invoice_id = client.create_invoice(
    partner_id=1,
    invoice_type='out_invoice',  # or 'in_invoice', 'out_refund', 'in_refund'
    lines=[
        {'name': 'Product', 'quantity': 2, 'price_unit': 100, 'product_id': 5}
    ],
    invoice_date='2026-02-19',
    invoice_date_due='2026-03-19',
    payment_reference='INV-2026-001'
)

# Get invoice
invoice = client.get_invoice(invoice_id)

# Get multiple invoices
invoices = client.get_invoices(
    partner_id=1,
    state='posted',
    date_from='2026-01-01'
)

# Post invoice
client.post_invoice(invoice_id)

# Cancel invoice
client.cancel_invoice(invoice_id)

# Register payment
payment_id = client.register_invoice_payment(
    invoice_id=invoice_id,
    amount=1000,
    payment_date='2026-02-19'
)

# Delete invoice (draft only)
client.delete_invoice(invoice_id)
```

#### Expense Operations

```python
# Create expense
expense_id = client.create_expense(
    employee_id=1,
    product_id=2,
    name="Travel Expense",
    unit_amount=350.00,
    quantity=1,
    date='2026-02-19'
)

# Get expenses
expenses = client.get_expenses(
    employee_id=1,
    state='reported',
    limit=50
)

# Submit for approval
client.submit_expenses([1, 2, 3])

# Approve expenses
client.approve_expenses([1, 2, 3])

# Post expenses
client.post_expenses([1, 2, 3])
```

#### Payment Operations

```python
# Create payment
payment_id = client.create_payment(
    partner_id=1,
    amount=1000,
    payment_type='outbound',  # or 'inbound'
    payment_date='2026-02-19',
    payment_reference='PAY-001'
)

# Get payments
payments = client.get_payments(
    partner_id=1,
    state='posted',
    limit=50
)
```

#### Journal Entry Operations

```python
# Create journal entry
entry_id = client.create_journal_entry(
    name="Monthly Depreciation",
    date='2026-02-19',
    lines=[
        {'account_id': 10, 'debit': 1000, 'credit': 0, 'name': 'Depreciation'},
        {'account_id': 20, 'debit': 0, 'credit': 1000, 'name': 'Accumulated Depreciation'}
    ],
    journal_id=1,
    ref='DEPR-001'
)

# Get journal entries
entries = client.get_journal_entries(
    date_from='2026-01-01',
    state='posted',
    limit=100
)

# Post journal entry
client.post_journal_entry(entry_id)

# Reverse journal entry
reversal_id = client.reverse_journal_entry(entry_id, date='2026-02-20')
```

#### Partner Operations

```python
# Get partner
partner = client.get_partner(partner_id)

# Search partners
partners = client.search_partners(
    name='Acme',
    email='@acme.com',
    customer=True,
    limit=10
)

# Create partner
partner_id = client.create_partner(
    name='New Customer',
    email='contact@example.com',
    phone='+1-555-0100',
    city='New York',
    customer=True,
    supplier=False
)
```

#### Product Operations

```python
# Get product
product = client.get_product(product_id)

# Search products
products = client.search_products(
    name='Widget',
    default_code='WID-',
    limit=10
)
```

#### Data Export

```python
# Export to JSON
client.export_data(
    model='res.partner',
    ids=[1, 2, 3],
    fields=['id', 'name', 'email'],
    output_file='exports/partners.json',
    format='json'
)

# Export to CSV
client.export_data(
    model='res.partner',
    ids=[1, 2, 3],
    fields=['id', 'name', 'email'],
    output_file='exports/partners.csv',
    format='csv'
)
```

### OdooSkills

High-level skills for AI agent integration:

```python
from Skills.odoo_skills import OdooSkills

skills = OdooSkills()  # Auto-creates client
# Or
skills = OdooSkills(client)  # Use existing client

# Invoice skills
result = skills.create_customer_invoice(
    customer_name="Acme Corp",
    items=[{'name': 'Service', 'quantity': 1, 'price_unit': 1000}]
)

result = skills.create_vendor_bill(
    vendor_name="Office Supplies",
    items=[{'name': 'Chairs', 'quantity': 5, 'price_unit': 200}]
)

result = skills.post_invoice(invoice_id)

result = skills.register_payment(
    invoice_id=invoice_id,
    amount=1000
)

# Expense skills
result = skills.create_employee_expense(
    employee_id=1,
    expense_type="Travel",
    amount=350,
    description="Client meeting"
)

result = skills.submit_expense_report([1, 2, 3])

# Payment skills
result = skills.make_vendor_payment(
    vendor_name="Supplier Inc",
    amount=5000
)

result = skills.record_customer_payment(
    customer_name="Acme Corp",
    amount=10000
)

# Journal entry skills
result = skills.create_journal_entry(
    name="Adjustment Entry",
    date='2026-02-19',
    lines=[
        {'account_id': 10, 'debit': 500, 'credit': 0},
        {'account_id': 20, 'debit': 0, 'credit': 500}
    ]
)

# Report skills
result = skills.get_accounts_receivable()
result = skills.get_accounts_payable()
result = skills.get_journal_entries(date_from='2026-01-01')

# Partner skills
result = skills.find_customer("Acme")
result = skills.create_customer(
    name="New Customer",
    email='contact@example.com'
)

# Utility skills
result = skills.check_connection()
result = skills.get_system_info()
```

### FinanceAgent

Task-based agent for autonomous operations:

```python
from Agents.Finance_Agent import FinanceAgent

# Use as context manager
with FinanceAgent() as agent:
    # Create invoice task
    task = {
        'action_type': 'create_invoice',
        'customer_name': 'Acme Corp',
        'items': [
            {'name': 'Consulting', 'quantity': 10, 'price_unit': 150}
        ],
        'invoice_date': '2026-02-19'
    }
    success = agent.execute_task(task)
    
    # Log expense task
    task = {
        'action_type': 'log_expense',
        'employee_id': 1,
        'expense_type': 'Travel',
        'amount': 350,
        'description': 'Client meeting'
    }
    success = agent.execute_task(task)
    
    # Generate report task
    task = {
        'action_type': 'generate_report',
        'report_type': 'receivables'
    }
    success = agent.execute_task(task)
    report = task.get('result')
```

#### Supported Task Types

| Action Type | Parameters |
|-------------|------------|
| `create_invoice` | customer_name, customer_id, items, invoice_date, due_date |
| `create_vendor_bill` | vendor_name, vendor_id, items, bill_date, due_date |
| `log_expense` | employee_id, expense_type, amount, description, date |
| `submit_expenses` | expense_ids |
| `register_payment` | invoice_id, amount, payment_date, payment_reference |
| `create_journal_entry` | name, date, lines, journal_id, reference |
| `post_invoice` | invoice_id |
| `get_invoices` | customer_id, customer_name, state, limit |
| `get_expenses` | employee_id, state, limit |
| `generate_report` | report_type, date_from, date_to |
| `find_customer` | search_term |
| `create_customer` | name, email, phone, city |

## Error Handling

All operations include comprehensive error handling:

```python
from utils.odoo_client import (
    OdooClientError,
    OdooAuthenticationError,
    OdooOperationError,
    OdooValidationError
)

try:
    client = get_odoo_client()
    client.connect()
    invoice_id = client.create_invoice(...)
except OdooAuthenticationError as e:
    print(f"Authentication failed: {e}")
except OdooValidationError as e:
    print(f"Validation error: {e}")
except OdooOperationError as e:
    print(f"Operation failed: {e}")
except OdooClientError as e:
    print(f"Client error: {e}")
```

## Testing

### Run Unit Tests

```bash
python test_odoo_integration.py
```

### Run Full Demo

```bash
python odoo_demo.py
```

## File Structure

```
D:\hackthone-0\
├── utils\
│   └── odoo_client.py       # Core Odoo client
├── Skills\
│   └── odoo_skills.py       # High-level skills
├── Agents\
│   └── Finance_Agent.py     # Finance agent
├── odoo_demo.py             # Demo script
├── test_odoo_integration.py # Test suite
└── ODOO_INTEGRATION_README.md  # This file
```

## Examples

### Complete Invoice Workflow

```python
from utils.odoo_client import get_odoo_client

with get_odoo_client() as client:
    # 1. Create or find customer
    partners = client.search_partners(name="Acme Corp")
    if not partners:
        customer_id = client.create_partner(
            name="Acme Corp",
            email="billing@acme.com",
            customer=True
        )
    else:
        customer_id = partners[0]['id']
    
    # 2. Create invoice
    invoice_id = client.create_invoice(
        partner_id=customer_id,
        invoice_type='out_invoice',
        lines=[
            {'name': 'Consulting Services', 'quantity': 40, 'price_unit': 150},
            {'name': 'Software License', 'quantity': 1, 'price_unit': 1000}
        ],
        invoice_date='2026-02-19',
        invoice_date_due='2026-03-19'
    )
    
    # 3. Post invoice
    client.post_invoice(invoice_id)
    
    # 4. Register payment
    client.register_invoice_payment(
        invoice_id=invoice_id,
        amount=7000,
        payment_date='2026-02-19'
    )
    
    # 5. Get updated invoice
    invoice = client.get_invoice(invoice_id)
    print(f"Invoice {invoice['name']}: {invoice['payment_state']}")
```

### Expense Report Workflow

```python
from utils.odoo_client import get_odoo_client

with get_odoo_client() as client:
    # 1. Create expenses
    expense_ids = []
    for expense_data in [
        {'type': 'Travel', 'amount': 350, 'desc': 'Client meeting'},
        {'type': 'Meals', 'amount': 75, 'desc': 'Business lunch'},
        {'type': 'Hotel', 'amount': 200, 'desc': 'Overnight stay'}
    ]:
        expense_id = client.create_expense(
            employee_id=1,
            product_id=1,  # Adjust based on your products
            name=expense_data['desc'],
            unit_amount=expense_data['amount']
        )
        expense_ids.append(expense_id)
    
    # 2. Submit for approval
    client.submit_expenses(expense_ids)
    
    # 3. Check status
    expenses = client.get_expenses(employee_id=1, state='reported')
    print(f"Submitted {len(expenses)} expenses")
```

### Financial Reporting

```python
from Skills.odoo_skills import OdooSkills

skills = OdooSkills()

# Accounts Receivable
ar = skills.get_accounts_receivable()
print(f"Total Receivable: ${ar['total_receivable']:.2f}")
print(f"Outstanding Invoices: {ar['invoice_count']}")

# Accounts Payable
ap = skills.get_accounts_payable()
print(f"Total Payable: ${ap['total_payable']:.2f}")
print(f"Outstanding Bills: {ap['bill_count']}")

# Journal Entries
entries = skills.get_journal_entries(
    date_from='2026-01-01',
    date_to='2026-01-31'
)
print(f"Journal Entries: {entries['count']}")
```

## Best Practices

1. **Use Context Managers**: Always use `with` statement for automatic connection management
2. **Error Handling**: Wrap operations in try-except blocks
3. **Validation**: Validate inputs before making API calls
4. **Logging**: Enable logging for debugging
5. **Connection Pooling**: Reuse client instances when possible
6. **Batch Operations**: Use bulk operations for better performance

## Troubleshooting

### Connection Issues

```
Error: Authentication failed
```
- Check ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASSWORD in .env
- Verify Odoo server is running
- Check network connectivity

```
Error: XML-RPC fault
```
- Verify the model name is correct
- Check user permissions
- Ensure the operation is supported

### Common Issues

**Invoice creation fails**: Ensure partner_id exists and invoice lines are provided

**Payment registration fails**: Invoice must be in posted state

**Expense submission fails**: Ensure employee record exists

## License

This integration is part of the Gold Tier AI Employee System.
