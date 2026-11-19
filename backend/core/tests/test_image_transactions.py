from unittest.mock import patch

import pytest

from django.db import transaction

from common.tests.image_helpers import jpeg_field
from core.models import ImageVariant
from programming.tests.factories import ProjectFactory


@pytest.fixture
def execute_on_commit():
    """Use Django's real commit hooks for these transaction tests."""
    return


def make_variant(owner):
    variant = ImageVariant.objects.create(owner=owner, role="probe", width=1, height=1)
    variant.file.save("transaction-probe.jpg", jpeg_field("probe.jpg"), save=True)
    return variant


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "operation",
    ["variant_instance", "variant_queryset", "owner_instance", "owner_queryset"],
)
@pytest.mark.parametrize("rollback", [True, False])
def test_file_cleanup_follows_transaction(operation, rollback):
    with patch("programming.models.submit"):
        owner = ProjectFactory(image=jpeg_field("old.jpg"))
        variant = make_variant(owner)
        target = variant.file
        storage, name = target.storage, target.name
        assert storage.exists(name)

        with transaction.atomic():
            if operation == "variant_instance":
                variant.delete()
            elif operation == "variant_queryset":
                ImageVariant.objects.filter(pk=variant.pk).delete()
            elif operation == "owner_instance":
                owner.delete()
            else:
                type(owner).objects.filter(pk=owner.pk).delete()
            assert storage.exists(name)
            if rollback:
                transaction.set_rollback(True)

        assert storage.exists(name) is rollback


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("kind", ["instance", "queryset"])
def test_variant_deletion_in_autocommit(kind):
    with patch("programming.models.submit"):
        owner = ProjectFactory()
        variant = make_variant(owner)
        storage, name = variant.file.storage, variant.file.name
        if kind == "instance":
            variant.delete()
        else:
            ImageVariant.objects.filter(pk=variant.pk).delete()
        assert not storage.exists(name)


@pytest.mark.django_db(transaction=True)
def test_failing_storage_delete_does_not_block_later_commit_hooks():
    with patch("programming.models.submit"):
        owner = ProjectFactory(image=jpeg_field("old.jpg"))
        variant = make_variant(owner)
        later = []

        def failing_delete(name):
            raise RuntimeError("r2 down")

        with patch.object(variant.file.storage, "delete", new=failing_delete):
            with transaction.atomic():
                variant.delete()
                transaction.on_commit(lambda: later.append(True))
        assert later == [True]
        assert not ImageVariant.objects.filter(pk=variant.pk).exists()
