from io import StringIO

import pytest

from django.core.management import call_command

from common.tests.image_helpers import _png_field
from shop.models import ShopSettings


@pytest.mark.django_db
class TestSeedShopSettingsCommand:
    def test_command_seeds_missing_english_and_polish_copy(self) -> None:
        settings_obj = ShopSettings.objects.create(
            image=_png_field("shop-settings-bg.png", size=(1920, 1080))
        )

        output = StringIO()
        call_command("configure_shop", stdout=output)

        settings_obj.refresh_from_db()

        assert "en: seeded" in output.getvalue()
        assert "pl: seeded" in output.getvalue()

        assert settings_obj.safe_translation_getter("title", language_code="en") == (
            "Collect the night sky in print."
        )
        assert settings_obj.safe_translation_getter("title", language_code="pl") == (
            "Zabierz nocne niebo na swoją ścianę."
        )
        assert (
            "Discover selected astrophotography images and some of my best work"
            in settings_obj.safe_translation_getter(
                "description",
                language_code="en",
            )
        )
        assert (
            "Odkryj wybrane zdjęcia astrofotograficzne oraz niektóre z moich najlepszych prac"
            in settings_obj.safe_translation_getter(
                "description",
                language_code="pl",
            )
        )

    def test_command_keeps_existing_copy_without_overwrite(self) -> None:
        settings_obj = ShopSettings.objects.create(
            image=_png_field("shop-settings-bg.png", size=(1920, 1080))
        )
        settings_obj.set_current_language("en")
        settings_obj.title = "Custom title"
        settings_obj.description = "<p>Custom description.</p>"
        settings_obj.save()

        output = StringIO()
        call_command("configure_shop", stdout=output)

        settings_obj.refresh_from_db()

        assert "en: kept existing values" in output.getvalue()
        assert settings_obj.safe_translation_getter("title", language_code="en") == "Custom title"
        assert (
            settings_obj.safe_translation_getter("description", language_code="en")
            == "<p>Custom description.</p>"
        )

    def test_command_fills_only_missing_fields_without_overwrite(self) -> None:
        settings_obj = ShopSettings.objects.create(
            image=_png_field("shop-settings-bg.png", size=(1920, 1080))
        )
        settings_obj.set_current_language("en")
        settings_obj.title = "Custom title"
        settings_obj.description = ""
        settings_obj.save()

        call_command("configure_shop")

        settings_obj.refresh_from_db()

        assert settings_obj.safe_translation_getter("title", language_code="en") == "Custom title"
        assert (
            "Discover selected astrophotography images and some of my best work"
            in settings_obj.safe_translation_getter(
                "description",
                language_code="en",
            )
        )

    def test_command_overwrites_existing_copy_when_requested(self) -> None:
        settings_obj = ShopSettings.objects.create(
            image=_png_field("shop-settings-bg.png", size=(1920, 1080))
        )
        settings_obj.set_current_language("en")
        settings_obj.title = "Custom title"
        settings_obj.description = "<p>Custom description.</p>"
        settings_obj.save()

        output = StringIO()
        call_command("configure_shop", overwrite=True, stdout=output)

        settings_obj.refresh_from_db()

        assert "en: seeded" in output.getvalue()
        assert settings_obj.safe_translation_getter("title", language_code="en") == (
            "Collect the night sky in print."
        )

    def test_command_creates_shop_settings_when_missing(self) -> None:
        output = StringIO()

        call_command("configure_shop", stdout=output)

        settings_obj = ShopSettings.get_current()

        assert settings_obj is not None
        assert "Created ShopSettings singleton." in output.getvalue()
        assert settings_obj.safe_translation_getter("title", language_code="en") == (
            "Collect the night sky in print."
        )

    def test_command_can_skip_when_shop_settings_is_missing(self) -> None:
        output = StringIO()

        call_command("configure_shop", skip_missing=True, stdout=output)

        assert "ShopSettings does not exist yet. Skipping." in output.getvalue()
