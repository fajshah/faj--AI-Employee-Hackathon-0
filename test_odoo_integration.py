"""
Comprehensive Test Suite for Odoo Integration
Tests OdooClient, OdooSkills, and FinanceAgent
"""

import unittest
import logging
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add project root to path for absolute imports
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.odoo_client import (
    OdooClient,
    OdooClientError,
    OdooAuthenticationError,
    OdooOperationError,
    OdooValidationError,
    get_odoo_client
)
from Skills.odoo_skills import OdooSkills
from Agents.Finance_Agent import FinanceAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== Unit Tests with Mocks ====================

class TestOdooClientValidation(unittest.TestCase):
    """Test OdooClient configuration validation"""
    
    def test_empty_url_raises_error(self):
        """Test that empty URL raises validation error"""
        with self.assertRaises(OdooValidationError):
            OdooClient("", "db", "user", "pass")
    
    def test_invalid_url_format_raises_error(self):
        """Test that URL without protocol raises error"""
        with self.assertRaises(OdooValidationError):
            OdooClient("localhost:8069", "db", "user", "pass")
    
    def test_empty_db_raises_error(self):
        """Test that empty database name raises error"""
        with self.assertRaises(OdooValidationError):
            OdooClient("http://localhost:8069", "", "user", "pass")
    
    def test_empty_username_raises_error(self):
        """Test that empty username raises error"""
        with self.assertRaises(OdooValidationError):
            OdooClient("http://localhost:8069", "db", "", "pass")
    
    def test_empty_password_raises_error(self):
        """Test that empty password raises error"""
        with self.assertRaises(OdooValidationError):
            OdooClient("http://localhost:8069", "db", "user", "")
    
    def test_valid_config_accepted(self):
        """Test that valid configuration is accepted"""
        client = OdooClient("http://localhost:8069", "odoo", "admin", "admin")
        self.assertEqual(client.url, "http://localhost:8069")
        self.assertEqual(client.db, "odoo")
        self.assertEqual(client.username, "admin")


class TestOdooClientMocked(unittest.TestCase):
    """Test OdooClient with mocked XML-RPC"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = OdooClient(
            url="http://localhost:8069",
            db="test_db",
            username="admin",
            password="admin"
        )
        
        # Mock the server proxies
        self.mock_common = Mock()
        self.mock_models = Mock()
        self.client._common = self.mock_common
        self.client._models = self.mock_models
        self.client.uid = 2
        self.client._connected = True
    
    def test_connect_success(self):
        """Test successful connection"""
        self.mock_common.authenticate.return_value = 2
        
        result = self.client.connect()
        
        self.assertTrue(result)
        self.assertEqual(self.client.uid, 2)
        self.assertTrue(self.client._connected)
    
    def test_connect_failure(self):
        """Test failed authentication"""
        self.mock_common.authenticate.return_value = False
        
        with self.assertRaises(OdooAuthenticationError):
            self.client.connect()
    
    def test_create_record(self):
        """Test creating a record"""
        self.mock_models.execute_kw.return_value = 123
        
        record_id = self.client.create('res.partner', {'name': 'Test Partner'})
        
        self.assertEqual(record_id, 123)
        self.mock_models.execute_kw.assert_called_once()
    
    def test_read_records(self):
        """Test reading records"""
        mock_data = [{'id': 1, 'name': 'Partner 1'}]
        self.mock_models.execute_kw.return_value = mock_data
        
        results = self.client.read('res.partner', [1])
        
        self.assertEqual(results, mock_data)
    
    def test_update_records(self):
        """Test updating records"""
        self.mock_models.execute_kw.return_value = True
        
        result = self.client.update('res.partner', [1], {'name': 'Updated'})
        
        self.assertTrue(result)
    
    def test_delete_records(self):
        """Test deleting records"""
        self.mock_models.execute_kw.return_value = True
        
        result = self.client.delete('res.partner', [1])
        
        self.assertTrue(result)
    
    def test_search(self):
        """Test searching records"""
        self.mock_models.execute_kw.return_value = [1, 2, 3]
        
        results = self.client.search('res.partner', [('name', 'ilike', 'test')])
        
        self.assertEqual(results, [1, 2, 3])
    
    def test_search_read(self):
        """Test search and read"""
        mock_data = [
            {'id': 1, 'name': 'Test 1'},
            {'id': 2, 'name': 'Test 2'}
        ]
        self.mock_models.execute_kw.return_value = mock_data
        
        results = self.client.search_read(
            'res.partner',
            [('name', 'ilike', 'test')],
            fields=['id', 'name']
        )
        
        self.assertEqual(results, mock_data)
    
    def test_context_manager(self):
        """Test context manager usage"""
        self.mock_common.authenticate.return_value = 2
        
        with patch('utils.odoo_client.xmlrpc') as mock_xmlrpc:
            mock_xmlrpc.client.ServerProxy.side_effect = [
                self.mock_common,
                self.mock_models
            ]
            
            with OdooClient("http://localhost:8069", "db", "user", "pass") as client:
                self.assertTrue(client._connected)
            
            # After context, should be disconnected
            self.assertFalse(client._connected)


class TestInvoiceOperations(unittest.TestCase):
    """Test invoice-related operations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = OdooClient(
            url="http://localhost:8069",
            db="test_db",
            username="admin",
            password="admin"
        )
        
        self.mock_common = Mock()
        self.mock_models = Mock()
        self.client._common = self.mock_common
        self.client._models = self.mock_models
        self.client.uid = 2
        self.client._connected = True
    
    def test_create_invoice(self):
        """Test creating an invoice"""
        self.mock_models.execute_kw.side_effect = [123]  # create returns ID
        
        invoice_id = self.client.create_invoice(
            partner_id=1,
            invoice_type='out_invoice',
            lines=[
                {'name': 'Product 1', 'quantity': 2, 'price_unit': 100}
            ]
        )
        
        self.assertEqual(invoice_id, 123)
    
    def test_create_invoice_invalid_type(self):
        """Test creating invoice with invalid type"""
        with self.assertRaises(OdooValidationError):
            self.client.create_invoice(
                partner_id=1,
                invoice_type='invalid_type',
                lines=[{'name': 'Product', 'quantity': 1, 'price_unit': 100}]
            )
    
    def test_create_invoice_no_lines(self):
        """Test creating invoice without lines raises error"""
        with self.assertRaises(OdooValidationError):
            self.client.create_invoice(
                partner_id=1,
                invoice_type='out_invoice',
                lines=None
            )
    
    def test_create_invoice_invalid_partner(self):
        """Test creating invoice with invalid partner"""
        with self.assertRaises(OdooValidationError):
            self.client.create_invoice(
                partner_id=0,
                invoice_type='out_invoice',
                lines=[{'name': 'Product', 'quantity': 1, 'price_unit': 100}]
            )
    
    def test_get_invoices(self):
        """Test getting invoices"""
        mock_invoices = [
            {'id': 1, 'name': 'INV/2026/001', 'amount_total': 1000},
            {'id': 2, 'name': 'INV/2026/002', 'amount_total': 500}
        ]
        self.mock_models.execute_kw.return_value = mock_invoices
        
        invoices = self.client.get_invoices(partner_id=1, limit=10)
        
        self.assertEqual(len(invoices), 2)
    
    def test_post_invoice(self):
        """Test posting an invoice"""
        self.mock_models.execute_kw.return_value = True
        
        result = self.client.post_invoice(123)
        
        self.assertTrue(result)
    
    def test_cancel_invoice(self):
        """Test canceling an invoice"""
        self.mock_models.execute_kw.return_value = True
        
        result = self.client.cancel_invoice(123)
        
        self.assertTrue(result)


class TestExpenseOperations(unittest.TestCase):
    """Test expense-related operations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = OdooClient(
            url="http://localhost:8069",
            db="test_db",
            username="admin",
            password="admin"
        )
        
        self.mock_common = Mock()
        self.mock_models = Mock()
        self.client._common = self.mock_common
        self.client._models = self.mock_models
        self.client.uid = 2
        self.client._connected = True
    
    def test_create_expense(self):
        """Test creating an expense"""
        self.mock_models.execute_kw.return_value = 456
        
        expense_id = self.client.create_expense(
            employee_id=1,
            product_id=2,
            name="Travel Expense",
            unit_amount=500.00,
            quantity=1
        )
        
        self.assertEqual(expense_id, 456)
    
    def test_create_expense_invalid_employee(self):
        """Test creating expense with invalid employee"""
        with self.assertRaises(OdooValidationError):
            self.client.create_expense(
                employee_id=0,
                product_id=1,
                name="Expense",
                unit_amount=100
            )
    
    def test_create_expense_negative_amount(self):
        """Test creating expense with negative amount"""
        with self.assertRaises(OdooValidationError):
            self.client.create_expense(
                employee_id=1,
                product_id=1,
                name="Expense",
                unit_amount=-100
            )
    
    def test_get_expenses(self):
        """Test getting expenses"""
        mock_expenses = [
            {'id': 1, 'name': 'Expense 1', 'total_amount': 100},
            {'id': 2, 'name': 'Expense 2', 'total_amount': 200}
        ]
        self.mock_models.execute_kw.return_value = mock_expenses
        
        expenses = self.client.get_expenses(employee_id=1)
        
        self.assertEqual(len(expenses), 2)
    
    def test_submit_expenses(self):
        """Test submitting expenses"""
        self.mock_models.execute_kw.return_value = True
        
        result = self.client.submit_expenses([1, 2, 3])
        
        self.assertTrue(result)


class TestPaymentOperations(unittest.TestCase):
    """Test payment-related operations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = OdooClient(
            url="http://localhost:8069",
            db="test_db",
            username="admin",
            password="admin"
        )
        
        self.mock_common = Mock()
        self.mock_models = Mock()
        self.client._common = self.mock_common
        self.client._models = self.mock_models
        self.client.uid = 2
        self.client._connected = True
    
    def test_create_payment(self):
        """Test creating a payment"""
        self.mock_models.execute_kw.return_value = 789
        
        payment_id = self.client.create_payment(
            partner_id=1,
            amount=1000,
            payment_type='outbound'
        )
        
        self.assertEqual(payment_id, 789)
    
    def test_create_payment_invalid_type(self):
        """Test creating payment with invalid type"""
        with self.assertRaises(OdooValidationError):
            self.client.create_payment(
                partner_id=1,
                amount=1000,
                payment_type='invalid'
            )
    
    def test_get_payments(self):
        """Test getting payments"""
        mock_payments = [
            {'id': 1, 'name': 'PAY/2026/001', 'amount': 1000},
            {'id': 2, 'name': 'PAY/2026/002', 'amount': 500}
        ]
        self.mock_models.execute_kw.return_value = mock_payments
        
        payments = self.client.get_payments(partner_id=1)
        
        self.assertEqual(len(payments), 2)


class TestJournalEntryOperations(unittest.TestCase):
    """Test journal entry operations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = OdooClient(
            url="http://localhost:8069",
            db="test_db",
            username="admin",
            password="admin"
        )
        
        self.mock_common = Mock()
        self.mock_models = Mock()
        self.client._common = self.mock_common
        self.client._models = self.mock_models
        self.client.uid = 2
        self.client._connected = True
    
    def test_create_journal_entry(self):
        """Test creating a journal entry"""
        self.mock_models.execute_kw.return_value = 999
        
        entry_id = self.client.create_journal_entry(
            name="Monthly Entry",
            date="2026-02-19",
            lines=[
                {'account_id': 10, 'debit': 1000, 'credit': 0},
                {'account_id': 20, 'debit': 0, 'credit': 1000}
            ]
        )
        
        self.assertEqual(entry_id, 999)
    
    def test_create_journal_entry_no_lines(self):
        """Test creating journal entry without lines"""
        with self.assertRaises(OdooValidationError):
            self.client.create_journal_entry(
                name="Entry",
                date="2026-02-19",
                lines=[]
            )
    
    def test_create_journal_entry_missing_account(self):
        """Test creating journal entry with missing account"""
        with self.assertRaises(OdooValidationError):
            self.client.create_journal_entry(
                name="Entry",
                date="2026-02-19",
                lines=[{'debit': 100, 'credit': 0}]  # Missing account_id
            )
    
    def test_get_journal_entries(self):
        """Test getting journal entries"""
        mock_entries = [
            {'id': 1, 'name': 'JE/2026/001', 'date': '2026-02-01'},
            {'id': 2, 'name': 'JE/2026/002', 'date': '2026-02-02'}
        ]
        self.mock_models.execute_kw.return_value = mock_entries
        
        entries = self.client.get_journal_entries()
        
        self.assertEqual(len(entries), 2)


class TestOdooSkills(unittest.TestCase):
    """Test OdooSkills high-level operations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_client = Mock(spec=OdooClient)
        self.skills = OdooSkills(self.mock_client)
    
    def test_create_customer_invoice(self):
        """Test creating customer invoice via skills"""
        self.mock_client.search_partners.return_value = [{'id': 1, 'name': 'Test Customer'}]
        self.mock_client.create_invoice.return_value = 123
        
        result = self.skills.create_customer_invoice(
            customer_name="Test Customer",
            items=[{'name': 'Product', 'quantity': 1, 'price_unit': 100}]
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['invoice_id'], 123)
    
    def test_create_customer_invoice_new_customer(self):
        """Test creating invoice creates customer if not found"""
        self.mock_client.search_partners.return_value = []
        self.mock_client.create_partner.return_value = 999
        self.mock_client.create_invoice.return_value = 123
        
        result = self.skills.create_customer_invoice(
            customer_name="New Customer",
            items=[{'name': 'Product', 'quantity': 1, 'price_unit': 100}]
        )
        
        self.assertTrue(result['success'])
        self.mock_client.create_partner.assert_called_once()
    
    def test_find_customer(self):
        """Test finding customer"""
        self.mock_client.search_partners.return_value = [
            {'id': 1, 'name': 'Test Customer', 'email': 'test@example.com'}
        ]
        
        result = self.skills.find_customer("Test")
        
        self.assertTrue(result['success'])
        self.assertEqual(result['count'], 1)
    
    def test_check_connection(self):
        """Test connection check"""
        self.mock_client.check_connection.return_value = True
        self.mock_client.get_server_version.return_value = {'server_version': '16.0'}
        
        result = self.skills.check_connection()
        
        self.assertTrue(result['success'])
        self.assertTrue(result['connected'])


class TestFinanceAgent(unittest.TestCase):
    """Test FinanceAgent"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_client = Mock(spec=OdooClient)
        self.agent = FinanceAgent(self.mock_client)
    
    def test_execute_create_invoice_task(self):
        """Test executing create invoice task"""
        self.mock_client.search_partners.return_value = [{'id': 1}]
        self.mock_client.create_invoice.return_value = 123
        
        task = {
            'action_type': 'create_invoice',
            'customer_id': 1,
            'items': [{'name': 'Product', 'quantity': 1, 'price_unit': 100}]
        }
        
        result = self.agent.execute_task(task)
        
        self.assertTrue(result)
    
    def test_execute_log_expense_task(self):
        """Test executing log expense task"""
        self.mock_client.search_products.return_value = [{'id': 1}]
        self.mock_client.create_expense.return_value = 456
        
        task = {
            'action_type': 'log_expense',
            'employee_id': 1,
            'expense_type': 'Travel',
            'amount': 500,
            'description': 'Business trip'
        }
        
        result = self.agent.execute_task(task)
        
        self.assertTrue(result)
    
    def test_execute_unknown_action(self):
        """Test executing unknown action type"""
        task = {'action_type': 'unknown_action'}
        
        result = self.agent.execute_task(task)
        
        self.assertFalse(result)
    
    def test_get_status(self):
        """Test getting agent status"""
        status = self.agent.get_status()
        
        self.assertEqual(status['name'], 'Finance_Agent')
        self.assertIn('connected', status)


# ==================== Integration Test Helpers ====================

class IntegrationTestHelpers:
    """Helper methods for integration tests"""
    
    @staticmethod
    def create_test_invoice(client: OdooClient) -> int:
        """Create a test invoice and return ID"""
        # Find or create partner
        partners = client.search_partners(name="Test Partner")
        if not partners:
            partner_id = client.create_partner(name="Test Partner", customer=True)
        else:
            partner_id = partners[0]['id']
        
        # Create invoice
        invoice_id = client.create_invoice(
            partner_id=partner_id,
            invoice_type='out_invoice',
            lines=[
                {'name': 'Test Product', 'quantity': 1, 'price_unit': 100}
            ]
        )
        
        return invoice_id
    
    @staticmethod
    def cleanup_test_data(client: OdooClient, invoice_ids: list = None):
        """Clean up test data"""
        if invoice_ids:
            for invoice_id in invoice_ids:
                try:
                    client.delete_invoice(invoice_id)
                except Exception:
                    pass  # May already be deleted or posted


# ==================== Run Tests ====================

def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestOdooClientValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestOdooClientMocked))
    suite.addTests(loader.loadTestsFromTestCase(TestInvoiceOperations))
    suite.addTests(loader.loadTestsFromTestCase(TestExpenseOperations))
    suite.addTests(loader.loadTestsFromTestCase(TestPaymentOperations))
    suite.addTests(loader.loadTestsFromTestCase(TestJournalEntryOperations))
    suite.addTests(loader.loadTestsFromTestCase(TestOdooSkills))
    suite.addTests(loader.loadTestsFromTestCase(TestFinanceAgent))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
