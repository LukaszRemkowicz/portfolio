import uuid
from io import BytesIO
from unittest.mock import MagicMock

import pytest
from PIL import Image
from pytest_mock import MockerFixture

from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.test import Client, override_settings
from django.urls import reverse

from astrophotography.models import AstroImage, Camera, Lens, MainPageBackgroundImage, Place
from astrophotography.tests.factories import (
    AstroImageFactory,
    CameraFactory,
    LensFactory,
    MainPageBackgroundImageFactory,
    PlaceFactory,
)


@pytest.mark.django_db
class TestAstroImageAdmin:
    CHANGELIST_URL: str = reverse("admin:astrophotography_astroimage_changelist")
    CHANGE_URL_NAME: str = "admin:astrophotography_astroimage_change"

    def test_admin_list_displays_name(self, admin_client: Client) -> None:
        """
        Verify that the AstroImage list view in Admin displays the translated name.
        """
        # Create an image with an English name
        image: AstroImage = AstroImageFactory()

        # Get the page as admin
        response: HttpResponse = admin_client.get(self.CHANGELIST_URL)

        # Check success
        assert response.status_code == 200

        # Check that the name is in the response content
        content: str = response.content.decode("utf-8")
        assert image.name in content

    def test_admin_change_page_displays_fields(self, admin_client: Client) -> None:
        """
        Verify that the AstroImage change page loads without errors and shows translated fields.
        """
        image: AstroImage = AstroImageFactory()
        url: str = reverse(self.CHANGE_URL_NAME, args=[image.pk])

        response: HttpResponse = admin_client.get(url)

        assert response.status_code == 200
        content: str = response.content.decode("utf-8")
        assert image.name in content

    def test_admin_change_page_filtering_pl(self, admin_client: Client) -> None:
        """
        Verify that non-translatable fields are hidden when editing 'pl' language.
        """
        image: AstroImage = AstroImageFactory()
        # Explicit use of hardcoded string for clarity if requested, or keep refactored
        url: str = reverse(self.CHANGE_URL_NAME, args=[image.pk])

        # Request with language=pl
        response: HttpResponse = admin_client.get(url, {"language": "pl"})

        assert response.status_code == 200
        content: str = response.content.decode("utf-8")

        # Translatable field SHOULD be present (label "Name" or value)
        assert "Name" in content

        # Shared fields SHOULD NOT be present
        assert "Capture Date" not in content
        assert "Place/City" not in content
        assert "Astrobin URL" not in content


@pytest.mark.django_db
class TestCameraLensAdmin:
    CAMERA_CHANGELIST_URL: str = reverse("admin:astrophotography_camera_changelist")
    LENS_CHANGELIST_URL: str = reverse("admin:astrophotography_lens_changelist")

    def test_camera_list_display(self, admin_client: Client) -> None:
        """
        Verify that the camera model name appears in the admin list view.
        """
        camera: Camera = CameraFactory(model="Nikon Z6 Mod")
        response: HttpResponse = admin_client.get(self.CAMERA_CHANGELIST_URL)
        content: str = response.content.decode("utf-8")

        assert response.status_code == 200
        assert camera.model in content

    def test_camera_change_view(self, admin_client: Client) -> None:
        """Verify that the camera change page loads correctly."""
        camera: Camera = CameraFactory()
        url: str = reverse("admin:astrophotography_camera_change", args=[camera.pk])
        response: HttpResponse = admin_client.get(url)
        assert response.status_code == 200
        assert camera.model in response.content.decode("utf-8")

    def test_lens_list_display(self, admin_client: Client) -> None:
        """
        Verify that the lens model name appears in the admin list view.
        """
        lens: Lens = LensFactory(model="Nikkor Z 20mm f/1.8")
        response: HttpResponse = admin_client.get(self.LENS_CHANGELIST_URL)
        content: str = response.content.decode("utf-8")

        assert response.status_code == 200
        assert lens.model in content

    def test_lens_change_view(self, admin_client: Client) -> None:
        """Verify that the lens change page loads correctly."""
        lens: Lens = LensFactory()
        url: str = reverse("admin:astrophotography_lens_change", args=[lens.pk])
        response: HttpResponse = admin_client.get(url)
        assert response.status_code == 200
        assert lens.model in response.content.decode("utf-8")


@pytest.mark.django_db
class TestMainPageBackgroundImageAdmin:
    CHANGELIST_URL: str = reverse("admin:astrophotography_mainpagebackgroundimage_changelist")
    CHANGE_URL_NAME: str = "admin:astrophotography_mainpagebackgroundimage_change"

    def test_admin_changelist_view(self, admin_client: Client) -> None:
        response: HttpResponse = admin_client.get(self.CHANGELIST_URL)
        assert response.status_code == 200
        assert "Main Page Background" in response.content.decode("utf-8")

    def test_admin_change_view(self, admin_client: Client) -> None:

        img: Image.Image = Image.new("RGB", (1, 1), color="red")
        img_io: BytesIO = BytesIO()
        img.save(img_io, format="PNG")
        img_io.seek(0)
        image_file: SimpleUploadedFile = SimpleUploadedFile(
            "test_bg_admin.png", img_io.read(), content_type="image/png"
        )

        bg_image: MainPageBackgroundImage = MainPageBackgroundImageFactory(path=image_file)
        bg_image.set_current_language("en")
        bg_image.name = "Admin Existing BG"
        bg_image.save()

        url: str = reverse(self.CHANGE_URL_NAME, args=[bg_image.pk])
        response: HttpResponse = admin_client.get(url)

        assert response.status_code == 200
        assert "Admin Existing BG" in response.content.decode("utf-8")


@pytest.mark.django_db
class TestPlaceAdmin:
    ADD_URL: str = reverse("admin:astrophotography_place_add")
    CHANGE_URL_NAME: str = "admin:astrophotography_place_change"

    def test_save_model_triggers_translation_on_create(
        self,
        admin_client: Client,
        mocker: MockerFixture,
        mock_translate_task: MagicMock,
        mock_get_available_languages: MagicMock,
    ) -> None:
        """Test that creating a new Place via Admin triggers translation task."""

        with override_settings(DEFAULT_APP_LANGUAGE="en"):

            # Use mocker.MagicMock instead of importing MagicMock
            mock_translate_task.delay.side_effect = lambda *args, **kwargs: mocker.MagicMock(
                id=str(uuid.uuid4())
            )

            response: HttpResponse = admin_client.post(
                self.ADD_URL, {"name": "Hawaii", "country": "US", "_save": "Save"}
            )
        assert response.status_code == 302  # Redirect on success

        # Verify Place exists
        place: Place = Place.objects.get(translations__name="Hawaii")
        assert place.country == "US"

        # Verify task was dispatched
        # We expect one call for 'pl' (since 'en' is default)
        mock_translate_task.delay.assert_called_once()

        args, kwargs = mock_translate_task.delay.call_args
        assert kwargs["model_name"] == "astrophotography.Place"
        assert kwargs["instance_pk"] == place.pk
        assert kwargs["language_code"] == "pl"
        assert kwargs["method_name"] == "translate_place"

    def test_save_model_triggers_translation_on_name_change(
        self,
        admin_client: Client,
        mocker: MockerFixture,
        mock_translate_task: MagicMock,
        mock_get_available_languages: MagicMock,
    ) -> None:
        """Test that updating Place name via Admin triggers translation task."""

        with override_settings(DEFAULT_APP_LANGUAGE="en"):

            mock_translate_task.delay.side_effect = lambda *args, **kwargs: mocker.MagicMock(
                id=str(uuid.uuid4())
            )

            # 1. Create initial place
            place: Place = PlaceFactory(name="Greece", country="GR")

            url: str = reverse(self.CHANGE_URL_NAME, args=[place.pk])
            data: dict[str, str] = {"name": "New Greece", "country": "GR", "_save": "Save"}

            response: HttpResponse = admin_client.post(url, data)
        assert response.status_code == 302

        # Verify task dispatched
        mock_translate_task.delay.assert_called_once()

        args, kwargs = mock_translate_task.delay.call_args
        assert kwargs["model_name"] == "astrophotography.Place"
        assert kwargs["instance_pk"] == place.pk
        assert kwargs["language_code"] == "pl"
        assert kwargs["method_name"] == "translate_place"

    def test_save_model_does_not_trigger_translation_if_no_name_change(
        self, admin_client: Client, mocker: MockerFixture, mock_translate_task: MagicMock
    ) -> None:
        """Test that translation is triggered when target language differs from BASE."""

        # Mock the task to return a proper task ID
        mock_translate_task.delay.return_value.id = str(uuid.uuid4())

        # 1. Create initial place with English (BASE) and Polish translation
        place: Place = PlaceFactory(name="Italy", country="IT")

        # Add Polish translation that differs from BASE
        place.set_current_language("pl")
        place.name = "Włochy"
        place.save()

        # Reset the mock after initial creation
        mock_translate_task.reset_mock()

        # 2. Update the place (change country, not name)
        url: str = reverse(self.CHANGE_URL_NAME, args=[place.pk])
        data: dict[str, str] = {
            "name": "Italy",  # Unchanged
            "country": "GR",  # Changed country
            "_save": "Save",
        }

        response: HttpResponse = admin_client.post(url, data)
        assert response.status_code == 302

        # Verify task WAS NOT called because name did not change
        mock_translate_task.delay.assert_not_called()

    def test_country_field_is_translated(self, admin_client: Client) -> None:
        """
        Verify that the Country field uses Select2Widget and language is activated for Polish.
        """
        # "PL" -> "Poland" in English, "Polska" in Polish
        place: Place = PlaceFactory(name="Poland", country="PL")
        url: str = reverse(self.CHANGE_URL_NAME, args=[place.pk])

        # Request with language=pl
        # This triggers changeform_view which should activate 'pl' language
        response: HttpResponse = admin_client.get(url, {"language": "pl"})

        assert response.status_code == 200
        content: str = response.content.decode("utf-8")

        # Verify country field is present with Select2 widget
        assert 'name="country"' in content
        assert "themed-select2" in content

        # Verify page language is Polish (title should be in Polish)
        assert 'lang="pl"' in content


@pytest.mark.django_db
class TestAdminDebug:
    CHANGE_URL_NAME: str = "admin:astrophotography_astroimage_change"

    def test_admin_dynamic_mixin_debug(self, admin_client: Client) -> None:
        """Verify that the dynamic CSS link is injected and returns expected content."""
        image: AstroImage = AstroImageFactory()
        url: str = reverse(self.CHANGE_URL_NAME, args=[image.pk])

        response: HttpResponse = admin_client.get(url)
        content: str = response.content.decode("utf-8")

        # 1. Verify the link tag is present in the HTML
        assert (
            '<link href="/admin/dynamic-parler-fixes.css" media="all" rel="stylesheet">' in content
        )

        # 2. Verify the CSS endpoint itself returns the expected generated CSS
        css_url: str = reverse("translation:admin-dynamic-css")
        css_response: HttpResponse = admin_client.get(css_url)
        assert css_response.status_code == 200
        assert "Dynamic Parler CSS generated for default language" in css_response.content.decode(
            "utf-8"
        )

    def test_tabs_structure_multilang(self, admin_client: Client) -> None:
        """Create object with EN and PL translations and check tabs structure."""
        image: AstroImage = AstroImageFactory()
        image.set_current_language("pl")
        image.name = "Pl Name"
        image.save()

        url: str = reverse(self.CHANGE_URL_NAME, args=[image.pk]) + "?language=en"
        response: HttpResponse = admin_client.get(url)
        content: str = response.content.decode("utf-8")

        assert '<div class="parler-language-tabs">' in content
