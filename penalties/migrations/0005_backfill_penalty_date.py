# Backfill penalty_date from lateness_record.date or created_at.date()
from django.db import migrations


def backfill_penalty_date(apps, schema_editor):
    Penalty = apps.get_model("penalties", "Penalty")
    for p in Penalty.objects.select_related("lateness_record").iterator():
        if p.lateness_record_id and getattr(p.lateness_record, "date", None):
            p.penalty_date = p.lateness_record.date
        else:
            p.penalty_date = p.created_at.date() if p.created_at else p.penalty_date
        p.save(update_fields=["penalty_date"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("penalties", "0004_add_penalty_date"),
    ]

    operations = [
        migrations.RunPython(backfill_penalty_date, noop),
    ]
