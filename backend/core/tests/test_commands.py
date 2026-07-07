import json
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest
from pytest_mock import MockerFixture
from rest_framework import status

from django.core.management import call_command
from django.core.management.base import CommandError
from django.urls import reverse

from astrophotography.models import MeteorsMainPageConfig
from astrophotography.tests.factories import AstroImageFactory
from common.tests.image_helpers import jpeg_field
from core.management.commands.backfill_image_variants import Command as BackfillImageVariantsCommand
from core.management.commands.regenerate_thumbnails import Command as RegenerateThumbnailsCommand
from core.models import LandingPageSettings
from programming.tests.factories import ProjectImageFactory
from shop.models import ShopSettings
from shop.tests.factories import ShopProductFactory
from users.tests.factories import UserFactory


class TestMcpListCommandsCommand:
    def test_mcp_list_commands_returns_json_command_inventory(self) -> None:
        output = StringIO()

        call_command("mcp_list_commands", "--json", stdout=output)

        payload = json.loads(output.getvalue())
        assert payload == {
            "commands": [
                {
                    "name": "media_inventory",
                    "description": "Inspect DB image references and media files on disk.",
                    "read_only": True,
                    "params": {},
                }
            ]
        }


@pytest.mark.django_db
class TestMediaInventoryCommand:
    def test_media_inventory_reports_db_refs_missing_files_and_orphans(
        self,
        settings,
        tmp_path,
    ) -> None:
        settings.MEDIA_ROOT = tmp_path
        media_root = Path(settings.MEDIA_ROOT)

        with (
            patch("core.models.process_image_task.delay_on_commit"),
            patch("users.models.process_image_task.delay_on_commit"),
        ):
            astro_image = AstroImageFactory(original=jpeg_field("astro-source.jpg"))
            user = UserFactory()
            user.avatar.save("avatar-source.jpg", jpeg_field("avatar-source.jpg"), save=True)

        type(astro_image).objects.filter(pk=astro_image.pk).update(
            original="images/missing-source.jpg"
        )
        orphan_path = media_root / "orphans" / "manual-orphan.jpg"
        orphan_path.parent.mkdir(parents=True, exist_ok=True)
        orphan_path.write_bytes(b"orphan")

        output = StringIO()
        call_command("media_inventory", "--json", stdout=output)

        payload = json.loads(output.getvalue())

        assert payload["summary"]["db_references"] >= 2
        assert payload["summary"]["missing_references"] == 1
        assert payload["summary"]["unreferenced_files"] >= 2
        assert any(
            field["model"] == "users.User" and field["field"] == "avatar"
            for field in payload["fields"]
        )
        assert any(
            reference["model"] == "astrophotography.AstroImage"
            and reference["field"] == "original"
            and reference["file"] == "images/missing-source.jpg"
            for reference in payload["missing_references"]
        )
        assert any(
            disk_file["path"] == "orphans/manual-orphan.jpg"
            for disk_file in payload["delete_candidates"]
        )


@pytest.mark.django_db
class TestSeedSettingsCommand:
    def test_seed_settings_creates_defaults(self, api_client):
        """Test that seed_settings command creates default settings and config"""
        # Ensure no settings record exists
        LandingPageSettings.objects.all().delete()
        MeteorsMainPageConfig.objects.all().delete()

        # Run seeding
        call_command("seed_settings")

        # Verify through the settings API (integrative test)
        url = reverse("settings")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        # Defaults should be True, and meteors should be auto-linked
        assert response.data["programming"] is True
        assert response.data["contactForm"] is True
        assert response.data["travelHighlights"] is True
        assert response.data["lastimages"] is True
        assert response.data["shop"] is False
        assert response.data["meteors"]["randomShootingStars"] is True


@pytest.mark.django_db
class TestClearCacheCommand:
    def test_clear_cache_calls_backend_cache_clear(self, mocker: MockerFixture) -> None:
        mock_clear = mocker.patch("core.management.commands.clear_cache.cache.clear")

        call_command("clear_cache")

        mock_clear.assert_called_once()


@pytest.mark.django_db
class TestRegenerateThumbnailsCommand:
    def test_command_does_not_inherit_variant_backfill_command(self) -> None:
        assert not issubclass(RegenerateThumbnailsCommand, BackfillImageVariantsCommand)

    def test_regenerates_thumbnail_variants_only(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory(
                original=jpeg_field("regenerate-thumbnail.jpg", size=(1200, 800)),
            )

        image.sync_image_variants()
        image.variants.filter(role="thumbnail").delete()
        existing_card_count = image.variants.filter(role="card").count()

        call_command("regenerate_thumbnails", object_id=str(image.pk))

        image.refresh_from_db()
        thumbnail = image.variants.get(role="thumbnail", width=560)
        assert thumbnail.height == 373
        assert image.variants.filter(role="card").count() == existing_card_count

    def test_force_rebuilds_existing_thumbnail_variant(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory(
                original=jpeg_field("force-thumbnail.jpg", size=(1200, 800)),
            )

        image.sync_image_variants()
        old_thumbnail_name = image.variants.get(role="thumbnail", width=560).file.name

        call_command("regenerate_thumbnails", object_id=str(image.pk), force=True)

        image.refresh_from_db()
        new_thumbnail_name = image.variants.get(role="thumbnail", width=560).file.name
        assert new_thumbnail_name != old_thumbnail_name


@pytest.mark.django_db
class TestBackfillImageVariantsCommand:
    def test_generates_missing_variants(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory(
                original=jpeg_field("backfill.jpg", size=(1200, 800)),
            )

        assert image.variants.count() == 0

        call_command("backfill_image_variants", object_id=str(image.pk))

        image.refresh_from_db()
        original_format = image.variants.get(role="original_format")
        card_widths = [
            variant.width for variant in image.variants.filter(role="card").order_by("width")
        ]
        thumbnail_widths = [
            variant.width for variant in image.variants.filter(role="thumbnail").order_by("width")
        ]
        assert card_widths == [
            320,
            560,
            840,
            1120,
        ]
        assert original_format.width == 1200
        assert thumbnail_widths == [560]

    def test_generates_project_image_original_format_from_model_specs(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = ProjectImageFactory(
                original=jpeg_field("project-backfill.jpg", size=(900, 600)),
            )

        assert [spec.role for spec in image.get_image_variant_specs()] == ["original_format"]

        call_command("backfill_image_variants", object_id=str(image.pk))

        image.refresh_from_db()
        original_format = image.variants.get(role="original_format", width=900)
        assert original_format.height == 600
        assert original_format.file.name.startswith("programming/original_format/")

    def test_generates_user_profile_variants(self) -> None:
        with patch("users.models.process_image_task.delay_on_commit"):
            user = UserFactory(
                avatar=jpeg_field("avatar-backfill.jpg", size=(800, 800)),
                about_me_image=jpeg_field("about-me-backfill.jpg", size=(1200, 800)),
                about_me_image2=jpeg_field("about-me-2-backfill.jpg", size=(900, 600)),
            )

        assert user.variants.count() == 0

        call_command("backfill_image_variants", object_id=str(user.pk))

        user.refresh_from_db()
        avatar = user.variants.get(role="avatar__original_format", width=800)
        portrait = user.variants.get(role="about_me_image__original_format", width=1200)
        second_portrait = user.variants.get(role="about_me_image2__original_format", width=900)
        assert avatar.file.name.startswith("avatars/avatar/original_format/")
        assert portrait.file.name.startswith("about_me_images/about_me_image/original_format/")
        assert second_portrait.file.name.startswith(
            "about_me_images/about_me_image2/original_format/"
        )

    def test_generates_new_thumbnail_spec_for_existing_variant_rows(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory(
                original=jpeg_field("thumbnail-backfill.jpg", size=(1200, 800)),
            )

        image.variants.create(
            file="images/card/existing-320.webp",
            role="card",
            width=320,
            height=213,
            mime_type="image/webp",
        )

        call_command("backfill_image_variants", object_id=str(image.pk))

        image.refresh_from_db()
        original_format = image.variants.get(role="original_format")
        thumbnail_variant = image.variants.get(role="thumbnail", width=560)
        assert original_format.width == 1200
        assert thumbnail_variant.height == 373
        assert thumbnail_variant.file.name.startswith("images/thumbnail/")

    def test_generates_shop_product_thumbnail_from_linked_astroimage_original(self) -> None:
        with patch("shop.models.process_image_task.delay_on_commit"):
            astro_image = AstroImageFactory(
                original=jpeg_field("astro-product-source.jpg", size=(1600, 1200))
            )
            product = ShopProductFactory(
                image=astro_image,
                image_cropped=None,
            )

        assert product.variants.count() == 0

        call_command("backfill_image_variants", object_id=str(product.pk))

        product.refresh_from_db()
        thumbnail_variant = product.variants.get(role="thumbnail", width=560)
        assert thumbnail_variant.height == 420
        assert thumbnail_variant.file.name.startswith("shop/products/cropped/")

    def test_generates_shop_settings_background_variant(self) -> None:
        with patch("shop.models.process_image_task.delay_on_commit"):
            settings = ShopSettings.objects.create(
                image=jpeg_field("shop-background.jpg", size=(2200, 1467)),
                title="Prints",
                description="Shop background",
            )

        assert settings.variants.count() == 0

        call_command("backfill_image_variants", object_id=str(settings.pk))

        settings.refresh_from_db()
        background_variant = settings.variants.get(role="background", width=1920)
        assert background_variant.height == 1280
        assert background_variant.file.name.startswith("shop/backgrounds/background/")

    def test_reports_missing_source_file_and_continues(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory(
                original=jpeg_field("missing-source-seed.jpg", size=(1200, 800)),
            )
        type(image).objects.filter(pk=image.pk).update(original="images/missing-source.jpg")
        stderr = StringIO()

        with pytest.raises(CommandError, match="Image variant backfill failed"):
            call_command("backfill_image_variants", object_id=str(image.pk), stderr=stderr)

        assert image.variants.count() == 0
        assert "missing source file" in stderr.getvalue()

    def test_silent_reports_missing_source_without_raising(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory(
                original=jpeg_field("silent-missing-source-seed.jpg", size=(1200, 800)),
            )
        type(image).objects.filter(pk=image.pk).update(original="images/silent-missing.jpg")
        stderr = StringIO()
        stdout = StringIO()

        call_command(
            "backfill_image_variants",
            object_id=str(image.pk),
            silent=True,
            stdout=stdout,
            stderr=stderr,
        )

        assert image.variants.count() == 0
        assert "missing source file" in stderr.getvalue()
        assert "Errors: 1" in stdout.getvalue()

    def test_reports_missing_source_when_original_file_is_missing(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory(
                original=jpeg_field("legacy-source-seed.jpg", size=(1200, 800)),
            )
        type(image).objects.filter(pk=image.pk).update(original="images/legacy-source.png")
        stderr = StringIO()

        with pytest.raises(CommandError, match="Image variant backfill failed"):
            call_command("backfill_image_variants", object_id=str(image.pk), stderr=stderr)

        image.refresh_from_db()
        assert image.variants.count() == 0
        assert "missing source file" in stderr.getvalue()

    def test_reports_error_when_source_file_cannot_generate_variants(self) -> None:
        with patch("core.models.process_image_task.delay_on_commit"):
            image = AstroImageFactory(
                original=jpeg_field("bad-source-seed.jpg", size=(1200, 800)),
            )
        stderr = StringIO()

        with (
            patch("core.mixins.build_image_with_given_width", return_value=None),
            pytest.raises(CommandError, match="Image variant backfill failed"),
        ):
            call_command("backfill_image_variants", object_id=str(image.pk), stderr=stderr)

        image.refresh_from_db()
        assert image.variants.count() == 0
        assert "source image error" in stderr.getvalue()
