import csv
import io
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from .models import Alert, AlertComment, Customer, Rule, Transaction


class OperationalRegressionTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(get_user_model().objects.create_user(username='operations-test', is_superuser=True))
        self.customer = Customer.objects.create(customer_id='OPS-C1', first_name='Test', last_name='Customer', email='ops@example.invalid')
        self.txn = Transaction.objects.create(transaction_id='OPS-T1', customer=self.customer,
            transaction_type='PAYMENT', amount=100000000, status='COMPLETED')
        Rule.objects.create(name='Operations threshold', description='Test', rule_type='THRESHOLD',
                            configuration={'amount_threshold': 100}, status='ACTIVE')

    def test_sync_monitor_returns_the_single_alert_created_by_the_pipeline(self):
        response = self.client.post('/api/transactions/monitor/', {'transaction_id': self.txn.transaction_id}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Alert.objects.filter(transaction=self.txn).count(), 1)
        self.assertEqual(response.data['alert']['alert_id'], response.data['monitoring_result']['alert_id'])

    def test_async_task_runs_the_full_pipeline_without_a_live_broker(self):
        from .tasks import monitor_transaction_async
        result = monitor_transaction_async.run(self.txn.transaction_id)
        self.assertEqual(Alert.objects.filter(transaction=self.txn).count(), 1)
        self.assertEqual(result['alert_id'], Alert.objects.get(transaction=self.txn).alert_id)

    @patch('aml.tasks.monitor_transaction_async.apply_async')
    @patch('aml.views.get_transaction_monitor')
    def test_async_monitor_queues_without_running_the_pipeline_in_the_request(self, monitor, enqueue):
        enqueue.return_value = SimpleNamespace(id='test-task')
        response = self.client.post('/api/transactions/monitor/', {
            'transaction_id': self.txn.transaction_id, 'asynchronous': True,
        }, format='json')
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data['task_id'], 'test-task')
        enqueue.assert_called_once_with(args=[self.txn.transaction_id], retry=False)
        monitor.assert_not_called()
        self.assertFalse(Alert.objects.exists())

    @patch('aml.tasks.monitor_transaction_async.apply_async')
    def test_async_rejects_missing_transactions_and_invalid_flags(self, enqueue):
        response = self.client.post('/api/transactions/monitor/', {'transaction_id': 'missing', 'asynchronous': True}, format='json')
        self.assertEqual(response.status_code, 404)
        response = self.client.post('/api/transactions/monitor/', {'transaction_id': self.txn.transaction_id, 'asynchronous': 'invalid'}, format='json')
        self.assertEqual(response.status_code, 400)
        enqueue.assert_not_called()

    @patch('aml.tasks.monitor_transaction_async.apply_async')
    def test_queue_outage_returns_retryable_error_without_creating_an_alert(self, enqueue):
        from kombu.exceptions import OperationalError
        enqueue.side_effect = OperationalError('unavailable')
        response = self.client.post('/api/transactions/monitor/', {'transaction_id': self.txn.transaction_id, 'asynchronous': True}, format='json')
        self.assertEqual(response.status_code, 503)
        self.assertFalse(Alert.objects.exists())

    def make_alert(self, alert_id, **kwargs):
        return Alert.objects.create(alert_id=alert_id, transaction=self.txn, customer=self.customer,
                                    risk_score=50, **kwargs)

    def csv_rows(self, response):
        return list(csv.DictReader(io.StringIO(response.content.decode('utf-8-sig'))))

    def test_export_uses_search_assignee_and_ordering_filters(self):
        low = self.make_alert('MATCH-LOW', title='Target', assigned_to='reviewer')
        high = self.make_alert('MATCH-HIGH', title='Target', assigned_to='reviewer')
        high.risk_score = 90
        high.save()
        self.make_alert('OTHER-ASSIGNEE', title='Target', assigned_to='another')
        self.make_alert('OTHER-SEARCH', title='Unrelated', assigned_to='reviewer')
        response = self.client.get('/api/alerts/export/', {'search': 'Target', 'assigned_to': 'reviewer', 'ordering': '-risk_score'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row['Alert ID'] for row in self.csv_rows(response)], [high.alert_id, low.alert_id])

    def test_csv_and_xlsx_escape_all_untrusted_text_cells(self):
        self.customer.customer_id = '=CUSTOMER'
        self.customer.first_name = '@NAME'
        self.customer.save()
        alert = self.make_alert('=ALERT', title='=TITLE', description='+DESCRIPTION', reviewed_by='@USER')
        for export_format in ['csv', 'xlsx']:
            with self.subTest(export_format=export_format):
                response = self.client.get('/api/alerts/export/', {'export_format': export_format})
                self.assertEqual(response.status_code, 200)
                if export_format == 'csv':
                    row = self.csv_rows(response)[0]
                else:
                    import openpyxl
                    sheet = openpyxl.load_workbook(io.BytesIO(response.content)).active
                    headers, values = list(sheet.values)
                    row = dict(zip(headers, values))
                    self.assertFalse(any(cell.data_type == 'f' for cells in sheet for cell in cells))
                self.assertEqual(row['Alert ID'], "'=ALERT")
                self.assertEqual(row['Customer ID'], "'=CUSTOMER")
                self.assertEqual(row['Title'], "'=TITLE")
                self.assertEqual(row['Description'], "'+DESCRIPTION")
                self.assertEqual(row['Reviewed By'], "'@USER")
        AlertComment.objects.create(alert=alert, author='=AUTHOR', comment='=COMMENT')
        row = self.csv_rows(self.client.get('/api/alerts/comments-export/'))[0]
        self.assertEqual(row['Alert ID'], "'=ALERT")
        self.assertEqual(row['Author'], "'=AUTHOR")
        self.assertEqual(row['Comment'], "'=COMMENT")


class DemoCommandTest(TestCase):
    @override_settings(DEBUG=True)
    def test_demo_seeding_is_repeatable_and_generates_single_alerts(self):
        output = io.StringIO()
        call_command('seed_demo', stdout=output)
        counts = (Customer.objects.count(), Transaction.objects.count(), Alert.objects.count(), Rule.objects.count())
        self.assertEqual(counts[:3], (3, 3, 2))
        call_command('seed_demo', stdout=output)
        self.assertEqual(counts, (Customer.objects.count(), Transaction.objects.count(), Alert.objects.count(), Rule.objects.count()))
        self.assertIn('DEMO-C1', output.getvalue())

    @override_settings(DEBUG=False)
    def test_demo_command_is_disabled_outside_development(self):
        with self.assertRaises(CommandError):
            call_command('seed_demo')
        self.assertFalse(Customer.objects.exists())

    @override_settings(DEBUG=True)
    def test_demo_collision_rolls_back_without_overwriting_data(self):
        customer = Customer.objects.create(customer_id='DEMO-C1', first_name='Existing', last_name='Customer', email='existing@example.invalid')
        with self.assertRaises(CommandError):
            call_command('seed_demo')
        customer.refresh_from_db()
        self.assertEqual(customer.email, 'existing@example.invalid')
        self.assertFalse(Rule.objects.exists())
        self.assertFalse(Transaction.objects.exists())
