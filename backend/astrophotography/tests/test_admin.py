import uuid
from datetime import date
from io import BytesIO
from unittest.mock import MagicMock

import pytest
from PIL import Image
from psycopg2.extras import DateRange
from pytest_mock import MockerFixture

from django.contrib.admin.sites import site
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.test import Client, RequestFactory, override_settings
from django.urls import reverse

from astrophotography.admin import MainPageLocationAdmin
from astrophotography.models import (
    AstroImage,
    Camera,
    Lens,
    MainPageBackgroundImage,
    MainPageLocation,
    MeteorsMainPageConfig,
    Place,
    Tag,
    Telescope,
    Tracker,
    Tripod,
)
from astrophotography.tests.factories import (
    AstroImageFactory,
    CameraFactory,
    LensFactory,
    MainPageBackgroundImageFactory,
    MainPageLocationFactory,
    PlaceFactory,
)
from core.widgets import ThemedRangeWidget


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

    def test_admin_add_creates_object(self, admin_client: Client) -> None:
        """
        Verify that submitting the AstroImage add form successfully creates a new object
        with all attributes and the uploaded file.
        """
        url: str = reverse("admin:astrophotography_astroimage_add")
        place: Place = PlaceFactory()

        # Create a mock image file
        image_file = BytesIO()
        image = Image.new("RGB", (100, 100), color="black")
        image.save(image_file, "jpeg")
        image_file.name = "test_nebula.jpg"
        image_file.seek(0)

        data = {
            "name": "Test Orion Nebula",
            "description": "A very bright test nebula",
            "path": image_file,
            "place": place.pk,
            "capture_date": "2026-01-01",
            "zoom": "True",
            "celestial_object": "Landscape",
            # Additional relationships can be posted as lists if many-to-many
        }

        response: HttpResponse = admin_client.post(url, data, format="multipart")

        # The admin should save and redirect to the changelist
        if response.status_code == 200:
            form = response.context_data.get("adminform")
            errors = form.form.errors if form else "No form errors found"
            pytest.fail(f"Form submission failed with errors: {errors}")
        assert response.status_code == 302
        assert AstroImage.objects.filter(translations__name="Test Orion Nebula").exists()
        created_image = AstroImage.objects.get(translations__name="Test Orion Nebula")
        assert created_image.place == place
        assert created_image.celestial_object == "Landscape"


@pytest.mark.django_db
class TestEquipmentAdmin:
    @pytest.mark.parametrize(
        "url_name, model_class, model_value",
        [
            ("admin:astrophotography_camera_add", Camera, "Sony A7S III"),
            ("admin:astrophotography_lens_add", Lens, "Sony FE 35mm f/1.4"),
            ("admin:astrophotography_telescope_add", Telescope, "RedCat 51"),
            ("admin:astrophotography_tracker_add", Tracker, "Star Adventurer GTi"),
            ("admin:astrophotography_tripod_add", Tripod, "Benro Mach3"),
        ],
    )
    def test_equipment_admin_add(
        self, admin_client: Client, url_name: str, model_class, model_value: str
    ) -> None:
        url: str = reverse(url_name)
        data = {"model": model_value}
        response: HttpResponse = admin_client.post(url, data)
        assert response.status_code == 302, f"Failed to add {model_class.__name__}"
        assert model_class.objects.filter(model=model_value).exists()

    def test_camera_list_display(self, admin_client: Client) -> None:
        camera: Camera = CameraFactory(model="Nikon Z6 Mod")
        response: HttpResponse = admin_client.get(
            reverse("admin:astrophotography_camera_changelist")
        )
        assert response.status_code == 200
        assert camera.model in response.content.decode("utf-8")

    def test_camera_change_view(self, admin_client: Client) -> None:
        camera: Camera = CameraFactory()
        response: HttpResponse = admin_client.get(
            reverse("admin:astrophotography_camera_change", args=[camera.pk])
        )
        assert response.status_code == 200

    def test_lens_list_display(self, admin_client: Client) -> None:
        lens: Lens = LensFactory(model="Nikkor Z 20mm f/1.8")
        response: HttpResponse = admin_client.get(reverse("admin:astrophotography_lens_changelist"))
        assert response.status_code == 200
        assert lens.model in response.content.decode("utf-8")

    def test_lens_change_view(self, admin_client: Client) -> None:
        lens: Lens = LensFactory()
        response: HttpResponse = admin_client.get(
            reverse("admin:astrophotography_lens_change", args=[lens.pk])
        )
        assert response.status_code == 200


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

    def test_admin_add_creates_object(self, admin_client: Client) -> None:
        url: str = reverse("admin:astrophotography_mainpagebackgroundimage_add")
        image_file = BytesIO()
        image = Image.new("RGB", (100, 100), color="black")
        image.save(image_file, "jpeg")
        image_file.name = "test_bg.jpg"
        image_file.seek(0)
        data = {"name": "Test Background Entry", "path": image_file}
        response = admin_client.post(url, data, format="multipart")
        if response.status_code == 200:
            form = response.context_data.get("adminform")
            errors = form.form.errors if form else "No form errors found"
            pytest.fail(f"Form submission failed with errors: {errors}")
        assert response.status_code == 302
        assert MainPageBackgroundImage.objects.filter(
            translations__name="Test Background Entry"
        ).exists()


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
                self.ADD_URL, {"name": "New Test Place", "country": "US", "_save": "Save"}
            )
        assert response.status_code == 302  # Redirect on success

        # Verify Place exists
        place: Place = Place.objects.get(translations__name="New Test Place")
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

    def test_admin_add_creates_object(self, admin_client: Client) -> None:
        url: str = self.ADD_URL
        data = {"name": "Test Location", "country": "PL", "is_region": "True"}
        response = admin_client.post(url, data)
        if response.status_code == 200:
            form = response.context_data.get("adminform")
            errors = form.form.errors if form else "No form errors found"
            pytest.fail(f"Form submission failed with errors: {errors}")
        assert response.status_code == 302
        assert Place.objects.filter(translations__name="Test Location").exists()


class TestMainPageBackgroundImageAdminActions:
    ADD_URL: str = reverse("admin:astrophotography_mainpagebackgroundimage_add")
    CHANGE_URL_NAME: str = "admin:astrophotography_mainpagebackgroundimage_change"

    def test_save_model_triggers_translation_on_create(
        self,
        admin_client: Client,
        mocker: MockerFixture,
        mock_translate_task: MagicMock,
        mock_get_available_languages: MagicMock,
    ) -> None:
        with override_settings(DEFAULT_APP_LANGUAGE="en"):
            mock_translate_task.delay.side_effect = lambda *args, **kwargs: mocker.MagicMock(
                id=str(uuid.uuid4())
            )

            img: Image.Image = Image.new("RGB", (1, 1), color="red")
            img_io: BytesIO = BytesIO()
            img.save(img_io, format="PNG")
            img_io.seek(0)
            image_file: SimpleUploadedFile = SimpleUploadedFile(
                "test_bg.png", img_io.read(), content_type="image/png"
            )

            response: HttpResponse = admin_client.post(
                self.ADD_URL, {"name": "Test Background", "path": image_file, "_save": "Save"}
            )
        assert response.status_code == 302  # Redirect on success

        bg: MainPageBackgroundImage = MainPageBackgroundImage.objects.get(
            translations__name="Test Background"
        )

        mock_translate_task.delay.assert_called_once()
        args, kwargs = mock_translate_task.delay.call_args
        assert kwargs["model_name"] == "astrophotography.MainPageBackgroundImage"
        assert kwargs["instance_pk"] == bg.pk
        assert kwargs["language_code"] == "pl"
        assert kwargs["method_name"] == "translate_main_page_background_image"

    def test_save_model_triggers_translation_on_name_change(
        self,
        admin_client: Client,
        mocker: MockerFixture,
        mock_translate_task: MagicMock,
        mock_get_available_languages: MagicMock,
    ) -> None:
        """Test that updating MainPageBackgroundImage name via Admin triggers translation task."""

        with override_settings(DEFAULT_APP_LANGUAGE="en"):
            mock_translate_task.delay.side_effect = lambda *args, **kwargs: mocker.MagicMock(
                id=str(uuid.uuid4())
            )

            bg: MainPageBackgroundImage = MainPageBackgroundImageFactory(name="Old Name")

            url: str = reverse(self.CHANGE_URL_NAME, args=[bg.pk])
            data: dict[str, str] = {"name": "New Name", "_save": "Save"}

            response: HttpResponse = admin_client.post(url, data)
        assert response.status_code == 302

        mock_translate_task.delay.assert_called_once()
        args, kwargs = mock_translate_task.delay.call_args
        assert kwargs["model_name"] == "astrophotography.MainPageBackgroundImage"
        assert kwargs["instance_pk"] == bg.pk
        assert kwargs["language_code"] == "pl"
        assert kwargs["method_name"] == "translate_main_page_background_image"

    def test_save_model_does_not_trigger_translation_if_no_name_change(
        self, admin_client: Client, mocker: MockerFixture, mock_translate_task: MagicMock
    ) -> None:
        """Test that translation is NOT triggered when the name doesn't change."""

        mock_translate_task.delay.return_value.id = str(uuid.uuid4())

        bg: MainPageBackgroundImage = MainPageBackgroundImageFactory(name="Test BG")

        bg.set_current_language("pl")
        bg.name = "Testowe Tlo"
        bg.save()

        bg.set_current_language("en")
        mock_translate_task.reset_mock()

        url: str = reverse(self.CHANGE_URL_NAME, args=[bg.pk])

        with override_settings(DEFAULT_APP_LANGUAGE="en"):
            replacement_image = BytesIO()
            Image.new("RGB", (100, 100), color="black").save(replacement_image, "jpeg")
            replacement_image.name = "replacement_bg.jpg"
            replacement_image.seek(0)
            data: dict[str, str] = {
                "name": "Test BG",  # Same name
                "_save": "Save",
                "path": replacement_image,
            }
            response: HttpResponse = admin_client.post(url, data, format="multipart")

        if response.status_code == 200:
            form = response.context_data.get("adminform")
            errors = form.form.errors if form else "No form errors found"
            pytest.fail(f"Form submission failed with errors: {errors}")
        assert response.status_code == 302
        assert mock_translate_task.delay.call_count == 0


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


@pytest.mark.django_db
class TestMainPageLocationAdmin:
    CHANGE_URL_NAME: str = "admin:astrophotography_mainpagelocation_change"

    def test_admin_change_page_has_ui_enhancements(self, admin_client: Client) -> None:
        """
        Verify that the MainPageLocation change page includes the expandable CSS/JS
        and date range widgets.
        """
        location: MainPageLocation = MainPageLocationFactory()
        url: str = reverse(self.CHANGE_URL_NAME, args=[location.pk])

        response: HttpResponse = admin_client.get(url)
        assert response.status_code == 200

        content: str = response.content.decode("utf-8")

        # 1. Check for Expandable Inputs config
        assert "core/css/admin_expandable.css" in content
        assert "core/js/admin_expandable_fields.js" in content
        assert 'id="id_highlight_name"' in content
        assert 'id="id_highlight_title"' in content

        # 2. Check for Date Range Widget (Themed)
        assert "core/css/admin_date_clean.css" in content
        assert 'name="adventure_date_0"' in content
        assert 'name="adventure_date_1"' in content

        # Verify placeholders ("example" text) and types are correctly rendered
        assert 'placeholder="Start Date"' in content
        assert 'placeholder="End Date"' in content
        assert 'type="date"' in content
        assert 'onclick="this.showPicker()"' in content

        # 3. Verify Parler integration (tabs)
        assert '<div class="parler-language-tabs">' in content

    def test_adventure_date_uses_themed_range_widget(self, admin_user):
        """
        Verify that the adventure_date field in the MainPageLocationAdmin form
        uses the ThemedRangeWidget correctly.
        """
        factory = RequestFactory()
        request = factory.get("/")
        request.user = admin_user

        admin = MainPageLocationAdmin(MainPageLocation, site)
        form_class = admin.get_form(request)
        form = form_class()

        widget = form.fields["adventure_date"].widget
        assert isinstance(
            widget, ThemedRangeWidget
        ), f"Expected ThemedRangeWidget, got {type(widget)}"

        # Verify base_widget inside the range widget
        base_w = widget.widgets[0]
        assert base_w.input_type == "date"
        assert base_w.attrs.get("onclick") == "this.showPicker()"

    def test_save_model_triggers_translation_for_highlight_title(
        self,
        admin_client: Client,
        mocker,
        mock_translate_task,
        mock_get_available_languages,
    ):
        """
        Verify that saving a MainPageLocation with a highlight_title triggers the translation task.
        """
        place = PlaceFactory()
        # Reset mock after Place creation to ignore translate_place calls
        mock_translate_task.delay.reset_mock()

        url = reverse("admin:astrophotography_mainpagelocation_add")
        data = {
            "place": place.pk,
            "highlight_name": "Original Name",
            "highlight_title": "Original Title",
            "adventure_date_0": "2025-01-01",
            "adventure_date_1": "2025-01-31",
            "is_active": "on",
            "_save": "Save",
        }

        # Global mock in conftest.py handles the return value for us now
        response = admin_client.post(url, data)
        assert response.status_code == 302

        # Check if task was called with correct parameters
        assert mock_translate_task.delay.called
        # Find the call for 'pl'
        pl_call = next(
            c for c in mock_translate_task.delay.call_args_list if c.kwargs["language_code"] == "pl"
        )
        assert pl_call.kwargs["method_name"] == "translate_main_page_location"
        assert pl_call.kwargs["model_name"] == "astrophotography.MainPageLocation"

    def test_admin_add_page_loads(self, admin_client: Client) -> None:
        """GET /admin/astrophotography/mainpagelocation/add/ must return 200."""
        url: str = reverse("admin:astrophotography_mainpagelocation_add")
        response: HttpResponse = admin_client.get(url)
        assert response.status_code == 200
        content: str = response.content.decode("utf-8")
        assert 'id="id_highlight_name"' in content

    def test_admin_add_creates_object(
        self,
        admin_client: Client,
        mock_translate_task: MagicMock,
        mock_get_available_languages: MagicMock,
    ) -> None:
        """
        Regression test: POST to add view must persist a new MainPageLocation row.

        This specifically guards against the Postgres sequence desync bug that
        produces IntegrityError 'duplicate key value violates unique constraint
        astrophotography_mainpagelocation_pkey' when a row was inserted with an
        explicit id that the sequence hasn't advanced past yet.
        """
        place: Place = PlaceFactory()
        mock_translate_task.delay.reset_mock()

        url: str = reverse("admin:astrophotography_mainpagelocation_add")
        data: dict = {
            "place": place.pk,
            "highlight_name": "New Location",
            "adventure_date_0": "2025-01-01",
            "adventure_date_1": "2025-01-31",
            "is_active": "on",
            "_save": "Save",
        }

        response: HttpResponse = admin_client.post(url, data)

        # Must redirect (302) on successful creation, not show an error page.
        assert response.status_code == 302, (
            f"Expected 302 redirect after add, got {response.status_code}. "
            "Possible sequence desync or validation error."
        )

        assert MainPageLocation.objects.filter(
            translations__highlight_name="New Location"
        ).exists(), "MainPageLocation was not saved to the database."

    def test_admin_add_second_object_after_first(
        self,
        admin_client: Client,
        mock_translate_task: MagicMock,
        mock_get_available_languages: MagicMock,
    ) -> None:
        """
        Regression test: creating a second MainPageLocation must not raise a
        duplicate-key IntegrityError.  Reproduces the exact failure path: an
        existing row with id=N exists, then we try to add another row which
        Django should assign id=N+1 via the sequence.
        """
        place: Place = PlaceFactory()

        # First object — inserted via factory so it has a concrete id in the DB.
        existing: MainPageLocation = MainPageLocationFactory(place=place)
        mock_translate_task.delay.reset_mock()

        url: str = reverse("admin:astrophotography_mainpagelocation_add")
        data: dict = {
            "place": place.pk,
            "highlight_name": "Second Location",
            "adventure_date_0": "2026-01-01",
            "adventure_date_1": "2026-01-31",
            "is_active": "on",
            "_save": "Save",
        }

        response: HttpResponse = admin_client.post(url, data)

        assert response.status_code == 302, (
            f"Adding a second MainPageLocation failed with status {response.status_code}. "
            f"Possible sequence desync (existing id={existing.pk})."
        )
        assert MainPageLocation.objects.count() == 2

    def test_admin_overlapping_date_range_validation(self, admin_client: Client) -> None:
        """
        Verify that the Admin form correctly handles overlapping date ranges.
        """
        place: Place = PlaceFactory()
        # Existing: 2026-05-01 to 2026-05-15
        MainPageLocationFactory(
            place=place, adventure_date=DateRange(date(2026, 5, 1), date(2026, 5, 15))
        )

        url: str = reverse("admin:astrophotography_mainpagelocation_add")
        # Overlapping: 2026-05-10 to 2026-05-20
        data: dict = {
            "place": place.pk,
            "highlight_name": "Overlapping location",
            "adventure_date_0": "2026-05-10",
            "adventure_date_1": "2026-05-20",
            "is_active": "on",
            "_save": "Save",
        }

        response: HttpResponse = admin_client.post(url, data)
        # Should stay on the same page (200 OK) with validation error
        assert response.status_code == 200
        assert "overlapping Date range already exists" in response.content.decode()


@pytest.mark.django_db
class TestTagAdmin:
    def test_admin_add_creates_object(self, admin_client: Client) -> None:
        url: str = reverse("admin:astrophotography_tag_add")
        data = {
            "name": "Milky Way",
        }
        response = admin_client.post(url, data)
        if response.status_code == 200:
            form = response.context_data.get("adminform")
            errors = form.form.errors if form else "No form errors found"
            pytest.fail(f"Form submission failed with errors: {errors}")
        assert response.status_code == 302
        assert Tag.objects.filter(translations__name="Milky Way").exists()


@pytest.mark.django_db
class TestMeteorsMainPageConfigAdmin:
    def test_admin_add_creates_object(self, admin_client: Client) -> None:
        url: str = reverse("admin:astrophotography_meteorsmainpageconfig_add")
        data = {"bolid_chance": "10.5", "bolid_interval": "5"}
        response = admin_client.post(url, data)
        if response.status_code == 200:
            form = response.context_data.get("adminform")
            errors = form.form.errors if form else "No form errors found"
            pytest.fail(f"Form submission failed with errors: {errors}")
        assert response.status_code == 302
        assert MeteorsMainPageConfig.objects.filter(bolid_chance=10.5).exists()
