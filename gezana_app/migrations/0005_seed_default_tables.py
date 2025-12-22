from django.db import migrations


def seed_default_tables(apps, schema_editor):
    """
    Ensure a new deployment has basic tables so bookings can succeed
    without manual admin setup.
    """
    Table = apps.get_model("gezana_app", "Table")

    # If tables already exist (e.g., from admin), do nothing.
    if Table.objects.exists():
        return

    defaults = [
        ("T1", 2),
        ("T2", 2),
        ("T3", 4),
        ("T4", 4),
        ("T5", 6),
        ("T6", 6),
        ("T7", 8),
    ]
    Table.objects.bulk_create(
        [Table(table_number=number, capacity=capacity) for number, capacity in defaults]
    )


def remove_default_tables(apps, schema_editor):
    Table = apps.get_model("gezana_app", "Table")
    numbers = ["T1", "T2", "T3", "T4", "T5", "T6", "T7"]
    Table.objects.filter(table_number__in=numbers).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("gezana_app", "0004_alter_menuitem_options_remove_menuitem_created_at_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_default_tables, remove_default_tables),
    ]
