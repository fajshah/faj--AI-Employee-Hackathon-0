"""
Odoo Integration Demo Script
Demonstrates all Odoo capabilities including invoices, expenses, payments, and journal entries

Usage:
    python odoo_demo.py
    
Make sure your .env file has the correct Odoo credentials:
    ODOO_URL=http://localhost:8069
    ODOO_DB=odoo
    ODOO_USER=admin
    ODOO_PASSWORD=admin
"""

import sys
import os
from datetime import datetime, timedelta

# Add project root to path for absolute imports
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.odoo_client import OdooClient, get_odoo_client, OdooClientError
from Skills.odoo_skills import OdooSkills
from Agents.Finance_Agent import FinanceAgent


def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def print_subheader(title: str):
    """Print a formatted subheader"""
    print(f"\n--- {title} ---")


def print_result(name: str, result: dict):
    """Print a formatted result"""
    status = "✓" if result.get('success') else "✗"
    print(f"\n{status} {name}")
    if result.get('message'):
        print(f"  {result['message']}")
    elif result.get('error'):
        print(f"  Error: {result['error']}")


def demo_connection():
    """Demo: Test connection to Odoo"""
    print_header("1. CONNECTION TEST")
    
    try:
        client = get_odoo_client()
        client.connect()
        
        version = client.get_server_version()
        print(f"✓ Connected to Odoo")
        print(f"  URL: {client.url}")
        print(f"  Database: {client.db}")
        print(f"  User ID: {client.uid}")
        print(f"  Server Version: {version.get('server_version', 'Unknown')}")
        
        client.disconnect()
        return True
        
    except OdooClientError as e:
        print(f"✗ Connection failed: {e}")
        print("\n  Make sure:")
        print("  - Odoo server is running")
        print("  - Credentials in .env are correct")
        return False


def demo_basic_crud():
    """Demo: Basic CRUD operations"""
    print_header("2. BASIC CRUD OPERATIONS")
    
    try:
        with get_odoo_client() as client:
            
            # Create a partner
            print_subheader("Create Partner")
            partner_id = client.create(
                'res.partner',
                {
                    'name': 'Demo Customer',
                    'email': 'demo@example.com',
                    'phone': '+1-555-0123',
                    'city': 'New York',
                    'customer': True
                }
            )
            print(f"✓ Created partner with ID: {partner_id}")
            
            # Read the partner
            print_subheader("Read Partner")
            partner = client.read('res.partner', [partner_id])
            if partner:
                print(f"  Name: {partner[0].get('name')}")
                print(f"  Email: {partner[0].get('email')}")
                print(f"  City: {partner[0].get('city')}")
            
            # Search for partners
            print_subheader("Search Partners")
            partner_ids = client.search(
                'res.partner',
                [('name', 'ilike', 'Demo')],
                limit=5
            )
            print(f"  Found {len(partner_ids)} partners matching 'Demo'")
            
            # Search and read
            print_subheader("Search and Read")
            partners = client.search_read(
                'res.partner',
                [('name', 'ilike', 'Demo')],
                fields=['id', 'name', 'email'],
                limit=5
            )
            for p in partners:
                print(f"  - {p['name']} ({p.get('email', 'No email')})")
            
            # Update the partner
            print_subheader("Update Partner")
            client.update('res.partner', [partner_id], {'city': 'Boston'})
            updated = client.read('res.partner', [partner_id])
            print(f"  Updated city to: {updated[0].get('city')}")
            
            # Delete the partner
            print_subheader("Delete Partner")
            client.delete('res.partner', [partner_id])
            print(f"  Deleted partner {partner_id}")
            
        return True
        
    except OdooClientError as e:
        print(f"✗ CRUD operations failed: {e}")
        return False


def demo_invoice_operations():
    """Demo: Invoice operations"""
    print_header("3. INVOICE OPERATIONS")
    
    try:
        with get_odoo_client() as client:
            skills = OdooSkills(client)
            
            # Create a customer
            print_subheader("Create Customer")
            customer_result = skills.create_customer(
                name="Acme Corporation",
                email="billing@acme.com",
                phone="+1-555-0100"
            )
            print_result("Create Customer", customer_result)
            customer_id = customer_result.get('customer_id')
            
            if not customer_id:
                # Try to find existing customer
                partners = client.search_partners(name="Acme")
                if partners:
                    customer_id = partners[0]['id']
                    print(f"  Using existing customer ID: {customer_id}")
                else:
                    print("  Skipping invoice demo (no customer)")
                    return False
            
            # Create an invoice
            print_subheader("Create Customer Invoice")
            invoice_result = skills.create_customer_invoice(
                customer_id=customer_id,
                items=[
                    {'name': 'Consulting Services', 'quantity': 10, 'price_unit': 150},
                    {'name': 'Software License', 'quantity': 1, 'price_unit': 500}
                ],
                invoice_date=datetime.now().strftime('%Y-%m-%d'),
                payment_reference="INV-2026-001"
            )
            print_result("Create Invoice", invoice_result)
            invoice_id = invoice_result.get('invoice_id')
            
            if invoice_id:
                # Get invoice details
                print_subheader("Get Invoice Details")
                invoice = client.get_invoice(invoice_id)
                if invoice:
                    print(f"  Invoice: {invoice.get('name', 'Draft')}")
                    print(f"  Amount: ${invoice.get('amount_total', 0):.2f}")
                    print(f"  State: {invoice.get('state', 'draft')}")
                
                # Post the invoice
                print_subheader("Post Invoice")
                post_result = skills.post_invoice(invoice_id)
                print_result("Post Invoice", post_result)
                
                # Register payment
                print_subheader("Register Payment")
                payment_result = skills.register_payment(
                    invoice_id=invoice_id,
                    amount=invoice.get('amount_total', 2000),
                    payment_reference="PAY-2026-001"
                )
                print_result("Register Payment", payment_result)
                
                # Get customer invoices
                print_subheader("Get Customer Invoices")
                invoices_result = skills.get_customer_invoices(customer_id=customer_id)
                print(f"  Found {invoices_result.get('count', 0)} invoices")
            
            # Get accounts receivable
            print_subheader("Accounts Receivable Report")
            ar_result = skills.get_accounts_receivable()
            if ar_result.get('success'):
                print(f"  Total Receivable: ${ar_result.get('total_receivable', 0):.2f}")
                print(f"  Outstanding Invoices: {ar_result.get('invoice_count', 0)}")
            
            return True
            
    except OdooClientError as e:
        print(f"✗ Invoice operations failed: {e}")
        return False


def demo_vendor_bills():
    """Demo: Vendor bill operations"""
    print_header("4. VENDOR BILL OPERATIONS")
    
    try:
        with get_odoo_client() as client:
            skills = OdooSkills(client)
            
            # Create a vendor bill
            print_subheader("Create Vendor Bill")
            bill_result = skills.create_vendor_bill(
                vendor_name="Office Supplies Inc",
                items=[
                    {'name': 'Office Chairs', 'quantity': 5, 'price_unit': 200},
                    {'name': 'Desk Organizers', 'quantity': 10, 'price_unit': 25}
                ],
                bill_date=datetime.now().strftime('%Y-%m-%d')
            )
            print_result("Create Vendor Bill", bill_result)
            
            # Get accounts payable
            print_subheader("Accounts Payable Report")
            ap_result = skills.get_accounts_payable()
            if ap_result.get('success'):
                print(f"  Total Payable: ${ap_result.get('total_payable', 0):.2f}")
                print(f"  Outstanding Bills: {ap_result.get('bill_count', 0)}")
            
            return True
            
    except OdooClientError as e:
        print(f"✗ Vendor bill operations failed: {e}")
        return False


def demo_expense_operations():
    """Demo: Expense operations"""
    print_header("5. EXPENSE OPERATIONS")
    
    try:
        with get_odoo_client() as client:
            skills = OdooSkills(client)
            
            # Note: This requires an employee record to exist
            print_subheader("Create Employee Expense")
            
            # Try to get first employee
            employees = client.search_read('hr.employee', [], limit=1)
            
            if employees:
                employee_id = employees[0]['id']
                employee_name = employees[0].get('name', 'Unknown')
                print(f"  Using employee: {employee_name} (ID: {employee_id})")
                
                expense_result = skills.create_employee_expense(
                    employee_id=employee_id,
                    expense_type="Travel",
                    amount=350.00,
                    description="Client meeting travel expenses",
                    date=datetime.now().strftime('%Y-%m-%d')
                )
                print_result("Create Expense", expense_result)
                
                # Get employee expenses
                print_subheader("Get Employee Expenses")
                expenses_result = skills.get_employee_expenses(
                    employee_id=employee_id,
                    limit=10
                )
                print(f"  Found {expenses_result.get('count', 0)} expenses")
                
            else:
                print("  No employees found. Create an employee first.")
                print("  Skipping expense demo.")
            
            return True
            
    except OdooClientError as e:
        print(f"✗ Expense operations failed: {e}")
        return False


def demo_payment_operations():
    """Demo: Payment operations"""
    print_header("6. PAYMENT OPERATIONS")
    
    try:
        with get_odoo_client() as client:
            skills = OdooSkills(client)
            
            # Make vendor payment
            print_subheader("Make Vendor Payment")
            
            # Find a vendor
            vendors = client.search_partners(name="Office", supplier=True)
            
            if vendors:
                vendor_name = vendors[0]['name']
                payment_result = skills.make_vendor_payment(
                    vendor_name=vendor_name,
                    amount=500.00,
                    payment_reference="VENDOR-PAY-001"
                )
                print_result("Vendor Payment", payment_result)
            else:
                print("  No vendors found. Skipping vendor payment demo.")
            
            # Record customer payment
            print_subheader("Record Customer Payment")
            
            # Find a customer
            customers = client.search_partners(name="Acme", customer=True)
            
            if customers:
                customer_name = customers[0]['name']
                payment_result = skills.record_customer_payment(
                    customer_name=customer_name,
                    amount=1000.00,
                    payment_reference="CUSTOMER-PAY-001"
                )
                print_result("Customer Payment", payment_result)
            else:
                print("  No customers found. Skipping customer payment demo.")
            
            # Get payments
            print_subheader("Recent Payments")
            payments = client.get_payments(limit=5)
            print(f"  Found {len(payments)} payments")
            for payment in payments[:3]:
                print(f"  - {payment.get('name')}: ${payment.get('amount', 0):.2f}")
            
            return True
            
    except OdooClientError as e:
        print(f"✗ Payment operations failed: {e}")
        return False


def demo_journal_entries():
    """Demo: Journal entry operations"""
    print_header("7. JOURNAL ENTRY OPERATIONS")
    
    try:
        with get_odoo_client() as client:
            skills = OdooSkills(client)
            
            # Create a journal entry
            print_subheader("Create Journal Entry")
            
            # Find accounts (debit and credit)
            accounts = client.search_read('account.account', [('user_type_id.type', '=', 'other')], limit=2)
            
            if len(accounts) >= 2:
                debit_account = accounts[0]['id']
                credit_account = accounts[1]['id']
                
                entry_result = skills.create_journal_entry(
                    name="Monthly Depreciation Entry",
                    date=datetime.now().strftime('%Y-%m-%d'),
                    lines=[
                        {'account_id': debit_account, 'debit': 1000, 'credit': 0, 'name': 'Depreciation Expense'},
                        {'account_id': credit_account, 'debit': 0, 'credit': 1000, 'name': 'Accumulated Depreciation'}
                    ],
                    reference="DEPR-2026-02"
                )
                print_result("Create Journal Entry", entry_result)
                
                if entry_result.get('success'):
                    entry_id = entry_result.get('entry_id')
                    
                    # Post the entry
                    print_subheader("Post Journal Entry")
                    post_result = client.post_journal_entry(entry_id)
                    print(f"  {'✓' if post_result else '✗'} Posted entry {entry_id}")
                    
            else:
                print("  Need at least 2 accounts for journal entry demo.")
                print("  Configure your chart of accounts first.")
            
            # Get journal entries
            print_subheader("Recent Journal Entries")
            entries_result = skills.get_journal_entries(limit=5)
            if entries_result.get('success'):
                print(f"  Found {entries_result.get('count', 0)} entries")
            
            return True
            
    except OdooClientError as e:
        print(f"✗ Journal entry operations failed: {e}")
        return False


def demo_finance_agent():
    """Demo: Finance Agent task execution"""
    print_header("8. FINANCE AGENT TASK EXECUTION")
    
    try:
        with FinanceAgent() as agent:
            
            if not agent._connected:
                print("  Could not connect to Odoo. Skipping agent demo.")
                return False
            
            print_subheader("Execute Task: Create Invoice")
            task = {
                'action_type': 'create_invoice',
                'customer_name': 'Test Customer',
                'items': [
                    {'name': 'Product A', 'quantity': 2, 'price_unit': 100}
                ]
            }
            result = agent.execute_task(task)
            print(f"  {'✓' if result else '✗'} Task executed")
            
            print_subheader("Execute Task: Generate Report")
            report_task = {
                'action_type': 'generate_report',
                'report_type': 'receivables'
            }
            result = agent.execute_task(report_task)
            if result and report_task.get('result'):
                report = report_task['result']
                print(f"  Report: {report_task.get('report_name')}")
                print(f"  Total: ${report.get('total_receivable', 0):.2f}")
            
            print_subheader("Agent Status")
            status = agent.get_status()
            print(f"  Name: {status['name']}")
            print(f"  Connected: {status['connected']}")
            
            return True
            
    except OdooClientError as e:
        print(f"✗ Finance agent demo failed: {e}")
        return False


def demo_partner_operations():
    """Demo: Partner (customer/vendor) operations"""
    print_header("9. PARTNER OPERATIONS")
    
    try:
        with get_odoo_client() as client:
            skills = OdooSkills(client)
            
            # Search partners
            print_subheader("Search Partners")
            partners = client.search_partners(name="", limit=5)
            print(f"  Found {len(partners)} partners")
            for partner in partners[:3]:
                print(f"  - {partner.get('name')} ({partner.get('email', 'No email')})")
            
            # Create a new customer
            print_subheader("Create New Customer")
            customer_result = skills.create_customer(
                name="Global Tech Solutions",
                email="contact@globaltech.com",
                phone="+1-555-0200",
                city="San Francisco"
            )
            print_result("Create Customer", customer_result)
            
            # Find customer
            print_subheader("Find Customer")
            find_result = skills.find_customer("Global Tech")
            if find_result.get('success'):
                print(f"  Found {find_result.get('count', 0)} matching customers")
            
            return True
            
    except OdooClientError as e:
        print(f"✗ Partner operations failed: {e}")
        return False


def demo_export_data():
    """Demo: Export data to file"""
    print_header("10. DATA EXPORT")
    
    try:
        with get_odoo_client() as client:
            
            print_subheader("Export Partners to JSON")
            
            # Get partner IDs
            partner_ids = client.search('res.partner', [], limit=10)
            
            if partner_ids:
                # Export to JSON
                output_file = "exports/partners_export.json"
                exported_path = client.export_data(
                    model='res.partner',
                    ids=partner_ids[:5],
                    fields=['id', 'name', 'email', 'phone', 'city'],
                    output_file=output_file,
                    format='json'
                )
                print(f"  ✓ Exported to: {exported_path}")
                
                # Export to CSV
                output_file_csv = "exports/partners_export.csv"
                exported_path_csv = client.export_data(
                    model='res.partner',
                    ids=partner_ids[:5],
                    fields=['id', 'name', 'email', 'phone', 'city'],
                    output_file=output_file_csv,
                    format='csv'
                )
                print(f"  ✓ Exported to: {exported_path_csv}")
            else:
                print("  No partners to export.")
            
            return True
            
    except OdooClientError as e:
        print(f"✗ Data export failed: {e}")
        return False


def run_full_demo():
    """Run the complete demo"""
    print_header("ODOO INTEGRATION DEMO")
    print("This demo showcases all Odoo integration capabilities")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Run demos
    results['Connection'] = demo_connection()
    results['Basic CRUD'] = demo_basic_crud()
    results['Invoices'] = demo_invoice_operations()
    results['Vendor Bills'] = demo_vendor_bills()
    results['Expenses'] = demo_expense_operations()
    results['Payments'] = demo_payment_operations()
    results['Journal Entries'] = demo_journal_entries()
    results['Finance Agent'] = demo_finance_agent()
    results['Partners'] = demo_partner_operations()
    results['Data Export'] = demo_export_data()
    
    # Summary
    print_header("DEMO SUMMARY")
    
    for name, success in results.items():
        status = "✓" if success else "✗"
        print(f"  {status} {name}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print(f"\n  Total: {passed}/{total} demos successful")
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = run_full_demo()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
