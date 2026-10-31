from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .intelligence import normalize_text
from .models import Alert, AlertComment, AuditLog, Customer, Device, Merchant, Rule, ThresholdConfig, Transaction, WatchlistEntry


class IntelligenceTest(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.user = get_user_model().objects.create_user(username='compliance')
        self.user.groups.add(Group.objects.get_or_create(name='COMPLIANCE_OFFICER')[0])
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.customer = Customer.objects.create(customer_id='C-1', first_name='علی', last_name='کریمی', email='c1@example.com')
        self.txn = self.make_transaction('T-1', amount=100)
        self.rule = Rule.objects.create(name='Amount', description='Amount rule', rule_type='THRESHOLD',
                                        configuration={'amount_threshold': 200}, status='DRAFT')
        self.alert = Alert.objects.create(alert_id='A-1', transaction=self.txn, customer=self.customer,
                                         title='Review', description='Reason', risk_score=50,
                                         assigned_to='investigator', assigned_at=self.now - timedelta(hours=25))
        self.alert.triggered_rules.add(self.rule)

    def make_transaction(self, transaction_id, **kwargs):
        values = {'customer': self.customer, 'transaction_type': 'PAYMENT', 'status': 'COMPLETED',
                  'amount': 100, 'transaction_date': self.now - timedelta(hours=1)}
        values.update(kwargs)
        return Transaction.objects.create(transaction_id=transaction_id, **values)

    def simulate(self, config=None, **kwargs):
        data = {'rule_id': str(self.rule.pk), 'configuration': {'amount_threshold': 50} if config is None else config}
        data.update(kwargs)
        return self.client.post('/api/intelligence/simulate/', data, format='json')

    def test_simulation_compares_without_writes(self):
        before = (Alert.objects.count(), AlertComment.objects.count(), self.rule.versions.count())
        response = self.simulate()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['baseline_matches'], 0)
        self.assertEqual(response.data['candidate_matches'], 1)
        self.assertEqual(response.data['new_matches'], 1)
        self.rule.refresh_from_db()
        self.txn.refresh_from_db()
        self.assertEqual(self.rule.configuration, {'amount_threshold': 200})
        self.assertEqual(self.rule.status, 'DRAFT')
        self.assertIsNone(self.rule.last_applied_at)
        self.assertIsNone(self.txn.risk_score)
        self.assertEqual(before, (Alert.objects.count(), AlertComment.objects.count(), self.rule.versions.count()))

    def test_simulation_bounds_and_deterministic_sampling(self):
        self.make_transaction('T-2')
        self.make_transaction('future', transaction_date=self.now + timedelta(days=1))
        self.make_transaction('old', transaction_date=self.now - timedelta(days=100))
        self.make_transaction('failed', status='FAILED')
        response = self.simulate(limit=1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['eligible_count'], 2)
        self.assertEqual(response.data['evaluated_count'], 1)
        self.assertTrue(response.data['truncated'])
        self.assertEqual(response.data['results'][0]['transaction_id'], 'T-1')
        for field, value in [('limit', 501), ('days', 0), ('days', 91), ('rule_id', 'invalid')]:
            with self.subTest(field=field, value=value):
                self.assertEqual(self.simulate(**{field: value}).status_code, 400)

    def test_simulation_rejects_unsafe_configurations(self):
        for config in [{'amount_threshold': 0}, {'amount_threshold': -1}, {'amount_threshold': 'NaN'},
                       {'amount_threshold': True}, {'unknown': 1}, {'daily_count_threshold': 1.5}, []]:
            with self.subTest(config=config):
                self.assertEqual(self.simulate(config).status_code, 400)
        self.rule.rule_type = 'DEVICE_SHARING'
        self.rule.save()
        self.assertEqual(self.simulate().status_code, 400)

    def test_historical_daily_count_does_not_see_later_transactions(self):
        self.txn.transaction_date = self.now.replace(hour=1, minute=0, second=0, microsecond=0) - timedelta(days=1)
        self.txn.save()
        self.make_transaction('later', transaction_date=self.txn.transaction_date + timedelta(hours=1))
        self.rule.configuration = {'daily_count_threshold': 2}
        self.rule.save()
        response = self.simulate({'daily_count_threshold': 2})
        by_id = {r['transaction_id']: r for r in response.data['results']}
        self.assertFalse(by_id['T-1']['candidate_match'])
        self.assertTrue(by_id['later']['candidate_match'])

    def test_pattern_and_behavioral_simulation(self):
        self.make_transaction('earlier', amount=10, transaction_date=self.txn.transaction_date - timedelta(minutes=1))
        self.make_transaction('later', transaction_date=self.txn.transaction_date + timedelta(minutes=1))
        self.rule.rule_type = 'PATTERN'
        self.rule.configuration = {'rapid_transaction_threshold': True, 'rapid_transaction_count': 3}
        self.rule.save()
        response = self.simulate(self.rule.configuration)
        by_id = {r['transaction_id']: r for r in response.data['results']}
        self.assertFalse(by_id['T-1']['candidate_match'])
        self.assertTrue(by_id['later']['candidate_match'])
        self.rule.rule_type = 'BEHAVIORAL'
        self.rule.configuration = {'amount_increase_threshold': 3}
        self.rule.save()
        response = self.simulate(self.rule.configuration)
        by_id = {r['transaction_id']: r for r in response.data['results']}
        self.assertTrue(by_id['T-1']['candidate_match'])

    def test_geographic_configuration_validation(self):
        self.rule.rule_type = 'GEOGRAPHIC'
        self.rule.configuration = {'high_risk_countries': ['AF']}
        self.rule.save()
        self.txn.receiver_country = 'AF'
        self.txn.save()
        self.assertEqual(self.simulate({'high_risk_countries': ['AF']}).data['candidate_matches'], 1)
        self.assertEqual(self.simulate({'high_risk_countries': 'AF'}).status_code, 400)
        self.assertEqual(self.simulate({'high_risk_countries': ['af']}).status_code, 400)

    def test_screen_normalizes_persian_name_and_digits(self):
        entry = WatchlistEntry.objects.create(entry_type='ENTITY', name='علي كريمي', national_id='001234', source_list='Internal')
        response = self.client.post('/api/intelligence/screen/', {'name': 'عَلِی کَرِیمِی'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['matches'][0]['id'], entry.pk)
        self.assertEqual(response.data['matches'][0]['score'], 100)
        response = self.client.post('/api/intelligence/screen/', {'national_id': '۰۰۱۲۳۴'}, format='json')
        self.assertEqual(response.data['matches'][0]['match_type'], 'national_id')
        self.assertEqual(normalize_text('كِي'), normalize_text('کی'))

    def test_screen_ignores_inactive_and_country_entries(self):
        WatchlistEntry.objects.create(entry_type='ENTITY', name='علی کریمی', is_active=False)
        WatchlistEntry.objects.create(entry_type='COUNTRY', country_code='IR')
        response = self.client.post('/api/intelligence/screen/', {'name': 'علی کریمی'}, format='json')
        self.assertEqual(response.data['screened_count'], 0)
        self.assertEqual(response.data['matches'], [])
        for data in [{}, {'name': 'ََ'}, {'name': 'علی', 'minimum_score': 69}]:
            self.assertEqual(self.client.post('/api/intelligence/screen/', data, format='json').status_code, 400)

    def test_screen_fuzzy_match_requires_threshold(self):
        WatchlistEntry.objects.create(entry_type='ENTITY', name='علی کریمی')
        response = self.client.post('/api/intelligence/screen/', {'name': 'علی کریم', 'minimum_score': 85}, format='json')
        self.assertEqual(response.data['match_count'], 1)
        response = self.client.post('/api/intelligence/screen/', {'name': 'علی کریم', 'minimum_score': 100}, format='json')
        self.assertEqual(response.data['match_count'], 0)

    def test_graph_contains_entities_counts_and_shared_customers(self):
        device = Device.objects.create(device_id='D-1')
        merchant = Merchant.objects.create(merchant_id='M-1', name='Shop')
        self.txn.device, self.txn.merchant, self.txn.receiver_account = device, merchant, 'ACC-1'
        self.txn.save()
        peer = Customer.objects.create(customer_id='C-2', first_name='Peer', last_name='User', email='c2@example.com')
        self.make_transaction('peer', customer=peer, device=device)
        response = self.client.get('/api/intelligence/graph/', {'customer_id': 'C-1'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['edges']), 3)
        self.assertEqual({n['kind'] for n in response.data['nodes']}, {'customer', 'device', 'merchant', 'account'})
        self.assertEqual(response.data['related_customers'][0]['customer__customer_id'], 'C-2')
        self.assertEqual(response.data['related_customers'][0]['transactions'], 1)
        self.assertEqual(self.client.get('/api/intelligence/graph/', {'customer_id': 'unknown'}).status_code, 404)
        self.assertEqual(self.client.get('/api/intelligence/graph/', {'customer_id': 'C-1', 'days': 'oops'}).status_code, 400)

    def test_graph_empty_and_truncated(self):
        self.txn.status = 'FAILED'
        self.txn.save()
        response = self.client.get('/api/intelligence/graph/', {'customer_id': 'C-1'})
        self.assertEqual(response.data['edges'], [])
        Transaction.objects.bulk_create([Transaction(transaction_id=f'B-{i}', customer=self.customer,
            transaction_type='PAYMENT', amount=1, status='COMPLETED', transaction_date=self.now) for i in range(201)])
        response = self.client.get('/api/intelligence/graph/', {'customer_id': 'C-1'})
        self.assertEqual(response.data['sampled_count'], 200)
        self.assertTrue(response.data['truncated'])

    def test_sla_uses_existing_configuration_and_excludes_closed(self):
        ThresholdConfig.objects.create(name='SLA', threshold_type='ALERT_SLA_HOURS', value=10)
        self.alert.assigned_at = self.now - timedelta(hours=11)
        self.alert.save()
        Alert.objects.create(alert_id='soon', transaction=self.txn, customer=self.customer, risk_score=1,
                             assigned_to='investigator', assigned_at=self.now - timedelta(hours=9))
        Alert.objects.create(alert_id='unassigned', transaction=self.txn, customer=self.customer, risk_score=1)
        Alert.objects.create(alert_id='closed', transaction=self.txn, customer=self.customer, risk_score=1,
                             assigned_to='investigator', assigned_at=self.now - timedelta(hours=50), status='RESOLVED')
        response = self.client.get('/api/intelligence/sla/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['assigned_open'], 2)
        self.assertEqual(response.data['overdue'], 1)
        self.assertEqual(response.data['due_soon'], 1)
        self.assertEqual(response.data['unassigned_open'], 1)
        self.assertEqual(response.data['results'][0]['alert_id'], 'A-1')

    def test_sla_exact_deadline_is_not_overdue(self):
        ThresholdConfig.objects.create(name='SLA', threshold_type='ALERT_SLA_HOURS', value=24)
        self.alert.assigned_at = self.now - timedelta(hours=24)
        self.alert.save()
        with patch('aml.intelligence.timezone.now', return_value=self.now):
            response = self.client.get('/api/intelligence/sla/')
        self.assertEqual(response.data['overdue'], 0)
        self.assertEqual(response.data['due_soon'], 1)

    def test_case_export_has_chronological_history_and_explicit_provenance(self):
        first = AlertComment.objects.create(alert=self.alert, author='reviewer', comment='First')
        second = AlertComment.objects.create(alert=self.alert, author='reviewer', comment='Second')
        response = self.client.get('/api/intelligence/case-export/', {'alert_id': 'A-1'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['schema_version'], 1)
        self.assertEqual(response.data['exported_by'], 'compliance')
        self.assertEqual([c['id'] for c in response.data['history']], [first.pk, second.pk])
        self.assertEqual(response.data['alert']['transaction_detail']['transaction_id'], 'T-1')
        self.assertEqual(response.data['rules_current_snapshot'][0]['name'], self.rule.name)
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertEqual(response['Cache-Control'], 'no-store')
        self.assertEqual(self.client.get('/api/intelligence/case-export/', {'alert_id': 'missing'}).status_code, 404)

    def test_screening_inputs_are_not_persisted_in_audit_body(self):
        response = self.client.post('/api/intelligence/screen/', {
            'name': 'Private Name', 'national_id': '001234', 'minimum_score': 85,
        }, format='json')
        self.assertEqual(response.status_code, 200)
        audit = AuditLog.objects.filter(path='/api/intelligence/screen/').latest('timestamp')
        self.assertEqual(audit.request_body, {'minimum_score': 85})
        self.assertEqual(response['Cache-Control'], 'no-store')

    def test_large_watchlist_rejects_instead_of_screening_an_incomplete_list(self):
        WatchlistEntry.objects.bulk_create([
            WatchlistEntry(entry_type='ENTITY', name=f'Entity {i}') for i in range(5001)
        ])
        response = self.client.post('/api/intelligence/screen/', {'name': 'Entity'}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_evidence_bundle_never_silently_omits_history(self):
        AlertComment.objects.bulk_create([
            AlertComment(alert=self.alert, author='reviewer', comment='Note') for _ in range(10001)
        ])
        response = self.client.get('/api/intelligence/case-export/', {'alert_id': 'A-1'})
        self.assertEqual(response.status_code, 400)
        self.assertNotIn('Content-Disposition', response)

    def test_role_permissions_for_all_five_endpoints(self):
        for role in ['AUDITOR', 'INVESTIGATOR', 'SUPERVISOR']:
            with self.subTest(role=role):
                self.user.groups.set([Group.objects.get_or_create(name=role)[0]])
                self.assertEqual(self.simulate().status_code, 403)
                self.assertEqual(self.client.post('/api/intelligence/screen/', {'name': 'علی'}).status_code, 403)
                for action, params in [('sla', {}), ('graph', {'customer_id': 'C-1'}), ('case-export', {'alert_id': 'A-1'})]:
                    self.assertEqual(self.client.get(f'/api/intelligence/{action}/', params).status_code, 200)
        self.user.groups.clear()
        self.assertEqual(self.client.get('/api/intelligence/sla/').status_code, 403)
        self.client.force_authenticate(None)
        self.assertIn(self.client.get('/api/intelligence/sla/').status_code, [401, 403])
