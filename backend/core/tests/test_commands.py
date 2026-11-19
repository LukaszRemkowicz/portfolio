from io import StringIO
from unittest.mock import patch

import pytest
from pytest_mock import MockerFixture

from django.core.management import call_command
from django.core.management.base import CommandError

from astrophotography.models import MeteorsMainPageConfig
from astrophotography.tests.factories import AstroImageFactory
from common.tests.image_helpers import jpeg_field
from core.models import LandingPageSettings
from programming.tests.factories import ProjectFactory
from shop.models import ShopSettings
from shop.tests.factories import ShopProductFactory
from users.tests.factories import UserFactory


@pytest.mark.django_db
class TestSeedSettingsCommand:
    def test_seed_settings_creates_defaults(self):
        """Test that seed_settings command creates default settings and config"""
        LandingPageSettings.objects.all().delete()
        MeteorsMainPageConfig.objects.all().delete()

        call_command("seed_settings")

        settings_obj = LandingPageSettings.objects.get()
        assert settings_obj.programming_enabled is True
        assert settings_obj.contact_form_enabled is True
        assert settings_obj.shop_enabled is False
        assert settings_obj.meteors is not None


@pytest.mark.django_db
class TestClearCacheCommand:
    def test_clear_cache_calls_backend_cache_clear(self, mocker: MockerFixture) -> None:
        mock_clear = mocker.patch("core.management.commands.clear_cache.cache.clear")

        call_command("clear_cache")

        mock_clear.assert_called_once()


@pytest.mark.django_db
class TestBackfillImageVariantsCommand:
    def test_generates_missing_variants(self) -> None:
        with patch("core.models.submit"):
            image = AstroImageFactory(
                original=jpeg_field("backfill.jpg", size=(3000, 2000)),
            )

        assert image.variants.count() == 0

        call_command("backfill_image_variants", object_id=str(image.pk))

        image.refresh_from_db()
        high_resolution = image.variants.get(role="high_resolution")
        detail_widths = [
            variant.width for variant in image.variants.filter(role="detail").order_by("width")
        ]
        thumbnail_widths = [
            variant.width for variant in image.variants.filter(role="thumbnail").order_by("width")
        ]
        assert detail_widths == [
            1280,
            1920,
            2560,
        ]
        assert high_resolution.width == 1920
        assert thumbnail_widths == [320, 560]

    def test_generates_project_variants_from_model_specs(self) -> None:
        with patch("programming.models.submit"):
            project = ProjectFactory(image=jpeg_field("project-backfill.jpg", size=(900, 600)))

        call_command("backfill_image_variants", object_id=str(project.pk))

        project.refresh_from_db()
        original_format = project.variants.get(role="original_format", width=900)
        assert original_format.height == 600
        assert original_format.file.name.startswith("programming/projects/original_format/")

    def test_generates_user_profile_variants(self) -> None:
        with patch("users.models.submit"):
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
        with patch("core.models.submit"):
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
        high_resolution = image.variants.get(role="high_resolution")
        thumbnail_variant = image.variants.get(role="thumbnail", width=560)
        assert high_resolution.width == 1200
        assert thumbnail_variant.height == 373
        assert thumbnail_variant.file.name.startswith("images/thumbnail/")
        assert not image.variants.filter(role="card").exists()

    def test_generates_shop_product_thumbnail_from_linked_astroimage_original(self) -> None:
        with patch("shop.models.submit"):
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
        with patch("shop.models.submit"):
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
        with patch("core.models.submit"):
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
        with patch("core.models.submit"):
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
        with patch("core.models.submit"):
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
        with patch("core.models.submit"):
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
