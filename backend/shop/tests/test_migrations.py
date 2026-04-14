import pytest

from django.core.management import call_command
from django.db import connection


@pytest.mark.django_db(transaction=True)
def test_shop_initial_migration_applies_cleanly_from_zero() -> None:
    call_command("migrate", "shop", "zero", verbosity=0)
    call_command("migrate", "shop", verbosity=0)

    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM django_migrations WHERE app = 'shop' ORDER BY name")
        applied_migrations = [row[0] for row in cursor.fetchall()]

    table_names = set(connection.introspection.table_names())

    assert applied_migrations == ["0001_initial"]
    assert "shop_shopsettings" in table_names
    assert "shop_shopsettings_translation" in table_names
    assert "shop_shopproduct" in table_names
    assert "shop_shopproduct_translation" in table_names
