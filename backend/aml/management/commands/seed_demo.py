from decimal import Decimal
from uuid import NAMESPACE_DNS, uuid5

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from aml.models import Customer, Device, Merchant, Rule, Transaction, WatchlistEntry
from aml.services.transaction_monitor import get_transaction_monitor


class Command(BaseCommand):
    help = 'Create fictional development-only demo data without replacing existing records.'

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('Demo seeding is disabled outside DEBUG mode. Use an isolated development database.')
        with transaction.atomic():
            Rule.objects.get_or_create(
                pk=uuid5(NAMESPACE_DNS, 'demo.didebaan.amount'),
                defaults={'name': 'Demo amount threshold', 'description': 'Fictional demo rule; not a regulatory threshold.',
                          'rule_type': 'THRESHOLD', 'status': 'ACTIVE',
                          'configuration': {'amount_threshold': 100000000}},
            )
            device, _ = Device.objects.get_or_create(device_id='DEMO-DEVICE')
            merchant, _ = Merchant.objects.get_or_create(merchant_id='DEMO-MERCHANT', defaults={'name': 'فروشگاه آزمایشی'})
            WatchlistEntry.objects.get_or_create(
                entry_type='ENTITY', name='شرکت نمونه آزمایشی', source_list='DEMO (fictional)',
            )
            created_count = 0
            for index, (first, last, amount) in enumerate([
                ('علی', 'آزمایشی', '10000000'), ('مریم', 'آزمایشی', '150000000'),
                ('رضا', 'آزمایشی', '300000000'),
            ], start=1):
                email = f'demo-{index}@example.invalid'
                customer, _ = Customer.objects.get_or_create(
                    customer_id=f'DEMO-C{index}',
                    defaults={'first_name': first, 'last_name': last, 'email': email},
                )
                if customer.email != email:
                    raise CommandError(f'DEMO-C{index} already belongs to another record; no demo changes were saved.')
                txn, created = Transaction.objects.get_or_create(
                    transaction_id=f'DEMO-T{index}',
                    defaults={'customer': customer, 'transaction_type': 'PAYMENT', 'amount': Decimal(amount),
                              'currency': 'IRR', 'status': 'COMPLETED', 'device': device, 'merchant': merchant,
                              'receiver_account': 'DEMO-ACCOUNT'},
                )
                if txn.customer_id != customer.pk:
                    raise CommandError(f'DEMO-T{index} already belongs to another customer; no demo changes were saved.')
                if created:
                    get_transaction_monitor().monitor_transaction(txn)
                    created_count += 1
        self.stdout.write(self.style.SUCCESS(
            f'Created and monitored {created_count} demo transactions. '
            'Try customer DEMO-C1 in the graph and شرکت نمونه آزمایشی in screening. '
            'Existing demo records were preserved.'
        ))
