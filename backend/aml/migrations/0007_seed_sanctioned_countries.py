from django.db import migrations

SANCTIONED_COUNTRIES = ['KP', 'SD', 'SY', 'SO', 'LY']
SOURCE_LIST = 'UN/FATF'


def seed_watchlist(apps, schema_editor):
    WatchlistEntry = apps.get_model('aml', 'WatchlistEntry')
    for code in SANCTIONED_COUNTRIES:
        WatchlistEntry.objects.get_or_create(
            entry_type='COUNTRY',
            country_code=code,
            defaults={'source_list': SOURCE_LIST, 'added_by': 'migration'},
        )


def unseed_watchlist(apps, schema_editor):
    WatchlistEntry = apps.get_model('aml', 'WatchlistEntry')
    WatchlistEntry.objects.filter(
        entry_type='COUNTRY',
        country_code__in=SANCTIONED_COUNTRIES,
        added_by='migration',
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('aml', '0006_watchlist_sla_index_pass'),
    ]

    operations = [
        migrations.RunPython(seed_watchlist, unseed_watchlist),
    ]
