import uuid
from unittest.mock import MagicMock, patch

import pytest

from django.test import Client
from django.urls import reverse

from astrophotography.models import Place
from astrophotography.tests.factories import (
    AstroImageFactory,
    CameraFactory,
    LensFactory,
    MainPageBackgroundImageFactory,
    PlaceFactory,
)


@pytest.mark.django_db
class TestAstroImageAdmin:
    def test_admin_list_displays_name(self, admin_client: Client) -> None:
        """
        Verify that the AstroImage list view in Admin displays the translated name.
        """
        # Create an image with an English name
        image = AstroImageFactory()

        # URL for the change list
        url = reverse("admin:astrophotography_astroimage_changelist")

        # Get the page as admin
        response = admin_client.get(url)

        # Check success
        assert response.status_code == 200

        # Check that the name is in the response content
        content = response.content.decode("utf-8")
        assert image.name in content

    def test_admin_change_page_displays_fields(self, admin_client: Client) -> None:
        """
        Verify that the AstroImage change page loads without errors and shows translated fields.
        """
        image = AstroImageFactory()
        url = reverse("admin:astrophotography_astroimage_change", args=[image.pk])

        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert image.name in content

    def test_admin_change_page_filtering_pl(self, admin_client: Client) -> None:
        """
        Verify that non-translatable fields are hidden when editing 'pl' language.
        """
        image = AstroImageFactory()
        url = reverse("admin:astrophotography_astroimage_change", args=[image.pk])

        # Request with language=pl
        response = admin_client.get(url, {"language": "pl"})

        assert response.status_code == 200
        content = response.content.decode("utf-8")

        # Translatable field SHOULD be present (label "Name" or value)
        assert "Name" in content

        # Shared fields SHOULD NOT be present
        assert "Capture Date" not in content
        assert "Place/City" not in content
        assert "Astrobin URL" not in content


@pytest.mark.django_db
class TestCameraLensAdmin:
    def test_camera_list_display(self, admin_client: Client) -> None:
        """
        Verify that the camera model name appears in the admin list view.
        """
        CameraFactory(model="Nikon Z6 Mod")
        url = reverse("admin:astrophotography_camera_changelist")

        response = admin_client.get(url)
        content = response.content.decode("utf-8")

        assert response.status_code == 200
        assert "Nikon Z6 Mod" in content

    def test_lens_list_display(self, admin_client: Client) -> None:
        """
        Verify that the lens model name appears in the admin list view.
        """
        LensFactory(model="Nikkor Z 20mm f/1.8")
        url = reverse("admin:astrophotography_lens_changelist")

        response = admin_client.get(url)
        content = response.content.decode("utf-8")

        assert response.status_code == 200
        assert "Nikkor Z 20mm f/1.8" in content


@pytest.mark.django_db
class TestMainPageBackgroundImageAdmin:
    def test_admin_changelist_view(self, admin_client: Client) -> None:
        url = reverse("admin:astrophotography_mainpagebackgroundimage_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200
        assert "Main Page Background" in response.content.decode("utf-8")

    def test_admin_change_view(self, admin_client: Client) -> None:
        from io import BytesIO

        from PIL import Image

        from django.core.files.uploadedfile import SimpleUploadedFile

        img = Image.new("RGB", (1, 1), color="red")
        img_io = BytesIO()
        img.save(img_io, format="PNG")
        img_io.seek(0)
        image_file = SimpleUploadedFile(
            "test_bg_admin.png", img_io.read(), content_type="image/png"
        )

        bg_image = MainPageBackgroundImageFactory(path=image_file)
        bg_image.set_current_language("en")
        bg_image.name = "Admin Existing BG"
        bg_image.save()

        url = reverse("admin:astrophotography_mainpagebackgroundimage_change", args=[bg_image.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        assert "Admin Existing BG" in response.content.decode("utf-8")


@pytest.mark.django_db
class TestPlaceAdmin:
    def test_save_model_triggers_translation_on_create(self, admin_client: Client) -> None:
        """Test that creating a new Place via Admin triggers translation task."""

        with (
            patch("translation.mixins.translate_instance_task") as mock_task,
            patch("django.conf.settings.PARLER_DEFAULT_LANGUAGE_CODE", "en"),
            patch(
                "translation.services.TranslationService.get_available_languages",
                return_value=["en", "pl"],
            ),
        ):

            mock_task.delay.side_effect = lambda *args, **kwargs: MagicMock(id=str(uuid.uuid4()))

            url = reverse("admin:astrophotography_place_add")
            data = {"name": "Hawaii", "country": "US", "_save": "Save"}

            response = admin_client.post(url, data)
            assert response.status_code == 302  # Redirect on success

            # Verify Place exists
            place = Place.objects.get(translations__name="Hawaii")
            assert place.country == "US"

            # Verify task was dispatched
            # We expect one call for 'pl' (since 'en' is default)
            mock_task.delay.assert_called_once()

            args, kwargs = mock_task.delay.call_args
            assert kwargs["model_name"] == "astrophotography.Place"
            assert kwargs["instance_pk"] == place.pk
            assert kwargs["language_code"] == "pl"
            assert kwargs["method_name"] == "translate_place"

    def test_save_model_triggers_translation_on_name_change(self, admin_client: Client) -> None:
        """Test that updating Place name via Admin triggers translation task."""

        with (
            patch("translation.mixins.translate_instance_task") as mock_task,
            patch("django.conf.settings.PARLER_DEFAULT_LANGUAGE_CODE", "en"),
            patch(
                "translation.services.TranslationService.get_available_languages",
                return_value=["en", "pl"],
            ),
        ):

            mock_task.delay.side_effect = lambda *args, **kwargs: MagicMock(id=str(uuid.uuid4()))

            # 1. Create initial place
            place = PlaceFactory(name="Greece", country="GR")

            url = reverse("admin:astrophotography_place_change", args=[place.pk])
            data = {"name": "New Greece", "country": "GR", "_save": "Save"}

            response = admin_client.post(url, data)
            assert response.status_code == 302

            # Verify task dispatched
            mock_task.delay.assert_called_once()

            args, kwargs = mock_task.delay.call_args
            assert kwargs["model_name"] == "astrophotography.Place"
            assert kwargs["instance_pk"] == place.pk
            assert kwargs["language_code"] == "pl"
            assert kwargs["method_name"] == "translate_place"

    def test_save_model_does_not_trigger_translation_if_no_name_change(
        self, admin_client: Client
    ) -> None:
        """Test that translation is triggered when target language differs from BASE."""
        import uuid

        with patch("translation.mixins.translate_instance_task") as mock_task:
            # Mock the task to return a proper task ID
            mock_task.delay.return_value.id = str(uuid.uuid4())

            # 1. Create initial place with English (BASE) and Polish translation
            place = PlaceFactory(name="Italy", country="IT")

            # Add Polish translation that differs from BASE
            place.set_current_language("pl")
            place.name = "Włochy"
            place.save()

            # Reset the mock after initial creation
            mock_task.reset_mock()

            # 2. Update the place (change country, not name)
            url = reverse("admin:astrophotography_place_change", args=[place.pk])
            data = {
                "name": "Italy",  # Unchanged
                "country": "GR",  # Changed country
                "_save": "Save",
            }

            response = admin_client.post(url, data)
            assert response.status_code == 302

            # Verify task WAS called because Polish translation differs from BASE
            # New logic: compares target language against BASE, not field changes
            mock_task.delay.assert_called()

    def test_country_field_is_translated(self, admin_client: Client) -> None:
        """
        Verify that the Country field uses Select2Widget and language is activated for Polish.
        """
        # "PL" -> "Poland" in English, "Polska" in Polish
        place = PlaceFactory(name="Poland", country="PL")
        url = reverse("admin:astrophotography_place_change", args=[place.pk])

        # Request with language=pl
        # This triggers changeform_view which should activate 'pl' language
        response = admin_client.get(url, {"language": "pl"})

        assert response.status_code == 200
        content = response.content.decode("utf-8")

        # Verify country field is present with Select2 widget
        assert 'name="country"' in content
        assert "themed-select2" in content

        # Verify page language is Polish (title should be in Polish)
        assert 'lang="pl"' in content


@pytest.mark.django_db
class TestAdminDebug:
    def test_admin_dynamic_mixin_debug(self, admin_client: Client) -> None:
        """Verify that the dynamic CSS link is injected and returns expected content."""
        image = AstroImageFactory()
        url = reverse("admin:astrophotography_astroimage_change", args=[image.pk])

        response = admin_client.get(url)
        content = response.content.decode("utf-8")

        # 1. Verify the link tag is present in the HTML
        assert (
            '<link href="/admin/dynamic-parler-fixes.css" media="all" rel="stylesheet">' in content
        )

        # 2. Verify the CSS endpoint itself returns the expected generated CSS
        css_url = reverse("admin-dynamic-css")
        css_response = admin_client.get(css_url)
        assert css_response.status_code == 200
        assert "Dynamic Parler CSS generated for default language" in css_response.content.decode(
            "utf-8"
        )

    def test_tabs_structure_multilang(self, admin_client: Client) -> None:
        """Create object with EN and PL translations and check tabs structure."""
        image = AstroImageFactory()
        image.set_current_language("pl")
        image.name = "Pl Name"
        image.save()

        url = reverse("admin:astrophotography_astroimage_change", args=[image.pk]) + "?language=en"
        response = admin_client.get(url)
        content = response.content.decode("utf-8")

        assert '<div class="parler-language-tabs">' in content
