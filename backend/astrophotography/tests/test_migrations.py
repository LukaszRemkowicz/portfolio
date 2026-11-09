from uuid import uuid4

import pytest

from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from astrophotography.models import AstroImage
from core.models import ImageVariant
from programming.models import ProjectImage


@pytest.mark.django_db(transaction=True)
def test_astroimage_variant_role_migration_preserves_other_models_and_files() -> None:
    migration = ("astrophotography", "0023_rename_astroimage_original_format_role")
    previous_migration = ("astrophotography", "0022_mainpagelocation_legacy_slugs")
    executor = MigrationExecutor(connection)
    latest_targets = executor.loader.graph.leaf_nodes()
    assert migration in executor.loader.graph.nodes

    previous_targets = [node for node in latest_targets if node[0] != "astrophotography"]
    previous_targets.append(previous_migration)
    stored_files: list[str] = []

    executor.migrate(previous_targets)
    try:
        astro_file = default_storage.save(
            f"images/original_format/migration-{uuid4().hex}.webp",
            ContentFile(b"existing generated image"),
        )
        project_file = default_storage.save(
            f"programming/original_format/migration-{uuid4().hex}.webp",
            ContentFile(b"existing project image"),
        )
        stored_files.extend([astro_file, project_file])
        astro_variant = ImageVariant.objects.create(
            content_type=ContentType.objects.get_for_model(AstroImage),
            object_id=str(uuid4()),
            file=astro_file,
            role="original_format",
            width=1920,
            height=1280,
            mime_type="image/webp",
        )
        project_variant = ImageVariant.objects.create(
            content_type=ContentType.objects.get_for_model(ProjectImage),
            object_id=str(uuid4()),
            file=project_file,
            role="original_format",
            width=900,
            height=600,
            mime_type="image/webp",
        )
        astro_variant_id = astro_variant.pk
        astro_dimensions = (astro_variant.width, astro_variant.height, astro_variant.mime_type)

        MigrationExecutor(connection).migrate(latest_targets)

        astro_variant.refresh_from_db()
        project_variant.refresh_from_db()
        assert astro_variant.pk == astro_variant_id
        assert astro_variant.role == "high_resolution"
        assert (
            astro_variant.width,
            astro_variant.height,
            astro_variant.mime_type,
        ) == astro_dimensions
        assert astro_variant.file.name == astro_file
        assert project_variant.role == "original_format"
        assert project_variant.file.name == project_file
        assert all(default_storage.exists(name) for name in stored_files)

        MigrationExecutor(connection).migrate(previous_targets)

        astro_variant.refresh_from_db()
        project_variant.refresh_from_db()
        assert astro_variant.role == "original_format"
        assert astro_variant.pk == astro_variant_id
        assert astro_variant.file.name == astro_file
        assert project_variant.role == "original_format"
        assert all(default_storage.exists(name) for name in stored_files)
    finally:
        MigrationExecutor(connection).migrate(latest_targets)
        for name in stored_files:
            default_storage.delete(name)


@pytest.mark.django_db(transaction=True)
def test_astroimage_variant_role_migration_allows_missing_content_type() -> None:
    migration = ("astrophotography", "0023_rename_astroimage_original_format_role")
    previous_migration = ("astrophotography", "0022_mainpagelocation_legacy_slugs")
    executor = MigrationExecutor(connection)
    latest_targets = executor.loader.graph.leaf_nodes()
    assert migration in executor.loader.graph.nodes

    previous_targets = [node for node in latest_targets if node[0] != "astrophotography"]
    previous_targets.append(previous_migration)
    ContentType.objects.filter(app_label="astrophotography", model="astroimage").delete()

    try:
        executor.migrate(previous_targets)
        MigrationExecutor(connection).migrate(latest_targets)
        assert not ContentType.objects.filter(
            app_label="astrophotography",
            model="astroimage",
        ).exists()
    finally:
        MigrationExecutor(connection).migrate(latest_targets)
