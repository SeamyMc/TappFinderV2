from django.db import migrations


def backfill(apps, schema_editor):
    PintLog = apps.get_model('pints', 'PintLog')
    AmenityReport = apps.get_model('pints', 'AmenityReport')
    Event = apps.get_model('pints', 'Event')
    EventConfirmation = apps.get_model('pints', 'EventConfirmation')
    Contribution = apps.get_model('pints', 'Contribution')

    rows = []
    for log in PintLog.objects.filter(is_seeded=False).iterator():
        rows.append(Contribution(
            user_id=log.user_id,
            kind='pint',
            pub_id=log.pub_id,
            pint_log_id=log.id,
            created_at=log.logged_at,
        ))

    seen = set()
    for report in AmenityReport.objects.order_by('created_at').iterator():
        key = (report.pub_id, report.amenity_id)
        kind = 'confirmation' if key in seen else 'amenity'
        seen.add(key)
        rows.append(Contribution(
            user_id=report.user_id,
            kind=kind,
            pub_id=report.pub_id,
            amenity_report_id=report.id,
            created_at=report.created_at,
        ))

    for event in Event.objects.exclude(created_by__isnull=True).iterator():
        rows.append(Contribution(
            user_id=event.created_by_id,
            kind='event',
            pub_id=event.pub_id,
            event_id=event.id,
            created_at=event.created_at,
        ))

    for conf in EventConfirmation.objects.select_related('event').iterator():
        rows.append(Contribution(
            user_id=conf.user_id,
            kind='confirmation',
            pub_id=conf.event.pub_id,
            event_confirmation_id=conf.id,
            created_at=conf.created_at,
        ))

    Contribution.objects.bulk_create(rows, batch_size=500)


def unbackfill(apps, schema_editor):
    Contribution = apps.get_model('pints', 'Contribution')
    Contribution.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('pints', '0006_contribution'),
    ]

    operations = [
        migrations.RunPython(backfill, unbackfill),
    ]
