import sys

import pytest

from django.core.management import call_command

from astrophotography.models import AstroImage
from astrophotography.tests.factories import AstroImageFactory
from core.management.commands.backfill_baseimage_fields import Command
from scripts.release_entrypoint import RELEASE_CONFIGURATION_COMMANDS


@pytest.mark.django_db
class TestBackfillBaseImageFieldsCommand:
    def test_command_backfills_legacy_values_into_new_fields(self, mocker) -> None:
        mocker.patch("core.models.process_image_task.delay_on_commit")
        image = AstroImageFactory()
        AstroImage.objects.filter(pk=image.pk).update(
            path="images/example.webp",
            original_image="images/example.jpg",
            original="",
            original_webp="",
        )

        call_command("backfill_baseimage_fields")

        image.refresh_from_db()
        assert image.original.name == "images/example.jpg"
        assert image.original_webp.name == "images/example.webp"

    def test_command_skips_new_fields_that_are_already_populated(self, mocker) -> None:
        mocker.patch("core.models.process_image_task.delay_on_commit")
        image = AstroImageFactory()
        AstroImage.objects.filter(pk=image.pk).update(
            path="images/current.webp",
            original_image="images/legacy.jpg",
            original="images/already-set.jpg",
            original_webp="",
        )

        call_command("backfill_baseimage_fields")

        image.refresh_from_db()
        assert image.original.name == "images/already-set.jpg"
        assert image.original_webp.name == "images/current.webp"

    def test_command_handles_unconverted_rows_without_webp_target(self, mocker) -> None:
        mocker.patch("core.models.process_image_task.delay_on_commit")
        image = AstroImageFactory()
        AstroImage.objects.filter(pk=image.pk).update(
            path="images/raw-upload.jpg",
            original_image="",
            original="",
            original_webp="",
        )

        call_command("backfill_baseimage_fields")

        image.refresh_from_db()
        assert image.original.name == "images/raw-upload.jpg"
        assert not image.original_webp

    def test_command_leaves_empty_rows_unchanged(self, mocker) -> None:
        mocker.patch("core.models.process_image_task.delay_on_commit")
        image = AstroImageFactory()
        AstroImage.objects.filter(pk=image.pk).update(
            path="",
            original_image="",
            original="",
            original_webp="",
        )

        call_command("backfill_baseimage_fields")

        image.refresh_from_db()
        assert not image.original
        assert not image.original_webp

    def test_backfill_instance_returns_updated_fields(self, mocker) -> None:
        mocker.patch("core.models.process_image_task.delay_on_commit")
        image = AstroImageFactory()
        AstroImage.objects.filter(pk=image.pk).update(
            path="images/example.webp",
            original_image="images/example.jpg",
            original="",
            original_webp="",
        )
        image.refresh_from_db()
        command = Command()

        updated_fields = command._backfill_instance(image)

        assert updated_fields == ["original", "original_webp"]
        assert image.original.name == "images/example.jpg"
        assert image.original_webp.name == "images/example.webp"

    def test_release_entrypoint_runs_backfill_command(self) -> None:
        assert RELEASE_CONFIGURATION_COMMANDS == (
            (sys.executable, "manage.py", "backfill_baseimage_fields"),
        )
