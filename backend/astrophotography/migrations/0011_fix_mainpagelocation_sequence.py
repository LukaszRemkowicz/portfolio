# backend/astrophotography/migrations/0011_fix_mainpagelocation_sequence.py
from django.db import migrations


def reset_mainpagelocation_sequence(apps, schema_editor):
    """
    Reset the PostgreSQL sequence for astrophotography_mainpagelocation.id
    to MAX(id) so the next INSERT does not collide with existing rows.
    This is a no-op on SQLite (test databases).
    """
    if schema_editor.connection.vendor != "postgresql":
        return

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT setval(
                pg_get_serial_sequence(
                    'astrophotography_mainpagelocation', 'id'
                ),
                COALESCE(MAX(id), 1),
                true
            )
            FROM astrophotography_mainpagelocation;
            """
        )


class Migration(migrations.Migration):

    dependencies = [
        ("astrophotography", "0010_mainpagelocationtranslation_highlight_title"),
    ]

    operations = [
        migrations.RunPython(
            reset_mainpagelocation_sequence,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
